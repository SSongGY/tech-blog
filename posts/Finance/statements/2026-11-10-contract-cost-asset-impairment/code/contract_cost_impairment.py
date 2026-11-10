"""계약원가 자산의 손상차손과 환입을 계산한다.

가상 회사 가나클라우드가 가상 고객 A사와 5년 구독 계약을 맺고, 계약 체결 수수료 800을
계약체결원가 자산으로 두어 5년 정액 상각한다. 금액 단위는 천원이다.
근거: 기업회계기준서 제1115호 문단 99·101·102·104, 제1037호 문단 66·68·69.
"""

COMMISSION = 800.0
TERM_YEARS = 5
ANNUAL_AMORTISATION = COMMISSION / TERM_YEARS
SERVICE_COST_PER_YEAR = 450.0   # 용역 제공에 직접 관련되는 원가 — 아직 비용으로 인식하지 않은 것


def fmt(value):
    return f"{value:>9,.1f}"


def headroom(fee_per_year, years_left, variable_estimate, collect_rate):
    """문단 101 ⑴ − ⑵. ⑴은 신용위험을 반영해 조정하고, 변동대가 제약은 적용하지 않는다(문단 102)."""
    consideration = (fee_per_year * years_left + variable_estimate) * collect_rate
    costs = SERVICE_COST_PER_YEAR * years_left
    return consideration, costs, consideration - costs


def main():
    print("[1] 계약 조건과 상각 — 손상 전")
    print(f"    수수료 자산 {COMMISSION:,.1f}, {TERM_YEARS}년 정액 상각 → 매년 {ANNUAL_AMORTISATION:,.1f}")
    carrying = COMMISSION - ANNUAL_AMORTISATION * 2
    print(f"    2년차 말 장부금액 {carrying:,.1f}")
    print()

    print("[2] 2년차 말 손상 검사 — A사가 남은 3년 연 구독료를 1,000에서 600으로 낮춤 (문단 101·102)")
    years_left = 3
    cases = [
        ("변동대가 제외 (수익 인식의 제약을 잘못 적용)", 0.0),
        ("변동대가 포함 (문단 102 — 제약을 적용하지 않는다)", 60.0),
    ]
    impairment = 0.0
    for label, variable in cases:
        consideration, costs, room = headroom(600.0, years_left, variable, 0.95)
        loss = max(0.0, carrying - room)
        print(f"  {label}")
        print(f"    ⑴ 받을 대가 ({600.0 * years_left:,.0f} + 초과 사용료 {variable:,.0f}) × 회수율 95% = {consideration:,.1f}")
        print(f"    ⑵ 남은 직접원가 {SERVICE_COST_PER_YEAR:,.0f} × {years_left} = {costs:,.1f}")
        print(f"    한도 ⑴ − ⑵ = {room:,.1f}   장부금액 {carrying:,.1f}   손상차손 {loss:,.1f}")
        impairment = loss
    print()

    print("[3] 같은 시점에 계약 전체는 손실부담계약인가 (제1037호 문단 66·68)")
    consideration, costs, room = headroom(600.0, years_left, 60.0, 0.95)
    print(f"    남은 대가 {consideration:,.1f} > 남은 직접원가 {costs:,.1f} → 손실부담계약 아님, 충당부채 없음")
    print(f"    그래도 수수료 자산 {carrying:,.1f}은 한도 {room:,.1f}를 넘으므로 손상차손 {impairment:,.1f}")
    print()

    print("[4] 손상 후 상각과 3년차 말 환입 (문단 104)")
    after = carrying - impairment
    new_amortisation = after / years_left
    carrying_y3 = after - new_amortisation
    without_impairment_y3 = COMMISSION - ANNUAL_AMORTISATION * 3
    print(f"    손상 후 장부금액 {after:,.1f}, 남은 3년 상각 매년 {new_amortisation:,.1f}")
    print(f"    3년차 말 장부금액 {carrying_y3:,.1f}")
    consideration, costs, room = headroom(900.0, 2, 0.0, 0.98)
    print(f"    3년차 말 상황 개선 — 남은 2년 연 900, 회수율 98%: 한도 {consideration:,.1f} − {costs:,.1f} = {room:,.1f}")
    print(f"    손상이 없었다면 3년차 말 장부금액 (상각 후) {without_impairment_y3:,.1f}")
    reversal = min(room, without_impairment_y3) - carrying_y3
    print(f"    환입 = min({room:,.1f}, {without_impairment_y3:,.1f}) − {carrying_y3:,.1f} = {reversal:,.1f}")
    print()

    print("[5] 연도별 비용 — 수수료 자산 관련")
    print(f"    {'연도':<5}{'상각비':>9}{'손상차손':>9}{'환입':>9}{'연말 장부':>9}")
    rows = [
        (1, ANNUAL_AMORTISATION, 0.0, 0.0),
        (2, ANNUAL_AMORTISATION, impairment, 0.0),
        (3, new_amortisation, 0.0, reversal),
    ]
    balance = COMMISSION
    for year, amort, loss, back in rows:
        balance = balance - amort - loss + back
        print(f"    {year}년차{fmt(amort)}{fmt(loss)}{fmt(back)}{fmt(balance)}")
    for year in (4, 5):
        amort = balance / (TERM_YEARS - year + 1)
        balance -= amort
        print(f"    {year}년차{fmt(amort)}{fmt(0.0)}{fmt(0.0)}{fmt(balance)}")


if __name__ == "__main__":
    main()
