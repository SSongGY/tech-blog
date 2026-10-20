"""호가 스프레드가 왕복 거래 비용에 얼마를 보태는지 계산한다.

두 가상 종목은 현재가대가 같아 호가가격단위도 같지만, 호가에 깔린 잔량과
비어 있는 호가의 수가 다르다. 같은 수량을 시장가로 사고팔아 체결 단가를
비교하면 그 차이가 그대로 비용으로 나온다.
"""

# 코스닥시장 호가가격단위 (KRX, Basic Facts about Trading System)
TICK_TABLE = [
    (2_000, 1),
    (5_000, 5),
    (20_000, 10),
    (50_000, 50),
    (200_000, 100),
    (500_000, 500),
    (None, 1_000),
]

# 매도 시에만 붙는 증권거래세 (코스닥, 2026-01-01 이후 양도분)
TAX_RATE = 0.0020
# 위탁수수료는 증권사·계좌마다 다르므로 가정값이다. 온라인 주식 계좌에서
# 흔히 보이는 수준 하나를 골라 양쪽 종목에 똑같이 적용한다.
FEE_RATE = 0.00015


def tick_size(price):
    for upper, unit in TICK_TABLE:
        if upper is None or price < upper:
            return unit


def walk(book, quantity):
    """호가를 좋은 가격부터 훑어 체결 단가와 대금을 구한다."""
    filled, amount, steps = 0, 0, []
    for price, resting in book:
        take = min(resting, quantity - filled)
        if take <= 0:
            break
        filled += take
        amount += take * price
        steps.append((price, take, take * price))
    return filled, amount, steps


def round_trip(name, asks, bids, quantity):
    bought, buy_amount, buy_steps = walk(asks, quantity)
    sold, sell_amount, sell_steps = walk(bids, quantity)
    assert bought == sold == quantity, f"{name}: 호가 잔량이 모자라 전량 체결되지 않는다"

    fee = round(buy_amount * FEE_RATE) + round(sell_amount * FEE_RATE)
    tax = round(sell_amount * TAX_RATE)
    slip = buy_amount - sell_amount
    total = slip + fee + tax
    return {
        "name": name,
        "best_ask": asks[0][0],
        "best_bid": bids[0][0],
        "buy_amount": buy_amount,
        "sell_amount": sell_amount,
        "buy_avg": buy_amount / quantity,
        "sell_avg": sell_amount / quantity,
        "buy_steps": buy_steps,
        "sell_steps": sell_steps,
        "slip": slip,
        "fee": fee,
        "tax": tax,
        "total": total,
        "cost_rate": total / buy_amount,
    }


def print_book(name, asks, bids):
    print(f"[{name}] 호가창 — 호가가격단위 {tick_size(asks[0][0]):,}원")
    print(f"  {'구분':<6}{'호가':>12}{'잔량(주)':>12}")
    for price, resting in reversed(asks):
        print(f"  {'매도':<6}{price:>12,}{resting:>12,}")
    print(f"  {'-' * 30}")
    for price, resting in bids:
        print(f"  {'매수':<6}{price:>12,}{resting:>12,}")
    spread = asks[0][0] - bids[0][0]
    mid = (asks[0][0] + bids[0][0]) / 2
    print(f"  최우선 스프레드 {spread:,}원 (중간가 대비 {spread / mid * 100:.3f}%)")
    print()


def print_fills(label, steps):
    print(f"  {label}")
    for price, qty, amount in steps:
        print(f"    {price:>10,}원 × {qty:>5,}주 = {amount:>12,}원")


GANA_ASKS = [(24_000, 1_800), (24_050, 2_100), (24_100, 1_700), (24_150, 2_400), (24_200, 1_900)]
GANA_BIDS = [(23_950, 2_000), (23_900, 1_800), (23_850, 2_300), (23_800, 1_600), (23_750, 2_100)]

DARA_ASKS = [(24_100, 60), (24_250, 80), (24_400, 70), (24_600, 90), (24_800, 100)]
DARA_BIDS = [(23_800, 70), (23_650, 60), (23_500, 90), (23_300, 80), (23_100, 100)]

QUANTITY = 300

print("=" * 64)
print("1. 가격대별 호가가격단위와 그 비율")
print("=" * 64)
print(f"  {'주가':>12}{'호가단위':>10}{'주가 대비':>12}")
for upper, _ in TICK_TABLE:
    if upper is None:
        continue
    for price in (upper - 1, upper):
        unit = tick_size(price)
        print(f"  {price:>12,}{unit:>10,}{unit / price * 100:>11.3f}%")
print()

print("=" * 64)
print("2. 두 가상 종목의 호가창")
print("=" * 64)
print_book("가나전자", GANA_ASKS, GANA_BIDS)
print_book("다라정밀", DARA_ASKS, DARA_BIDS)

print("=" * 64)
print(f"3. {QUANTITY}주를 시장가로 사고 바로 되판다")
print("=" * 64)
results = [
    round_trip("가나전자", GANA_ASKS, GANA_BIDS, QUANTITY),
    round_trip("다라정밀", DARA_ASKS, DARA_BIDS, QUANTITY),
]
for r in results:
    print(f"[{r['name']}]")
    print_fills("매수 체결", r["buy_steps"])
    print(f"    매수 대금 {r['buy_amount']:,}원 · 평균 단가 {r['buy_avg']:,.2f}원")
    print_fills("매도 체결", r["sell_steps"])
    print(f"    매도 대금 {r['sell_amount']:,}원 · 평균 단가 {r['sell_avg']:,.2f}원")
    print()

print("=" * 64)
print("4. 왕복 비용 분해")
print("=" * 64)
print(f"  {'항목':<16}{'가나전자':>14}{'다라정밀':>14}")
for key, label in [("slip", "스프레드·슬리피지"), ("fee", "위탁수수료(가정)"), ("tax", "증권거래세"), ("total", "합계")]:
    print(f"  {label:<16}{results[0][key]:>13,}원{results[1][key]:>13,}원")
print(f"  {'매수대금 대비':<16}{results[0]['cost_rate'] * 100:>13.3f}%{results[1]['cost_rate'] * 100:>13.3f}%")
print()

print("=" * 64)
print("5. 같은 비용률로 한 해에 n번 사고팔면 원금이 얼마나 남는가")
print("=" * 64)
print(f"  {'왕복 횟수':>10}{'가나전자':>14}{'다라정밀':>14}")
for n in (1, 2, 4, 12, 24):
    left = [(1 - r["cost_rate"]) ** n for r in results]
    print(f"  {n:>10}{(left[0] - 1) * 100:>13.2f}%{(left[1] - 1) * 100:>13.2f}%")
