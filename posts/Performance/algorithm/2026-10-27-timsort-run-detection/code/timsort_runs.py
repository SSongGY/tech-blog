"""Timsort 가 입력의 모양에 따라 얼마나 다르게 도는지 비교 횟수로 센다.

시간은 장비마다 흔들리므로 `__lt__` 호출 횟수를 함께 센다. 비교 횟수는
구현이 같으면 어디서 돌려도 같은 값이 나오므로, 런 탐지가 실제로 일을
줄이는지 확인하는 데 시간보다 낫다.
"""

import random
import time
from functools import cmp_to_key

N = 32768          # 2의 거듭제곱 — 병합이 고르게 갈라진다
SEED = 20261027
REPEAT = 5         # 시간은 가장 빠른 회차를 쓴다


class Counted:
    """비교할 때마다 세는 래퍼. 파이썬 정렬은 `<` 만 쓴다."""

    __slots__ = ("value",)
    comparisons = 0

    def __init__(self, value: int) -> None:
        self.value = value

    def __lt__(self, other: "Counted") -> bool:
        Counted.comparisons += 1
        return self.value < other.value


def make_inputs(rng: random.Random) -> dict[str, list[int]]:
    ascending = list(range(N))

    nearly = ascending.copy()
    for _ in range(N // 100):                      # 1% 자리만 흐트러뜨린다
        nearly[rng.randrange(N)] = rng.randrange(N)

    blocks: list[int] = []
    for start in range(0, N, 1024):                # 1024 개씩 정렬된 덩어리 32개
        chunk = [rng.randrange(N) for _ in range(1024)]
        chunk.sort()
        blocks.extend(chunk)

    return {
        "무작위": [rng.randrange(N) for _ in range(N)],
        "오름차순": ascending,
        "내림차순": ascending[::-1],
        "거의 오름차순 (1% 흐트러짐)": nearly,
        "1024개씩 정렬된 블록 32개": blocks,
    }


def count_comparisons(data: list[int]) -> int:
    wrapped = [Counted(v) for v in data]
    Counted.comparisons = 0
    wrapped.sort()
    return Counted.comparisons


def best_time(data: list[int]) -> float:
    best = float("inf")
    for _ in range(REPEAT):
        copy = data.copy()
        started = time.perf_counter()
        copy.sort()
        best = min(best, time.perf_counter() - started)
    return best


def section(title: str) -> None:
    print()
    print("=" * 68)
    print(title)
    print("=" * 68)


def step_shapes(inputs: dict[str, list[int]]) -> None:
    section(f"1. 입력 모양별 비교 횟수와 시간 — 원소 {N:,}개")
    print(f"  {'입력 모양':<28} {'비교 횟수':>12} {'n log2 n 대비':>14} {'가장 빠른 회차':>16}")
    print("  " + "-" * 72)
    upper = N * (N - 1).bit_length()
    for label, data in inputs.items():
        comparisons = count_comparisons(data)
        elapsed = best_time(data)
        print(f"  {label:<28} {comparisons:>12,} {comparisons / upper:>13.1%} {elapsed * 1000:>14.2f}ms")
    print()
    print(f"  n log2 n = {upper:,} (비교 횟수의 대략적인 상한)")
    print(f"  n - 1    = {N - 1:,} (이미 정렬된 입력의 하한)")


def step_block_size(rng: random.Random) -> None:
    section("2. 덩어리 크기를 바꾸면 — 런이 길수록 병합 단계가 준다")
    print("  모형: 런을 찾는 데 n-1 번, 병합 단계마다 n 번 — (n-1) + n x log2(덩어리 수)")
    print()
    print(f"  {'덩어리 크기':>12} {'덩어리 수':>10} {'비교 횟수':>12} {'모형값':>12} {'차이':>10}")
    print("  " + "-" * 62)
    for size in (16, 32, 64, 256, 1024, 4096, 32768):
        data: list[int] = []
        for _ in range(N // size):
            chunk = [rng.randrange(N) for _ in range(size)]
            chunk.sort()
            data.extend(chunk)
        blocks = N // size
        levels = blocks.bit_length() - 1          # log2(덩어리 수)
        model = (N - 1) + N * levels
        measured = count_comparisons(data)
        print(f"  {size:>12,} {blocks:>10,} {measured:>12,} {model:>12,} {measured - model:>+10,}")
    print()
    print("  덩어리가 16 일 때만 모형보다 크게 벗어난다 — minrun 이 32 라서")
    print("  짧은 런은 이진 삽입 정렬로 32 까지 늘리고, 그 비용이 더해지기 때문이다")


def step_stability(rng: random.Random) -> None:
    section("3. 안정 정렬이라 두 단계로 나눠 정렬할 수 있다")
    records = [
        {"team": "가", "name": "A", "score": 90},
        {"team": "나", "name": "B", "score": 90},
        {"team": "가", "name": "C", "score": 70},
        {"team": "나", "name": "D", "score": 95},
        {"team": "가", "name": "E", "score": 90},
    ]
    print("  원본 순서:", [r["name"] for r in records])

    # 보조 키로 먼저, 주 키로 나중에 — 안정이라 앞 단계 순서가 남는다
    records.sort(key=lambda r: r["name"])
    records.sort(key=lambda r: -r["score"])
    print("  이름 → 점수 내림차순 순으로 두 번 정렬:")
    for r in records:
        print(f"    {r['score']:>3}  {r['name']}  ({r['team']}팀)")

    same = [r["name"] for r in records if r["score"] == 90]
    print(f"  점수가 같은 90점 묶음의 순서: {same}  ← 앞 단계의 이름 순서가 그대로 남는다")


def step_key_cost() -> None:
    section("4. key 함수는 몇 번 불리는가")
    calls = 0

    def key_fn(value: int) -> int:
        nonlocal calls
        calls += 1
        return value % 1000

    data = list(range(N))
    calls = 0
    data.sort(key=key_fn)
    print(f"  원소 {N:,}개를 key 로 정렬 → key 호출 {calls:,}회")
    print(f"  비교 횟수 상한 n log2 n = {N * (N - 1).bit_length():,} 와 비교하면 훨씬 적다")
    print("  key 는 원소마다 한 번만 계산해 두고, 그 값끼리 비교하기 때문이다")


def step_cmp_to_key(rng: random.Random) -> None:
    section("5. key 대신 비교 함수를 쓰면 호출 횟수가 달라진다")
    data = [rng.randrange(N) for _ in range(N)]

    key_calls = 0

    def key_fn(value: int) -> int:
        nonlocal key_calls
        key_calls += 1
        return value

    cmp_calls = 0

    def cmp_fn(left: int, right: int) -> int:
        nonlocal cmp_calls
        cmp_calls += 1
        return (left > right) - (left < right)

    copy = data.copy()
    started = time.perf_counter()
    copy.sort(key=key_fn)
    key_seconds = time.perf_counter() - started

    copy = data.copy()
    started = time.perf_counter()
    copy.sort(key=cmp_to_key(cmp_fn))
    cmp_seconds = time.perf_counter() - started

    print(f"  key=  로 정렬   → 함수 호출 {key_calls:>9,}회 · {key_seconds * 1000:7.1f}ms")
    print(f"  cmp_to_key 로 정렬 → 함수 호출 {cmp_calls:>9,}회 · {cmp_seconds * 1000:7.1f}ms")
    print(f"  호출 횟수 비 {cmp_calls / key_calls:.1f}배 — 비교 함수는 비교할 때마다 불린다")


def main() -> None:
    print(f"난수 시드 {SEED} · 원소 수 {N:,} · 시간은 {REPEAT}회 중 가장 빠른 값")
    rng = random.Random(SEED)
    inputs = make_inputs(rng)
    step_shapes(inputs)
    step_block_size(random.Random(SEED))
    step_stability(random.Random(SEED))
    step_key_cost()
    step_cmp_to_key(random.Random(SEED))


if __name__ == "__main__":
    main()
