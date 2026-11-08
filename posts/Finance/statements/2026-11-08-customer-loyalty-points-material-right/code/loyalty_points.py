"""고객 포인트 — 중요한 권리인 선택권에 거래가격을 배분한다.

가상 회사 다라마트가 한 해 매출 10,000(만원)에 대해 포인트 500을 적립해 준다.
포인트 1점은 다음 구매에서 1만원 할인이다.
기업회계기준서 제1115호 문단 74·76, B40~B42, B46 의 처리를 숫자로 따라간다.
"""

import sys

SALES_PRICE = 10_000.0     # 고객이 낸 대가 = 상품의 개별 판매가격
POINTS_ISSUED = 500        # 적립 포인트 (1점 = 1만원 할인)
DISCOUNT_WITHOUT_OPTION = 0.0   # 포인트 없이도 받을 할인 (B42(1)) — 예제는 없다고 둔다

# 연차별 (그해 사용 포인트, 그해 말 추정한 총 사용 포인트)
REDEMPTIONS = [(240, 400), (130, 420), (50, 420)]


def point_ssp(expected_rate):
    """포인트의 개별 판매가격 추정 (B42) — 받을 할인에서 (1)을 빼고 (2) 행사 가능성을 곱한다."""
    return (POINTS_ISSUED - DISCOUNT_WITHOUT_OPTION) * expected_rate


def allocate(point_value):
    """상대적 개별 판매가격으로 거래가격을 나눈다 (문단 74·76)."""
    total_ssp = SALES_PRICE + point_value
    goods = SALES_PRICE * SALES_PRICE / total_ssp
    return goods, SALES_PRICE - goods


def main():
    print(f"Python {sys.version.split()[0]}")
    print()
    print("[0] 가상 거래 — 다라마트, 1년차 (단위: 만원)")
    print(f"  상품 매출 대가 {SALES_PRICE:,.1f} · 적립 포인트 {POINTS_ISSUED}점 (1점 = 1만원 할인)")
    print()

    first_rate = REDEMPTIONS[0][1] / POINTS_ISSUED
    print("[1] 포인트의 개별 판매가격 — 직접 관측할 수 없어 추정한다 (B42)")
    print(f"  포인트로 받을 할인 {POINTS_ISSUED:,.1f}")
    print(f"  (1) 포인트 없이도 받을 할인 {DISCOUNT_WITHOUT_OPTION:,.1f}")
    print(f"  (2) 행사 가능성 {first_rate:.0%} (적립 {POINTS_ISSUED}점 중 {REDEMPTIONS[0][1]}점 사용 예상)")
    ssp = point_ssp(first_rate)
    print(f"  포인트 개별 판매가격 = ({POINTS_ISSUED} − {DISCOUNT_WITHOUT_OPTION:.0f}) × {first_rate:.0%} = {ssp:,.1f}")
    print()

    print("[2] 상대적 개별 판매가격 배분 (문단 74·76)")
    goods, points = allocate(ssp)
    total_ssp = SALES_PRICE + ssp
    print(f"  {'':<10}{'개별 판매가격':>10}{'비율':>8}{'배분액':>10}")
    print(f"  {'상품':<10}{SALES_PRICE:>14,.1f}{SALES_PRICE / total_ssp:>9.2%}{goods:>11,.1f}")
    print(f"  {'포인트':<10}{ssp:>14,.1f}{ssp / total_ssp:>9.2%}{points:>11,.1f}")
    print(f"  {'합계':<10}{total_ssp:>14,.1f}{1:>9.2%}{SALES_PRICE:>11,.1f}")
    print(f"  판매 시점 수익 {goods:,.1f} · 계약부채 {points:,.1f}")
    print()

    print("[3] 같은 거래, 판단만 다를 때 판매 시점 수익")
    print(f"  {'판단':<34}{'수익':>8}{'계약부채':>8}")
    print(f"  {'마케팅 제안 — 중요한 권리 아님 (B41)':<30}{SALES_PRICE:>10,.1f}{0.0:>10,.1f}")
    for rate in (0.6, 0.8, 1.0):
        g, p = allocate(point_ssp(rate))
        label = f"중요한 권리 — 사용 예상 {rate:.0%}"
        print(f"  {label:<30}{g:>10,.1f}{p:>10,.1f}")
    print("  사용 예상을 낮게 잡을수록 판매 시점 수익이 커진다")
    print()

    print("[4] 포인트 사용에 따라 계약부채를 수익으로 옮긴다 (B40·B46)")
    print("    누적 수익 = 포인트 배분액 × 누적 사용 ÷ 그해 말 추정 총 사용")
    print(f"  {'연차':>4}{'그해 사용':>9}{'누적 사용':>9}{'추정 총사용':>9}"
          f"{'누적 수익':>9}{'그해 수익':>9}{'기말 계약부채':>9}")
    cumulative_used = 0
    recognised = 0.0
    for year, (used, expected_total) in enumerate(REDEMPTIONS, start=1):
        cumulative_used += used
        cumulative_revenue = points * cumulative_used / expected_total
        year_revenue = cumulative_revenue - recognised
        recognised = cumulative_revenue
        print(f"  {year:>4}{used:>12}{cumulative_used:>12}{expected_total:>13}"
              f"{cumulative_revenue:>13,.1f}{year_revenue:>12,.1f}{points - recognised:>14,.1f}")
    print(f"  적립 {POINTS_ISSUED}점 중 사용 {cumulative_used}점 · 미사용 {POINTS_ISSUED - cumulative_used}점은"
          " 사용 패턴에 따라 이미 수익에 들어갔다")


if __name__ == "__main__":
    main()
