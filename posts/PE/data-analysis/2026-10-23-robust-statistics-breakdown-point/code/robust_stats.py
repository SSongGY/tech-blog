"""강건 통계량의 붕괴점과 효율을 계산으로 확인한다.

1. 유한표본 붕괴점 — 표본 n 개 중 k 개를 임의로 큰 값으로 바꿔 가며
   추정값이 한없이 커지는 최소 k/n 을 찾는다 (Donoho·Huber 1983 의 정의).
2. 이상치 검출 — 같은 표본에 이상치를 1~4 개 넣고 Z 점수와 수정 Z 점수를 비교한다.
3. 대가 — 정규분포 표본에서 평균·중앙값·절사평균의 분산을 비교한다(효율).

표준 라이브러리만 쓴다. 난수 시드를 고정했으므로 다시 돌려도 같은 값이 나온다.
"""

import math
import random
import statistics
import sys

# 가상의 API 응답시간(ms) 20건. 이상치가 없는 깨끗한 표본이다.
CLEAN = [
    188, 192, 195, 201, 186, 199, 204, 190, 197, 193,
    205, 189, 196, 202, 194, 191, 198, 200, 187, 203,
]


def rule(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def trimmed_mean(data, alpha):
    """양쪽에서 floor(alpha·n) 개씩 버리고 평균을 낸다."""
    xs = sorted(data)
    g = math.floor(alpha * len(xs))
    return statistics.fmean(xs[g:len(xs) - g])


def mad(data):
    """중앙값 절대편차. 정규분포 표준편차와 맞추는 상수는 곱하지 않은 원값이다."""
    m = statistics.median(data)
    return statistics.median([abs(x - m) for x in data])


def iqr(data):
    q1, _, q3 = statistics.quantiles(data, n=4, method="inclusive")
    return q3 - q1


ESTIMATORS = [
    ("평균", "위치", statistics.fmean),
    ("10% 절사평균", "위치", lambda d: trimmed_mean(d, 0.10)),
    ("25% 절사평균", "위치", lambda d: trimmed_mean(d, 0.25)),
    ("중앙값", "위치", statistics.median),
    ("표준편차", "척도", statistics.stdev),
    ("사분위범위", "척도", iqr),
    ("MAD", "척도", mad),
]


def contaminate(data, k, magnitude):
    """앞에서 k 개를 서로 다른 큰 값으로 바꾼다. 같은 값으로 바꾸면 MAD 가 동점에 걸린다."""
    out = list(data)
    for i in range(k):
        out[i] = magnitude * (1 + i)
    return out


def breaks_down(fn, data, k):
    """오염값을 10^6 에서 10^12 로 키웠을 때 추정값도 따라 커지면 붕괴로 본다."""
    small = fn(contaminate(data, k, 1e6))
    large = fn(contaminate(data, k, 1e12))
    return abs(large) > 1e3 * max(abs(small), 1.0)


def section_breakdown():
    rule("1. 유한표본 붕괴점 (n = 20, 오염값을 10^6 -> 10^12 로 키워 본다)")
    n = len(CLEAN)
    print(f"  깨끗한 표본  평균={statistics.fmean(CLEAN):.2f}  중앙값={statistics.median(CLEAN):.1f}"
          f"  표준편차={statistics.stdev(CLEAN):.2f}  MAD={mad(CLEAN):.1f}")
    print()
    print(f"  {'추정량':<12}{'종류':<6}{'붕괴하는 최소 k':>14}{'붕괴점 k/n':>12}")
    for name, kind, fn in ESTIMATORS:
        k_star = next(k for k in range(1, n + 1) if breaks_down(fn, CLEAN, k))
        print(f"  {name:<12}{kind:<6}{k_star:>14}{k_star / n:>12.2f}")

    print()
    print("  k 를 늘려 가며 본 중앙값과 평균 (오염값 10^6 기준)")
    print(f"  {'k':>3}{'평균':>16}{'중앙값':>14}{'MAD':>12}")
    for k in (0, 1, 5, 9, 10):
        d = contaminate(CLEAN, k, 1e6)
        print(f"  {k:>3}{statistics.fmean(d):>16.1f}{statistics.median(d):>14.1f}{mad(d):>12.1f}")


def scores(data):
    mean, sd = statistics.fmean(data), statistics.stdev(data)
    med, m = statistics.median(data), mad(data)
    z = [(x - mean) / sd for x in data]
    mz = [0.6745 * (x - med) / m for x in data]
    return z, mz


def section_detection():
    rule("2. 이상치 검출 — Z 점수(평균·표준편차)와 수정 Z 점수(중앙값·MAD)")
    n = len(CLEAN)
    print(f"  Z 점수 최댓값의 상한 (n-1)/sqrt(n) = {(n - 1) / math.sqrt(n):.3f}")
    print(f"  {'이상치 수':>8}{'Z>3 검출':>10}{'Z 최댓값':>10}{'수정Z>3.5 검출':>16}")
    for k in range(1, 5):
        data = list(CLEAN)
        for i in range(k):
            data[i] = 4200  # 재시도 타임아웃이 실측값 자리에 들어간 경우
        z, mz = scores(data)
        hit_z = sum(1 for v in z if abs(v) > 3)
        hit_mz = sum(1 for v in mz if abs(v) > 3.5)
        print(f"  {k:>8}{hit_z:>10}{max(z):>10.3f}{hit_mz:>16}")


def section_efficiency():
    rule("3. 대가 — 정규분포 N(200, 10^2), n = 20, 20000 회 반복")
    rng = random.Random(20261023)
    reps, n = 20000, 20
    est = {"평균": [], "10% 절사평균": [], "25% 절사평균": [], "중앙값": []}
    sd_hat, mad_hat = [], []
    for _ in range(reps):
        d = [rng.gauss(200, 10) for _ in range(n)]
        est["평균"].append(statistics.fmean(d))
        est["10% 절사평균"].append(trimmed_mean(d, 0.10))
        est["25% 절사평균"].append(trimmed_mean(d, 0.25))
        est["중앙값"].append(statistics.median(d))
        sd_hat.append(statistics.stdev(d))
        mad_hat.append(mad(d))
    base = statistics.variance(est["평균"])
    print(f"  {'추정량':<12}{'추정값 분산':>12}{'평균 대비 효율':>14}")
    for name, values in est.items():
        v = statistics.variance(values)
        print(f"  {name:<12}{v:>12.3f}{base / v:>14.3f}")
    print(f"  (참고) 중앙값의 점근 효율 2/pi = {2 / math.pi:.3f}")

    c = 1 / statistics.NormalDist().inv_cdf(0.75)
    print()
    print(f"  Phi^-1(0.75) = {statistics.NormalDist().inv_cdf(0.75):.4f}  ->  보정 상수 1/Phi^-1(0.75) = {c:.4f}")
    print(f"  표준편차 평균 = {statistics.fmean(sd_hat):.3f},  보정한 MAD 평균 = {c * statistics.fmean(mad_hat):.3f}  (참값 10)")
    print(f"  표준편차의 분산 = {statistics.variance(sd_hat):.3f},  보정한 MAD 의 분산 = {statistics.variance([c * x for x in mad_hat]):.3f}")


def main():
    print(f"Python {sys.version.split()[0]}")
    section_breakdown()
    section_detection()
    section_efficiency()


if __name__ == "__main__":
    main()
