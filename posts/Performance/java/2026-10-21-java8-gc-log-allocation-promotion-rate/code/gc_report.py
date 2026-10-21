"""Java 8 형식의 GC 로그에서 할당률·승격률과 힙 역산 값을 뽑는다.

Java 8 의 -XX:+PrintGCDetails 한 줄은 이렇게 생겼다.

    2026-10-22T08:33:21.880+0900: 1.794: [GC (Allocation Failure)
      [PSYoungGen: 64195K->768K(64512K)] 256109K->193449K(523264K), 0.0004713 secs]

  - PSYoungGen 의 before->after(capacity) 는 Young 영역
  - 그 뒤 before->after(capacity) 는 힙 전체
  - 둘을 빼면 Old 영역이 나온다. 로그에 Old 가 따로 안 적히므로 이 뺄셈이 전부다

여기서 두 지표가 나온다.

  할당률 = Σ(이번 GC 직전 Young − 지난 GC 직후 Young) / 경과 시간
  승격률 = Σ(이번 GC 직후 Old − 이번 GC 직전 Old) / 경과 시간

할당률은 "초당 몇 MiB 를 새로 만드는가"이고, 승격률은 "그중 몇 MiB 가 Old 로
넘어가는가"다. 힙 설정을 역산하는 데 쓰는 것은 후자다.
"""

from __future__ import annotations

import re
import sys

KIB = 1024
MIB = 1024 * 1024

# 타임스탬프 뒤의 가동 시각, GC 종류, Young/전체의 before->after(capacity), 정지 시간
GC_LINE = re.compile(
    r"(?P<uptime>\d+\.\d+): \[(?P<kind>Full GC|GC) \((?P<cause>[^)]*)\).*?"
    r"PSYoungGen: (?P<young_before>\d+)K->(?P<young_after>\d+)K\((?P<young_cap>\d+)K\)"
    r".*?(?P<heap_before>\d+)K->(?P<heap_after>\d+)K\((?P<heap_cap>\d+)K\), "
    r"(?P<pause>\d+\.\d+) secs\]"
)


class Event:
    def __init__(self, match: re.Match) -> None:
        self.uptime = float(match["uptime"])
        self.full = match["kind"] == "Full GC"
        self.cause = match["cause"]
        self.young_before = int(match["young_before"]) * KIB
        self.young_after = int(match["young_after"]) * KIB
        self.young_cap = int(match["young_cap"]) * KIB
        self.heap_before = int(match["heap_before"]) * KIB
        self.heap_after = int(match["heap_after"]) * KIB
        self.heap_cap = int(match["heap_cap"]) * KIB
        self.pause = float(match["pause"])

    @property
    def old_before(self) -> int:
        return self.heap_before - self.young_before

    @property
    def old_after(self) -> int:
        return self.heap_after - self.young_after


def parse(path: str) -> list[Event]:
    events = []
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            match = GC_LINE.search(line)
            if match:
                events.append(Event(match))
    return events


def report(path: str) -> None:
    events = parse(path)
    if len(events) < 2:
        print(f"[{path}] GC 이벤트가 2건 미만이라 비율을 낼 수 없다")
        return

    minors = [e for e in events if not e.full]
    fulls = [e for e in events if e.full]
    span = events[-1].uptime - events[0].uptime

    allocated = 0
    for previous, current in zip(events, events[1:]):
        # 지난 GC 가 Young 을 비운 자리에서 이번 GC 직전까지 채운 양이다.
        allocated += max(0, current.young_before - previous.young_after)

    promoted = sum(max(0, e.old_after - e.old_before) for e in events)
    pause_total = sum(e.pause for e in events)

    print(f"[{path}]")
    print(f"  측정 구간            : {events[0].uptime:.3f}초 ~ {events[-1].uptime:.3f}초 "
          f"({span:.3f}초)")
    print(f"  Young GC             : {len(minors)}회 · Full GC {len(fulls)}회")
    print(f"  Young 영역 용량      : {events[-1].young_cap / MIB:,.1f} MiB")
    print(f"  힙 전체 용량         : {events[-1].heap_cap / MIB:,.1f} MiB")
    print(f"  정지 시간 합계       : {pause_total * 1000:,.1f} ms "
          f"(구간의 {pause_total / span * 100:.2f}%)")
    if minors:
        pauses = sorted(e.pause for e in minors)
        print(f"  Young GC 정지        : 평균 {sum(pauses) / len(pauses) * 1000:.2f} ms · "
              f"최대 {pauses[-1] * 1000:.2f} ms")
    if fulls:
        pauses = sorted(e.pause for e in fulls)
        print(f"  Full GC 정지         : 평균 {sum(pauses) / len(pauses) * 1000:.2f} ms · "
              f"최대 {pauses[-1] * 1000:.2f} ms")

    allocation_rate = allocated / span / MIB
    promotion_rate = promoted / span / MIB
    print(f"\n  할당률               : {allocation_rate:,.1f} MiB/s")
    print(f"  승격률               : {promotion_rate:,.2f} MiB/s")
    if allocation_rate:
        print(f"  승격 비율            : {promotion_rate / allocation_rate * 100:.3f}% "
              f"(할당한 것 중 Old 로 넘어간 몫)")
    print(f"  Young GC 간격        : {span / max(1, len(minors)) * 1000:,.1f} ms")

    # 역산 — Old 의 남은 자리를 승격률로 나누면 다음 Full GC 까지의 시간이 나온다.
    last = events[-1]
    old_capacity = last.heap_cap - last.young_cap
    old_free = old_capacity - last.old_after
    print(f"\n  역산 — Old 용량 {old_capacity / MIB:,.1f} MiB 중 "
          f"{last.old_after / MIB:,.1f} MiB 사용")
    if promotion_rate > 0:
        print(f"  남은 {old_free / MIB:,.1f} MiB 를 지금 승격률로 채우는 데 "
              f"{old_free / MIB / promotion_rate:,.1f}초")
    else:
        print("  승격이 없다 — 이 부하에서는 Old 가 차지 않는다")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("사용법: python gc_report.py <gc 로그 경로> [...]")
        return 2
    for path in argv[1:]:
        report(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
