"""가설 검정의 α·β·검정력·표본 크기를 공식으로 계산하고 모의실험으로 검산한다.

python power_and_errors.py

z 검정(모표준편차 σ 를 안다고 가정)만 쓴다. NIST/SEMATECH e-Handbook
§7.2.2.2 의 표본 크기 공식과 같은 가정이다.
"""

import math
import random
import sys
from statistics import NormalDist

STD_NORMAL = NormalDist()
SEED = 20261109
TRIALS = 20000


def z(p):
    return STD_NORMAL.inv_cdf(p)


def sample_size(alpha, beta, effect, two_sided=True):
    """NIST §7.2.2.2: N = (z_{1-α/2} + z_{1-β})² (σ/δ)². effect 는 δ/σ."""
    z_alpha = z(1 - alpha / 2) if two_sided else z(1 - alpha)
    return (z_alpha + z(1 - beta)) ** 2 / effect ** 2


def power(alpha, n, effect, two_sided=True):
    """참 평균이 δ 만큼 옮겨졌을 때 귀무가설을 기각할 확률."""
    shift = effect * math.sqrt(n)
    if two_sided:
        crit = z(1 - alpha / 2)
        return (1 - STD_NORMAL.cdf(crit - shift)) + STD_NORMAL.cdf(-crit - shift)
    return 1 - STD_NORMAL.cdf(z(1 - alpha) - shift)


def rejects(rng, n, true_shift, alpha):
    """표본 n 개를 뽑아 양측 z 검정을 한 번 한다."""
    total = sum(rng.gauss(true_shift, 1.0) for _ in range(n))
    z_stat = (total / n) / (1.0 / math.sqrt(n))
    return abs(z_stat) > z(1 - alpha / 2)


def main():
    print(f"Python {sys.version.split()[0]} · 난수 시드 {SEED} · 모의실험 {TRIALS:,}회")

    print("\n### 1. NIST 예제 재현 — 단측 α=0.05, β=0.10, δ=1σ")
    n_one = sample_size(0.05, 0.10, 1.0, two_sided=False)
    n_two = sample_size(0.05, 0.10, 1.0, two_sided=True)
    print(f"  z_0.95={z(0.95):.3f}  z_0.90={z(0.90):.3f}")
    print(f"  단측 N = ({z(0.95):.3f} + {z(0.90):.3f})^2 = {n_one:.3f} -> {math.ceil(n_one)}")
    print(f"  양측 N = ({z(0.975):.3f} + {z(0.90):.3f})^2 = {n_two:.3f} -> {math.ceil(n_two)}")

    print("\n### 2. 표본을 고정하면 α 를 줄일수록 β 가 커진다 (n=16, δ=0.5σ, 양측)")
    print("  alpha | 임계값 z | power  | beta")
    for alpha in (0.10, 0.05, 0.01, 0.001):
        p = power(alpha, 16, 0.5)
        print(f"  {alpha:5.3f} | {z(1 - alpha / 2):8.3f} | {p:.4f} | {1 - p:.4f}")

    print("\n### 3. 표본이 늘면 검정력이 오른다 (α=0.05 양측, δ=0.5σ)")
    print("   n  | power")
    for n in (8, 16, 24, 32, 42, 64):
        print(f"  {n:3d} | {power(0.05, n, 0.5):.4f}")

    print("\n### 4. 효과가 작아지면 표본은 제곱으로 는다 (α=0.05 양측, 검정력 0.80)")
    print("  δ/σ  | N 계산값  | 올림")
    for effect in (1.0, 0.5, 0.25, 0.1):
        n = sample_size(0.05, 0.20, effect)
        print(f"  {effect:4.2f} | {n:9.2f} | {math.ceil(n):5d}")
    print(f"  상수 (z_0.975+z_0.80)^2 = {(z(0.975) + z(0.80)) ** 2:.3f}")

    print("\n### 5. 모의실험 검산 — n=32, α=0.05 양측")
    rng = random.Random(SEED)
    for label, shift, expected in (
        ("H0 참 (δ=0)   -> 1종 오류율", 0.0, 0.05),
        ("H1 참 (δ=0.5σ) -> 검정력", 0.5, power(0.05, 32, 0.5)),
    ):
        hits = sum(rejects(rng, 32, shift, 0.05) for _ in range(TRIALS))
        print(f"  {label}: 모의 {hits / TRIALS:.4f} / 공식 {expected:.4f}")

    print("\n### 6. 다중 비교 — H0 가 모두 참인 검정 m 개 중 하나라도 기각될 확률")
    k = TRIALS // 4
    # 모의실험 비율의 표준오차 — 이 폭 안의 흔들림은 우연이다
    print(f"  모의 {k:,}회, α 근처 비율의 표준오차 ≈ {math.sqrt(0.05 * 0.95 / k):.4f}")
    print("   m  | 1-(1-α)^m | 모의(α 그대로) | 1-(1-α/m)^m | 모의(Bonferroni α/m)")
    rng = random.Random(SEED)
    for m in (1, 5, 10, 20):
        plain = bonf = 0
        for _ in range(TRIALS // 4):
            p_values = [2 * (1 - STD_NORMAL.cdf(abs(rng.gauss(0, 1)))) for _ in range(m)]
            plain += min(p_values) < 0.05
            bonf += min(p_values) < 0.05 / m
        print(f"  {m:3d} | {1 - 0.95 ** m:9.4f} | {plain / k:14.4f} |"
              f" {1 - (1 - 0.05 / m) ** m:11.4f} | {bonf / k:.4f}")

    print("\n### 7. 중간 확인(peeking) — H0 참, 총 200개를 k 번 나눠 보며 유의하면 멈춤")
    print("   k  | 거짓 양성")
    rng = random.Random(SEED)
    for looks in (1, 2, 5, 10, 20):
        step = 200 // looks
        hits = 0
        for _ in range(TRIALS // 4):
            total = 0.0
            for i in range(1, looks + 1):
                total += sum(rng.gauss(0, 1) for _ in range(step))
                n = step * i
                if abs(total / math.sqrt(n)) > z(0.975):
                    hits += 1
                    break
        print(f"  {looks:3d} | {hits / (TRIALS // 4):.4f}")


if __name__ == "__main__":
    main()
