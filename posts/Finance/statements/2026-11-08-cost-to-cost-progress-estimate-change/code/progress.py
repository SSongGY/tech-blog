"""원가기준 진행률로 수익을 인식하는 두 가상 건설사를 비교한다.

가나건설과 다라건설은 같은 공사(계약금액 1,000억원, 3년)를 맡았다.
처음 추정 총원가는 둘 다 800억원이다. 다라건설만 2년차 말에
총원가 추정이 950억원으로 오른다. 금액 단위는 억원.
"""

import platform

CONTRACT_PRICE = 1000.0

# 연차별 발생원가와 그 해 말 추정 총원가
GANA = {
    "name": "가나건설",
    "costs": [240.0, 360.0, 200.0],
    "estimates": [800.0, 800.0, 800.0],
}
DARA = {
    "name": "다라건설",
    "costs": [240.0, 410.0, 300.0],
    "estimates": [800.0, 950.0, 950.0],
}

# 청구 일정은 두 회사가 같다. 청구하면 대가를 받을 무조건적 권리가 생긴다고 본다
BILLINGS = [350.0, 300.0, 350.0]


def run_contract(company):
    """연차별 진행률·수익·이익과 계약자산/계약부채를 계산한다."""
    rows = []
    cum_cost = 0.0
    cum_revenue_prev = 0.0
    cum_billing = 0.0
    for year, (cost, estimate, billing) in enumerate(
        zip(company["costs"], company["estimates"], BILLINGS), start=1
    ):
        cum_cost += cost
        cum_billing += billing
        progress = cum_cost / estimate
        # 진행률이 누적 개념이라 누적 수익을 새로 계산하고 이미 인식한 몫을 뺀다.
        # 과거 연도 숫자는 고치지 않으므로 추정 변경 효과가 변경한 해에 몰린다
        cum_revenue = CONTRACT_PRICE * progress
        revenue = cum_revenue - cum_revenue_prev
        profit = revenue - cost
        position = cum_revenue - cum_billing
        rows.append(
            {
                "year": year,
                "cost": cost,
                "cum_cost": cum_cost,
                "estimate": estimate,
                "progress": progress,
                "revenue": revenue,
                "profit": profit,
                "cum_revenue": cum_revenue,
                "cum_billing": cum_billing,
                "position": position,
            }
        )
        cum_revenue_prev = cum_revenue
    return rows


def print_contract(company, rows):
    print(f"  {company['name']}")
    print(
        f"  {'연차':>4} {'발생원가':>8} {'누적원가':>8} {'추정총원가':>9} "
        f"{'진행률':>8} {'수익':>8} {'이익':>8}"
    )
    for r in rows:
        print(
            f"  {r['year']:>4} {r['cost']:>10.1f} {r['cum_cost']:>10.1f} "
            f"{r['estimate']:>12.1f} {r['progress']:>9.2%} "
            f"{r['revenue']:>9.1f} {r['profit']:>9.1f}"
        )
    total_revenue = sum(r["revenue"] for r in rows)
    total_profit = sum(r["profit"] for r in rows)
    print(f"  합계 수익 {total_revenue:.1f}, 합계 이익 {total_profit:.1f}")
    print()


def print_position(company, rows):
    print(f"  {company['name']}")
    print(f"  {'연차':>4} {'누적수익':>8} {'누적청구':>8} {'차이':>8}  표시")
    for r in rows:
        if r["position"] > 0.05:
            label = "계약자산(미청구)"
        elif r["position"] < -0.05:
            label = "계약부채(초과청구)"
        else:
            label = "없음"
        print(
            f"  {r['year']:>4} {r['cum_revenue']:>10.1f} {r['cum_billing']:>10.1f} "
            f"{r['position']:>9.1f}  {label}"
        )
    print()


def waste_case():
    """B19(1): 비효율로 낭비된 원가를 진행률에서 빼는지에 따라 1년차 수익이 갈린다."""
    normal_cost = 240.0
    waste = 40.0
    total_estimate = 800.0
    incurred = normal_cost + waste

    naive_progress = incurred / (total_estimate + waste)
    naive_revenue = CONTRACT_PRICE * naive_progress
    adjusted_progress = normal_cost / total_estimate
    adjusted_revenue = CONTRACT_PRICE * adjusted_progress

    print("[3] 1년차에 계약가격에 반영되지 않은 낭비 원가 40이 생긴 경우 — 문단 B19(1)")
    print(f"  발생원가 {incurred:.1f} = 정상 원가 {normal_cost:.1f} + 낭비 {waste:.1f}")
    print(f"  {'방식':<28} {'진행률':>8} {'수익':>8} {'비용':>8} {'이익':>8}")
    print(
        f"  {'낭비를 진행률에 포함':<26} {naive_progress:>9.2%} "
        f"{naive_revenue:>9.1f} {incurred:>9.1f} {naive_revenue - incurred:>9.1f}"
    )
    print(
        f"  {'낭비를 진행률에서 제외':<25} {adjusted_progress:>9.2%} "
        f"{adjusted_revenue:>9.1f} {incurred:>9.1f} {adjusted_revenue - incurred:>9.1f}"
    )
    print(
        f"  낭비를 포함하면 수익이 {naive_revenue - adjusted_revenue:.1f} 더 잡힌다"
        " — 낭비한 만큼 공사가 진척된 것처럼 보인다"
    )


def main():
    print(f"Python {platform.python_version()}")
    print(f"계약금액 {CONTRACT_PRICE:.1f}억원, 청구 일정 {BILLINGS}")
    print()

    gana_rows = run_contract(GANA)
    dara_rows = run_contract(DARA)

    print("[1] 연차별 진행률과 수익 — 진행률 = 누적 발생원가 / 추정 총원가 (문단 39·B18)")
    print_contract(GANA, gana_rows)
    print_contract(DARA, dara_rows)

    y1, y2 = dara_rows[0], dara_rows[1]
    old_progress = y2["cum_cost"] / 800.0
    print("  다라건설 2년차 분해 — 추정을 바꾸지 않았다면")
    print(
        f"    진행률 {old_progress:.2%}, 누적 수익 {CONTRACT_PRICE * old_progress:.1f}, "
        f"2년차 수익 {CONTRACT_PRICE * old_progress - y1['cum_revenue']:.1f}"
    )
    print(
        f"    실제: 진행률 {y2['progress']:.2%}, 누적 수익 {y2['cum_revenue']:.1f}, "
        f"2년차 수익 {y2['revenue']:.1f}"
    )
    print(
        f"    1년차에 인식한 이익 {y1['profit']:.1f} 중 새 추정으로는 "
        f"{y1['cum_cost'] / 950.0 * CONTRACT_PRICE - y1['cum_cost']:.1f} 만 맞다 "
        "— 1년차는 고치지 않고 차이를 2년차에 반영한다 (문단 43, 제1008호 전진적용)"
    )
    print()

    print("[2] 재무상태표 표시 — 누적 수익과 누적 청구액의 차이 (문단 105~107)")
    print_position(GANA, gana_rows)
    print_position(DARA, dara_rows)

    waste_case()


if __name__ == "__main__":
    main()
