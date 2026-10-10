"""K-IFRS 제1037호 충당부채의 인식과 측정을 가상 회사로 계산한다.

소송 하나의 인식 여부가 확률 50% 를 사이에 두고 갈리는 모습, 판매보증의 기댓값,
보증 비율 추정만 다른 두 회사의 연도별 비용과 부채 잔액, 먼 미래 지출의 현재가치와
할인 상각을 찍는다. 단위는 백만원. 회사와 숫자는 계산을 보이려고 만든 가상 자료다.
"""


def classify(probability, remote_threshold=0.05):
    """문단 14·23·27·28·86 — 가능성이 높으면 충당부채, 아니면 우발부채(공시), 희박하면 공시도 안 한다.

    '희박하다'의 수치 기준은 기준서에 없다. 여기서는 5% 미만으로 가정한다.
    """
    if probability > 0.5:
        return "충당부채 인식"
    if probability >= remote_threshold:
        return "우발부채 — 주석 공시만"
    return "가능성 희박 — 공시도 안 함"


def print_lawsuit():
    print("[1] 소송 1건, 지면 100 을 배상 — 패소 확률에 따른 처리 (문단 14·23·27·28·40)")
    print(f"  {'패소 확률':>8}  {'처리':<22}{'재무상태표 부채':>14}")
    for probability in (0.03, 0.30, 0.49, 0.51, 0.80):
        result = classify(probability)
        # 단일 의무는 가장 가능성이 높은 결과가 최선의 추정치가 될 수 있다 (문단 40)
        amount = 100 if result == "충당부채 인식" else 0
        print(f"  {probability:>8.0%}  {result:<22}{amount:>10}")
    print("  49% 와 51% 사이에서 부채가 0 에서 100 으로 바뀐다 — 확률을 곱한 49 나 51 로 잡지 않는다")
    print()


WARRANTY_OUTCOMES = [
    # (결과, 확률, 대당 수리비) — 문단 39 의 판매보증 예시와 같은 형태
    ("결함 없음", 0.80, 0),
    ("작은 결함", 0.15, 10),
    ("큰 결함", 0.05, 50),
]


def expected_cost(outcomes):
    return sum(probability * cost for _, probability, cost in outcomes)


def print_expected_value():
    print("[2] 판매보증 — 많은 항목이 걸린 의무는 기댓값으로 (문단 39)")
    for name, probability, cost in WARRANTY_OUTCOMES:
        print(f"  {name:<8} 확률 {probability:>4.0%}  대당 수리비 {cost:>3}  → {probability * cost:>4.1f}")
    per_unit = expected_cost(WARRANTY_OUTCOMES)
    print(f"  대당 기대 수리비 {per_unit:.1f}  → 1,000 대 판매 시 충당부채 {per_unit * 1000:,.0f}")
    print()
    return per_unit


UNITS_SOLD = [1000, 1000, 1000]
ACTUAL_COST_PER_UNIT = 4.0


def warranty_ledger(initial_estimate, revised_estimate):
    """보증기간 1년. t년 판매분의 수리비는 t+1년에 실제로 나간다고 가정한다.

    1년차 말에는 initial_estimate 로 설정하고, 2년차부터는 실제 경험을 반영해
    revised_estimate 로 바꾼다. 남은 잔액은 매 보고기간말에 다시 추정해 환입한다 (문단 59).
    """
    rows = []
    balance = 0.0
    for year, units in enumerate(UNITS_SOLD, start=1):
        opening = balance
        used = UNITS_SOLD[year - 2] * ACTUAL_COST_PER_UNIT if year >= 2 else 0.0
        # 지난해 판매분은 올해 수리가 끝났으므로 남은 잔액은 더 필요 없다
        reversal = opening - used
        estimate = initial_estimate if year == 1 else revised_estimate
        new_provision = units * estimate
        expense = new_provision - reversal
        balance = new_provision
        rows.append((year, opening, used, reversal, new_provision, expense, balance))
    return rows


def print_two_companies():
    print("[3] 같은 제품·같은 실제 수리비(대당 4), 1년차 추정만 다른 두 회사")
    print("    가나전자: 1년차부터 대당 4 로 추정  /  다라물산: 1년차 대당 6, 2년차부터 4 로 수정")
    totals = {}
    for company, initial in (("가나전자", 4.0), ("다라물산", 6.0)):
        print(f"  {company}")
        print(f"    {'연도':<5}{'기초 잔액':>9}{'사용':>8}{'환입':>8}{'신규 설정':>10}{'보증비용':>10}{'기말 잔액':>10}")
        rows = warranty_ledger(initial, ACTUAL_COST_PER_UNIT)
        for year, opening, used, reversal, new, expense, closing in rows:
            print(f"    {year}년차{opening:>10,.0f}{used:>10,.0f}{reversal:>10,.0f}"
                  f"{new:>11,.0f}{expense:>11,.0f}{closing:>11,.0f}")
        totals[company] = [row[5] for row in rows]
    print("  연도별 보증비용 차이 (다라물산 − 가나전자):",
          " / ".join(f"{year}년차 {b - a:+,.0f}" for year, (a, b)
                     in enumerate(zip(totals["가나전자"], totals["다라물산"]), start=1)))
    print(f"  3년 합계: 가나전자 {sum(totals['가나전자']):,.0f}, 다라물산 {sum(totals['다라물산']):,.0f}")
    print()


def print_discounting():
    print("[4] 5년 뒤 원상복구 1,000 — 현재가치로 측정하고 해마다 할인을 푼다 (문단 45·47·60)")
    amount, years, rate = 1000, 5, 0.05
    balance = amount / (1 + rate) ** years
    print(f"  할인율 {rate:.0%} 가정, 최초 인식액 {balance:,.2f}")
    print(f"  {'연도':<5}{'기초 잔액':>10}{'이자비용':>10}{'기말 잔액':>10}")
    for year in range(1, years + 1):
        interest = balance * rate
        print(f"  {year}년차{balance:>12,.2f}{interest:>10,.2f}{balance + interest:>12,.2f}")
        balance += interest
    print(f"  5년 동안의 이자비용 합계 {amount - amount / (1 + rate) ** years:,.2f} — 영업비용이 아니라 차입원가로 잡힌다")


def main():
    print_lawsuit()
    print_expected_value()
    print_two_companies()
    print_discounting()


if __name__ == "__main__":
    main()
