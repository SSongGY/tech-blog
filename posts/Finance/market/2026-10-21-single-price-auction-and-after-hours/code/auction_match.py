"""단일가매매와 접속매매를 같은 호가 묶음으로 돌려 비교한다.

종목·호가는 전부 가상이다. 실재하는 종목이 아니다.
"""

import platform
from dataclasses import dataclass

TICK = 100  # 호가단위. 이 예제의 가격대는 100원 단위라고 둔다


@dataclass
class Order:
    oid: str
    side: str  # "매수" | "매도"
    price: int
    qty: int
    stamp: str  # 접수 시각


# 가나전자(가상) 종가 단일가에 쌓인 호가. 직전 체결가는 15,000원이라고 둔다
BOOK = [
    Order("B1", "매수", 15_000, 600, "15:20:30"),
    Order("S1", "매도", 14_900, 300, "15:21:40"),
    Order("S2", "매도", 15_000, 500, "15:22:10"),
    Order("B2", "매수", 15_100, 800, "15:22:50"),
    Order("S3", "매도", 15_100, 400, "15:23:05"),
    Order("S4", "매도", 15_200, 600, "15:24:30"),
    Order("B3", "매수", 14_900, 500, "15:25:10"),
    Order("S5", "매도", 15_300, 900, "15:26:00"),
    Order("B4", "매수", 15_200, 400, "15:27:00"),
    Order("S6", "매도", 15_100, 300, "15:28:20"),
    Order("B5", "매수", 15_300, 200, "15:29:40"),
]

LAST_PRICE = 15_000


def print_environment() -> None:
    print("=" * 66)
    print("0. 실행 환경")
    print("=" * 66)
    print(f"Python {platform.python_version()} / {platform.system()} {platform.release()}")
    print(f"호가단위 가정 : {TICK:,}원")
    print()


def print_book(orders: list[Order]) -> None:
    print("=" * 66)
    print("1. 호가장 — 가나전자(가상) 종가 단일가, 직전 체결가 15,000원")
    print("=" * 66)
    print(f"{'번호':<5}{'구분':<6}{'가격(원)':>10}{'수량(주)':>10}  {'접수시각':<10}")
    for o in sorted(orders, key=lambda x: (-x.price, x.stamp)):
        print(f"{o.oid:<5}{o.side:<6}{o.price:>10,}{o.qty:>10,}  {o.stamp:<10}")
    buy = sum(o.qty for o in orders if o.side == "매수")
    sell = sum(o.qty for o in orders if o.side == "매도")
    print(f"\n매수 호가 합계 {buy:,}주 · 매도 호가 합계 {sell:,}주")
    print()


def matched_at(orders: list[Order], price: int) -> tuple[int, int, int]:
    """price 로 체결한다고 할 때 (체결가능 매도, 체결가능 매수, 체결수량)."""
    sell = sum(o.qty for o in orders if o.side == "매도" and o.price <= price)
    buy = sum(o.qty for o in orders if o.side == "매수" and o.price >= price)
    return sell, buy, min(sell, buy)


def candidate_prices(orders: list[Order]) -> list[int]:
    lo = min(o.price for o in orders)
    hi = max(o.price for o in orders)
    return list(range(lo, hi + TICK, TICK))


def find_single_price(orders: list[Order]) -> tuple[int, int, list[int]]:
    """체결수량을 가장 크게 만드는 가격을 찾는다. 동점 가격도 함께 돌려준다."""
    table = [(p, matched_at(orders, p)[2]) for p in candidate_prices(orders)]
    best = max(q for _, q in table)
    ties = [p for p, q in table if q == best]
    return ties[0], best, ties


def print_price_scan(orders: list[Order]) -> None:
    print("=" * 66)
    print("2. 가격마다 몇 주가 체결되는가 — 합치가격 찾기")
    print("=" * 66)
    print(f"{'후보가격':>10}{'체결가능 매도':>14}{'체결가능 매수':>14}{'체결수량':>12}")
    price, best, ties = find_single_price(orders)
    for p in candidate_prices(orders):
        sell, buy, qty = matched_at(orders, p)
        mark = "  <= 최대" if qty == best else ""
        print(f"{p:>10,}{sell:>14,}{buy:>14,}{qty:>12,}{mark}")
    print()
    print(f"체결수량이 가장 큰 가격 : {price:,}원 ({best:,}주)")
    print(f"동점 가격 개수          : {len(ties)}개")
    print()


def allocate(orders: list[Order], price: int) -> tuple[list[tuple[Order, int]], int]:
    """단일가로 체결한다. 가격우선 -> 시간우선 순으로 배분한다."""
    sell_q = sorted(
        [o for o in orders if o.side == "매도" and o.price <= price],
        key=lambda o: (o.price, o.stamp),
    )
    buy_q = sorted(
        [o for o in orders if o.side == "매수" and o.price >= price],
        key=lambda o: (-o.price, o.stamp),
    )
    total = min(sum(o.qty for o in sell_q), sum(o.qty for o in buy_q))

    fills: list[tuple[Order, int]] = []
    for queue in (sell_q, buy_q):
        left = total
        for o in queue:
            take = min(left, o.qty)
            fills.append((o, take))
            left -= take
    return fills, total


def print_allocation(orders: list[Order], price: int) -> None:
    print("=" * 66)
    print(f"3. {price:,}원 하나로 체결한다 — 누가 얼마나 받는가")
    print("=" * 66)
    fills, total = allocate(orders, price)
    print(f"{'번호':<5}{'구분':<6}{'호가':>9}{'수량':>8}{'체결':>8}{'잔량':>8}  비고")
    for o, take in fills:
        note = ""
        if take == 0:
            note = "가격우선에서 밀렸다"
        elif take < o.qty:
            note = "같은 가격대에서 시간우선에 밀려 일부만"
        elif o.side == "매수" and o.price > price:
            note = f"{o.price - price:,}원 싸게 샀다"
        elif o.side == "매도" and o.price < price:
            note = f"{price - o.price:,}원 비싸게 팔았다"
        print(
            f"{o.oid:<5}{o.side:<6}{o.price:>9,}{o.qty:>8,}{take:>8,}"
            f"{o.qty - take:>8,}  {note}"
        )
    in_range = {o.oid for o, _ in fills}
    out_of_range = [o for o in orders if o.oid not in in_range]
    for o in sorted(out_of_range, key=lambda x: (-x.price, x.stamp)):
        print(f"{o.oid:<5}{o.side:<6}{o.price:>9,}{o.qty:>8,}{0:>8}{o.qty:>8,}  체결가 밖의 호가")
    print(f"\n총 체결수량 {total:,}주 · 체결가격은 {price:,}원 하나뿐이다")
    print()


def run_continuous(arrival: list[Order]) -> list[tuple[int, int]]:
    """접속매매. 들어온 호가를 장부와 바로 맞춘다. 체결가는 장부에 있던 호가의 가격."""
    bids: list[Order] = []
    asks: list[Order] = []
    trades: list[tuple[int, int]] = []

    for incoming in arrival:
        rest = incoming.qty
        if incoming.side == "매수":
            asks.sort(key=lambda o: (o.price, o.stamp))
            while rest > 0 and asks and asks[0].price <= incoming.price:
                book = asks[0]
                take = min(rest, book.qty)
                trades.append((book.price, take))
                book.qty -= take
                rest -= take
                if book.qty == 0:
                    asks.pop(0)
            if rest > 0:
                bids.append(Order(incoming.oid, "매수", incoming.price, rest, incoming.stamp))
        else:
            bids.sort(key=lambda o: (-o.price, o.stamp))
            while rest > 0 and bids and bids[0].price >= incoming.price:
                book = bids[0]
                take = min(rest, book.qty)
                trades.append((book.price, take))
                book.qty -= take
                rest -= take
                if book.qty == 0:
                    bids.pop(0)
            if rest > 0:
                asks.append(Order(incoming.oid, "매도", incoming.price, rest, incoming.stamp))
    return trades


def summarize(label: str, arrival: list[Order]) -> tuple[int, int, int, int]:
    trades = run_continuous([Order(o.oid, o.side, o.price, o.qty, o.stamp) for o in arrival])
    total = sum(q for _, q in trades)
    prices = [p for p, _ in trades]
    print(f"[{label}] 접수 순서 {' → '.join(o.oid for o in arrival)}")
    print(f"  체결 내역 : {', '.join(f'{p:,}원×{q:,}주' for p, q in trades)}")
    print(
        f"  체결 {len(trades)}건 · 총 {total:,}주 · "
        f"가격 {min(prices):,}~{max(prices):,}원 · 마지막 체결가 {prices[-1]:,}원"
    )
    print()
    return len(trades), total, min(prices), max(prices)


def print_order_dependence(orders: list[Order]) -> None:
    print("=" * 66)
    print("4. 같은 호가를 접속매매로 — 접수 순서가 결과를 바꾼다")
    print("=" * 66)
    by_time = sorted(orders, key=lambda o: o.stamp)
    # 같은 호가 묶음, 접수 순서만 다르게 둔 가정. 무작위가 아니라 고정된 배열이다
    shuffled_ids = ["B5", "S1", "B4", "S6", "B1", "S5", "B2", "S2", "B3", "S3", "S4"]
    lookup = {o.oid: o for o in orders}
    other = [lookup[i] for i in shuffled_ids]

    a = summarize("순서 A", by_time)
    b = summarize("순서 B", other)
    print(f"두 순서의 체결 건수 {a[0]}건 vs {b[0]}건, 총 체결수량 {a[1]:,}주 vs {b[1]:,}주")
    print(f"마지막 체결가가 그날의 종가가 된다면 어느 순서로 들어왔느냐가 종가를 바꾼다.")
    print()


def print_order_independence(orders: list[Order]) -> None:
    print("=" * 66)
    print("5. 단일가는 접수 순서를 바꿔도 가격이 같다 — 검산")
    print("=" * 66)
    shuffled_ids = ["B5", "S1", "B4", "S6", "B1", "S5", "B2", "S2", "B3", "S3", "S4"]
    lookup = {o.oid: o for o in orders}
    for label, seq in (
        ("접수 시각 순", sorted(orders, key=lambda o: o.stamp)),
        ("순서를 뒤섞음", [lookup[i] for i in shuffled_ids]),
        ("역순", sorted(orders, key=lambda o: o.stamp, reverse=True)),
    ):
        price, qty, ties = find_single_price(seq)
        print(f"{label:<14} 합치가격 {price:,}원 · 체결 {qty:,}주 · 동점 {len(ties)}개")
    print()
    print("가격·수량만 쓰고 접수 순서는 쓰지 않으니 당연한 결과다.")
    print("접수 순서는 같은 가격대 안에서 누가 체결되는지를 가르는 데만 쓰인다.")
    print()


def print_tie_case() -> None:
    print("=" * 66)
    print("6. 체결수량이 같은 가격이 둘일 때 — 규칙이 더 필요해진다")
    print("=" * 66)
    tie_book = [
        Order("T1", "매도", 15_000, 500, "15:21:00"),
        Order("T2", "매도", 15_100, 500, "15:22:00"),
        Order("T3", "매수", 15_100, 500, "15:23:00"),
        Order("T4", "매수", 15_000, 500, "15:24:00"),
    ]
    print(f"{'후보가격':>10}{'체결가능 매도':>14}{'체결가능 매수':>14}{'체결수량':>12}")
    for p in candidate_prices(tie_book):
        sell, buy, qty = matched_at(tie_book, p)
        print(f"{p:>10,}{sell:>14,}{buy:>14,}{qty:>12,}")
    _, best, ties = find_single_price(tie_book)
    print()
    print(f"체결수량 {best:,}주가 되는 가격이 {len(ties)}개다: {', '.join(f'{p:,}원' for p in ties)}")
    print("체결수량만으로는 하나를 고를 수 없으므로 거래소 업무규정이 선택 기준을 따로 둔다.")
    print(f"(이 예제의 직전 체결가는 {LAST_PRICE:,}원이다)")
    print()


def main() -> None:
    print_environment()
    print_book(BOOK)
    print_price_scan(BOOK)
    price, _, _ = find_single_price(BOOK)
    print_allocation(BOOK, price)
    print_order_dependence(BOOK)
    print_order_independence(BOOK)
    print_tie_case()


if __name__ == "__main__":
    main()
