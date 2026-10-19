"""존슨-린덴스트라우스 보조정리를 수치로 확인한다.

세 가지를 본다.
  1) 목표 차원 하한 k0 가 원 차원 p 와 무관하게 n 과 epsilon 으로만 정해지는 것
  2) k = k0 로 투영하면 모든 쌍의 제곱거리가 (1 +- epsilon) 안에 들어오는 것
  3) k 를 하한보다 한참 낮추면 그 보장이 깨지는 것

투영 행렬은 세 가지 분포로 만들어 비교한다. 가우시안은 Dasgupta-Gupta 판,
나머지 둘은 Achlioptas 의 Theorem 1.1 이 제시한 동전던지기 분포다.
"""

import math
import random
from itertools import combinations

EPSILON = 0.5
N_POINTS = 50
P_DIM = 1000
SEED = 20261019


def k_bound(n, eps):
    """Dasgupta-Gupta 하한: k >= 24 ln n / (3 eps^2 - 2 eps^3)."""
    return math.ceil(24 * math.log(n) / (3 * eps ** 2 - 2 * eps ** 3))


def make_points(rng, n, p):
    return [[rng.gauss(0.0, 1.0) for _ in range(p)] for _ in range(n)]


def columns_gaussian(rng, p, k):
    return [[rng.gauss(0.0, 1.0) for _ in range(p)] for _ in range(k)]


def columns_pm1(rng, p, k):
    return [[rng.choice((-1.0, 1.0)) for _ in range(p)] for _ in range(k)]


def columns_sparse(rng, p, k):
    """+-sqrt(3) 을 각 1/6, 0 을 2/3 로 뽑는다. 좌표의 2/3 가 0 이라 계산이 준다."""
    root3 = math.sqrt(3.0)
    cols = []
    for _ in range(k):
        col = []
        for i in range(p):
            r = rng.random()
            if r < 1.0 / 6.0:
                col.append((i, root3))
            elif r < 1.0 / 3.0:
                col.append((i, -root3))
        cols.append(col)
    return cols


def project_dense(points, cols):
    scale = 1.0 / math.sqrt(len(cols))
    return [[scale * sum(a * b for a, b in zip(x, col)) for col in cols]
            for x in points]


def project_sparse(points, cols):
    scale = 1.0 / math.sqrt(len(cols))
    out = []
    for x in points:
        out.append([scale * sum(sign * x[i] for i, sign in col) for col in cols])
    return out


def sq_dist(a, b):
    return sum((u - v) ** 2 for u, v in zip(a, b))


def distortions(points, embedded):
    """쌍마다 투영 후 제곱거리 / 원래 제곱거리."""
    ratios = []
    for i, j in combinations(range(len(points)), 2):
        ratios.append(sq_dist(embedded[i], embedded[j]) / sq_dist(points[i], points[j]))
    return ratios


def report(label, ratios, eps):
    lo, hi = min(ratios), max(ratios)
    bad = sum(1 for r in ratios if r < 1 - eps or r > 1 + eps)
    print(f"  {label:<24} 최소 {lo:.4f}  최대 {hi:.4f}  "
          f"허용 밖 {bad}/{len(ratios)} 쌍")


def main():
    rng = random.Random(SEED)
    k0 = k_bound(N_POINTS, EPSILON)

    print("[1] 목표 차원 하한 k0 = ceil(24 ln n / (3e^2 - 2e^3))")
    print(f"  {'n':>10} | " + " | ".join(f"e={e:<4}" for e in (0.1, 0.2, 0.3, 0.5)))
    for n in (100, 1000, 10 ** 4, 10 ** 6, 10 ** 9):
        cells = " | ".join(f"{k_bound(n, e):>6}" for e in (0.1, 0.2, 0.3, 0.5))
        print(f"  {n:>10} | {cells}")
    print("  원 차원 p 는 식에 들어가지 않는다")

    print()
    print(f"[2] n={N_POINTS}, p={P_DIM}, epsilon={EPSILON} -> k0={k0}")
    points = make_points(rng, N_POINTS, P_DIM)

    embedded = project_dense(points, columns_gaussian(rng, P_DIM, k0))
    report("가우시안 N(0,1)", distortions(points, embedded), EPSILON)

    embedded = project_dense(points, columns_pm1(rng, P_DIM, k0))
    report("동전던지기 +-1", distortions(points, embedded), EPSILON)

    embedded = project_sparse(points, columns_sparse(rng, P_DIM, k0))
    report("희소 +-sqrt(3), 0", distortions(points, embedded), EPSILON)

    print()
    k_small = 20
    print(f"[3] 하한을 무시하고 k={k_small} 로 줄이면 (k0={k0})")
    embedded = project_dense(points, columns_gaussian(rng, P_DIM, k_small))
    report("가우시안 N(0,1)", distortions(points, embedded), EPSILON)


if __name__ == "__main__":
    main()
