"""손실부담계약 충당부채를 가상 회사로 계산한다.

[1] 계약을 이행하는 데 드는 원가의 범위(제1037호 문단 68A, 2022년 시행)에
    따라 같은 계약이 손실부담계약이 되기도 하고 안 되기도 한다.
[2] 회피 불가능 원가는 이행원가와 위약금 중 적은 쪽이다(문단 68).
[3] 진행률로 수익을 인식하는 공사 계약의 총원가가 계약금액을 넘을 때,
    충당부채가 없으면 남은 손실이 다음 해로 넘어간다.
금액 단위는 억원.
"""

import platform

# [1]·[2] 가나조선의 고정가격 납품 계약
CONTRACT_PRICE = 500.0
INCREMENTAL_COST = 460.0   # 직접 재료원가·노무원가
ALLOCATED_COST = 70.0      # 이 계약에 쓰는 설비의 감가상각비 배분액


def fulfil_cost(include_allocation):
    if include_allocation:
        return INCREMENTAL_COST + ALLOCATED_COST
    return INCREMENTAL_COST


def scope_case():
    print("[1] 이행원가에 무엇을 넣는가 — 문단 68A (2022-01-01 이후 시작 회계연도부터)")
    print(f"  계약금액(받을 효익) {CONTRACT_PRICE:.1f}")
    print(f"  증분원가 {INCREMENTAL_COST:.1f} · 직접 관련 원가 배분액 {ALLOCATED_COST:.1f}")
    print(f"  {'이행원가 범위':<22} {'이행원가':>8} {'효익':>8} {'차이':>8}  판정")
    for label, include in (("증분원가만", False), ("증분원가 + 배분액", True)):
        cost = fulfil_cost(include)
        gap = cost - CONTRACT_PRICE
        verdict = "손실부담계약" if gap > 0 else "손실부담 아님"
        print(
            f"  {label:<20} {cost:>10.1f} {CONTRACT_PRICE:>9.1f} {gap:>9.1f}  {verdict}"
        )
    print("  같은 계약이 이행원가의 범위만으로 판정이 갈린다")
    print()


def penalty_case():
    print("[2] 회피 불가능 원가 — 이행할 때의 순원가와 위약금 중 적은 쪽 (문단 68)")
    cost = fulfil_cost(True)
    net_fulfil = cost - CONTRACT_PRICE
    print(f"  이행하면: 원가 {cost:.1f} − 효익 {CONTRACT_PRICE:.1f} = 순원가 {net_fulfil:.1f}")
    print(f"  {'위약금':>8} {'충당부채':>10}  근거")
    for penalty in (50.0, 20.0):
        provision = min(net_fulfil, penalty)
        reason = "이행이 더 싸다" if net_fulfil <= penalty else "해약이 더 싸다"
        print(f"  {penalty:>10.1f} {provision:>11.1f}  {reason}")
    print()


# [3] 다라건설의 공사 계약 — 2년차 말에 총원가 추정이 계약금액을 넘는다
PROJECT_PRICE = 1000.0
COSTS = [240.0, 410.0, 430.0]
ESTIMATES = [800.0, 1080.0, 1080.0]


def project_case(with_provision):
    rows = []
    cum_cost = 0.0
    cum_revenue_prev = 0.0
    provision = 0.0
    for year, (cost, estimate) in enumerate(zip(COSTS, ESTIMATES), start=1):
        cum_cost += cost
        cum_revenue = PROJECT_PRICE * cum_cost / estimate
        revenue = cum_revenue - cum_revenue_prev
        profit = revenue - cost
        change = 0.0
        if with_provision:
            # 남은 공사에서 인식할 수익보다 남은 원가가 크면 그 차이가 앞으로의 손실이다
            remaining_cost = estimate - cum_cost
            remaining_revenue = PROJECT_PRICE - cum_revenue
            needed = max(remaining_cost - remaining_revenue, 0.0)
            change = needed - provision
            provision = needed
            profit -= change
        rows.append((year, revenue, cost, change, profit, provision))
        cum_revenue_prev = cum_revenue
    return rows


def print_project(title, rows):
    print(f"  {title}")
    print(
        f"  {'연차':>4} {'수익':>8} {'원가':>8} {'충당부채 전입(사용)':>12} "
        f"{'이익':>8} {'기말 충당부채':>10}"
    )
    for year, revenue, cost, change, profit, provision in rows:
        print(
            f"  {year:>4} {revenue:>10.1f} {cost:>9.1f} {change:>16.1f} "
            f"{profit:>9.1f} {provision:>13.1f}"
        )
    total = sum(r[4] for r in rows)
    print(f"  합계 이익 {total:.1f}")
    print()


def main():
    print(f"Python {platform.python_version()}")
    print()
    scope_case()
    penalty_case()

    print("[3] 진행률로 수익을 인식하는 공사 — 2년차 말 추정 총원가 1,080 > 계약금액 1,000")
    print("    위약금은 커서 해약하지 않는다고 가정한다")
    print_project("(가) 진행률만 적용", project_case(False))
    print_project("(나) 남은 손실을 손실부담계약 충당부채로 인식 (제1037호 문단 5(7)·66)", project_case(True))


if __name__ == "__main__":
    main()
