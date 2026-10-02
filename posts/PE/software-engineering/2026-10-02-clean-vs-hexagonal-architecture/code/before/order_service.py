"""계층형으로 짠 주문 서비스 — 업무 규칙이 저장 기술(sqlite3)을 직접 안다."""

import sqlite3


class OrderService:
    def __init__(self, db_path: str) -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS shop_order (id INTEGER PRIMARY KEY, amount INTEGER)"
        )

    def place_order(self, amount: int) -> int:
        if amount <= 0:
            raise ValueError("주문 금액은 0보다 커야 한다")
        cursor = self._conn.execute("INSERT INTO shop_order (amount) VALUES (?)", (amount,))
        return cursor.lastrowid
