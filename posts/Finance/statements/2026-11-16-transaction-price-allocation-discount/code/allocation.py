"""거래가격 배분과 할인 배분 — 기업회계기준서 제1115호 문단 73~86.

가상 가전회사 파하가전이 냉장고·정수기·2년 관리 용역을 묶어 판다.
금액 단위는 천원이다.

예제의 가정
- 냉장고·정수기는 1분기 초에 인도하고 그때 수익을 인식한다.
- 관리 용역은 8분기에 걸쳐 고르게 이행한다.
- 파하가전은 냉장고를 900 에 따로 팔고, 정수기+관리 묶음을 450 에 따로 판다.
"""

SSP = {"냉장고": 900, "정수기": 300, "관리 용역": 300}
BUNDLE_PRICE = 1_350
SERVICE_QUARTERS = 8
FIRST_YEAR_QUARTERS = 4
REGULAR_BUNDLE = ("정수기", "관리 용역")
REGULAR_BUNDLE_PRICE = 450
APP_CONTRACT_PRICE = 1_650   # 앱 연동 서비스까지 넣은 계약


def allocate_by_ssp(items, total):
    ssp_sum = sum(SSP[name] for name in items)
    return {name: total * SSP[name] / ssp_sum for name in items}


def proportional():
    return allocate_by_ssp(SSP, BUNDLE_PRICE)


def concentrated():
    """문단 82 세 조건을 충족해 할인 전체를 정수기+관리 묶음에 배분한다."""
    result = {"냉장고": SSP["냉장고"]}
    result.update(allocate_by_ssp(REGULAR_BUNDLE, REGULAR_BUNDLE_PRICE))
    return result


def first_year_revenue(allocation):
    goods = allocation["냉장고"] + allocation["정수기"]
    service = allocation["관리 용역"] * FIRST_YEAR_QUARTERS / SERVICE_QUARTERS
    return goods, service, allocation["관리 용역"] - service


def show_allocation():
    discount = sum(SSP.values()) - BUNDLE_PRICE
    print(f"[1] 묶음 판매 거래가격 배분 — 개별 판매가격 합계 {sum(SSP.values()):,}, 계약가격 {BUNDLE_PRICE:,}, 할인 {discount}")
    print("    수행의무     개별판매가격   비례 배분(81)   일부 집중(82)")
    prop, conc = proportional(), concentrated()
    for name, price in SSP.items():
        print(f"    {name:<8} {price:>10,} {prop[name]:>14,.1f} {conc[name]:>14,.1f}")
    print(f"    합계       {sum(SSP.values()):>10,} {sum(prop.values()):>14,.1f} {sum(conc.values()):>14,.1f}")
    print()
    return prop, conc


def show_first_year(prop, conc):
    print("[2] 첫해 수익과 연말 계약부채 — 관리 용역은 8분기 중 4분기 이행")
    print("    배분 방식      재화 수익   용역 수익   첫해 합계   계약부채")
    for label, allocation in (("비례 배분", prop), ("일부 집중", conc)):
        goods, service, liability = first_year_revenue(allocation)
        print(f"    {label:<10} {goods:>10,.1f} {service:>10,.1f} {goods + service:>10,.1f} {liability:>10,.1f}")
    print()


def show_residual_order():
    observable = SSP["냉장고"] + REGULAR_BUNDLE_PRICE
    right = APP_CONTRACT_PRICE - observable
    wrong = APP_CONTRACT_PRICE - sum(SSP.values())
    print(f"[3] 앱 연동 서비스를 잔여접근법으로 — 계약가격 {APP_CONTRACT_PRICE:,} (문단 79⑶·83)")
    print("    순서                          다른 수행의무 몫   앱 연동 몫")
    print(f"    할인 먼저 배분 후 잔여 (83)   {observable:>14,} {right:>10,}")
    print(f"    잔여 먼저, 할인 무시          {sum(SSP.values()):>14,} {wrong:>10,}")


def main():
    print("환경: Python 표준 라이브러리, 금액 단위 천원, 가상 회사 파하가전")
    print()
    prop, conc = show_allocation()
    show_first_year(prop, conc)
    show_residual_order()


if __name__ == "__main__":
    main()
