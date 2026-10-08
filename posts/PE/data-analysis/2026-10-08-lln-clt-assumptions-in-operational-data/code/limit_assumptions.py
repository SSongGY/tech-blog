"""대수의 법칙·중심극한정리의 전제가 깨질 때 표본평균의 오차 계산이 어떻게 틀어지는지 확인한다.

외부 의존성 없이 표준 라이브러리만 쓴다. 시드를 고정해 같은 출력이 나오게 한다.
"""
import math
import random
import statistics
import sys

SEED = 20261008
Z_975 = 1.959964
T_975_DF9 = 2.262157  # 자유도 9 의 t 분포 97.5% 분위수 (배치 10개)


def naive_interval_covers(sample, true_mean):
    # 운영 대시보드가 흔히 쓰는 '평균 ± 1.96·s/√n' 그대로다
    n = len(sample)
    mean = statistics.fmean(sample)
    half = Z_975 * statistics.stdev(sample) / math.sqrt(n)
    return abs(mean - true_mean) <= half


def batch_interval_covers(sample, true_mean, batches=10):
    # 인접한 관측을 한 배치로 묶어 배치 평균끼리는 거의 독립이 되게 한다
    size = len(sample) // batches
    means = [statistics.fmean(sample[i * size:(i + 1) * size]) for i in range(batches)]
    half = T_975_DF9 * statistics.stdev(means) / math.sqrt(batches)
    return abs(statistics.fmean(means) - true_mean) <= half


def check_baseline(rng):
    print("[1] 기준선 — 독립·동일분포 지수분포(1), n = 100, 반복 4000회")
    hits = sum(naive_interval_covers([rng.expovariate(1.0) for _ in range(100)], 1.0) for _ in range(4000))
    print(f"  '평균 ± 1.96·s/√n' 이 참 평균을 덮은 비율: {hits / 4000:.4f}  (목표 0.95)")


def ar1_path(rng, n, rho):
    # 정상 AR(1): 주변분포가 N(0,1) 이 되도록 잡음을 sqrt(1-rho^2) 로 줄인다
    x = rng.gauss(0.0, 1.0)
    scale = math.sqrt(1.0 - rho * rho)
    path = []
    for _ in range(n):
        path.append(x)
        x = rho * x + scale * rng.gauss(0.0, 1.0)
    return path


def ar1_variance_factor(n, rho):
    # n·Var(평균)/σ² = 1 + 2 Σ_{k=1}^{n-1} (1 - k/n) ρ^k  (유한 n 정확식)
    return 1.0 + 2.0 * sum((1.0 - k / n) * rho ** k for k in range(1, n))


def check_dependence(rng):
    n, repeats = 1000, 2000
    print(f"\n[2] 독립이 깨질 때 — 정상 AR(1), 주변분포 N(0,1), n = {n}, 반복 {repeats}회")
    print(f"{'rho':>5} {'(1+r)/(1-r)':>12} {'정확식':>8} {'모의 n·Var':>11} {'유효 n':>8} {'단순 구간':>10} {'배치 평균':>10}")
    for rho in (0.0, 0.5, 0.9):
        means, naive, batch = [], 0, 0
        for _ in range(repeats):
            path = ar1_path(rng, n, rho)
            means.append(statistics.fmean(path))
            naive += naive_interval_covers(path, 0.0)
            batch += batch_interval_covers(path, 0.0)
        exact = ar1_variance_factor(n, rho)
        print(
            f"{rho:>5.1f} {(1 + rho) / (1 - rho):>12.4f} {exact:>8.4f} {n * statistics.pvariance(means):>11.4f}"
            f" {n / exact:>8.1f} {naive / repeats:>10.4f} {batch / repeats:>10.4f}"
        )


def check_running_mean_pareto(rng):
    print("\n[3] 분산이 무한해도 평균은 있다 — 파레토(alpha=1.5, 하한 1), 참 평균 3")
    total = 0.0
    checkpoints = {100, 1000, 10000, 100000, 1000000}
    print(f"{'n':>8} {'누적 평균':>10}")
    for n in range(1, 1000001):
        total += rng.paretovariate(1.5)
        if n in checkpoints:
            print(f"{n:>8} {total / n:>10.4f}")


def check_infinite_variance(rng):
    repeats = 1000
    print(f"\n[4] 분산이 무한할 때 — 파레토 표본평균의 신뢰구간 (반복 {repeats}회)")
    print(f"{'alpha':>6} {'참 평균':>7} {'분산':>6} {'n':>6} {'단순 구간':>10} {'평균<참값':>10}")
    for alpha in (3.0, 1.5):
        true_mean = alpha / (alpha - 1.0)
        variance = "무한" if alpha <= 2 else f"{alpha / ((alpha - 1) ** 2 * (alpha - 2)):.2f}"
        for n in (100, 1000, 10000):
            covered, below = 0, 0
            for _ in range(repeats):
                sample = [rng.paretovariate(alpha) for _ in range(n)]
                covered += naive_interval_covers(sample, true_mean)
                below += statistics.fmean(sample) < true_mean
            print(f"{alpha:>6.1f} {true_mean:>7.2f} {variance:>6} {n:>6} {covered / repeats:>10.4f} {below / repeats:>10.4f}")


def normal_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def erlang_cdf(x, n):
    # 지수분포(1) n 개의 합은 얼랑(n,1) 이다: P(S ≤ x) = 1 - Σ_{k<n} e^{-x} x^k / k!
    if x <= 0:
        return 0.0
    log_x = math.log(x)
    tail = sum(math.exp(-x + k * log_x - math.lgamma(k + 1)) for k in range(n))
    return max(0.0, 1.0 - tail)


def check_berry_esseen():
    # 지수분포(1): σ = 1, E|X-1|^3 = 12/e - 2  →  β3/σ^3 = 12/e - 2
    beta3 = 12.0 / math.e - 2.0
    print(f"\n[5] 수렴 속도 — 지수분포(1) 표준화 평균과 N(0,1) 의 최대 거리 (정확 계산, β3 = {beta3:.4f})")
    print(f"{'n':>6} {'실제 sup|F_n - Φ|':>18} {'베리-에센 상한 0.4748·β3/√n':>28}")
    grid = [i / 500.0 for i in range(-3000, 3001)]  # z = -6.000 … 6.000, 간격 0.002
    for n in (1, 5, 30, 100, 1000):
        root = math.sqrt(n)
        distance = max(abs(erlang_cdf(n + z * root, n) - normal_cdf(z)) for z in grid)
        print(f"{n:>6} {distance:>18.4f} {0.4748 * beta3 / root:>28.4f}")


def main():
    print(f"Python {sys.version.split()[0]}, seed = {SEED}\n")
    rng = random.Random(SEED)
    check_baseline(rng)
    check_dependence(rng)
    check_running_mean_pareto(rng)
    check_infinite_variance(rng)
    check_berry_esseen()


if __name__ == "__main__":
    main()
