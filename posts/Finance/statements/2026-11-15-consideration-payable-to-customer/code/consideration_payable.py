"""고객에게 지급할 대가 — 기업회계기준서 제1115호 문단 70~72.

가상 식품회사 사아식품이 유통사 자차마트(고객)에 상반기 동안 제품을 팔며
여러 명목으로 돈을 지급한다. 단위는 천원.
"""

SALES = {"1분기": 400_000, "2분기": 450_000}
COST_RATIO = 0.70

# (명목, 지급액, 받은 용역이 구별되는가, 그 용역의 공정가치 — 추정 불가면 None)
PAYMENTS = [
    ("입점 장려금", 30_000, False, None),
    ("전단 공동광고비", 50_000, True, 40_000),
    ("매대 진열 대행료", 20_000, True, None),
]

# 소비자 쿠폰: (프로그램, 약속한 분기, 쿠폰이 붙는 제품을 판 분기, 예상 지급액)
COUPONS = [
    ("쿠폰 A", "1분기", "1분기", 6_000),
    ("쿠폰 A", "1분기", "2분기", 9_000),
    ("쿠폰 B", "2분기", "1분기", 12_000),
]
QUARTER_ORDER = list(SALES)


def classify(amount, distinct, fair_value):
    """문단 70·71: (비용으로 처리할 금액, 수익에서 차감할 금액)."""
    if not distinct:
        return 0, amount
    if fair_value is None:
        return 0, amount
    expense = min(amount, fair_value)
    return expense, amount - expense


def print_inputs():
    print("[0] 입력 자료 (가상, 단위 천원)")
    for quarter, amount in SALES.items():
        print(f"    {quarter} 자차마트 매출(명목) {amount:>9,}  원가율 {COST_RATIO:.0%}")
    for name, amount, distinct, fair_value in PAYMENTS:
        fv = "추정 불가" if fair_value is None else f"{fair_value:,}"
        print(f"    {name:<10} 지급 {amount:>7,}  구별되는 용역 {'예' if distinct else '아니오':<3}  공정가치 {fv}")
    for program, promised, sold, amount in COUPONS:
        print(f"    {program} 약속 {promised} · 대상 제품 판매 {sold} · 예상 지급 {amount:>6,}")
    print()


def payments_table():
    print("[1] 지급 명목별 처리 — 문단 70·71")
    print("    명목             지급액      비용     수익 차감")
    total_expense, total_reduction = 0, 0
    for name, amount, distinct, fair_value in PAYMENTS:
        expense, reduction = classify(amount, distinct, fair_value)
        total_expense += expense
        total_reduction += reduction
        print(f"    {name:<12}{amount:>9,}{expense:>10,}{reduction:>12,}")
    print(f"    {'합계':<12}{sum(p[1] for p in PAYMENTS):>9,}{total_expense:>10,}{total_reduction:>12,}")
    print()
    return total_expense, total_reduction


def coupon_timing():
    print("[2] 쿠폰의 수익 차감 시점 — 문단 72: 판매와 약속 중 나중 분기")
    print("    프로그램  약속    판매    차감 분기   금액")
    by_quarter = dict.fromkeys(QUARTER_ORDER, 0)
    for program, promised, sold, amount in COUPONS:
        later = max(promised, sold, key=QUARTER_ORDER.index)
        by_quarter[later] += amount
        print(f"    {program:<8}{promised:<7}{sold:<7}{later:<9}{amount:>8,}")
    print("    분기별 차감 " + "  ".join(f"{q} {v:,}" for q, v in by_quarter.items()))
    print()
    return by_quarter


def income_statement(total_expense, payment_reduction, coupon_by_quarter):
    gross_sales = sum(SALES.values())
    cost = round(gross_sales * COST_RATIO)
    paid_total = sum(p[1] for p in PAYMENTS) + sum(c[3] for c in COUPONS)
    reduction = payment_reduction + sum(coupon_by_quarter.values())

    rows = [
        ("기준서대로", gross_sales - reduction, total_expense),
        ("전부 판관비로", gross_sales, paid_total),
    ]
    print("[3] 상반기 손익계산서 — 처리 방식별")
    print("    구분            매출       매출원가   매출총이익  총이익률   판관비(지급분)   영업이익")
    for label, revenue, selling_expense in rows:
        gross_profit = revenue - cost
        print(f"    {label:<12}{revenue:>10,}{cost:>11,}{gross_profit:>11,}{gross_profit / revenue:>10.1%}"
              f"{selling_expense:>14,}{gross_profit - selling_expense:>12,}")
    print("    → 영업이익은 같고, 매출과 매출총이익률이 달라진다")


if __name__ == "__main__":
    print_inputs()
    expense, reduction = payments_table()
    coupons = coupon_timing()
    income_statement(expense, reduction, coupons)
