"""전대리스 — 분류 기준은 기초자산이 아니라 사용권자산이다.

가상 회사 가나물산이 사무실 한 층을 10년 빌린 뒤(상위리스), 2년이 지나
그 층을 다라상사에 다시 빌려준다(전대리스). K-IFRS 제1116호 B58 에 따라
전대리스를 사용권자산 기준으로 분류하고, 남은 8년 전부를 전대하는 경우와
3년만 전대하는 경우의 재무상태표와 손익을 계산한다. 표준 라이브러리만 쓴다.
"""

import platform

HEAD_YEARS = 10
HEAD_PAYMENT = 100.0       # 상위리스 연 리스료 (매년 말)
HEAD_RATE = 0.05           # 상위리스 할인율
BUILDING_LIFE = 40         # 건물(기초자산)의 경제적 내용연수
SUBLEASE_START = 2         # 상위리스 2년 차 말에 전대를 시작한다
SUB_PAYMENT = 110.0        # 전대리스 연 리스료 (매년 말)


def annuity_factor(years, rate):
    return sum(1 / (1 + rate) ** t for t in range(1, years + 1))


def head_lease_position(elapsed):
    """경과 연수 말의 상위리스 리스부채와 사용권자산 장부금액."""
    initial = HEAD_PAYMENT * annuity_factor(HEAD_YEARS, HEAD_RATE)
    remaining = HEAD_YEARS - elapsed
    liability = HEAD_PAYMENT * annuity_factor(remaining, HEAD_RATE)
    right_of_use = initial * remaining / HEAD_YEARS
    return initial, liability, right_of_use


def main():
    initial, liability, right_of_use = head_lease_position(SUBLEASE_START)
    remaining = HEAD_YEARS - SUBLEASE_START
    depreciation = initial / HEAD_YEARS

    print("[0] 환경")
    print(f"  Python {platform.python_version()}")
    print("  가상 회사: 가나물산(중간리스제공자), 다라상사(전대리스이용자) — 실재 기업 아님")
    print(f"  상위리스 {HEAD_YEARS}년, 연 {HEAD_PAYMENT:.0f} 후급, 할인율 {HEAD_RATE:.0%}")
    print(f"  전대리스 연 {SUB_PAYMENT:.0f} 후급, 내재이자율을 쉽게 산정할 수 없어 "
          f"상위리스 할인율 사용 (문단 68)")
    print()

    print(f"[1] 전대 시작 시점 ({SUBLEASE_START}년 차 말) 상위리스")
    print(f"  최초 사용권자산·리스부채 {initial:.2f}")
    print(f"  리스부채   {liability:.2f}  (남은 {remaining}년 리스료의 현재가치)")
    print(f"  사용권자산 {right_of_use:.2f}  (= {initial:.2f} × {remaining}/{HEAD_YEARS})")
    print()

    print("[2] 분류 지표 — 리스기간이 경제적 내용연수의 상당 부분인가 (문단 63⑶)")
    print(f"  {'전대 기간':>6} {'기초자산 기준':>12} {'사용권자산 기준':>14}")
    for sub_years in (remaining, 3):
        print(f"  {sub_years:>6}년 {sub_years / BUILDING_LIFE:>14.1%} "
              f"{sub_years / remaining:>16.1%}")
    print(f"  (기초자산 내용연수 {BUILDING_LIFE}년, 사용권자산의 남은 기간 {remaining}년)")
    print("  B58⑵ 에 따라 사용권자산 기준 칸으로 분류한다")
    print()

    # 사례 1: 남은 8년 전부를 전대 → 금융리스
    net_investment = SUB_PAYMENT * annuity_factor(remaining, HEAD_RATE)
    gain = net_investment - right_of_use
    print(f"[3] 사례 1 — 남은 {remaining}년 전부를 전대 (금융리스)")
    print(f"  전대리스 순투자 {net_investment:.2f}  "
          f"(= {SUB_PAYMENT:.0f} × {annuity_factor(remaining, HEAD_RATE):.4f})")
    print(f"  제거하는 사용권자산 {right_of_use:.2f}")
    print(f"  전대 개시일 손익   {gain:+.2f}")
    print(f"  상위리스 리스부채 {liability:.2f} 는 그대로 남는다")
    print()

    # 사례 2: 3년만 전대 → 운용리스
    print("[4] 사례 2 — 3년만 전대 (운용리스)")
    print(f"  사용권자산 {right_of_use:.2f} 와 리스부채 {liability:.2f} 를 그대로 둔다")
    print(f"  전대 리스료는 받을 때마다 리스수익 {SUB_PAYMENT:.2f}")
    print()

    interest = liability * HEAD_RATE
    finance_income = net_investment * HEAD_RATE
    print(f"[5] 전대 첫해 ({SUBLEASE_START + 1}년 차) 손익")
    print(f"  {'항목':<16} {'사례 1 금융':>10} {'사례 2 운용':>10}")
    rows = [
        ("리스수익", 0.0, SUB_PAYMENT),
        ("전대 금융수익", finance_income, 0.0),
        ("감가상각비", 0.0, -depreciation),
        ("상위리스 이자비용", -interest, -interest),
    ]
    totals = [0.0, 0.0]
    for label, case1, case2 in rows:
        totals[0] += case1
        totals[1] += case2
        print(f"  {label:<16} {case1:>12.2f} {case2:>12.2f}")
    print(f"  {'합계':<16} {totals[0]:>12.2f} {totals[1]:>12.2f}")
    print(f"  (사례 1 은 전대 개시일에 이익 {gain:.2f} 를 따로 인식했다)")
    print()

    print("[6] 전대 직후 재무상태표 — 자산과 부채가 함께 남는다")
    print(f"  {'항목':<16} {'사례 1 금융':>10} {'사례 2 운용':>10}")
    print(f"  {'사용권자산':<16} {0.0:>12.2f} {right_of_use:>12.2f}")
    print(f"  {'전대리스 순투자':<16} {net_investment:>12.2f} {0.0:>12.2f}")
    print(f"  {'리스부채':<16} {liability:>12.2f} {liability:>12.2f}")
    print()

    print("[7] 상위리스가 단기리스(문단 6 면제 적용)였다면 (B58⑴)")
    print("  사용권자산이 없으므로 전대 기간과 관계없이 운용리스로 분류한다")


if __name__ == "__main__":
    main()
