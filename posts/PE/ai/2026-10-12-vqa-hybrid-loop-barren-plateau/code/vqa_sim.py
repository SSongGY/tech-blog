"""변분 양자 알고리즘(VQA)의 하이브리드 루프와 기울기 소실 고원을 상태벡터로 계산한다.

외부 의존성 없이 표준 라이브러리만 쓴다. 양자 하드웨어가 아니라 고전 시뮬레이션이다.
측정 표본 추출 없이 기댓값을 정확히 계산하므로, 실제 장치의 측정 잡음·하드웨어 잡음은 없다.

회로는 RY 회전과 CZ만 쓰는 하드웨어 효율형 안사츠다. 두 게이트 모두 실수 행렬이라
상태벡터를 실수 리스트로 다룰 수 있다.
"""

import math
import random
import statistics
import sys
import time


# ---------------------------------------------------------------------------
# 상태벡터 시뮬레이터: 인덱스의 q번째 비트가 큐비트 q의 값이다
# ---------------------------------------------------------------------------
def apply_ry(state, qubit, theta):
    c, s = math.cos(theta / 2), math.sin(theta / 2)
    mask = 1 << qubit
    for i in range(len(state)):
        if i & mask:
            continue
        j = i | mask
        a, b = state[i], state[j]
        state[i] = c * a - s * b
        state[j] = s * a + c * b


def apply_cz(state, q1, q2):
    both = (1 << q1) | (1 << q2)
    for i in range(len(state)):
        if i & both == both:
            state[i] = -state[i]


def run_ansatz(n_qubits, layers, params):
    """층마다 모든 큐비트에 RY(θ)를 걸고 이웃끼리 CZ로 얽는다."""
    state = [0.0] * (2 ** n_qubits)
    state[0] = 1.0
    k = 0
    for _ in range(layers):
        for q in range(n_qubits):
            apply_ry(state, q, params[k])
            k += 1
        for q in range(n_qubits - 1):
            apply_cz(state, q, q + 1)
    return state


def prob_bit(state, qubit, value):
    mask = 1 << qubit
    return sum(a * a for i, a in enumerate(state) if bool(i & mask) == bool(value))


# 비용 함수 두 가지 — Cerezo 등(2021)의 전역·국소 비용
def global_cost(state, n_qubits):
    """1 - P(모든 큐비트가 0). 측정 대상이 큐비트 전체다."""
    return 1.0 - state[0] ** 2


def local_cost(state, n_qubits, target=0):
    """1 - (큐비트별로 target일 확률의 평균). 측정 대상이 큐비트 하나씩이다."""
    return 1.0 - sum(prob_bit(state, q, target) for q in range(n_qubits)) / n_qubits


def shift_gradient(cost_fn, n_qubits, layers, params, index):
    """매개변수 이동 규칙: RY(θ)는 θ±π/2 두 번 돌린 비용의 차를 2로 나누면 정확한 미분이다."""
    plus, minus = list(params), list(params)
    plus[index] += math.pi / 2
    minus[index] -= math.pi / 2
    c_plus = cost_fn(run_ansatz(n_qubits, layers, plus), n_qubits)
    c_minus = cost_fn(run_ansatz(n_qubits, layers, minus), n_qubits)
    return (c_plus - c_minus) / 2


# ---------------------------------------------------------------------------
def section_shift_rule():
    print("[1] 매개변수 이동 규칙 — 1큐비트 RY(θ)|0>, 비용 <Z> = cos θ")
    print("    θ       이동 규칙         해석적 미분 -sinθ   유한 차분(h=1e-3)")

    def z_expectation(theta):
        state = run_ansatz(1, 1, [theta])
        return state[0] ** 2 - state[1] ** 2

    for theta in (0.3, 1.2, 2.5):
        shift = (z_expectation(theta + math.pi / 2) - z_expectation(theta - math.pi / 2)) / 2
        h = 1e-3
        finite = (z_expectation(theta + h) - z_expectation(theta - h)) / (2 * h)
        print(f"    {theta:<6}  {shift:+.12f}  {-math.sin(theta):+.12f}   {finite:+.12f}")
    print()


def section_hybrid_loop():
    print("[2] 하이브리드 루프 — 2큐비트·2층, 목표 |11>, 국소 비용, 경사하강(학습률 0.4)")
    n, layers = 2, 2
    rng = random.Random(3)
    params = [rng.uniform(0, 2 * math.pi) for _ in range(n * layers)]
    cost = lambda st, nq: local_cost(st, nq, target=1)
    circuit_runs = 0
    for step in range(41):
        c = cost(run_ansatz(n, layers, params), n)
        circuit_runs += 1
        if step % 10 == 0:
            print(f"    반복 {step:>2}: 비용 {c:.6f}  (누적 회로 실행 {circuit_runs}회)")
        if step == 40:
            break
        grad = [shift_gradient(cost, n, layers, params, i) for i in range(len(params))]
        circuit_runs += 2 * len(params)
        params = [p - 0.4 * g for p, g in zip(params, grad)]
    final = run_ansatz(n, layers, params)
    print(f"    마지막 상태에서 |11> 확률: {final[3] ** 2:.6f}")
    print(f"    매개변수 {len(params)}개 -> 기울기 1회에 회로 {2 * len(params)}번")
    print()


def gradient_variance(cost_fn, n_qubits, layers, samples, rng):
    grads = []
    for _ in range(samples):
        params = [rng.uniform(0, 2 * math.pi) for _ in range(n_qubits * layers)]
        grads.append(shift_gradient(cost_fn, n_qubits, layers, params, 0))
    return statistics.pvariance(grads)


def section_barren_plateau():
    print("[3] 기울기 소실 고원 — 무작위 초기화 200회, 첫 매개변수의 기울기 분산")
    print("    큐비트  전역 비용(2층)   국소 비용(2층)   국소 비용(n층)")
    samples = 200
    for n in (2, 4, 6, 8, 10):
        rng = random.Random(100 + n)
        g2 = gradient_variance(global_cost, n, 2, samples, rng)
        l2 = gradient_variance(local_cost, n, 2, samples, rng)
        ln = gradient_variance(local_cost, n, n, samples, rng)
        print(f"    {n:>4}    {g2:.3e}        {l2:.3e}        {ln:.3e}")
    print()


def main():
    print(f"Python {sys.version.split()[0]}")
    print()
    started = time.perf_counter()
    section_shift_rule()
    section_hybrid_loop()
    section_barren_plateau()
    print(f"소요 {time.perf_counter() - started:.1f}초 (고전 시뮬레이션, 측정 잡음 없음)")


if __name__ == "__main__":
    main()
