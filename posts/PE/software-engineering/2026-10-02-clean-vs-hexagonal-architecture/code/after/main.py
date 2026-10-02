"""조립 지점 — 어떤 어댑터를 꽂을지 여기서만 정한다."""

from adapters import InMemoryOrderRepository, SqliteOrderRepository
from domain import PlaceOrder


def run(label: str, use_case: PlaceOrder) -> None:
    orders = [use_case.execute(amount) for amount in (12000, 30000)]
    print(f"  {label:<24} -> {orders}")


if __name__ == "__main__":
    run("InMemoryOrderRepository", PlaceOrder(InMemoryOrderRepository()))
    run("SqliteOrderRepository", PlaceOrder(SqliteOrderRepository(":memory:")))
