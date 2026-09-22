"""부트스트랩 재표집의 절차와 신뢰구간 세 가지를 직접 계산해 확인한다.

[1] 복원추출 B회로 표준오차를 추정하고, 알려진 참값과 맞춰 본다
[2] B 를 키우며 백분위수 구간이 언제 안정되는지 본다
[3] 표준·백분위수·BCa 구간을 나란히 놓고 z0, a 가 끝점을 어디로 옮기는지 본다
[4] 중앙값 — 잭나이프 복제값은 두 값뿐이지만 부트스트랩 복제값은 흩어진다

모집단을 지수분포로 둔 이유는 치우친 분포라야 백분위수와 BCa 가 갈리기 때문이다.
지수분포는 참값을 손으로 적을 수 있어 추정값이 맞는지 확인할 수 있다.
"""

import math
import random
import statistics

SEED = 20260922
SAMPLE_SIZE = 25
MEAN = 1.0            # 지수분포 Exp(1)
B_DEFAULT = 4000
B_LADDER = [50, 200, 1000, 4000, 20000]
REPEATS = 20          # 같은 B 를 여러 번 돌려 흔들림을 본다
NORMAL = statistics.NormalDist()


def draw_sample(rng):
    return [rng.expovariate(1 / MEAN) for _ in range(SAMPLE_SIZE)]


def variance(values):
    """1/(n-1) 로 나눈 불편분산."""
    return statistics.variance(values)


def resample(sample, rng):
    n = len(sample)
    return [sample[int(rng.random() * n)] for _ in range(n)]


def replicates(sample, statistic, b, rng):
    return sorted(statistic(resample(sample, rng)) for _ in range(b))


def percentile(sorted_values, q):
    """가장 단순한 정의: 정렬된 B 개 중 ceil(q*B) 번째. 논문의 G^-1(q) 에 해당한다."""
    b = len(sorted_values)
    index = max(0, min(b - 1, math.ceil(q * b) - 1))
    return sorted_values[index]


def jackknife_values(sample, statistic):
    return [
        statistic(sample[:i] + sample[i + 1:])
        for i in range(len(sample))
    ]


def acceleration(sample, statistic):
    """식 (3.11)-(3.12): d_i = theta(i) - theta(.),  a = sum d^3 / (6 * (sum d^2)^1.5)"""
    values = jackknife_values(sample, statistic)
    mean = sum(values) / len(values)
    diffs = [v - mean for v in values]
    numerator = sum(d ** 3 for d in diffs)
    denominator = sum(d * d for d in diffs) ** 1.5
    return numerator / (6 * denominator) if denominator else 0.0


def bias_corrector(reps, observed):
    """식 (2.9): z0 = Phi^-1( G(theta_hat) )"""
    below = sum(1 for r in reps if r < observed)
    fraction = below / len(reps)
    fraction = min(max(fraction, 1e-6), 1 - 1e-6)
    return NORMAL.inv_cdf(fraction)


def bca_endpoint(reps, z0, a, alpha):
    """식 (2.2): theta_bca(alpha) = G^-1( Phi( z0 + (z0 + z_alpha)/(1 - a(z0 + z_alpha)) ) )"""
    z_alpha = NORMAL.inv_cdf(alpha)
    adjusted = z0 + (z0 + z_alpha) / (1 - a * (z0 + z_alpha))
    return percentile(reps, NORMAL.cdf(adjusted))


def section_standard_error(sample):
    print("[1] 표준오차 추정 - 복원추출 B회의 복제값이 흩어진 정도")
    print(f"    표본: Exp(1) 에서 뽑은 n = {SAMPLE_SIZE}개")
    print()
    theta_mean = statistics.fmean(sample)
    theta_var = variance(sample)
    print(f"    표본평균  = {theta_mean:.4f}   (모평균 1)")
    print(f"    불편분산  = {theta_var:.4f}   (모분산 1)")
    print()
    print("    추정량   | 부트스트랩 SE | 잭나이프 SE |  이론값")
    print("    ---------+---------------+-------------+---------")
    rng = random.Random(SEED + 1)
    for label, stat, theory in (
        ("표본평균", statistics.fmean, math.sqrt(theta_var / SAMPLE_SIZE)),
        ("불편분산", variance, None),
    ):
        reps = replicates(sample, stat, B_DEFAULT, rng)
        boot_se = statistics.stdev(reps)
        jack = jackknife_values(sample, stat)
        jack_mean = sum(jack) / len(jack)
        jack_se = math.sqrt(
            (SAMPLE_SIZE - 1) / SAMPLE_SIZE * sum((v - jack_mean) ** 2 for v in jack)
        )
        theory_text = f"{theory:.4f}" if theory is not None else "   -  "
        print(f"    {label} | {boot_se:13.4f} | {jack_se:11.4f} | {theory_text}")
    print()
    print("    표본평균은 표준오차를 손으로 적을 수 있어 세 값이 맞는지 확인된다.")
    print()


def section_b_ladder(sample):
    print("[2] B 를 키우면 무엇이 먼저 안정되는가")
    print(f"    추정량은 불편분산. 같은 B 로 {REPEATS}번 돌려 흔들림(표준편차)을 잰다.")
    print()
    print("         B | SE 추정의 흔들림 | 2.5% 끝점의 흔들림 | 97.5% 끝점의 흔들림")
    print("    -------+------------------+--------------------+--------------------")
    for b in B_LADDER:
        ses, lows, highs = [], [], []
        for trial in range(REPEATS):
            rng = random.Random(SEED + 100 * trial + b)
            reps = replicates(sample, variance, b, rng)
            ses.append(statistics.stdev(reps))
            lows.append(percentile(reps, 0.025))
            highs.append(percentile(reps, 0.975))
        print(
            f"    {b:6,} | {statistics.stdev(ses):16.5f} |"
            f" {statistics.stdev(lows):18.5f} | {statistics.stdev(highs):19.5f}"
        )
    print()
    print("    표준오차는 B=200 에서 이미 자리를 잡지만 구간 끝점은 그렇지 않다.")
    print()


def section_intervals(sample):
    print("[3] 신뢰구간 세 가지 - 같은 복제값에서 끝점만 다르게 읽는다")
    print(f"    추정량은 불편분산, B = {B_DEFAULT:,}, 신뢰수준 95%")
    print()
    rng = random.Random(SEED + 2)
    observed = variance(sample)
    reps = replicates(sample, variance, B_DEFAULT, rng)
    boot_se = statistics.stdev(reps)
    z0 = bias_corrector(reps, observed)
    a = acceleration(sample, variance)
    print(f"    관측값 theta_hat = {observed:.4f}")
    print(f"    복제값 중 theta_hat 보다 작은 비율 = "
          f"{sum(1 for r in reps if r < observed) / len(reps):.3f}  ->  z0 = {z0:+.4f}")
    print(f"    잭나이프 차이로 구한 가속도            a  = {a:+.4f}")
    print()
    z = NORMAL.inv_cdf(0.975)
    pct_low, pct_high = percentile(reps, 0.025), percentile(reps, 0.975)
    bca_low, bca_high = bca_endpoint(reps, z0, a, 0.025), bca_endpoint(reps, z0, a, 0.975)
    print("    방법       |   하한   |   상한   |   폭   | 중심 - 관측값")
    print("    -----------+----------+----------+--------+---------------")
    for label, low, high in (
        ("표준    ", observed - z * boot_se, observed + z * boot_se),
        ("백분위수", pct_low, pct_high),
        ("BCa     ", bca_low, bca_high),
    ):
        shift = (low + high) / 2 - observed
        print(f"    {label}   | {low:8.4f} | {high:8.4f} | {high - low:6.4f} | {shift:+13.4f}")
    print()
    print(f"    z0 = {z0:+.4f} 이 양수라는 것은 복제값의 절반 이상이 관측값보다 작다는 뜻이고,")
    print("    BCa 는 그만큼 끝점을 위로 되돌린다.")
    print(f"      하한 {pct_low:.4f} -> {bca_low:.4f}  ({bca_low - pct_low:+.4f})")
    print(f"      상한 {pct_high:.4f} -> {bca_high:.4f}  ({bca_high - pct_high:+.4f})")
    print("    표준 구간만 관측값을 한가운데 두고, 나머지 둘은 복제값의 치우침을 반영한다.")
    print()


def section_median(sample):
    print("[4] 중앙값 - 잭나이프가 멈추는 자리")
    print()
    jack = jackknife_values(sample, statistics.median)
    rng = random.Random(SEED + 3)
    reps = replicates(sample, statistics.median, B_DEFAULT, rng)
    jack_mean = sum(jack) / len(jack)
    jack_se = math.sqrt(
        (SAMPLE_SIZE - 1) / SAMPLE_SIZE * sum((v - jack_mean) ** 2 for v in jack)
    )
    # Exp(1) 중앙값의 점근 표준오차 = 1 / (2 f(m) sqrt(n)), f(ln2) = 0.5
    theory = 1 / (2 * 0.5 * math.sqrt(SAMPLE_SIZE))
    print(f"    잭나이프 복제값의 서로 다른 값 개수 : {len(set(jack))}개 (n = {SAMPLE_SIZE})")
    print(f"    부트스트랩 복제값의 서로 다른 값 개수 : {len(set(reps))}개 (B = {B_DEFAULT:,})")
    print()
    print(f"    잭나이프 SE     = {jack_se:.4f}")
    print(f"    부트스트랩 SE   = {statistics.stdev(reps):.4f}")
    print(f"    점근 이론값     = {theory:.4f}   (1 / (2 f(m) sqrt(n)), Exp(1) 에서 f(ln2)=0.5)")
    print()
    print("    하나를 빼도 가운데 값이 두 자리 사이에서만 움직이므로 잭나이프는 정보를")
    print("    거의 얻지 못한다. 복원추출은 같은 관측치를 여러 번 뽑아 순위를 흔들어")
    print("    중앙값을 실제로 이동시킨다.")
    print()


def main():
    rng = random.Random(SEED)
    sample = draw_sample(rng)
    section_standard_error(sample)
    section_b_ladder(sample)
    section_intervals(sample)
    section_median(sample)


if __name__ == "__main__":
    main()
