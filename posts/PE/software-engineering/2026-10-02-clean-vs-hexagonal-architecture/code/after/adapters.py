"""바깥 — 포트를 구현하는 어댑터. 안쪽(domain)을 import 한다."""

import sqlite3

from domain import Order


class InMemoryOrderRepository:
    def __init__(self) -> None:
        self.rows: dict[int, int] = {}

    def next_id(self) -> int:
        return len(self.rows) + 1

    def save(self, order: Order) -> None:
        self.rows[order.order_id] = order.amount


class SqliteOrderRepository:
    def __init__(self, db_path: str) -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS shop_order (id INTEGER PRIMARY KEY, amount INTEGER)"
        )

    def next_id(self) -> int:
        row = self._conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM shop_order").fetchone()
        return row[0]

    def save(self, order: Order) -> None:
        self._conn.execute(
            "INSERT INTO shop_order (id, amount) VALUES (?, ?)", (order.order_id, order.amount)
        )
