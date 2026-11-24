"""우발자산 — 기업회계기준서 제1037호 문단 31~35·89~90.

가상 회사 가나전자(원고)가 다라물산(피고)에 특허침해 손해배상 300 억원을 청구했다.
같은 소송을 두 회사가 해마다 장부에 어떻게 올리는지 나란히 계산한다.
숫자와 확률은 계산 원리를 보이려고 만든 가정이며 단위는 억원이다.
두 회사가 같은 확률 판단을 한다고 두어, 차이가 기준서 문턱에서만 나오게 했다.
"""

CLAIM = 300.0

# 연말마다의 소송 상태. outcomes 는 (금액, 확률) 이고 settled 는 판결 확정 여부다.
STAGES = [
    (2025, "소 제기, 1심 진행 중", [(300.0, 0.35), (0.0, 0.65)], False),
    (2026, "1심 300 인용, 피고 항소", [(300.0, 0.70), (0.0, 0.30)], False),
    (2027, "항소심 240 으로 감액, 상고 기각 확정", [(240.0, 1.00)], True),
]

# 기준서에는 '희박'의 수치 기준이 없다. 표 [2] 를 그리려고 둔 이 예제만의 가정이다.
REMOTE_BELOW = 0.05


def win_probability(outcomes):
    return sum(p for amount, p in outcomes if amount > 0)


def most_likely(outcomes):
    return max(outcomes, key=lambda item: item[1])[0]


def amount_if_paid(outcomes):
    # 공시하는 재무적 영향은 '지면 얼마인가'다. 패소(0) 를 빼고 가장 가능성 높은 금액을 쓴다
    paying = [item for item in outcomes if item[0] > 0]
    return most_likely(paying) if paying else 0.0


def expected(outcomes):
    return sum(amount * p for amount, p in outcomes)


def plaintiff_view(outcomes, settled):
    """원고 쪽 — 문단 31·33·34·35·89."""
    p = win_probability(outcomes)
    if settled:                          # 문단 33·35 — 실현이 거의 확실하면 우발자산이 아니다
        return "자산 인식", most_likely(outcomes), "—"
    if p > 0.5:                          # 문단 34·89 — 유입 가능성이 높으면 공시
        return "인식 안 함", 0.0, f"우발자산 공시 {amount_if_paid(outcomes):.0f}"
    return "인식 안 함", 0.0, "공시 안 함"


def defendant_view(outcomes, settled):
    """피고 쪽 — 문단 14·23·27·28·86."""
    p = win_probability(outcomes)
    if settled:                          # 금액과 시기가 정해졌으니 충당부채가 아닌 확정 채무
        return "확정 채무", most_likely(outcomes), "—"
    if p > 0.5:                          # 문단 23 — 일어날 가능성이 더 높다
        return "충당부채", most_likely(outcomes), "—"
    if p >= REMOTE_BELOW:                # 문단 28·86 — 희박하지 않으면 공시
        return "인식 안 함", 0.0, f"우발부채 공시 {amount_if_paid(outcomes):.0f}"
    return "인식 안 함", 0.0, "공시 안 함"


def section_timeline():
    print("[1] 같은 소송, 두 회사의 연말 장부 (청구 300) — 문단 23·28·33~35·86·89")
    for year, status, outcomes, settled in STAGES:
        p = win_probability(outcomes)
        print(f"  {year} 말  {status}  (원고 승소 가능성 {p:.0%}, 기댓값 {expected(outcomes):.0f})")
        for name, view in (("가나전자(원고)", plaintiff_view), ("다라물산(피고)", defendant_view)):
            item, amount, note = view(outcomes, settled)
            print(f"    {name}  재무상태표 {item:<6} {amount:>6.0f}   주석 {note}")
    print()


def section_threshold():
    print("[2] 원고 승소 가능성별 처리 — 같은 확률이 양쪽에서 다르게 읽힌다")
    print(f"  ('희박' 기준 {REMOTE_BELOW:.0%} 미만은 이 예제의 가정. 기준서에는 수치가 없다)")
    print(f"  {'승소 가능성':<10}{'원고(가나전자)':<22}{'피고(다라물산)'}")
    for p in (0.03, 0.30, 0.50, 0.51, 0.90, 0.99):
        outcomes = [(CLAIM, p), (0.0, 1.0 - p)]
        a_item, _, a_note = plaintiff_view(outcomes, False)
        d_item, d_amount, d_note = defendant_view(outcomes, False)
        left = a_note if a_item == "인식 안 함" else a_item
        right = f"{d_item} {d_amount:.0f}" if d_amount else d_note
        print(f"  {p:>8.0%}    {left:<18}{right}")
    p_label = "판결 확정"
    a_item, a_amount, _ = plaintiff_view([(CLAIM, 1.0)], True)
    d_item, d_amount, _ = defendant_view([(CLAIM, 1.0)], True)
    print(f"  {p_label:<8}  {a_item} {a_amount:.0f}{'':<9}{d_item} {d_amount:.0f}")
    print()


def section_profit():
    print("[3] 연도별 당기손익 영향 — 합계는 같고 시기가 다르다")
    prev_a = prev_d = 0.0
    total_a = total_d = 0.0
    print(f"  {'연도':>4}{'가나전자':>10}{'다라물산':>10}")
    for year, _, outcomes, settled in STAGES:
        _, a_amount, _ = plaintiff_view(outcomes, settled)
        _, d_amount, _ = defendant_view(outcomes, settled)
        pl_a = a_amount - prev_a          # 자산이 늘면 이익
        pl_d = prev_d - d_amount          # 부채가 늘면 비용, 줄면 환입
        total_a += pl_a
        total_d += pl_d
        prev_a, prev_d = a_amount, d_amount
        print(f"  {year:>4}{pl_a:>+10.0f}{pl_d:>+10.0f}")
    print(f"  {'합계':>3}{total_a:>+10.0f}{total_d:>+10.0f}")
    print("  2028 년 현금 240 이 오가며 미수금·확정 채무가 없어지고 손익은 생기지 않는다")


if __name__ == "__main__":
    section_timeline()
    section_threshold()
    section_profit()
