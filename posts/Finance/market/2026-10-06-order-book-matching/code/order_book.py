"""호가와 체결 — 가격우선·시간우선으로 주문이 맺어지는 순서를 따라간다.

가상 종목 가나전자의 호가창 한 장면을 만들고, 지정가·시장가 주문 네 건을 차례로
넣어 어느 주문과 어느 가격에 체결되는지 찍는다. 접속매매(복수가격 개별경쟁매매)만
다룬다. 체결가격은 먼저 들어와 있던 주문의 가격이다.
"""
import platform
import sys
from dataclasses import dataclass


def tick_size(price: int) -> int:
    """유가증권시장 호가가격단위 — 가격대별로 주문을 낼 수 있는 최소 간격."""
    for upper, tick in ((2_000, 1), (5_000, 5), (20_000, 10), (50_000, 50),
                        (200_000, 100), (500_000, 500)):
        if price < upper:
            return tick
    return 1_000


@dataclass
class Order:
    name: str
    side: str          # "매수" | "매도"
    quantity: int
    price: int | None  # None 이면 시장가
    time: str


class OrderBook:
    def __init__(self) -> None:
        self.bids: list[Order] = []
        self.asks: list[Order] = []

    def sorted_side(self, side: str) -> list[Order]:
        # 가격우선 다음 시간우선. 매수는 높은 값이, 매도는 낮은 값이 앞이다
        if side == "매수":
            return sorted(self.bids, key=lambda o: (-o.price, o.time))
        return sorted(self.asks, key=lambda o: (o.price, o.time))

    def submit(self, order: Order) -> None:
        kind = "시장가" if order.price is None else f"지정가 {order.price:,}"
        print(f"  {order.time} {order.name} {order.side} {kind} × {order.quantity:,}")
        if order.price is not None and order.price % tick_size(order.price) != 0:
            print(f"    거부 — {order.price:,}원은 호가 단위 {tick_size(order.price)}원에 맞지 않는다")
            return
        opposite = "매도" if order.side == "매수" else "매수"
        book = self.asks if opposite == "매도" else self.bids
        filled_value = filled_qty = 0
        for resting in self.sorted_side(opposite):
            if order.quantity == 0:
                break
            crosses = (order.price is None
                       or (order.side == "매수" and order.price >= resting.price)
                       or (order.side == "매도" and order.price <= resting.price))
            if not crosses:
                break
            qty = min(order.quantity, resting.quantity)
            # 체결가격은 먼저 접수돼 있던 쪽(resting)의 가격이다
            print(f"    체결 {qty:>5,}주 @ {resting.price:,}  상대 {resting.name}({resting.time})")
            order.quantity -= qty
            resting.quantity -= qty
            filled_value += qty * resting.price
            filled_qty += qty
            if resting.quantity == 0:
                book.remove(resting)
        if filled_qty:
            print(f"    평균 체결가 {filled_value / filled_qty:,.2f}원 · {filled_qty:,}주")
        if order.quantity and order.price is not None:
            (self.bids if order.side == "매수" else self.asks).append(order)
            print(f"    잔량 {order.quantity:,}주가 {order.price:,}원에 호가로 남는다")

    def show(self, title: str) -> None:
        print(f"  ── {title} ──")
        print(f"  {'매도 잔량':>10}{'가격':>10}{'매수 잔량':>10}   대기 주문(접수 순)")
        levels = sorted({o.price for o in self.asks} | {o.price for o in self.bids}, reverse=True)
        for price in levels:
            asks = [o for o in self.sorted_side("매도") if o.price == price]
            bids = [o for o in self.sorted_side("매수") if o.price == price]
            ask_qty = sum(o.quantity for o in asks)
            bid_qty = sum(o.quantity for o in bids)
            queue = ", ".join(f"{o.name} {o.quantity}" for o in asks + bids)
            print(f"  {ask_qty or '':>10}{price:>10,}{bid_qty or '':>10}   {queue}")
        best_ask = min(o.price for o in self.asks)
        best_bid = max(o.price for o in self.bids)
        print(f"  최우선 매도 {best_ask:,} · 최우선 매수 {best_bid:,} · 스프레드 {best_ask - best_bid:,}원")
        print()


def print_tick_table() -> None:
    print("[1] 호가가격단위 — 가격대마다 주문 가격의 최소 간격이 다르다")
    for price in (1_999, 2_000, 9_990, 19_990, 20_000, 49_950, 50_000, 500_000):
        print(f"  {price:>9,}원 → {tick_size(price):>5,}원 단위")
    print()


def main() -> None:
    print(f"Python {platform.python_version()} · {sys.platform}")
    print()
    print_tick_table()

    book = OrderBook()
    for order in (
        Order("E", "매도", 500, 10_060, "09:00:40"),
        Order("D", "매도", 300, 10_050, "09:00:20"),
        Order("B", "매도", 200, 10_040, "09:00:10"),
        Order("C", "매도", 150, 10_040, "09:00:30"),
        Order("F", "매수", 400, 10_020, "09:00:15"),
        Order("G", "매수", 300, 10_010, "09:00:05"),
        Order("H", "매수", 600, 10_000, "09:00:01"),
    ):
        (book.bids if order.side == "매수" else book.asks).append(order)

    print("[2] 가나전자 호가창 — 체결 전")
    book.show("09:01:00 직전")

    print("[3] 주문 다섯 건을 차례로 넣는다")
    book.submit(Order("I", "매수", 100, 10_030, "09:01:00"))
    book.submit(Order("J", "매수", 450, None, "09:01:05"))
    book.submit(Order("K", "매도", 600, 10_010, "09:01:10"))
    book.submit(Order("L", "매수", 300, 10_050, "09:01:15"))
    book.submit(Order("M", "매수", 100, 10_035, "09:01:20"))
    print()

    print("[4] 가나전자 호가창 — 체결 후")
    book.show("09:01:20 직후")


if __name__ == "__main__":
    main()
