"""어디까지가 현금인가 — 현금및현금성자산과 단기금융상품.

K-IFRS 제1007호 '현금흐름표' 문단 6~9·45·48 과 제1001호 '재무제표 표시'
문단 54(i)·55·66(d) 를 근거로, 같은 금액의 여유자금을 다르게 굴린 가상 두 회사의
재무상태표 표시와 현금비율, 현금흐름표 기말 현금을 계산한다.

회사와 금액은 전부 가상이다. 금액 단위는 백만원.
"""

# 기말 현재 두 회사가 들고 있는 자금. 총액 450 으로 같고 넣어 둔 자리만 다르다.
#   (이름, 금액, 취득일로부터 만기 개월수 또는 None=요구불, 가치변동위험 경미 여부)
HOLDINGS = {
    "가나전자": [
        ("보통예금", 200, None, True),
        ("수시입출금 MMF", 150, None, True),
        ("정기예금 (취득 시 만기 2개월)", 100, 2, True),
    ],
    "다라물산": [
        ("보통예금", 200, None, True),
        ("정기예금 (취득 시 만기 6개월)", 250, 6, True),
    ],
}

# 두 회사가 들고 있지는 않지만 분류가 갈리는 자리를 보이려고 따로 둔 사례.
#   (이름, 만기 개월수 또는 None=요구불, 가치변동위험 경미 여부, 지분상품 여부)
EDGE_CASES = [
    ("보통예금", None, True, False),
    ("상장주식 — 단기 운용 목적", None, False, True),
    ("취득 시 상환일이 두 달 남았던 상환우선주", 2, True, True),
    ("정기예금 — 취득 시 만기 2개월", 2, True, False),
    ("정기예금 — 취득 시 만기 12개월, 잔존 2개월", 12, True, False),
    ("정기예금 — 취득 시 만기 18개월", 18, True, False),
]

# 두 회사의 나머지 전제는 같게 두어, 배치 차이만 비율에 나타나게 한다.
CURRENT_LIABILITIES = 500
OTHER_QUICK_ASSETS = 300  # 매출채권 등. 당좌자산에는 들어가고 현금에는 안 들어간다.

# 가나전자가 제삼자와의 계약으로 지정 목적에만 쓰기로 한 요구불예금.
# 인출 자체는 막혀 있지 않다 (IFRS 해석위원회 2022년 4월 결정의 사실관계).
RESTRICTED_DEMAND_DEPOSIT = 80

# 기초 잔액과 당기 영업활동 현금흐름. 두 회사가 같다.
OPENING_CASH_AND_EQUIVALENTS = 380
OPERATING_CASH_FLOW = 70


def classify(months_to_maturity, low_risk, is_equity=False):
    """문단 6~7 의 요건을 묻는 순서 그대로 본다.

    세 가지를 차례로 본다. 요구불인가, 지분상품인가, 취득일로부터 만기가 짧은가.
    3개월은 문단 7 이 드는 '예를 들어'이지 그 자체가 규칙은 아니다.
    여기서는 그 예시를 기준선으로 삼아 분류한다.
    """
    if months_to_maturity is None and not is_equity:
        return "현금및현금성자산", "요구불예금은 현금의 정의에 바로 든다 (문단 6)"
    if is_equity and months_to_maturity is None:
        return "현금및현금성자산 아님", "상환일이 없는 지분상품은 제외 (문단 7)"
    if not low_risk:
        return "현금및현금성자산 아님", "가치변동 위험이 경미하지 않음 (문단 6)"
    if months_to_maturity <= 3:
        reason = "취득일로부터 만기 3개월 이내 (문단 7 예시)"
        if is_equity:
            reason = "상환일까지 기간이 단기인 우선주 — 문단 7 의 예외"
        return "현금및현금성자산", reason
    if months_to_maturity <= 12:
        return "단기금융상품", "취득일 기준 만기 3개월 초과 (문단 7·55)"
    return "장기금융상품", "보고기간 후 12개월 이후 만기 (문단 66)"


def split(holdings):
    """회사별로 표시 항목별 합계를 낸다."""
    buckets = {}
    for name, amount, months, low_risk in holdings:
        label, _ = classify(months, low_risk)
        buckets[label] = buckets.get(label, 0) + amount
    return buckets


def fmt(value):
    return f"{value:,.0f}"


def section_1():
    print("[1] 분류가 갈리는 자리 — 문단 6~7 의 요건을 순서대로 묻는다")
    for name, months, low_risk, is_equity in EDGE_CASES:
        label, reason = classify(months, low_risk, is_equity)
        print(f"    {name:<34}{label:<16}{reason}")
    print("    잔존 만기가 2개월로 같아도 취득 시 만기가 다르면 분류가 갈린다.")
    print()

    print("[2] 두 회사가 들고 있는 자금 (단위: 백만원)")
    for company, holdings in HOLDINGS.items():
        print(f"    {company}")
        for name, amount, months, low_risk in holdings:
            label, _ = classify(months, low_risk)
            print(f"      {name:<30}{fmt(amount):>6}  {label}")
    print()


def section_2():
    print("[3] 재무상태표 표시와 현금비율 — 총액은 같고 자리만 다르다")
    print(f"    {'':<10}{'현금및현금성자산':>14}{'단기금융상품':>12}{'자금 합계':>10}"
          f"{'유동부채':>9}{'현금비율':>9}{'당좌비율':>9}")
    for company, holdings in HOLDINGS.items():
        buckets = split(holdings)
        cash = buckets.get("현금및현금성자산", 0)
        short_term = buckets.get("단기금융상품", 0)
        total = cash + short_term
        cash_ratio = cash / CURRENT_LIABILITIES * 100
        quick = (cash + short_term + OTHER_QUICK_ASSETS) / CURRENT_LIABILITIES * 100
        print(f"    {company:<10}{fmt(cash):>14}{fmt(short_term):>12}{fmt(total):>10}"
              f"{fmt(CURRENT_LIABILITIES):>9}{cash_ratio:>8.1f}%{quick:>8.1f}%")
    print("    두 회사가 쥔 돈은 450 으로 같지만 현금비율은 갈린다.")
    print("    매출채권까지 넣는 당좌비율에서는 단기금융상품도 분자에 들어가 차이가 사라진다.")
    print()


def section_3():
    print("[4] 사용이 제한된 요구불예금 — 현금에서 빼지 않고 공시한다 (문단 48)")
    cash = split(HOLDINGS["가나전자"]).get("현금및현금성자산", 0)
    free = cash - RESTRICTED_DEMAND_DEPOSIT
    print(f"    가나전자 현금및현금성자산          {fmt(cash):>6}")
    print(f"      그중 지정 목적에만 쓸 수 있는 요구불예금  {fmt(RESTRICTED_DEMAND_DEPOSIT):>6}")
    print(f"      제약 없이 쓸 수 있는 금액             {fmt(free):>6}")
    print(f"    현금비율  표시된 금액 기준 {cash / CURRENT_LIABILITIES * 100:.1f}%"
          f"  →  제약을 뺀 금액 기준 {free / CURRENT_LIABILITIES * 100:.1f}%")
    print("    인출이 막힌 것이 아니므로 현금의 정의는 그대로 충족한다.")
    print("    표시 금액은 450 이고, 줄어드는 것은 본문이 아니라 읽는 사람의 해석이다.")
    print()


def section_4():
    print("[5] 같은 영업성과, 다른 기말 현금 — 현금성자산 밖으로 옮기면 투자활동이다")
    print(f"    두 회사 모두 기초 현금및현금성자산 {fmt(OPENING_CASH_AND_EQUIVALENTS)},"
          f" 영업활동 현금흐름 +{fmt(OPERATING_CASH_FLOW)}")
    print(f"    {'':<10}{'기초':>8}{'영업활동':>10}{'투자활동':>10}{'기말':>8}{'증감':>8}")
    for company, holdings in HOLDINGS.items():
        short_term = split(holdings).get("단기금융상품", 0)
        # 3개월 초과 예금에 넣은 금액은 현금및현금성자산 밖으로 나간 것이므로
        # 투자활동 현금유출이 된다 (문단 9 의 반대 경우).
        investing = -short_term
        closing = OPENING_CASH_AND_EQUIVALENTS + OPERATING_CASH_FLOW + investing
        change = closing - OPENING_CASH_AND_EQUIVALENTS
        print(f"    {company:<10}{fmt(OPENING_CASH_AND_EQUIVALENTS):>8}"
              f"{'+' + fmt(OPERATING_CASH_FLOW):>10}{fmt(investing):>10}"
              f"{fmt(closing):>8}{('+' if change >= 0 else '') + fmt(change):>8}")
    print("    다라물산의 현금은 180 줄었지만 벌어들인 현금은 가나전자와 같다.")
    print("    현금및현금성자산 안에서 옮긴 가나전자의 MMF·2개월 예금은 현금흐름이 아니다 (문단 9).")
    print()


def section_5():
    print("[6] 현금흐름표 기말 현금과 재무상태표의 조정 (문단 45)")
    # 당좌차월이 현금관리의 일부인 경우 현금및현금성자산의 구성요소에 든다 (문단 8).
    overdraft = 30
    cash = split(HOLDINGS["다라물산"]).get("현금및현금성자산", 0)
    short_term = split(HOLDINGS["다라물산"]).get("단기금융상품", 0)
    print("    다라물산이 즉시 상환 의무가 붙은 당좌차월 30 을 현금관리에 쓴다고 하면")
    print(f"      재무상태표 현금및현금성자산 (자산)        {fmt(cash):>6}")
    print(f"      재무상태표 단기차입금 중 당좌차월 (부채)   {fmt(-overdraft):>6}")
    print(f"      현금흐름표 기말 현금및현금성자산          {fmt(cash - overdraft):>6}")
    print(f"      (단기금융상품 {fmt(short_term)} 은 어느 쪽에도 들지 않는다)")
    print("    자산 한 줄만 보고 현금흐름표 기말 현금과 맞춰 보면 30 이 어긋난다.")
    print("    그 차이를 메우는 것이 문단 45 가 요구하는 조정 공시다.")
    print()


def main():
    print("어디까지가 현금인가 — 가상 회사 가나전자·다라물산 (단위: 백만원)")
    print("K-IFRS 제1007호 문단 6~9·45·48, 제1001호 문단 54(i)·55·66(d)")
    print()
    section_1()
    section_2()
    section_3()
    section_4()
    section_5()


if __name__ == "__main__":
    main()
