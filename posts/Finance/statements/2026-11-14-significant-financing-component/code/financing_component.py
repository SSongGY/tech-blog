"""유의적인 금융요소 — 기업회계기준서 제1115호 문단 60~65.

가상 회사 차카기계가 현금판매가격 1,000,000(천원)인 설비 한 대를
세 가지 지급 조건으로 판다. 대금을 늦게 받는 할부(기업이 금융을 제공),
먼저 받는 선수금(고객이 금융을 제공), 10개월 뒤 받는 단기 외상이다.
"""

CASH_PRICE = 1_000_000      # 인도할 때 현금으로 결제하면 받을 가격
COST = 600_000              # 설비 원가 — 매출총이익을 보이려고 둔다
INSTALLMENT = 380_000       # 할부: 인도 후 1·2·3년 말에 받는 금액
PREPAYMENT = 890_000        # 선수금: 인도 2년 전 계약일에 받는 금액
PREPAY_YEARS = 2


def present_value(rate, payments):
    """payments 는 (연수, 금액) 목록이다. 기준 시점(인도일) 현재가치."""
    return sum(amount / (1 + rate) ** year for year, amount in payments)


def implied_rate(cash_price, payments):
    """명목 대가를 현금판매가격으로 할인하는 이자율을 이분법으로 찾는다.

    문단 64 는 이 방식으로 할인율을 산정할 수 있다고 적는다.
    """
    low, high = 0.0, 1.0
    for _ in range(200):
        mid = (low + high) / 2
        if present_value(mid, payments) > cash_price:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def won(value):
    return f"{value:>11,.0f}"


def installment_case():
    payments = [(1, INSTALLMENT), (2, INSTALLMENT), (3, INSTALLMENT)]
    nominal = sum(amount for _, amount in payments)
    rate = implied_rate(CASH_PRICE, payments)
    print("[1] 할부판매 — 인도 후 3년간 매년 말 380,000 회수")
    print(f"    명목 대가 {won(nominal)}  현금판매가격 {won(CASH_PRICE)}"
          f"  차이 {won(nominal - CASH_PRICE)} ({(nominal / CASH_PRICE - 1) * 100:.1f}%)")
    print(f"    내재 이자율 {rate * 100:.4f}%  (문단 64: 계약 개시시점에 정하고 바꾸지 않는다)")
    print()
    print("    연도   기초 채권    이자수익       회수    기말 채권")
    balance = CASH_PRICE
    interests = []
    for year in range(1, 4):
        interest = round(balance * rate)
        if year == 3:
            # 반올림 누적분을 마지막 해에서 맞춘다
            interest = INSTALLMENT - balance
        closing = balance + interest - INSTALLMENT
        interests.append(interest)
        print(f"    {year}년차 {won(balance)} {won(interest)} {won(INSTALLMENT)} {won(closing)}")
        balance = closing
    print(f"    이자수익 합계 {won(sum(interests))}")
    print()
    return nominal, rate, interests


def prepayment_case():
    # 한 번 받고 한 번 인도하므로 이자율은 닫힌 식으로 나온다.
    # 선수금이 인도일까지 불어나 현금판매가격이 되는 이자율이다.
    rate = (CASH_PRICE / PREPAYMENT) ** (1 / PREPAY_YEARS) - 1
    print("[2] 선수금 — 인도 2년 전 계약일에 890,000 수령")
    print(f"    명목 대가 {won(PREPAYMENT)}  현금판매가격 {won(CASH_PRICE)}"
          f"  차이 {won(CASH_PRICE - PREPAYMENT)}")
    print(f"    내재 이자율 {rate * 100:.4f}%")
    print()
    print("    연도   기초 계약부채    이자비용    기말 계약부채")
    balance = PREPAYMENT
    interests = []
    for year in range(1, PREPAY_YEARS + 1):
        interest = round(balance * rate)
        if year == PREPAY_YEARS:
            interest = CASH_PRICE - balance
        closing = balance + interest
        interests.append(interest)
        print(f"    {year}년차 {won(balance)}     {won(interest)}  {won(closing)}")
        balance = closing
    print(f"    인도일에 계약부채 {won(balance)} 를 수익으로 대체")
    print()
    return rate, interests


def compare_income(inst_nominal, inst_interests, pre_interests):
    print("[3] 손익계산서에 남는 모양 — 조정 여부별 (원가 600,000)")
    print("    구분                         매출      매출총이익     이자손익    전 기간 합계")
    rows = [
        ("할부  금융요소 반영", CASH_PRICE, sum(inst_interests)),
        ("할부  반영하지 않음", inst_nominal, 0),
        ("선수금 금융요소 반영", CASH_PRICE, -sum(pre_interests)),
        ("선수금 반영하지 않음", PREPAYMENT, 0),
    ]
    for label, revenue, interest in rows:
        gross = revenue - COST
        print(f"    {label:<14} {won(revenue)} {won(gross)} {won(interest)} {won(gross + interest)}")
    print("    → 같은 지급 조건이면 전 기간 합계는 같고, 매출과 이자로 나뉘는 몫만 달라진다")
    print()


def short_term_case():
    months = 10
    nominal = 1_040_000
    print("[4] 단기 외상 — 인도 후 10개월 뒤 1,040,000 회수")
    print(f"    인도~회수 기간 {months}개월 ≤ 12개월 → 문단 63 실무적 간편법 적용 가능")
    print(f"    간편법 적용 시 인도일 수익 {won(nominal)}  (현금판매가격과 차이 {won(nominal - CASH_PRICE)}도 매출)")
    print()


def main():
    print("가상 회사: 차카기계 / 설비 1대, 현금판매가격 1,000,000(천원), 원가 600,000")
    print()
    inst_nominal, _, inst_interests = installment_case()
    _, pre_interests = prepayment_case()
    compare_income(inst_nominal, inst_interests, pre_interests)
    short_term_case()


if __name__ == "__main__":
    main()
