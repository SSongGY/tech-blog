"""리스 변경 — 별도 리스, 범위 축소, 그 밖의 변경.

가상 회사 다라물산이 사무실 두 층을 10년 빌린 리스를 6년차 초에 바꾼다.
K-IFRS 제1116호 문단 44~46 과 적용사례 17 의 방법으로 네 가지 변경을
계산해 리스부채·사용권자산·당기손익이 어떻게 갈리는지 본다.
표준 라이브러리만 쓴다.
"""

import platform

ORIGINAL_RATE = 0.06      # 리스개시일 증분차입이자율
MODIFICATION_RATE = 0.05  # 변경 유효일 증분차입이자율
PAYMENT_PER_FLOOR = 100.0
FLOORS = 2
LEASE_YEARS = 10
ELAPSED_YEARS = 5
MARKET_PRICE_PER_FLOOR = 100.0  # 변경 유효일 한 층의 개별 가격


def present_value(payment, years, rate):
    # 매년 말 후급 리스료의 현재가치
    return sum(payment / (1 + rate) ** t for t in range(1, years + 1))


def print_row(label, liability, rou, profit, note=""):
    print(f"  {label:<24} {liability:>9.2f} {rou:>9.2f} {profit:>+9.2f}  {note}")


def main():
    print("[0] 환경")
    print(f"  Python {platform.python_version()}")
    print("  가상 회사: 다라물산 (실재 기업 아님)")
    print(f"  사무실 {FLOORS}개 층, 층당 연 {PAYMENT_PER_FLOOR:.0f} × {LEASE_YEARS}년 후급,"
          f" 개시일 할인율 {ORIGINAL_RATE:.0%}")
    print(f"  6년차 초 변경, 변경 유효일 증분차입이자율 {MODIFICATION_RATE:.0%}")
    print()

    annual = PAYMENT_PER_FLOOR * FLOORS
    cost = present_value(annual, LEASE_YEARS, ORIGINAL_RATE)
    remaining = LEASE_YEARS - ELAPSED_YEARS
    liability = present_value(annual, remaining, ORIGINAL_RATE)
    rou = cost * remaining / LEASE_YEARS
    print(f"[1] 리스개시일 리스부채 = 사용권자산 원가 = {cost:.2f}")
    print(f"[2] 6년차 초 변경 직전 장부 (5년 지급·상각 뒤)")
    print(f"  리스부채 {liability:.2f} · 사용권자산 {rou:.2f}")
    print()

    header = f"  {'변경':<24} {'리스부채':>9} {'사용권자산':>9} {'당기손익':>9}  처리"

    # 경로 1: 한 층 추가, 개별 가격대로 → 별도 리스 (문단 44)
    print("[3] 경로 1 — 한 층 추가, 층당 연 100 (개별 가격) → 별도 리스 (문단 44)")
    new_lease = present_value(MARKET_PRICE_PER_FLOOR, remaining, MODIFICATION_RATE)
    print(header)
    print_row("기존 리스", liability, rou, 0.0, "그대로 둔다")
    print_row("새 리스(3층)", new_lease, new_lease, 0.0, "새 개시일, 할인율 5%")
    print_row("합계", liability + new_lease, rou + new_lease, 0.0)
    print()

    # 경로 2: 한 층 추가지만 할인된 대가 → 별도 리스 아님 (문단 45·46⑵)
    discounted = 70.0
    print(f"[4] 경로 2 — 한 층 추가, 층당 연 {discounted:.0f} (개별 가격 아님)"
          " → 별도 리스 아님 (문단 45·46⑵)")
    new_liability = present_value(annual + discounted, remaining, MODIFICATION_RATE)
    adjustment = new_liability - liability
    print(header)
    print_row("변경 뒤", new_liability, rou + adjustment, 0.0,
              f"부채 재측정 {adjustment:+.2f} → 사용권자산 조정")
    print()

    # 경로 3: 한 층 반납 → 범위 축소 (문단 46⑴, 적용사례 17 의 비율 방식)
    reduced_payment = 110.0
    ratio = 1 / FLOORS
    print(f"[5] 경로 3 — 한 층 반납, 남은 한 층 연 {reduced_payment:.0f}"
          " → 범위 축소 (문단 46⑴)")
    rou_cut = rou * ratio
    liability_cut = liability * ratio
    gain = liability_cut - rou_cut
    print(f"  ① 줄어든 면적 비율 {ratio:.0%} 만큼 줄인다")
    print(f"     사용권자산 -{rou_cut:.2f} · 리스부채 -{liability_cut:.2f}"
          f" → 차이 {gain:+.2f} 당기손익")
    kept_liability = liability - liability_cut
    kept_rou = rou - rou_cut
    remeasured = present_value(reduced_payment, remaining, MODIFICATION_RATE)
    adjustment3 = remeasured - kept_liability
    print(f"  ② 남은 리스료 {reduced_payment:.0f} × {remaining}년을 수정 할인율"
          f" {MODIFICATION_RATE:.0%} 로 재측정 {remeasured:.2f}")
    print(f"     남은 부채 {kept_liability:.2f} 와의 차이 {adjustment3:+.2f}"
          " → 사용권자산 조정")
    print(header)
    print_row("변경 뒤", remeasured, kept_rou + adjustment3, gain,
              "비율 감소분만 손익, 재측정분은 자산")
    print()

    # 경로 4: 기간만 3년 연장, 리스료 그대로 → 그 밖의 변경 (문단 45·46⑵)
    extra_years = 3
    print(f"[6] 경로 4 — 두 층 그대로 기간만 {extra_years}년 연장 → 그 밖의 변경"
          " (문단 45·46⑵)")
    extended = present_value(annual, remaining + extra_years, MODIFICATION_RATE)
    adjustment4 = extended - liability
    print(header)
    print_row("변경 뒤", extended, rou + adjustment4, 0.0,
              f"부채 재측정 {adjustment4:+.2f} → 사용권자산 조정")
    print()

    # 범위 축소에서 손익 방향은 부채와 자산 장부금액의 상대 크기로 정해진다
    print("[7] 범위 축소 손익의 크기 — 개시일 할인율별 (같은 계약, 5년 경과)")
    print(f"  {'개시일 할인율':>10} {'리스부채':>9} {'사용권자산':>9} {'50% 축소 손익':>12}")
    for rate in (0.02, 0.04, 0.06, 0.08):
        c = present_value(annual, LEASE_YEARS, rate)
        lia = present_value(annual, remaining, rate)
        asset = c * remaining / LEASE_YEARS
        print(f"  {rate:>10.0%} {lia:>9.2f} {asset:>9.2f} {(lia - asset) * ratio:>+12.2f}")


if __name__ == "__main__":
    main()
