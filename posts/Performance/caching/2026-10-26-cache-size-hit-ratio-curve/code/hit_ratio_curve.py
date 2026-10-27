"""캐시 크기를 키우며 적중률이 어디서 꺾이는지 잰다.

지프 분포를 따르는 접근 기록을 만들고 캐시 크기를 두 배씩 늘려 가며
LRU 적중률과, 같은 크기로 낼 수 있는 상한(가장 인기 있는 k개를 고정해 둔
정적 캐시)을 나란히 잰다. 분포 지수 alpha 를 1.0 · 0.7 · 0.0 으로 바꿔
평평한 분포에서 같은 곡선이 어떻게 달라지는지도 본다.

난수는 시드를 고정했으므로 몇 번을 돌려도 같은 숫자가 나온다.
"""

from __future__ import annotations

import math
import platform
import random
import time
from collections import OrderedDict

KEY_COUNT = 10_000       # 서로 다른 키의 개수
TRACE_LEN = 200_000      # 접근 횟수
SEED = 20261026
ALPHAS = (1.0, 0.7, 0.0)                               # 0.0 은 균등 분포
CACHE_SIZES = (10, 25, 50, 100, 200, 400, 800, 1600, 3200)


def zipf_weights(key_count: int, alpha: float) -> list[float]:
    """순위 i 의 상대 빈도를 1/i**alpha 로 둔다. alpha=0 이면 전부 같다."""
    return [1.0 / (rank ** alpha) for rank in range(1, key_count + 1)]


def build_trace(weights: list[float], length: int, rng: random.Random) -> list[int]:
    """키는 1부터 시작하는 인기 순위 자체다. 1번이 가장 자주 불린다."""
    keys = range(1, len(weights) + 1)
    return rng.choices(list(keys), weights=weights, k=length)


def lru_hit_ratio(trace: list[int], capacity: int) -> tuple[float, float]:
    """(전체 구간 적중률, 뒤쪽 절반만 센 적중률).

    뒤쪽 절반을 따로 세는 이유는 '캐시가 비어 있던 초반 때문에 낮게 나온 것'과
    '정책이 원래 그만큼만 맞히는 것'을 가르기 위해서다.
    """
    cache: OrderedDict[int, None] = OrderedDict()
    half = len(trace) // 2
    hits = 0
    steady_hits = 0
    for position, key in enumerate(trace):
        if key in cache:
            cache.move_to_end(key)
            hits += 1
            if position >= half:
                steady_hits += 1
        else:
            if len(cache) >= capacity:
                cache.popitem(last=False)
            cache[key] = None
    return hits / len(trace), steady_hits / (len(trace) - half)


def static_hit_ratio(trace: list[int], capacity: int) -> float:
    """인기 상위 k 개를 미리 넣고 교체하지 않는 캐시. 분포가 변하지 않는
    동안에는 이보다 더 맞힐 수 없다."""
    hot = frozenset(range(1, capacity + 1))
    return sum(1 for key in trace if key in hot) / len(trace)


def top_k_share(weights: list[float], capacity: int) -> float:
    total = sum(weights)
    return sum(weights[:capacity]) / total


def main() -> None:
    print("=" * 72)
    print("환경")
    print("=" * 72)
    print(f"  Python  {platform.python_version()}")
    print(f"  OS      {platform.system()} {platform.release()}")
    print(f"  키 개수 {KEY_COUNT:,} · 접근 {TRACE_LEN:,}회 · 시드 {SEED}")
    print()

    for alpha in ALPHAS:
        rng = random.Random(SEED)
        weights = zipf_weights(KEY_COUNT, alpha)
        started = time.perf_counter()
        trace = build_trace(weights, TRACE_LEN, rng)
        distinct = len(set(trace))

        label = "균등 분포" if alpha == 0.0 else f"지프 alpha={alpha}"
        print("=" * 72)
        print(f"{label} — 실제로 한 번이라도 불린 키 {distinct:,}개 "
              f"/ {KEY_COUNT:,}개")
        print("=" * 72)
        print("  캐시 크기 | 키 공간 대비 | LRU 적중률 | LRU 뒷절반 | 상위k 고정 | "
              "이론 누적비중 | 직전 대비")
        print("  ----------+--------------+------------+------------+------------+"
              "---------------+----------")

        previous = 0.0
        for size in CACHE_SIZES:
            lru, steady = lru_hit_ratio(trace, size)
            static = static_hit_ratio(trace, size)
            theory = top_k_share(weights, size)
            gain = lru - previous
            previous = lru
            print(f"  {size:9,} | {size / KEY_COUNT:11.1%} | {lru:10.1%} | "
                  f"{steady:10.1%} | {static:10.1%} | {theory:13.1%} | {gain:+9.1%}")

        # 크기를 두 배로 늘릴 때마다 상한이 몇 %p 씩 오르는지. 50 부터는
        # 전부 정확히 두 배씩 늘어나므로 이 구간만 센다.
        doubling = [s for s in CACHE_SIZES if s >= 50]
        steps = [
            top_k_share(weights, hi) - top_k_share(weights, lo)
            for lo, hi in zip(doubling, doubling[1:])
        ]
        print(f"  상한(상위k 고정)이 두 배마다 오르는 폭: "
              f"{' '.join(f'{v:+.1%}' for v in steps)}")
        if alpha == 1.0:
            harmonic = sum(1.0 / rank for rank in range(1, KEY_COUNT + 1))
            print(f"  Breslau 외(1999)의 H(C) ≈ Ω·ln C 로 예측한 폭: "
                  f"{math.log(2) / harmonic:+.1%}  (Ω = 1/H_N, H_N = {harmonic:.4f})")
        print(f"  (이 분포 한 벌을 재는 데 {time.perf_counter() - started:.1f}초)")
        print()


if __name__ == "__main__":
    main()
