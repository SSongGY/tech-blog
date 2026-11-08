"""A/B 테스트의 세 계산 — 표본 크기, 두 비율 z 검정, SRM 검사 — 과 중간 확인(peeking)의 함정.

표준 라이브러리만 쓴다. 정규분포는 statistics.NormalDist, 난수는 시드를 고정한 random.Random.
"""
import math
import platform
import random
from statistics import NormalDist

STD_NORMAL = NormalDist()


def sample_size_per_group(p_control, p_treatment, alpha=0.05, power=0.80):
    """두 비율 비교에 필요한 군당 표본 수 (양측, 정규 근사)."""
    z_alpha = STD_NORMAL.inv_cdf(1 - alpha / 2)
    z_beta = STD_NORMAL.inv_cdf(power)
    p_bar = (p_control + p_treatment) / 2
    delta = abs(p_treatment - p_control)
    numerator = (z_alpha * math.sqrt(2 * p_bar * (1 - p_bar))
                 + z_beta * math.sqrt(p_control * (1 - p_control)
                                      + p_treatment * (1 - p_treatment)))
    return math.ceil(numerator ** 2 / delta ** 2)


def two_proportion_z(x1, n1, x2, n2):
    """NIST/SEMATECH 7.3.3 의 합동(pooled) z 통계량과 양측 p-value."""
    p1, p2 = x1 / n1, x2 / n2
    p_pool = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    z = (p2 - p1) / se
    return z, 2 * (1 - STD_NORMAL.cdf(abs(z)))


def srm_chi_square(observed, ratios):
    """설계한 배분 비율 대비 관측 사용자 수의 카이제곱 적합도 검정 (자유도 1)."""
    total = sum(observed)
    expected = [total * r for r in ratios]
    chi2 = sum((o - e) ** 2 / e for o, e in zip(observed, expected))
    # 자유도 1 카이제곱은 표준정규의 제곱이므로 정규분포로 p-value 를 구한다
    return chi2, 2 * (1 - STD_NORMAL.cdf(math.sqrt(chi2)))


def aa_false_positive_rate(rng, runs, looks, users_per_look, p, alpha):
    """같은 것끼리 비교하는 A/A 실험에서 '유의하다'가 나오는 비율.

    마지막에 한 번만 보는 경우와, 중간마다 보다가 처음 유의할 때 멈추는 경우를 함께 센다.
    """
    z_crit = STD_NORMAL.inv_cdf(1 - alpha / 2)
    final_hits = peek_hits = 0
    for _ in range(runs):
        x1 = x2 = n = 0
        stopped = False
        for _ in range(looks):
            x1 += rng.binomialvariate(users_per_look, p)
            x2 += rng.binomialvariate(users_per_look, p)
            n += users_per_look
            z, _ = two_proportion_z(x1, n, x2, n)
            if not stopped and abs(z) > z_crit:
                stopped = True
        final_hits += abs(z) > z_crit
        peek_hits += stopped
    return final_hits / runs, peek_hits / runs


def main():
    print(f"Python {platform.python_version()}")

    print("\n[1] 표본 크기 — 기준 전환율 5.0%, 최소 검출 효과 +0.5%p, α=0.05(양측), 검정력 80%")
    p_c, p_t = 0.050, 0.055
    n_exact = sample_size_per_group(p_c, p_t)
    z_sum_sq = 2 * (STD_NORMAL.inv_cdf(0.975) + STD_NORMAL.inv_cdf(0.80)) ** 2
    variance = p_c * (1 - p_c)
    n_rule = math.ceil(16 * variance / (p_t - p_c) ** 2)
    print(f"  두 비율 공식      : 군당 {n_exact:,}명 (총 {2 * n_exact:,}명)")
    print(f"  2(z0.975+z0.80)^2 = {z_sum_sq:.2f}  -> 어림 계수 16")
    print(f"  16σ²/Δ² 어림      : 군당 {n_rule:,}명 (σ²=p(1-p)={variance:.4f})")
    for mde in (0.0025, 0.0010):
        n = sample_size_per_group(p_c, p_c + mde)
        print(f"  효과를 +{mde * 100:.2f}%p 로 줄이면 : 군당 {n:,}명")

    print("\n[2] 결과 판정 — 두 비율 z 검정 (NIST/SEMATECH 7.3.3)")
    x_c, n_c, x_t, n_t = 1_550, 31_000, 1_705, 31_000
    z, p_value = two_proportion_z(x_c, n_c, x_t, n_t)
    lift = (x_t / n_t) / (x_c / n_c) - 1
    print(f"  대조군 A : {x_c:,}/{n_c:,} = {x_c / n_c:.2%}")
    print(f"  실험군 B : {x_t:,}/{n_t:,} = {x_t / n_t:.2%}  (상대 개선 {lift:+.1%})")
    print(f"  z = {z:.3f}, 양측 p-value = {p_value:.4f} -> "
          f"{'귀무가설 기각(유의)' if p_value < 0.05 else '기각 못 함'}")

    print("\n[3] SRM 검사 — 설계 50:50, 카이제곱 적합도, 임계 p < 0.0005")
    for observed in ((31_000, 31_000), (31_150, 30_850), (31_600, 30_400)):
        chi2, p_srm = srm_chi_square(observed, (0.5, 0.5))
        verdict = "SRM — 결과를 쓰지 않는다" if p_srm < 0.0005 else "정상"
        print(f"  A={observed[0]:,} B={observed[1]:,} : χ²={chi2:6.2f}, "
              f"p={p_srm:.2e} -> {verdict}")

    print("\n[4] A/A 실험 10,000회 — 전환율 5%, 군당 200명씩 10번 나눠 유입, α=0.05")
    rng = random.Random(20261109)
    final_rate, peek_rate = aa_false_positive_rate(
        rng, runs=10_000, looks=10, users_per_look=200, p=0.05, alpha=0.05)
    print(f"  마지막에 한 번만 판정         : 거짓 양성 {final_rate:.2%}")
    print(f"  매번 들여다보고 유의하면 멈춤 : 거짓 양성 {peek_rate:.2%}")


if __name__ == "__main__":
    main()
