"""안쪽 — 업무 규칙과 포트. 바깥의 어떤 모듈도 import 하지 않는다."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Order:
    order_id: int
    amount: int


class OrderRepository(Protocol):
    """나가는 포트. 쓰는 쪽(유스케이스)이 필요한 모양을 정하고, 구현은 바깥이 맞춘다."""

    def next_id(self) -> int: ...

    def save(self, order: Order) -> None: ...


class PlaceOrder:
    """들어오는 포트이자 유스케이스. 저장 기술을 모른 채 포트만 부른다."""

    def __init__(self, repository: OrderRepository) -> None:
        self._repository = repository

    def execute(self, amount: int) -> Order:
        if amount <= 0:
            raise ValueError("주문 금액은 0보다 커야 한다")
        order = Order(self._repository.next_id(), amount)
        self._repository.save(order)
        return order
