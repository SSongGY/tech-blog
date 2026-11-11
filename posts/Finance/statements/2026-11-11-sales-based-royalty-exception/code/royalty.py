"""판매기준 로열티가 언제 수익이 되는지 계산한다.

가상 회사 가나라이선싱은 지적재산 라이선스를 팔고 고정 계약금과 판매기준 로열티를 함께 받는다.
금액 단위는 백만원이다. 회계연도는 1~12월이다.
근거: 기업회계기준서 제1115호 문단 B63~B63B, 50~59.
"""

ROYALTY_RATE = 0.05           # 고객 매출액의 5%
YEARS = [1, 2, 3]

# 고객(라이선시)의 연도별 실제 매출. 계약 시점에는 알 수 없다.
LICENSEE_SALES = {1: 4_000.0, 2: 10_000.0, 3: 6_000.0}

# 계약 시점에 기업이 세운 3년 누적 고객 매출 시나리오와 확률 (가정)
SCENARIOS = [(12_000.0, 0.3), (20_000.0, 0.5), (30_000.0, 0.2)]


def fmt(value):
    return f"{value:>9,.1f}"


def actual_royalty():
    return {y: LICENSEE_SALES[y] * ROYALTY_RATE for y in YEARS}


def case_use_right(fixed_fee):
    """사용권: 고정 계약금은 이전 시점(1년차)에, 로열티는 고객 매출이 일어날 때 (B61, B63)."""
    royalty = actual_royalty()
    return {y: (fixed_fee if y == 1 else 0.0) + royalty[y] for y in YEARS}


def case_access_right(fixed_fee):
    """접근권 3년: 고정 계약금은 기간에 걸쳐, 로열티는 고객 매출이 일어날 때 (B60, B63).

    로열티가 배분된 수행의무가 매년 이행되고 있으므로 B63 의 두 사건 중 나중 것은 고객 매출이다.
    """
    royalty = actual_royalty()
    return {y: fixed_fee / len(YEARS) + royalty[y] for y in YEARS}


def case_estimate_without_exception():
    """비교용 가정: B63 예외가 없다면 사용권 이전 시점에 로열티 추정치를 거래가격에 넣었을 것이다.

    기대값(문단 53)과, 제약(문단 56)으로 가장 낮은 시나리오까지만 넣는다고 판단한 경우를 같이 본다.
    제약 금액을 어디로 둘지는 기업의 판단이다. 여기서는 가장 낮은 시나리오를 쓴다는 가정이다.
    """
    expected = sum(sales * p for sales, p in SCENARIOS) * ROYALTY_RATE
    constrained = min(sales for sales, _ in SCENARIOS) * ROYALTY_RATE
    return expected, constrained


def case_not_predominant(progress):
    """라이선스가 지배적 항목이 아닐 때: 변동대가 규정(문단 50~59)으로 돌아간다 (B63B).

    로열티가 라이선스와 3년 기술지원 용역 하나의 수행의무에 관련되고, 그 수행의무는 기간에 걸쳐 이행된다고 가정한다.
    매 연말 제약된 거래가격 = 지금까지 실제 로열티 + 남은 기간 가장 낮은 시나리오의 연평균 × 남은 연수.
    """
    royalty = actual_royalty()
    low_per_year = min(sales for sales, _ in SCENARIOS) * ROYALTY_RATE / len(YEARS)
    rows = []
    cumulative_prev = 0.0
    for i, y in enumerate(YEARS):
        earned = sum(royalty[k] for k in YEARS[: i + 1])
        remaining = len(YEARS) - (i + 1)
        price = earned + low_per_year * remaining
        cumulative = price * progress[y]
        rows.append((y, earned, price, cumulative, cumulative - cumulative_prev))
        cumulative_prev = cumulative
    return rows


def main():
    royalty = actual_royalty()
    print("[1] 고객 매출과 실제 로열티 (매출액의 5%)")
    for y in YEARS:
        print(f"    {y}년차  고객 매출 {fmt(LICENSEE_SALES[y])}   로열티 {fmt(royalty[y])}")
    print(f"    합계             {fmt(sum(LICENSEE_SALES.values()))}          {fmt(sum(royalty.values()))}")
    print()

    fixed = 300.0
    use = case_use_right(fixed)
    access = case_access_right(fixed)
    print(f"[2] 고정 계약금 {fixed:,.0f} + 로열티 — B63 적용 (라이선스만 관련)")
    print(f"    {'처리':<26}" + "".join(f"{f'{y}년차':>10}" for y in YEARS) + f"{'합계':>10}")
    print(f"    {'사용권: 계약금은 1년차, 로열티는 매출 때':<26}"
          + "".join(f"{fmt(use[y]):>10}" for y in YEARS) + f"{fmt(sum(use.values())):>10}")
    print(f"    {'접근권: 계약금은 3년 정액, 로열티는 매출 때':<26}"
          + "".join(f"{fmt(access[y]):>10}" for y in YEARS) + f"{fmt(sum(access.values())):>10}")
    print()

    expected, constrained = case_estimate_without_exception()
    print("[3] 비교 — 예외가 없다면 사용권 이전 시점(1년차)에 넣었을 로열티 추정치")
    for sales, p in SCENARIOS:
        print(f"    시나리오 3년 고객 매출 {fmt(sales)}  확률 {p:.0%}  로열티 {fmt(sales * ROYALTY_RATE)}")
    print(f"    기대값 (문단 53)                       {fmt(expected)}")
    print(f"    가장 낮은 시나리오까지만 (제약 판단 가정)   {fmt(constrained)}")
    print(f"    실제 3년 로열티                          {fmt(sum(royalty.values()))}")
    print(f"    B63 적용 시 1년차 로열티 수익             {fmt(royalty[1])}")
    print()

    progress = {1: 1 / 3, 2: 2 / 3, 3: 1.0}
    rows = case_not_predominant(progress)
    print("[4] 라이선스가 지배적 항목이 아닐 때 — 변동대가 규정으로 (B63B, 문단 56·59)")
    print(f"    {'연도':<6}{'누적 실제':>10}{'제약된 가격':>12}{'진행률':>8}{'누적 수익':>10}{'당기 수익':>10}")
    for y, earned, price, cumulative, current in rows:
        print(f"    {f'{y}년차':<6}{fmt(earned):>10}{fmt(price):>12}{progress[y]:>8.0%}"
              f"{fmt(cumulative):>10}{fmt(current):>10}")
    print(f"    비교: 같은 해 실제 로열티  " + "  ".join(f"{y}년차 {royalty[y]:,.1f}" for y in YEARS))


if __name__ == "__main__":
    main()
