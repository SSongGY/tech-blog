"""확정기여제도와 확정급여제도가 재무제표에 남기는 자국을 비교한다.

가상 회사 셋이 해마다 같은 근무원가만큼 퇴직급여를 쌓는다. 가나전자는 확정기여제도라
낸 돈이 곧 비용이다. 다라물산과 마바화학은 확정급여제도이고, 기초 순확정급여부채가
200으로 같다. 다만 다라물산은 확정급여채무와 사외적립자산이 둘 다 크고, 마바화학은
둘 다 작다. 한 해 동안 할인율이 1%p 내려가면 세 회사의 손익·기타포괄손익·재무상태표가
어떻게 갈리는지 계산한다.

단순화: 이자는 기초 잔액에만 붙이고, 기여금 납부와 퇴직금 지급은 기말에 한다고 본다.
확정급여채무는 듀레이션이 12년인 미래 지급액의 현재가치로 보고 할인율 변화를
반영한다. 금액 단위는 억원이고, 법인세 효과는 넣지 않았다.
파이썬 표준 라이브러리만 쓴다.
"""

SERVICE_COST = 100.0       # 한 해 동안 근무로 늘어나는 퇴직급여 (세 회사 동일)
CONTRIBUTION = 100.0       # 한 해 동안 회사가 외부 기금에 내는 돈 (세 회사 동일)
RATE_OPEN = 0.05           # 기초 할인율
RATE_CLOSE = 0.04          # 기말 할인율 (1%p 하락)
DURATION = 12              # 확정급여채무의 듀레이션 (년)
ACTUAL_RETURN = 0.0375     # 사외적립자산의 실제 수익률

# (회사, 기초 확정급여채무, 기초 사외적립자산, 기중 퇴직금 지급액)
DB_COMPANIES = (
    ("다라물산", 1_000.0, 800.0, 60.0),
    ("마바화학", 300.0, 100.0, 20.0),
)


def rate_factor(rate_from, rate_to):
    """같은 미래 지급액을 rate_from 에서 rate_to 로 다시 할인할 때 현재가치가 몇 배가 되는가."""
    return ((1 + rate_from) / (1 + rate_to)) ** DURATION


def roll_forward(dbo_open, assets_open, benefits):
    interest_cost = dbo_open * RATE_OPEN
    interest_income = assets_open * RATE_OPEN
    dbo_before = dbo_open + SERVICE_COST + interest_cost - benefits
    actuarial_loss = dbo_before * (rate_factor(RATE_OPEN, RATE_CLOSE) - 1)
    dbo_close = dbo_before + actuarial_loss

    actual_return = assets_open * ACTUAL_RETURN
    # 순이자에 넣은 기대 몫과 실제 수익의 차이가 재측정요소가 된다
    asset_remeasure = actual_return - interest_income
    assets_close = assets_open + actual_return + CONTRIBUTION - benefits

    return {
        "net_open": dbo_open - assets_open,
        "interest_cost": interest_cost,
        "interest_income": interest_income,
        "net_interest": interest_cost - interest_income,
        "actuarial_loss": actuarial_loss,
        "asset_remeasure": asset_remeasure,
        "dbo_close": dbo_close,
        "assets_close": assets_close,
        "net_close": dbo_close - assets_close,
    }


def section_1():
    print("[1] 확정기여제도 — 가나전자는 낸 돈이 곧 비용이다")
    print(f"    한 해 기여금 {CONTRIBUTION:,.1f} -> 당기 비용 {CONTRIBUTION:,.1f}")
    print(f"    할인율이 {RATE_OPEN:.0%} 에서 {RATE_CLOSE:.0%} 로 바뀌어도 "
          f"재무상태표에 남는 퇴직급여부채: 0.0")
    print("    기금의 운용 결과는 종업원 몫이고 회사의 추가 부담은 없다")
    print()


def section_2(results):
    print("[2] 확정급여제도 — 기초에는 순부채가 같은 두 회사")
    print(f"    {'회사':<10}{'확정급여채무':>12}{'사외적립자산':>12}{'순확정급여부채':>14}")
    for name, dbo, assets, _ in DB_COMPANIES:
        print(f"    {name:<10}{dbo:>12,.1f}{assets:>12,.1f}{dbo - assets:>14,.1f}")
    print("    재무상태표에는 오른쪽 한 줄만 보인다")
    print()


def section_3(results):
    print(f"[3] 한 해 뒤 — 할인율이 {RATE_OPEN:.0%} 에서 {RATE_CLOSE:.0%} 로 내려갔다")
    print(f"    {'':<22}{'다라물산':>12}{'마바화학':>12}")
    rows = (
        ("근무원가 (손익)", lambda r: SERVICE_COST),
        ("순이자 (손익)", lambda r: r["net_interest"]),
        ("  채무 이자원가", lambda r: r["interest_cost"]),
        ("  자산 이자수익", lambda r: -r["interest_income"]),
        ("당기손익 합계", lambda r: SERVICE_COST + r["net_interest"]),
        ("보험수리적손실 (OCI)", lambda r: -r["actuarial_loss"]),
        ("자산 재측정요소 (OCI)", lambda r: r["asset_remeasure"]),
        ("기타포괄손익 합계", lambda r: r["asset_remeasure"] - r["actuarial_loss"]),
    )
    for label, getter in rows:
        values = "".join(f"{getter(results[name]):>12,.1f}" for name, *_ in DB_COMPANIES)
        print(f"    {label:<22}{values}")
    print(f"    가나전자(확정기여)의 당기손익은 {CONTRIBUTION:,.1f}, 기타포괄손익은 0.0")
    print()


def section_4(results):
    print("[4] 기말 재무상태표 — 같은 출발점에서 순부채가 갈렸다")
    print(f"    {'회사':<10}{'확정급여채무':>12}{'사외적립자산':>12}"
          f"{'순확정급여부채':>14}{'기초 대비':>10}")
    for name, *_ in DB_COMPANIES:
        r = results[name]
        print(f"    {name:<10}{r['dbo_close']:>12,.1f}{r['assets_close']:>12,.1f}"
              f"{r['net_close']:>14,.1f}{r['net_close'] - r['net_open']:>+10,.1f}")
    print()


def section_5(results):
    print("[5] 민감도 — 기말 할인율이 다시 움직이면 순부채는 얼마나 흔들리나")
    shifts = (-0.01, -0.005, 0.005, 0.01)
    header = "".join(f"{f'{s:+.1%}p':>11}" for s in shifts)
    print(f"    {'회사':<10}{'기말 순부채':>12}{header}")
    for name, *_ in DB_COMPANIES:
        r = results[name]
        cells = ""
        for s in shifts:
            dbo = r["dbo_close"] * rate_factor(RATE_CLOSE, RATE_CLOSE + s)
            cells += f"{dbo - r['assets_close'] - r['net_close']:>+11,.1f}"
        print(f"    {name:<10}{r['net_close']:>12,.1f}{cells}")
    print("    표의 값은 순부채의 변화량이다. 사외적립자산은 고정하고 채무만 다시 할인했다")


def main():
    results = {name: roll_forward(dbo, assets, benefits)
               for name, dbo, assets, benefits in DB_COMPANIES}
    section_1()
    section_2(results)
    section_3(results)
    section_4(results)
    section_5(results)


if __name__ == "__main__":
    main()
