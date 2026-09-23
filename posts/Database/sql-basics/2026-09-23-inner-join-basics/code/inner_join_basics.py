"""INNER JOIN — 조인 조건과 행 수의 관계를 숫자로 확인한다.

메모리 SQLite에 고객 4명과 주문 6건, 배송 2건을 넣고
조인 조건의 유무·중복 키·NULL 키가 결과 행 수를 어떻게 바꾸는지 본다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

CUSTOMERS = [
    (1, "김서준", "서울"),
    (2, "이하윤", "부산"),
    (3, "박도윤", "대구"),
    (4, "최시우", "광주"),  # 주문이 없는 고객
]

# customer_id 9 는 customer 에 없는 값, None 은 값이 비어 있는 경우
SALE_ORDERS = [
    (101, 1, 120),
    (102, 1, 80),
    (103, 1, 200),
    (104, 2, 150),
    (105, 9, 300),
    (106, None, 50),
    (107, 1, 80),  # 102번과 금액이 같다 — SUM(DISTINCT) 가 여기서 틀린다
]

# 고객 1번에게만 배송이 두 건 달려 있다
SHIPMENTS = [
    (201, 1, "완료"),
    (202, 1, "준비"),
    (203, 2, "완료"),
]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE customer (
            id   INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            city TEXT NOT NULL
        );
        CREATE TABLE sale_order (
            id          INTEGER PRIMARY KEY,
            customer_id INTEGER,
            amount      INTEGER NOT NULL
        );
        CREATE TABLE shipment (
            id          INTEGER PRIMARY KEY,
            customer_id INTEGER,
            status      TEXT NOT NULL
        );
        """
    )
    conn.executemany("INSERT INTO customer VALUES (?, ?, ?)", CUSTOMERS)
    conn.executemany("INSERT INTO sale_order VALUES (?, ?, ?)", SALE_ORDERS)
    conn.executemany("INSERT INTO shipment VALUES (?, ?, ?)", SHIPMENTS)
    conn.commit()
    return conn


def show(conn: sqlite3.Connection, label: str, sql: str) -> None:
    print(f"\n[{label}]")
    print(f"  {' '.join(sql.split())}")
    try:
        rows = conn.execute(sql).fetchall()
    except sqlite3.Error as exc:
        print(f"  [에러] {type(exc).__name__}: {exc}")
        return
    if not rows:
        print("  (0건)")
        return
    for row in rows:
        print(f"  {row}")
    print(f"  -> {len(rows)}행")


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("\n=== 1. 두 표의 행 수 ===")
    show(conn, "1-A 고객", "SELECT COUNT(*) FROM customer")
    show(conn, "1-B 주문", "SELECT COUNT(*) FROM sale_order")

    print("\n=== 2. 조인 조건이 없으면 곱해진다 ===")
    show(
        conn,
        "2-A CROSS JOIN",
        "SELECT COUNT(*) FROM customer CROSS JOIN sale_order",
    )
    show(
        conn,
        "2-B 쉼표 조인, WHERE 없음",
        "SELECT COUNT(*) FROM customer, sale_order",
    )
    show(
        conn,
        "2-C INNER JOIN ON 1=1",
        "SELECT COUNT(*) FROM customer INNER JOIN sale_order ON 1 = 1",
    )

    print("\n=== 3. 조인 조건을 주면 ===")
    show(
        conn,
        "3-A INNER JOIN ON",
        """
        SELECT c.name, o.id, o.amount
        FROM customer AS c
        INNER JOIN sale_order AS o ON o.customer_id = c.id
        ORDER BY o.id
        """,
    )
    show(
        conn,
        "3-B 쉼표 조인 + WHERE (같은 결과)",
        """
        SELECT c.name, o.id, o.amount
        FROM customer AS c, sale_order AS o
        WHERE o.customer_id = c.id
        ORDER BY o.id
        """,
    )
    show(
        conn,
        "3-C USING (컬럼 이름이 같을 때)",
        """
        SELECT customer_id, COUNT(*)
        FROM sale_order INNER JOIN shipment USING (customer_id)
        GROUP BY customer_id
        """,
    )

    print("\n=== 4. 짝이 없는 행은 사라진다 ===")
    show(
        conn,
        "4-A 주문이 없는 고객",
        """
        SELECT c.name FROM customer AS c
        INNER JOIN sale_order AS o ON o.customer_id = c.id
        WHERE c.id = 4
        """,
    )
    show(
        conn,
        "4-B 고객이 없는 주문 (customer_id = 9)",
        """
        SELECT o.id FROM sale_order AS o
        INNER JOIN customer AS c ON o.customer_id = c.id
        WHERE o.id = 105
        """,
    )
    show(
        conn,
        "4-C NULL 키는 무엇과도 짝이 되지 않는다",
        """
        SELECT o.id FROM sale_order AS o
        INNER JOIN customer AS c ON o.customer_id = c.id
        WHERE o.id = 106
        """,
    )
    show(
        conn,
        "4-D NULL = NULL 도 짝이 아니다",
        "SELECT COUNT(*) FROM sale_order AS a "
        "INNER JOIN sale_order AS b ON a.customer_id = b.customer_id "
        "WHERE a.id = 106 AND b.id = 106",
    )

    print("\n=== 5. 합계가 틀어지는 자리 ===")
    show(
        conn,
        "5-A 주문만 집계",
        "SELECT SUM(amount) FROM sale_order WHERE customer_id = 1",
    )
    show(
        conn,
        "5-B 배송을 함께 조인하고 집계",
        """
        SELECT SUM(o.amount)
        FROM sale_order AS o
        INNER JOIN shipment AS s ON s.customer_id = o.customer_id
        WHERE o.customer_id = 1
        """,
    )
    show(
        conn,
        "5-C 조인 결과를 그대로 본다",
        """
        SELECT o.id, s.id, o.amount
        FROM sale_order AS o
        INNER JOIN shipment AS s ON s.customer_id = o.customer_id
        WHERE o.customer_id = 1
        ORDER BY o.id, s.id
        """,
    )
    show(
        conn,
        "5-D DISTINCT 로 덮으면",
        """
        SELECT SUM(DISTINCT o.amount)
        FROM sale_order AS o
        INNER JOIN shipment AS s ON s.customer_id = o.customer_id
        WHERE o.customer_id = 1
        """,
    )

    print("\n=== 6. 실행계획 ===")
    show(
        conn,
        "6-A 인덱스 없음",
        """
        EXPLAIN QUERY PLAN
        SELECT c.name, o.amount FROM customer AS c
        INNER JOIN sale_order AS o ON o.customer_id = c.id
        """,
    )
    conn.execute("CREATE INDEX ix_sale_order_customer_id ON sale_order(customer_id)")
    show(
        conn,
        "6-B 조인 키에 인덱스를 만든 뒤",
        """
        EXPLAIN QUERY PLAN
        SELECT c.name, o.amount FROM customer AS c
        INNER JOIN sale_order AS o ON o.customer_id = c.id
        """,
    )
    show(
        conn,
        "6-C 한쪽을 먼저 좁히면",
        """
        EXPLAIN QUERY PLAN
        SELECT c.name, o.amount FROM customer AS c
        INNER JOIN sale_order AS o ON o.customer_id = c.id
        WHERE c.city = '서울'
        """,
    )

    conn.close()


if __name__ == "__main__":
    main()
