"""가상 회사 사아설비의 한 해 수익을, 판단 하나만 바꿔 다시 계산한다.

기업회계기준서 제1115호 문단 123~126 이 공시하라는 판단(진행률 방법, 통제 이전 시점,
반품률 가정, 개별 판매가격 추정)이 수익을 얼마나 움직이는지 보이려는 예제다.
숫자는 모두 가상이다. 금액 단위는 억원.
"""

import sys

OTHER_REVENUE = 3000  # 판단이 개입하지 않는 나머지 수익

# [1] 기간에 걸쳐 이행하는 설비 구축 계약 — 문단 124
BUILD_PRICE = 1000
BUILD_TOTAL_COST = 800
BUILD_COST_TO_DATE = 360   # 자재를 먼저 사들여 원가가 앞에 몰려 있다
UNITS_TOTAL = 10
UNITS_INSTALLED = 3

# [2] 한 시점에 이행하는 수출 — 문단 125
SHIPPED_DEC_28 = 240       # 12월 28일 선적, 1월 5일 고객 도착

# [3] 반품권이 있는 판매 — 문단 126⑴⑵⑷
RETURN_SALES = 2000
COST_RATIO = 0.60

# [4] 장비 + 3년 유지보수 묶음 — 문단 126⑶
BUNDLE_PRICE = 1200
SSP_EQUIPMENT = 1000
MAINTENANCE_YEARS = 3


def build_revenue(method):
    if method == "투입법(발생원가)":
        progress = BUILD_COST_TO_DATE / BUILD_TOTAL_COST
    else:
        progress = UNITS_INSTALLED / UNITS_TOTAL
    return progress, BUILD_PRICE * progress


def shipment_revenue(transfer_point):
    # 선적 시점에 통제가 넘어간다고 판단하면 올해, 도착 시점이면 내년 수익이다
    return SHIPPED_DEC_28 if transfer_point == "선적 시점" else 0


def return_sale(return_rate):
    revenue = RETURN_SALES * (1 - return_rate)
    refund_liability = RETURN_SALES * return_rate
    return_asset = RETURN_SALES * COST_RATIO * return_rate
    cost_of_sales = RETURN_SALES * COST_RATIO - return_asset
    return revenue, refund_liability, return_asset, revenue - cost_of_sales


def bundle_revenue(ssp_maintenance):
    total_ssp = SSP_EQUIPMENT + ssp_maintenance
    equipment = BUNDLE_PRICE * SSP_EQUIPMENT / total_ssp
    maintenance = BUNDLE_PRICE - equipment
    # 장비는 인도 시점, 유지보수는 3년에 걸쳐 고르게 이행한다고 둔다
    return equipment, maintenance, equipment + maintenance / MAINTENANCE_YEARS


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    print("[1] 진행률 방법 — 문단 124 (거래가격 1000, 추정 총원가 800)")
    build = {}
    for method in ("투입법(발생원가)", "산출법(설치 대수)"):
        progress, revenue = build_revenue(method)
        build[method] = revenue
        print(f"  {method:<14} 진행률 {progress:6.1%}  당기 수익 {revenue:7.1f}")
    print(f"  발생원가 {BUILD_COST_TO_DATE} / {BUILD_TOTAL_COST},"
          f" 설치 {UNITS_INSTALLED} / {UNITS_TOTAL}대\n")

    print("[2] 통제 이전 시점 — 문단 125 (12월 28일 선적 240, 1월 5일 도착)")
    ship = {}
    for point in ("선적 시점", "도착 시점"):
        ship[point] = shipment_revenue(point)
        print(f"  통제 이전 {point:<6} 당기 수익 {ship[point]:7.1f}")
    print()

    print("[3] 반품률 가정 — 문단 126⑴⑵⑷ (판매 2000, 원가율 60%)")
    print("  반품률   수익   환불부채  반환재고 회수권  매출총이익")
    ret = {}
    for rate in (0.05, 0.08):
        revenue, refund, asset, gross = return_sale(rate)
        ret[rate] = revenue
        print(f"  {rate:5.0%} {revenue:7.1f} {refund:8.1f} {asset:12.1f} {gross:10.1f}")
    print()

    print("[4] 유지보수 개별 판매가격 추정 — 문단 126⑶ (묶음 1200, 장비 1000)")
    print("  추정 방법              유지보수 SSP  장비 배분  유지보수 배분  당기 수익")
    bundle = {}
    for label, ssp in (("관측 가능한 단독 판매가격", 300),
                       ("예상원가 + 이윤", 250)):
        equipment, maintenance, revenue = bundle_revenue(ssp)
        bundle[label] = revenue
        print(f"  {label:<16} {ssp:9} {equipment:10.1f} {maintenance:12.1f} {revenue:9.1f}")
    print()

    base = (OTHER_REVENUE + build["투입법(발생원가)"] + ship["선적 시점"]
            + ret[0.05] + bundle["관측 가능한 단독 판매가격"])
    swings = [
        ("124 진행률: 투입법 → 산출법",
         build["산출법(설치 대수)"] - build["투입법(발생원가)"]),
        ("125 통제 이전: 선적 → 도착", ship["도착 시점"] - ship["선적 시점"]),
        ("126 반품률: 5% → 8%", ret[0.08] - ret[0.05]),
        ("126 SSP: 관측 300 → 원가+이윤 250",
         bundle["예상원가 + 이윤"] - bundle["관측 가능한 단독 판매가격"]),
    ]
    print(f"[5] 판단 하나만 바꿨을 때 당기 수익 — 회사가 택한 판단의 수익 {base:.1f}")
    for label, delta in swings:
        print(f"  {label:<30} {delta:+8.1f}  ({delta / base:+6.2%})")
    largest = max(swings, key=lambda s: abs(s[1]))
    print(f"  가장 큰 변동: {largest[0]}")


if __name__ == "__main__":
    main()
