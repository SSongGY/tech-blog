"""캐시 스탬피드를 막는 네 가지 방식을 같은 요청열에 먹여 비교한다.

요청 도착 시각은 한 번만 만들어 네 방식이 전부 같은 것을 쓴다. 난수 시드가
고정돼 있으므로 몇 번을 돌려도 같은 숫자가 나온다.

재는 것
  재계산 횟수  — 원본(DB·외부 API)에 몇 번 갔는가
  최대 동시    — 한 시점에 재계산이 몇 개나 겹쳤는가. 스탬피드의 크기다
  대기 요청    — 재계산이 끝날 때까지 붙들린 요청 수
  평균 대기    — 붙들린 요청 하나가 기다린 평균 시간
  낡은 값      — 만료된 값을 그대로 받아 간 요청 수
"""

import math
import random

SEED = 20261015
DURATION_MS = 120_000          # 2분
MEAN_INTERVAL_MS = 20.0        # 초당 50건
TTL_MS = 10_000
RECOMPUTE_MS = 800             # 원본 재계산 비용 Δ
BETA = 1.0                     # XFetch 의 β. 논문 기본값이 1이다


def arrival_times() -> list[float]:
    """지수분포 간격으로 도착 시각을 만든다. 포아송 과정이다."""
    rng = random.Random(SEED)
    times, now = [], 0.0
    while now < DURATION_MS:
        now += rng.expovariate(1.0 / MEAN_INTERVAL_MS)
        if now < DURATION_MS:
            times.append(now)
    return times


class Cache:
    """만료 시각과 진행 중인 재계산만 들고 있는 최소 모형."""

    def __init__(self) -> None:
        self.expiry = -math.inf      # 처음에는 값이 없다
        self.filled = False
        self.inflight: list[float] = []   # 진행 중인 재계산의 완료 시각들
        self.recomputes = 0
        self.max_concurrent = 0

    def settle(self, now: float) -> None:
        """now 까지 끝난 재계산을 반영한다."""
        done = [end for end in self.inflight if end <= now]
        for end in done:
            self.expiry = max(self.expiry, end + TTL_MS)
            self.filled = True
        self.inflight = [end for end in self.inflight if end > now]

    def start(self, now: float) -> float:
        self.recomputes += 1
        end = now + RECOMPUTE_MS
        self.inflight.append(end)
        self.max_concurrent = max(self.max_concurrent, len(self.inflight))
        return end


class Result:
    def __init__(self, name: str) -> None:
        self.name = name
        self.waited = 0
        self.wait_total = 0.0
        self.stale = 0

    def row(self, cache: Cache, total: int) -> tuple:
        mean_wait = self.wait_total / self.waited if self.waited else 0.0
        return (
            self.name,
            cache.recomputes,
            cache.max_concurrent,
            self.waited,
            mean_wait,
            self.stale,
            100.0 * (total - self.waited) / total,
        )


def simulate(name: str, times: list[float]) -> tuple:
    cache = Cache()
    out = Result(name)
    rng = random.Random(SEED + 1)

    for now in times:
        cache.settle(now)

        if not cache.filled and not cache.inflight:
            # 첫 요청은 어느 방식이든 직접 채우고 기다린다.
            end = cache.start(now)
            out.waited += 1
            out.wait_total += end - now
            continue

        expired = now >= cache.expiry

        if name == "아무 대책 없음":
            if expired:
                end = cache.start(now)
                out.waited += 1
                out.wait_total += end - now

        elif name == "뮤텍스 락":
            if expired:
                if cache.inflight:
                    end = min(cache.inflight)
                else:
                    end = cache.start(now)
                out.waited += 1
                out.wait_total += end - now

        elif name == "확률적 조기 만료 (XFetch)":
            # Time() - Δ·β·log(rand()) >= expiry 이면 미리 다시 만든다.
            early = now - RECOMPUTE_MS * BETA * math.log(rng.random()) >= cache.expiry
            if early and not cache.inflight:
                cache.start(now)
                # 아직 만료 전이므로 지금 값을 그대로 돌려준다. 기다리지 않는다.
            elif expired:
                if cache.inflight:
                    end = min(cache.inflight)
                else:
                    end = cache.start(now)
                out.waited += 1
                out.wait_total += end - now

        elif name == "백그라운드 갱신 (stale-while-revalidate)":
            if expired:
                if not cache.inflight:
                    cache.start(now)
                out.stale += 1   # 낡은 값을 그대로 돌려주고 기다리지 않는다

    return out.row(cache, len(times))


def main() -> None:
    times = arrival_times()
    print(f"요청 {len(times)}건 · {DURATION_MS // 1000}초 · 평균 간격 {MEAN_INTERVAL_MS:.0f}ms")
    print(f"TTL {TTL_MS // 1000}초 · 재계산 {RECOMPUTE_MS}ms · β={BETA} · 시드 {SEED}")
    print()

    header = ("방식", "재계산", "최대동시", "대기요청", "평균대기ms", "낡은값", "무대기%")
    rows = [
        simulate(name, times)
        for name in (
            "아무 대책 없음",
            "뮤텍스 락",
            "확률적 조기 만료 (XFetch)",
            "백그라운드 갱신 (stale-while-revalidate)",
        )
    ]

    width = max(len(r[0]) for r in rows + [header])
    print(f"{header[0]:<{width}} {header[1]:>7} {header[2]:>9} {header[3]:>9} "
          f"{header[4]:>11} {header[5]:>7} {header[6]:>8}")
    print("-" * (width + 56))
    for r in rows:
        print(f"{r[0]:<{width}} {r[1]:>7} {r[2]:>9} {r[3]:>9} "
              f"{r[4]:>11.1f} {r[5]:>7} {r[6]:>7.2f}%")


if __name__ == "__main__":
    main()
