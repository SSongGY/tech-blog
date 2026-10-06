"""유상증자 — 지분율 희석과 가치 희석을 나눠서 계산한다.

가상 회사 가나전자가 신주 200만 주를 세 가지 방식(주주배정·제3자배정·일반공모)으로
발행할 때, 기존 주주 갑의 지분율과 재산이 어떻게 바뀌는지 계산한다.
이어서 할인율과 발행 규모를 바꿔 가며 기존 1주의 이론 가치가 얼마나 줄어드는지,
주주배정 뒤 비교표시 EPS를 어떤 계수로 고치는지 본다.
"""
import math
import platform
import sys

EOK = 100_000_000  # 1억원

SHARES = 10_000_000      # 증자 전 발행주식수
BASE_PRICE = 10_000      # 기준주가(원)
NEW_SHARES = 2_000_000   # 신주 수 — 증자비율 20%
HOLDER = 1_000_000       # 주주 갑의 보유 주식 — 지분율 10%


def tick_size(price: float) -> int:
    """유가증권시장 호가가격단위 — 가격대별로 주문을 낼 수 있는 최소 간격."""
    for upper, tick in ((2_000, 1), (5_000, 5), (20_000, 10), (50_000, 50),
                        (200_000, 100), (500_000, 500)):
        if price < upper:
            return tick
    return 1_000


def round_up_to_tick(price: float) -> int:
    # 증권의 발행 및 공시 등에 관한 규정 제5-18조: 호가 단위 미만은 절상
    tick = tick_size(price)
    return math.ceil(price / tick) * tick


def ex_rights_price(price: float, shares: int, issue_price: float, new_shares: int) -> float:
    """이론권리락주가 — 증자 전 시가총액과 납입금을 합쳐 늘어난 주식 수로 나눈 값."""
    return (price * shares + issue_price * new_shares) / (shares + new_shares)


def issue_prices() -> dict[str, int]:
    rate = NEW_SHARES / SHARES
    # 주주배정은 할인율을 이론권리락주가에 거는 관행식을 쓴다 — 기준주가에 걸면
    # 권리락 뒤 가격 대비 실제 할인 폭이 공시한 할인율보다 작아진다
    rights = round_up_to_tick(BASE_PRICE * (1 - 0.25) / (1 + rate * 0.25))
    return {
        "주주배정(25%)": rights,
        "제3자배정(10%)": round_up_to_tick(BASE_PRICE * (1 - 0.10)),
        "일반공모(30%)": round_up_to_tick(BASE_PRICE * (1 - 0.30)),
    }


def print_issue_prices() -> dict[str, int]:
    print(f"[1] 가나전자 — 발행주식 {SHARES:,}주, 기준주가 {BASE_PRICE:,}원, 신주 {NEW_SHARES:,}주(증자비율 20%)")
    print(f"  {'방식(할인율)':14}{'발행가':>8}{'이론권리락주가':>14}{'권리락가 대비 할인':>16}{'조달액(억원)':>12}")
    prices = issue_prices()
    for name, issue in prices.items():
        terp = ex_rights_price(BASE_PRICE, SHARES, issue, NEW_SHARES)
        print(f"  {name:14}{issue:>8,}{terp:>14,.2f}{1 - issue / terp:>16.2%}{issue * NEW_SHARES / EOK:>12,.1f}")
    print("  주주배정 발행가 = 기준주가 × (1 − 할인율) / (1 + 증자비율 × 할인율), 호가 단위로 절상")
    print()
    return prices


def print_holder_outcomes(prices: dict[str, int]) -> None:
    print(f"[2] 주주 갑({HOLDER:,}주, 지분율 {HOLDER / SHARES:.2%})의 재산 — 증자 전 {HOLDER * BASE_PRICE / EOK:,.2f}억원")
    print(f"  {'경우':22}{'보유 후':>11}{'지분율 후':>10}{'주식 평가':>10}{'낸 돈':>8}{'받은 돈':>8}{'순재산':>9}{'증감':>8}")
    total = SHARES + NEW_SHARES
    rights = prices["주주배정(25%)"]
    rights_terp = ex_rights_price(BASE_PRICE, SHARES, rights, NEW_SHARES)
    entitled = HOLDER * NEW_SHARES // SHARES
    right_value = rights_terp - rights  # 신주 1주를 싸게 살 권리의 이론 가치
    cases = [
        ("주주배정 — 청약", HOLDER + entitled, rights_terp, entitled * rights, 0),
        ("주주배정 — 권리 매각", HOLDER, rights_terp, 0, entitled * right_value),
        ("주주배정 — 실권", HOLDER, rights_terp, 0, 0),
    ]
    for name in ("제3자배정(10%)", "일반공모(30%)"):
        terp = ex_rights_price(BASE_PRICE, SHARES, prices[name], NEW_SHARES)
        cases.append((name.split("(")[0] + " — 배정 없음", HOLDER, terp, 0, 0))
    before = HOLDER * BASE_PRICE
    for name, held, terp, paid, received in cases:
        value = held * terp
        net = value - paid + received
        print(f"  {name:22}{held:>11,}{held / total:>10.2%}{value / EOK:>10,.2f}{paid / EOK:>8,.2f}"
              f"{received / EOK:>8,.2f}{net / EOK:>9,.2f}{(net - before) / EOK:>+8,.2f}")
    third = prices["제3자배정(10%)"]
    third_terp = ex_rights_price(BASE_PRICE, SHARES, third, NEW_SHARES)
    print(f"  권리 1개의 이론 가치 = {rights_terp:,.2f} − {rights:,} = {right_value:,.2f}원")
    print(f"  제3자배정 인수자가 얻는 차익 = ({third_terp:,.2f} − {third:,}) × {NEW_SHARES:,}주 = "
          f"{(third_terp - third) * NEW_SHARES / EOK:,.2f}억원")
    print()


def print_value_dilution_grid() -> None:
    print("[3] 기존 주주가 신주를 받지 않을 때 1주의 이론 가치 감소율 (발행가 = 기준주가 × (1 − 할인율))")
    rates = (0.10, 0.20, 0.50, 1.00)
    header = "".join(f"{f'증자 {r:.0%}':>11}" for r in rates)
    print(f"  {'할인율':8}{header}")
    for discount in (0.0, 0.10, 0.20, 0.30):
        issue = BASE_PRICE * (1 - discount)
        cells = []
        for rate in rates:
            terp = ex_rights_price(BASE_PRICE, SHARES, issue, int(SHARES * rate))
            cells.append(f"{1 - terp / BASE_PRICE:>11.2%}")
        print(f"  {discount:>6.0%}  " + "".join(cells))
    shares_row = "".join(f"{1 / (1 + r):>11.2%}" for r in rates)
    print(f"  {'남는 지분':7}{shares_row}   ← 참여하지 않은 주주의 지분율이 원래의 몇 %로 줄어드는가")
    print()


def print_eps_adjustment(prices: dict[str, int]) -> None:
    print("[4] 주주배정 뒤 비교표시 EPS — 기업회계기준서 제1033호 부록 A2의 조정계수")
    rights = prices["주주배정(25%)"]
    terp = ex_rights_price(BASE_PRICE, SHARES, rights, NEW_SHARES)
    factor = BASE_PRICE / terp  # 권리행사 직전 공정가치 / 이론적 권리락 공정가치
    prior_income = 100 * EOK
    prior_eps = prior_income / SHARES
    print(f"  조정계수 = {BASE_PRICE:,} / {terp:,.2f} = {factor:.5f}")
    print(f"  전기 EPS(고치기 전) = 100억원 / {SHARES:,}주 = {prior_eps:,.2f}원")
    print(f"  전기 EPS(소급 수정) = 100억원 / ({SHARES:,}주 × {factor:.5f}) = {prior_eps / factor:,.2f}원")
    print(f"  무상 요소에 해당하는 주식 수 = {SHARES * factor - SHARES:,.0f}주")


def main() -> None:
    print(f"Python {platform.python_version()} · {sys.platform}")
    print()
    prices = print_issue_prices()
    print_holder_outcomes(prices)
    print_value_dilution_grid()
    print_eps_adjustment(prices)


if __name__ == "__main__":
    main()
