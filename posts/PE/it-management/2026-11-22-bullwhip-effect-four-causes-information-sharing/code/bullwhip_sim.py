"""채찍 효과 검산 — Lee·Padmanabhan·Whang(1997) 의 정리 1·3 을 시뮬레이션으로 확인한다.

1. 수요 신호 처리(정리 1, 식 3.3·3.5): AR(1) 수요에 대한 최적 주문의 분산
2. 주문 일괄 처리(정리 3, 식 3.11~3.13): 무작위·동조·균형 주문의 분산
3. 논문 밖 확장: 같은 주문 규칙을 4단계에 이어 붙였을 때 주문 데이터만 보는 경우와
   판매(POS) 데이터를 공유받는 경우의 단계별 분산
"""

import random
import statistics

SEED = 20261122
PERIODS = 200_000


def order_gain(rho, lead_time):
    """식 (3.3) 의 수요 변화분 계수 ρ(1-ρ^(v+1))/(1-ρ)."""
    return rho * (1 - rho ** (lead_time + 1)) / (1 - rho)


def theorem1_variance(rho, lead_time, sigma):
    """식 (3.5): Var(z) = Var(D) + 2ρ(1-ρ^(v+1))(1-ρ^(v+2))σ² / ((1+ρ)(1-ρ)²)."""
    demand_var = sigma**2 / (1 - rho**2)
    extra = (
        2 * rho * (1 - rho ** (lead_time + 1)) * (1 - rho ** (lead_time + 2)) * sigma**2
    ) / ((1 + rho) * (1 - rho) ** 2)
    return demand_var, demand_var + extra


def ar1_demand(rng, rho, sigma, base, periods):
    # 정상 상태 평균에서 출발해 초기값이 분산을 흔들지 않게 한다
    level = base / (1 - rho)
    series = []
    for _ in range(periods):
        level = base + rho * level + rng.gauss(0, sigma)
        series.append(level)
    return series


def signal_orders(observed, gain):
    """z_t = D_t + k(D_t - D_{t-1}) — 받은 신호를 그대로 주문에 실어 보낸다."""
    return [observed[t] + gain * (observed[t] - observed[t - 1])
            for t in range(1, len(observed))]


def check_theorem1(rng):
    print("[1] 수요 신호 처리 — 정리 1 식(3.5) vs 시뮬레이션 (σ=10, d=100)")
    print(f"{'ρ':>4} {'v':>2} {'Var(D) 식':>10} {'Var(z) 식':>10} "
          f"{'Var(D) 실측':>11} {'Var(z) 실측':>11} {'배율 식':>8} {'배율 실측':>9}")
    sigma = 10.0
    for rho in (0.5, 0.8):
        demand = ar1_demand(rng, rho, sigma, 100.0, PERIODS)
        for lead_time in (0, 1, 2, 4):
            orders = signal_orders(demand, order_gain(rho, lead_time))
            var_d, var_z = theorem1_variance(rho, lead_time, sigma)
            sim_d = statistics.pvariance(demand)
            sim_z = statistics.pvariance(orders)
            print(f"{rho:>4} {lead_time:>2} {var_d:>10.1f} {var_z:>10.1f} "
                  f"{sim_d:>11.1f} {sim_z:>11.1f} {var_z / var_d:>8.2f} "
                  f"{sim_z / sim_d:>9.2f}")
    # 논문 본문은 v=0 에서 Var(z)=Var(D)+2ρ 라고 적었다. σ² 를 곱해야 식(3.5)와 맞는다
    _, var_z0 = theorem1_variance(0.5, 0, sigma)
    print(f"  v=0, ρ=0.5: Var(z)-Var(D) = {var_z0 - sigma**2 / 0.75:.1f}"
          f"  (2ρσ² = {2 * 0.5 * sigma**2:.1f})")


def batching_variance(case, retailers, cycle, mean, sigma):
    """식 (3.11)·(3.12)·(3.13)."""
    base = retailers * sigma**2
    if case == "random":
        return base + mean**2 * retailers * (cycle - 1)
    if case == "correlated":
        return base + mean**2 * retailers**2 * (cycle - 1)
    k = retailers % cycle
    return base + mean**2 * k * (cycle - k)


def ordering_count(rng, case, retailers, cycle):
    """임의로 고른 한 기간에 주문을 내는 소매점 수 n."""
    if case == "random":
        return sum(1 for _ in range(retailers) if rng.randrange(cycle) == 0)
    if case == "correlated":
        return retailers if rng.randrange(cycle) == 0 else 0
    group_size, k = divmod(retailers, cycle)
    # 균형 주문: k 개 그룹은 M+1 곳, 나머지 R-k 개 그룹은 M 곳
    return group_size + 1 if rng.randrange(cycle) < k else group_size


def check_theorem3(rng):
    retailers, cycle, mean, sigma = 23, 5, 10.0, 3.0
    trials = 100_000
    print()
    print(f"[2] 주문 일괄 처리 — 정리 3 (N={retailers}, R={cycle}, m={mean:g}, σ={sigma:g})")
    print(f"  소매점 판매 합계의 기간당 분산 Nσ² = {retailers * sigma**2:.0f}")
    print(f"{'방식':<11} {'E(Z) 실측':>10} {'Var(Z) 식':>10} {'Var(Z) 실측':>11} {'Nσ² 대비':>9}")
    for case in ("correlated", "random", "balanced"):
        totals = []
        for _ in range(trials):
            n = ordering_count(rng, case, retailers, cycle)
            # 주문하는 소매점은 지난 R 기간 판매량을 한 번에 주문한다
            totals.append(sum(rng.gauss(mean, sigma) for _ in range(n * cycle)))
        expected = batching_variance(case, retailers, cycle, mean, sigma)
        sim_var = statistics.pvariance(totals)
        print(f"{case:<11} {statistics.fmean(totals):>10.1f} {expected:>10.0f} "
              f"{sim_var:>11.0f} {sim_var / (retailers * sigma**2):>9.1f}")


def check_multistage(rng):
    rho, sigma, lead_time, stages = 0.5, 10.0, 1, 4
    gain = order_gain(rho, lead_time)
    demand = ar1_demand(rng, rho, sigma, 100.0, PERIODS)
    names = ["소매", "도매", "유통", "제조"]
    print()
    print(f"[3] 확장 — 4단계 연쇄 (ρ={rho}, v={lead_time}, k={gain:.3f})")
    print(f"  소비자 수요 분산 = {statistics.pvariance(demand):.1f}")
    print(f"{'단계':<4} {'주문만 보고 예측':>16} {'POS 공유 후 예측':>16}")
    seen_orders = demand
    pos_orders = signal_orders(demand, gain)
    for name in names[:stages]:
        seen_orders = signal_orders(seen_orders, gain)
        ratio_chain = statistics.pvariance(seen_orders) / statistics.pvariance(demand)
        ratio_pos = statistics.pvariance(pos_orders) / statistics.pvariance(demand)
        print(f"{name:<4} {ratio_chain:>16.2f} {ratio_pos:>16.2f}")


def main():
    rng = random.Random(SEED)
    check_theorem1(rng)
    check_theorem3(rng)
    check_multistage(rng)


if __name__ == "__main__":
    main()
