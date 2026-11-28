"""제조자·판매자 리스제공자의 개시일 매출이익 — 기업회계기준서 제1116호 문단 71~74.

가상 회사 사하기계가 원가 70억원, 정상 판매가격(공정가치) 100억원인 기계를
5년 금융리스로 내준다. 시장이자율은 10%, 5년 뒤 돌려받을 무보증잔존가치는 10억원이다.
고객을 끌려고 연 2%를 내건 경우와 시장이자율로 리스료를 정한 경우를 비교한다.
"""

import platform

COST = 70.0          # 기계 원가(억원)
FAIR_VALUE = 100.0   # 정상 판매가격 = 공정가치
YEARS = 5
MARKET_RATE = 0.10
TEASER_RATE = 0.02   # 판촉용으로 내건 이자율
RESIDUAL = 10.0      # 5년 말 무보증잔존가치
CLOSING_COST = 0.5   # 영업사원 성과수수료 등 리스 체결 원가


def pv_annuity(payment: float, rate: float, years: int) -> float:
    return sum(payment / (1 + rate) ** t for t in range(1, years + 1))


def pv_single(amount: float, rate: float, years: int) -> float:
    return amount / (1 + rate) ** years


def payment_for(rate: float) -> float:
    # 내건 이자율로 공정가치를 회수하도록 연 리스료를 정한다(무보증잔존가치 몫은 빼고)
    target = FAIR_VALUE - pv_single(RESIDUAL, rate, YEARS)
    return target / pv_annuity(1.0, rate, YEARS)


def day_one(payment: float, rate: float) -> dict[str, float]:
    pv_payments = pv_annuity(payment, rate, YEARS)
    pv_residual = pv_single(RESIDUAL, rate, YEARS)
    revenue = min(FAIR_VALUE, pv_payments)  # 문단 71⑴: 둘 중 적은 금액
    cost_of_sales = COST - pv_residual      # 문단 71⑵: 잔존가치 현재가치는 원가에서 뺀다
    return {
        "pv_payments": pv_payments,
        "pv_residual": pv_residual,
        "revenue": revenue,
        "cost_of_sales": cost_of_sales,
        "gross_profit": revenue - cost_of_sales,
        "net_investment": pv_payments + pv_residual,
    }


def schedule(payment: float, rate: float, opening: float) -> list[tuple[int, float, float, float]]:
    rows = []
    balance = opening
    for year in range(1, YEARS + 1):
        income = balance * rate
        balance = balance + income - payment
        if year == YEARS:
            balance -= RESIDUAL  # 기계를 돌려받아 잔존가치만큼 순투자가 빠진다
        rows.append((year, income, payment, balance))
    return rows


def print_day_one(label: str, payment: float, rate: float, result: dict[str, float]) -> None:
    print(f"  {label}")
    print(f"    연 리스료                 {payment:8.2f}")
    print(f"    할인에 쓴 이자율          {rate:8.0%}")
    print(f"    리스료 현재가치           {result['pv_payments']:8.2f}")
    print(f"    무보증잔존가치 현재가치   {result['pv_residual']:8.2f}")
    print(f"    매출액 = min(100, 현재가치) {result['revenue']:6.2f}")
    print(f"    매출원가 = 70 - 잔존 현재가치 {result['cost_of_sales']:4.2f}")
    print(f"    매출총이익                {result['gross_profit']:8.2f}")
    print(f"    리스순투자                {result['net_investment']:8.2f}")


def main() -> None:
    print(f"환경: Python {platform.python_version()}")
    print("가정: 원가 70, 공정가치 100, 5년 매년 말 수취, 시장이자율 10%, 무보증잔존가치 10 (단위: 억원)")
    print()

    print("[0] 일반 판매로 팔았을 때 (문단 72의 비교 대상)")
    print(f"    매출 {FAIR_VALUE:.2f} - 원가 {COST:.2f} = 매출총이익 {FAIR_VALUE - COST:.2f}")
    print()

    market_payment = payment_for(MARKET_RATE)
    teaser_payment = payment_for(TEASER_RATE)

    print("[1] 시장이자율 10%로 리스료를 정한 경우")
    a = day_one(market_payment, MARKET_RATE)
    print_day_one("시장이자율로 할인", market_payment, MARKET_RATE, a)
    print()

    print("[2] 판촉 이자율 2%로 리스료를 정한 경우 — 할인율을 어떻게 고르느냐")
    wrong = day_one(teaser_payment, TEASER_RATE)
    right = day_one(teaser_payment, MARKET_RATE)
    print_day_one("(가) 내건 2%로 할인 — 문단 73이 막는 처리", teaser_payment, TEASER_RATE, wrong)
    print()
    print_day_one("(나) 시장이자율 10%로 할인 — 문단 73의 처리", teaser_payment, MARKET_RATE, right)
    print()
    print(f"    개시일 이익 차이 (가)-(나) = {wrong['gross_profit'] - right['gross_profit']:.2f}")
    print()

    print("[3] 판촉 리스의 연도별 이익 — 개시일 매출총이익 + 금융수익 (단위: 억원)")
    wrong_rows = schedule(teaser_payment, TEASER_RATE, wrong["net_investment"])
    right_rows = schedule(teaser_payment, MARKET_RATE, right["net_investment"])
    print(f"  {'시점':>4}{'(가) 2% 처리':>14}{'(나) 10% 처리':>14}")
    print("  " + "-" * 34)
    print(f"  {'개시일':>4}{wrong['gross_profit']:14.2f}{right['gross_profit']:14.2f}")
    wrong_total = wrong["gross_profit"]
    right_total = right["gross_profit"]
    for (year, w_income, _, w_end), (_, r_income, _, r_end) in zip(wrong_rows, right_rows):
        print(f"  {year:>4}년{w_income:14.2f}{r_income:14.2f}")
        wrong_total += w_income
        right_total += r_income
    print("  " + "-" * 34)
    print(f"  {'합계':>4}{wrong_total:14.2f}{right_total:14.2f}")
    # 부동소수 오차로 -0.00 이 찍히지 않게 반올림 뒤 절댓값을 쓴다
    wrong_end = abs(round(wrong_rows[-1][3], 6))
    right_end = abs(round(right_rows[-1][3], 6))
    print(f"  5년 말 순투자 잔액: (가) {wrong_end:.2f} / (나) {right_end:.2f}")
    print(f"  현금 검산: 리스료 합계 {teaser_payment * YEARS:.2f} + 잔존가치 {RESIDUAL:.2f}"
          f" - 원가 {COST:.2f} = {teaser_payment * YEARS + RESIDUAL - COST:.2f}")
    print()

    print("[4] 리스 체결 원가 (문단 74)")
    print(f"    성과수수료 {CLOSING_COST:.2f} → 개시일 비용. 순투자에 넣지 않는다")
    print(f"    (나) 처리의 개시일 영업 손익 = {right['gross_profit']:.2f} - {CLOSING_COST:.2f}"
          f" = {right['gross_profit'] - CLOSING_COST:.2f}")
    print(f"    리스순투자는 그대로 {right['net_investment']:.2f}")


if __name__ == "__main__":
    main()
