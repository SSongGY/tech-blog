"""기대 시험 오차를 편향²·분산·잡음으로 나누고, 규제 기법이 어느 항을 움직이는지 잰다.

참 함수 sin(pi x) 에 잡음 N(0, 0.2^2) 를 얹은 학습 표본 20개를 200번 새로 뽑아
같은 모형을 200번 맞춘다. 격자 위 각 x 에서 예측 200개의 평균이 참값과 얼마나
떨어졌는지가 편향, 예측 200개가 서로 얼마나 흩어졌는지가 분산이다.
외부 의존성 없이 표준 라이브러리만 쓴다.
"""

import math
import platform
import random
import sys

NOISE_SD = 0.2
TRAIN_SIZE = 20
TRIALS = 200
GRID = [-0.95 + 1.9 * i / 100 for i in range(101)]
SEED = 11


def true_function(x):
    return math.sin(math.pi * x)


def make_train(size, rng):
    # 학습 x 를 구간에 고르게 깐다. 양 끝이 비면 외삽 실패가 분산을 지배한다.
    step = 2.0 / size
    xs = [-1.0 + step * (i + rng.uniform(0.1, 0.9)) for i in range(size)]
    ys = [true_function(x) + rng.gauss(0.0, NOISE_SD) for x in xs]
    return xs, ys


def legendre_features(x, degree):
    # 단항식 대신 르장드르 다항식을 써서 고차에서도 정규방정식이 무너지지 않게 한다.
    row = [1.0]
    if degree >= 1:
        row.append(x)
    for k in range(1, degree):
        row.append(((2 * k + 1) * x * row[k] - k * row[k - 1]) / (k + 1))
    return row


def solve(matrix, vector):
    size = len(vector)
    aug = [matrix[i][:] + [vector[i]] for i in range(size)]
    for col in range(size):
        pivot = max(range(col, size), key=lambda r: abs(aug[r][col]))
        aug[col], aug[pivot] = aug[pivot], aug[col]
        for r in range(col + 1, size):
            factor = aug[r][col] / aug[col][col]
            for c in range(col, size + 1):
                aug[r][c] -= factor * aug[col][c]
    result = [0.0] * size
    for r in range(size - 1, -1, -1):
        acc = aug[r][size] - sum(aug[r][c] * result[c] for c in range(r + 1, size))
        result[r] = acc / aug[r][r]
    return result


def normal_equations(xs, ys, degree):
    rows = [legendre_features(x, degree) for x in xs]
    width = degree + 1
    gram = [[sum(row[i] * row[j] for row in rows) for j in range(width)] for i in range(width)]
    rhs = [sum(row[i] * y for row, y in zip(rows, ys)) for i in range(width)]
    return gram, rhs


def fit_ridge(gram, rhs, penalties):
    # penalties[j] 를 대각에 더한다. 절편(j=0)은 0 으로 둬 평균 수준을 끌어내리지 않는다.
    width = len(rhs)
    reg = [[gram[i][j] + (penalties[i] if i == j else 0.0) for j in range(width)] for i in range(width)]
    return solve(reg, rhs)


def fit_lasso(gram, rhs, rate, sweeps=200):
    # (1/2)||y - Xw||^2 + rate * sum|w_j| 를 좌표 하강으로 푼다. 절편은 벌점에서 뺀다.
    width = len(rhs)
    weights = [0.0] * width
    for _ in range(sweeps):
        for j in range(width):
            rho = rhs[j] - sum(gram[j][k] * weights[k] for k in range(width) if k != j)
            if j == 0:
                weights[j] = rho / gram[j][j]
            elif rho > rate:
                weights[j] = (rho - rate) / gram[j][j]
            elif rho < -rate:
                weights[j] = (rho + rate) / gram[j][j]
            else:
                weights[j] = 0.0
    return weights


def mat_mul(a, b):
    size = len(a)
    return [[sum(a[i][k] * b[k][j] for k in range(size)) for j in range(size)] for i in range(size)]


def mat_pow(matrix, exponent):
    size = len(matrix)
    result = [[1.0 if i == j else 0.0 for j in range(size)] for i in range(size)]
    base = matrix
    while exponent:
        if exponent & 1:
            result = mat_mul(result, base)
        exponent >>= 1
        if exponent:
            base = mat_mul(base, base)
    return result


def fit_early_stopping(gram, rhs, checkpoints):
    # 0 에서 출발한 경사 하강 t 걸음의 해는 w_t = w* - (I - eta G)^t w* 로 닫힌 꼴이 된다.
    # 백만 걸음을 하나씩 밟는 대신 행렬 거듭제곱으로 바로 구한다.
    width = len(rhs)
    eta = 1.0 / sum(gram[i][i] for i in range(width))
    optimum = solve(gram, rhs)
    step = [[(1.0 if i == j else 0.0) - eta * gram[i][j] for j in range(width)] for i in range(width)]
    results = {}
    for target in checkpoints:
        power = mat_pow(step, target)
        moved = [sum(power[i][k] * optimum[k] for k in range(width)) for i in range(width)]
        results[target] = [optimum[i] - moved[i] for i in range(width)]
    return results


def predict(weights, x):
    return sum(w * f for w, f in zip(weights, legendre_features(x, len(weights) - 1)))


def decompose(predictions):
    """예측 행렬[시행][격자] 에서 격자 평균 편향², 분산을 구한다."""
    bias_sq = variance = 0.0
    for g, x in enumerate(GRID):
        column = [row[g] for row in predictions]
        mean = sum(column) / len(column)
        bias_sq += (mean - true_function(x)) ** 2
        variance += sum((p - mean) ** 2 for p in column) / len(column)
    return bias_sq / len(GRID), variance / len(GRID)


def simulated_test_mse(predictions, rng):
    # 새 잡음을 얹은 시험 관측과 직접 비교한다. 분해식 합계와 맞는지 보려는 것이다.
    total = 0.0
    for row in predictions:
        for g, x in enumerate(GRID):
            y = true_function(x) + rng.gauss(0.0, NOISE_SD)
            total += (row[g] - y) ** 2
    return total / (len(predictions) * len(GRID))


def train_sets(size=TRAIN_SIZE):
    rng = random.Random(SEED + size)
    return [make_train(size, rng) for _ in range(TRIALS)]


def report(label, predictions, extra=""):
    bias_sq, variance = decompose(predictions)
    total = bias_sq + variance + NOISE_SD ** 2
    print(f"{label:>10} {bias_sq:>10.4f} {variance:>10.4f} {total:>10.4f}{extra}")
    return bias_sq, variance


def header(extra=""):
    print(f"{'설정':>10} {'편향²':>10} {'분산':>10} {'기대오차':>10}{extra}")


def main():
    print(f"Python {platform.python_version()} / {platform.system()} / seed={SEED}")
    print(f"참 함수 y = sin(pi x) + N(0, {NOISE_SD}^2), 학습 표본 {TRAIN_SIZE}개를 {TRIALS}번 새로 뽑는다")
    print(f"평가 격자 x = -0.95 ~ 0.95, {len(GRID)}점.  잡음 분산 {NOISE_SD ** 2:.4f} 은 줄일 수 없는 하한")
    sets = train_sets()
    print("첫 번째 학습 표본 (앞 5개)")
    for x, y in list(zip(*sets[0]))[:5]:
        print(f"  x={x:+.4f}  y={y:+.4f}")

    print("\n[1] 분해식 검산 — 차수 3, 규제 없음")
    preds = []
    for xs, ys in sets:
        gram, rhs = normal_equations(xs, ys, 3)
        w = fit_ridge(gram, rhs, [0.0] * 4)
        preds.append([predict(w, x) for x in GRID])
    bias_sq, variance = decompose(preds)
    print(f"  편향² {bias_sq:.4f} + 분산 {variance:.4f} + 잡음 {NOISE_SD ** 2:.4f} = {bias_sq + variance + NOISE_SD ** 2:.4f}")
    print(f"  새 잡음을 얹은 시험 관측과 직접 잰 MSE = {simulated_test_mse(preds, random.Random(SEED * 7)):.4f}")

    print("\n[2] 모형 용량(차수)을 올린다 — 규제 없음")
    header()
    systems = {}
    for degree in (1, 2, 3, 5, 7, 9, 12, 15):
        preds = []
        for i, (xs, ys) in enumerate(sets):
            gram, rhs = normal_equations(xs, ys, degree)
            systems[(degree, i)] = (gram, rhs)
            w = fit_ridge(gram, rhs, [0.0] * (degree + 1))
            preds.append([predict(w, x) for x in GRID])
        report(f"차수 {degree}", preds)

    print("\n[3] L2 규제 — 차수 15, 벌점 lambda * sum w_j^2 (절편 제외)")
    header(f" {'계수 크기':>10}")
    for rate in (0.0, 1e-4, 1e-3, 1e-2, 1e-1, 1.0, 10.0):
        preds, norms = [], []
        for i in range(TRIALS):
            gram, rhs = systems[(15, i)]
            w = fit_ridge(gram, rhs, [0.0] + [rate] * 15)
            norms.append(math.sqrt(sum(v * v for v in w[1:])))
            preds.append([predict(w, x) for x in GRID])
        report(f"λ={rate:g}", preds, f" {sum(norms) / TRIALS:>10.2f}")

    print("\n[4] L1 규제 — 차수 15, 벌점 lambda * sum |w_j| (절편 제외), 좌표 하강 200회")
    header(f" {'0인 계수':>10}")
    for rate in (0.01, 0.1, 0.5, 2.0):
        preds, zeros = [], []
        for i in range(TRIALS):
            gram, rhs = systems[(15, i)]
            w = fit_lasso(gram, rhs, rate)
            zeros.append(sum(1 for v in w[1:] if v == 0.0))
            preds.append([predict(w, x) for x in GRID])
        report(f"λ={rate:g}", preds, f" {sum(zeros) / TRIALS:>7.2f}/15")

    print("\n[5] 조기 종료 — 차수 15, w=0 에서 출발한 경사 하강, 학습률 1/trace(G)")
    header(f" {'계수 크기':>10}")
    checkpoints = (10, 100, 1000, 10000, 100000, 1000000)
    stopped = {t: [] for t in checkpoints}
    for i in range(TRIALS):
        gram, rhs = systems[(15, i)]
        for t, w in fit_early_stopping(gram, rhs, checkpoints).items():
            stopped[t].append(w)
    for t in checkpoints:
        preds = [[predict(w, x) for x in GRID] for w in stopped[t]]
        norm = sum(math.sqrt(sum(v * v for v in w[1:])) for w in stopped[t]) / TRIALS
        report(f"t={t}", preds, f" {norm:>10.2f}")

    print("\n[6] 드롭아웃(입력 유지 확률 p)을 주변화한 목적식 — 차수 15")
    print("    ||y - Xw||^2 + (1-p)/p * ||Γw||^2,  Γ = diag(XᵀX)^(1/2), 절편은 떨구지 않는다")
    header()
    for keep in (1.0, 0.95, 0.9, 0.7, 0.5):
        preds = []
        for i in range(TRIALS):
            gram, rhs = systems[(15, i)]
            factor = (1.0 - keep) / keep
            penalties = [0.0] + [factor * gram[j][j] for j in range(1, 16)]
            w = fit_ridge(gram, rhs, penalties)
            preds.append([predict(w, x) for x in GRID])
        report(f"p={keep:g}", preds)

    print("\n[7] 교차검증으로 L2 강도를 고른다 — 차수 15, 학습 표본마다 5-겹 CV")
    grid = (1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1.0, 10.0)
    chosen, preds = [], []
    for xs, ys in sets:
        scores = {}
        for rate in grid:
            err = 0.0
            for k in range(5):
                train_idx = [j for j in range(len(xs)) if j % 5 != k]
                held_idx = [j for j in range(len(xs)) if j % 5 == k]
                gram, rhs = normal_equations([xs[j] for j in train_idx], [ys[j] for j in train_idx], 15)
                w = fit_ridge(gram, rhs, [0.0] + [rate] * 15)
                err += sum((predict(w, xs[j]) - ys[j]) ** 2 for j in held_idx)
            scores[rate] = err / len(xs)
        best = min(scores, key=scores.get)
        chosen.append(best)
        gram, rhs = normal_equations(xs, ys, 15)
        w = fit_ridge(gram, rhs, [0.0] + [best] * 15)
        preds.append([predict(w, x) for x in GRID])
    counts = {rate: chosen.count(rate) for rate in grid}
    print("  고른 λ 분포: " + ", ".join(f"{rate:g}→{n}" for rate, n in counts.items() if n))
    header()
    report("CV 선택", preds)

    print("\n[8] 데이터를 늘린다 — 차수 15, 규제 없음")
    header()
    for size in (20, 40, 80):
        preds = []
        for xs, ys in train_sets(size):
            gram, rhs = normal_equations(xs, ys, 15)
            w = fit_ridge(gram, rhs, [0.0] * 16)
            preds.append([predict(w, x) for x in GRID])
        report(f"N={size}", preds)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
