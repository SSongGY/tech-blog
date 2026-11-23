"""충당부채의 할인과 위험 반영 — 기업회계기준서 제1037호 문단 42~47·59·60·84⑸.

가상 회사 마바화학이 10년 뒤 공장 부지를 정화해야 하는 의무를 진다.
숫자는 계산 원리를 보이려고 만든 가정이며 단위는 억원이다.
"""

YEARS = 10
# 정화 비용 결과의 분포. 기댓값이 1,000 이 되도록 잡았다
OUTCOMES = [(800.0, 0.3), (1000.0, 0.4), (1200.0, 0.3)]
# 결과 변동성을 떠안는 대가로 잡은 위험조정 — 문단 43 의 "위험조정"
RISK_ADJUSTMENT = 80.0
# 위험을 뺀 세전 할인율 가정
RISK_FREE_RATE = 0.04


def present_value(amount, rate, years):
    return amount / (1.0 + rate) ** years


def implied_rate(target_pv, amount, years):
    # amount 를 years 동안 할인해 target_pv 가 되는 이율
    return (amount / target_pv) ** (1.0 / years) - 1.0


def section_timing():
    print("[1] 같은 1,000 을 언제 내느냐 — 시간가치 (문단 45·46, 할인율 4%)")
    print(f"  {'지급 시점':>8}  {'현재가치':>9}  {'할인 효과':>9}")
    for years in (0, 1, 3, 5, 10):
        pv = present_value(1000.0, RISK_FREE_RATE, years)
        print(f"  {years:>6}년 뒤  {pv:>9.2f}  {1000.0 - pv:>9.2f}")
    print("  10년 뒤 지급이면 장부에는 3분의 2 남짓만 오른다")
    print()


def section_risk_once():
    expected = sum(amount * prob for amount, prob in OUTCOMES)
    adjusted = expected + RISK_ADJUSTMENT
    pv_cash_flow_way = present_value(adjusted, RISK_FREE_RATE, YEARS)
    rate = implied_rate(pv_cash_flow_way, expected, YEARS)
    pv_rate_way = present_value(expected, rate, YEARS)
    pv_double = present_value(adjusted, rate, YEARS)
    pv_none = present_value(expected, RISK_FREE_RATE, YEARS)

    print("[2] 위험을 어디에 넣느냐 (문단 42·43·47)")
    print(f"  결과 분포 기댓값 {expected:.1f} · 위험조정 {RISK_ADJUSTMENT:.1f}")
    print(f"  {'방법':<34}{'현금흐름':>8}{'할인율':>9}{'충당부채':>10}")
    rows = [
        ("위험 반영 없음", expected, RISK_FREE_RATE, pv_none),
        ("가) 현금흐름에 위험조정", adjusted, RISK_FREE_RATE, pv_cash_flow_way),
        ("나) 할인율에 위험 반영", expected, rate, pv_rate_way),
        ("다) 둘 다 반영 — 이중 조정", adjusted, rate, pv_double),
    ]
    for label, cash, r, pv in rows:
        print(f"  {label:<30}{cash:>10.1f}{r * 100:>8.3f}%{pv:>10.2f}")
    print(f"  가)와 나)는 같은 금액 — 부채의 위험을 할인율로 넣으면 할인율이 {RISK_FREE_RATE * 100:.1f}% 에서 "
          f"{rate * 100:.3f}% 로 낮아진다")
    print(f"  다)는 가)보다 {pv_double - pv_cash_flow_way:.2f} 크다 — 문단 43 이 막는 과대 표시")
    print()
    return adjusted


def section_rate_sensitivity(adjusted):
    print("[3] 할인율만 바꿔 본 충당부채 (위험조정 현금흐름 1,080, 10년 뒤)")
    base = present_value(adjusted, RISK_FREE_RATE, YEARS)
    for rate in (0.02, 0.03, 0.04, 0.06, 0.08):
        pv = present_value(adjusted, rate, YEARS)
        print(f"  할인율 {rate * 100:>3.0f}% → 충당부채 {pv:>8.2f}  (4% 대비 {pv - base:+8.2f})")
    print("  할인율이 높을수록 부채가 작다 — 갚을 사람의 신용이 나쁠수록 부채가 줄어드는 셈이 된다")
    print()


def section_rollforward(adjusted):
    print("[4] 충당부채 변동표 — 기간 경과와 할인율 변동을 나눠 적는다 (문단 59·60·84⑸)")
    opening = present_value(adjusted, RISK_FREE_RATE, YEARS)
    rates = {2026: 0.04, 2027: 0.03, 2028: 0.03}
    print(f"  {'연도':>4}{'기초':>10}{'기간 경과':>10}{'할인율 변동':>12}{'기말':>10}{'기말 할인율':>11}")
    remaining = YEARS
    for year in (2026, 2027, 2028):
        unwind = opening * rates[year]          # 기초 할인율로 1년 증액, 차입원가
        remaining -= 1
        before_change = opening + unwind
        end_rate = 0.03                         # 2026 말부터 시장금리가 내려 3% 로 바뀐다
        closing = present_value(adjusted, end_rate, remaining)
        rate_effect = closing - before_change
        print(f"  {year:>4}{opening:>10.2f}{unwind:>10.2f}{rate_effect:>12.2f}{closing:>10.2f}"
              f"{end_rate * 100:>10.1f}%")
        opening = closing
    print("  2026 말 시장금리가 내려 할인율을 3% 로 바꿨다 — 정화 비용 추정은 그대로다")
    print("  기간 경과분은 차입원가(문단 60), 할인율 변동분은 따로 공시한다(문단 84⑸)")


def main():
    section_timing()
    adjusted = section_risk_once()
    section_rate_sensitivity(adjusted)
    section_rollforward(adjusted)


if __name__ == "__main__":
    main()
