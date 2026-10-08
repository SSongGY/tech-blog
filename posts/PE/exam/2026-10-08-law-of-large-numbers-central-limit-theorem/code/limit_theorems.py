"""대수의 법칙과 중심극한정리를 난수로 검산한다.

외부 의존성 없이 표준 라이브러리만 쓴다. 시드를 고정해 같은 출력이 나오게 한다.
"""
import math
import random
import statistics
import sys

SEED = 20261008
REPEATS = 20000


def die_mean(rng, n):
    return sum(rng.randint(1, 6) for _ in range(n)) / n


def skewness(values):
    mean = statistics.fmean(values)
    sd = statistics.pstdev(values)
    return statistics.fmean(((v - mean) / sd) ** 3 for v in values)


def check_law_of_large_numbers(rng):
    print("[1] 대수의 법칙 — 주사위 표본평균 (mu = 3.5, sigma^2 = 35/12)")
    total = 0
    checkpoints = {10, 100, 1000, 10000, 100000}
    print(f"{'n':>8} {'표본평균':>10} {'|평균-3.5|':>12}")
    for n in range(1, 100001):
        total += rng.randint(1, 6)
        if n in checkpoints:
            mean = total / n
            print(f"{n:>8} {mean:>10.4f} {abs(mean - 3.5):>12.4f}")


def check_chebyshev_bound(rng):
    # 약한 대수의 법칙의 증명은 체비쇼프 부등식 sigma^2/(n eps^2) 을 상한으로 쓴다
    print("\n[2] 체비쇼프 상한과 실제 이탈 비율 (eps = 0.3, 반복 2000회)")
    variance = 35 / 12
    eps = 0.3
    print(f"{'n':>6} {'상한 s^2/(n e^2)':>18} {'실제 P(|평균-mu|>=eps)':>24}")
    for n in (10, 50, 100, 500):
        hits = sum(abs(die_mean(rng, n) - 3.5) >= eps for _ in range(2000))
        bound = min(1.0, variance / (n * eps * eps))
        print(f"{n:>6} {bound:>18.4f} {hits / 2000:>24.4f}")


def check_central_limit_theorem(rng):
    # 모집단은 지수분포(1): 평균 1, 분산 1, 왜도 2 로 정규분포와 거리가 멀다
    print(f"\n[3] 중심극한정리 — 지수분포(1) 표본평균의 표준화 (반복 {REPEATS}회)")
    print(f"{'n':>5} {'평균의 평균':>11} {'n*분산':>9} {'왜도':>8} {'이론 2/sqrt(n)':>15} {'P(Z<-1.96)':>11} {'P(Z>1.96)':>10}")
    for n in (1, 5, 30, 100):
        means = [statistics.fmean(rng.expovariate(1.0) for _ in range(n)) for _ in range(REPEATS)]
        z_values = [(m - 1.0) * math.sqrt(n) for m in means]
        # 양쪽 꼬리를 따로 센다. 합만 보면 비대칭이 서로 상쇄돼 0.95 근처로 보일 수 있다
        lower = sum(z < -1.96 for z in z_values) / REPEATS
        upper = sum(z > 1.96 for z in z_values) / REPEATS
        print(
            f"{n:>5} {statistics.fmean(means):>11.4f} {n * statistics.pvariance(means):>9.4f}"
            f" {skewness(means):>8.4f} {2 / math.sqrt(n):>15.4f} {lower:>11.4f} {upper:>10.4f}"
        )
    print("  정규분포라면 양쪽 꼬리가 각각 0.0250")


def check_cauchy(rng):
    # 코시 분포는 기댓값이 없어 두 정리의 전제가 깨진다
    print("\n[4] 전제가 깨질 때 — 표준 코시 분포 표본평균")
    total = 0.0
    checkpoints = {100, 1000, 10000, 100000, 1000000}
    print(f"{'n':>8} {'표본평균':>12}")
    for n in range(1, 1000001):
        total += math.tan(math.pi * (rng.random() - 0.5))
        if n in checkpoints:
            print(f"{n:>8} {total / n:>12.4f}")


def main():
    print(f"Python {sys.version.split()[0]}, seed = {SEED}\n")
    rng = random.Random(SEED)
    check_law_of_large_numbers(rng)
    check_chebyshev_bound(rng)
    check_central_limit_theorem(rng)
    check_cauchy(rng)


if __name__ == "__main__":
    main()
