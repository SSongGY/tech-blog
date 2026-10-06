"""공매도 — 빌려서 팔고, 되사서 갚는 흐름과 손익.

가상 종목 가나전자 1,000주를 빌려 10,000원에 판 뒤 여러 가격에서 되사는 경우의
손익을 계산하고, 같은 수량을 산 투자자와 나란히 놓아 손익의 위·아래 한계가 왜
반대인지 본다. 대차 수수료율 연 4%는 계산을 보이려고 둔 가정값이다.
"""
import platform
import sys

SHARES = 1_000
SELL_PRICE = 10_000
FEE_RATE = 0.04            # 가정값. 실제 수수료율은 종목·시기·증권사마다 다르다
COLLATERAL_RATIO = 1.05    # 빌린 주식 평가액의 105%
HOLDING_DAYS = 30


def tick_size(price: int) -> int:
    """유가증권시장 호가가격단위."""
    for upper, tick in ((2_000, 1), (5_000, 5), (20_000, 10), (50_000, 50),
                        (200_000, 100), (500_000, 500)):
        if price < upper:
            return tick
    return 1_000


def borrow_fee(days: int) -> int:
    # 단순화: 차입 시점 가액에 연율을 일할 계산한다
    return round(SHARES * SELL_PRICE * FEE_RATE * days / 365)


def short_pnl(buyback_price: int, days: int = HOLDING_DAYS) -> int:
    return (SELL_PRICE - buyback_price) * SHARES - borrow_fee(days)


def long_pnl(sell_price: int) -> int:
    return (sell_price - SELL_PRICE) * SHARES


def main() -> None:
    print(f"Python {platform.python_version()} · {sys.platform}")
    print()

    print("[1] 흐름 — 빌린다, 판다, 되산다, 갚는다")
    print(f"  D+0   대여자에게서 가나전자 {SHARES:,}주를 빌린다")
    print(f"  D+0   {SELL_PRICE:,}원에 판다 → 매도대금 {SHARES * SELL_PRICE:,}원")
    print(f"  D+{HOLDING_DAYS}  시장에서 {SHARES:,}주를 되산다")
    print(f"  D+{HOLDING_DAYS}  {SHARES:,}주를 대여자에게 돌려준다 · "
          f"대차 수수료 {borrow_fee(HOLDING_DAYS):,}원 (연 {FEE_RATE:.0%} 가정, {HOLDING_DAYS}일)")
    print()

    print(f"[2] 되사는 가격별 손익 — {SHARES:,}주, {SELL_PRICE:,}원 기준, 거래비용·세금 제외")
    print(f"  {'되사는 가격':>10}  {'공매도 손익':>14}  {'같은 수량 매수 손익':>16}")
    for price in (0, 5_000, 8_000, 10_000, 12_000, 20_000, 30_000, 50_000):
        print(f"  {price:>12,}  {short_pnl(price):>+16,}  {long_pnl(price):>+20,}")
    best = short_pnl(0)
    print(f"  공매도 최대 이익: 주가가 0원일 때 {best:+,}원 — 매도대금에서 수수료를 뺀 값이 상한")
    print("  공매도 손실: 되사는 가격에 상한이 없으므로 손실에도 하한이 없다")
    print()

    print(f"[3] 주가에 따라 유지해야 하는 담보 — 빌린 주식 평가액의 {COLLATERAL_RATIO:.0%}")
    for price in (8_000, 10_000, 12_000, 20_000, 30_000):
        required = round(price * SHARES * COLLATERAL_RATIO)
        print(f"  주가 {price:>7,}원  평가액 {price * SHARES:>12,}원  필요 담보 {required:>12,}원")
    print()

    print("[4] 상환기간이 길어지면 쌓이는 수수료 — 기본 90일, 연장해도 총 12개월 이내")
    for days in (30, 90, 180, 365):
        print(f"  {days:>4}일  수수료 {borrow_fee(days):>9,}원  "
              f"주가 그대로일 때 손익 {short_pnl(SELL_PRICE, days):>+10,}원")
    print()

    print("[5] 가격 제한 — 직전 체결가 이하로는 공매도 호가를 낼 수 없다(원칙)")
    for last_price in (9_990, 10_000, 19_990, 49_000):
        tick = tick_size(last_price)
        print(f"  직전 체결가 {last_price:>7,}원 · 호가 단위 {tick:>3}원 → "
              f"공매도 호가는 {last_price + tick:,}원 이상")


if __name__ == "__main__":
    main()
