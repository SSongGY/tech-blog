"""프로그램매매와 차익거래 — 이론가격과 시장가격이 벌어질 때 무엇이 움직이는가.

가상 지수 `가나200`과 그 지수선물을 놓고 세 가지를 계산한다.

1. 보유비용모형으로 선물 이론가격을 구하고, 시장가격과의 괴리를 잰다.
2. 괴리가 왕복 거래비용을 넘는 세 경우에 매수차익·매도차익 중 어느 쪽이
   성립하는지 판정하고, 만기까지 들고 갔을 때의 손익을 센다.
   만기 지수를 두 가지로 바꿔 넣어 손익이 지수와 무관하다는 것을 확인한다.
3. 괴리가 매일 달라질 때 매수차익잔고가 어떻게 쌓이고 만기에 어떻게 풀리는지
   누적해, 만기일에 현물 쪽으로 몰리는 물량을 센다.

실재하는 지수·종목이 아니다. 지수값·이자율·배당·거래비용 전부 지어낸 값이다.
"""

import sys
import unicodedata

# ------------------------------------------------------------ 시장 가정값

SPOT = 420.00          # 가나200 현물 지수
RATE = 0.0320          # 연 무위험이자율. 차입·운용 모두 같은 금리로 둔다
DAYS = 73              # 선물 만기까지 남은 날수
DIVIDEND = 1.40        # 잔존기간에 받을 배당을 지수 포인트로 환산한 값

# 왕복 거래비용. 현물 바스켓 매매수수료·세금과 선물 수수료를 지수 포인트로 환산했다.
# 실제 값은 증권사와 세제에 따라 달라지므로, 임계를 보이려고 둔 가정값이다.
COST = 0.35

# 지수 1포인트의 원화 환산. 계약 단위를 보이려고 둔 가정값이다.
POINT_VALUE = 250_000

# 괴리가 서로 다른 세 경우의 시장 선물가격
CASES = [
    ("고평가", 422.80),
    ("저평가", 420.10),
    ("균형권", 421.40),
]

# 만기까지 다섯 거래일. (잔존일수, 현물지수, 시장 선물가격)
# 마지막 날은 만기일이라 선물과 현물이 같은 값으로 정산된다.
PATH = [
    (5, 420.00, 420.55),
    (4, 418.20, 418.72),
    (3, 422.60, 423.25),
    (2, 424.10, 424.33),
    (0, 423.00, 423.00),
]


def width(text):
    """한글은 터미널에서 두 칸을 차지한다. 그대로 len 을 쓰면 표가 어긋난다."""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def pad(text, size, align=">"):
    space = " " * max(0, size - width(text))
    return space + text if align == ">" else text + space


def print_environment():
    print("[환경]")
    print(f"  Python {sys.version.split()[0]}")
    print()


def theoretical_price(spot, rate, days, dividend):
    """보유비용모형. 현물을 만기까지 들고 가는 비용에서 그동안 받을 배당을 뺀다."""
    carry = spot * rate * days / 365
    return spot + carry - dividend, carry


def print_market():
    fair, carry = theoretical_price(SPOT, RATE, DAYS, DIVIDEND)
    print("[가나200 시장 가정값]")
    rows = [
        ("현물 지수", f"{SPOT:.2f}"),
        ("연 무위험이자율", f"{RATE * 100:.2f} %"),
        ("만기까지 남은 날수", f"{DAYS} 일"),
        ("잔존기간 배당 (지수환산)", f"{DIVIDEND:.2f}"),
        ("왕복 거래비용 (지수환산)", f"{COST:.2f}"),
    ]
    for name, value in rows:
        print(f"  {pad(name, 26, '<')}{pad(value, 10)}")
    print()
    print("[선물 이론가격 = 현물 + 보유비용 - 배당]")
    print(f"  보유비용 = {SPOT:.2f} x {RATE:.4f} x {DAYS}/365 = {carry:>8.3f}")
    print(f"  이론가격 = {SPOT:.2f} + {carry:.3f} - {DIVIDEND:.2f} = {fair:>8.3f}")
    print(f"  이론베이시스 = 이론가격 - 현물 = {fair - SPOT:>8.3f}")
    print()
    return fair


def print_cases(fair):
    """괴리를 재고 어느 차익거래가 성립하는지 판정한다."""
    print("[시장 선물가격별 괴리와 판정]")
    widths = [(6, "구분"), (10, "시장선물"), (13, "시장베이시스"), (9, "괴리"), (9, "괴리율")]
    header = "  " + "".join(pad(name, size) for size, name in widths) + "  판정"
    print(header)
    print("  " + "-" * (width(header) + 30))
    for label, futures in CASES:
        basis = futures - SPOT
        gap = futures - fair
        gap_rate = gap / fair * 100
        if gap > COST:
            verdict = "매수차익거래 (현물매수 + 선물매도)"
        elif -gap > COST:
            verdict = "매도차익거래 (현물매도 + 선물매수)"
        else:
            verdict = "진입 안 함 (괴리가 거래비용 미만)"
        print("  " + pad(label, 6) + f"{futures:>10.2f}{basis:>13.3f}"
              f"{gap:>9.3f}{gap_rate:>8.3f}%  {verdict}")
    print()


def buy_arbitrage_pnl(futures, terminal_spot):
    """매수차익거래를 만기까지 보유했을 때의 손익을 항목별로 돌려준다.

    현물을 사고 선물을 팔았으므로 만기 지수가 오르면 현물에서 벌고 선물에서
    같은 크기를 잃는다. 남는 것은 진입 시점에 이미 정해진 값뿐이다.
    """
    spot_pnl = terminal_spot - SPOT              # 현물 매수 손익
    futures_pnl = futures - terminal_spot        # 선물 매도 손익
    funding = SPOT * RATE * DAYS / 365           # 현물 매수대금 조달비용
    return {
        "현물 손익": spot_pnl,
        "선물 손익": futures_pnl,
        "배당 수취": DIVIDEND,
        "조달비용": -funding,
        "거래비용": -COST,
    }


def sell_arbitrage_pnl(futures, terminal_spot):
    """매도차익거래. 현물을 팔아 받은 대금을 만기까지 굴리고 배당은 포기한다."""
    spot_pnl = SPOT - terminal_spot
    futures_pnl = terminal_spot - futures
    interest = SPOT * RATE * DAYS / 365
    return {
        "현물 손익": spot_pnl,
        "선물 손익": futures_pnl,
        "배당 포기": -DIVIDEND,
        "운용수익": interest,
        "거래비용": -COST,
    }


def print_pnl(title, legs_by_terminal, fair, futures):
    print(f"[{title}]")
    print(f"  진입 시 시장선물 {futures:.2f} / 이론가격 {fair:.3f} / "
          f"괴리 {futures - fair:+.3f}")
    names = list(next(iter(legs_by_terminal.values())).keys())
    head = "  " + pad("항목", 12, "<") + "".join(
        pad(f"만기지수 {t:.2f}", 18) for t in legs_by_terminal)
    rule = "  " + "-" * (width(head) - 2)
    print(head)
    print(rule)
    for name in names:
        row = "  " + pad(name, 12, "<")
        for legs in legs_by_terminal.values():
            row += f"{legs[name]:>18.3f}"
        print(row)
    print(rule)
    total_row = "  " + pad("합계", 12, "<")
    for legs in legs_by_terminal.values():
        total_row += f"{sum(legs.values()):>18.3f}"
    print(total_row)
    one = sum(next(iter(legs_by_terminal.values())).values())
    print(f"  1계약 손익 = {one:.3f} 포인트 x {POINT_VALUE:,}원 = {one * POINT_VALUE:,.0f}원")
    print()


def print_balance_path(fair_rate, dividend_rate):
    """괴리가 날마다 달라질 때 매수차익잔고가 쌓였다가 만기에 풀리는 과정."""
    print("[매수차익잔고 — 괴리가 비용을 넘을 때 쌓고 만기에 전부 푼다]")
    widths = [(8, "잔존일"), (9, "현물"), (9, "선물"), (10, "이론가"), (9, "괴리"),
              (10, "신규진입"), (9, "청산"), (9, "잔고")]
    header = "  " + "".join(pad(name, size) for size, name in widths)
    print(header)
    print("  " + "-" * (width(header) - 2))
    balance = 0.0           # 계약 수 기준 매수차익잔고
    spot_flow = []
    for days, spot, futures in PATH:
        fair = spot + spot * fair_rate * days / 365 - dividend_rate * days / 365
        gap = futures - fair
        entry = 0.0
        unwind = 0.0
        if days == 0:
            unwind = balance            # 만기에는 잔고를 전부 청산한다
            balance = 0.0
        elif gap > COST:
            entry = round(gap / COST, 1)  # 괴리가 클수록 많이 들어간다고 둔 가정
            balance += entry
        elif gap < -COST and balance > 0:
            unwind = min(balance, round(-gap / COST, 1))
            balance -= unwind
        spot_flow.append((days, entry, unwind))
        print(f"  {days:>8d}{spot:>9.2f}{futures:>9.2f}{fair:>10.3f}{gap:>9.3f}"
              f"{entry:>10.1f}{unwind:>9.1f}{balance:>9.1f}")
    print()
    print("  잔고 1계약은 현물 바스켓 매수 1단위에 대응한다.")
    print("  신규진입은 현물 매수, 청산은 현물 매도로 시장에 나간다.")
    for days, entry, unwind in spot_flow:
        if unwind:
            label = "만기 청산" if days == 0 else "괴리 역전 청산"
            print(f"    잔존 {days}일 — {label}: 현물 매도 {unwind:.1f} 단위 "
                  f"({unwind * POINT_VALUE * PATH[0][1] / 100:,.0f}원 규모)")
    print()


def main():
    print_environment()
    fair = print_market()
    print_cases(fair)

    high = CASES[0][1]
    print_pnl(
        "매수차익거래를 만기까지 보유 — 만기 지수를 바꿔도 손익이 같다",
        {390.00: buy_arbitrage_pnl(high, 390.00),
         450.00: buy_arbitrage_pnl(high, 450.00)},
        fair, high,
    )

    low = CASES[1][1]
    print_pnl(
        "매도차익거래를 만기까지 보유",
        {390.00: sell_arbitrage_pnl(low, 390.00),
         450.00: sell_arbitrage_pnl(low, 450.00)},
        fair, low,
    )

    flat = CASES[2][1]
    legs = buy_arbitrage_pnl(flat, 420.00)
    print("[균형권에서 억지로 들어갔을 때]")
    print(f"  시장선물 {flat:.2f} / 괴리 {flat - fair:+.3f} / "
          f"왕복 거래비용 {COST:.2f}")
    print(f"  합계 = {sum(legs.values()):+.3f} 포인트 — "
          f"괴리가 비용을 못 덮어 손실로 끝난다.")
    print()

    # 경로 계산에서는 배당을 연율로 환산해 잔존일수에 비례시킨다.
    print_balance_path(RATE, DIVIDEND * 365 / DAYS)


if __name__ == "__main__":
    main()
