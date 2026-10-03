"""배당수익률과 배당성향 — 같은 배당금을 주가로 나누느냐, 이익으로 나누느냐.

주당배당금이 같은 세 가상 회사로 두 지표가 서로 다른 것을 재는 것을 보이고,
배당을 그대로 두고 주가만 떨어뜨렸을 때 무엇이 움직이는지 본다. 끝으로 순이익이
줄어도 배당을 유지해 배당성향이 100%를 넘는 회사가 그 돈을 어디서 꺼내는지,
상법 제462조 배당가능이익 한도로 따라간다.
"""
import platform
import sys


def print_definitions() -> None:
    print("[0] 산식")
    print("  배당수익률 = 주당배당금 ÷ 주가                 (주주가 낸 값 대비 받는 돈)")
    print("  배당성향   = 배당금총액 ÷ 당기순이익            (회사가 번 돈 중 나눠 준 몫)")
    print("            = 주당배당금 ÷ 주당순이익(EPS)       (주식 수가 같으면 같은 값)")
    print("  두 지표를 잇는 식: 배당수익률 = 배당성향 ÷ PER   (PER = 주가 ÷ EPS)")
    print()


def print_same_dividend() -> None:
    print("[1] 주당배당금 1,500원으로 같은 세 회사 (단위: 원)")
    companies = [
        # 이름, 주가, EPS, 주당배당금
        ("가나식품", 75_000, 5_000, 1_500),
        ("다라통신", 30_000, 2_000, 1_500),
        ("마바유통", 30_000, 10_000, 1_500),
    ]
    print(f"  {'':10}{'주가':>8}{'EPS':>8}{'주당배당금':>10}{'PER':>8}{'배당수익률':>10}{'배당성향':>9}{'성향÷PER':>10}")
    for name, price, eps, dps in companies:
        per = price / eps
        dividend_yield = dps / price
        payout = dps / eps
        print(f"  {name:10}{price:>8,}{eps:>8,}{dps:>10,}{per:>7.1f}배{dividend_yield:>10.2%}{payout:>9.1%}{payout / per:>10.2%}")
    print("  가나식품·다라통신은 PER 이 같고 성향이 달라 수익률이 갈린다")
    print("  다라통신·마바유통은 수익률이 같고 성향이 75% 대 15% 로 갈린다")
    print()


def print_price_drop() -> None:
    print("[2] 다라통신 — 배당은 그대로, 주가만 40% 떨어지면 (단위: 원)")
    eps, dps = 2_000, 1_500
    print(f"  {'':10}{'주가':>8}{'주당배당금':>10}{'배당수익률':>10}{'배당성향':>9}")
    for label, price in (("하락 전", 30_000), ("하락 후", 18_000)):
        print(f"  {label:10}{price:>8,}{dps:>10,}{dps / price:>10.2%}{dps / eps:>9.1%}")
    print("  회사가 더 나눠 준 것이 아니다. 분모인 주가가 줄어 수익률이 올라갔다")
    print()


def distributable_limit(net_assets: float, capital: float, reserves: float,
                        reserve_to_add: float, unrealized_gain: float) -> float:
    """상법 제462조 제1항: 순자산에서 네 항목을 뺀 금액까지 배당할 수 있다."""
    return net_assets - capital - reserves - reserve_to_add - unrealized_gain


def print_over_100() -> None:
    print("[3] 사아화학 — 순이익이 줄어도 주당배당금 1,000원을 유지한 3년 (단위: 억원)")
    shares = 10_000_000
    dps = 1_000
    dividend_total = dps * shares / 1e8           # 100억
    capital = 50
    capital_reserve = 100
    legal_reserve = 25                              # 자본금의 1/2 에 이미 도달 (상법 제458조)
    unrealized_gain = 0
    retained = 400                                  # 준비금을 뺀 나머지 이익잉여금, 연초
    print(f"  자본금 {capital} · 자본준비금 {capital_reserve} · 이익준비금 {legal_reserve}(한도 도달) · 미실현이익 {unrealized_gain}")
    print(f"  {'연도':6}{'순이익':>7}{'배당':>6}{'배당성향':>10}{'연말 순자산':>11}{'배당가능 한도':>13}{'배당 후 잉여금':>13}")
    for year, net_income in ((1, 125), (2, 40), (3, -30)):
        retained += net_income
        net_assets = capital + capital_reserve + legal_reserve + retained
        # 준비금이 자본금 1/2 에 이르렀으므로 이번 결산기에 더 쌓을 이익준비금은 0
        reserve_to_add = 0 if legal_reserve >= capital / 2 else dividend_total / 10
        limit = distributable_limit(net_assets, capital, capital_reserve + legal_reserve,
                                    reserve_to_add, unrealized_gain)
        payout = f"{dividend_total / net_income:.0%}" if net_income > 0 else "산출 불가"
        retained -= dividend_total
        print(f"  {year}년차{net_income:>8}{dividend_total:>6.0f}{payout:>10}{net_assets:>11.0f}{limit:>13.0f}{retained:>13.0f}")
    print("  2년차는 번 돈 40억보다 많은 100억을 나눠 줬다. 모자란 60억은 과거에 쌓아 둔 잉여금에서 나왔다")
    print("  3년차는 순손실이라 배당성향이 음수가 되어 비율로서 뜻이 없다. 잉여금만 130억 줄었다")
    years_left = retained / (dividend_total + 30)
    print(f"  가정: 3년차와 같은 순손실 30억·배당 100억이 반복되면 남은 잉여금 {retained:.0f}억은 {years_left:.1f}년 치다")
    print()


def main() -> None:
    print(f"Python {platform.python_version()} / {platform.system()}")
    print("회사: 가나식품·다라통신·마바유통·사아화학(모두 가상) / 숫자는 설명용 가정값")
    print()
    print_definitions()
    print_same_dividend()
    print_price_drop()
    print_over_100()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
