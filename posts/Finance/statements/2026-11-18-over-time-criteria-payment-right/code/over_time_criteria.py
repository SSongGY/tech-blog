"""기간에 걸쳐 이행하는 수행의무의 세 기준 — 문단 35⑶의 두 요건을 계산으로 확인한다.

가상 회사 마바기계가 고객 맞춤 설비 1대를 2년에 걸쳐 만든다.
같은 공사 일정에 계약 조건만 바꾼 네 계약을 두고,
분기마다 '지금 계약이 해지되면 받을 수 있는 금액'이 문단 37·B9 를 충족하는지 본다.
금액 단위: 백만원.
"""

CONTRACT_PRICE = 1_000
TOTAL_COST = 800
ADVANCE = 200  # 계약 개시 때 받는 선급금, 나머지 800 은 인도 때 받는다

# 분기 말 누적원가 (8 분기, 4 분기가 1년차 말)
CUMULATIVE_COST = [80, 200, 340, 480, 600, 700, 770, 800]

EXPECTED_MARGIN = (CONTRACT_PRICE - TOTAL_COST) / TOTAL_COST  # 원가 대비 25%


def comp_cost_plus_margin(cost):
    """원가 + 계약상 예상 이윤 중 수행 정도에 비례하는 부분 (B9⑴)."""
    return cost * (1 + EXPECTED_MARGIN)


def comp_cost_only(cost):
    """발생원가만 돌려받는다 — 이윤이 없다."""
    return cost


def comp_keep_advance(cost):
    """받은 선급금만 돌려주지 않아도 된다 — 그 이상은 청구할 수 없다."""
    return ADVANCE


CONTRACTS = [
    # (이름, 해지 보상, 대체 용도 있음?)
    ("A 맞춤 사양 + 원가·이윤 보상", comp_cost_plus_margin, False),
    ("B 맞춤 사양 + 원가만 보상", comp_cost_only, False),
    ("C 맞춤 사양 + 선급금 보유", comp_keep_advance, False),
    ("D 표준 사양 + 원가·이윤 보상", comp_cost_plus_margin, True),
]


def required_amount(cost):
    """B9 — 원가 회수에 적정 이윤을 더한 금액. 여기서는 B9⑴ 의 비례 이윤으로 잡는다."""
    return cost * (1 + EXPECTED_MARGIN)


def payment_right_each_quarter(compensation):
    """분기마다 보상액이 요구 금액 이상인지. 문단 37 은 '계약기간에는 언제든지'를 요구한다."""
    rows = []
    for quarter, cost in enumerate(CUMULATIVE_COST, start=1):
        comp = compensation(cost)
        need = required_amount(cost)
        rows.append((quarter, cost, comp, need, comp >= need - 1e-9))
    return rows


def yearly_revenue(over_time):
    """(수익, 매출원가) 를 연차별로 돌려준다."""
    year1_cost = CUMULATIVE_COST[3]
    if over_time:
        year1_rev = CONTRACT_PRICE * year1_cost / TOTAL_COST
        year1_expense = year1_cost
    else:
        # 인도는 2년차 말이다. 1년차 원가는 재공품으로 쌓였다가 인도 때 한꺼번에 비용이 된다
        year1_rev = 0.0
        year1_expense = 0
    year2_rev = CONTRACT_PRICE - year1_rev
    year2_expense = TOTAL_COST - year1_expense
    return (year1_rev, year1_expense), (year2_rev, year2_expense)


def year1_balance_sheet(over_time):
    year1_cost = CUMULATIVE_COST[3]
    if over_time:
        revenue = CONTRACT_PRICE * year1_cost / TOTAL_COST
        return {"계약자산": revenue - ADVANCE, "재고자산(재공품)": 0.0, "계약부채": 0.0}
    return {"계약자산": 0.0, "재고자산(재공품)": float(year1_cost), "계약부채": float(ADVANCE)}


def main():
    print("[1] 분기별 해지 보상 점검 — 문단 37·B9")
    print(f"  계약가격 {CONTRACT_PRICE:,}, 추정 총원가 {TOTAL_COST}, 원가 대비 예상 이윤 {EXPECTED_MARGIN:.0%}, 선급금 {ADVANCE}")
    verdicts = {}
    for name, comp, _ in CONTRACTS:
        rows = payment_right_each_quarter(comp)
        print(f"  {name}")
        print("    분기  누적원가  해지보상  요구금액  충족")
        for quarter, cost, got, need, ok in rows:
            print(f"    {quarter:>3}  {cost:>8}  {got:>8.1f}  {need:>8.1f}  {'예' if ok else '아니오'}")
        verdicts[name] = all(ok for *_, ok in rows)
        failed = [q for q, *_, ok in rows if not ok]
        if failed:
            print(f"    -> 충족하지 못한 분기: {failed}")
        else:
            print("    -> 모든 분기 충족")
    print()

    print("[2] 문단 35⑶ 판정 — 대체 용도 없음 AND 집행 가능한 지급청구권")
    print("  계약                          대체용도없음  지급청구권  35⑶   인식")
    results = {}
    for name, _, alt_use in CONTRACTS:
        no_alt = not alt_use
        right = verdicts[name]
        over_time = no_alt and right
        results[name] = over_time
        print(f"  {name:<24}  {'예' if no_alt else '아니오':>8}  {'예' if right else '아니오':>8}  "
              f"{'충족' if over_time else '미충족':>4}  {'기간에 걸쳐' if over_time else '인도 시점'}")
    print()

    print("[3] 연차별 수익과 이익")
    for name, _, _ in CONTRACTS:
        (r1, c1), (r2, c2) = yearly_revenue(results[name])
        print(f"  {name}")
        print(f"    1년차  수익 {r1:>7.1f}  매출원가 {c1:>5}  이익 {r1 - c1:>7.1f}")
        print(f"    2년차  수익 {r2:>7.1f}  매출원가 {c2:>5}  이익 {r2 - c2:>7.1f}")
    print()

    print("[4] 1년차 말 재무상태표 — 같은 공사, 다른 계정")
    for label, over_time in (("기간에 걸쳐 (A)", True), ("인도 시점 (B·C·D)", False)):
        bs = year1_balance_sheet(over_time)
        parts = ", ".join(f"{k} {v:.1f}" for k, v in bs.items())
        print(f"  {label}: {parts}")
    print("  인도 시점 인식에서 원가 480 은 비용이 아니라 재고로 남고, 선급금 200 은 계약부채로 남는다")


if __name__ == "__main__":
    main()
