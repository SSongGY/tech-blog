"""페이지 교체 알고리즘 4가지(OPT·FIFO·LRU·Clock)를 같은 참조열로 돌려 교재 값을 검산한다.

교재 예제 두 개(Silberschatz, OSTEP)의 부재 횟수를 다시 세고,
벨레이디의 이상현상이 FIFO 에서만 생기는 이유를 "프레임 내용의 포함 관계" 로 확인한다.
"""

import random
from collections import deque

SILBERSCHATZ_REFS = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]
OSTEP_REFS = [0, 1, 2, 0, 1, 3, 0, 3, 1, 2, 1]
BELADY_REFS = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]


def simulate_fifo(refs: list[int], frame_count: int) -> list[tuple[int, bool, set[int]]]:
    queue: deque[int] = deque()
    trace = []
    for page in refs:
        fault = page not in queue
        if fault:
            if len(queue) == frame_count:
                queue.popleft()
            queue.append(page)
        trace.append((page, fault, set(queue)))
    return trace


def simulate_lru(refs: list[int], frame_count: int) -> list[tuple[int, bool, set[int]]]:
    # 리스트 앞쪽이 가장 오래전에 쓴 페이지다
    order: list[int] = []
    trace = []
    for page in refs:
        fault = page not in order
        if fault:
            if len(order) == frame_count:
                order.pop(0)
        else:
            order.remove(page)
        order.append(page)
        trace.append((page, fault, set(order)))
    return trace


def simulate_opt(refs: list[int], frame_count: int) -> list[tuple[int, bool, set[int]]]:
    frames: list[int] = []
    trace = []
    for position, page in enumerate(refs):
        fault = page not in frames
        if fault:
            if len(frames) == frame_count:
                future = refs[position + 1:]

                def next_use(candidate: int) -> int:
                    # 다시 안 쓰이는 페이지는 무한대 거리로 본다
                    return future.index(candidate) if candidate in future else len(refs)

                # 거리가 같으면 먼저 들어온 쪽을 고른다 — 교재가 정하지 않은 동률 규칙
                victim = max(frames, key=next_use)
                frames.remove(victim)
            frames.append(page)
        trace.append((page, fault, set(frames)))
    return trace


def simulate_clock(refs: list[int], frame_count: int) -> list[tuple[int, bool, set[int]]]:
    frames: list[int | None] = [None] * frame_count
    use_bits = [0] * frame_count
    hand = 0
    trace = []
    for page in refs:
        if page in frames:
            use_bits[frames.index(page)] = 1
            trace.append((page, False, {p for p in frames if p is not None}))
            continue
        # 사용 비트가 1이면 0으로 지우고 넘어간다 — 두 번째 기회
        while frames[hand] is not None and use_bits[hand] == 1:
            use_bits[hand] = 0
            hand = (hand + 1) % frame_count
        frames[hand] = page
        use_bits[hand] = 1
        hand = (hand + 1) % frame_count
        trace.append((page, True, {p for p in frames if p is not None}))
    return trace


ALGORITHMS = {
    "OPT": simulate_opt,
    "FIFO": simulate_fifo,
    "LRU": simulate_lru,
    "Clock": simulate_clock,
}


def count_faults(trace: list[tuple[int, bool, set[int]]]) -> int:
    return sum(1 for _, fault, _ in trace if fault)


def print_trace(title: str, trace: list[tuple[int, bool, set[int]]]) -> None:
    print(f"\n  {title}")
    print("    참조 | 부재 | 프레임 내용")
    for page, fault, frames in trace:
        mark = "F" if fault else "."
        print(f"    {page:>4} |  {mark}   | {sorted(frames)}")
    print(f"    부재 {count_faults(trace)}회")


def section(title: str) -> None:
    print("\n" + "=" * 64)
    print(title)
    print("=" * 64)


def main() -> None:
    section("1. Silberschatz 참조열, 프레임 3개 — 교재 값 FIFO 15 · OPT 9 · LRU 12")
    print(f"  참조열 {SILBERSCHATZ_REFS} ({len(SILBERSCHATZ_REFS)}회)")
    for name, simulate in ALGORITHMS.items():
        faults = count_faults(simulate(SILBERSCHATZ_REFS, 3))
        print(f"  {name:<5} 부재 {faults:>2}회")

    section("2. OSTEP 참조열, 프레임 3개 — 교재 값 OPT 6적중 · FIFO 적중률 36.4%")
    print(f"  참조열 {OSTEP_REFS} ({len(OSTEP_REFS)}회)")
    compulsory = len(set(OSTEP_REFS))
    for name, simulate in ALGORITHMS.items():
        faults = count_faults(simulate(OSTEP_REFS, 3))
        hits = len(OSTEP_REFS) - faults
        hit_rate = hits / len(OSTEP_REFS) * 100
        # 강제 부재(처음 참조)를 뺀 적중률 — OSTEP 의 "modulo compulsory misses"
        warm_rate = hits / (len(OSTEP_REFS) - compulsory) * 100
        print(f"  {name:<5} 적중 {hits} · 부재 {faults} · 적중률 {hit_rate:.1f}% · 강제 부재 제외 {warm_rate:.1f}%")

    section("3. 벨레이디 참조열 — 프레임 수 1~6 에 따른 부재 횟수")
    print(f"  참조열 {BELADY_REFS} ({len(BELADY_REFS)}회)")
    print("  프레임 | " + " | ".join(f"{name:>5}" for name in ALGORITHMS))
    for frame_count in range(1, 7):
        row = [count_faults(simulate(BELADY_REFS, frame_count)) for simulate in ALGORITHMS.values()]
        print(f"  {frame_count:>6} | " + " | ".join(f"{value:>5}" for value in row))

    section("4. FIFO 프레임 3개와 4개의 추적")
    fifo3 = simulate_fifo(BELADY_REFS, 3)
    fifo4 = simulate_fifo(BELADY_REFS, 4)
    print_trace("FIFO, 프레임 3개", fifo3)
    print_trace("FIFO, 프레임 4개", fifo4)

    section("5. 포함 관계(스택 성질) — 프레임 N개의 내용이 N+1개의 내용에 늘 들어 있는가")
    for name, simulate in ALGORITHMS.items():
        broken = []
        for frame_count in range(1, 6):
            small = simulate(BELADY_REFS, frame_count)
            large = simulate(BELADY_REFS, frame_count + 1)
            for step, ((_, _, small_set), (_, _, large_set)) in enumerate(zip(small, large), start=1):
                if not small_set <= large_set:
                    broken.append((frame_count, step, sorted(small_set), sorted(large_set)))
        if broken:
            frame_count, step, small_set, large_set = broken[0]
            print(f"  {name:<5} 깨짐 {len(broken)}곳 · 첫 사례: N={frame_count}, {step}번째 참조 뒤 "
                  f"{small_set} ⊄ {large_set}")
        else:
            print(f"  {name:<5} 깨짐 없음")

    search_anomaly("6. 무작위 참조열 20,000개 — 길이 12, 페이지 1~5", length=12, page_count=5)
    search_anomaly("7. 무작위 참조열 20,000개 — 길이 30, 페이지 1~8", length=30, page_count=8)


def search_anomaly(title: str, length: int, page_count: int, trials: int = 20_000) -> None:
    section(f"{title} (seed 42)")
    rng = random.Random(42)
    anomaly_strings = {name: 0 for name in ALGORITHMS}
    first_example: dict[str, tuple[list[int], list[int]]] = {}
    for _ in range(trials):
        refs = [rng.randint(1, page_count) for _ in range(length)]
        for name, simulate in ALGORITHMS.items():
            faults = [count_faults(simulate(refs, n)) for n in range(1, page_count + 1)]
            if any(faults[i + 1] > faults[i] for i in range(len(faults) - 1)):
                anomaly_strings[name] += 1
                first_example.setdefault(name, (refs, faults))
    print(f"  프레임을 1~{page_count}개로 늘려 가며 부재가 한 번이라도 늘면 이상현상으로 센다")
    for name, count in anomaly_strings.items():
        print(f"  {name:<5} {count:>4}개 / {trials} ({count / trials * 100:.2f}%)")
    for name, (refs, faults) in first_example.items():
        print(f"  {name} 첫 사례 참조열 {refs}")
        print(f"        프레임 1~{page_count}개 부재 {faults}")


if __name__ == "__main__":
    main()
