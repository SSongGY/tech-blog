"""수행의무 식별 — 기업회계기준서 제1115호 문단 22~30.

가상 기계회사 마바기계가 포장 설비 1대를 설치까지 해 주고 유지보수를 붙여 판다.
같은 계약을 두 회사가 맺었다고 놓고, 설치의 성격만 다르게 둔다.

- 사아기계: 설치가 표준 작업이다. 다른 설치업체도 할 수 있고 설비를 바꾸지 않는다.
  설비·설치·유지보수가 각각 구별되어 수행의무가 셋이다.
- 마바기계: 설치하면서 설비를 고객 생산라인에 맞게 유의적으로 고쳐 만든다(문단 29⑵).
  설비와 설치가 하나의 결합산출물이 되어 수행의무가 둘이다(문단 30).

예제의 가정 (금액 단위: 백만원)
- 계약가격 1,200 = 개별 판매가격 합계. 할인이 없어 배분이 개별 판매가격 그대로다.
- 설비는 1년차 4분기에 고객 공장에 인도한다. 설치는 2년차 1분기에 끝나고 고객이 인수한다.
- 유지보수 24개월은 2년차 2분기부터 8분기 동안 고르게 이행한다(일련의 용역, 문단 22⑵).
- 결합 수행의무는 설치 완료·인수 시점에 통제가 이전된다고 가정한다.
  기간에 걸쳐 이전되는지(문단 35)는 별도 판단이고, 이 예제에서는 다루지 않는다.
- 대금: 설비 인도 때 900, 설치 완료 때 300(설치 150 + 유지보수 선납 150).
"""

SSP = {"설비": 900, "설치": 150, "유지보수": 150}
COST = {"설비": 600, "설치": 100, "유지보수": 80}
CONTRACT_PRICE = 1_200
MAINTENANCE_QUARTERS = 8

# (연차, 분기) — 유지보수는 2년차 2분기부터 8분기
DELIVERY = (1, 4)
INSTALL_DONE = (2, 1)
MAINTENANCE_START = (2, 2)
BILLING = [((1, 4), 900), ((2, 1), 300)]
YEARS = [1, 2, 3, 4]


def quarters_from(start, count):
    year, quarter = start
    result = []
    for _ in range(count):
        result.append((year, quarter))
        quarter += 1
        if quarter == 5:
            year, quarter = year + 1, 1
    return result


MAINTENANCE_SCHEDULE = quarters_from(MAINTENANCE_START, MAINTENANCE_QUARTERS)


def obligations(install_integrates):
    """수행의무 목록: (이름, 배분액, 원가, 통제 이전 시점들)."""
    maintenance = ("유지보수", SSP["유지보수"], COST["유지보수"], MAINTENANCE_SCHEDULE)
    if install_integrates:
        combined_price = SSP["설비"] + SSP["설치"]
        combined_cost = COST["설비"] + COST["설치"]
        return [("설비+설치(결합)", combined_price, combined_cost, [INSTALL_DONE]), maintenance]
    return [
        ("설비", SSP["설비"], COST["설비"], [DELIVERY]),
        ("설치", SSP["설치"], COST["설치"], [INSTALL_DONE]),
        maintenance,
    ]


def by_year(install_integrates):
    revenue = {y: 0.0 for y in YEARS}
    cost = {y: 0.0 for y in YEARS}
    for _, price, cst, points in obligations(install_integrates):
        for year, _ in points:
            # 기간에 걸쳐 이행하는 유지보수는 분기마다 같은 몫을 인식한다
            revenue[year] += price / len(points)
            cost[year] += cst / len(points)
    return revenue, cost


def year_end_positions(revenue):
    cum_rev = cum_bill = 0.0
    rows = []
    for year in YEARS:
        cum_rev += revenue[year]
        cum_bill += sum(amount for (y, _), amount in BILLING if y == year)
        rows.append((year, cum_rev, cum_bill, cum_bill - cum_rev))
    return rows


def print_case(label, install_integrates):
    print(f"  {label}")
    for name, price, cst, points in obligations(install_integrates):
        when = "분기마다" if len(points) > 1 else f"{points[0][0]}년차 {points[0][1]}분기"
        print(f"    수행의무 {name:<12} 배분 {price:7.1f}  원가 {cst:6.1f}  인식 {when}")
    revenue, cost = by_year(install_integrates)
    print("    연차      수익     원가   매출총이익")
    for year in YEARS:
        print(f"     {year}   {revenue[year]:7.2f}  {cost[year]:7.2f}  {revenue[year] - cost[year]:9.2f}")
    print(f"    합계  {sum(revenue.values()):7.2f}  {sum(cost.values()):7.2f}"
          f"  {sum(revenue.values()) - sum(cost.values()):9.2f}")
    return revenue


def main():
    assert sum(SSP.values()) == CONTRACT_PRICE
    print("[1] 수행의무 구성에 따른 연차별 수익 — 문단 22·27·29·30")
    rev_a = print_case("사아기계 — 설치가 표준 작업: 수행의무 3개", install_integrates=False)
    print()
    rev_b = print_case("마바기계 — 설치가 설비를 유의적으로 고객 맞춤화: 수행의무 2개", install_integrates=True)
    print()
    print(f"  1년차 수익 차이 {rev_a[1] - rev_b[1]:.2f} — 마바기계는 설비를 인도했어도 결합산출물이 이전되지 않았다")
    print()

    print("[2] 연말 계약부채 — 누적 청구 − 누적 수익 (문단 106)")
    for label, revenue in (("사아기계", rev_a), ("마바기계", rev_b)):
        print(f"  {label}")
        print("    연차   누적수익   누적청구   계약부채")
        for year, cum_rev, cum_bill, liability in year_end_positions(revenue):
            print(f"     {year}   {cum_rev:8.2f}   {cum_bill:8.2f}   {liability:8.2f}")
    print()

    print("[3] 유지보수를 일련의 용역 하나로 볼 때 — 문단 22⑵·23")
    monthly = SSP["유지보수"] / 24
    print(f"  24개월 각각이 구별되는 용역이지만 실질이 같고 이전 방식이 같아 수행의무 1개로 본다")
    print(f"  월별 몫 {monthly:.2f}, 분기 몫 {monthly * 3:.2f}, 8분기 합계 {monthly * 24:.2f}")


if __name__ == "__main__":
    main()
