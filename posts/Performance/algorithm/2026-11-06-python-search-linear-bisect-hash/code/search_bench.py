"""list 선형 탐색, bisect 이진 탐색, set·dict 해시 탐색의 조회 시간을 크기별로 잰다.

1) 원소 수를 10배씩 늘리며 없는 키를 찾는 시간 (선형 탐색의 최악 경우)
2) 같은 크기에서 키 위치에 따라 list 가 얼마나 달라지는지
3) 해시 값이 전부 같은 키로 dict 를 채울 때 삽입 시간이 어떻게 늘어나는지
난수는 시드를 고정한다. 시간은 환경마다 다르므로 절대값이 아니라 기울기를 본다.
"""
import platform
import random
import statistics
import sys
import time
from bisect import bisect_left

SIZES = [1_000, 10_000, 100_000, 1_000_000]
PROBE_COUNT = 50
REPEAT = 5
SEED = 20261106


def median_ns_per_call(func, probes) -> float:
    """probes 전체를 한 번 도는 시간을 여러 번 재서 중앙값을 호출 한 번당 ns 로 돌려준다."""
    samples = []
    for _ in range(REPEAT):
        start = time.perf_counter_ns()
        for key in probes:
            func(key)
        samples.append((time.perf_counter_ns() - start) / len(probes))
    return statistics.median(samples)


def bisect_contains(sorted_list, key) -> bool:
    idx = bisect_left(sorted_list, key)
    return idx < len(sorted_list) and sorted_list[idx] == key


def bench_by_size() -> None:
    print("\n### 1. 없는 키를 찾는 시간 (호출 한 번당, ns)")
    print(f"  {'n':>9} | {'list in':>12} | {'bisect':>8} | {'set':>7} | {'dict':>7}")
    print(f"  {'-' * 9}-+-{'-' * 12}-+-{'-' * 8}-+-{'-' * 7}-+-{'-' * 7}")
    rng = random.Random(SEED)
    for size in SIZES:
        data = list(range(0, size * 2, 2))          # 짝수만 → 홀수 키는 반드시 없다
        rng.shuffle(data)
        sorted_data = sorted(data)
        as_set = set(data)
        as_dict = dict.fromkeys(data)
        probes = [rng.randrange(1, size * 2, 2) for _ in range(PROBE_COUNT)]
        list_ns = median_ns_per_call(lambda k: k in data, probes)
        bisect_ns = median_ns_per_call(lambda k: bisect_contains(sorted_data, k), probes)
        set_ns = median_ns_per_call(lambda k: k in as_set, probes)
        dict_ns = median_ns_per_call(lambda k: k in as_dict, probes)
        print(f"  {size:>9,} | {list_ns:>12,.0f} | {bisect_ns:>8,.0f} | "
              f"{set_ns:>7,.0f} | {dict_ns:>7,.0f}")


def bench_by_position() -> None:
    print("\n### 2. list 에서 키 위치별 시간 (n = 100,000, 호출 한 번당, ns)")
    size = 100_000
    data = list(range(size))
    for label, key in [("맨 앞", 0), ("가운데", size // 2), ("맨 뒤", size - 1),
                       ("없음", -1)]:
        ns = median_ns_per_call(lambda k: k in data, [key] * PROBE_COUNT)
        print(f"  {label:<6} | {ns:>10,.0f}")


class SameHash:
    """해시 값이 전부 같아서 dict 안에서 서로 충돌하는 키."""

    def __init__(self, number: int) -> None:
        self.number = number

    def __hash__(self) -> int:
        return 1

    def __eq__(self, other) -> bool:
        return isinstance(other, SameHash) and self.number == other.number


def bench_collision() -> None:
    print("\n### 3. 해시가 전부 같은 키로 dict 를 채우는 시간 (ms)")
    print(f"  {'n':>6} | {'같은 해시':>10} | {'정수 키':>8}")
    print(f"  {'-' * 6}-+-{'-' * 10}-+-{'-' * 8}")
    for size in [500, 1_000, 2_000, 4_000]:
        keys = [SameHash(i) for i in range(size)]
        start = time.perf_counter_ns()
        collided = {key: None for key in keys}
        same_ms = (time.perf_counter_ns() - start) / 1e6
        start = time.perf_counter_ns()
        plain = {i: None for i in range(size)}
        plain_ms = (time.perf_counter_ns() - start) / 1e6
        assert len(collided) == len(plain) == size
        print(f"  {size:>6,} | {same_ms:>10.2f} | {plain_ms:>8.3f}")


def main() -> None:
    print(f"Python {platform.python_version()} / {platform.system()} {platform.release()}")
    print(f"free-threaded 빌드: {'예' if getattr(sys, '_is_gil_enabled', lambda: True)() is False else '아니오'}")
    bench_by_size()
    bench_by_position()
    bench_collision()


if __name__ == "__main__":
    main()
