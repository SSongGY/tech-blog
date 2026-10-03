"""현금흐름할인(DCF) — 미래 현금흐름을 할인율로 오늘 값으로 바꿔 더한다.

가상 회사 자차물류의 5년 예측 잉여현금흐름과 그 뒤의 영구성장 가치(잔존가치)를
할인해 기업가치를 구한다. 할인율을 1%p 바꿨을 때 기업가치·주당가치가 얼마나
움직이는지, 그 움직임의 대부분이 잔존가치에서 나온다는 것을 계산으로 보인다.
예측 현금흐름·성장률·할인율·순차입금은 모두 설명용 가정값이다.
"""
import platform
import sys

FIRST_YEAR_FCF = 100.0      # 1년차 잉여현금흐름(FCFF), 억원
FORECAST_GROWTH = 0.05      # 예측 기간 5년 동안의 연 성장률
FORECAST_YEARS = 5
TERMINAL_GROWTH = 0.02      # 6년차부터 영구히 이어진다고 보는 성장률
BASE_RATE = 0.08            # 기준 할인율(가중평균자본비용 가정)
NET_DEBT = 400.0            # 순차입금 = 차입금 − 현금, 억원
SHARES = 10_000_000


def forecast() -> list[float]:
    return [FIRST_YEAR_FCF * (1 + FORECAST_GROWTH) ** (t - 1) for t in range(1, FORECAST_YEARS + 1)]


def valuation(rate: float, growth: float) -> dict[str, float]:
    flows = forecast()
    pv_forecast = sum(fcf / (1 + rate) ** t for t, fcf in enumerate(flows, start=1))
    # 잔존가치는 5년차 말 시점의 값이므로 5년을 더 할인해야 오늘 값이 된다
    terminal = flows[-1] * (1 + growth) / (rate - growth)
    pv_terminal = terminal / (1 + rate) ** FORECAST_YEARS
    ev = pv_forecast + pv_terminal
    equity = ev - NET_DEBT
    return {
        "pv_forecast": pv_forecast, "terminal": terminal, "pv_terminal": pv_terminal,
        "ev": ev, "equity": equity, "per_share": equity * 1e8 / SHARES,
    }


def print_definitions() -> None:
    print("[0] 산식")
    print("  현재가치(PV)  = t년 뒤 현금흐름 ÷ (1 + 할인율)^t")
    print("  잔존가치(TV)  = 6년차 현금흐름 ÷ (할인율 − 영구성장률)     (5년차 말 시점의 값)")
    print("  기업가치(EV)  = 1~5년차 PV 합 + TV 의 PV")
    print("  주주가치      = EV − 순차입금,  주당가치 = 주주가치 ÷ 발행주식수")
    print(f"  가정: 1년차 FCF {FIRST_YEAR_FCF:.0f}억, 5년간 연 {FORECAST_GROWTH:.0%} 성장, 이후 영구성장 {TERMINAL_GROWTH:.0%},"
          f" 할인율 {BASE_RATE:.0%}, 순차입금 {NET_DEBT:.0f}억, 주식 {SHARES:,}주")
    print()


def print_base_case() -> None:
    print(f"[1] 자차물류 — 할인율 {BASE_RATE:.0%} 에서 연도별 할인 (단위: 억원)")
    print(f"  {'연도':6}{'FCF':>8}{'할인계수':>10}{'현재가치':>10}")
    for t, fcf in enumerate(forecast(), start=1):
        factor = 1 / (1 + BASE_RATE) ** t
        print(f"  {t}년차{fcf:>10.1f}{factor:>10.4f}{fcf * factor:>10.1f}")
    v = valuation(BASE_RATE, TERMINAL_GROWTH)
    factor5 = 1 / (1 + BASE_RATE) ** FORECAST_YEARS
    print(f"  잔존가치{v['terminal']:>8.1f}{factor5:>10.4f}{v['pv_terminal']:>10.1f}   (5년차 말 시점 값을 5년 할인)")
    print()


def print_composition() -> None:
    print("[2] 기업가치는 어디서 나오는가 (할인율 8%, 단위: 억원)")
    v = valuation(BASE_RATE, TERMINAL_GROWTH)
    print(f"  1~5년차 현재가치 합 {v['pv_forecast']:>8.1f}  ({v['pv_forecast'] / v['ev']:.1%})")
    print(f"  잔존가치의 현재가치 {v['pv_terminal']:>8.1f}  ({v['pv_terminal'] / v['ev']:.1%})")
    print(f"  기업가치(EV)        {v['ev']:>8.1f}")
    print(f"  − 순차입금          {NET_DEBT:>8.1f}")
    print(f"  = 주주가치          {v['equity']:>8.1f}   주당 {v['per_share']:,.0f}원")
    print()


def print_rate_change() -> None:
    print("[3] 할인율만 1%p 바꾸면 (영구성장률 2% 고정, 단위: 억원)")
    base = valuation(BASE_RATE, TERMINAL_GROWTH)
    print(f"  {'할인율':6}{'5년 PV합':>9}{'TV의 PV':>9}{'EV':>9}{'EV 변화':>9}{'주주가치':>9}{'주당가치(원)':>12}{'주당 변화':>9}")
    for rate in (0.07, 0.08, 0.09):
        v = valuation(rate, TERMINAL_GROWTH)
        print(f"  {rate:>5.0%} {v['pv_forecast']:>10.1f}{v['pv_terminal']:>9.1f}{v['ev']:>9.1f}"
              f"{v['ev'] / base['ev'] - 1:>+9.1%}{v['equity']:>9.1f}{v['per_share']:>12,.0f}{v['per_share'] / base['per_share'] - 1:>+9.1%}")
    print("  5년 PV합은 몇 % 움직이는 데 그치고, 흔들림의 대부분은 TV 에서 나온다")
    print("  순차입금은 할인율과 무관하게 그대로라 주당가치 변화율이 EV 변화율보다 크다")
    print()


def print_grid() -> None:
    print("[4] 주당가치 민감도 (단위: 원, 행 = 할인율, 열 = 영구성장률)")
    growths = (0.010, 0.015, 0.020, 0.025, 0.030)
    rates = (0.070, 0.075, 0.080, 0.085, 0.090)
    print("  " + f"{'':8}" + "".join(f"{g:>10.1%}" for g in growths))
    for rate in rates:
        row = "".join(f"{valuation(rate, g)['per_share']:>10,.0f}" for g in growths)
        print(f"  {rate:>7.1%} {row}")
    low = valuation(0.090, 0.010)["per_share"]
    high = valuation(0.070, 0.030)["per_share"]
    print(f"  표의 양 끝: {low:,.0f}원 ~ {high:,.0f}원 ({high / low:.1f}배)")
    print()


def print_spread() -> None:
    print("[5] 할인율 − 영구성장률 차이와 잔존가치 배수 (TV = 6년차 FCF × 1 ÷ (r − g))")
    print(f"  {'r − g':>7}{'1 ÷ (r − g)':>14}")
    for spread in (0.07, 0.06, 0.05, 0.04, 0.03):
        print(f"  {spread:>7.0%}{1 / spread:>13.1f}배")
    print("  차이가 작아질수록 같은 1%p 가 배수를 더 크게 바꾼다")
    print()


def main() -> None:
    print(f"Python {platform.python_version()} / {platform.system()}")
    print("회사: 자차물류(가상) / 예측 현금흐름·성장률·할인율·순차입금은 설명용 가정값")
    print()
    print_definitions()
    print_base_case()
    print_composition()
    print_rate_change()
    print_grid()
    print_spread()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
