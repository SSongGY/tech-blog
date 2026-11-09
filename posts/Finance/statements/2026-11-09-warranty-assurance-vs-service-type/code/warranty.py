"""보증을 확신 유형과 용역 유형으로 나눠 회계처리할 때 연도별 손익이 어떻게 갈리는지 계산한다.

가상 회사 가나가전이 공기청정기 1,000대를 판다. 금액 단위는 만원이다.
근거: 기업회계기준서 제1115호 문단 74·76, B28~B33 / 제1037호 문단 36·39.
"""

UNITS = 1_000
UNIT_COST = 60.0

# 1년 결함 보증의 대당 수리비 시나리오 — (확률, 대당 수리비)
ASSURANCE_SCENARIOS = [(0.80, 0.0), (0.15, 2.0), (0.05, 10.0)]

# 안 A: 1년 결함 보증만 붙인 판매
PRICE_BASIC = 100.0

# 안 B: 1년 결함 보증 + 2~3년차 무상 수리 용역(연장보증)을 묶은 판매
PRICE_BUNDLE = 108.0
SSP_PRODUCT = 100.0      # 1년 보증이 붙은 제품을 따로 팔 때 가격
SSP_EXTENDED = 20.0      # 연장보증을 따로 팔 때 가격 — 따로 살 수 있으므로 구별되는 용역(B29)
EXTENDED_YEARS = [2, 3]
SERVICE_COST_PER_YEAR = 3.0   # 연장보증 기간의 대당 연간 수리 원가


def fmt(value):
    return f"{value:>10,.1f}"


def expected_assurance_cost():
    # 다수 항목에 걸린 의무는 확률 가중평균(기댓값)으로 잰다 (제1037호 문단 39)
    return sum(p * cost for p, cost in ASSURANCE_SCENARIOS)


def allocate_bundle():
    # 상대적 개별 판매가격 비율로 거래가격을 배분한다 (제1115호 문단 74·76)
    total_ssp = SSP_PRODUCT + SSP_EXTENDED
    product = PRICE_BUNDLE * SSP_PRODUCT / total_ssp
    extended = PRICE_BUNDLE * SSP_EXTENDED / total_ssp
    return product, extended


def plan_basic(provision_per_unit):
    years = {y: {"revenue": 0.0, "cost": 0.0, "warranty": 0.0} for y in (1, 2, 3)}
    years[1]["revenue"] = UNITS * PRICE_BASIC
    years[1]["cost"] = UNITS * UNIT_COST
    years[1]["warranty"] = UNITS * provision_per_unit
    return years


def plan_bundle_service_type(provision_per_unit):
    product, extended = allocate_bundle()
    years = plan_basic(provision_per_unit)
    years[1]["revenue"] = UNITS * product
    # 연장보증 몫은 계약부채로 두었다가 용역을 제공하는 2·3년차에 나눠 수익으로 인식한다
    for y in EXTENDED_YEARS:
        years[y]["revenue"] = UNITS * extended / len(EXTENDED_YEARS)
        # 용역 유형의 수리 원가는 충당부채가 아니라 용역을 제공할 때 원가로 잡는다
        years[y]["warranty"] = UNITS * SERVICE_COST_PER_YEAR
    return years


def plan_bundle_as_assurance(provision_per_unit):
    # 연장보증까지 확신 유형으로 잘못 본 경우 — 기준서가 허용하는 처리가 아니다
    years = plan_basic(provision_per_unit)
    years[1]["revenue"] = UNITS * PRICE_BUNDLE
    extra = UNITS * SERVICE_COST_PER_YEAR * len(EXTENDED_YEARS)
    years[1]["warranty"] = UNITS * provision_per_unit + extra
    return years


def gross_profit(row):
    return row["revenue"] - row["cost"] - row["warranty"]


def print_plan(label, years):
    print(f"  {label}")
    print(f"    {'연도':>4} {'수익':>10} {'매출원가':>10} {'보증원가':>10} {'매출총이익':>10}")
    total = 0.0
    for y in (1, 2, 3):
        row = years[y]
        gp = gross_profit(row)
        total += gp
        print(f"    {y:>4}{fmt(row['revenue'])}{fmt(row['cost'])}{fmt(row['warranty'])}{fmt(gp)}")
    print(f"    합계 매출총이익 {total:,.1f}")
    return total


def main():
    print("[1] 확신 유형 보증의 충당부채 — 기댓값 (제1037호 문단 39)")
    print(f"    {'확률':>6} {'대당 수리비':>10}")
    for p, cost in ASSURANCE_SCENARIOS:
        print(f"    {p:>6.2f} {cost:>10.1f}")
    per_unit = expected_assurance_cost()
    print(f"  대당 기댓값 {per_unit:.2f} → 충당부채 {UNITS * per_unit:,.1f}")
    print()

    print("[2] 묶음 가격 배분 — 상대적 개별 판매가격 (제1115호 문단 74·76, B29)")
    product, extended = allocate_bundle()
    print(f"  개별 판매가격 합계 {SSP_PRODUCT + SSP_EXTENDED:.1f} (제품 {SSP_PRODUCT:.1f} + 연장보증 {SSP_EXTENDED:.1f})")
    print(f"  묶음 가격 {PRICE_BUNDLE:.1f} → 제품 {product:.1f} · 연장보증 {extended:.1f} (대당)")
    print(f"  판매 시점 계약부채 {UNITS * extended:,.1f}")
    print()

    print("[3] 연도별 손익 — 1,000대, 1년차 초에 판매")
    total_a = print_plan("안 A: 1년 결함 보증만 (확신 유형 → 충당부채)", plan_basic(per_unit))
    print()
    years_b = plan_bundle_service_type(per_unit)
    total_b = print_plan("안 B: 연장보증 묶음, 용역 유형으로 분리 (B29·B32)", years_b)
    print()
    years_c = plan_bundle_as_assurance(per_unit)
    total_c = print_plan("안 C: 같은 묶음을 전부 확신 유형으로 본 경우 (허용되지 않음)", years_c)
    print()
    print(f"  안 B와 안 C의 3년 합계 차이 {total_b - total_c:,.1f}")
    print(f"  1년차 매출총이익 차이 (C − B) {gross_profit(years_c[1]) - gross_profit(years_b[1]):,.1f}")
    print()

    print("[4] 안 B의 계약부채 잔액 (연말)")
    balance = UNITS * extended
    for y in (1, 2, 3):
        balance -= years_b[y]["revenue"] if y in EXTENDED_YEARS else 0.0
        print(f"    {y}년차 말 {balance:,.1f}")


if __name__ == "__main__":
    main()
