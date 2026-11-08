"""Count-Min Sketch 를 Cormode·Muthukrishnan(2005) 3절 구성대로 구현하고 보장을 잰다.

1) 크기 — eps, delta 로 w = ceil(e/eps), d = ceil(ln(1/delta))
2) Zipf 스트림 100만 건 — 과소 추정 0건인가, eps*N 을 넘는 오차가 delta 이하인가
3) 빈도 구간별 오차 — 오차는 N 에 비례하는 덧셈 오차라 드문 항목일수록 상대 오차가 크다
4) 같은 메모리에서 w 와 d 를 바꾸면
5) 균등 분포 스트림 — 빈도가 고르게 낮으면
6) 빈도 상위 항목(heavy hitters) 찾기 — 놓치는 것이 없는가, 잘못 넣는 것은 무엇인가
7) 메모리 — 정확한 Counter 와 비교
"""
import math
import random
import tracemalloc
from collections import Counter

PRIME = (1 << 61) - 1  # 메르센 소수. 항목 번호보다 충분히 커야 해시가 고르게 퍼진다
SEED = 20261108
NUM_ITEMS = 100_000
STREAM_LENGTH = 1_000_000


class CountMinSketch:
    def __init__(self, width, depth, rng):
        self.width = width
        self.depth = depth
        # 행마다 (a, b) 두 정수로 해시 함수 하나를 정한다
        self.params = [(rng.randrange(1, PRIME), rng.randrange(0, PRIME)) for _ in range(depth)]
        self.table = [[0] * width for _ in range(depth)]

    @classmethod
    def from_error(cls, eps, delta, rng):
        return cls(math.ceil(math.e / eps), math.ceil(math.log(1 / delta)), rng)

    def _columns(self, item):
        return [((a * item + b) % PRIME) % self.width for a, b in self.params]

    def update(self, item, count=1):
        for row, col in zip(self.table, self._columns(item)):
            row[col] += count

    def estimate(self, item):
        return min(row[col] for row, col in zip(self.table, self._columns(item)))


def zipf_stream(rng, exponent):
    weights = [1 / (rank ** exponent) for rank in range(1, NUM_ITEMS + 1)]
    return rng.choices(range(NUM_ITEMS), weights=weights, k=STREAM_LENGTH)


def build(stream, width, depth, seed):
    sketch = CountMinSketch(width, depth, random.Random(seed))
    for item in stream:
        sketch.update(item)
    return sketch


def error_report(sketch, exact, eps):
    total = sum(exact.values())
    bound = eps * total
    errors = [sketch.estimate(item) - count for item, count in exact.items()]
    under = sum(1 for e in errors if e < 0)
    over_bound = sum(1 for e in errors if e > bound)
    errors.sort()
    pick = lambda q: errors[min(len(errors) - 1, int(q * len(errors)))]
    print(f"  항목 {len(errors):,}개 · N = {total:,} · 상한 eps*N = {bound:,.0f}")
    print(f"  과소 추정 {under}건 · 상한 초과 {over_bound}건 ({over_bound / len(errors):.3%})")
    print(f"  오차 중앙값 {pick(0.5):,} · 90% {pick(0.9):,} · 99% {pick(0.99):,} · 최대 {errors[-1]:,}")


def section_size():
    print("== 1) eps, delta 로 정한 크기 ==")
    for eps, delta in ((0.01, 0.01), (0.001, 0.01), (0.01, 0.001)):
        width = math.ceil(math.e / eps)
        depth = math.ceil(math.log(1 / delta))
        print(f"  eps={eps:<6} delta={delta:<6} -> w={width:>5} d={depth} 카운터 {width * depth:,}개")
    print()


def section_zipf(stream, exact):
    print("== 2) Zipf(s=1.1) 스트림, eps=0.01 delta=0.01 (w=272, d=5) ==")
    sketch = build(stream, 272, 5, SEED)
    error_report(sketch, exact, 0.01)
    print()
    return sketch


def section_by_frequency(sketch, exact):
    print("== 3) 실제 빈도 구간별 오차 ==")
    print("  실제 빈도       항목 수   평균 오차   평균 상대 오차")
    bands = [(10_000, None), (1_000, 10_000), (100, 1_000), (10, 100), (1, 10)]
    for low, high in bands:
        items = [i for i, c in exact.items() if c >= low and (high is None or c < high)]
        if not items:
            continue
        errors = [sketch.estimate(i) - exact[i] for i in items]
        relative = [e / exact[i] for e, i in zip(errors, items)]
        label = f"{low:,} 이상" if high is None else f"{low:,}~{high - 1:,}"
        print(f"  {label:14} {len(items):>7,}  {sum(errors) / len(errors):>10,.1f}  {sum(relative) / len(relative):>12.1%}")
    print()


def section_shape(stream, exact):
    print("== 4) 카운터 1,360개를 w x d 로 나누는 방법 ==")
    print("    w x d    평균 오차   99% 오차    최대 오차")
    for depth in (1, 2, 5, 10, 20):
        width = 1360 // depth
        sketch = build(stream, width, depth, SEED + depth)
        errors = sorted(sketch.estimate(i) - c for i, c in exact.items())
        mean = sum(errors) / len(errors)
        print(f"  {width:>4} x {depth:<2} {mean:>10,.1f} {errors[int(0.99 * len(errors))]:>10,} {errors[-1]:>10,}")
    print()


def section_uniform():
    print("== 5) 균등 분포 스트림 (항목마다 평균 10회) ==")
    rng = random.Random(SEED)
    stream = [rng.randrange(NUM_ITEMS) for _ in range(STREAM_LENGTH)]
    exact = Counter(stream)
    sketch = build(stream, 272, 5, SEED)
    error_report(sketch, exact, 0.01)
    sample = sorted(exact)[:3]
    for item in sample:
        print(f"  항목 {item}: 실제 {exact[item]} -> 추정 {sketch.estimate(item):,}")
    print()


def section_heavy(stream, exact):
    # phi 와 같은 eps 로는 보장 하한 (phi - eps)N 이 0 이 되므로 eps 를 phi 보다 작게 잡는다
    print("== 6) 빈도가 N 의 1% (phi=0.01) 를 넘는 항목, eps=0.002 (w=1360, d=5) ==")
    sketch = build(stream, 1360, 5, SEED)
    total = sum(exact.values())
    threshold = 0.01 * total
    truth = {i for i, c in exact.items() if c > threshold}
    reported = {i for i in exact if sketch.estimate(i) > threshold}
    print(f"  실제 {len(truth)}개 · 보고 {len(reported)}개 · 놓친 것 {len(truth - reported)}개")
    for item in sorted(reported - truth, key=lambda i: -exact[i]):
        print(f"  잘못 보고: 항목 {item} 실제 {exact[item]:,} ({exact[item] / total:.3%}) 추정 {sketch.estimate(item):,}")
    print(f"  보장 범위: 확률 1-delta 로, 실제 빈도가 (phi - eps)N = {(0.01 - 0.002) * total:,.0f} 미만인 항목은 보고되지 않는다")
    print()


def section_memory(stream):
    print("== 7) 메모리 (tracemalloc) ==")
    tracemalloc.start()
    exact = Counter(stream)
    exact_bytes = tracemalloc.get_traced_memory()[0]
    tracemalloc.stop()
    tracemalloc.start()
    sketch = build(stream, 272, 5, SEED)
    sketch_bytes = tracemalloc.get_traced_memory()[0]
    tracemalloc.stop()
    print(f"  Counter (고유 항목 {len(exact):,}개): {exact_bytes / 1024:,.0f} KiB")
    print(f"  Count-Min 272 x 5 (스트림을 다 넣은 뒤): {sketch_bytes / 1024:,.1f} KiB")
    print()


def main():
    section_size()
    rng = random.Random(SEED)
    stream = zipf_stream(rng, 1.1)
    exact = Counter(stream)
    sketch = section_zipf(stream, exact)
    section_by_frequency(sketch, exact)
    section_shape(stream, exact)
    section_uniform()
    section_heavy(stream, exact)
    section_memory(stream)


if __name__ == "__main__":
    main()
