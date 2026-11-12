"""재매입 선도·콜옵션이 붙은 판매를 기업회계기준서 제1115호 B66~B69 에 따라 처리한다.

가상 회사 가나기계가 장부금액 700 의 기계를 고객에게 1,000 에 넘기고
2년 뒤 다시 사 오는 약정을 맺는다. 재매입 가격만 바꿔 세 처리를 비교한다.
단위는 백만원이다. 숫자는 계산을 보이려고 만든 가상 자료다.
"""

SALE_PRICE = 1_000.0
CARRYING_AMOUNT = 700.0
TERM_YEARS = 2
# 리스로 처리하면 기계는 리스 기초자산으로 남아 감가상각된다(제1116호 문단 84).
# 남은 내용연수 10년, 잔존가치 0, 정액법은 예제를 위한 가정이다.
REMAINING_LIFE_YEARS = 10
YEARS = range(1, TERM_YEARS + 1)


def classify(repurchase_price, sale_price=SALE_PRICE):
    """B66: 판매후리스가 아니라는 전제에서 재매입 가격으로 리스와 금융약정을 가른다."""
    if repurchase_price < sale_price:
        return "리스 (B66⑴)"
    return "금융약정 (B66⑵, B68)"


def case_sale():
    """재매입약정이 없을 때: 넘기는 날 통제가 이전되어 매출과 원가를 인식한다."""
    rows = {0: {"매출": SALE_PRICE, "매출원가": -CARRYING_AMOUNT}}
    for y in YEARS:
        rows[y] = {}
    return rows


def case_lease(repurchase_price):
    """B66⑴: 받은 대가 중 재매입 대금은 부채로 두고 차액을 리스기간에 걸쳐 리스료수익으로."""
    lease_income = (SALE_PRICE - repurchase_price) / TERM_YEARS
    depreciation = CARRYING_AMOUNT / REMAINING_LIFE_YEARS
    rows = {0: {}}
    for y in YEARS:
        rows[y] = {"리스료수익": lease_income, "감가상각비": -depreciation}
    return rows


def effective_rate(received, repay, years):
    """받은 금액이 years 뒤 repay 가 되게 하는 연 유효이자율."""
    return (repay / received) ** (1 / years) - 1


def case_financing(repurchase_price):
    """B68: 기계를 계속 인식하고 받은 대가를 금융부채로, 차액을 이자로 나눠 인식한다."""
    rate = effective_rate(SALE_PRICE, repurchase_price, TERM_YEARS)
    liability = SALE_PRICE
    rows = {0: {}}
    schedule = []
    for y in YEARS:
        interest = liability * rate
        opening = liability
        liability += interest
        rows[y] = {"이자비용": -interest}
        schedule.append((y, opening, interest, liability))
    return rows, rate, schedule


def total(rows):
    return sum(v for r in rows.values() for v in r.values())


def print_rows(label, rows):
    print(f"  {label}")
    for t in sorted(rows):
        when = "넘긴 날" if t == 0 else f"{t}년차"
        items = rows[t]
        if not items:
            print(f"    {when:<6}  (손익 없음)")
            continue
        text = "  ".join(f"{k} {v:>8,.1f}" for k, v in items.items())
        print(f"    {when:<6}  {text}")
    print(f"    2년 손익 합계  {total(rows):>8,.1f}")


def main():
    print("[1] 재매입 가격에 따른 분류 (원래 판매가격 1,000, 판매후리스 아님)")
    for price in (800.0, 1_000.0, 1_100.0):
        print(f"    재매입 가격 {price:>7,.1f}  ->  {classify(price)}")
    print()

    print("[2] 세 처리의 손익 — 재매입이 실제로 일어나는 경우")
    print_rows("가. 재매입약정 없음 — 판매", case_sale())
    print_rows("나. 재매입 800 — 리스", case_lease(800.0))
    fin_rows, rate, schedule = case_financing(1_100.0)
    print_rows("다. 재매입 1,100 — 금융약정", fin_rows)
    print()

    print(f"[3] 금융약정의 부채 — 유효이자율 {rate:.4%} (1,000 -> 1,100, 2년)")
    print("    연도      기초 부채     이자비용     기말 부채")
    for y, opening, interest, closing in schedule:
        print(f"    {y}년차   {opening:>9,.1f}   {interest:>9,.1f}   {closing:>9,.1f}")
    print()

    print("[4] 2년 뒤 옵션이 행사되지 않고 소멸 (콜옵션일 때, B69)")
    lease_rows = case_lease(800.0)
    lease_dep_total = -sum(r.get("감가상각비", 0.0) for r in lease_rows.values())
    lease_carrying = CARRYING_AMOUNT - lease_dep_total
    lapse_lease = 800.0 - lease_carrying
    print(f"    나. 리스      부채 800.0 제거 -> 매출 800.0, 매출원가 {lease_carrying:,.1f}"
          f"  (2년 감가상각 {lease_dep_total:,.1f} 뒤 장부금액)")
    print(f"        2년 손익 합계  {total(lease_rows) + lapse_lease:>8,.1f}")
    lapse_fin = 1_100.0 - CARRYING_AMOUNT
    print(f"    다. 금융약정  부채 1,100.0 제거 -> 매출 1,100.0, 매출원가 {CARRYING_AMOUNT:,.1f}")
    print(f"        2년 손익 합계  {total(fin_rows) + lapse_fin:>8,.1f}")
    print(f"    비교: 가. 판매  2년 손익 합계  {total(case_sale()):>8,.1f}")
    print()

    print("[5] 시간가치를 넣은 비교 (B67) — 재매입 가격 1,000 을 2년 뒤에 치를 때")
    for discount in (0.0, 0.03, 0.05):
        pv = 1_000.0 / (1 + discount) ** TERM_YEARS
        verdict = "판매가격 이상" if pv >= SALE_PRICE else "판매가격 미만"
        print(f"    할인율 {discount:>4.0%}  현재가치 {pv:>8,.1f}  ->  {verdict}")


if __name__ == "__main__":
    main()
