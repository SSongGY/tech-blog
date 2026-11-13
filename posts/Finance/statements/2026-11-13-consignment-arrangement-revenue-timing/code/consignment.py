"""위탁약정을 기업회계기준서 제1115호 문단 B77~B78 에 따라 처리한다.

가상 회사 바사전자가 공기청정기 100대를 유통업자 아자유통에 넘긴다.
계약 조건만 다른 두 경우를 비교한다.
  가. 판매 — 아자유통이 대당 500 에 사들이고, 대금을 무조건 갚아야 하며 반품할 수 없다
  나. 위탁 — 아자유통은 팔린 만큼만 정산하고, 남은 제품은 기간이 끝나면 돌려준다
단위는 천원이다. 숫자는 계산을 보이려고 만든 가상 자료다.
"""

import sys

UNITS_DELIVERED = 100
UNIT_COST = 300.0              # 대당 제조원가(장부금액)
WHOLESALE_PRICE = 500.0        # 가. 판매일 때 아자유통이 사들이는 값
RETAIL_PRICE = 600.0           # 나. 위탁일 때 최종 고객에게 파는 값 (바사전자가 정한다)
COMMISSION = 100.0             # 나. 위탁일 때 대당 판매수수료
DEPOSIT = 10_000.0             # 나. 위탁일 때 아자유통이 낸 보증금
# 아자유통이 최종 고객에게 판 대수 (분기별). 남은 대수는 3분기 말에 돌려받는다.
SELL_THROUGH = {1: 20, 2: 45, 3: 25}
QUARTERS = sorted(SELL_THROUGH)


def check_indicators(name, entity_controls_until_event, can_recall_or_redirect,
                     unconditional_obligation):
    """B78 의 세 지표. 지표일 뿐 판단 기준을 대신하지 않는다(B78 '이에 한정되지는 않는다')."""
    flags = [
        ("⑴ 정해진 사건까지 기업이 통제", entity_controls_until_event),
        ("⑵ 반환 요구·제삼자 이전 가능", can_recall_or_redirect),
        ("⑶ 무조건적인 지급 의무 없음", not unconditional_obligation),
    ]
    hits = sum(1 for _, v in flags if v)
    print(f"  {name}")
    for label, value in flags:
        print(f"    {label:<24} {'예' if value else '아니오'}")
    print(f"    위탁 지표 {hits}/3")
    return hits


def case_sale():
    """B77: 아자유통이 인도 시점에 통제를 얻으면 넘길 때 수익을 인식한다."""
    revenue = WHOLESALE_PRICE * UNITS_DELIVERED
    cost = UNIT_COST * UNITS_DELIVERED
    rows = {q: {"매출": 0.0, "판매수수료": 0.0, "매출원가": 0.0, "기업 재고": 0.0}
            for q in QUARTERS}
    rows[1] = {"매출": revenue, "판매수수료": 0.0, "매출원가": -cost, "기업 재고": 0.0}
    return rows


def case_consignment():
    """B77: 위탁물로 보유되면 넘길 때가 아니라 최종 고객에게 팔릴 때 수익을 인식한다.

    바사전자가 팔리기 전까지 제품을 통제하므로 최종 고객과의 거래에서 본인이다(B35).
    그래서 최종 판매가격을 매출로, 아자유통 몫은 판매수수료(비용)로 둔다.
    """
    on_hand = UNITS_DELIVERED
    rows = {}
    for q in QUARTERS:
        sold = SELL_THROUGH[q]
        on_hand -= sold
        rows[q] = {
            "매출": RETAIL_PRICE * sold,
            "판매수수료": -COMMISSION * sold,
            "매출원가": -UNIT_COST * sold,
            "기업 재고": UNIT_COST * on_hand,
        }
    return rows, on_hand


def print_rows(label, rows):
    print(f"  {label}")
    cumulative = 0.0
    for q in QUARTERS:
        r = rows[q]
        profit = r["매출"] + r["판매수수료"] + r["매출원가"]
        cumulative += profit
        print(f"    {q}분기  매출 {r['매출']:>8,.0f}  수수료 {r['판매수수료']:>7,.0f}"
              f"  매출원가 {r['매출원가']:>8,.0f}  이익 {profit:>7,.0f}"
              f"  누적 {cumulative:>7,.0f}  기말 재고 {r['기업 재고']:>7,.0f}")
    return cumulative


def main():
    print(f"[0] 환경  Python {sys.version.split()[0]}")
    print()
    print("[1] B78 위탁약정 지표")
    check_indicators("가. 판매 계약", False, False, True)
    check_indicators("나. 위탁 계약", True, True, False)
    print()

    print(f"[2] 공기청정기 {UNITS_DELIVERED}대를 1분기 초에 아자유통에 넘김 "
          f"(대당 원가 {UNIT_COST:,.0f})")
    total_sale = print_rows(f"가. 판매 — 대당 {WHOLESALE_PRICE:,.0f}, 반품 불가", case_sale())
    rows, returned = case_consignment()
    total_cons = print_rows(
        f"나. 위탁 — 최종가 {RETAIL_PRICE:,.0f}, 수수료 {COMMISSION:,.0f}", rows)
    print(f"    3분기 말 돌려받은 제품 {returned}대 -> 재고 {UNIT_COST * returned:,.0f} "
          f"(매출 없음)")
    print()

    print("[3] 1분기 말 재무상태표에서 갈리는 줄")
    q1 = rows[1]
    print(f"    가. 판매  매출채권 {WHOLESALE_PRICE * UNITS_DELIVERED:>8,.0f}"
          f"  재고 {0.0:>8,.0f}  예수보증금 {0.0:>8,.0f}")
    receivable = (RETAIL_PRICE - COMMISSION) * SELL_THROUGH[1]
    print(f"    나. 위탁  매출채권 {receivable:>8,.0f}"
          f"  재고 {q1['기업 재고']:>8,.0f}  예수보증금 {DEPOSIT:>8,.0f}")
    print("    (위탁의 보증금은 수익이 아니라 돌려줄 수 있는 돈이므로 부채로 둔다)")
    print()

    print("[4] 세 분기 이익 합계")
    print(f"    가. 판매  {total_sale:>8,.0f}  (1분기에 전부)")
    print(f"    나. 위탁  {total_cons:>8,.0f}  (팔린 {UNITS_DELIVERED - returned}대분, "
          f"{returned}대는 재고로 남음)")
    print(f"    1분기 매출 차이  {case_sale()[1]['매출'] - q1['매출']:>8,.0f}")


if __name__ == "__main__":
    main()
