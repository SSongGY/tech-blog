"""반품권이 있는 판매 — 환불부채, 반환재고 회수권, 변동대가 제약.

가상 회사 가나리빙이 12월에 쿠션 1,000개를 반품 가능 조건으로 판다.
기업회계기준서 제1115호 문단 53·56·B21~B25 의 처리를 숫자로 따라간다.
금액 단위는 만원이다.
"""

import sys

UNITS_SOLD = 1_000
UNIT_PRICE = 10.0       # 개당 판매가
UNIT_COST = 6.0         # 개당 재고 장부금액
RECOVERY_COST = 0.5     # 반품 1개를 회수하는 데 드는 원가
VALUE_DECLINE = 1.0     # 반품된 제품의 가치 감소 (B25 가 회수 원가에 포함시킨다)

# 비슷한 판매가 많으므로 기댓값을 쓴다 (문단 53(1))
RETURN_SCENARIOS = [(0.03, 0.2), (0.05, 0.5), (0.08, 0.3)]


def recognise(return_units):
    """반품 예상 수량을 받아 판매 시점의 다섯 금액을 돌려준다 (B21)."""
    kept = UNITS_SOLD - return_units
    revenue = kept * UNIT_PRICE
    refund_liability = return_units * UNIT_PRICE
    # 회수권 자산은 이전 장부금액에서 회수 원가를 뺀다 (B25)
    asset_per_unit = UNIT_COST - RECOVERY_COST - VALUE_DECLINE
    return_asset = return_units * asset_per_unit
    cost_of_sales = UNITS_SOLD * UNIT_COST - return_asset
    return {
        "revenue": revenue,
        "refund_liability": refund_liability,
        "return_asset": return_asset,
        "cost_of_sales": cost_of_sales,
        "gross_profit": revenue - cost_of_sales,
    }


def print_row(label, r):
    print(f"  {label:<18}{r['revenue']:>9,.1f}{r['refund_liability']:>9,.1f}"
          f"{r['return_asset']:>9,.1f}{r['cost_of_sales']:>10,.1f}{r['gross_profit']:>9,.1f}")


def print_header():
    print(f"  {'':<18}{'수익':>8}{'환불부채':>6}{'회수권':>7}{'매출원가':>7}{'매출총이익':>6}")


def main():
    print(f"Python {sys.version.split()[0]}")
    print()
    print("[0] 가상 거래 — 가나리빙, 12월 판매 (단위: 만원)")
    print(f"  판매 수량 {UNITS_SOLD:,}개 · 개당 판매가 {UNIT_PRICE} · 개당 장부금액 {UNIT_COST}")
    print(f"  반품 1개당 회수 원가 {RECOVERY_COST} · 가치 감소 {VALUE_DECLINE}")
    print(f"  판매대가 합계 {UNITS_SOLD * UNIT_PRICE:,.1f} · 재고 장부금액 합계 {UNITS_SOLD * UNIT_COST:,.1f}")
    print()

    print("[1] 반품률 추정 — 기댓값과 가능성이 가장 높은 금액 (문단 53)")
    print(f"  {'반품률':>6}{'확률':>8}{'반품 수량':>10}")
    expected_rate = 0.0
    for rate, prob in RETURN_SCENARIOS:
        print(f"  {rate:>6.0%}{prob:>9.1f}{UNITS_SOLD * rate:>10.0f}")
        expected_rate += rate * prob
    most_likely = max(RETURN_SCENARIOS, key=lambda s: s[1])[0]
    print(f"  기댓값 반품률 {expected_rate:.1%} → {UNITS_SOLD * expected_rate:.0f}개")
    print(f"  가능성이 가장 높은 반품률 {most_likely:.0%} → {UNITS_SOLD * most_likely:.0f}개")
    print()

    expected_units = round(UNITS_SOLD * expected_rate)
    constrained_units = round(UNITS_SOLD * max(r for r, _ in RETURN_SCENARIOS))
    print("[2] 판매 시점 인식 — 기댓값 대 제약 적용 (문단 56·57, B21·B23·B25)")
    print("    제약: 새 제품군이라 경험이 적으면(57(3)) 되돌릴 일이 없을 만큼만 수익에 넣는다")
    print_header()
    base = recognise(expected_units)
    print_row(f"기댓값 {expected_units}개", base)
    print_row(f"제약 {constrained_units}개", recognise(constrained_units))
    print_row("반품 없음 가정", recognise(0))
    print(f"  검산: 남는 {UNITS_SOLD - expected_units}개 × 개당 이익 {UNIT_PRICE - UNIT_COST}"
          f" − 반품 {expected_units}개 × 회수 손실 {RECOVERY_COST + VALUE_DECLINE}"
          f" = {(UNITS_SOLD - expected_units) * (UNIT_PRICE - UNIT_COST) - expected_units * (RECOVERY_COST + VALUE_DECLINE):,.1f}")
    print()

    print("[3] 12월 말 — 20개가 반품됐고, 전체 반품 예상을 70개로 올린다 (B24·B25)")
    returned = 20
    revised_units = 70
    revised = recognise(revised_units)
    print(f"  (가) 반품 {returned}개 정산")
    print(f"      환불부채 −{returned * UNIT_PRICE:,.1f} (현금 환불)")
    print(f"      회수권 −{returned * (UNIT_COST - RECOVERY_COST - VALUE_DECLINE):,.1f}"
          f" + 회수 원가 지급 {returned * RECOVERY_COST:,.1f}"
          f" → 반환재고 {returned * (UNIT_COST - VALUE_DECLINE):,.1f}")
    print(f"  (나) 반품 예상 {expected_units}개 → {revised_units}개 재추정")
    print(f"      수익 조정 {revised['revenue'] - base['revenue']:+,.1f} (환불부채 증가분)")
    print(f"      매출원가 조정 {revised['cost_of_sales'] - base['cost_of_sales']:+,.1f} (회수권 증가분)")
    print(f"      매출총이익 조정 {revised['gross_profit'] - base['gross_profit']:+,.1f}")
    remaining = revised_units - returned
    print(f"  12월 말 잔액 — 환불부채 {remaining * UNIT_PRICE:,.1f} · 회수권"
          f" {remaining * (UNIT_COST - RECOVERY_COST - VALUE_DECLINE):,.1f} (남은 예상 반품 {remaining}개)")
    print(f"  12월 손익 — 수익 {revised['revenue']:,.1f} · 매출원가 {revised['cost_of_sales']:,.1f}"
          f" · 매출총이익 {revised['gross_profit']:,.1f}")
    print()

    print("[4] 반품을 받을 때 되돌리는 방식과 비교 — 1월에 남은 50개가 예상대로 반품")
    print("    (가)는 기준서가 허용하는 방식이 아니다. 차이를 보이려고 나란히 놓는다")
    loss_per_return = UNIT_PRICE - UNIT_COST + RECOVERY_COST + VALUE_DECLINE
    full = recognise(0)
    dec_a = full["gross_profit"] - returned * loss_per_return
    jan_a = -remaining * loss_per_return
    print(f"  {'':<26}{'12월 이익':>8}{'1월 이익':>8}{'합계':>8}")
    print(f"  {'(가) 반품 때마다 되돌림':<24}{dec_a:>10,.1f}{jan_a:>10,.1f}{dec_a + jan_a:>10,.1f}")
    print(f"  {'(나) 환불부채로 미리 뺌':<24}{revised['gross_profit']:>10,.1f}{0.0:>10,.1f}"
          f"{revised['gross_profit']:>10,.1f}")
    print("  합계는 같고, 반품 손실이 드러나는 달이 다르다")


if __name__ == "__main__":
    main()
