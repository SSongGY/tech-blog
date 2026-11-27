"""리스의 식별과 구성요소 분리 — 같은 운송 계약이 리스인지 용역인지에 따라 숫자가 갈린다.

가상 회사 가나유통이 다라운송과 5년짜리 화물차 운송 계약을 맺는다.
K-IFRS 제1116호 문단 9·B9~B31 의 판단 순서를 네 가지 계약 조건에 적용하고,
리스로 판단되면 문단 13 의 대가 배분과 문단 15 의 간편법을 각각 적용해
재무상태표와 첫해 손익이 어떻게 달라지는지 계산한다. 표준 라이브러리만 쓴다.
"""

import platform

YEARS = 5
ANNUAL_PAYMENT = 120.0        # 계약상 연 대가 (매년 말 지급)
STANDALONE_LEASE = 100.0      # 화물차만 빌릴 때의 개별 가격
STANDALONE_SERVICE = 30.0     # 정비·기사 용역만 살 때의 개별 가격
BORROWING_RATE = 0.06         # 리스이용자의 증분차입이자율


def identify_lease(case):
    """판단 순서를 따라가며 걸린 단계와 결론을 돌려준다 (B9·B13~B19·B24)."""
    steps = []
    if not case["asset_specified"]:
        steps.append("식별되는 자산 없음 (B13)")
        return steps, False
    steps.append("자산이 특정됨 (B13)")
    if case["supplier_can_substitute"]:
        if case["substitution_only_after_date"]:
            # 특정일 이후에만 바꿀 수 있으면 사용기간 내내의 실질적 능력이 아니다
            steps.append("대체권이 특정일 이후에만 생김 → 실질적이지 않음 (B15)")
        elif case["substitution_benefit"] > case["substitution_cost"]:
            steps.append(
                f"대체 효익 {case['substitution_benefit']:.0f} > 원가 "
                f"{case['substitution_cost']:.0f} → 실질적 대체권 (B14)")
            return steps, False
        else:
            steps.append(
                f"대체 효익 {case['substitution_benefit']:.0f} ≤ 원가 "
                f"{case['substitution_cost']:.0f} → 실질적이지 않음 (B14⑵)")
    else:
        steps.append("공급자 대체권 없음")
    if not case["customer_gets_substantially_all_benefits"]:
        steps.append("경제적 효익의 대부분을 얻지 못함 (B21)")
        return steps, False
    steps.append("경제적 효익의 대부분을 얻음 (B21)")
    if not case["customer_directs_how_and_purpose"]:
        steps.append("운행 노선·시간을 공급자가 정함 → 사용 지시권 없음 (B24)")
        return steps, False
    steps.append("운행 노선·시간을 고객이 정함 → 사용 지시권 있음 (B24⑴)")
    return steps, True


def annuity_factor(years, rate):
    return sum(1 / (1 + rate) ** t for t in range(1, years + 1))


def measure(annual_lease_payment):
    """리스부채·사용권자산과 첫해 비용 (개시일에 선급·직접원가 없음)."""
    liability = annual_lease_payment * annuity_factor(YEARS, BORROWING_RATE)
    interest = liability * BORROWING_RATE
    depreciation = liability / YEARS
    return liability, interest, depreciation


CASES = [
    ("A 차량번호 명시, 노선은 가나유통이 정함", dict(
        asset_specified=True, supplier_can_substitute=False,
        substitution_only_after_date=False, substitution_benefit=0,
        substitution_cost=0, customer_gets_substantially_all_benefits=True,
        customer_directs_how_and_purpose=True)),
    ("B 다라운송이 차고지의 같은 차종으로 언제든 교체", dict(
        asset_specified=True, supplier_can_substitute=True,
        substitution_only_after_date=False, substitution_benefit=8,
        substitution_cost=2, customer_gets_substantially_all_benefits=True,
        customer_directs_how_and_purpose=True)),
    ("C 교체는 3년 차부터만 가능", dict(
        asset_specified=True, supplier_can_substitute=True,
        substitution_only_after_date=True, substitution_benefit=8,
        substitution_cost=2, customer_gets_substantially_all_benefits=True,
        customer_directs_how_and_purpose=True)),
    ("D 차량번호 명시, 노선·시간은 다라운송이 정함", dict(
        asset_specified=True, supplier_can_substitute=False,
        substitution_only_after_date=False, substitution_benefit=0,
        substitution_cost=0, customer_gets_substantially_all_benefits=True,
        customer_directs_how_and_purpose=False)),
]


def main():
    print("[0] 환경")
    print(f"  Python {platform.python_version()}")
    print("  가상 회사: 가나유통(고객), 다라운송(공급자) — 실재 기업 아님")
    print(f"  계약 {YEARS}년, 연 대가 {ANNUAL_PAYMENT:.0f} 후급, "
          f"증분차입이자율 {BORROWING_RATE:.0%}")
    print(f"  개별 가격: 화물차 {STANDALONE_LEASE:.0f}, "
          f"정비·기사 용역 {STANDALONE_SERVICE:.0f}")
    print()

    print("[1] 계약 조건별 판단")
    verdicts = {}
    for name, case in CASES:
        steps, is_lease = identify_lease(case)
        verdicts[name[0]] = is_lease
        print(f"  {name}")
        for step in steps:
            print(f"    - {step}")
        print(f"    => {'리스를 포함한다' if is_lease else '리스가 아니다 (용역)'}")
    print()

    total_standalone = STANDALONE_LEASE + STANDALONE_SERVICE
    lease_part = ANNUAL_PAYMENT * STANDALONE_LEASE / total_standalone
    service_part = ANNUAL_PAYMENT - lease_part
    print("[2] 리스요소와 비리스요소에 대가 배분 (문단 13)")
    print(f"  리스요소   {ANNUAL_PAYMENT:.0f} × {STANDALONE_LEASE:.0f}/"
          f"{total_standalone:.0f} = {lease_part:.2f}")
    print(f"  비리스요소 {ANNUAL_PAYMENT:.0f} × {STANDALONE_SERVICE:.0f}/"
          f"{total_standalone:.0f} = {service_part:.2f}")
    print(f"  연금현가계수 ({YEARS}년, {BORROWING_RATE:.0%}) "
          f"{annuity_factor(YEARS, BORROWING_RATE):.4f}")
    print()

    separated = measure(lease_part)
    expedient = measure(ANNUAL_PAYMENT)
    print("[3] 개시일 재무상태표와 첫해 손익")
    header = (f"  {'처리':<22} {'리스부채':>9} {'사용권자산':>9} "
              f"{'감가상각':>8} {'이자':>8} {'용역비용':>8} {'비용 합계':>9}")
    print(header)
    rows = [
        ("용역 (B·D)", 0.0, 0.0, 0.0, ANNUAL_PAYMENT),
        ("리스, 요소 분리 (A·C)", separated[0], separated[2], separated[1], service_part),
        ("리스, 간편법 (문단 15)", expedient[0], expedient[2], expedient[1], 0.0),
    ]
    for label, liability, depreciation, interest, service in rows:
        total = depreciation + interest + service
        print(f"  {label:<22} {liability:>11.2f} {liability:>11.2f} "
              f"{depreciation:>10.2f} {interest:>8.2f} {service:>10.2f} "
              f"{total:>10.2f}")
    # EBITDA 는 감가상각·이자를 빼기 전 이익이므로 용역비용만 줄인다
    print("  EBITDA 를 줄이는 비용은 용역비용 칸뿐이다: "
          f"용역 {ANNUAL_PAYMENT:.2f} / 요소 분리 {service_part:.2f} / 간편법 0.00")
    print()

    print("[4] 5년 합계 비용은 같다 — 시점만 다르다")
    for label, (liability, _, _), service in [
        ("용역", (0.0, 0, 0), ANNUAL_PAYMENT),
        ("리스, 요소 분리", separated, service_part),
        ("리스, 간편법", expedient, 0.0),
    ]:
        balance = liability
        yearly = []
        for _ in range(YEARS):
            interest = balance * BORROWING_RATE
            payment = ANNUAL_PAYMENT - service if liability else 0.0
            balance = balance + interest - payment
            yearly.append(liability / YEARS + interest + service)
        cells = " ".join(f"{v:>7.2f}" for v in yearly)
        print(f"  {label:<14} {cells}   합계 {sum(yearly):.2f}")
    print("  (각 칸은 1~5년 차 비용: 감가상각 + 이자 + 용역비용)")


if __name__ == "__main__":
    main()
