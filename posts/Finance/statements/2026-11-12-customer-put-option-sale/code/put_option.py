"""고객 풋옵션이 붙은 판매를 기업회계기준서 제1115호 B70~B76 에 따라 처리한다.

가상 회사 다라중공업이 장부금액 700 인 굴착기 10대를 대당 1,000 에 팔고,
3년 뒤 고객이 요청하면 되사 주는 풋옵션을 붙인다. 풋 가격만 다른 세 계약을 비교한다.
단위는 백만원이다. 숫자와 확률은 계산을 보이려고 만든 가상 자료다.
"""

UNITS = 10
SALE_PRICE = 1_000.0          # 대당 원래 판매가격
CARRYING_AMOUNT = 700.0       # 대당 장부금액
TERM_YEARS = 3
MARKET_VALUE_AT_PUT = 600.0   # 3년 뒤 대당 예상 시장가치 (가정)
# 리스로 처리하면 굴착기는 리스 기초자산으로 남아 감가상각된다(제1116호 문단 84).
# 남은 내용연수 10년, 잔존가치 0, 정액법은 예제를 위한 가정이다.
REMAINING_LIFE_YEARS = 10
# 풋 가격이 시장가치보다 낮을 때 행사될 것으로 보는 대수 (가정)
EXPECTED_RETURNS_LOW_PUT = 1
YEARS = range(1, TERM_YEARS + 1)


def classify(put_price, market_value, sale_price=SALE_PRICE):
    """B70~B74 의 네 갈래. 판매후리스가 아니라고 전제한다.

    B71 은 여러 요소를 보라고 하고 그 예로 '재매입 가격이 시장가치보다 유의적으로
    높을 것'을 든다. 예제는 단순화해 풋 가격이 시장가치보다 높으면 유인이 유의적이라고 본다.
    """
    incentive = put_price > market_value
    if put_price < sale_price:
        return "리스 (B70)" if incentive else "반품권이 있는 판매 (B72)"
    if put_price > market_value:
        return "금융약정 (B73)"
    return "반품권이 있는 판매 (B74)"


def case_plain_sale():
    revenue = SALE_PRICE * UNITS
    cost = CARRYING_AMOUNT * UNITS
    return {0: {"매출": revenue, "매출원가": -cost}}


def case_return_right(put_price, expected_returns=EXPECTED_RETURNS_LOW_PUT):
    """B72 -> B20~B27: 되사 줄 것으로 예상되는 몫은 매출 대신 환불부채로 둔다."""
    refund_liability = put_price * expected_returns
    revenue = SALE_PRICE * UNITS - refund_liability
    # B25: 돌려받을 자산은 종전 장부금액에서 예상 가치 감소를 뺀 금액으로 잰다
    value_drop = max(CARRYING_AMOUNT - MARKET_VALUE_AT_PUT, 0.0)
    return_asset = (CARRYING_AMOUNT - value_drop) * expected_returns
    cost = CARRYING_AMOUNT * UNITS - return_asset
    detail = {"환불부채": refund_liability, "반환재고회수권": return_asset}
    return {0: {"매출": revenue, "매출원가": -cost}}, detail


def case_lease(put_price):
    """B70: 고객이 낸 판매가격과 풋 가격의 차이는 3년 사용의 대가다."""
    lease_income = (SALE_PRICE - put_price) * UNITS / TERM_YEARS
    depreciation = CARRYING_AMOUNT * UNITS / REMAINING_LIFE_YEARS
    rows = {0: {}}
    for y in YEARS:
        rows[y] = {"리스료수익": lease_income, "감가상각비": -depreciation}
    return rows


def case_financing(put_price):
    """B73 -> B68: 받은 대가를 금융부채로 두고 풋 가격까지 이자로 키운다."""
    received = SALE_PRICE * UNITS
    repay = put_price * UNITS
    rate = (repay / received) ** (1 / TERM_YEARS) - 1
    liability = received
    rows = {0: {}}
    for y in YEARS:
        interest = liability * rate
        liability += interest
        rows[y] = {"이자비용": -interest}
    return rows, rate


def total(rows):
    return sum(v for r in rows.values() for v in r.values())


def print_rows(label, rows):
    print(f"  {label}")
    for t in sorted(rows):
        when = "판 날" if t == 0 else f"{t}년차"
        items = rows[t]
        if not items:
            print(f"    {when:<5}  (손익 없음)")
            continue
        text = "  ".join(f"{k} {v:>9,.1f}" for k, v in items.items())
        print(f"    {when:<5}  {text}")
    print(f"    3년 손익 합계  {total(rows):>9,.1f}")


def main():
    print(f"[1] 풋 가격에 따른 분류 (원래 판매가격 {SALE_PRICE:,.0f}, 판매후리스 아님)")
    print("    풋 가격    예상 시장가치   분류")
    cases = [(400.0, 600.0), (500.0, 600.0), (600.0, 600.0), (700.0, 600.0),
             (900.0, 600.0), (1_000.0, 600.0), (1_050.0, 600.0), (1_050.0, 1_200.0)]
    for put, market in cases:
        print(f"    {put:>7,.0f}    {market:>9,.0f}      {classify(put, market)}")
    print()

    print(f"[2] 굴착기 {UNITS}대, 3년 뒤 예상 시장가치 대당 {MARKET_VALUE_AT_PUT:,.0f}")
    print_rows("가. 풋옵션 없음 — 판매", case_plain_sale())
    ret_rows, detail = case_return_right(500.0)
    print_rows(f"나. 풋 500 — 반품권이 있는 판매 ({EXPECTED_RETURNS_LOW_PUT}대 행사 예상)", ret_rows)
    print("    " + "  ".join(f"{k} {v:,.1f}" for k, v in detail.items()))
    print_rows("다. 풋 700 — 리스", case_lease(700.0))
    fin_rows, rate = case_financing(1_050.0)
    print_rows(f"라. 풋 1,050 — 금융약정 (유효이자율 {rate:.4%})", fin_rows)
    print()

    print("[3] 3년 뒤 풋옵션이 행사되지 않고 소멸 (B76)")
    lease_rows = case_lease(700.0)
    dep_total = CARRYING_AMOUNT * UNITS / REMAINING_LIFE_YEARS * TERM_YEARS
    lease_carrying = CARRYING_AMOUNT * UNITS - dep_total
    lapse_lease = 700.0 * UNITS - lease_carrying
    print(f"    다. 리스      부채 {700.0 * UNITS:,.1f} 제거 -> 매출 {700.0 * UNITS:,.1f}, "
          f"매출원가 {lease_carrying:,.1f}")
    print(f"        3년 손익 합계  {total(lease_rows) + lapse_lease:>9,.1f}")
    lapse_fin = 1_050.0 * UNITS - CARRYING_AMOUNT * UNITS
    print(f"    라. 금융약정  부채 {1_050.0 * UNITS:,.1f} 제거 -> 매출 {1_050.0 * UNITS:,.1f}, "
          f"매출원가 {CARRYING_AMOUNT * UNITS:,.1f}")
    print(f"        3년 손익 합계  {total(fin_rows) + lapse_fin:>9,.1f}")
    print(f"    비교: 가. 판매  3년 손익 합계  {total(case_plain_sale()):>9,.1f}")


if __name__ == "__main__":
    main()
