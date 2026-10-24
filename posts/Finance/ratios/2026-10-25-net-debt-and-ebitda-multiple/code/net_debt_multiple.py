"""순차입금과 순차입금배수(Net Debt/EBITDA)를 가상 회사 세 곳으로 계산한다.

세 회사의 자기자본 400과 부채총계 600을 같게 맞춰 부채비율을 150.0%로 고정하고,
차입금 구성·보유 현금·이익 규모만 다르게 두었다. 부채비율과 차입금의존도가 같아도
순차입금배수는 갈린다는 것, 순차입금이 같아도 배수는 갈린다는 것, 같은 배수가
같은 상황이 아니라는 것을 차례로 확인한다.

차입금의존도와 부채비율 산식은 한국은행 기업경영분석 710·707을 따르고,
차입금의 기초·기말 조정표는 K-IFRS 제1007호 문단 44B 의 변동 유형을 쓴다.
금액 단위는 억원이고, 차입금평균이자율 5.0%와 리스 금액은 설명용 가정값이다.
"""

import unicodedata

INTEREST_RATE = 0.05
TOTAL_CAPITAL = 1000  # 세 회사 모두 자기자본 400 + 부채총계 600


def width(text):
    """한글은 두 칸을 차지하므로 출력 폭을 글자 수가 아니라 칸 수로 센다."""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def pad(text, columns, align="left"):
    gap = " " * max(0, columns - width(text))
    return text + gap if align == "left" else gap + text


def num(value, decimals=1, columns=9):
    return pad(f"{value:,.{decimals}f}", columns, "right")


# 자기자본 400 · 부채총계 600 은 세 회사가 같다. 차입금 구성과 현금, 이익만 다르다.
COMPANIES = [
    {
        "name": "마루텍",
        "equity": 400,
        "short_term_debt": 150,
        "long_term_debt": 250,
        "bonds": 100,
        "other_liabilities": 100,  # 매입채무 등 이자를 부담하지 않는 부채
        "cash": 350,
        "operating_income": 110,
        "depreciation": 40,
        "capex": 70,
        "cash_tax": 18,
    },
    {
        "name": "너울산업",
        "equity": 400,
        "short_term_debt": 150,
        "long_term_debt": 250,
        "bonds": 100,
        "other_liabilities": 100,
        "cash": 50,
        "operating_income": 110,
        "depreciation": 40,
        "capex": 70,
        "cash_tax": 18,
    },
    {
        "name": "벼리로지스",
        "equity": 400,
        "short_term_debt": 60,
        "long_term_debt": 140,
        "bonds": 0,
        "other_liabilities": 400,
        "cash": 50,
        "operating_income": 30,
        "depreciation": 20,
        "capex": 25,
        "cash_tax": 4,
    },
]


def gross_debt(c):
    return c["short_term_debt"] + c["long_term_debt"] + c["bonds"]


def total_liabilities(c):
    return gross_debt(c) + c["other_liabilities"]


def net_debt(c):
    return gross_debt(c) - c["cash"]


def ebitda(c):
    """영업이익에 감가상각비와 무형자산상각비를 더한 값. 기준서에 산식이 없는 지표다."""
    return c["operating_income"] + c["depreciation"]


def section(title):
    print()
    print(title)


def table(header, rows, label_width=12):
    print(pad("", label_width) + "".join(pad(h, w, "right") for h, w in header))
    for name, values in rows:
        print(pad(name, label_width) + "".join(values))


def main():
    section("[1] 재무상태표 — 자기자본 400 과 부채총계 600 은 세 회사가 같다 (억원)")
    table(
        [("단기차입금", 11), ("장기차입금", 11), ("회사채", 8), ("차입금 계", 10),
         ("기타부채", 9), ("부채총계", 9), ("현금성자산", 11), ("자기자본", 9)],
        [
            (c["name"], [
                num(c["short_term_debt"], 0, 11), num(c["long_term_debt"], 0, 11),
                num(c["bonds"], 0, 8), num(gross_debt(c), 0, 10),
                num(c["other_liabilities"], 0, 9), num(total_liabilities(c), 0, 9),
                num(c["cash"], 0, 11), num(c["equity"], 0, 9),
            ])
            for c in COMPANIES
        ],
    )

    section("[2] 순차입금과 순차입금배수 — 부채비율이 같아도 갈린다 (억원, %, 배)")
    table(
        [("부채비율", 9), ("차입금의존도", 13), ("총차입금", 9), ("현금성자산", 11),
         ("순차입금", 9), ("EBITDA", 9), ("순차입금배수", 13)],
        [
            (c["name"], [
                num(total_liabilities(c) / c["equity"] * 100, 1, 9),
                num(gross_debt(c) / TOTAL_CAPITAL * 100, 1, 13),
                num(gross_debt(c), 0, 9), num(c["cash"], 0, 11),
                num(net_debt(c), 0, 9), num(ebitda(c), 0, 9),
                num(net_debt(c) / ebitda(c), 2, 13),
            ])
            for c in COMPANIES
        ],
    )

    section("[3] EBITDA 로 가는 사다리 — 영업이익에 상각비를 되돌린다 (억원)")
    table(
        [("영업이익", 9), ("감가상각비", 11), ("EBITDA", 9), ("이자비용", 9),
         ("법인세 납부", 12), ("자본적지출", 11), ("남는 현금", 10)],
        [
            (c["name"], [
                num(c["operating_income"], 0, 9), num(c["depreciation"], 0, 11),
                num(ebitda(c), 0, 9), num(gross_debt(c) * INTEREST_RATE, 1, 9),
                num(c["cash_tax"], 0, 12), num(c["capex"], 0, 11),
                num(ebitda(c) - gross_debt(c) * INTEREST_RATE - c["cash_tax"] - c["capex"], 1, 10),
            ])
            for c in COMPANIES
        ],
    )

    section("[4] 배수는 상환 연수가 아니다 — 남는 현금으로 순차입금을 갚으면 (배, 년)")
    table(
        [("순차입금", 9), ("순차입금배수", 13), ("남는 현금", 10), ("실제 상환 연수", 15)],
        [
            (c["name"], [
                num(net_debt(c), 0, 9),
                num(net_debt(c) / ebitda(c), 2, 13),
                num(ebitda(c) - gross_debt(c) * INTEREST_RATE - c["cash_tax"] - c["capex"], 1, 10),
                num(net_debt(c) / (ebitda(c) - gross_debt(c) * INTEREST_RATE
                                   - c["cash_tax"] - c["capex"]), 1, 15),
            ])
            for c in COMPANIES
        ],
    )

    maru = COMPANIES[0]
    section("[5] 마루텍의 현금 350 중 꺼낼 수 없는 돈이 있다면 (억원, 배)")
    pledged, overseas = 120, 80
    usable = maru["cash"] - pledged - overseas
    adjusted = gross_debt(maru) - usable
    table(
        [("차감한 현금", 12), ("순차입금", 9), ("순차입금배수", 13)],
        [
            ("현금 전액 차감", [num(maru["cash"], 0, 12), num(net_debt(maru), 0, 9),
                           num(net_debt(maru) / ebitda(maru), 2, 13)]),
            (f"질권 {pledged} 제외", [num(maru["cash"] - pledged, 0, 12),
                                  num(gross_debt(maru) - maru["cash"] + pledged, 0, 9),
                                  num((gross_debt(maru) - maru["cash"] + pledged) / ebitda(maru), 2, 13)]),
            (f"해외 {overseas} 도 제외", [num(usable, 0, 12), num(adjusted, 0, 9),
                                     num(adjusted / ebitda(maru), 2, 13)]),
        ],
        label_width=18,
    )

    section("[6] 너울산업이 창고 운용리스를 사용권자산으로 인식하면 (억원, 배)")
    # 연 리스료 36 이 영업비용에서 빠지고 사용권자산 감가상각비 30 과 리스이자 6 으로 갈린다.
    lease_liability, lease_payment, lease_depreciation = 150, 36, 30
    nool = COMPANIES[1]
    before_ebitda = ebitda(nool)
    after_operating = nool["operating_income"] + lease_payment - lease_depreciation
    after_ebitda = after_operating + nool["depreciation"] + lease_depreciation
    table(
        [("영업이익", 9), ("상각비 계", 10), ("EBITDA", 9), ("순차입금", 9), ("순차입금배수", 13)],
        [
            ("리스 인식 전", [num(nool["operating_income"], 0, 9), num(nool["depreciation"], 0, 10),
                         num(before_ebitda, 0, 9), num(net_debt(nool), 0, 9),
                         num(net_debt(nool) / before_ebitda, 2, 13)]),
            ("리스부채 포함", [num(after_operating, 0, 9),
                          num(nool["depreciation"] + lease_depreciation, 0, 10),
                          num(after_ebitda, 0, 9), num(net_debt(nool) + lease_liability, 0, 9),
                          num((net_debt(nool) + lease_liability) / after_ebitda, 2, 13)]),
            ("리스부채 제외", [num(after_operating, 0, 9),
                          num(nool["depreciation"] + lease_depreciation, 0, 10),
                          num(after_ebitda, 0, 9), num(net_debt(nool), 0, 9),
                          num(net_debt(nool) / after_ebitda, 2, 13)]),
        ],
        label_width=16,
    )

    section("[7] 너울산업의 차입금 조정표 — K-IFRS 제1007호 문단 44B 의 변동 유형 (억원)")
    opening_debt, opening_cash = 470, 90
    borrowed, repaid, fx = 120, -100, 10
    closing_debt = opening_debt + borrowed + repaid + fx
    print(f"  기초 총차입금                       {opening_debt:>8,.0f}")
    print(f"  (+) 재무활동 현금흐름 — 차입        {borrowed:>8,.0f}")
    print(f"  (+) 재무활동 현금흐름 — 상환        {repaid:>8,.0f}")
    print(f"  (+) 환율변동효과 (비현금)           {fx:>8,.0f}")
    print(f"  기말 총차입금                       {closing_debt:>8,.0f}")
    print(f"  (-) 기말 현금성자산                 {nool['cash']:>8,.0f}")
    print(f"  기말 순차입금                       {closing_debt - nool['cash']:>8,.0f}")
    print()
    print(f"  기초 순차입금 {opening_debt - opening_cash:,.0f} 에서 기말 {closing_debt - nool['cash']:,.0f} 로 "
          f"{closing_debt - nool['cash'] - (opening_debt - opening_cash):,.0f} 늘었고, "
          f"그중 {fx:,.0f} 은 현금이 오가지 않은 환율변동이다.")


if __name__ == "__main__":
    main()
