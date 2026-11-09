"""환불되지 않는 선수수수료(가입비)를 언제 수익으로 인식하는지 계산한다.

가상 회사 가나피트니스가 10월 1일에 회원 500명을 받는다. 금액 단위는 천원이다.
회계연도는 1~12월이다.
근거: 기업회계기준서 제1115호 문단 25·95·98·99, B19, B40, B48~B51.
"""

MEMBERS = 500
JOINING_FEE = 240.0          # 1인당 가입비 — 환불되지 않는다
MONTHLY_FEE = 100.0          # 1인당 월 회비
CONTRACT_MONTHS = 12         # 최초 계약기간
EXPECTED_MONTHS = 30         # 갱신을 포함한 예상 회원 기간 — 갱신 때 가입비를 다시 받지 않는다
START_MONTH = 10             # 1년차 10월 가입
SETUP_COST = 40.0            # 1인당 등록·회원카드 발급 등 준비 원가
SERVICE_COST_PER_MONTH = 60.0


def fmt(value):
    return f"{value:>10,.1f}"


def months_by_year(total_months):
    """가입 시점부터 total_months 동안 각 회계연도에 속하는 개월 수."""
    result = {}
    month, year, left = START_MONTH, 1, total_months
    while left > 0:
        in_year = min(13 - month, left)
        result[year] = in_year
        left -= in_year
        month, year = 1, year + 1
    return result


def spread(amount, total_months):
    # 기간에 걸쳐 고르게 이전되는 용역이라 경과 개월 수로 나눈다
    return {y: amount * m / total_months for y, m in months_by_year(total_months).items()}


def print_schedule(title, schedule, total):
    print(f"  {title}")
    balance = total
    for year in range(1, 5):
        recognised = schedule.get(year, 0.0)
        balance -= recognised
        print(f"    {year}년차 {fmt(recognised)}   연말 계약부채 {fmt(balance)}")


def main():
    fee_total = MEMBERS * JOINING_FEE
    print("[1] 받은 가입비")
    print(f"  {MEMBERS}명 × {JOINING_FEE:.0f} = {fee_total:,.1f} (10월 1일 현금 수취, 환불 없음)")
    print()

    print("[2] 가입비 수익 인식 — 세 가지 처리")
    print_schedule("(가) 받은 날 전액 수익 — 기준서가 허용하는 처리가 아니다 (B49)", {1: fee_total}, fee_total)
    print_schedule(f"(나) 최초 계약기간 {CONTRACT_MONTHS}개월에 나눔 — 갱신 선택권이 중요한 권리가 아닐 때 (B49)",
                   spread(fee_total, CONTRACT_MONTHS), fee_total)
    print_schedule(f"(다) 갱신 포함 예상 회원 기간 {EXPECTED_MONTHS}개월에 나눔 — 갱신 선택권이 중요한 권리일 때 (B40·B49)",
                   spread(fee_total, EXPECTED_MONTHS), fee_total)
    print()

    print("[3] 1년차 손익 — 가입비 처리별 (월 회비 3개월분은 같다)")
    monthly_revenue = MEMBERS * MONTHLY_FEE * months_by_year(CONTRACT_MONTHS)[1]
    service_cost = MEMBERS * SERVICE_COST_PER_MONTH * months_by_year(CONTRACT_MONTHS)[1]
    setup = MEMBERS * SETUP_COST
    print(f"    {'처리':<6}{'회비 수익':>10}{'가입비 수익':>10}{'용역 원가':>10}{'준비 원가':>10}{'이익':>10}")
    cases = [
        ("(가)", fee_total),
        ("(나)", spread(fee_total, CONTRACT_MONTHS)[1]),
        ("(다)", spread(fee_total, EXPECTED_MONTHS)[1]),
    ]
    for label, fee_rev in cases:
        profit = monthly_revenue + fee_rev - service_cost - setup
        print(f"    {label:<6}{fmt(monthly_revenue)}{fmt(fee_rev)}{fmt(service_cost)}{fmt(setup)}{fmt(profit)}")
    print("    준비 원가는 문단 98⑴ 일반관리원가로 보아 발생 시점에 비용으로 둔 경우다")
    print()

    print("[4] 준비 원가가 문단 95 요건을 충족한다고 볼 때 — 자산으로 두고 상각 (문단 99)")
    amort = spread(setup, EXPECTED_MONTHS)
    balance = setup
    for year in range(1, 5):
        balance -= amort.get(year, 0.0)
        print(f"    {year}년차 상각 {fmt(amort.get(year, 0.0))}   연말 자산 {fmt(balance)}")
    print()

    print("[5] 원가 기준 진행률에 준비 원가를 넣으면 — 최초 12개월 계약, 3개월 경과 시점 (B19·B51)")
    elapsed = months_by_year(CONTRACT_MONTHS)[1]
    service_to_date = SERVICE_COST_PER_MONTH * elapsed
    service_total = SERVICE_COST_PER_MONTH * CONTRACT_MONTHS
    wrong = (SETUP_COST + service_to_date) / (SETUP_COST + service_total)
    right = service_to_date / service_total
    print(f"    준비 원가 포함  ({SETUP_COST:.0f} + {service_to_date:.0f}) / ({SETUP_COST:.0f} + {service_total:.0f}) = {wrong:.1%}")
    print(f"    준비 원가 제외  {service_to_date:.0f} / {service_total:.0f} = {right:.1%}")
    contract_price = JOINING_FEE + MONTHLY_FEE * CONTRACT_MONTHS
    diff = MEMBERS * contract_price * (wrong - right)
    print(f"    계약 대가 1인당 {contract_price:.0f} 기준, 500명의 수익 차이 {diff:,.1f}")


if __name__ == "__main__":
    main()
