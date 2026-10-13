"""유동비율과 당좌비율을 가상 회사 세 곳으로 계산한다.

세 회사의 유동자산 합계와 유동부채를 같게 맞추고 구성만 다르게 두었다.
한국은행 기업경영분석 702(유동비율)·703(당좌비율)·704(현금비율)의 산식을 쓴다.
당좌자산은 유동자산에서 재고자산을 뺀 금액이다. 금액 단위는 억원이다.
"""

import unicodedata


def width(text):
    """한글은 두 칸을 차지하므로 출력 폭을 글자 수가 아니라 칸 수로 센다."""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def pad(text, columns, align="left"):
    gap = " " * max(0, columns - width(text))
    return text + gap if align == "left" else gap + text


def num(value, decimals=1, columns=9):
    return pad(f"{value:,.{decimals}f}", columns, "right")


# 유동자산 합계 300, 유동부채 200 — 세 회사가 모두 같다. 구성만 다르다.
COMPANIES = [
    {
        "name": "가온전기",
        "cash": 80,
        "short_term_funds": 40,
        "receivables": 120,
        "inventory": 40,
        "prepaid": 20,
        "current_liabilities": 200,
    },
    {
        "name": "두레물산",
        "cash": 20,
        "short_term_funds": 10,
        "receivables": 60,
        "inventory": 190,
        "prepaid": 20,
        "current_liabilities": 200,
    },
    {
        "name": "세움유통",
        "cash": 40,
        "short_term_funds": 30,
        "receivables": 100,
        "inventory": 110,
        "prepaid": 20,
        "current_liabilities": 200,
    },
]

ITEMS = ("cash", "short_term_funds", "receivables", "inventory", "prepaid")


def current_assets(company):
    return sum(company[item] for item in ITEMS)


def quick_assets(company):
    """당좌자산 = 유동자산 - 재고자산 (한국은행 703)."""
    return current_assets(company) - company["inventory"]


def ratios(company):
    liabilities = company["current_liabilities"]
    return {
        "current": current_assets(company) / liabilities * 100,
        "quick": quick_assets(company) / liabilities * 100,
        "cash": company["cash"] / liabilities * 100,
        # 선급비용은 현금으로 회수되지 않고 비용으로 대체되므로 빼 보는 민감도 계산이다.
        "quick_excluding_prepaid": (quick_assets(company) - company["prepaid"])
        / liabilities
        * 100,
    }


def print_composition():
    print("[1] 유동 항목 구성 — 합계와 유동부채는 세 회사가 같다 (억원)")
    print(
        pad("", 11)
        + pad("현금및현금성자산", 18, "right")
        + pad("단기금융상품", 14, "right")
        + pad("매출채권", 10, "right")
        + pad("재고자산", 10, "right")
        + pad("선급비용", 10, "right")
        + pad("유동자산", 10, "right")
        + pad("유동부채", 10, "right")
    )
    for company in COMPANIES:
        print(
            pad(company["name"], 11)
            + num(company["cash"], 0, 18)
            + num(company["short_term_funds"], 0, 14)
            + num(company["receivables"], 0, 10)
            + num(company["inventory"], 0, 10)
            + num(company["prepaid"], 0, 10)
            + num(current_assets(company), 0, 10)
            + num(company["current_liabilities"], 0, 10)
        )
    print()


def print_ratios():
    print("[2] 세 비율 — 분자를 어디까지 쓰는가 (%)")
    print(
        pad("", 11)
        + pad("유동비율", 12, "right")
        + pad("당좌비율", 12, "right")
        + pad("현금비율", 12, "right")
    )
    for company in COMPANIES:
        r = ratios(company)
        print(
            pad(company["name"], 11)
            + num(r["current"], 1, 12)
            + num(r["quick"], 1, 12)
            + num(r["cash"], 1, 12)
        )
    print()


def print_gap_identity():
    print("[3] 두 비율의 간격은 재고자산 ÷ 유동부채와 같다 (%p)")
    print(
        pad("", 11)
        + pad("유동비율-당좌비율", 20, "right")
        + pad("재고÷유동부채", 16, "right")
    )
    for company in COMPANIES:
        r = ratios(company)
        gap = r["current"] - r["quick"]
        inventory_share = (
            company["inventory"] / company["current_liabilities"] * 100
        )
        print(pad(company["name"], 11) + num(gap, 1, 20) + num(inventory_share, 1, 16))
    print()


def print_prepaid_sensitivity():
    print("[4] 선급비용까지 빼면 — 분자 정의가 바뀔 때의 민감도 (%)")
    print(
        pad("", 11)
        + pad("당좌비율", 12, "right")
        + pad("선급비용 제외", 16, "right")
        + pad("차이", 10, "right")
    )
    for company in COMPANIES:
        r = ratios(company)
        print(
            pad(company["name"], 11)
            + num(r["quick"], 1, 12)
            + num(r["quick_excluding_prepaid"], 1, 16)
            + num(r["quick_excluding_prepaid"] - r["quick"], 1, 10)
        )
    print()


def print_year_end_moves(amount=20):
    # 세 회사 모두 현금잔액이 이 금액 이상이어야 실제로 할 수 있는 거래다.
    assert all(company["cash"] >= amount for company in COMPANIES)

    print(f"[5] 기말에 현금 {amount}을 움직이면 — 같은 거래가 두 비율을 반대로 민다 (%)")
    print(
        pad("", 11)
        + pad("거래", 22)
        + pad("유동비율", 12, "right")
        + pad("당좌비율", 12, "right")
    )
    for company in COMPANIES:
        assets = current_assets(company)
        quick = quick_assets(company)
        liabilities = company["current_liabilities"]
        rows = [
            ("그대로", assets, quick, liabilities),
            (
                f"현금 {amount}으로 유동부채 상환",
                assets - amount,
                quick - amount,
                liabilities - amount,
            ),
            (
                f"단기차입 {amount} 일으킴",
                assets + amount,
                quick + amount,
                liabilities + amount,
            ),
        ]
        for label, a, q, l in rows:
            print(
                pad(company["name"] if label == "그대로" else "", 11)
                + pad(label, 22)
                + num(a / l * 100, 1, 12)
                + num(q / l * 100, 1, 12)
            )
    print()
    print("  상환은 분자가 분모보다 클 때만 비율을 올린다. 유동비율은 분자가 300,")
    print("  당좌비율은 분자가 당좌자산이므로 같은 상환이 서로 반대로 움직일 수 있다.")
    print()


def print_fire_sale(recovery=0.70):
    print(f"[6] 재고를 장부금액의 {recovery:.0%}에 처분하면 (%)")
    print(
        pad("", 11)
        + pad("유동비율", 12, "right")
        + pad("당좌비율", 12, "right")
        + pad("처분손실", 12, "right")
    )
    for company in COMPANIES:
        inventory = company["inventory"]
        liabilities = company["current_liabilities"]
        loss = inventory * (1 - recovery)
        assets_after = current_assets(company) - loss
        quick_after = quick_assets(company) + inventory * recovery
        print(
            pad(company["name"], 11)
            + num(assets_after / liabilities * 100, 1, 12)
            + num(quick_after / liabilities * 100, 1, 12)
            + num(loss, 1, 12)
        )
    print()
    print("  처분한 뒤에는 재고가 없으므로 두 비율이 같아진다.")
    print()


def main():
    print_composition()
    print_ratios()
    print_gap_identity()
    print_prepaid_sensitivity()
    print_year_end_moves()
    print_fire_sale()


if __name__ == "__main__":
    main()
