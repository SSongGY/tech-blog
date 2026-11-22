"""충당부채의 변제 — 보험금을 부채에서 빼지 않고 자산으로 따로 잡는다
(기업회계기준서 제1037호 문단 29·53~58).

가상 회사 다라물산이 제품 결함 소송에 걸렸다. 배상액 최선의 추정치는 300,
제조물책임보험에서 자기부담금 50 을 뺀 250 을 돌려받을 수 있다. 단위는 억원.
"""

PROVISION = 300.0       # 소송 배상 최선의 추정치 (문단 36)
REIMBURSEMENT = 250.0   # 보험사가 보전할 금액 (보상 300 − 자기부담금 50)
OTHER_LIABILITIES = 800.0
EQUITY = 1_000.0


def reimbursement_asset(expected: float, provision: float, virtually_certain: bool) -> float:
    """문단 53 — 거의 확실할 때만, 충당부채를 넘지 않게."""
    if not virtually_certain:
        return 0.0
    return min(expected, provision)


def section1() -> None:
    print("[1] 보험사 확인 여부에 따른 2026 말 처리 (문단 53·54)")
    print(f"  {'상태':<26}{'충당부채':>8}{'변제자산':>9}{'총액 비용':>9}{'순액 비용':>9}")
    for label, certain in [("보험사가 보상 확인서 발급", True),
                           ("보험사가 면책 사유 검토 중", False)]:
        asset = reimbursement_asset(REIMBURSEMENT, PROVISION, certain)
        print(f"  {label:<26}{PROVISION:>8.1f}{asset:>9.1f}{PROVISION:>9.1f}{PROVISION - asset:>9.1f}")
    print("  충당부채는 어느 경우에도 300 — 변제는 부채를 줄이지 않는다 (문단 56)")
    print("  손익계산서는 변제수익과 상계한 순액 표시를 허용한다 (문단 54)")
    print()


def section2() -> None:
    print("[2] 돌려받을 금액이 충당부채보다 크면 — 자산은 충당부채가 한도 (문단 53)")
    for expected in (250.0, 300.0, 340.0):
        asset = reimbursement_asset(expected, PROVISION, True)
        print(f"  예상 변제 {expected:>6.1f} → 변제자산 {asset:>6.1f}"
              f"  (넘는 {max(expected - PROVISION, 0):.1f} 은 자산으로 잡지 않음)")
    print()


def section3() -> None:
    print("[3] 보험사 확인이 1년 늦어지면 — 같은 사건, 손익이 나뉘는 해 (문단 53)")
    print(f"  {'경우':<18}{'2026':>8}{'2027':>8}{'2028':>8}{'합계':>8}")
    early = [-(PROVISION - REIMBURSEMENT), 0.0, 0.0]
    late = [-PROVISION, REIMBURSEMENT, 0.0]
    for label, pnl in [("2026 확인", early), ("2027 확인", late)]:
        cells = "".join(f"{v:>8.1f}" for v in pnl)
        print(f"  {label:<18}{cells}{sum(pnl):>8.1f}")
    print("  2028 에 배상 300 을 내고 보험금 250 을 받으면 손익 영향은 없다 — 잔액만 정리된다")
    print()


def section4() -> None:
    print("[4] 총액 표시와 순액 표시의 부채비율 (다라물산 자본 1,000, 다른 부채 800)")
    gross_liab = OTHER_LIABILITIES + PROVISION
    net_liab = OTHER_LIABILITIES + PROVISION - REIMBURSEMENT
    print(f"  총액(기준서): 부채 {gross_liab:,.1f} / 자본 {EQUITY:,.1f} = {gross_liab / EQUITY:.0%}"
          f"  · 변제자산 {REIMBURSEMENT:.1f} 은 자산 쪽")
    print(f"  순액(허용 안 됨): 부채 {net_liab:,.1f} / 자본 {EQUITY:,.1f} = {net_liab / EQUITY:.0%}")
    print("  자본은 같다 — 자산과 부채 양쪽에서 같은 250 을 빼느냐 마느냐의 차이다")
    print()


def section5() -> None:
    print("[5] 제삼자와 나눠 지는 의무 (문단 29·57·58)")
    joint_total, partner_share = 500.0, 0.6
    own = joint_total * (1 - partner_share)
    print(f"  연대채무 {joint_total:.1f}, 공동수급사 부담 예상 {partner_share:.0%}"
          f" → 충당부채 {own:.1f} / 우발부채 공시 {joint_total - own:.1f}")
    partner_share_after = 0.2  # 공동수급사의 재무 상태가 나빠졌다고 가정
    own_after = joint_total * (1 - partner_share_after)
    print(f"  공동수급사 부담 예상이 {partner_share_after:.0%} 로 낮아지면"
          f" → 충당부채 {own_after:.1f} (추가 {own_after - own:.1f}, 문단 30)")
    print("  하도급사만 지급 의무를 지고 다라물산은 지급 의무가 없는 몫 → 충당부채에 넣지 않음 (문단 57)")


if __name__ == "__main__":
    section1()
    section2()
    section3()
    section4()
    section5()
