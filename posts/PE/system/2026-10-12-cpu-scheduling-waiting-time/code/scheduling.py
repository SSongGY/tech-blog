"""CPU 스케줄링 알고리즘 다섯 가지를 1단위 시간씩 흉내 내어 대기·반환·응답 시간을 계산한다.

교재(Silberschatz 10판 5장 슬라이드)의 예제를 그대로 넣어 교재 값과 맞는지 검산하고,
같은 작업 묶음에 다섯 알고리즘을 모두 돌려 나란히 비교한다.

동률 규칙 (교재가 정하지 않은 부분이라 여기서 정한다):
- 고르는 기준 값이 같으면 먼저 도착한 것, 도착 시각도 같으면 목록에 먼저 적힌 것
  (같은 시각에 들어온 프로세스의 큐 순서를 목록 순서로 나타낸다)
- RR 에서 할당량이 끝난 순간 새 프로세스가 도착하면, 새 프로세스를 먼저 큐 뒤에 넣는다
"""

from collections import deque
from dataclasses import dataclass
from fractions import Fraction
from itertools import permutations


@dataclass(frozen=True)
class Process:
    name: str
    arrival: int
    burst: int
    priority: int = 0  # 작을수록 높다 (교재 관례)


def merge_ticks(ticks: list[str]) -> list[tuple[str, int, int]]:
    """1단위 실행 기록을 (이름, 시작, 끝) 구간으로 묶는다. '-' 는 CPU 유휴."""
    segments = []
    for t, name in enumerate(ticks):
        if segments and segments[-1][0] == name:
            segments[-1] = (name, segments[-1][1], t + 1)
        else:
            segments.append((name, t, t + 1))
    return segments


def simulate(procs: list[Process], key, preemptive: bool) -> list[str]:
    """준비 큐에서 key 가 가장 작은 프로세스를 고른다. preemptive 면 매 단위마다 다시 고른다."""
    remaining = {p.name: p.burst for p in procs}
    ticks, current, t = [], None, 0
    while any(remaining.values()):
        ready = [p for p in procs if p.arrival <= t and remaining[p.name] > 0]
        if current is None or preemptive:
            current = min(ready, key=lambda p: (key(p, remaining), p.arrival, procs.index(p)),
                          default=None)
        if current is None:
            ticks.append("-")
        else:
            ticks.append(current.name)
            remaining[current.name] -= 1
            if remaining[current.name] == 0:
                current = None
        t += 1
    return ticks


def round_robin(procs: list[Process], quantum: int) -> list[str]:
    remaining = {p.name: p.burst for p in procs}
    pending = sorted(procs, key=lambda p: p.arrival)  # 안정 정렬이라 동시 도착은 목록 순서
    queue, ticks, current, used, t = deque(), [], None, 0, 0
    while any(remaining.values()):
        while pending and pending[0].arrival <= t:
            queue.append(pending.pop(0))
        if current is not None and used == quantum:
            queue.append(current)  # 같은 시각 도착한 프로세스보다 뒤에 선다
            current = None
        if current is None and queue:
            current, used = queue.popleft(), 0
        if current is None:
            ticks.append("-")
        else:
            ticks.append(current.name)
            remaining[current.name] -= 1
            used += 1
            if remaining[current.name] == 0:
                current = None
        t += 1
    return ticks


ALGORITHMS = {
    "FCFS": lambda ps: simulate(ps, lambda p, r: p.arrival, preemptive=False),
    "SJF": lambda ps: simulate(ps, lambda p, r: p.burst, preemptive=False),
    "SRTF": lambda ps: simulate(ps, lambda p, r: r[p.name], preemptive=True),
    "Priority": lambda ps: simulate(ps, lambda p, r: p.priority, preemptive=False),
    "RR(q=4)": lambda ps: round_robin(ps, 4),
}


def measure(procs: list[Process], ticks: list[str]) -> dict[str, dict[str, int]]:
    result = {}
    for p in procs:
        first = ticks.index(p.name)
        finish = len(ticks) - ticks[::-1].index(p.name)
        turnaround = finish - p.arrival
        result[p.name] = {"first": first, "finish": finish, "turnaround": turnaround,
                          "waiting": turnaround - p.burst, "response": first - p.arrival}
    return result


def average(metrics: dict, field: str) -> str:
    value = Fraction(sum(m[field] for m in metrics.values()), len(metrics))
    return f"{value} = {float(value):.2f}" if value.denominator != 1 else str(value)


def gantt(ticks: list[str]) -> str:
    return " ".join(f"[{n} {s}-{e}]" for n, s, e in merge_ticks(ticks))


def report(title: str, procs: list[Process], ticks: list[str]) -> dict:
    metrics = measure(procs, ticks)
    print(f"\n-- {title}")
    print(f"   간트: {gantt(ticks)}")
    print("   프로세스 | 도착 | 실행 | 첫 실행 | 종료 | 반환 | 대기 | 응답")
    for p in procs:
        m = metrics[p.name]
        print(f"   {p.name:8s} | {p.arrival:4d} | {p.burst:4d} | {m['first']:7d} | "
              f"{m['finish']:4d} | {m['turnaround']:4d} | {m['waiting']:4d} | {m['response']:4d}")
    print(f"   평균 대기 {average(metrics, 'waiting')} · 평균 반환 "
          f"{average(metrics, 'turnaround')} · 평균 응답 {average(metrics, 'response')}")
    return metrics


def main() -> None:
    print("== 1. 교재 예제 검산 ==")
    fcfs = [Process("P1", 0, 24), Process("P2", 0, 3), Process("P3", 0, 3)]
    report("1-1. FCFS, 도착 순서 P1·P2·P3 (교재 평균 대기 17)", fcfs, ALGORITHMS["FCFS"](fcfs))
    reordered = [Process("P2", 0, 3), Process("P3", 0, 3), Process("P1", 0, 24)]
    report("1-2. FCFS, 도착 순서 P2·P3·P1 (교재 평균 대기 3)", reordered,
           ALGORITHMS["FCFS"](reordered))

    sjf_at_zero = [Process("P1", 0, 6), Process("P2", 0, 8), Process("P3", 0, 7),
                   Process("P4", 0, 3)]
    report("1-3. SJF, 모두 0에 도착 (교재 평균 대기 7)", sjf_at_zero,
           ALGORITHMS["SJF"](sjf_at_zero))
    sjf_table = [Process("P1", 0, 6), Process("P2", 2, 8), Process("P3", 4, 7),
                 Process("P4", 5, 3)]
    report("1-4. SJF, 슬라이드 표의 도착 시각 0·2·4·5 를 그대로 쓰면", sjf_table,
           ALGORITHMS["SJF"](sjf_table))

    srtf = [Process("P1", 0, 8), Process("P2", 1, 4), Process("P3", 2, 9),
            Process("P4", 3, 5)]
    report("1-5. SRTF (교재 평균 대기 6.5)", srtf, ALGORITHMS["SRTF"](srtf))
    report("1-6. RR q=4 (교재 평균 반환 15.7)", fcfs, ALGORITHMS["RR(q=4)"](fcfs))

    prio = [Process("P1", 0, 10, 3), Process("P2", 0, 1, 1), Process("P3", 0, 2, 4),
            Process("P4", 0, 1, 5), Process("P5", 0, 5, 2)]
    report("1-7. 비선점 우선순위 (교재 평균 대기 8.2)", prio, ALGORITHMS["Priority"](prio))

    print("\n== 2. SJF 가 평균 대기 최소인지 — 1-3 의 네 프로세스로 24가지 순서를 전부 ==")
    totals = {}
    for order in permutations(sjf_at_zero):
        clock, waits = 0, 0
        for p in order:
            waits += clock
            clock += p.burst
        totals["".join(p.name[1] for p in order)] = Fraction(waits, len(order))
    best = min(totals.values())
    print(f"   최소 평균 대기 {best} · 그 순서 {[k for k, v in totals.items() if v == best]}")
    print(f"   최대 평균 대기 {max(totals.values())} · 순서 수 {len(totals)}")

    print("\n== 3. 같은 작업 묶음(1-5)에 다섯 알고리즘 ==")
    srtf_prio = [Process(p.name, p.arrival, p.burst, prio) for p, prio
                 in zip(srtf, (3, 1, 4, 2))]
    print("   우선순위는 P1 3, P2 1, P3 4, P4 2 로 붙였다 (작을수록 높음)")
    print("   알고리즘 | 평균 대기 | 평균 반환 | 평균 응답 | 문맥 교환")
    for name, run in ALGORITHMS.items():
        ticks = run(srtf_prio)
        m = measure(srtf_prio, ticks)
        switches = len(merge_ticks(ticks)) - 1
        print(f"   {name:8s} | {average(m, 'waiting'):9s} | {average(m, 'turnaround'):9s} | "
              f"{average(m, 'response'):9s} | {switches}")

    print("\n== 4. RR 할당량에 따른 변화 — 1-1 의 P1 24·P2 3·P3 3 ==")
    print("   q  | 평균 반환 | 평균 대기 | 평균 응답 | 문맥 교환")
    for q in (1, 2, 3, 4, 5, 6, 8, 12, 24):
        ticks = round_robin(fcfs, q)
        m = measure(fcfs, ticks)
        print(f"   {q:2d} | {average(m, 'turnaround'):9s} | {average(m, 'waiting'):9s} | "
              f"{average(m, 'response'):9s} | {len(merge_ticks(ticks)) - 1}")

    print("\n== 5. 다음 실행 시간 예측 — 지수 평균, tau0 = 10, alpha = 1/2 ==")
    tau, alpha = Fraction(10), Fraction(1, 2)
    history = []
    for burst in (6, 4, 6, 4, 13, 13, 13):
        history.append((burst, tau))
        tau = alpha * burst + (1 - alpha) * tau
    print("   실제 t  : " + " ".join(f"{b:>4}" for b, _ in history))
    print("   예측 tau: " + " ".join(f"{str(t):>4}" for _, t in history) + f"  (다음 {tau})")


if __name__ == "__main__":
    main()
