"""매출총이익률·영업이익률·순이익률을 가상 회사 세 곳으로 계산한다.

세 회사의 매출액 1,000과 영업이익 120을 같게 맞추고 그 위아래만 다르게 두었다.
한국은행 기업경영분석 610(매출액순이익률)·611(매출액영업이익률)·612(매출원가 대 매출액)와
609(매출액세전순이익률)의 산식을 쓴다. 매출총이익률은 이 지표 목록에 없으므로
매출총이익 ÷ 매출액으로 직접 계산하고, 612와 합이 100이 되는지 확인한다.
금액 단위는 억원이고 법인세비용은 세전순이익의 22%로 가정했다.
"""

import unicodedata

TAX_RATE = 0.22


def width(text):
    """한글은 두 칸을 차지하므로 출력 폭을 글자 수가 아니라 칸 수로 센다."""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def pad(text, columns, align="left"):
    gap = " " * max(0, columns - width(text))
    return text + gap if align == "left" else gap + text


def num(value, decimals=1, columns=9):
    return pad(f"{value:,.{decimals}f}", columns, "right")


def signed(value, decimals=1, columns=9):
    return pad(f"{value:+,.{decimals}f}", columns, "right")


# 매출액 1,000과 영업이익 120은 세 회사가 같다. 원가 구조와 영업외수지만 다르다.
COMPANIES = [
    {
        "name": "한결정밀",
        "note": "자체 설계 장비",
        "sales": 1000,
        "cost_of_sales": 550,
        "sga": 330,
        "non_operating_income": 10,
        "non_operating_expenses": 30,
    },
    {
        "name": "마루유통",
        "note": "소매 유통",
        "sales": 1000,
        "cost_of_sales": 820,
        "sga": 60,
        "non_operating_income": 5,
        "non_operating_expenses": 15,
    },
    {
        "name": "벼리소재",
        "note": "차입 설비 투자",
        "sales": 1000,
        "cost_of_sales": 700,
        "sga": 180,
        "non_operating_income": 2,
        "non_operating_expenses": 72,
    },
]


def statement(company):
    """손익계산서를 매출액부터 당기순이익까지 단계별로 계산한다."""
    sales = company["sales"]
    gross = sales - company["cost_of_sales"]
    operating = gross - company["sga"]
    net_non_operating = (
        company["non_operating_income"] - company["non_operating_expenses"]
    )
    pretax = operating + net_non_operating
    tax = pretax * TAX_RATE
    return {
        "sales": sales,
        "cost_of_sales": company["cost_of_sales"],
        "gross": gross,
        "sga": company["sga"],
        "operating": operating,
        "net_non_operating": net_non_operating,
        "pretax": pretax,
        "tax": tax,
        "net": pretax - tax,
    }


def margins(company):
    s = statement(company)
    sales = s["sales"]
    return {
        "gross": s["gross"] / sales * 100,
        "operating": s["operating"] / sales * 100,
        "pretax": s["pretax"] / sales * 100,
        "net": s["net"] / sales * 100,
        "cost_to_sales": s["cost_of_sales"] / sales * 100,
        "net_non_operating": s["net_non_operating"] / sales * 100,
    }


def print_statements():
    print("[1] 손익계산서 — 매출액과 영업이익은 세 회사가 같다 (억원)")
    print(
        pad("", 11)
        + pad("매출액", 10, "right")
        + pad("매출원가", 10, "right")
        + pad("매출총이익", 12, "right")
        + pad("판관비", 10, "right")
        + pad("영업이익", 10, "right")
        + pad("영업외수지", 12, "right")
        + pad("세전순이익", 12, "right")
        + pad("법인세", 10, "right")
        + pad("당기순이익", 12, "right")
    )
    for company in COMPANIES:
        s = statement(company)
        print(
            pad(company["name"], 11)
            + num(s["sales"], 0, 10)
            + num(s["cost_of_sales"], 0, 10)
            + num(s["gross"], 0, 12)
            + num(s["sga"], 0, 10)
            + num(s["operating"], 0, 10)
            + signed(s["net_non_operating"], 0, 12)
            + num(s["pretax"], 0, 12)
            + num(s["tax"], 1, 10)
            + num(s["net"], 1, 12)
        )
    print()


def print_margins():
    print("[2] 세 마진 — 영업이익률만 보면 셋이 같다 (%)")
    print(
        pad("", 11)
        + pad("매출총이익률", 14, "right")
        + pad("영업이익률", 12, "right")
        + pad("세전순이익률", 14, "right")
        + pad("순이익률", 10, "right")
    )
    for company in COMPANIES:
        m = margins(company)
        print(
            pad(company["name"], 11)
            + num(m["gross"], 1, 14)
            + num(m["operating"], 1, 12)
            + num(m["pretax"], 1, 14)
            + num(m["net"], 1, 10)
        )
    print()


def print_cost_identity():
    print("[3] 매출총이익률 + 매출원가 대 매출액 = 100 (%)")
    print(
        pad("", 11)
        + pad("매출총이익률", 14, "right")
        + pad("매출원가 대 매출액", 20, "right")
        + pad("합", 8, "right")
    )
    for company in COMPANIES:
        m = margins(company)
        print(
            pad(company["name"], 11)
            + num(m["gross"], 1, 14)
            + num(m["cost_to_sales"], 1, 20)
            + num(m["gross"] + m["cost_to_sales"], 1, 8)
        )
    print()


def print_waterfall():
    print("[4] 매출액을 100으로 놓고 단계마다 빠지는 몫 (%p)")
    print(
        pad("", 11)
        + pad("매출원가", 10, "right")
        + pad("판관비", 10, "right")
        + pad("영업외수지", 12, "right")
        + pad("법인세", 10, "right")
        + pad("남는 몫", 10, "right")
    )
    for company in COMPANIES:
        s = statement(company)
        sales = s["sales"]
        print(
            pad(company["name"], 11)
            + signed(-s["cost_of_sales"] / sales * 100, 1, 10)
            + signed(-s["sga"] / sales * 100, 1, 10)
            + signed(s["net_non_operating"] / sales * 100, 1, 12)
            + signed(-s["tax"] / sales * 100, 1, 10)
            + num(s["net"] / sales * 100, 1, 10)
        )
    print()
    print("  빠지는 네 몫의 크기가 회사마다 다르고, 큰 쪽이 어디냐가 업종을 가른다.")
    print()


def print_pretax_identity():
    print("[5] 매출액세전순이익률 = 매출액영업이익률 + 영업외수지 ÷ 매출액 (%)")
    print(
        pad("", 11)
        + pad("영업이익률(A)", 16, "right")
        + pad("영업외수지÷매출액(B)", 24, "right")
        + pad("A+B", 10, "right")
        + pad("세전순이익률", 14, "right")
    )
    for company in COMPANIES:
        m = margins(company)
        print(
            pad(company["name"], 11)
            + num(m["operating"], 1, 16)
            + signed(m["net_non_operating"], 1, 24)
            + num(m["operating"] + m["net_non_operating"], 1, 10)
            + num(m["pretax"], 1, 14)
        )
    print()


def print_reclassification(company_name="한결정밀", amount=50):
    """판관비에 있던 물류비를 매출원가로 옮겨 본다. 영업이익은 움직이지 않는다."""
    company = next(c for c in COMPANIES if c["name"] == company_name)
    moved = dict(company)
    moved["cost_of_sales"] = company["cost_of_sales"] + amount
    moved["sga"] = company["sga"] - amount
    assert moved["sga"] >= 0

    print(f"[6] {company_name}이 물류비 {amount}을 판관비에서 매출원가로 옮기면 (%)")
    print(
        pad("", 16)
        + pad("매출총이익률", 14, "right")
        + pad("영업이익률", 12, "right")
        + pad("순이익률", 10, "right")
    )
    for label, target in (("옮기기 전", company), ("옮긴 뒤", moved)):
        m = margins(target)
        print(
            pad(label, 16)
            + num(m["gross"], 1, 14)
            + num(m["operating"], 1, 12)
            + num(m["net"], 1, 10)
        )
    before, after = margins(company), margins(moved)
    print(
        pad("차이", 16)
        + signed(after["gross"] - before["gross"], 1, 14)
        + signed(after["operating"] - before["operating"], 1, 12)
        + signed(after["net"] - before["net"], 1, 10)
    )
    print()
    print("  같은 비용을 어느 칸에 담느냐만 바뀌었는데 매출총이익률은 움직인다.")
    print("  영업이익은 두 칸을 모두 뺀 뒤의 금액이므로 분류 선택의 영향을 받지 않는다.")
    print()


def main():
    print_statements()
    print_margins()
    print_cost_identity()
    print_waterfall()
    print_pretax_identity()
    print_reclassification()


if __name__ == "__main__":
    main()
