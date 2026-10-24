"""운전자본 증감이 영업활동 현금흐름을 어떻게 끌어내리는지 가상 회사로 계산한다.

가상 회사 `사름식품`의 매출액만 바꿔 네 가지 경우를 만든다. 매출원가율·판관비율·
회전일수는 네 경우가 모두 같으므로 영업이익률도 같다. 그런데도 영업활동 현금흐름은
갈린다. 매출채권·재고자산·매입채무가 매출에 비례해 늘고 줄기 때문이다.

간접법의 조정 항목과 부호는 K-IFRS 제1007호 문단 20(1)(재고자산과 영업활동 관련
채권·채무의 변동)을 따른다. 순운전자본은 한국은행 기업경영분석 713(순운전자본 대
총자본)의 분자 정의인 유동자산 − 유동부채에서 영업 항목만 뽑아 쓴다.
금액 단위는 억원이고, 회전일수·법인세율·감가상각비율은 설명용 가정값이다.
"""

import unicodedata

BASE_SALES = 1000          # 전기 매출액
COGS_RATE = 0.70           # 매출원가율
SGA_RATE = 0.24            # 판매비와관리비율 — 영업이익률은 6.0% 로 고정된다
TAX_RATE = 0.22
DEPRECIATION_RATE = 0.025  # 매출액 대비 감가상각비
DAYS = 365

RECEIVABLE_DAYS = 60       # 매출액 기준
INVENTORY_DAYS = 70        # 매출원가 기준
PAYABLE_DAYS = 30          # 매출원가 기준


def width(text):
    """한글은 두 칸을 차지하므로 출력 폭을 글자 수가 아니라 칸 수로 센다."""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def pad(text, columns, align="left"):
    gap = " " * max(0, columns - width(text))
    return text + gap if align == "left" else gap + text


def num(value, decimals=2, columns=10):
    return pad(f"{value:,.{decimals}f}", columns, "right")


def working_capital(sales, receivable_days=RECEIVABLE_DAYS, inventory_days=INVENTORY_DAYS,
                    payable_days=PAYABLE_DAYS):
    """매출 규모에 회전일수를 걸어 영업 운전자본 세 항목의 기말 잔액을 만든다."""
    cogs = sales * COGS_RATE
    receivables = sales * receivable_days / DAYS
    inventory = cogs * inventory_days / DAYS
    payables = cogs * payable_days / DAYS
    return {
        "receivables": receivables,
        "inventory": inventory,
        "payables": payables,
        "net": receivables + inventory - payables,
    }


def net_income(sales):
    return sales * (1 - COGS_RATE - SGA_RATE) * (1 - TAX_RATE)


def operating_cash_flow(sales, opening=None, **days):
    """간접법: 당기순이익 + 감가상각비 − 영업 자산 증가 + 영업 부채 증가."""
    opening = opening if opening is not None else working_capital(BASE_SALES)
    closing = working_capital(sales, **days)
    return (net_income(sales)
            + sales * DEPRECIATION_RATE
            - (closing["receivables"] - opening["receivables"])
            - (closing["inventory"] - opening["inventory"])
            + (closing["payables"] - opening["payables"]))


CASES = [
    ("역성장 −20%", 800),
    ("정체 0%", 1000),
    ("성장 +20%", 1200),
    ("급성장 +50%", 1500),
]

OPENING = working_capital(BASE_SALES)


def section(title):
    print()
    print(title)


def table(header, rows, label_width=14):
    print(pad("", label_width) + "".join(pad(h, w, "right") for h, w in header))
    for name, values in rows:
        print(pad(name, label_width) + "".join(values))


def main():
    section(f"[1] 전기 재무상태표의 영업 운전자본 — 매출액 {BASE_SALES:,} 기준 (억원)")
    print(f"  매출채권 (매출액 × {RECEIVABLE_DAYS}/365)      {OPENING['receivables']:>10,.2f}")
    print(f"  재고자산 (매출원가 × {INVENTORY_DAYS}/365)     {OPENING['inventory']:>10,.2f}")
    print(f"  매입채무 (매출원가 × {PAYABLE_DAYS}/365)     {-OPENING['payables']:>10,.2f}")
    print(f"  순운전자본                        {OPENING['net']:>10,.2f}")

    section("[2] 손익 — 네 경우의 영업이익률은 6.00% 로 같다 (억원, %)")
    table(
        [("매출액", 10), ("매출원가", 10), ("판관비", 10), ("영업이익", 10),
         ("영업이익률", 11), ("당기순이익", 11)],
        [
            (name, [
                num(sales, 0, 10), num(sales * COGS_RATE, 1, 10), num(sales * SGA_RATE, 1, 10),
                num(sales * (1 - COGS_RATE - SGA_RATE), 2, 10),
                num((1 - COGS_RATE - SGA_RATE) * 100, 2, 11), num(net_income(sales), 2, 11),
            ])
            for name, sales in CASES
        ],
    )

    section("[3] 기말 운전자본 잔액과 전기 대비 증감 (억원)")
    table(
        [("매출채권", 10), ("재고자산", 10), ("매입채무", 10), ("순운전자본", 11),
         ("전기 대비 증감", 15)],
        [
            (name, [
                num(working_capital(sales)["receivables"], 2, 10),
                num(working_capital(sales)["inventory"], 2, 10),
                num(working_capital(sales)["payables"], 2, 10),
                num(working_capital(sales)["net"], 2, 11),
                num(working_capital(sales)["net"] - OPENING["net"], 2, 15),
            ])
            for name, sales in CASES
        ],
    )

    section("[4] 간접법 — 당기순이익에서 영업활동 현금흐름까지 (억원)")
    table(
        [("당기순이익", 11), ("+감가상각비", 12), ("-매출채권증가", 14),
         ("-재고증가", 11), ("+매입채무증가", 14), ("영업활동현금흐름", 17)],
        [
            (name, [
                num(net_income(sales), 2, 11), num(sales * DEPRECIATION_RATE, 2, 12),
                num(-(working_capital(sales)["receivables"] - OPENING["receivables"]), 2, 14),
                num(-(working_capital(sales)["inventory"] - OPENING["inventory"]), 2, 11),
                num(working_capital(sales)["payables"] - OPENING["payables"], 2, 14),
                num(operating_cash_flow(sales), 2, 17),
            ])
            for name, sales in CASES
        ],
    )

    section("[5] 이익과 현금의 간격 — 같은 이익률에서 얼마나 벌어지는가 (억원, 배)")
    table(
        [("영업이익", 10), ("영업활동현금흐름", 17), ("차이", 11), ("현금흐름÷영업이익", 18)],
        [
            (name, [
                num(sales * (1 - COGS_RATE - SGA_RATE), 2, 10),
                num(operating_cash_flow(sales), 2, 17),
                num(operating_cash_flow(sales) - sales * (1 - COGS_RATE - SGA_RATE), 2, 11),
                num(operating_cash_flow(sales) / (sales * (1 - COGS_RATE - SGA_RATE)), 2, 18),
            ])
            for name, sales in CASES
        ],
    )

    section("[6] 영업활동 현금흐름이 0 이 되는 성장률 — 이분법으로 찾는다")
    low, high = 0.0, 3.0
    for _ in range(200):
        mid = (low + high) / 2
        if operating_cash_flow(BASE_SALES * (1 + mid)) > 0:
            low = mid
        else:
            high = mid
    breakeven = (low + high) / 2
    print(f"  매출 성장률 {breakeven * 100:,.2f}% 에서 영업활동 현금흐름 "
          f"{operating_cash_flow(BASE_SALES * (1 + breakeven)):,.4f}")
    print(f"  이보다 빨리 자라면 이익이 나는 해에도 영업에서 현금이 빠져나간다.")
    print(f"  (회전일수 매출채권 {RECEIVABLE_DAYS}일 · 재고 {INVENTORY_DAYS}일 · "
          f"매입채무 {PAYABLE_DAYS}일, 영업이익률 6.00% 일 때)")

    section("[7] 급성장 +50% 에서 회전일수만 줄이면 (억원)")
    faster = {"receivable_days": 45, "inventory_days": 55, "payable_days": PAYABLE_DAYS}
    table(
        [("매출채권", 10), ("재고자산", 10), ("순운전자본", 11), ("전기 대비 증감", 15),
         ("영업활동현금흐름", 17)],
        [
            ("60일 · 70일", [
                num(working_capital(1500)["receivables"], 2, 10),
                num(working_capital(1500)["inventory"], 2, 10),
                num(working_capital(1500)["net"], 2, 11),
                num(working_capital(1500)["net"] - OPENING["net"], 2, 15),
                num(operating_cash_flow(1500), 2, 17),
            ]),
            ("45일 · 55일", [
                num(working_capital(1500, **faster)["receivables"], 2, 10),
                num(working_capital(1500, **faster)["inventory"], 2, 10),
                num(working_capital(1500, **faster)["net"], 2, 11),
                num(working_capital(1500, **faster)["net"] - OPENING["net"], 2, 15),
                num(operating_cash_flow(1500, **faster), 2, 17),
            ]),
        ],
    )

    section("[8] 재무상태표의 차액과 현금흐름표의 변동액은 같지 않다 (억원)")
    # 급성장 +50% 의 매출채권 증가분 중 일부가 영업활동 밖에서 들어온 경우를 가정한다.
    increase = working_capital(1500)["receivables"] - OPENING["receivables"]
    acquired, fx = 40.00, 15.00
    print(f"  재무상태표 매출채권 증가 (기말 − 기초)        {increase:>10,.2f}")
    print(f"  (-) 사업결합으로 승계한 매출채권            {-acquired:>10,.2f}")
    print(f"  (-) 외화 매출채권의 환율변동효과            {-fx:>10,.2f}")
    print(f"  영업활동에서 조정할 매출채권 증가            {increase - acquired - fx:>10,.2f}")
    print()
    print(f"  두 숫자를 같다고 보면 영업활동 현금흐름을 {acquired + fx:,.2f} 만큼 "
          f"적게 적는다.")


if __name__ == "__main__":
    main()
