"""현금전환주기(CCC)를 가상 회사 네 곳으로 계산한다.

재고일수 + 매출채권 회수일수 - 매입채무 지급일수.
세 회전율의 분자는 한국은행 기업경영분석 807·809·810 을 따라 모두 매출액으로 둔다.
금액 단위는 억원이고, 잔액은 기초·기말 평균잔액이다.
"""

import unicodedata

DAYS_IN_YEAR = 365


def width(text):
    """한글은 두 칸을 차지하므로 출력 폭을 글자 수가 아니라 칸 수로 센다."""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def pad(text, columns, align="left"):
    gap = " " * max(0, columns - width(text))
    return text + gap if align == "left" else gap + text


def num(value, decimals=1, columns=9):
    return pad(f"{value:,.{decimals}f}", columns, "right")


# 가상 회사 네 곳. 실재하지 않는 이름이고 숫자도 계산 원리를 보이려고 만든 값이다.
# 매입 조건과 판매 조건만 다르게 두어 현금전환주기의 부호가 갈리도록 설계했다.
COMPANIES = [
    {
        "name": "바다중공업",
        "note": "주문 제작 설비. 재고를 오래 들고 가고 대금은 나중에 받는다",
        "sales": 1_200,
        "inventory": 300,
        "receivables": 250,
        "payables": 150,
        "contract_liabilities": 0,
    },
    {
        "name": "하늘식자재",
        "note": "식자재 도매. 재고 회전은 빠르지만 거래처에 외상을 준다",
        "sales": 2_000,
        "inventory": 120,
        "receivables": 180,
        "payables": 250,
        "contract_liabilities": 0,
    },
    {
        "name": "나래마트",
        "note": "소매 매장. 판 자리에서 대금을 받고 납품 대금은 뒤에 낸다",
        "sales": 3_000,
        "inventory": 250,
        "receivables": 20,
        "payables": 420,
        "contract_liabilities": 0,
    },
    {
        "name": "마루소프트",
        "note": "연간 구독. 재고가 없고 구독료를 미리 받는다",
        "sales": 600,
        "inventory": 0,
        "receivables": 50,
        "payables": 20,
        "contract_liabilities": 200,
    },
]


def metrics(company):
    """회전율·회전일수·현금전환주기를 한 번에 계산한다."""
    sales = company["sales"]
    daily_sales = sales / DAYS_IN_YEAR
    result = {"daily_sales": daily_sales}

    for key in ("inventory", "receivables", "payables", "contract_liabilities"):
        balance = company[key]
        result[key + "_turnover"] = sales / balance if balance else None
        result[key + "_days"] = balance / sales * DAYS_IN_YEAR

    result["operating_cycle"] = result["inventory_days"] + result["receivables_days"]
    result["ccc"] = result["operating_cycle"] - result["payables_days"]
    result["ccc_extended"] = result["ccc"] - result["contract_liabilities_days"]

    result["working_capital"] = (
        company["receivables"] + company["inventory"] - company["payables"]
    )
    result["working_capital_extended"] = (
        result["working_capital"] - company["contract_liabilities"]
    )
    return result


def print_balances():
    print("[1] 가상 회사 네 곳 — 매출액과 평균잔액 (억원)")
    print(
        pad("", 12)
        + pad("매출액", 10, "right")
        + pad("재고자산", 10, "right")
        + pad("매출채권", 10, "right")
        + pad("매입채무", 10, "right")
        + pad("계약부채", 10, "right")
    )
    for company in COMPANIES:
        print(
            pad(company["name"], 12)
            + num(company["sales"], 0, 10)
            + num(company["inventory"], 0, 10)
            + num(company["receivables"], 0, 10)
            + num(company["payables"], 0, 10)
            + num(company["contract_liabilities"], 0, 10)
        )
    print()
    for company in COMPANIES:
        print(f"  {company['name']} — {company['note']}")
    print()


def print_turnover(computed):
    print("[2] 회전율 (회) 과 회전일수 (일) — 분자는 셋 다 매출액")
    print(
        pad("", 12)
        + pad("재고", 20, "right")
        + pad("매출채권", 20, "right")
        + pad("매입채무", 20, "right")
    )
    print(
        pad("", 12)
        + pad("회전율", 10, "right")
        + pad("일수", 10, "right")
        + pad("회전율", 10, "right")
        + pad("일수", 10, "right")
        + pad("회전율", 10, "right")
        + pad("일수", 10, "right")
    )
    for company in COMPANIES:
        m = computed[company["name"]]
        inventory_turnover = (
            num(m["inventory_turnover"], 1, 10)
            if m["inventory_turnover"]
            else pad("-", 10, "right")
        )
        print(
            pad(company["name"], 12)
            + inventory_turnover
            + num(m["inventory_days"], 1, 10)
            + num(m["receivables_turnover"], 1, 10)
            + num(m["receivables_days"], 1, 10)
            + num(m["payables_turnover"], 1, 10)
            + num(m["payables_days"], 1, 10)
        )
    print()


def print_ccc(computed):
    print("[3] 현금전환주기와 영업에 묶인 운전자본")
    print(
        pad("", 12)
        + pad("영업주기", 11, "right")
        + pad("지급일수", 11, "right")
        + pad("CCC", 10, "right")
        + pad("하루매출", 11, "right")
        + pad("운전자본", 11, "right")
        + pad("CCC×하루매출", 15, "right")
    )
    for company in COMPANIES:
        m = computed[company["name"]]
        print(
            pad(company["name"], 12)
            + num(m["operating_cycle"], 1, 11)
            + num(m["payables_days"], 1, 11)
            + num(m["ccc"], 1, 10)
            + num(m["daily_sales"], 2, 11)
            + num(m["working_capital"], 1, 11)
            + num(m["ccc"] * m["daily_sales"], 1, 15)
        )
    print()
    print("  운전자본 = 매출채권 + 재고자산 - 매입채무. 마지막 두 칸이 같은지 본다.")
    print()


def print_contract_liabilities(computed):
    print("[4] 계약부채(선수금)를 넣으면 — 전통 산식에 잡히지 않는 자금")
    print(
        pad("", 12)
        + pad("계약부채일수", 15, "right")
        + pad("CCC", 10, "right")
        + pad("확장 CCC", 12, "right")
        + pad("운전자본", 11, "right")
        + pad("확장 운전자본", 16, "right")
    )
    for company in COMPANIES:
        m = computed[company["name"]]
        print(
            pad(company["name"], 12)
            + num(m["contract_liabilities_days"], 1, 15)
            + num(m["ccc"], 1, 10)
            + num(m["ccc_extended"], 1, 12)
            + num(m["working_capital"], 1, 11)
            + num(m["working_capital_extended"], 1, 16)
        )
    print()
    print("  확장 CCC = CCC - 계약부채일수. 확장 운전자본 = 운전자본 - 계약부채.")
    print()


def print_growth(computed, rates=(0.20, -0.20)):
    print("[5] 매출이 늘거나 줄 때 운전자본이 움직이는 금액 (회전일수는 그대로)")
    print("    운전자본 증감 = 확장 CCC x 하루매출 증감. 양수면 현금 유출이다.")
    print()
    header = pad("", 12) + pad("확장 CCC", 12, "right")
    for rate in rates:
        header += pad(f"매출 {rate:+.0%}", 16, "right")
    print(header)
    for company in COMPANIES:
        m = computed[company["name"]]
        row = pad(company["name"], 12) + num(m["ccc_extended"], 1, 12)
        for rate in rates:
            delta_daily = m["daily_sales"] * rate
            delta_wc = m["ccc_extended"] * delta_daily
            flow = "유출" if delta_wc > 0 else "유입"
            row += pad(f"{delta_wc:+,.1f} {flow}", 16, "right")
        print(row)
    print()


def print_receivables_to_payables(computed):
    print("[6] 매출채권 대 매입채무 (한국은행 712) — 기업간 신용의 방향")
    for company in COMPANIES:
        ratio = company["receivables"] / company["payables"] * 100
        direction = "받을 돈이 더 크다" if ratio > 100 else "낼 돈이 더 크다"
        print(
            pad("  " + company["name"], 14)
            + num(ratio, 1, 9)
            + "%   "
            + direction
        )
    print()


def main():
    computed = {company["name"]: metrics(company) for company in COMPANIES}
    print_balances()
    print_turnover(computed)
    print_ccc(computed)
    print_contract_liabilities(computed)
    print_growth(computed)
    print_receivables_to_payables(computed)


if __name__ == "__main__":
    main()
