"""진행률 산출법과 미설치 자재 — 기업회계기준서 제1115호 문단 39~42, B14~B19.

가상 승강기회사 아자승강기가 건물 한 동에 승강기 10대를 공급하고 설치한다.
설비 공급과 설치는 구별되지 않아 수행의무 하나이고, 기간에 걸쳐 이행한다고 가정한다.
같은 1년차 사실을 세 가지 진행률 측정방법으로 재 본다.

예제의 가정 (금액 단위: 백만원)
- 계약가격 1,000, 추정 총원가 800 = 승강기 기기 400 + 설치 400.
- 기기는 제삼자에게서 조달하고 설계·생산에 관여하지 않는다.
- 1년차에 기기 10대를 모두 현장에 인도했고, 인도 때 고객이 기기를 통제한다.
- 1년차 설치원가는 100 이 들었고, 10대 중 2대 설치를 마쳤다.
- 2년차에 나머지 설치원가 300 이 들고 10대 설치를 모두 마친다. 추정은 바뀌지 않는다.
- 발생원가는 발생한 해의 비용이다.
"""

CONTRACT_PRICE = 1_000
EQUIPMENT_COST = 400
INSTALL_COST_TOTAL = 400
TOTAL_COST = EQUIPMENT_COST + INSTALL_COST_TOTAL
UNITS = 10

# 연차별 누적값: (누적 기기원가, 누적 설치원가, 누적 설치 완료 대수)
CUMULATIVE = {1: (400, 100, 2), 2: (400, 400, 10)}

HOURLY_RATE = 0.5          # B16 간편법 예: 시간당 청구 금액
HOURS_BY_YEAR = {1: 120, 2: 200}


def cost_unadjusted(year):
    equipment, install, _ = CUMULATIVE[year]
    progress = (equipment + install) / TOTAL_COST
    return progress, CONTRACT_PRICE * progress


def cost_adjusted(year):
    """B19⑵ — 미설치 자재는 원가만큼만 수익, 나머지 원가로 진행률을 잰다."""
    equipment, install, _ = CUMULATIVE[year]
    margin_progress = install / INSTALL_COST_TOTAL
    margin_revenue = (CONTRACT_PRICE - EQUIPMENT_COST) * margin_progress
    return margin_progress, equipment + margin_revenue


def output_units(year):
    """B15 — 설치를 마친 대수로 잰다."""
    _, _, installed = CUMULATIVE[year]
    progress = installed / UNITS
    return progress, CONTRACT_PRICE * progress


METHODS = [
    ("원가기준 투입법(조정 없음)", cost_unadjusted),
    ("원가기준 투입법(B19⑵ 조정)", cost_adjusted),
    ("산출법(설치 완료 대수)", output_units),
]


def cumulative_cost(year):
    equipment, install, _ = CUMULATIVE[year]
    return equipment + install


def main():
    print("[1] 1년차 말 — 같은 사실, 세 가지 진행률 (문단 41·B15·B18·B19)")
    print(f"  누적원가 {cumulative_cost(1)} = 기기 {CUMULATIVE[1][0]} + 설치 {CUMULATIVE[1][1]},"
          f" 설치 완료 {CUMULATIVE[1][2]}/{UNITS}대, 추정 총원가 {TOTAL_COST}")
    print("  방법                             진행률     수익     비용     이익")
    for name, method in METHODS:
        progress, revenue = method(1)
        cost = cumulative_cost(1)
        print(f"  {name:<26} {progress:7.2%}  {revenue:7.1f}  {cost:7.1f}  {revenue - cost:7.1f}")
    print()

    print("[2] 연차별 수익과 이익 — 2년차에 완성하면 합계는 같다")
    for name, method in METHODS:
        print(f"  {name}")
        prev_revenue = prev_cost = 0.0
        total_profit = 0.0
        for year in (1, 2):
            _, cum_revenue = method(year)
            cum_cost = cumulative_cost(year)
            revenue, cost = cum_revenue - prev_revenue, cum_cost - prev_cost
            total_profit += revenue - cost
            print(f"    {year}년차  수익 {revenue:7.1f}  비용 {cost:7.1f}  이익 {revenue - cost:7.1f}"
                  f"  이익률 {(revenue - cost) / revenue:7.1%}")
            prev_revenue, prev_cost = cum_revenue, cum_cost
        print(f"    합계 이익 {total_profit:.1f}")
    print()

    equipment, install, _ = CUMULATIVE[1]
    print("[3] B19⑵ 조정의 분해 — 1년차")
    print(f"  미설치 기기: 수익 {equipment:.1f} = 원가 {equipment:.1f}, 이익 0")
    print(f"  설치 부분: 진행률 {install}/{INSTALL_COST_TOTAL} = {install / INSTALL_COST_TOTAL:.2%},"
          f" 수익 ({CONTRACT_PRICE} - {EQUIPMENT_COST}) x {install / INSTALL_COST_TOTAL:.2%}"
          f" = {(CONTRACT_PRICE - EQUIPMENT_COST) * install / INSTALL_COST_TOTAL:.1f}")
    markup = CONTRACT_PRICE / TOTAL_COST
    print(f"  조정 없음은 원가 1 마다 수익 {markup:.2f} 를 붙인다:"
          f" 기기 {equipment} x {markup:.2f} = {equipment * markup:.1f},"
          f" 설치 {install} x {markup:.2f} = {install * markup:.1f}")
    print(f"  B19⑵ 조정은 기기 {equipment:.1f}, 설치 {install} x"
          f" {(CONTRACT_PRICE - EQUIPMENT_COST) / INSTALL_COST_TOTAL:.2f}"
          f" = {install * (CONTRACT_PRICE - EQUIPMENT_COST) / INSTALL_COST_TOTAL:.1f}")
    print(f"  수익 차이 {cost_unadjusted(1)[1] - cost_adjusted(1)[1]:.1f}"
          f" = 기기에 붙은 이익 {equipment * markup - equipment:.1f}"
          f" - 설치에 덜 붙은 이익 {install * (CONTRACT_PRICE - EQUIPMENT_COST) / INSTALL_COST_TOTAL - install * markup:.1f}")
    print()

    print("[4] B16 실무적 간편법 — 시간당 고정금액을 청구하는 유지보수 계약")
    for year, hours in HOURS_BY_YEAR.items():
        print(f"  {year}년차  제공 {hours}시간 x {HOURLY_RATE} = 수익 {hours * HOURLY_RATE:.1f}"
              " (청구권이 있는 금액으로 인식)")


if __name__ == "__main__":
    main()
