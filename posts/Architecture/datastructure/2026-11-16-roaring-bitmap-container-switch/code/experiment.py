"""roaring.py 로 네 가지를 잰다.

[1] 논문 그림 1의 예시 집합이 어떤 컨테이너로 나뉘는가
[2] 한 청크 안 원소 수에 따른 크기 — 배열 vs 비트맵, 4096 경계
[3] 밀도별 크기 — 단순 비트맵, 32비트 정렬 배열, Roaring
[4] 경계에서 넣고 빼기를 반복하면 변환이 몇 번 일어나는가
[5] 교집합 연산 횟수 — 세 가지 컨테이너 조합
"""
import platform
import random
import sys

from roaring import (
    ARRAY_LIMIT,
    BITMAP_BYTES,
    ArrayContainer,
    BitmapContainer,
    OpCounter,
    RoaringBitmap,
    intersect,
    intersect_containers,
)

UNIVERSE = 1 << 24          # 0 ~ 16,777,215 (청크 256개)
SEED = 20261116


def describe(bitmap):
    for key, container in zip(bitmap.keys, bitmap.containers):
        print(f"  key=0x{key:04X}  {container.kind:<6}  원소 {len(container):>6}"
              f"  {container.nbytes():>6} B")


def figure_one():
    print("[1] 논문 그림 1 집합: 62의 배수 1000개, [2^16, 2^16+100), [2*2^16, 3*2^16) 짝수")
    values = [62 * k for k in range(1000)]
    values += range(1 << 16, (1 << 16) + 100)
    values += range(2 << 16, 3 << 16, 2)
    describe(RoaringBitmap(values))
    print()


def chunk_sizes():
    print("[2] 한 청크(2^16 칸)에 원소 n개를 넣었을 때 컨테이너 크기")
    print("  n      | 배열로 담으면 | 비트맵으로 담으면 | Roaring 이 고른 것")
    rng = random.Random(SEED)
    for n in (1, 100, 4095, 4096, 4097, 10000, 65536):
        lows = rng.sample(range(1 << 16), n)
        chosen = RoaringBitmap(lows).containers[0]
        print(f"  {n:>6} | {n * 2:>11} B | {BITMAP_BYTES:>15} B | "
              f"{chosen.kind} {chosen.nbytes()} B")
    print()


def density_sizes():
    print(f"[3] 0 ~ {UNIVERSE - 1:,} 범위, 균등 무작위 집합의 크기 (원소당 비트)")
    print("  밀도      | 원소 수   | 단순 비트맵 | 정렬 배열(32비트) | Roaring | 컨테이너(배열/비트맵)")
    rng = random.Random(SEED)
    for density in (0.0001, 0.001, 0.01, 0.05, 0.0625, 0.07, 0.2, 0.5):
        n = int(UNIVERSE * density)
        values = rng.sample(range(UNIVERSE), n)
        bitmap = RoaringBitmap(values)
        plain_bits = UNIVERSE / n
        sorted_bits = 32.0
        # 페이로드 + 1단계 색인(키 2바이트 + 개수 4바이트) — 색인 크기는 이 구현의 가정
        index_bytes = len(bitmap.keys) * 6
        roaring_bits = (bitmap.payload_bytes() + index_bytes) * 8 / n
        kinds = [c.kind for c in bitmap.containers]
        print(f"  {density:<9} | {n:>9,} | {plain_bits:>11.2f} | {sorted_bits:>17.2f} | "
              f"{roaring_bits:>7.2f} | {kinds.count('array')}/{kinds.count('bitmap')}")
    print()

    print("[3-B] 원소 1000개를 2^16 간격으로 흩으면 (청크마다 1개)")
    spread = RoaringBitmap(k << 16 for k in range(1000))
    index_bytes = len(spread.keys) * 6
    print(f"  컨테이너 {len(spread.keys)}개, 원소당 "
          f"{(spread.payload_bytes() + index_bytes) * 8 / len(spread):.2f} 비트")
    print()


def boundary_flapping():
    print("[4] 원소 4096개 청크에서 같은 값 하나를 넣고 빼기를 10번 반복")
    bitmap = RoaringBitmap(range(0, 2 * ARRAY_LIMIT, 2))
    print(f"  시작: {bitmap.containers[0].kind}, 원소 {len(bitmap)}")
    for _ in range(10):
        bitmap.add(1)
        bitmap.remove(1)
    print(f"  끝  : {bitmap.containers[0].kind}, 원소 {len(bitmap)}, "
          f"종류 변환 {bitmap.conversions}번")
    print()


def intersection_costs():
    print("[5] 한 청크 안 교집합의 기본 연산 횟수 (비교·워드 AND·비트 확인)")
    rng = random.Random(SEED)
    cases = [
        ("배열 1000 ∩ 배열 1000", 1000, 1000),
        ("배열 1000 ∩ 배열 4000", 1000, 4000),
        ("배열 1000 ∩ 비트맵 30000", 1000, 30000),
        ("비트맵 30000 ∩ 비트맵 30000", 30000, 30000),
        ("비트맵 5000 ∩ 비트맵 5000", 5000, 5000),
    ]
    for label, n1, n2 in cases:
        lows1 = rng.sample(range(1 << 16), n1)
        lows2 = rng.sample(range(1 << 16), n2)
        a = ArrayContainer(lows1) if n1 <= ARRAY_LIMIT else BitmapContainer(lows1)
        b = ArrayContainer(lows2) if n2 <= ARRAY_LIMIT else BitmapContainer(lows2)
        counter = OpCounter()
        result = intersect_containers(a, b, counter)
        expected = sorted(set(lows1) & set(lows2))
        kind = "array" if len(result) <= ARRAY_LIMIT else "bitmap"
        print(f"  {label:<26} 연산 {counter.count:>5}  결과 {len(result):>5}개 → {kind}"
              f"  검산 {'일치' if sorted(result) == expected else '불일치'}")
    print()

    print("[5-B] 전체 교집합 (여러 청크) — set 연산과 대조")
    values1 = rng.sample(range(UNIVERSE), 200_000)
    values2 = rng.sample(range(UNIVERSE), 1_500_000)
    counter = OpCounter()
    result = intersect(RoaringBitmap(values1), RoaringBitmap(values2), counter)
    expected = sorted(set(values1) & set(values2))
    print(f"  20만 ∩ 150만: 결과 {len(result):,}개, 기본 연산 {counter.count:,}번, "
          f"검산 {'일치' if result == expected else '불일치'}")


def main():
    print(f"Python {platform.python_version()} / {platform.system()} {platform.release()}"
          f" / 64비트 {sys.maxsize > 2**32}")
    print()
    figure_one()
    chunk_sizes()
    density_sizes()
    boundary_flapping()
    intersection_costs()


if __name__ == "__main__":
    main()
