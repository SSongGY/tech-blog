"""과적합·과소적합의 원인과 해결 방안을 다항 회귀로 검산한다.

참 함수 sin(pi x) 에 잡음을 얹은 표본 20개로 다항식을 맞추고,
모형 용량(차수)·데이터 양·L2 규제·교차검증이 학습 오차와 시험 오차를
각각 어떻게 움직이는지 본다. 외부 의존성 없이 표준 라이브러리만 쓴다.
"""

import math
import platform
import random
import sys

NOISE_SD = 0.2
TRAIN_SIZE = 20
TEST_SIZE = 2000
SEED = 7


def true_function(x):
    return math.sin(math.pi * x)


def make_data(size, rng):
    xs = [rng.uniform(-1.0, 1.0) for _ in range(size)]
    ys = [true_function(x) + rng.gauss(0.0, NOISE_SD) for x in xs]
    return xs, ys


def make_train(size, rng):
    # 학습 x 를 구간에 고르게 깐다. 순수 난수로 뽑으면 양 끝이 비어,
    # 과적합이 아니라 외삽 실패가 시험 오차를 지배한다.
    step = 2.0 / size
    xs = [-1.0 + step * (i + rng.uniform(0.1, 0.9)) for i in range(size)]
    ys = [true_function(x) + rng.gauss(0.0, NOISE_SD) for x in xs]
    return xs, ys


def legendre_features(x, degree):
    # 단항식 x^k 대신 르장드르 다항식을 쓴다. [-1, 1]에서 직교에 가까워
    # 고차에서도 정규방정식이 수치적으로 무너지지 않는다.
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


def fit(xs, ys, degree, l2_rate=0.0):
    rows = [legendre_features(x, degree) for x in xs]
    width = degree + 1
    gram = [[sum(row[i] * row[j] for row in rows) for j in range(width)] for i in range(width)]
    # 절편은 규제하지 않는다. 절편까지 0으로 끌면 평균 수준부터 틀어진다.
    for i in range(1, width):
        gram[i][i] += l2_rate
    rhs = [sum(row[i] * y for row, y in zip(rows, ys)) for i in range(width)]
    return solve(gram, rhs)


def predict(weights, x):
    return sum(w * f for w, f in zip(weights, legendre_features(x, len(weights) - 1)))


def mse(weights, xs, ys):
    return sum((predict(weights, x) - y) ** 2 for x, y in zip(xs, ys)) / len(xs)


def weight_norm(weights):
    return math.sqrt(sum(w * w for w in weights[1:]))


def cross_validate(xs, ys, degree, folds):
    indices = list(range(len(xs)))
    errors = []
    for k in range(folds):
        held = set(indices[k::folds])
        train_x = [xs[i] for i in indices if i not in held]
        train_y = [ys[i] for i in indices if i not in held]
        weights = fit(train_x, train_y, degree)
        errors.append(mse(weights, [xs[i] for i in held], [ys[i] for i in held]))
    return sum(errors) / folds


def main():
    print(f"Python {platform.python_version()} / {platform.system()} / seed={SEED}")
    print(f"참 함수 y = sin(pi x) + N(0, {NOISE_SD}^2),  x ~ U(-1, 1)")
    print(f"잡음 분산 {NOISE_SD ** 2:.4f} 이 어떤 모형으로도 줄일 수 없는 시험 오차의 하한이다")

    rng = random.Random(SEED)
    train_x, train_y = make_train(TRAIN_SIZE, rng)
    test_x, test_y = make_data(TEST_SIZE, rng)
    print(f"학습 표본 {TRAIN_SIZE}개 (앞 5개), 시험 표본 {TEST_SIZE}개")
    for x, y in list(zip(train_x, train_y))[:5]:
        print(f"  x={x:+.4f}  y={y:+.4f}")

    print(f"\n[1] 모형 용량(다항식 차수)을 올린다 — 학습 표본 {TRAIN_SIZE}개, 규제 없음")
    print(f"{'차수':>4} {'학습 MSE':>10} {'시험 MSE':>12} {'격차':>12} {'계수 크기':>10}")
    for degree in (0, 1, 3, 5, 9, 15, 19):
        weights = fit(train_x, train_y, degree)
        tr, te = mse(weights, train_x, train_y), mse(weights, test_x, test_y)
        print(f"{degree:>4} {tr:>10.4f} {te:>12.4f} {te - tr:>12.4f} {weight_norm(weights):>10.2f}")

    print("\n[2] 데이터를 늘린다 — 차수 15 고정, 규제 없음")
    print(f"{'표본 수':>6} {'학습 MSE':>10} {'시험 MSE':>10}")
    for size in (TRAIN_SIZE, 40, 100, 1000):
        if size == TRAIN_SIZE:
            more_x, more_y = train_x, train_y
        else:
            more_x, more_y = make_train(size, random.Random(SEED + size))
        weights = fit(more_x, more_y, 15)
        print(f"{size:>6} {mse(weights, more_x, more_y):>10.4f} {mse(weights, test_x, test_y):>10.4f}")

    print(f"\n[3] L2 규제 강도를 올린다 — 차수 15, 학습 표본 {TRAIN_SIZE}개")
    print(f"{'lambda':>8} {'학습 MSE':>10} {'시험 MSE':>10} {'계수 크기':>10}")
    for l2_rate in (0.0, 1e-4, 1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0):
        weights = fit(train_x, train_y, 15, l2_rate)
        print(f"{l2_rate:>8g} {mse(weights, train_x, train_y):>10.4f} "
              f"{mse(weights, test_x, test_y):>10.4f} {weight_norm(weights):>10.2f}")

    print("\n[4] 5-겹 교차검증으로 차수를 고른다 — 시험 표본은 보지 않는다")
    print(f"{'차수':>4} {'CV MSE':>12} {'시험 MSE(참고)':>16}")
    scores = {}
    for degree in range(0, 12):
        scores[degree] = cross_validate(train_x, train_y, degree, folds=5)
        test_error = mse(fit(train_x, train_y, degree), test_x, test_y)
        print(f"{degree:>4} {scores[degree]:>12.4f} {test_error:>16.4f}")
    chosen = min(scores, key=scores.get)
    print(f"교차검증이 고른 차수: {chosen}")

    print(f"\n[5] 학습 표본만 바꿔 다시 맞춘다 — 표본 {TRAIN_SIZE}개를 5번 새로 뽑는다")
    print(f"{'차수':>4} {'시험 MSE 5회':>44}")
    for degree in (1, 3, 15):
        errors = []
        for trial in range(5):
            redo_x, redo_y = make_train(TRAIN_SIZE, random.Random(SEED * 100 + trial))
            errors.append(mse(fit(redo_x, redo_y, degree), test_x, test_y))
        print(f"{degree:>4}   " + "  ".join(f"{e:>9.4f}" for e in errors))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
