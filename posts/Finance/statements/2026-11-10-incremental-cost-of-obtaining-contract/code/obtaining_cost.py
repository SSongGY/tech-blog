"""계약체결 증분원가(영업 수수료)를 언제 비용으로 인식하는지 계산한다.

가상 회사 가나클라우드는 기업 고객에게 1년 단위 구독 계약을 판다. 금액 단위는 천원이다.
계약은 모두 1월 1일에 맺는다고 단순화한다. 회계연도는 1~12월이다.
근거: 기업회계기준서 제1115호 문단 91~94, 99~100.
"""

ANNUAL_FEE = 1_200.0      # 고객 1곳당 연 구독료
COMMISSION = 300.0        # 신규 계약 1건당 영업 수수료 — 계약을 맺어야만 지급한다
EXPECTED_YEARS = 4        # 갱신을 포함해 고객이 머물 것으로 예상하는 기간 (과거 경험에서 추정한 가정)

# 계약 체결 전후에 든 원가와, 계약을 맺지 않았어도 들었을지 여부 (문단 92·93)
COSTS = [
    ("영업 수수료 (체결 시 지급)", 300.0, True),
    ("제안서 작성 외부 자문료", 40.0, False),
    ("고객 방문 출장비", 25.0, False),
    ("영업팀 기본급 배분액", 120.0, False),
]

NEW_CUSTOMERS = {1: 200, 2: 300, 3: 450, 4: 450}   # 연도별 신규 고객 수 — 성장기를 가정


def fmt(value):
    return f"{value:>10,.1f}"


def amortise(amount, years, start_year):
    # 구독 용역이 기간에 걸쳐 고르게 이전되므로 상각도 정액이다 (문단 99)
    return {start_year + i: amount / years for i in range(years)}


def main():
    print("[1] 계약 1건에 든 원가 — 증분원가인가 (문단 92·93)")
    print(f"    {'항목':<22}{'금액':>8}  처리")
    for name, amount, incremental in COSTS:
        verdict = "자산 후보 (증분원가)" if incremental else "발생 시점 비용 (계약 체결과 무관)"
        print(f"    {name:<22}{amount:>8,.1f}  {verdict}")
    print()

    print("[2] 상각기간이 정하는 처리 — 고객 1곳")
    for label, years in [("갱신 예상 없음", 1), ("갱신 포함 예상 기간", EXPECTED_YEARS)]:
        expedient = "간편법 가능 (문단 94)" if years <= 1 else "간편법 불가 — 자산으로 두고 상각"
        print(f"    {label:<14} 상각기간 {years}년  → {expedient}")
    print()

    print(f"[3] 고객 1곳의 수수료 {COMMISSION:.0f} — 상각기간 {EXPECTED_YEARS}년 (문단 91·99)")
    schedule = amortise(COMMISSION, EXPECTED_YEARS, 1)
    balance = COMMISSION
    for year in range(1, EXPECTED_YEARS + 1):
        balance -= schedule[year]
        print(f"    {year}년차 상각 {fmt(schedule[year])}   연말 자산 {fmt(balance)}")
    print()

    print("[4] 성장기 4년 — 수수료를 즉시 비용으로 둘 때와 자산으로 상각할 때")
    print(f"    {'연도':<4}{'신규':>6}{'고객 수':>7}{'구독 수익':>10}{'즉시 비용':>10}{'상각비':>10}{'연말 자산':>10}")
    expense_by_year = {}
    for start, count in NEW_CUSTOMERS.items():
        for year, amount in amortise(COMMISSION * count, EXPECTED_YEARS, start).items():
            expense_by_year[year] = expense_by_year.get(year, 0.0) + amount
    paid_total = 0.0
    customers = 0
    for year, count in NEW_CUSTOMERS.items():
        customers += count          # 예상대로 이탈 없이 머문다고 가정
        paid = COMMISSION * count
        paid_total += paid
        amortised_to_date = sum(v for y, v in expense_by_year.items() if y <= year)
        print(f"    {year}년차{count:>6}{customers:>8} {fmt(ANNUAL_FEE * customers):>12} "
              f"{fmt(paid):>12} {fmt(expense_by_year[year]):>12} {fmt(paid_total - amortised_to_date):>12}")
    print()

    print("[5] 같은 4년의 수수료 비용 합계")
    print(f"    즉시 비용 {paid_total:,.1f}   상각비 {sum(expense_by_year[y] for y in NEW_CUSTOMERS):,.1f}"
          f"   차이(4년차 말 자산) {paid_total - sum(expense_by_year[y] for y in NEW_CUSTOMERS):,.1f}")


if __name__ == "__main__":
    main()
