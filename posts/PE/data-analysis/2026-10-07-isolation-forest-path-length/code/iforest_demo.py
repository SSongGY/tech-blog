"""Isolation Forest 를 논문(Liu·Ting·Zhou, ICDM 2008)의 알고리즘 1~3 그대로 구현해
경로 길이·이상 점수·부분표본 크기·시계열 창 구성을 확인한다. 표준 라이브러리만 쓴다."""
import math
import platform
import random
import sys

EULER_GAMMA = 0.5772156649


def average_path_length(n):
    """c(n): n개로 만든 이진 탐색 트리에서 실패 탐색의 평균 경로 길이 (논문 식 1).

    n=2 에서 근사식 H(1)≈ln1+γ 를 쓰면 0.15 가 나와 실제 값 1 과 크게 어긋난다.
    scikit-learn 처럼 n<=2 는 정확한 값으로 둔다.
    """
    if n <= 1:
        return 0.0
    if n == 2:
        return 1.0
    return 2.0 * (math.log(n - 1) + EULER_GAMMA) - 2.0 * (n - 1) / n


def build_itree(points, depth, height_limit, rng):
    """알고리즘 2: 속성 하나와 분할값을 무작위로 골라 재귀 분할한다."""
    if depth >= height_limit or len(points) <= 1:
        return ("leaf", len(points))
    dims = len(points[0])
    attr = rng.randrange(dims)
    lo = min(p[attr] for p in points)
    hi = max(p[attr] for p in points)
    if lo == hi:
        # 모든 값이 같으면 더 나눌 수 없다 — 논문의 종료 조건 (iii)
        return ("leaf", len(points))
    split = rng.uniform(lo, hi)
    left = [p for p in points if p[attr] < split]
    right = [p for p in points if p[attr] >= split]
    return ("node", attr, split,
            build_itree(left, depth + 1, height_limit, rng),
            build_itree(right, depth + 1, height_limit, rng))


def path_length(x, tree, depth=0):
    """알고리즘 3: 높이 제한에 걸려 여러 점이 남은 잎은 c(size) 를 더해 덜 자란 부분을 보정한다."""
    if tree[0] == "leaf":
        return depth + average_path_length(tree[1])
    _, attr, split, left, right = tree
    return path_length(x, left if x[attr] < split else right, depth + 1)


class IsolationForest:
    def __init__(self, n_trees=100, sample_size=256, seed=0):
        self.n_trees = n_trees
        self.sample_size = sample_size
        self.rng = random.Random(seed)

    def fit(self, data):
        """알고리즘 1: 비복원 부분표본마다 트리 하나. 높이 제한은 ceil(log2 ψ)."""
        self.psi = min(self.sample_size, len(data))
        height_limit = math.ceil(math.log2(self.psi))
        self.trees = [build_itree(self.rng.sample(data, self.psi), 0, height_limit, self.rng)
                      for _ in range(self.n_trees)]
        return self

    def mean_path(self, x):
        return sum(path_length(x, t) for t in self.trees) / len(self.trees)

    def score(self, x):
        """식 2: s = 2^(-E[h(x)] / c(ψ)). 1에 가까우면 이상, 0.5보다 한참 작으면 정상."""
        return 2.0 ** (-self.mean_path(x) / average_path_length(self.psi))


def gauss_cluster(rng, n, cx, cy, sd):
    return [(rng.gauss(cx, sd), rng.gauss(cy, sd)) for _ in range(n)]


def experiment_c_table():
    print("[실험1] 정규화 상수 c(n) 과 높이 제한 ceil(log2 n)")
    print(f"  {'n':>6}  {'c(n)':>7}  {'log2 n':>7}  {'높이 제한':>6}")
    for n in (2, 8, 64, 256, 1024, 4096):
        print(f"  {n:>6}  {average_path_length(n):>7.3f}  {math.log2(n):>7.2f}  {math.ceil(math.log2(n)):>6}")
    print()


def experiment_three_points():
    rng = random.Random(1)
    normal = gauss_cluster(rng, 500, 0.0, 0.0, 1.0)
    probes = [("중심점 (0, 0)", (0.0, 0.0)),
              ("가장자리 (2.5, 0)", (2.5, 0.0)),
              ("고립점 (6, 6)", (6.0, 6.0))]
    forest = IsolationForest(n_trees=100, sample_size=256, seed=2).fit(normal)
    print("[실험2] 정상 군집 500점(평균 0, 표준편차 1)으로 학습, ψ=256, 트리 100개")
    print(f"  c(ψ) = {average_path_length(256):.3f}")
    print(f"  {'점':<16}{'평균 경로 E[h]':>14}{'점수 s':>10}")
    for label, p in probes:
        print(f"  {label:<16}{forest.mean_path(p):>14.2f}{forest.score(p):>10.3f}")
    print()


def top_k_hit(scores, labels, k):
    """점수 상위 k개 중 실제 이상치 비율."""
    ranked = sorted(zip(scores, labels), key=lambda t: -t[0])[:k]
    return sum(lbl for _, lbl in ranked) / k


def experiment_subsampling():
    """논문 3절의 swamping·masking: 이상치가 빽빽하게 뭉쳐 있으면 전체 데이터로는 고립이 늦다."""
    rng = random.Random(3)
    normal = gauss_cluster(rng, 4000, 0.0, 0.0, 1.0)
    anomaly = gauss_cluster(rng, 100, 3.2, 3.2, 0.15)
    data = normal + anomaly
    labels = [0] * len(normal) + [1] * len(anomaly)
    print("[실험3] 정상 4000점 + 이상 군집 100점(중심 (3.2, 3.2), 표준편차 0.15) — 부분표본 크기 ψ 비교")
    print(f"  {'ψ':>6}{'높이 제한':>8}{'이상 평균 s':>12}{'정상 평균 s':>12}{'상위 100 적중':>14}")
    for psi in (4100, 1024, 256, 64):
        forest = IsolationForest(n_trees=100, sample_size=psi, seed=4).fit(data)
        scores = [forest.score(p) for p in data]
        a_mean = sum(scores[len(normal):]) / len(anomaly)
        n_mean = sum(scores[:len(normal)]) / len(normal)
        print(f"  {forest.psi:>6}{math.ceil(math.log2(forest.psi)):>8}{a_mean:>12.3f}{n_mean:>12.3f}"
              f"{top_k_hit(scores, labels, 100):>14.2f}")
    print()


def experiment_time_series():
    """값 하나만 보면 정상 범위 안인 형상 이상을, 슬라이딩 창으로 묶으면 잡는가."""
    period = 50
    series = [math.sin(2 * math.pi * t / period) for t in range(2000)]
    # 1500~1524 구간: 진폭은 그대로 두고 주기를 절반으로 — 값 범위는 [-1, 1] 그대로다
    anomaly_range = range(1500, 1525)
    for t in anomaly_range:
        series[t] = math.sin(2 * math.pi * t / (period / 2))
    rng = random.Random(5)
    series = [v + rng.gauss(0, 0.05) for v in series]

    print("[실험4] 사인파 2000시점(주기 50, 잡음 0.05), 1500~1524 구간만 주기 25로 바꿈")
    print(f"  값 범위: 정상 구간 [{min(series[:1500]):.2f}, {max(series[:1500]):.2f}]"
          f" · 이상 구간 [{min(series[1500:1525]):.2f}, {max(series[1500:1525]):.2f}]")
    print(f"  {'입력 구성':<22}{'이상 구간 최고 순위':>14}{'상위 25 중 이상 구간':>18}")
    for window in (1, 10, 25):
        vectors, starts = [], []
        for t in range(window - 1, len(series)):
            vectors.append(tuple(series[t - window + 1:t + 1]))
            starts.append(t)
        forest = IsolationForest(n_trees=100, sample_size=256, seed=6).fit(vectors)
        scores = [forest.score(v) for v in vectors]
        # 창의 끝 시점이 이상 구간에 들어가면 이상 창으로 본다
        flags = [1 if t in anomaly_range else 0 for t in starts]
        order = sorted(range(len(scores)), key=lambda i: -scores[i])
        best_rank = next(r for r, i in enumerate(order, 1) if flags[i])
        hit = sum(flags[i] for i in order[:25])
        label = "값 하나 (w=1)" if window == 1 else f"창 w={window}"
        print(f"  {label:<22}{best_rank:>14}{hit:>15} / 25")
    print()


def main():
    print(f"Python {platform.python_version()} ({sys.platform}) · 표준 라이브러리만 사용\n")
    experiment_c_table()
    experiment_three_points()
    experiment_subsampling()
    experiment_time_series()


if __name__ == "__main__":
    main()
