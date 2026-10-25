"""AR(1)·MA(1) 모형을 생성해 ACF·PACF 가 이론값대로 끊기는지 확인한다.

NIST/SEMATECH e-Handbook §6.4.4.4 의 모형식과 §6.4.4.6 의 식별 규칙을 그대로
따라간다. 표준 라이브러리만 쓴다 — 난수·제곱근 외에 필요한 것이 없다.

  AR(p): X_t = delta + phi_1 X_{t-1} + ... + phi_p X_{t-p} + A_t
  MA(q): X_t = mu + A_t - theta_1 A_{t-1} - ... - theta_q A_{t-q}

MA 항의 부호가 음수인 것은 핸드북 표기를 따른 것이다. 부호 규약이 책마다
갈리므로 이론 ACF 를 계산할 때 같은 규약을 써야 값이 맞는다.
"""

import math
import random

SERIES_LENGTH = 2000
SEED = 20261026
MAX_LAG = 8


def simulate_ar1(phi, mu, sigma, n, rng):
    """AR(1) 표본경로. 초기값은 정상분포의 평균에서 출발시키고 앞을 버린다."""
    burn_in = 500
    series = []
    x = mu
    for _ in range(burn_in + n):
        x = mu + phi * (x - mu) + rng.gauss(0.0, sigma)
        series.append(x)
    return series[burn_in:]


def simulate_ma1(theta, mu, sigma, n, rng):
    """MA(1) 표본경로. 백색잡음 두 개만 있으면 되므로 버닝이 필요 없다."""
    series = []
    previous_shock = rng.gauss(0.0, sigma)
    for _ in range(n):
        shock = rng.gauss(0.0, sigma)
        series.append(mu + shock - theta * previous_shock)
        previous_shock = shock
    return series


def sample_acf(series, max_lag):
    """표본 자기상관. 분모를 전체 편차제곱합으로 고정하는 통상 추정량이다."""
    n = len(series)
    mean = sum(series) / n
    deviations = [value - mean for value in series]
    denominator = sum(d * d for d in deviations)
    acf = []
    for lag in range(1, max_lag + 1):
        numerator = sum(deviations[t] * deviations[t - lag] for t in range(lag, n))
        acf.append(numerator / denominator)
    return acf


def pacf_from_acf(acf):
    """Durbin-Levinson 재귀로 편자기상관을 뽑는다.

    PACF 의 k 차 값은 'k-1 차까지의 영향을 걷어낸 뒤 남는 상관'이라서,
    AR(p) 에서 p 를 넘는 순간 0 이 된다. 이 성질이 식별 규칙의 근거다.
    """
    pacf = []
    coefficients = []
    for k in range(1, len(acf) + 1):
        if k == 1:
            phi_kk = acf[0]
        else:
            numerator = acf[k - 1] - sum(coefficients[j] * acf[k - 2 - j] for j in range(k - 1))
            denominator = 1.0 - sum(coefficients[j] * acf[j] for j in range(k - 1))
            phi_kk = numerator / denominator
        updated = [coefficients[j] - phi_kk * coefficients[k - 2 - j] for j in range(k - 1)]
        coefficients = updated + [phi_kk]
        pacf.append(phi_kk)
    return pacf


def theoretical_ar1_acf(phi, max_lag):
    return [phi ** lag for lag in range(1, max_lag + 1)]


def theoretical_ma1_acf(theta, max_lag):
    rho1 = -theta / (1.0 + theta * theta)
    return [rho1] + [0.0] * (max_lag - 1)


def print_table(title, theoretical, sample_acf_values, sample_pacf_values, band):
    print(title)
    print("  lag |  이론 ACF |  표본 ACF | 표본 PACF | 유의대역 밖?")
    print("  ----+-----------+-----------+-----------+-------------")
    for index, lag in enumerate(range(1, len(sample_acf_values) + 1)):
        acf_flag = "ACF" if abs(sample_acf_values[index]) > band else "   "
        pacf_flag = "PACF" if abs(sample_pacf_values[index]) > band else "    "
        print(
            f"  {lag:3d} | {theoretical[index]:9.4f} | {sample_acf_values[index]:9.4f} "
            f"| {sample_pacf_values[index]:9.4f} | {acf_flag} {pacf_flag}"
        )
    print()


def main():
    rng = random.Random(SEED)
    band = 2.0 / math.sqrt(SERIES_LENGTH)

    print(f"표본 길이 N = {SERIES_LENGTH}, 난수 시드 = {SEED}")
    print(f"유의대역 ±2/√N = ±{band:.4f}  (핸드북 §6.4.4.6 의 95% 기준)")
    print()

    phi = 0.7
    ar_series = simulate_ar1(phi=phi, mu=10.0, sigma=1.0, n=SERIES_LENGTH, rng=rng)
    ar_acf = sample_acf(ar_series, MAX_LAG)
    print_table(
        f"[AR(1)] X_t = delta + {phi} X_(t-1) + A_t     이론: ACF 는 지수감쇠, PACF 는 lag 1 이후 0",
        theoretical_ar1_acf(phi, MAX_LAG),
        ar_acf,
        pacf_from_acf(ar_acf),
        band,
    )

    theta = 0.7
    ma_series = simulate_ma1(theta=theta, mu=10.0, sigma=1.0, n=SERIES_LENGTH, rng=rng)
    ma_acf = sample_acf(ma_series, MAX_LAG)
    print_table(
        f"[MA(1)] X_t = mu + A_t - {theta} A_(t-1)      이론: ACF 는 lag 1 이후 0, PACF 는 지수감쇠",
        theoretical_ma1_acf(theta, MAX_LAG),
        ma_acf,
        pacf_from_acf(ma_acf),
        band,
    )

    print("[정상성] AR(1) 은 |phi| < 1 일 때만 분산이 수렴한다")
    print("  phi   | 이론 분산 sigma^2/(1-phi^2) | 표본 분산")
    print("  ------+-----------------------------+----------")
    for candidate in (0.3, 0.7, 0.95, 1.0):
        trial = simulate_ar1(phi=candidate, mu=0.0, sigma=1.0, n=SERIES_LENGTH, rng=random.Random(SEED))
        mean = sum(trial) / len(trial)
        variance = sum((v - mean) ** 2 for v in trial) / (len(trial) - 1)
        if abs(candidate) < 1.0:
            expected = f"{1.0 / (1.0 - candidate * candidate):27.4f}"
        else:
            expected = f"{'발산 (정상성 없음)':>25}"
        print(f"  {candidate:5.2f} | {expected} | {variance:9.4f}")
    print()
    print("  phi = 1.00 은 임의보행이다. 분산이 t 에 비례해 커지므로 표본 분산이")
    print("  표본 길이에 따라 달라진다 — 차분해서 정상계열로 만든 뒤 모형을 세운다.")


if __name__ == "__main__":
    main()
