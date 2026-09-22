"""근사 최근접 이웃 탐색이 필요한 이유와 HNSW 계층 구조를 직접 계산해 확인한다.

[1] 차원이 오르면 최근접과 최원점의 거리가 붙는다 (Beyer 외, ICDT 1999)
[2] HNSW 계층 배정식이 만드는 계층별 원소 수 (Malkov & Yashunin, alg.1 line 4)
[3] mL = 1/ln(M) 이 skip list 의 p = 1/M 에 대응한다는 진술 검산
[4] 원소당 평균 연결 수와 메모리 (논문 4.2.3 절의 식)
"""

import math
import random
import statistics

SEED = 20260922
DIMENSIONS = [2, 4, 8, 16, 32, 64, 128, 256, 512]
POINTS = 1000
QUERIES = 25

# 논문 4.1 절이 권하는 값. M 은 5~48 범위, Mmax0 = 2M, mL = 1/ln(M)
M_VALUES = [5, 16, 48]
M_DEFAULT = 16
ELEMENTS = 1_000_000


def squared_distance(a, b):
    return sum((x - y) * (x - y) for x, y in zip(a, b))


def concentration(dim, rng):
    """질의마다 (최원점거리 - 최근접거리) / 최근접거리 를 재고 중앙값을 돌려준다.

    평균이 아니라 중앙값을 쓰는 이유는, 질의가 우연히 한 점 바로 위에 떨어지면
    분모가 0에 가까워져 한 질의가 평균 전체를 끌고 가기 때문이다.
    """
    points = [[rng.random() for _ in range(dim)] for _ in range(POINTS)]
    ratios = []
    for _ in range(QUERIES):
        q = [rng.random() for _ in range(dim)]
        dists = [math.sqrt(squared_distance(q, p)) for p in points]
        dmin, dmax = min(dists), max(dists)
        ratios.append((dmax - dmin) / dmin)
    return statistics.median(ratios)


def section_distance_concentration():
    print("[1] 차원이 오르면 최근접과 최원점이 붙는다")
    print(f"    [0,1]^d 균등난수 {POINTS}점, 질의 {QUERIES}개, 유클리드 거리")
    print()
    print("     d  |  (Dmax-Dmin)/Dmin 중앙값 |  판독")
    print("    ----+--------------------------+---------------------------")
    rng = random.Random(SEED)
    for dim in DIMENSIONS:
        ratio = concentration(dim, rng)
        if ratio > 3:
            verdict = "최근접이 뚜렷하게 구분된다"
        elif ratio > 0.5:
            verdict = "구분이 흐려지기 시작한다"
        else:
            verdict = "사실상 전부 같은 거리"
        print(f"    {dim:4d} | {ratio:24.3f} | {verdict}")
    print()


def assign_levels(n, m_l, rng):
    """alg.1 line 4: l <- floor(-ln(unif(0,1)) * mL)"""
    counts = {}
    for _ in range(n):
        level = int(-math.log(rng.random()) * m_l)
        counts[level] = counts.get(level, 0) + 1
    return counts


def section_layer_sizes():
    m = M_DEFAULT
    m_l = 1 / math.log(m)
    print(f"[2] 계층 배정 - 원소 {ELEMENTS:,}개, M = {m}, mL = 1/ln(M) = {m_l:.4f}")
    print()
    print("    계층 | 그 계층이 최대층인 원소 |  그 계층에 존재하는 원소 | 직전 계층 대비")
    print("    -----+-------------------------+--------------------------+----------------")
    rng = random.Random(SEED)
    counts = assign_levels(ELEMENTS, m_l, rng)
    top = max(counts)
    # 계층 lc 에 존재하는 원소는 최대층이 lc 이상인 원소 전부다
    cumulative = 0
    present = {}
    for level in range(top, -1, -1):
        cumulative += counts.get(level, 0)
        present[level] = cumulative
    for level in range(top, -1, -1):
        below = present.get(level - 1)
        ratio = f"{present[level] / below:.4f}" if below else "-"
        print(f"    {level:4d} | {counts.get(level, 0):23,} | {present[level]:24,} | {ratio:>14}")
    print()
    print(f"    최상위 계층 = {top},  log_M(N) = {math.log(ELEMENTS) / math.log(m):.2f}")
    print()


def section_skiplist_correspondence():
    print("[3] mL = 1/ln(M) 이 skip list 의 p = 1/M 과 같은지 (p = exp(-1/mL))")
    print()
    print("    원소가 들어가는 평균 계층 수는 바닥함수 때문에 mL+1 이 아니라 p/(1-p)+1 이다.")
    print()
    print("      M | mL = 1/ln(M) | p=exp(-1/mL) |    1/M | 실측 계층비 | p/(1-p)+1 | 실측 평균")
    print("    ----+--------------+--------------+--------+-------------+-----------+-----------")
    for m in M_VALUES:
        m_l = 1 / math.log(m)
        p = math.exp(-1 / m_l)
        rng = random.Random(SEED)
        counts = assign_levels(ELEMENTS, m_l, rng)
        top = max(counts)
        # 0층에만 있는 원소를 뺀 나머지가 1층에도 존재하는 원소다
        measured = (ELEMENTS - counts.get(0, 0)) / ELEMENTS
        mean_levels = sum((lvl + 1) * c for lvl, c in counts.items()) / ELEMENTS
        print(
            f"    {m:3d} | {m_l:12.4f} | {p:12.4f} | {1 / m:6.4f} |"
            f" {measured:11.4f} | {p / (1 - p) + 1:9.4f} | {mean_levels:9.4f}"
            f"   (최상위 {top})"
        )
    print()


def section_memory():
    print("[4] 원소당 평균 연결 수 (논문 4.2.3: (Mmax0 + mL*Mmax) * bytes_per_link)")
    print("    Mmax0 = 2M, Mmax = M, 링크 4바이트로 둔다")
    print()
    print("      M | Mmax0 | 평균 연결 수 | 원소당 바이트 | 1억 원소 기준")
    print("    ----+-------+--------------+---------------+---------------")
    for m in M_VALUES:
        m_l = 1 / math.log(m)
        links = 2 * m + m_l * m
        per_element = links * 4
        print(
            f"    {m:3d} | {2 * m:5d} | {links:12.2f} | {per_element:13.1f} |"
            f" {per_element * 1e8 / 1024 ** 3:10.1f} GiB"
        )
    print()


def main():
    section_distance_concentration()
    section_layer_sizes()
    section_skiplist_correspondence()
    section_memory()


if __name__ == "__main__":
    main()
