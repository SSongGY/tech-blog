"""주식 수가 줄 때 자본 항목이 어디로 움직이는지 센다.

가상 회사 `한결소재` 하나를 놓고 세 갈래를 돌린다. 셋 다 발행주식수가 줄지만
자본 항목에 남는 자국이 전부 다르다.

  A. 액면병합  10:1  — 액면금액을 10배로 올린다. 자본금이 그대로다
  B. 무상감자  10:1  — 액면금액은 두고 주식수만 줄인다. 자본금이 줄고 결손을 메운다
  C. 유상감자  20%   — 주식을 사들여 소각하고 주주에게 현금을 돌려준다

실재하는 회사가 아니다. 자본 항목과 주가 전부 지어낸 값이다.
"""

import sys

PAR_VALUE = 500               # 액면금액
SHARES = 20_000_000           # 발행주식총수

# 감자 전 자본 항목 (단위: 원)
BEFORE = {
    "자본금": PAR_VALUE * SHARES,
    "자본잉여금(주식발행초과금)": 5_000_000_000,
    "자본조정(감자차손)": 0,
    "이익잉여금(결손금)": -6_000_000_000,
}
CASH = 6_000_000_000          # 현금및현금성자산
MARKET_PRICE = 1_000          # 감자 전 주가
MY_SHARES = 1_005             # 어느 주주의 보유 주식수


def equity_total(items):
    return sum(items.values())


def print_environment():
    print("[환경]")
    print(f"  Python {sys.version.split()[0]}")
    print()


def print_equity(label, items, shares, par, cash):
    print(f"[{label}]")
    for name, value in items.items():
        print(f"  {name:<24} {value:>18,} 원")
    print(f"  {'-' * 24} {'-' * 18}")
    print(f"  {'자본총계':<24} {equity_total(items):>18,} 원")
    print(f"  {'현금및현금성자산':<24} {cash:>18,} 원")
    print(f"  {'발행주식총수':<24} {shares:>18,} 주")
    print(f"  {'액면금액':<24} {par:>18,} 원")
    print(f"  {'액면총액(= 액면 x 주식수)':<24} {par * shares:>18,} 원")
    print()


def path_a():
    """액면병합: 주식수를 1/10로 줄이면서 액면금액을 10배로 올린다."""
    ratio = 10
    shares = SHARES // ratio
    par = PAR_VALUE * ratio
    items = dict(BEFORE)        # 자본 항목은 한 칸도 바뀌지 않는다
    print_equity("A. 액면병합 10:1 — 액면금액을 10배로 올린다", items, shares, par, CASH)
    print(f"  자본금 변동       {items['자본금'] - BEFORE['자본금']:>18,} 원")
    print(f"  자본총계 변동     {equity_total(items) - equity_total(BEFORE):>18,} 원")
    print(f"  현금 변동         {0:>18,} 원")
    print()
    return shares, par


def path_b():
    """무상감자: 액면금액을 두고 주식수만 줄인다. 자본금이 줄어든 만큼 결손을 메운다."""
    ratio = 10
    shares = SHARES // ratio
    par = PAR_VALUE
    reduced = BEFORE["자본금"] - par * shares

    items = dict(BEFORE)
    items["자본금"] = par * shares

    deficit = -BEFORE["이익잉여금(결손금)"]
    offset = min(reduced, deficit)              # 결손 보전에 쓰는 몫
    items["이익잉여금(결손금)"] = BEFORE["이익잉여금(결손금)"] + offset
    items["자본잉여금(주식발행초과금)"] += reduced - offset   # 남으면 감자차익

    print_equity("B. 무상감자 10:1 — 액면금액을 두고 주식수만 줄인다", items, shares, par, CASH)
    print(f"  자본금 감소액     {reduced:>18,} 원")
    print(f"  결손 보전에 충당  {offset:>18,} 원")
    print(f"  감자차익(자본잉여금 증가) {reduced - offset:>11,} 원")
    print(f"  자본총계 변동     {equity_total(items) - equity_total(BEFORE):>18,} 원")
    print(f"  현금 변동         {0:>18,} 원")
    print()
    return shares, par


def path_c():
    """유상감자: 주식을 사들여 소각하고 주주에게 현금을 돌려준다."""
    cancel_rate = 0.20
    refund_per_share = 1_000                    # 주당 환급금
    cancelled = int(SHARES * cancel_rate)
    shares = SHARES - cancelled
    par = PAR_VALUE

    reduced = PAR_VALUE * cancelled             # 자본금 감소액
    refund = refund_per_share * cancelled       # 주주에게 나가는 현금

    items = dict(BEFORE)
    items["자본금"] = par * shares
    # 환급액이 자본금 감소액보다 크면 그 차액이 감자차손으로 자본에서 차감된다
    items["자본조정(감자차손)"] = -(refund - reduced)
    cash = CASH - refund

    print_equity("C. 유상감자 20% — 소각하고 주당 1,000원을 환급한다", items, shares, par, cash)
    print(f"  소각 주식수       {cancelled:>18,} 주")
    print(f"  자본금 감소액     {reduced:>18,} 원")
    print(f"  주주 환급 총액    {refund:>18,} 원")
    print(f"  감자차손          {refund - reduced:>18,} 원")
    print(f"  자본총계 변동     {equity_total(items) - equity_total(BEFORE):>18,} 원")
    print(f"  현금 변동         {cash - CASH:>18,} 원")
    print()
    return shares, par


def shareholder_view(after):
    """주식 1,005주를 가진 주주가 각 경로에서 무엇을 받는지 센다."""
    print("[주주 한 사람의 장부] 감자 전 1,005주 · 주가 1,000원 · 평가금액 1,005,000원")
    header = (f"  {'경로':<14} {'보유주식':>10} {'단주':>8} {'지분율':>10} "
              f"{'받는 현금':>14} {'이론 주가':>12} {'평가금액+현금':>16}")
    print(header)
    print("  " + "-" * (len(header) - 2))

    before_ratio = MY_SHARES / SHARES
    for label, shares, par, refund_per_share, cancel_rate in after:
        kept = MY_SHARES * shares / SHARES
        whole = int(kept)
        fraction = kept - whole
        # 단주는 매각해 대금을 준다. 이론 주가로 환산한다
        theoretical = MARKET_PRICE * SHARES / shares if refund_per_share == 0 else MARKET_PRICE
        cash_in = int(fraction * theoretical)
        if refund_per_share:
            cancelled_mine = MY_SHARES - whole
            cash_in = cancelled_mine * refund_per_share
            whole = MY_SHARES - cancelled_mine
        ratio = whole / shares
        value = int(whole * theoretical) + cash_in
        print(f"  {label:<14} {whole:>10,} {fraction:>8.1f} {ratio:>9.5%} "
              f"{cash_in:>14,} {theoretical:>12,.0f} {value:>16,}")
    print()
    print(f"  감자 전 지분율 {before_ratio:.5%}")
    print()


def main():
    print_environment()
    print_equity("감자 전 — 가상 회사 한결소재", BEFORE, SHARES, PAR_VALUE, CASH)
    a_shares, a_par = path_a()
    b_shares, b_par = path_b()
    c_shares, c_par = path_c()
    shareholder_view([
        ("A 액면병합", a_shares, a_par, 0, 0.0),
        ("B 무상감자", b_shares, b_par, 0, 0.0),
        ("C 유상감자", c_shares, c_par, 1_000, 0.20),
    ])


if __name__ == "__main__":
    main()
