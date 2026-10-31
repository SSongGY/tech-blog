"""증거금률이 바꾸는 매수 한도와, 결제일에 돈을 못 채웠을 때 벌어지는 일.

여기 나오는 가나전자는 실재하지 않는 가상 회사다. 주가·예수금·증거금률은 계산
구조를 보이려고 만든 값이고, 실제 종목이나 특정 증권사의 기준이 아니다.

같은 예수금을 두고 증거금률만 바꿔 가며 매수 한도를 세고, 그 한도까지 샀을 때
결제일(T+2)에 모자라는 돈이 얼마인지, 못 채우면 다음 날 몇 주가 팔리는지,
그 처분금액이 모자란 돈과 얼마나 벌어지는지를 단계별로 찍는다.

파이썬 표준 라이브러리만 쓴다.
"""

import math
import sys

CASH = 4_000_000  # 계좌 예수금(원)
PRICE = 10_000  # 가나전자 매수 체결가(원)

# 증거금률. 종목·고객 등급에 따라 증권사가 정한다(유가증권시장 업무규정 제87조
# 제1항에 따라 1998-04-01 부터 회원 자율). 100% 는 미수가 아예 안 생기는 자리다.
MARGIN_RATES = [1.00, 0.40, 0.30, 0.20]

SETTLE_PRICE = 9_000  # 결제일(T+2) 종가 — 반대매매 수량 산정의 기준가격
LOWER_LIMIT = 0.30  # 가격제한폭 ±30%. 하한가 = 기준가격 × 0.7
OVERDUE_RATE = 0.09  # 미수금 연체이자율(연, 가정값). 증권사마다 다르다
FREEZE_DAYS = 30  # 미수동결계좌 지정 기간(매수로 지정된 경우)


def won(x):
    return f"{round(x):>12,}원"


def pct(x):
    return f"{x * 100:g}%"


def section(no, title):
    print()
    print(f"[{no}] {title}")
    print("-" * 68)


def buying_power():
    """증거금률별로 예수금 400만 원이 주문할 수 있는 금액과 수량."""
    section(1, f"예수금 {CASH:,}원으로 살 수 있는 금액 — 증거금률별")
    print(f"{'증거금률':>8} {'주문 가능액':>14} {'수량':>8} {'결제일 부족액':>14}")
    for rate in MARGIN_RATES:
        limit = CASH / rate
        qty = int(limit // PRICE)
        amount = qty * PRICE
        # 증거금으로 낸 돈도 결제대금의 일부다. 결제일에는 전액이 필요하므로
        # 모자란 돈은 매수대금에서 예수금을 뺀 나머지가 된다.
        short = max(0, amount - CASH)
        print(f"{pct(rate):>8} {won(limit)} {qty:>7,}주 {won(short)}")
    print()
    print("  증거금률이 낮을수록 같은 돈으로 더 많이 주문할 수 있고,")
    print("  그만큼 결제일에 채워 넣어야 할 돈이 커진다. 100% 에서만 0원이다.")


def leverage(rate):
    """자기 돈 대비 손익이 몇 배로 움직이는지."""
    qty = int((CASH / rate) // PRICE)
    amount = qty * PRICE
    debt = amount - CASH
    section(2, f"증거금률 {pct(rate)} 로 {qty:,}주를 샀을 때 주가가 움직이면")
    print(f"  매수대금 {amount:,}원 = 예수금 {CASH:,}원 + 결제일에 채울 돈 {debt:,}원")
    print()
    print(f"{'주가':>10} {'평가금액':>14} {'내 몫':>14} {'주가 변동':>10} {'내 몫 변동':>12}")
    for move in (0.10, 0.05, 0.0, -0.05, -0.10, -0.30):
        price = PRICE * (1 + move)
        value = qty * price
        equity = value - debt
        print(
            f"{round(price):>9,}원 {won(value)} {won(equity)}"
            f" {move * 100:>9.0f}% {(equity - CASH) / CASH * 100:>11.1f}%"
        )
    print()
    print(f"  주가 변동이 내 몫에서는 {1 / rate:.1f}배로 나타난다. 오를 때도 내릴 때도 같다.")


def forced_sale(rate):
    """결제일에 못 채웠을 때 다음 날 팔리는 수량과 금액."""
    qty = int((CASH / rate) // PRICE)
    amount = qty * PRICE
    short = amount - CASH
    floor_price = round(SETTLE_PRICE * (1 - LOWER_LIMIT) / 10) * 10  # 호가단위 10원
    need_qty = math.ceil(short / floor_price)
    need_qty = min(need_qty, qty)

    section(3, "결제일(T+2)에 못 채우면 — 다음 날(T+3) 반대매매")
    print(f"  모자란 돈           {short:,}원")
    print(f"  T+2 종가(기준가격)  {SETTLE_PRICE:,}원")
    print(f"  하한가(기준가격×0.7) {floor_price:,}원  ← 수량 산정은 이 값으로 한다")
    print(f"  산정 수량           {need_qty:,}주 (= 모자란 돈 ÷ 하한가, 올림)")
    print()
    print(f"{'실제 체결가':>12} {'처분금액':>14} {'모자란 돈과의 차':>18}")
    for price in (floor_price, 8_000, SETTLE_PRICE, 9_500):
        proceeds = need_qty * price
        print(f"{price:>11,}원 {won(proceeds)} {won(proceeds - short)}")
    print()
    print("  수량은 하한가로 세고 체결은 그날 시장가로 난다. 하한가까지 안 빠지면")
    print("  처분금액이 모자란 돈을 넘는다. 남는 돈은 계좌로 돌아오지만, 그만큼")
    print("  내가 고르지 않은 가격에 더 팔린 것이다.")
    print()
    overdue = short * OVERDUE_RATE / 365
    print(f"  미수금 하루치 연체이자(연 {pct(OVERDUE_RATE)} 가정) {round(overdue):,}원")
    return qty, need_qty


def after_freeze(held_qty, sold_qty):
    """미수동결계좌로 지정된 뒤 30일 동안의 매수 한도."""
    left_qty = held_qty - sold_qty
    left_value = left_qty * SETTLE_PRICE
    section(4, f"미수동결계좌 지정 — {FREEZE_DAYS}일간 증거금 현금 100%")
    print(f"  반대매매 뒤 남은 주식 {left_qty:,}주 (평가 {left_value:,}원)")
    print()
    print(f"{'보유 현금':>12} {'평소(증거금률 40%)':>20} {'동결 중(현금 100%)':>20}")
    for cash in (1_000_000, 3_000_000, 5_000_000):
        normal = cash / 0.40
        frozen = cash
        print(f"{cash:>11,}원 {won(normal)} {won(frozen)}")
    print()
    print("  대용증권은 증거금으로 인정되지 않는다. 남은 주식을 들고 있어도")
    print(f"  {FREEZE_DAYS}일 동안은 현금만큼만 살 수 있다.")


def main():
    print(f"python {sys.version.split()[0]}")
    print("가나전자 — 실재하지 않는 가상 회사. 아래 숫자는 전부 만든 값이다.")
    buying_power()
    leverage(0.40)
    held, sold = forced_sale(0.40)
    after_freeze(held, sold)


if __name__ == "__main__":
    main()
