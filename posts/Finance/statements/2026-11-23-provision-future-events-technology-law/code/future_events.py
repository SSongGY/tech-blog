"""충당부채 측정에 넣는 미래사건 — 기업회계기준서 제1037호 문단 48~50·85⑵.

가상 회사 자차화학이 2034 년 말 공장 부지의 오염 토양을 정화해야 한다.
2026 년 말 기준으로 8 년 뒤다. 숫자는 계산 원리를 보이려고 만든 가정이며
단위는 억원, 정화 물량 단위는 천 m³ 다.
"""

DISCOUNT_RATE = 0.04
VOLUME_NOW = 500.0            # 현행 법령 기준으로 정화해야 하는 물량
VOLUME_NEW_LAW = 650.0        # 기준이 강화되면 늘어나는 물량
UNIT_COST_TODAY = 2.0         # 지금 기술로 천 m³ 당 드는 비용
LEARNING_DROP = 0.015         # 전문가가 예측한 경험 축적에 따른 연간 단가 하락
COMPLEXITY_UPLIFT = 0.10      # 지금까지보다 깊은 오염층을 다루는 데 드는 할증
NEW_TECH_DROP = 0.50          # 실험실 단계 신기술이 약속하는 단가 하락


def present_value(amount, years):
    return amount / (1.0 + DISCOUNT_RATE) ** years


def unit_cost(years_ahead, learning=True, complexity=True):
    cost = UNIT_COST_TODAY
    if learning:
        cost *= (1.0 - LEARNING_DROP) ** years_ahead
    if complexity:
        cost *= 1.0 + COMPLEXITY_UPLIFT
    return cost


def section_technology():
    years = 8
    print("[1] 기술에 관한 가정별 2026 말 충당부채 (정화 물량 500, 8년 뒤, 할인율 4%) — 문단 48·49")
    rows = [
        ("현재 단가 그대로", UNIT_COST_TODAY, "—"),
        ("경험 축적에 따른 절감", unit_cost(years, True, False), "반영"),
        ("절감 + 깊은 오염층 할증", unit_cost(years, True, True), "반영"),
        ("실험실 단계 신기술 기대", unit_cost(years, True, True) * (1.0 - NEW_TECH_DROP),
         "반영 안 함"),
    ]
    print(f"  {'가정':<24}{'단가':>7}{'지출 추정':>10}{'현재가치':>10}  문단 49")
    for label, cost, verdict in rows:
        spend = VOLUME_NOW * cost
        print(f"  {label:<20}{cost:>10.3f}{spend:>10.2f}{present_value(spend, years):>10.2f}  {verdict}")
    print("  충분하고 객관적인 증거가 없는 완전히 새로운 기술은 예상하지 않는다")
    print()


def section_law():
    print("[2] 정화 기준을 강화하는 법률 — 언제 측정에 들어가나 (문단 50)")
    cost = unit_cost(8, True, True)            # 단가 가정은 2026 말 판단 그대로 둔다
    states = [
        (2026, 8, "입법예고만 됐다", VOLUME_NOW),
        (2027, 7, "국회 통과·공포, 2029 시행", VOLUME_NEW_LAW),
    ]
    prior = None
    print(f"  {'연말':>4}  {'법률 상태':<20}{'물량':>6}{'지출 추정':>10}{'충당부채':>10}")
    for year, years_left, status, volume in states:
        spend = volume * cost
        pv = present_value(spend, years_left)
        print(f"  {year:>4}  {status:<16}{volume:>8.0f}{spend:>10.2f}{pv:>10.2f}")
        if prior is not None:
            unwind = prior * DISCOUNT_RATE
            law_effect = pv - prior - unwind
            print(f"  2027 증가 {pv - prior:.2f} = 기간 경과 {unwind:.2f} + 법률 반영 {law_effect:.2f}")
        prior = pv
    print("  입법예고 단계의 2026 말에는 현행 기준 물량 500 으로만 측정한다")
    print()


def section_sensitivity():
    years = 8
    print("[3] 주요 가정 공시 — 연간 단가 하락률만 바꿔 본 2026 말 충당부채 (문단 85⑵)")
    base = None
    for drop in (0.0, 0.01, 0.015, 0.02, 0.03):
        cost = UNIT_COST_TODAY * (1.0 - drop) ** years * (1.0 + COMPLEXITY_UPLIFT)
        pv = present_value(VOLUME_NOW * cost, years)
        if drop == LEARNING_DROP:
            base = pv
        print(f"  연 {drop * 100:>3.1f}% 하락 → 충당부채 {pv:>8.2f}")
    print(f"  회사가 택한 1.5% 기준 {base:.2f} — 할인율·물량은 그대로이고 단가 가정만 다르다")


def main():
    section_technology()
    section_law()
    section_sensitivity()


if __name__ == "__main__":
    main()
