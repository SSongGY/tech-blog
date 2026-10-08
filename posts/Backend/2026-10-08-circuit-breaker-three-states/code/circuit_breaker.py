"""서킷 브레이커의 세 상태가 각각 어떤 장애를 막는지 가짜 시계 위에서 확인한다.

요청은 0.1초마다 한 건씩 들어온다(초당 10건). 하류 서비스의 동작은 시나리오가 정한다.
도착과 완료를 시간순 이벤트로 처리하므로, 타임아웃으로 끝나는 호출의 결과가
2초 뒤에야 브레이커에 들어오는 지연까지 그대로 드러난다. 난수는 쓰지 않는다.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field

REQUEST_INTERVAL = 0.1     # 초당 10건
OK_LATENCY = 0.05          # 정상 응답 시간
TIMEOUT = 2.0              # 장애 중 호출이 붙잡히는 시간 (호출자 쪽 타임아웃)
FAST_FAIL_LATENCY = 0.05   # 과부하 거절(503)처럼 바로 돌아오는 실패


class CircuitBreaker:
    """Azure 아키텍처 센터의 서킷 브레이커 패턴 설명을 그대로 옮긴 최소 구현.

    - Closed: 실패를 센다. 일정 시간 안에 임계값에 닿으면 Open.
      실패 카운터는 window 초마다 0으로 돌아간다 (window=None 이면 돌아가지 않는다)
    - Open: 호출을 바로 거절한다. open_timeout 이 지나면 Half-Open
    - Half-Open: 시험 호출을 trial_limit 건까지만 동시에 내보낸다.
      연속 성공이 success_threshold 에 닿으면 Closed, 한 건이라도 실패하면 Open
    """

    def __init__(self, failure_threshold: int, window: float | None,
                 open_timeout: float, trial_limit: int, success_threshold: int,
                 use_half_open: bool = True) -> None:
        self.failure_threshold = failure_threshold
        self.window = window
        self.open_timeout = open_timeout
        self.trial_limit = trial_limit
        self.success_threshold = success_threshold
        self.use_half_open = use_half_open
        self.state = "closed"
        self.failures = 0
        self.window_start = 0.0
        self.opened_at = 0.0
        self.trials_in_flight = 0
        self.trial_successes = 0
        self.log: list[str] = []

    def _move(self, now: float, new_state: str, reason: str) -> None:
        self.log.append(f"{now:6.2f}s  {self.state:>9} -> {new_state:<9} {reason}")
        self.state = new_state

    def allow(self, now: float) -> bool:
        if self.state == "open" and now - self.opened_at >= self.open_timeout:
            if self.use_half_open:
                self._move(now, "half-open", "타임아웃 경과")
                self.trials_in_flight = 0
                self.trial_successes = 0
            else:
                # 비교용: 시험 단계 없이 곧바로 모든 요청을 다시 보낸다
                self._move(now, "closed", "타임아웃 경과 (시험 없이)")
                self.failures = 0
                self.window_start = now
        if self.state == "open":
            return False
        if self.state == "half-open":
            if self.trials_in_flight >= self.trial_limit:
                return False
            self.trials_in_flight += 1
        return True

    def record(self, now: float, success: bool, was_trial: bool) -> None:
        if was_trial:
            self.trials_in_flight -= 1
            if self.state != "half-open":
                return
            if success:
                self.trial_successes += 1
                if self.trial_successes >= self.success_threshold:
                    self._move(now, "closed", f"시험 {self.trial_successes}건 연속 성공")
                    self.failures = 0
                    self.window_start = now
            else:
                self._trip(now, "시험 호출 실패")
            return
        if self.state != "closed" or success:
            return
        if self.window is not None and now - self.window_start >= self.window:
            # 카운터를 주기적으로 0으로 돌린다 — 드문 실패가 쌓여 열리지 않게
            self.failures = 0
            self.window_start = now
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self._trip(now, f"실패 {self.failures}건")

    def _trip(self, now: float, reason: str) -> None:
        self._move(now, "open", reason)
        self.opened_at = now


@dataclass
class Stats:
    attempted: int = 0          # 하류까지 간 호출
    rejected: int = 0           # 브레이커가 바로 거절
    succeeded: int = 0
    failed: int = 0
    held_seconds: float = 0.0   # 실패한 호출이 스레드를 붙잡은 시간의 합
    max_in_flight: int = 0
    failed_by_phase: dict = field(default_factory=dict)
    attempted_by_phase: dict = field(default_factory=dict)


def simulate(service, breaker: CircuitBreaker | None, duration: float,
             phase_of) -> Stats:
    stats = Stats()
    events: list[tuple] = []
    seq = 0
    for i in range(int(round(duration / REQUEST_INTERVAL))):
        heapq.heappush(events, (round(i * REQUEST_INTERVAL, 2), 1, seq, "arrive", None))
        seq += 1
    in_flight = 0
    while events:
        now, _, _, kind, payload = heapq.heappop(events)
        if kind == "arrive":
            if breaker is not None and not breaker.allow(now):
                stats.rejected += 1
                continue
            was_trial = breaker is not None and breaker.state == "half-open"
            success, latency = service(now, in_flight)
            in_flight += 1
            stats.max_in_flight = max(stats.max_in_flight, in_flight)
            stats.attempted += 1
            phase = phase_of(now)
            stats.attempted_by_phase[phase] = stats.attempted_by_phase.get(phase, 0) + 1
            # 완료 이벤트를 도착보다 먼저 처리하도록 우선순위 0
            heapq.heappush(events, (round(now + latency, 2), 0, seq, "done",
                                    (success, latency, was_trial, phase)))
            seq += 1
        else:
            success, latency, was_trial, phase = payload
            in_flight -= 1
            if success:
                stats.succeeded += 1
            else:
                stats.failed += 1
                stats.held_seconds += latency
                stats.failed_by_phase[phase] = stats.failed_by_phase.get(phase, 0) + 1
            if breaker is not None:
                breaker.record(now, success, was_trial)
    return stats


def sporadic_service(now: float, in_flight: int) -> tuple[bool, float]:
    # 3초에 한 번꼴로 실패하는 간헐 오류. 서비스 자체는 살아 있다
    tick = int(round(now / REQUEST_INTERVAL))
    return (tick % 30 != 15, OK_LATENCY)


def outage_service(now: float, in_flight: int) -> tuple[bool, float]:
    # 10~40초: 응답 없음(타임아웃). 40~50초: 막 살아나 동시 2건까지만 처리. 50초~: 정상
    if 10 <= now < 40:
        return (False, TIMEOUT)
    if 40 <= now < 50 and in_flight >= 2:
        return (False, FAST_FAIL_LATENCY)
    return (True, OK_LATENCY)


def sporadic_phase(now: float) -> str:
    return "정상"


def outage_phase(now: float) -> str:
    if now < 10:
        return "정상"
    if now < 40:
        return "장애"
    if now < 50:
        return "회복 중"
    return "회복 후"


def print_stats(title: str, stats: Stats, breaker: CircuitBreaker | None) -> None:
    print(f"\n-- {title}")
    print(f"   하류 호출 {stats.attempted} / 즉시 거절 {stats.rejected} / "
          f"성공 {stats.succeeded} / 실패 {stats.failed}")
    print(f"   실패 호출이 붙잡은 시간 합 {stats.held_seconds:.1f}초 / "
          f"동시 진행 최대 {stats.max_in_flight}건")
    phases = ["정상", "장애", "회복 중", "회복 후"]
    if any(p in stats.attempted_by_phase for p in phases[1:]):
        print("   구간별 하류 호출(실패): " + ", ".join(
            f"{p} {stats.attempted_by_phase.get(p, 0)}({stats.failed_by_phase.get(p, 0)})"
            for p in phases))
    if breaker is not None:
        print(f"   상태 전이 {len(breaker.log)}회")
        for line in breaker.log:
            print("     " + line)


def main() -> None:
    print("요청: 0.1초마다 1건(초당 10건), 정상 응답 0.05초, 장애 중 타임아웃 2초")

    print("\n==== 1. Closed — 드문 실패로는 열리지 않아야 한다 (60초, 3초마다 실패 1건) ====")
    breaker = CircuitBreaker(5, window=10.0, open_timeout=5.0,
                             trial_limit=1, success_threshold=3)
    print_stats("1-1. 실패 카운터를 10초마다 0으로 (임계 5건)",
                simulate(sporadic_service, breaker, 60, sporadic_phase), breaker)
    breaker = CircuitBreaker(5, window=None, open_timeout=5.0,
                             trial_limit=1, success_threshold=3)
    print_stats("1-2. 실패 카운터를 돌리지 않음 (임계 5건)",
                simulate(sporadic_service, breaker, 60, sporadic_phase), breaker)

    print("\n==== 2. Open — 장애 중 호출이 스레드를 붙잡지 않게 (80초) ====")
    print("하류: 0~10초 정상, 10~40초 무응답, 40~50초 동시 2건까지만, 50초~ 정상")
    print_stats("2-1. 브레이커 없음", simulate(outage_service, None, 80, outage_phase), None)
    breaker = CircuitBreaker(5, window=10.0, open_timeout=5.0,
                             trial_limit=1, success_threshold=3)
    print_stats("2-2. 브레이커 (임계 5건/10초, Open 5초, 시험 1건씩 3건 연속 성공)",
                simulate(outage_service, breaker, 80, outage_phase), breaker)

    print("\n==== 3. Half-Open — 막 살아난 서비스에 한꺼번에 몰리지 않게 ====")
    breaker = CircuitBreaker(5, window=10.0, open_timeout=5.0,
                             trial_limit=1, success_threshold=3, use_half_open=False)
    print_stats("3-1. Half-Open 없이 Open 5초 뒤 바로 Closed",
                simulate(outage_service, breaker, 80, outage_phase), breaker)


if __name__ == "__main__":
    main()
