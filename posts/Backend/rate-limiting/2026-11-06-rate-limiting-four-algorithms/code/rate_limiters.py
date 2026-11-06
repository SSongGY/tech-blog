"""처리율 제한 다섯 구현에 같은 요청열을 흘려 허용·거절을 비교한다.

python rate_limiters.py

시간은 정수 밀리초로 다룬다 — 실수 누적 오차가 경계 판정을 흔들지 않게 하려는 것이다.
한도는 모두 '10초에 10건'에 맞춘다.
"""

import random
from collections import deque

LIMIT = 10
WINDOW_MS = 10_000


class FixedWindow:
    name = "고정 창"

    def __init__(self):
        self.window_start = 0
        self.count = 0

    def allow(self, now):
        start = now - now % WINDOW_MS
        if start != self.window_start:
            self.window_start, self.count = start, 0
        if self.count < LIMIT:
            self.count += 1
            return True
        return False


class SlidingLog:
    name = "슬라이딩 로그"

    def __init__(self):
        self.log = deque()

    def allow(self, now):
        while self.log and self.log[0] <= now - WINDOW_MS:
            self.log.popleft()
        if len(self.log) < LIMIT:
            self.log.append(now)
            return True
        return False


class SlidingCounter:
    """직전 창 개수에 겹친 비율을 곱해 더하는 근사 (Cloudflare 2017 글의 식)."""
    name = "슬라이딩 카운터"

    def __init__(self):
        self.window_start = 0
        self.current = 0
        self.previous = 0
        # 근사가 얼마나 틀렸는지 재려고 자기가 허용한 시각을 따로 남긴다 — 실제 구현에는 없다
        self.audit = deque()
        self.over_allowed = 0
        self.over_denied = 0

    def allow(self, now):
        start = now - now % WINDOW_MS
        if start != self.window_start:
            # 창을 둘 이상 건너뛰었으면 직전 창은 비어 있다
            self.previous = self.current if start - self.window_start == WINDOW_MS else 0
            self.current = 0
            self.window_start = start
        elapsed = now - start
        estimate = self.previous * (WINDOW_MS - elapsed) / WINDOW_MS + self.current
        decision = estimate + 1 <= LIMIT

        while self.audit and self.audit[0] <= now - WINDOW_MS:
            self.audit.popleft()
        truth = len(self.audit) < LIMIT
        self.over_allowed += decision and not truth
        self.over_denied += truth and not decision

        if decision:
            self.current += 1
            self.audit.append(now)
        return decision


class TokenBucket:
    """RFC 2697 의 C 버킷처럼 가득 찬 채로 시작해, 요청마다 토큰 하나를 쓴다."""
    name = "토큰 버킷"

    def __init__(self):
        self.capacity = LIMIT
        self.refill_ms = WINDOW_MS // LIMIT  # 1초에 1개
        self.tokens = self.capacity
        self.last = 0

    def allow(self, now):
        gained = (now - self.last) // self.refill_ms
        if gained:
            self.tokens = min(self.capacity, self.tokens + gained)
            self.last += gained * self.refill_ms
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


class LeakyBucket:
    """대기열 길이 10, 1초에 1건씩 내보낸다. 받아 준 요청은 늦게 나간다."""
    name = "누출 버킷"

    def __init__(self):
        self.capacity = LIMIT
        self.leak_ms = WINDOW_MS // LIMIT
        self.next_free = 0  # 다음 요청이 나갈 수 있는 가장 이른 시각
        self.delays = []
        self.departures = []

    def allow(self, now):
        start = max(now, self.next_free)
        queued = (start - now) // self.leak_ms  # 내 앞에 남은 요청 수
        if queued >= self.capacity:
            return False
        self.next_free = start + self.leak_ms
        self.delays.append(start - now)
        self.departures.append(start)
        return True


ALL = (FixedWindow, SlidingLog, SlidingCounter, TokenBucket, LeakyBucket)


def run(requests):
    results = {}
    for cls in ALL:
        limiter = cls()
        allowed = [t for t in requests if limiter.allow(t)]
        results[cls.name] = (limiter, allowed)
    return results


def max_in_any_window(times):
    """허용된 요청 시각들에서, 길이 10초인 어떤 구간에든 들어간 최대 건수."""
    best, left = 0, 0
    for right, t in enumerate(times):
        while times[left] <= t - WINDOW_MS:
            left += 1
        best = max(best, right - left + 1)
    return best


def scenario_boundary():
    print("### 1. 창 경계 직전·직후에 10건씩 몰릴 때 (9.5~9.95초, 10.0~10.45초)")
    burst = [9_500 + 50 * i for i in range(10)] + [10_000 + 50 * i for i in range(10)]
    for name, (_, allowed) in run(burst).items():
        before = sum(1 for t in allowed if t < 10_000)
        after = len(allowed) - before
        print(f"  {name:<8} 허용 {len(allowed):2d}  (경계 앞 {before:2d} / 뒤 {after:2d})"
              f"  1초 안에 통과한 최대 = {len(allowed)}")


def passed_times(limiter, allowed):
    """백엔드에 실제로 닿는 시각. 누출 버킷만 늦게 내보낸다."""
    return limiter.departures if isinstance(limiter, LeakyBucket) else allowed


def scenario_steady():
    print("\n### 2. 초당 2건이 60초 동안 고르게 들어올 때 (120건)")
    print("  '최대'는 백엔드에 닿은 시각 기준 — 누출 버킷은 내보낸 시각으로 센다")
    steady = [500 * i for i in range(120)]
    for name, (limiter, allowed) in run(steady).items():
        extra = ""
        if isinstance(limiter, LeakyBucket):
            extra = f"  지연 최대 {max(limiter.delays) / 1000:.1f}초"
        passed = passed_times(limiter, allowed)
        print(f"  {name:<8} 허용 {len(allowed):3d}  어느 10초든 최대 {max_in_any_window(passed):2d}건{extra}")


def scenario_random(rate):
    print(f"\n### 3. 무작위 도착 (시드 42, 평균 초당 {rate}건, 1시간)")
    rng = random.Random(42)
    t, requests = 0, []
    while t < 3_600_000:
        t += max(1, int(rng.expovariate(rate) * 1000))
        requests.append(t)
    print(f"  요청 {len(requests)}건")
    for name, (limiter, allowed) in run(requests).items():
        passed = passed_times(limiter, allowed)
        print(f"  {name:<8} 허용 {len(allowed):4d}  어느 10초든 최대 {max_in_any_window(passed):2d}건")
        if isinstance(limiter, SlidingCounter):
            wrong = limiter.over_allowed + limiter.over_denied
            print(f"           근사 오판: 한도를 넘었는데 허용 {limiter.over_allowed}건,"
                  f" 한도 안인데 거절 {limiter.over_denied}건 (전체 요청의 {wrong / len(requests):.2%})")


def scenario_memory():
    print("\n### 4. 키 하나가 들고 있는 상태")
    print("  고정 창        : 창 시작 시각, 개수                    -> 값 2개")
    print("  슬라이딩 카운터: 창 시작 시각, 현재 개수, 직전 개수     -> 값 3개")
    print("  토큰 버킷      : 토큰 수, 마지막 충전 시각              -> 값 2개")
    print("  누출 버킷      : 다음 송출 가능 시각                    -> 값 1개")
    limiter = SlidingLog()
    for t in range(0, 10_000, 1_000):
        limiter.allow(t)
    print(f"  슬라이딩 로그  : 허용한 요청 시각 전부                 -> 지금 {len(limiter.log)}개 (한도만큼 늘어난다)")


def main():
    print(f"한도: {WINDOW_MS // 1000}초에 {LIMIT}건\n")
    scenario_boundary()
    scenario_steady()
    scenario_random(0.8)
    scenario_random(1.5)
    scenario_memory()


if __name__ == "__main__":
    main()
