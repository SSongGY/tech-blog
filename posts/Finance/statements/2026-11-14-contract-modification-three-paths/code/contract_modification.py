"""계약변경 — 기업회계기준서 제1115호 문단 18~21.

가상 회사 타파소재가 같은 고객과 맺은 계약을 중간에 바꾼다.
가·나는 구별되는 제품 단위를 넘기는 계약이고 추가 수량의 가격만 다르다.
다는 진행률로 수익을 잡는 단일 수행의무(공장 설비 공사)다.
금액 단위는 천원이다.
"""

ORIGINAL_UNITS = 120
ORIGINAL_PRICE = 100        # 원 계약 단가 = 계약 당시 개별 판매가격
DELIVERED_BEFORE = 60       # 계약변경일까지 넘긴 수량
ADDED_UNITS = 30


def money(value):
    return f"{value:>10,.0f}"


def separate_contract(added_price):
    """문단 20 — 추가분이 구별되고 개별 판매가격만큼 값이 오르면 별도 계약."""
    remaining = ORIGINAL_UNITS - DELIVERED_BEFORE
    return [
        ("원 계약 나머지", remaining, ORIGINAL_PRICE),
        ("추가 계약", ADDED_UNITS, added_price),
    ]


def terminate_and_new(added_price):
    """문단 21⑴ — 기존 계약을 끝내고 새 계약을 맺은 것처럼 본다.

    나머지 수행의무에 배분할 대가 = 아직 수익으로 잡지 않은 원 계약 대가
    + 변경으로 약속한 대가. 이를 나머지 전체 수량에 나눠 단가를 다시 정한다.
    """
    remaining = ORIGINAL_UNITS - DELIVERED_BEFORE
    unrecognised = remaining * ORIGINAL_PRICE
    added = ADDED_UNITS * added_price
    units = remaining + ADDED_UNITS
    return unrecognised, added, units, (unrecognised + added) / units


def print_units_case():
    remaining = ORIGINAL_UNITS - DELIVERED_BEFORE
    print(f"[1] 원 계약 — {ORIGINAL_UNITS}개 × {ORIGINAL_PRICE}, 변경일까지 {DELIVERED_BEFORE}개 인도"
          f" → 이미 인식한 수익 {money(DELIVERED_BEFORE * ORIGINAL_PRICE)}")
    print(f"    변경 내용: {ADDED_UNITS}개 추가. 변경일 현재 추가 제품의 개별 판매가격 100,"
          " 기존 고객이라 판매관련원가가 안 드는 만큼 조정한 가격 95")
    print()

    print("[2] 가. 추가분 단가 95 — 개별 판매가격을 반영 → 문단 20 별도 계약")
    total = 0
    for label, units, price in separate_contract(95):
        print(f"    {label:<10} {units:>3}개 × {price:>6.2f} = {money(units * price)}")
        total += units * price
    print(f"    변경일 이후 수익 합계 {money(total)}")
    print()

    print("[3] 나. 추가분 단가 80 — 개별 판매가격을 반영하지 않음 → 문단 21⑴ 종료 후 새 계약")
    unrecognised, added, units, unit_price = terminate_and_new(80)
    print(f"    ㈎ 원 계약 대가 중 아직 수익이 아닌 금액 {money(unrecognised)}")
    print(f"    ㈏ 계약변경으로 약속한 대가           {money(added)}")
    print(f"    나머지 {units}개에 배분 → 단가 {unit_price:.4f}")
    print(f"    변경일 이후 수익 합계 {money(unrecognised + added)}")
    wrong = remaining * ORIGINAL_PRICE + added
    print(f"    (별도 계약으로 잘못 처리하면 원 계약 나머지는 100, 추가분은 80 — 합계 {money(wrong)}은 같고"
          " 인도 순서에 따라 기간별 수익이 갈린다)")
    print()


def print_period_split():
    """나 경우에 기간별로 무엇이 달라지는지 — 다음 분기 원 계약분 40개만 인도."""
    _, _, _, unit_price = terminate_and_new(80)
    delivered_next = 40
    right = delivered_next * unit_price
    wrong = delivered_next * ORIGINAL_PRICE
    print(f"[4] 나. 다음 분기에 {delivered_next}개 인도(원 계약 물량부터) 시 그 분기 수익")
    print(f"    문단 21⑴ 적용   {delivered_next} × {unit_price:.4f} = {money(right)}")
    print(f"    별도 계약 오분류 {delivered_next} × {ORIGINAL_PRICE:.4f} = {money(wrong)}")
    print(f"    차이 {money(wrong - right)} — 앞 분기 수익이 크게, 뒤 분기가 작게 잡힌다")
    print()


def print_cumulative_catch_up():
    price, cost_estimate = 1_000_000, 700_000
    incurred_year1 = 420_000
    progress1 = incurred_year1 / cost_estimate
    revenue1 = price * progress1
    print("[5] 다. 단일 수행의무 공사 — 원가기준 진행률, 문단 21⑵ 누적효과 일괄조정")
    print(f"    원 계약  가격 {money(price)}  예상 원가 {money(cost_estimate)}")
    print(f"    1년차 말 발생원가 {money(incurred_year1)} → 진행률 {progress1 * 100:.2f}%"
          f" → 누적 수익 {money(revenue1)}")

    added_price, added_cost = 150_000, 120_000
    new_price = price + added_price
    new_cost = cost_estimate + added_cost
    progress_at_mod = incurred_year1 / new_cost
    cumulative_at_mod = new_price * progress_at_mod
    catch_up = cumulative_at_mod - revenue1
    print(f"    2년차 초 계약변경 — 사양 추가, 가격 +{added_price:,}, 예상 원가 +{added_cost:,}")
    print(f"    변경 후 가격 {money(new_price)}  예상 원가 {money(new_cost)}")
    print(f"    변경일 진행률 {incurred_year1:,} / {new_cost:,} = {progress_at_mod * 100:.2f}%")
    print(f"    변경일 누적 수익 {money(cumulative_at_mod)}  이미 인식 {money(revenue1)}")
    print(f"    변경일 수익 조정 {money(catch_up)}  (음수면 수익 감액)")

    incurred_year2 = 820_000
    revenue2 = new_price * incurred_year2 / new_cost - cumulative_at_mod
    print(f"    2년차 말 완공(누적 원가 {incurred_year2:,}) → 2년차 나머지 수익 {money(revenue2)}")
    total_revenue = revenue1 + catch_up + revenue2
    print(f"    전체 수익 {money(total_revenue)} = 변경 후 가격")
    margin_old = 1 - cost_estimate / price
    margin_new = 1 - new_cost / new_price
    print(f"    이익률 변경 전 {margin_old * 100:.2f}% → 변경 후 {margin_new * 100:.2f}%"
          " — 추가분의 이익률(20.00%)이 원 계약(30.00%)보다 낮아 전체가 내려간다")
    print()


def main():
    print("가상 회사: 타파소재 / 금액 단위 천원")
    print()
    print_units_case()
    print_period_split()
    print_cumulative_catch_up()


if __name__ == "__main__":
    main()
