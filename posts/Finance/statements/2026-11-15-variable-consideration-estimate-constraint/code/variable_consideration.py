"""변동대가 추정과 제약 — 기업회계기준서 제1115호 문단 50~57, 59, 87~88.

가상 회사 타파건설(공사)과 하나부품(부품 공급)의 숫자로 계산한다. 단위는 천원.
"""

FIXED_PRICE = 900_000

# 결과가 두 가지뿐인 보너스: 문단 53⑵ 가 가능성이 가장 높은 금액을 예로 든 경우
BINARY_BONUS = [(0, 0.30), (100_000, 0.70)]

# 결과가 여러 개인 보너스: 조기 완공 일수에 따라 단계가 갈린다
TIERED_BONUS = [(0, 0.20), (50_000, 0.50), (100_000, 0.30)]

UNIT_PRICE = 100
REBATE_PRICE = 90          # 연간 수량이 문턱을 넘으면 첫 단위부터 소급 적용
REBATE_THRESHOLD = 1_000
# (분기, 판매 수량, 그 분기 말에 예상한 연간 총수량)
QUARTERS = [("1분기", 200, 800), ("2분기", 350, 1_100), ("3분기", 300, 1_100), ("4분기", 250, 1_100)]


def expected_value(outcomes):
    return sum(amount * prob for amount, prob in outcomes)


def most_likely(outcomes):
    return max(outcomes, key=lambda pair: pair[1])[0]


def reversal_profile(included, outcomes):
    """포함한 금액이 실제보다 클 때 되돌려야 하는 확률과 최대 크기."""
    shortfalls = [(included - amount, prob) for amount, prob in outcomes if amount < included]
    probability = sum(prob for _, prob in shortfalls)
    worst = max((gap for gap, _ in shortfalls), default=0)
    return probability, worst


def print_inputs():
    print("[0] 입력 자료 (가상, 단위 천원)")
    print(f"    타파건설 공사 고정대가 {FIXED_PRICE:>9,}")
    print("    두 결과 보너스   " + "  ".join(f"{a:>7,}@{p:.0%}" for a, p in BINARY_BONUS))
    print("    단계 보너스     " + "  ".join(f"{a:>7,}@{p:.0%}" for a, p in TIERED_BONUS))
    print(f"    하나부품 단가 {UNIT_PRICE} → 연 {REBATE_THRESHOLD:,}개 이상이면 전량에 단가 {REBATE_PRICE} 소급 적용")
    print()


def binary_case():
    ev, ml = expected_value(BINARY_BONUS), most_likely(BINARY_BONUS)
    print("[1] 결과가 두 가지인 보너스 — 두 방법의 추정치")
    print(f"    기댓값                {FIXED_PRICE + ev:>11,.0f}   (실제로는 나올 수 없는 금액)")
    print(f"    가능성이 가장 높은 금액 {FIXED_PRICE + ml:>11,.0f}")
    print()


def tiered_case():
    ev, ml = expected_value(TIERED_BONUS), most_likely(TIERED_BONUS)
    print("[2] 단계 보너스 — 거래가격에 넣을 보너스 후보별 수익 환원 위험")
    print(f"    기댓값 {ev:,.0f}  가능성이 가장 높은 금액 {ml:,.0f}")
    print("    포함 금액     되돌릴 확률   되돌릴 최대 크기   누적 수익 대비")
    for label, included in [("0 (전부 제약)", 0), ("가능성 최고", ml), ("기댓값", ev), ("최대치", 100_000)]:
        prob, worst = reversal_profile(included, TIERED_BONUS)
        ratio = worst / (FIXED_PRICE + included)
        print(f"    {label:<12}{included:>9,.0f}  {prob:>8.0%}  {worst:>14,.0f}  {ratio:>12.1%}")
    print()


def rebate_case():
    print("[3] 소급 수량 리베이트 — 분기 말 재추정과 누적 따라잡기 (문단 59, 88)")
    print("    분기    판매   누적   예상 연간  적용 단가   누적 수익   분기 수익   명목 청구액")
    cumulative_units, cumulative_revenue = 0, 0
    for name, units, forecast in QUARTERS:
        cumulative_units += units
        price = REBATE_PRICE if forecast >= REBATE_THRESHOLD else UNIT_PRICE
        new_cumulative = cumulative_units * price
        quarter_revenue = new_cumulative - cumulative_revenue
        cumulative_revenue = new_cumulative
        print(f"    {name}  {units:>5}  {cumulative_units:>5,}  {forecast:>8,}  {price:>8}"
              f"  {new_cumulative:>10,}  {quarter_revenue:>10,}  {units * UNIT_PRICE:>10,}")
    print(f"    연간 수익 {cumulative_revenue:,} = {cumulative_units:,}개 × {REBATE_PRICE}")
    print()


if __name__ == "__main__":
    print_inputs()
    binary_case()
    tiered_case()
    rebate_case()
