"""K-IFRS 제1115호 수익 인식 5단계를 가상 회사 가나전자의 묶음 계약으로 계산한다.

장비와 3년 유지보수를 한 가격에 묶어 팔 때 거래가격을 어떻게 나누고,
연도별 매출과 계약부채가 어떻게 움직이는지 찍는다. 단위는 백만원.
회사와 숫자는 계산을 보이려고 만든 가상 자료다.
"""

# 개별 판매가격 — 각각 따로 팔 때 받는 값 (문단 77)
EQUIPMENT_SSP = 900
MAINTENANCE_SSP_PER_YEAR = 100
MAINTENANCE_YEARS = 3

# 묶음 계약 가격 — 1년차 초에 장비를 인도하고 대금을 한 번에 받는다고 가정한다
CONTRACT_PRICE = 960


def allocate(price, ssp_by_obligation):
    """거래가격을 개별 판매가격 비율로 나눈다 (문단 74·76). 할인도 같은 비율로 나뉜다 (문단 81)."""
    total_ssp = sum(ssp_by_obligation.values())
    return {name: price * ssp / total_ssp for name, ssp in ssp_by_obligation.items()}


def revenue_schedule(equipment_amount, maintenance_amount, years):
    """장비는 인도 시점에, 유지보수는 기간에 걸쳐 균등하게 인식한다 (문단 35·38)."""
    per_year = maintenance_amount / years
    return [equipment_amount + per_year if year == 1 else per_year for year in range(1, years + 1)]


def print_steps():
    print("[1] 5단계 적용 — 장비 + 3년 유지보수 묶음 계약 (단위: 백만원)")
    print("  1단계 계약 식별      문단 9의 다섯 요건을 충족한다고 가정")
    print("  2단계 수행의무 식별  장비 / 유지보수 — 고객이 각각 따로 효익을 얻을 수 있다 (문단 27)")
    print(f"  3단계 거래가격 산정  {CONTRACT_PRICE} (변동대가·유의적 금융요소 없음으로 가정)")
    ssp = {"장비": EQUIPMENT_SSP, "유지보수": MAINTENANCE_SSP_PER_YEAR * MAINTENANCE_YEARS}
    total_ssp = sum(ssp.values())
    print(f"  4단계 배분          개별 판매가격 합계 {total_ssp}, 계약가격 {CONTRACT_PRICE}"
          f" → 할인 {total_ssp - CONTRACT_PRICE} 을 비율대로 나눈다")
    allocated = allocate(CONTRACT_PRICE, ssp)
    for name, amount in allocated.items():
        print(f"      {name:<6} 개별 판매가격 {ssp[name]:>5}  비중 {ssp[name] / total_ssp:>5.1%}"
              f"  배분액 {amount:>6.0f}")
    print("  5단계 인식          장비는 인도 시점, 유지보수는 3년에 걸쳐")
    print()
    return allocated


def print_schedule(allocated):
    print("[2] 연도별 매출과 계약부채 — 대금 960 은 1년차 초에 전액 받음")
    print(f"  {'연도':<6}{'장비 매출':>10}{'유지보수 매출':>12}{'매출 합계':>10}{'받은 현금':>10}{'계약부채 기말':>12}")
    revenue = revenue_schedule(allocated["장비"], allocated["유지보수"], MAINTENANCE_YEARS)
    cumulative_revenue = 0
    cumulative_cash = 0
    for year, amount in enumerate(revenue, start=1):
        cash = CONTRACT_PRICE if year == 1 else 0
        cumulative_revenue += amount
        cumulative_cash += cash
        equipment = allocated["장비"] if year == 1 else 0
        maintenance = amount - equipment
        liability = cumulative_cash - cumulative_revenue
        print(f"  {year}년차{equipment:>12.0f}{maintenance:>14.0f}{amount:>12.0f}{cash:>12.0f}{liability:>14.0f}")
    print(f"  합계{'':>12}{'':>14}{cumulative_revenue:>12.0f}{cumulative_cash:>12.0f}")
    print()
    print("  비교: 인도 시점에 960 을 전부 매출로 잡으면 (기준서와 다른 처리)")
    print(f"    1년차 매출 {CONTRACT_PRICE}  2년차 0  3년차 0  — 1년차 매출이"
          f" {CONTRACT_PRICE - revenue[0]:.0f} 크고 이후 2년은 0")
    print()
    return revenue


def print_discount_to_one(revenue_proportional):
    print("[3] 할인을 어디에 붙이느냐 — 문단 81(비례 배분)과 문단 82(특정 수행의무에 배분)")
    maintenance_ssp = MAINTENANCE_SSP_PER_YEAR * MAINTENANCE_YEARS
    # 문단 82 의 요건을 모두 충족해 할인 240 전부가 장비에 속한다는 증거가 있다고 가정한다
    equipment_only = CONTRACT_PRICE - maintenance_ssp
    revenue_specific = revenue_schedule(equipment_only, maintenance_ssp, MAINTENANCE_YEARS)
    print(f"  {'연도':<6}{'비례 배분':>10}{'장비에 전부':>12}{'차이':>8}")
    for year, (a, b) in enumerate(zip(revenue_proportional, revenue_specific), start=1):
        print(f"  {year}년차{a:>12.0f}{b:>14.0f}{b - a:>+10.0f}")
    print(f"  3년 합계 {sum(revenue_proportional):.0f} 과 {sum(revenue_specific):.0f} — 합계는 같고 시점만 다르다")
    print()


def print_growth(allocated):
    print("[4] 계약 건수가 늘다가 멈출 때 — 1~5년차에 10·15·20·20·20 건 체결")
    contracts = [10, 15, 20, 20, 20]
    maintenance_per_year = allocated["유지보수"] / MAINTENANCE_YEARS
    print(f"  {'연도':<6}{'체결':>6}{'받은 현금':>10}{'매출':>10}{'현금-매출':>10}{'계약부채 기말':>12}")
    liability = 0
    for year, count in enumerate(contracts, start=1):
        cash = count * CONTRACT_PRICE
        equipment_revenue = count * allocated["장비"]
        # 올해와 지난 두 해에 맺은 계약의 유지보수가 올해 매출이 된다
        live = sum(contracts[max(0, year - MAINTENANCE_YEARS):year])
        revenue = equipment_revenue + live * maintenance_per_year
        liability += cash - revenue
        print(f"  {year}년차{count:>8}{cash:>12.0f}{revenue:>10.0f}{cash - revenue:>+12.0f}{liability:>14.0f}")
    print("  계약이 늘어나는 동안 받은 현금이 매출보다 크고 계약부채가 쌓인다.")
    print("  체결 건수가 3년(유지보수 기간) 동안 같으면 현금과 매출이 같아지고 계약부채가 더 늘지 않는다.")


def main():
    allocated = print_steps()
    revenue = print_schedule(allocated)
    print_discount_to_one(revenue)
    print_growth(allocated)


if __name__ == "__main__":
    main()
