"""정상만 학습한 오토인코더가 '지표 간 관계가 깨진' 점을 재구성 오차로 잡는지,
학습 데이터에 같은 이상이 섞이면 그 능력이 어떻게 무너지는지 확인한다.
표준 라이브러리만 쓴다 — 4-8-2-8-4 오토인코더와 역전파를 직접 구현했다."""
import math
import platform
import random
import sys

INPUT_DIM = 4
HIDDEN_DIM = 8
CODE_DIM = 2          # 정상 데이터의 자유도(u, v)와 같게 둔다 — 병목이 곧 '정상의 차원'이다
EPOCHS = 300
LEARNING_RATE = 0.01
NOISE_SD = 0.02


def normal_point(rng):
    """정상: 두 잠재 변수 u, v 로 네 지표가 정해진다. 셋째 지표는 u·v 와 같이 움직인다."""
    u, v = rng.uniform(-1, 1), rng.uniform(-1, 1)
    x = (u, v, u * v, u * u)
    return tuple(c + rng.gauss(0, NOISE_SD) for c in x)


def broken_point(rng):
    """이상: 네 값은 모두 정상 범위 안인데 셋째 지표만 부호가 뒤집혀 관계가 깨졌다."""
    u, v = rng.uniform(0.4, 1), rng.uniform(0.4, 1)
    x = (u, v, -u * v, u * u)
    return tuple(c + rng.gauss(0, NOISE_SD) for c in x)


class Dense:
    def __init__(self, n_in, n_out, activation, rng):
        bound = math.sqrt(6.0 / (n_in + n_out))
        self.w = [[rng.uniform(-bound, bound) for _ in range(n_in)] for _ in range(n_out)]
        self.b = [0.0] * n_out
        self.activation = activation
        # Adam 의 1·2차 모멘트
        self.mw = [[0.0] * n_in for _ in range(n_out)]
        self.vw = [[0.0] * n_in for _ in range(n_out)]
        self.mb = [0.0] * n_out
        self.vb = [0.0] * n_out

    def forward(self, x):
        self.x = x
        z = [sum(wi * xi for wi, xi in zip(row, x)) + b for row, b in zip(self.w, self.b)]
        self.y = [math.tanh(v) for v in z] if self.activation == "tanh" else z
        return self.y

    def backward(self, grad_y):
        if self.activation == "tanh":
            grad_z = [g * (1 - y * y) for g, y in zip(grad_y, self.y)]
        else:
            grad_z = grad_y
        self.gw = [[gz * xi for xi in self.x] for gz in grad_z]
        self.gb = grad_z
        return [sum(self.w[o][i] * grad_z[o] for o in range(len(grad_z))) for i in range(len(self.x))]

    def step(self, t, lr, beta1=0.9, beta2=0.999, eps=1e-8):
        c1, c2 = 1 - beta1 ** t, 1 - beta2 ** t
        for o in range(len(self.w)):
            for i in range(len(self.w[o])):
                g = self.gw[o][i]
                self.mw[o][i] = beta1 * self.mw[o][i] + (1 - beta1) * g
                self.vw[o][i] = beta2 * self.vw[o][i] + (1 - beta2) * g * g
                self.w[o][i] -= lr * (self.mw[o][i] / c1) / (math.sqrt(self.vw[o][i] / c2) + eps)
            g = self.gb[o]
            self.mb[o] = beta1 * self.mb[o] + (1 - beta1) * g
            self.vb[o] = beta2 * self.vb[o] + (1 - beta2) * g * g
            self.b[o] -= lr * (self.mb[o] / c1) / (math.sqrt(self.vb[o] / c2) + eps)


class Autoencoder:
    def __init__(self, rng):
        self.layers = [Dense(INPUT_DIM, HIDDEN_DIM, "tanh", rng),
                       Dense(HIDDEN_DIM, CODE_DIM, "linear", rng),   # 인코더 끝 = 병목
                       Dense(CODE_DIM, HIDDEN_DIM, "tanh", rng),
                       Dense(HIDDEN_DIM, INPUT_DIM, "linear", rng)]
        self.t = 0

    def reconstruct(self, x):
        for layer in self.layers:
            x = layer.forward(x)
        return x

    def error(self, x):
        """재구성 오차 = 입력과 복원값의 제곱 오차 합. 이것이 이상 점수다."""
        return sum((a - b) ** 2 for a, b in zip(x, self.reconstruct(x)))

    def fit(self, data, rng):
        for _ in range(EPOCHS):
            order = data[:]
            rng.shuffle(order)
            for x in order:
                out = self.reconstruct(x)
                grad = [2 * (o - xi) for o, xi in zip(out, x)]
                for layer in reversed(self.layers):
                    grad = layer.backward(grad)
                self.t += 1
                for layer in self.layers:
                    layer.step(self.t, LEARNING_RATE)
        return self


def percentile(values, q):
    s = sorted(values)
    return s[min(len(s) - 1, int(math.ceil(q * len(s))) - 1)]


def evaluate(label, model, valid, test_normal, test_broken):
    # 임계값은 정상 검증 데이터의 오차 분포에서만 정한다 — 이상 레이블을 쓰지 않는다
    threshold = percentile([model.error(x) for x in valid], 0.99)
    e_normal = [model.error(x) for x in test_normal]
    e_broken = [model.error(x) for x in test_broken]
    false_alarm = sum(e > threshold for e in e_normal) / len(e_normal)
    detected = sum(e > threshold for e in e_broken) / len(e_broken)
    print(f"  {label:<26}{sum(e_normal) / len(e_normal):>10.4f}{sum(e_broken) / len(e_broken):>10.4f}"
          f"{threshold:>10.4f}{detected:>8.2f}{false_alarm:>8.2f}")
    return [(x, e) for x, e in zip(test_normal, e_normal)]


def in_broken_region(x):
    """이상 점이 생기는 (u, v) 자리 — 같은 자리에서 셋째 지표가 정상과 이상으로 갈린다."""
    return x[0] >= 0.4 and x[1] >= 0.4


def print_region_breakdown(label, pairs):
    inside = [e for x, e in pairs if in_broken_region(x)]
    outside = [e for x, e in pairs if not in_broken_region(x)]
    print(f"  {label:<26}{sum(inside) / len(inside):>12.4f} ({len(inside):>3}점)"
          f"{sum(outside) / len(outside):>12.4f} ({len(outside):>3}점)")


def main():
    rng = random.Random(7)
    train_normal = [normal_point(rng) for _ in range(400)]
    contamination = [broken_point(rng) for _ in range(40)]
    valid = [normal_point(rng) for _ in range(200)]
    test_normal = [normal_point(rng) for _ in range(200)]
    test_broken = [broken_point(rng) for _ in range(50)]

    print(f"Python {platform.python_version()} ({sys.platform}) · 표준 라이브러리만 사용\n")
    print("[데이터]")
    print("  정상  x = (u, v, u·v, u²) + 잡음,  u, v ~ U(-1, 1)")
    print("  이상  x = (u, v, -u·v, u²) + 잡음, u, v ~ U(0.4, 1)  — 셋째 지표 부호만 뒤집음")
    print(f"  학습 정상 {len(train_normal)} · 오염용 이상 {len(contamination)} · 검증 정상 {len(valid)}"
          f" · 평가 정상 {len(test_normal)} · 평가 이상 {len(test_broken)}")
    print(f"  구조 {INPUT_DIM}-{HIDDEN_DIM}-{CODE_DIM}-{HIDDEN_DIM}-{INPUT_DIM}, Adam, 에폭 {EPOCHS}\n")

    lows = [min(x[i] for x in train_normal) for i in range(INPUT_DIM)]
    highs = [max(x[i] for x in train_normal) for i in range(INPUT_DIM)]
    inside = sum(all(lo <= c <= hi for c, lo, hi in zip(x, lows, highs)) for x in test_broken)
    print("[실험1] 지표별 범위 검사 — 학습 정상의 지표별 최소~최대 안에 드는 이상 점")
    print(f"  {inside} / {len(test_broken)}  (지표마다 따로 임계값을 걸면 이만큼을 놓친다)\n")

    print("[실험2] 재구성 오차 — 임계값은 검증 정상 오차의 99백분위")
    print(f"  {'학습 데이터':<26}{'정상 오차':>10}{'이상 오차':>10}{'임계값':>10}{'탐지율':>8}{'오경보':>8}")
    clean = Autoencoder(random.Random(11)).fit(train_normal, random.Random(12))
    clean_pairs = evaluate("정상 400", clean, valid, test_normal, test_broken)
    dirty = Autoencoder(random.Random(11)).fit(train_normal + contamination, random.Random(12))
    dirty_pairs = evaluate("정상 400 + 이상 40 (9.1%)", dirty, valid, test_normal, test_broken)

    print("\n[실험3] 평가 정상 점의 재구성 오차를 자리별로 — 이상이 생기는 자리 u, v >= 0.4 안과 밖")
    print(f"  {'학습 데이터':<26}{'자리 안':>18}{'자리 밖':>18}")
    print_region_breakdown("정상 400", clean_pairs)
    print_region_breakdown("정상 400 + 이상 40 (9.1%)", dirty_pairs)


if __name__ == "__main__":
    main()
