"""사채를 액면·할인·할증으로 발행했을 때 유효이자율법으로 이자비용을 계산한다.

K-IFRS 제1109호: 금융부채는 상각후원가로 측정하고(문단 4.2.1), 최초 측정 때
발행과 직접 관련된 거래원가를 공정가치에서 뺀다(문단 5.1.1).
금액 단위는 억원이다. 회사와 숫자는 모두 가상이다.
"""

import sys

FACE_VALUE = 1_000.0
COUPON_RATE = 0.05
YEARS = 3
MARKET_RATES = {"할증발행": 0.04, "액면발행": 0.05, "할인발행": 0.06}


def cash_flows(face, coupon_rate, years):
    coupon = face * coupon_rate
    return [coupon] * (years - 1) + [coupon + face]


def present_value(flows, rate):
    return sum(flow / (1 + rate) ** t for t, flow in enumerate(flows, start=1))


def effective_rate(flows, amount):
    # 현재가치가 최초 장부금액과 같아지는 할인율을 이분법으로 찾는다.
    # 현재가치는 할인율에 대해 단조 감소하므로 구간이 하나로 좁혀진다
    low, high = 0.0, 1.0
    for _ in range(200):
        middle = (low + high) / 2
        if present_value(flows, middle) > amount:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def amortization_table(initial, rate, flows, face):
    rows = []
    carrying = initial
    for year, flow in enumerate(flows, start=1):
        coupon = flow - (face if year == len(flows) else 0)
        expense = carrying * rate
        amortization = expense - coupon
        ending = carrying + amortization
        rows.append((year, carrying, expense, coupon, amortization, ending))
        carrying = ending - (face if year == len(flows) else 0)
    return rows


def print_table(label, initial, rate, flows):
    print(f"    {label}: 최초 장부금액 {initial:,.1f}, 유효이자율 {rate * 100:.4f}%")
    print(f"    {'연도':<5}{'기초 장부':>10}{'이자비용':>10}{'표면이자':>10}{'상각액':>10}{'기말 장부':>11}")
    total_expense = 0.0
    for year, beginning, expense, coupon, amortization, ending in amortization_table(
            initial, rate, flows, FACE_VALUE):
        total_expense += expense
        print(f"    {year}년차{beginning:>11,.1f}{expense:>10.1f}{coupon:>10.1f}{amortization:>+10.1f}{ending:>11,.1f}")
    print(f"    이자비용 합계 {total_expense:.1f} = 표면이자 {sum(flows) - FACE_VALUE:.1f}"
          f" + (액면 {FACE_VALUE:,.0f} - 최초 장부금액 {initial:,.1f})")
    return total_expense


def issue_prices():
    flows = cash_flows(FACE_VALUE, COUPON_RATE, YEARS)
    print(f"[1] 같은 사채, 다른 시장이자율 — 액면 {FACE_VALUE:,.0f}, 표면이자율 {COUPON_RATE:.0%},"
          f" {YEARS}년 만기, 연 1회 이자")
    print(f"    현금흐름: {', '.join(f'{f:,.0f}' for f in flows)}")
    print(f"    {'구분':<8}{'시장이자율':>8}{'발행가액':>12}{'액면과 차이':>12}")
    prices = {}
    for label, rate in MARKET_RATES.items():
        price = present_value(flows, rate)
        prices[label] = price
        # 부동소수점 오차로 -0.0 이 찍히지 않게 반올림한 뒤 0을 더한다
        difference = round(price - FACE_VALUE, 1) + 0.0
        print(f"    {label:<8}{rate:>9.0%}{price:>13,.1f}{difference:>+13.1f}")
    print("    표면이자율이 시장보다 낮으면 액면보다 싸게, 높으면 액면보다 비싸게 팔린다")
    print()
    return flows, prices


def discount_and_premium(flows, prices):
    print("[2] 유효이자율법 상각표 — 이자비용 = 기초 장부금액 x 유효이자율")
    totals = {}
    for label in ("할인발행", "할증발행"):
        rate = MARKET_RATES[label]
        totals[label] = print_table(label, prices[label], rate, flows)
        print()
    print(f"    현금으로 나가는 이자는 세 경우 모두 해마다 {FACE_VALUE * COUPON_RATE:.0f}이지만,"
          f" 3년 이자비용은 할인 {totals['할인발행']:.1f} / 할증 {totals['할증발행']:.1f}")
    print()


def issuance_costs(flows):
    print("[3] 사채발행비 — 거래원가는 최초 장부금액에서 뺀다 (문단 5.1.1)")
    costs = 20.0
    net_proceeds = FACE_VALUE - costs
    rate = effective_rate(flows, net_proceeds)
    print(f"    액면발행 1,000, 발행비 {costs:.0f} → 실제로 들어온 돈 {net_proceeds:,.0f}")
    print_table("발행비 차감 후", net_proceeds, rate, flows)
    print(f"    표면이자율 5%짜리 사채지만 회사가 부담하는 이자율은 {rate * 100:.2f}%")
    print()

    print("[4] 같은 1,000을 빌리는 두 방법의 유효이자율")
    loan_rate = 0.055
    loan_flows = cash_flows(FACE_VALUE, loan_rate, YEARS)
    loan_effective = effective_rate(loan_flows, FACE_VALUE)
    print(f"    은행 차입금: 금리 {loan_rate:.1%}, 부대비용 0      → 유효이자율 {loan_effective * 100:.2f}%")
    print(f"    회사채     : 표면 {COUPON_RATE:.1%}, 발행비 {costs:.0f}        → 유효이자율 {rate * 100:.2f}%")
    print("    표면 금리만 보면 회사채가 싸 보이지만, 발행비를 넣으면 순서가 바뀐다")
    print()


def current_portion(flows, prices):
    print("[5] 만기가 12개월 안으로 들어오면 유동부채로 옮긴다 (K-IFRS 제1001호 문단 69·72)")
    rows = amortization_table(prices["할인발행"], MARKET_RATES["할인발행"], flows, FACE_VALUE)
    for year, _, _, _, _, ending in rows[:-1]:
        remaining = YEARS - year
        place = "유동부채" if remaining <= 1 else "비유동부채"
        print(f"    {year}년차 말: 남은 만기 {remaining}년, 장부금액 {ending:,.1f} → {place}")
    print()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    flows, prices = issue_prices()
    discount_and_premium(flows, prices)
    issuance_costs(flows)
    current_portion(flows, prices)


if __name__ == "__main__":
    main()
