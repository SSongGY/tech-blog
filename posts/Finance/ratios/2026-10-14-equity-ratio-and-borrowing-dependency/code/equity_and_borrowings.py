"""자기자본비율·부채비율·차입금의존도를 가상 회사 세 곳으로 계산한다.

세 회사의 총자본 1,000과 매출액 1,200, 영업이익 120을 같게 맞추고
부채의 구성만 다르게 두었다. 한국은행 기업경영분석 701(자기자본비율)·
707(부채비율)·710(차입금의존도)·629(이자보상비율)·625(차입금평균이자율)·
627(금융비용 대 매출액)·801(총자산회전율)의 산식을 쓴다.
금액 단위는 억원이고 차입금평균이자율은 연 5.0%로 가정했다.
"""

import unicodedata

INTEREST_RATE = 0.05


def width(text):
    """한글은 두 칸을 차지하므로 출력 폭을 글자 수가 아니라 칸 수로 센다."""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def pad(text, columns, align="left"):
    gap = " " * max(0, columns - width(text))
    return text + gap if align == "left" else gap + text


def num(value, decimals=1, columns=9):
    return pad(f"{value:,.{decimals}f}", columns, "right")


# 총자본 1,000 · 매출액 1,200 · 영업이익 120 은 세 회사가 같다. 부채 구성만 다르다.
COMPANIES = [
    {
        "name": "나루정밀",
        "equity": 400,
        "payables": 450,          # 매입채무·미지급금 등 이자를 부담하지 않는 부채
        "short_term_debt": 80,
        "long_term_debt": 70,
        "bonds": 0,
        "sales": 1200,
        "operating_income": 120,
    },
    {
        "name": "들샘산업",
        "equity": 400,
        "payables": 80,
        "short_term_debt": 200,
        "long_term_debt": 220,
        "bonds": 100,
        "sales": 1200,
        "operating_income": 120,
    },
    {
        "name": "솔터물산",
        "equity": 250,
        "payables": 600,
        "short_term_debt": 90,
        "long_term_debt": 60,
        "bonds": 0,
        "sales": 1200,
        "operating_income": 120,
    },
]


def borrowings(company):
    """차입금 = 장단기차입금 + 회사채 (한국은행 710의 분자)."""
    return company["short_term_debt"] + company["long_term_debt"] + company["bonds"]


def liabilities(company):
    return company["payables"] + borrowings(company)


def total_capital(company):
    """총자본 = 자기자본 + 타인자본. 총자산과 같은 금액이다."""
    return company["equity"] + liabilities(company)


def indicators(company):
    capital = total_capital(company)
    interest = borrowings(company) * INTEREST_RATE
    return {
        "equity_ratio": company["equity"] / capital * 100,
        "debt_ratio": liabilities(company) / company["equity"] * 100,
        "borrowing_dependency": borrowings(company) / capital * 100,
        "interest": interest,
        "interest_coverage": company["operating_income"] / interest * 100,
        "interest_to_sales": interest / company["sales"] * 100,
        "asset_turnover": company["sales"] / capital,
    }


def print_composition():
    print("[1] 총자본의 구성 — 총자본 1,000은 세 회사가 같다 (억원)")
    print(
        pad("", 11)
        + pad("자기자본", 10, "right")
        + pad("매입채무 등", 13, "right")
        + pad("단기차입금", 12, "right")
        + pad("장기차입금", 12, "right")
        + pad("회사채", 9, "right")
        + pad("차입금 계", 11, "right")
        + pad("부채총계", 10, "right")
        + pad("총자본", 9, "right")
    )
    for company in COMPANIES:
        print(
            pad(company["name"], 11)
            + num(company["equity"], 0, 10)
            + num(company["payables"], 0, 13)
            + num(company["short_term_debt"], 0, 12)
            + num(company["long_term_debt"], 0, 12)
            + num(company["bonds"], 0, 9)
            + num(borrowings(company), 0, 11)
            + num(liabilities(company), 0, 10)
            + num(total_capital(company), 0, 9)
        )
    print()


def print_indicators():
    print("[2] 세 지표 — 같은 부채총계가 다르게 읽힌다 (%)")
    print(
        pad("", 11)
        + pad("자기자본비율", 14, "right")
        + pad("부채비율", 10, "right")
        + pad("차입금의존도", 14, "right")
    )
    for company in COMPANIES:
        i = indicators(company)
        print(
            pad(company["name"], 11)
            + num(i["equity_ratio"], 1, 14)
            + num(i["debt_ratio"], 1, 10)
            + num(i["borrowing_dependency"], 1, 14)
        )
    print()


def print_equivalence():
    print("[3] 자기자본비율과 부채비율은 같은 정보다 (%)")
    print(
        pad("", 11)
        + pad("자기자본비율", 14, "right")
        + pad("환산한 부채비율", 18, "right")
        + pad("실제 부채비율", 16, "right")
    )
    for company in COMPANIES:
        i = indicators(company)
        # 자산 = 부채 + 자본이므로 부채비율 = (100 / 자기자본비율 - 1) x 100 이다.
        converted = (100 / i["equity_ratio"] - 1) * 100
        print(
            pad(company["name"], 11)
            + num(i["equity_ratio"], 1, 14)
            + num(converted, 1, 18)
            + num(i["debt_ratio"], 1, 16)
        )
    print()
    print("  한쪽을 알면 다른 쪽이 나온다. 차입금의존도는 이 식에서 나오지 않는다.")
    print()


def print_interest_burden():
    print(f"[4] 차입금에 연 {INTEREST_RATE:.1%} 이자가 붙으면 (억원, %)")
    print(
        pad("", 11)
        + pad("차입금", 9, "right")
        + pad("이자비용", 10, "right")
        + pad("영업이익", 10, "right")
        + pad("이자보상비율", 14, "right")
    )
    for company in COMPANIES:
        i = indicators(company)
        print(
            pad(company["name"], 11)
            + num(borrowings(company), 0, 9)
            + num(i["interest"], 1, 10)
            + num(company["operating_income"], 0, 10)
            + num(i["interest_coverage"], 1, 14)
        )
    print()


def print_decomposition():
    print("[5] 금융비용 대 매출액 = 차입금평균이자율 × 차입금의존도 ÷ 총자산회전율 (%)")
    print(
        pad("", 11)
        + pad("차입금평균이자율", 18, "right")
        + pad("차입금의존도", 14, "right")
        + pad("총자산회전율", 14, "right")
        + pad("세 값의 곱", 12, "right")
        + pad("직접 계산", 11, "right")
    )
    for company in COMPANIES:
        i = indicators(company)
        product = (
            INTEREST_RATE * 100 * i["borrowing_dependency"] / 100 / i["asset_turnover"]
        )
        print(
            pad(company["name"], 11)
            + num(INTEREST_RATE * 100, 1, 18)
            + num(i["borrowing_dependency"], 1, 14)
            + num(i["asset_turnover"], 2, 14)
            + num(product, 3, 12)
            + num(i["interest_to_sales"], 3, 11)
        )
    print()


def print_swap(company_name="나루정밀", amount=100):
    """매입채무를 단기차입금으로 바꾼다. 부채총계는 그대로고 이자부부채만 늘어난다."""
    company = next(c for c in COMPANIES if c["name"] == company_name)
    swapped = dict(company)
    swapped["payables"] = company["payables"] - amount
    swapped["short_term_debt"] = company["short_term_debt"] + amount
    assert swapped["payables"] >= 0
    assert liabilities(swapped) == liabilities(company)

    print(f"[6] {company_name}이 매입채무 {amount}을 단기차입금으로 바꾸면")
    print(
        pad("", 14)
        + pad("부채총계", 10, "right")
        + pad("자기자본비율", 14, "right")
        + pad("부채비율", 10, "right")
        + pad("차입금의존도", 14, "right")
        + pad("이자비용", 10, "right")
        + pad("이자보상비율", 14, "right")
    )
    for label, target in (("바꾸기 전", company), ("바꾼 뒤", swapped)):
        i = indicators(target)
        print(
            pad(label, 14)
            + num(liabilities(target), 0, 10)
            + num(i["equity_ratio"], 1, 14)
            + num(i["debt_ratio"], 1, 10)
            + num(i["borrowing_dependency"], 1, 14)
            + num(i["interest"], 1, 10)
            + num(i["interest_coverage"], 1, 14)
        )
    print()
    print("  부채총계가 그대로라 앞의 두 지표는 움직이지 않는다.")
    print("  이자를 부담하는 부채만 늘었으므로 차입금의존도와 이자비용이 올라간다.")
    print()


def main():
    print_composition()
    print_indicators()
    print_equivalence()
    print_interest_burden()
    print_decomposition()
    print_swap()


if __name__ == "__main__":
    main()
