"""시가총액과 주가 — 주가가 높은 주식과 값이 큰 회사는 다르다.

주가만 보면 50만원짜리가 5만원짜리보다 비싸 보인다. 회사 전체에 매겨진 값은
주가에 주식 수를 곱해야 나온다. 두 가상 회사로 이 차이를 보이고, 이익과 견줄 때
주당으로 나누든 회사 전체로 보든 같은 PER이 나오는 것을 확인한다. 끝으로
자기주식이 있으면 어느 주식 수를 곱하느냐에 따라 시가총액과 PER이 갈리는 것을 본다.
"""
import platform
import sys

EOK = 100_000_000  # 1억원


def print_definitions() -> None:
    print("[0] 산식")
    print("  시가총액 = 주가 × 상장주식수                  (시장이 회사 지분 전체에 매긴 값)")
    print("  PER      = 주가 ÷ 주당순이익(EPS)             (주당으로 본 값)")
    print("           = 시가총액 ÷ 당기순이익              (회사 전체로 본 값, 주식 수가 같으면 같다)")
    print()


def print_price_vs_cap() -> None:
    print("[1] 주가와 시가총액 (주가는 원, 시가총액·순이익은 억원)")
    companies = [
        # 이름, 주가, 상장주식수, 당기순이익(원)
        ("가나전자", 50_000, 100_000_000, 4_000 * EOK),
        ("다라바이오", 500_000, 2_000_000, 500 * EOK),
    ]
    print(f"  {'':10}{'주가':>9}{'상장주식수':>14}{'시가총액':>10}{'순이익':>8}{'EPS':>9}{'주가÷EPS':>10}{'시총÷순이익':>12}")
    for name, price, shares, net_income in companies:
        market_cap = price * shares
        eps = net_income / shares
        print(f"  {name:10}{price:>9,}{shares:>14,}{market_cap / EOK:>10,.0f}{net_income / EOK:>8,.0f}"
              f"{eps:>9,.0f}{price / eps:>9.1f}배{market_cap / net_income:>11.1f}배")
    ratio_price = 500_000 / 50_000
    ratio_cap = (50_000 * 100_000_000) / (500_000 * 2_000_000)
    print(f"  주가는 다라바이오가 {ratio_price:.0f}배 높고, 시가총액은 가나전자가 {ratio_cap:.0f}배 크다")
    print("  이익 1원에 매긴 값(PER)은 다라바이오가 더 높다. 주가의 크기와는 다른 이야기다")
    print()


def print_same_company_two_prices() -> None:
    print("[2] 같은 회사를 주식 수만 달리 나눴다면 (가나전자, 시가총액 5조원 고정)")
    market_cap = 50_000 * 100_000_000
    net_income = 4_000 * EOK
    print(f"  {'상장주식수':>14}{'주가':>10}{'EPS':>9}{'PER':>8}")
    for shares in (10_000_000, 100_000_000, 1_000_000_000):
        price = market_cap / shares
        eps = net_income / shares
        print(f"  {shares:>14,}{price:>10,.0f}{eps:>9,.0f}{price / eps:>7.1f}배")
    print("  주식 수가 10배가 되면 주가와 EPS 가 함께 1/10 이 되고 PER 은 그대로다")
    print()


def print_treasury_shares() -> None:
    print("[3] 마바물산 — 자기주식 10% 를 가진 회사 (주가 30,000원, 순이익 270억원)")
    price = 30_000
    listed = 10_000_000
    treasury = 1_000_000
    outstanding = listed - treasury
    net_income = 270 * EOK
    eps = net_income / outstanding  # 주당이익의 분모는 유통보통주식수, 자기주식은 빠진다
    cap_listed = price * listed
    cap_outstanding = price * outstanding
    print(f"  상장주식수 {listed:,} · 자기주식 {treasury:,} · 유통주식수 {outstanding:,}")
    print(f"  EPS = 순이익 ÷ 유통주식수 = {eps:,.0f}원 → 주가 ÷ EPS = {price / eps:.1f}배")
    print(f"  {'기준':22}{'시가총액(억)':>12}{'시총÷순이익':>12}")
    print(f"  {'상장주식수 기준':22}{cap_listed / EOK:>12,.0f}{cap_listed / net_income:>11.1f}배")
    print(f"  {'자기주식 제외 기준':22}{cap_outstanding / EOK:>12,.0f}{cap_outstanding / net_income:>11.1f}배")
    print("  상장주식수로 곱한 시가총액은 회사가 스스로 가진 주식까지 값에 넣는다")
    print("  EPS 쪽 분모와 맞추려면 자기주식을 뺀 시가총액을 써야 두 PER 이 같아진다")
    print()


def main() -> None:
    print(f"Python {platform.python_version()} / {platform.system()}")
    print("회사: 가나전자·다라바이오·마바물산(모두 가상) / 숫자는 설명용 가정값")
    print()
    print_definitions()
    print_price_vs_cap()
    print_same_company_two_prices()
    print_treasury_shares()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
