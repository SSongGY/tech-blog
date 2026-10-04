"""액면분할과 무상증자 — 회사 값은 그대로인데 주식 수만 바뀌는 두 가지.

액면분할은 1주를 여러 주로 쪼개 액면가를 낮춘다. 자본금은 그대로다.
무상증자는 준비금을 자본금으로 옮기고(상법 제461조) 그만큼 새 주식을 나눠 준다.
자본금은 늘고 준비금은 같은 만큼 줄어 자본총계는 그대로다. 두 경우 모두
주주의 지분율과 이론상 시가총액이 유지되는 것을 계산하고, 1주 미만의 단주가 생길 때
지분율이 얼마나 흔들리는지, 비교표시 EPS를 왜 소급해 고치는지 본다.
"""
import platform
import sys

EOK = 100_000_000  # 1억원


def print_equity(label: str, par: int, shares: int, share_premium: float, retained: float) -> None:
    capital = par * shares  # 액면주식의 자본금은 발행주식의 액면총액
    total = capital + share_premium + retained
    print(f"  {label:8}{par:>8,}{shares:>14,}{capital / EOK:>8,.0f}{share_premium / EOK:>10,.0f}"
          f"{retained / EOK:>10,.0f}{total / EOK:>9,.0f}")


def print_equity_header() -> None:
    print(f"  {'':8}{'액면가':>8}{'발행주식수':>14}{'자본금':>8}{'주식발행초과금':>10}{'이익잉여금':>10}{'자본총계':>9}")


def print_split() -> None:
    print("[1] 자차소재 — 1주를 10주로 액면분할 (액면가·주가는 원, 자본 항목은 억원)")
    par, shares = 5_000, 2_000_000
    share_premium, retained = 300 * EOK, 500 * EOK
    print_equity_header()
    print_equity("분할 전", par, shares, share_premium, retained)
    print_equity("분할 후", par // 10, shares * 10, share_premium, retained)
    price = 500_000
    print(f"  이론 주가 {price:,} → {price // 10:,}원 · 시가총액 {price * shares / EOK:,.0f} → "
          f"{price // 10 * shares * 10 / EOK:,.0f}억원")
    holder = 20_000
    print(f"  주주 갑 {holder:,}주({holder / shares:.2%}) → {holder * 10:,}주({holder * 10 / (shares * 10):.2%})")
    print()


def print_bonus_issue() -> None:
    print("[2] 카타산업 — 1주당 1주 무상증자, 주식발행초과금을 자본금으로 전입 (단위 같음)")
    par, shares = 500, 10_000_000
    share_premium, retained = 300 * EOK, 400 * EOK
    ratio = 1.0
    new_shares = int(shares * ratio)
    transfer = par * new_shares  # 새 주식의 액면총액만큼 준비금이 자본금으로 옮겨진다
    print_equity_header()
    print_equity("증자 전", par, shares, share_premium, retained)
    print_equity("증자 후", par, shares + new_shares, share_premium - transfer, retained)
    price = 20_000
    ex_price = price * shares / (shares + new_shares)  # 신주 대가가 0 이므로 값을 늘어난 주식 수로 나눈다
    print(f"  자본금으로 옮긴 금액 {transfer / EOK:,.0f}억원 = 신주 {new_shares:,}주 × 액면 {par}원")
    print(f"  이론 주가 {price:,} → {ex_price:,.0f}원 · 시가총액 {price * shares / EOK:,.0f} → "
          f"{ex_price * (shares + new_shares) / EOK:,.0f}억원")
    print()


def print_fractional_shares() -> None:
    print("[3] 카타산업이 1주당 0.3주를 배정했다면 — 단주가 생길 때 (발행주식 10,000,000주)")
    shares, ratio, price_after = 10_000_000, 0.3, 20_000 / 1.3
    holders = [("갑", 333), ("을", 10), ("병", 1_000_000)]
    # 다른 주주의 단주까지 모두 버림 처리되면 실제 증자 후 주식 수는 13,000,000 보다 조금 적다.
    # 여기서는 지분율이 단주로 흔들리는 크기만 보려고 분모를 13,000,000 으로 둔다.
    total_after = int(shares * (1 + ratio))
    print(f"  {'주주':6}{'보유':>10}{'배정 계산':>12}{'받은 신주':>10}{'단주':>6}{'단주 현금(원)':>13}{'지분율 전':>11}{'지분율 후':>11}")
    for name, held in holders:
        entitled = held * ratio
        received = int(entitled)
        fraction = entitled - received
        cash = fraction * price_after  # 상법 제443조 준용: 단주는 팔아 그 대금을 지급
        before = held / shares
        after = (held + received) / total_after
        print(f"  {name:6}{held:>10,}{entitled:>12,.1f}{received:>10,}{fraction:>6.1f}{cash:>13,.0f}"
              f"{before:>11.5%}{after:>11.5%}")
    print("  단주 현금은 이론 주가 15,385원으로 환산한 값이다. 실제 지급액은 단주를 판 값으로 정해진다")
    print()


def print_eps_restatement() -> None:
    print("[4] 카타산업 — 1:1 무상증자 뒤 비교표시 EPS (순이익 억원, EPS 원)")
    income_prev, income_curr = 100 * EOK, 110 * EOK
    shares_before, shares_after = 10_000_000, 20_000_000
    eps_prev_raw = income_prev / shares_before
    eps_prev_restated = income_prev / shares_after  # K-IFRS 1033 문단 64: 비교기간도 늘어난 주식 수로
    eps_curr = income_curr / shares_after
    print(f"  {'':16}{'순이익':>8}{'주식수':>14}{'EPS':>8}{'당기 대비':>10}")
    print(f"  {'전기(고치기 전)':16}{income_prev / EOK:>8,.0f}{shares_before:>14,}{eps_prev_raw:>8,.0f}"
          f"{eps_curr / eps_prev_raw - 1:>10.1%}")
    print(f"  {'전기(소급 수정)':16}{income_prev / EOK:>8,.0f}{shares_after:>14,}{eps_prev_restated:>8,.0f}"
          f"{eps_curr / eps_prev_restated - 1:>10.1%}")
    print(f"  {'당기':16}{income_curr / EOK:>8,.0f}{shares_after:>14,}{eps_curr:>8,.0f}")
    print("  고치지 않으면 이익이 10% 늘었는데 EPS 가 45% 줄어든 것처럼 보인다")
    print()


def main() -> None:
    print(f"Python {platform.python_version()} / {platform.system()}")
    print("회사: 자차소재·카타산업(모두 가상) / 숫자는 설명용 가정값")
    print()
    print_split()
    print_bonus_issue()
    print_fractional_shares()
    print_eps_restatement()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
