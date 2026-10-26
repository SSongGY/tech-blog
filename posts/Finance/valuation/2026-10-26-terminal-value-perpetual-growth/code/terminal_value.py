"""DCF 기업가치에서 잔존가치가 차지하는 몫과 영구성장률 가정의 무게를 계산한다.

가상 회사 한들소재의 5년 예측 잉여현금흐름으로 기업가치를 구하고,
(1) 잔존가치가 전체의 몇 %인지, (2) 영구성장률과 할인율을 흔들면 값이 얼마나
움직이는지, (3) 출구배수로 잔존가치를 잡으면 거꾸로 어떤 영구성장률을
가정한 셈이 되는지, (4) 예측 기간을 10년으로 늘리면 몫이 어떻게 바뀌는지를 본다.

금액 단위는 억원이다. 모두 설명용으로 만든 가상 값이다.
"""

import unicodedata

FCF = [120.0, 132.0, 143.0, 151.0, 158.0]   # 1~5년차 잉여현금흐름
WACC = 0.090                                 # 가중평균자본비용
TERMINAL_GROWTH = 0.020                      # 영구성장률
TERMINAL_EBITDA = 225.0                      # 5년차 EBITDA. 출구배수를 환산할 때 쓴다

LATE_FCF = [164.3, 170.9, 177.7, 184.8, 192.2]  # 6~10년차. 연 4% 성장 가정


def width(text: str) -> int:
    """한글은 터미널에서 두 칸을 차지하므로 그만큼 세어 준다."""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def pad(text: str, size: int) -> str:
    return text + " " * max(0, size - width(text))


def rule(char: str = "-", width_: int = 74) -> None:
    print(char * width_)


def present_value(flows: list[float], rate: float) -> float:
    """1년차부터 차례로 할인해 더한다."""
    return sum(cf / (1 + rate) ** (year + 1) for year, cf in enumerate(flows))


def terminal_value(last_fcf: float, rate: float, growth: float) -> float:
    """영구성장 잔존가치. 마지막 해 다음 연도 현금흐름을 (r - g) 로 나눈다."""
    return last_fcf * (1 + growth) / (rate - growth)


def enterprise_value(flows: list[float], rate: float, growth: float) -> tuple[float, float, float]:
    """(예측 기간 현재가치, 잔존가치 현재가치, 합계) 를 돌려준다."""
    pv_forecast = present_value(flows, rate)
    tv = terminal_value(flows[-1], rate, growth)
    pv_terminal = tv / (1 + rate) ** len(flows)
    return pv_forecast, pv_terminal, pv_forecast + pv_terminal


BASE_FORECAST, BASE_TERMINAL, BASE_EV = enterprise_value(FCF, WACC, TERMINAL_GROWTH)


def print_base() -> None:
    print("[1] 한들소재 — 기본 가정으로 구한 기업가치 (단위: 억원)")
    rule()
    print(f"  할인율 {WACC:.1%}   영구성장률 {TERMINAL_GROWTH:.1%}   예측 기간 {len(FCF)}년")
    print()
    print(f"  {'연차':>4}{'FCF':>10}{'할인계수':>12}{'현재가치':>12}")
    for year, cf in enumerate(FCF, start=1):
        factor = 1 / (1 + WACC) ** year
        print(f"  {year:>4}{cf:>10,.1f}{factor:>12,.4f}{cf * factor:>12,.1f}")
    rule()
    tv = terminal_value(FCF[-1], WACC, TERMINAL_GROWTH)
    print(f"  예측 기간 현재가치 합        {BASE_FORECAST:>10,.1f}")
    print(f"  잔존가치 (5년차 말 시점)     {tv:>10,.1f}"
          f"   = {FCF[-1]:,.1f} × {1 + TERMINAL_GROWTH:.2f} ÷ "
          f"({WACC:.3f} - {TERMINAL_GROWTH:.3f})")
    print(f"  잔존가치의 현재가치          {BASE_TERMINAL:>10,.1f}"
          f"   = {tv:,.1f} ÷ {(1 + WACC) ** len(FCF):,.4f}")
    rule()
    print(f"  기업가치 EV                  {BASE_EV:>10,.1f}")
    print(f"  그중 잔존가치가 차지하는 몫   {BASE_TERMINAL / BASE_EV:>9,.1%}")
    print(f"  예측 기간이 차지하는 몫       {BASE_FORECAST / BASE_EV:>9,.1%}")
    print()


def print_growth_sensitivity() -> None:
    print("[2] 영구성장률만 바꿨을 때 — 할인율은 9.0% 고정")
    rule()
    print(f"  {pad('영구성장률', 12)}{'잔존가치':>12}{'TV 현재가치':>14}"
          f"{'EV':>10}{'TV 비중':>10}{'EV 변화':>10}")
    for step in range(1, 8):
        growth = step * 0.005
        pv_f, pv_t, ev = enterprise_value(FCF, WACC, growth)
        tv = terminal_value(FCF[-1], WACC, growth)
        print(f"  {growth:>10.1%}  {tv:>12,.1f}{pv_t:>14,.1f}{ev:>10,.1f}"
              f"{pv_t / ev:>10,.1%}{ev / BASE_EV - 1:>+10,.1%}")
    rule()
    low = enterprise_value(FCF, WACC, 0.015)[2]
    high = enterprise_value(FCF, WACC, 0.025)[2]
    print(f"  기준 2.0% 에서 ±0.5%p 만 움직여도 EV 는 "
          f"{low:,.1f} ~ {high:,.1f} ({low / BASE_EV - 1:+.1%} ~ {high / BASE_EV - 1:+.1%})")
    print(f"  영구성장률이 할인율 {WACC:.1%} 에 닿으면 분모가 0 이 되어 식이 성립하지 않는다")
    print()


def print_grid() -> None:
    print("[3] 할인율 × 영구성장률 — 기업가치 (단위: 억원)")
    rule()
    growths = [0.010, 0.015, 0.020, 0.025, 0.030]
    header = "  " + pad("할인율 \\ g", 12) + "".join(f"{g:>12.1%}" for g in growths)
    print(header)
    for step in range(5):
        rate = 0.080 + step * 0.005
        row = f"  {pad(f'{rate:.1%}', 12)}"
        for growth in growths:
            row += f"{enterprise_value(FCF, rate, growth)[2]:>12,.1f}"
        print(row)
    rule()
    lowest = enterprise_value(FCF, 0.100, 0.010)[2]
    highest = enterprise_value(FCF, 0.080, 0.030)[2]
    print(f"  표의 네 귀퉁이 중 가장 작은 값 {lowest:,.1f}, 가장 큰 값 {highest:,.1f} — "
          f"{highest / lowest:,.2f}배 차이")
    print()


def implied_growth(exit_multiple: float) -> float:
    """출구배수로 잔존가치를 잡았을 때 거꾸로 깔려 있는 영구성장률.

    TV = EBITDA5 × 배수 이므로 TV = FCF5(1+g)/(r-g) 를 g 에 대해 푼다.
    """
    tv = TERMINAL_EBITDA * exit_multiple
    return (tv * WACC - FCF[-1]) / (tv + FCF[-1])


def print_exit_multiple() -> None:
    print("[4] 출구배수로 잔존가치를 잡으면 어떤 영구성장률을 가정한 셈인가")
    rule()
    base_tv = terminal_value(FCF[-1], WACC, TERMINAL_GROWTH)
    print(f"  영구성장 {TERMINAL_GROWTH:.1%} 로 구한 잔존가치 {base_tv:,.1f} 는 "
          f"5년차 EBITDA {TERMINAL_EBITDA:,.1f} 의 {base_tv / TERMINAL_EBITDA:,.2f}배다")
    print()
    print(f"  {pad('출구배수', 10)}{'잔존가치':>12}{'내재 영구성장률':>18}{'EV':>10}")
    for multiple in (6.0, 8.0, 10.0, 12.0, 14.0):
        tv = TERMINAL_EBITDA * multiple
        pv_t = tv / (1 + WACC) ** len(FCF)
        growth = implied_growth(multiple)
        print(f"  {pad(f'{multiple:,.1f}배', 10)}{tv:>12,.1f}{growth:>17,.2%}"
              f"{BASE_FORECAST + pv_t:>10,.1f}")
    rule()
    print("  배수를 낮게 잡는 것은 성장을 낮게 보는 것과 같다. 둘을 함께 쓰면 두 번 깎인다")
    print()


def print_longer_forecast() -> None:
    print("[5] 예측 기간을 10년으로 늘리면 — 6~10년차는 연 4% 성장으로 명시한다")
    rule()
    flows10 = FCF + LATE_FCF
    pv_f, pv_t, ev = enterprise_value(flows10, WACC, TERMINAL_GROWTH)
    print(f"  {pad('예측 기간', 12)}{'예측 PV':>12}{'TV PV':>12}{'EV':>12}{'TV 비중':>10}")
    print(f"  {pad('5년', 12)}{BASE_FORECAST:>12,.1f}{BASE_TERMINAL:>12,.1f}"
          f"{BASE_EV:>12,.1f}{BASE_TERMINAL / BASE_EV:>10,.1%}")
    print(f"  {pad('10년', 12)}{pv_f:>12,.1f}{pv_t:>12,.1f}{ev:>12,.1f}{pv_t / ev:>10,.1%}")
    rule()
    print(f"  TV 비중은 {BASE_TERMINAL / BASE_EV:,.1%} 에서 {pv_t / ev:,.1%} 로 내려간다")
    print(f"  다만 EV 자체가 {BASE_EV:,.1f} 에서 {ev:,.1f} 로 "
          f"{ev / BASE_EV - 1:+,.1%} 움직인다 — 6~10년차를 2% 영구성장이 아니라")
    print("  4% 성장으로 명시했기 때문이다. 가정을 앞으로 당긴 것이지 없앤 것이 아니다")
    print()


def main() -> None:
    print_base()
    print_growth_sensitivity()
    print_grid()
    print_exit_multiple()
    print_longer_forecast()


if __name__ == "__main__":
    main()
