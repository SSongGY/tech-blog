"""ETF — 순자산가치(NAV)와 시장가격, 그리고 지수와의 거리.

가상 ETF 하나로 NAV 를 계산하고, 시장가격이 NAV 와 벌어질 때 괴리율과 투자자가
더 낸 돈을 본다. 지정참가회사(AP)의 차익거래가 비용보다 큰 괴리만 메운다는 것을
계산하고, 끝으로 보수와 복제 방식이 다른 두 ETF 로 추적차이와 추적오차가 서로
다른 것을 잰다는 것을 확인한다.
"""
import math
import platform
import random
import statistics
import sys

EOK = 100_000_000  # 1억원
TRADING_DAYS = 252


def print_definitions() -> None:
    print("[0] 산식")
    print("  NAV(1좌)  = (자산 평가액 - 부채) ÷ 발행 좌수")
    print("  괴리율    = (시장가격 - NAV) ÷ NAV")
    print("  추적차이  = 기간 ETF 수익률 - 기간 지수 수익률          (얼마나 뒤처졌나)")
    print("  추적오차  = 일간 (ETF 수익률 - 지수 수익률) 의 표준편차 × √252  (얼마나 들쭉날쭉했나)")
    print()


def print_nav() -> float:
    print("[1] 가나200 ETF 의 NAV (금액은 억원)")
    stocks = 995.0
    cash = 6.2
    accrued_fee = 0.4    # 매일 쌓이고 아직 내지 않은 운용보수
    payable = 0.8        # 결제 전 매수 대금
    units = 10_000_000
    net_assets = stocks + cash - accrued_fee - payable
    nav = net_assets * EOK / units
    print(f"  주식 평가액 {stocks:,.1f} + 현금 {cash:,.1f} - 미지급 보수 {accrued_fee:,.1f} - 미지급 매수대금 {payable:,.1f}")
    print(f"  = 순자산 {net_assets:,.1f}억원 ÷ {units:,}좌 = NAV {nav:,.0f}원")
    print()
    return nav


def print_premium(nav: float) -> None:
    print("[2] 같은 NAV, 다른 시장가격 — 1,000만원어치를 살 때")
    budget = 10_000_000
    cases = [
        ("LP 호가가 촘촘한 시간", 10_010),
        ("LP 호가가 비어 있는 시간", 10_250),
        ("매도 물량이 몰린 시간", 9_900),
    ]
    print(f"  {'상황':24}{'시장가격':>9}{'괴리율':>9}{'산 좌수':>9}{'NAV 로 환산':>13}{'차이':>11}")
    for label, price in cases:
        qty = budget // price
        value_at_nav = qty * nav
        print(f"  {label:24}{price:>9,}{(price - nav) / nav:>+9.2%}{qty:>9,}"
              f"{value_at_nav:>13,.0f}{value_at_nav - qty * price:>+11,.0f}")
    print("  괴리율이 + 인 시점에 사면 NAV 보다 비싸게 산 만큼이 처음부터 빠진 채 시작한다")
    print()


def print_arbitrage(nav: float) -> None:
    print("[3] 지정참가회사(AP)의 차익거래 — 1 설정단위 10만좌, 바스켓 매수·ETF 매도 비용 0.15% 가정")
    unit = 100_000
    cost_rate = 0.0015
    print(f"  {'괴리율':>8}{'ETF 매도 금액':>16}{'바스켓 매수 금액':>18}{'비용':>12}{'손익':>14}")
    for premium in (0.0005, 0.0010, 0.0015, 0.0030, 0.0100):
        price = nav * (1 + premium)
        sell = price * unit
        basket = nav * unit
        cost = (sell + basket) / 2 * cost_rate
        print(f"  {premium:>+8.2%}{sell:>16,.0f}{basket:>18,.0f}{cost:>12,.0f}{sell - basket - cost:>+14,.0f}")
    print("  비용 0.15% 보다 큰 괴리에서만 AP 가 바스켓으로 ETF 를 새로 만들어 판다 → 공급이 늘어 가격이 NAV 로 붙는다")
    print("  그보다 작은 괴리는 메울 이유가 없어 남는다. 할인(-)일 때는 반대로 ETF 를 사서 환매한다")
    print()


def simulate(fee: float, noise: float, cash_weight: float, index_returns: list[float], seed: int) -> list[float]:
    rng = random.Random(seed)
    daily_fee = fee / TRADING_DAYS
    # 현금으로 남은 몫은 지수를 따라가지 않고, 표본추출은 지수와 매일 조금씩 다르게 움직인다
    return [(1 - cash_weight) * r - daily_fee + rng.gauss(0, noise) for r in index_returns]


def cumulative(returns: list[float]) -> float:
    value = 1.0
    for r in returns:
        value *= 1 + r
    return value - 1


def measure(etf_returns: list[float], index_returns: list[float]) -> tuple[float, float]:
    diff = [e - i for e, i in zip(etf_returns, index_returns)]
    tracking_difference = cumulative(etf_returns) - cumulative(index_returns)
    tracking_error = statistics.stdev(diff) * math.sqrt(TRADING_DAYS)
    return tracking_difference, tracking_error


def print_tracking() -> None:
    print("[4] 같은 지수를 따르는 두 ETF — 가상 지수 경로 5개(각 252 거래일)")
    print("  가 ETF: 완전복제, 연 보수 0.50% / 나 ETF: 표본추출(일간 오차 0.06%), 현금 1%, 연 보수 0.05%")
    print(f"  {'경로':>4}{'지수':>9}{'가 추적차이':>12}{'가 추적오차':>12}{'나 추적차이':>12}{'나 추적오차':>12}")
    for path in range(1, 6):
        rng = random.Random(2026 + path)
        index_returns = [rng.gauss(0.0002, 0.010) for _ in range(TRADING_DAYS)]
        etf_a = simulate(0.0050, 0.0, 0.0, index_returns, seed=path)
        etf_b = simulate(0.0005, 0.0006, 0.01, index_returns, seed=100 + path)
        td_a, te_a = measure(etf_a, index_returns)
        td_b, te_b = measure(etf_b, index_returns)
        print(f"  {path:>4}{cumulative(index_returns):>+9.2%}{td_a:>+12.2%}{te_a:>12.2%}{td_b:>+12.2%}{te_b:>12.2%}")
    print("  가 ETF: 매일 같은 만큼 빠지니 추적오차는 0 에 가깝고, 추적차이는 해마다 보수 근처에 머문다")
    print("  나 ETF: 보수는 적지만 매일 지수와 다르게 움직여 추적오차가 크고, 추적차이가 경로마다 흩어진다")
    print()


def print_fee_drag() -> None:
    print("[5] 보수만 다를 때 — 같은 지수 경로를 따른 10년 뒤, 지수 대비 남는 비율")
    print(f"  {'연 보수':>8}{'1년':>9}{'5년':>9}{'10년':>9}")
    for fee in (0.0005, 0.0015, 0.0050, 0.0100):
        cells = "".join(f"{(1 - fee) ** years:>9.2%}" for years in (1, 5, 10))
        print(f"  {fee:>8.2%}{cells}")
    print("  지수가 오르든 내리든 상관없이 보수는 매년 그 비율만큼 순자산을 깎는다")
    print()


def main() -> None:
    print(f"Python {platform.python_version()} / {platform.system()}")
    print("ETF·지수: 가나200 ETF, 가·나 ETF, 가상 지수(모두 가상) / 숫자는 설명용 가정값")
    print()
    print_definitions()
    nav = print_nav()
    print_premium(nav)
    print_arbitrage(nav)
    print_tracking()
    print_fee_drag()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
