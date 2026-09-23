"""LEFT JOIN — 짝이 없는 행이 남는 자리와 사라지는 자리를 확인한다.

메모리 SQLite에 고객 4명과 주문 5건을 넣고, 조건을 ON 에 둘 때와 WHERE 에 둘 때
결과가 어떻게 갈리는지, 짝이 없는 행을 찾는 질의가 어디서 틀리는지 본다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

CUSTOMERS = [
    (1, "김서준"),
    (2, "이하윤"),  # 주문이 전부 취소
    (3, "박도윤"),
    (4, "최시우"),  # 주문이 하나도 없다
]

# coupon_code 는 비어 있을 수 있는 컬럼 — IS NULL 로 짝 없는 행을 찾을 때 함정이 된다
SALE_ORDERS = [
    (101, 1, "완료", 120, "WELCOME"),
    (102, 1, "완료", 80, None),
    (103, 1, "취소", 200, None),
    (104, 2, "취소", 150, "WELCOME"),
    (105, 3, "완료", 90, None),
]

# 완료 주문 101·105 만 배송이 잡혔다 — 102 는 아직 배송 전
SHIPMENTS = [
    (301, 101),
    (302, 105),
]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE customer (
            id   INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );
        CREATE TABLE sale_order (
            id          INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL REFERENCES customer(id),
            status      TEXT NOT NULL,
            amount      INTEGER NOT NULL,
            coupon_code TEXT
        );
        CREATE TABLE shipment (
            id       INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL REFERENCES sale_order(id)
        );
        """
    )
    conn.executemany("INSERT INTO customer VALUES (?, ?)", CUSTOMERS)
    conn.executemany("INSERT INTO sale_order VALUES (?, ?, ?, ?, ?)", SALE_ORDERS)
    conn.executemany("INSERT INTO shipment VALUES (?, ?)", SHIPMENTS)
    conn.commit()
    return conn


def show(conn: sqlite3.Connection, label: str, sql: str) -> None:
    print(f"\n[{label}]")
    print(f"  {' '.join(sql.split())}")
    rows = conn.execute(sql).fetchall()
    if not rows:
        print("  (0건)")
        return
    for row in rows:
        print(f"  {row}")
    print(f"  -> {len(rows)}행")


def show_plan(conn: sqlite3.Connection, label: str, sql: str) -> None:
    # sqlite3 CLI 가 그리는 트리 모양을 그대로 흉내 낸다 (id·parent 로 깊이를 잡는다)
    print(f"\n[{label}]")
    print(f"  {' '.join(sql.split())}")
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    depth = {0: -1}
    print("  QUERY PLAN")
    for i, (node_id, parent, _, detail) in enumerate(rows):
        depth[node_id] = depth.get(parent, -1) + 1
        is_last = all(r[1] != parent for r in rows[i + 1 :])
        branch = "`--" if is_last else "|--"
        print(f"  {'   ' * depth[node_id]}{branch}{detail}")


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("\n=== 1. INNER JOIN 과 LEFT JOIN 의 행 수 ===")
    show(
        conn,
        "1-A INNER JOIN",
        """
        SELECT c.name, o.id, o.status
        FROM customer AS c
        INNER JOIN sale_order AS o ON o.customer_id = c.id
        ORDER BY c.id, o.id
        """,
    )
    show(
        conn,
        "1-B LEFT JOIN",
        """
        SELECT c.name, o.id, o.status
        FROM customer AS c
        LEFT JOIN sale_order AS o ON o.customer_id = c.id
        ORDER BY c.id, o.id
        """,
    )

    print("\n=== 2. '완료' 주문만 붙이고 싶을 때 ===")
    show(
        conn,
        "2-A 조건을 WHERE 에",
        """
        SELECT c.name, o.id, o.status
        FROM customer AS c
        LEFT JOIN sale_order AS o ON o.customer_id = c.id
        WHERE o.status = '완료'
        ORDER BY c.id, o.id
        """,
    )
    show(
        conn,
        "2-B 조건을 ON 에",
        """
        SELECT c.name, o.id, o.status
        FROM customer AS c
        LEFT JOIN sale_order AS o ON o.customer_id = c.id AND o.status = '완료'
        ORDER BY c.id, o.id
        """,
    )
    show(
        conn,
        "2-C WHERE 에 OR IS NULL 을 덧붙이면",
        """
        SELECT c.name, o.id, o.status
        FROM customer AS c
        LEFT JOIN sale_order AS o ON o.customer_id = c.id
        WHERE o.status = '완료' OR o.id IS NULL
        ORDER BY c.id, o.id
        """,
    )

    print("\n=== 3. 고객별 완료 주문 수 ===")
    show(
        conn,
        "3-A COUNT(*)",
        """
        SELECT c.name, COUNT(*)
        FROM customer AS c
        LEFT JOIN sale_order AS o ON o.customer_id = c.id AND o.status = '완료'
        GROUP BY c.id ORDER BY c.id
        """,
    )
    show(
        conn,
        "3-B COUNT(o.id)",
        """
        SELECT c.name, COUNT(o.id)
        FROM customer AS c
        LEFT JOIN sale_order AS o ON o.customer_id = c.id AND o.status = '완료'
        GROUP BY c.id ORDER BY c.id
        """,
    )
    show(
        conn,
        "3-C SUM 은 0 이 아니라 NULL",
        """
        SELECT c.name, SUM(o.amount), COALESCE(SUM(o.amount), 0)
        FROM customer AS c
        LEFT JOIN sale_order AS o ON o.customer_id = c.id AND o.status = '완료'
        GROUP BY c.id ORDER BY c.id
        """,
    )

    print("\n=== 4. 주문이 없는 고객 찾기 ===")
    show(
        conn,
        "4-A 키 컬럼으로 IS NULL",
        """
        SELECT c.name
        FROM customer AS c
        LEFT JOIN sale_order AS o ON o.customer_id = c.id
        WHERE o.id IS NULL
        """,
    )
    show(
        conn,
        "4-B 비어 있을 수 있는 컬럼으로 IS NULL",
        """
        SELECT c.name, o.id
        FROM customer AS c
        LEFT JOIN sale_order AS o ON o.customer_id = c.id
        WHERE o.coupon_code IS NULL
        ORDER BY c.id, o.id
        """,
    )
    show(
        conn,
        "4-C NOT EXISTS",
        """
        SELECT c.name
        FROM customer AS c
        WHERE NOT EXISTS (SELECT 1 FROM sale_order AS o WHERE o.customer_id = c.id)
        """,
    )

    print("\n=== 5. 왼쪽 표 조건을 ON 에 쓰면 ===")
    show(
        conn,
        "5-A 왼쪽 표 조건을 WHERE 에",
        """
        SELECT c.name, o.id
        FROM customer AS c
        LEFT JOIN sale_order AS o ON o.customer_id = c.id
        WHERE c.id = 1
        ORDER BY c.id, o.id
        """,
    )
    show(
        conn,
        "5-B 왼쪽 표 조건을 ON 에",
        """
        SELECT c.name, o.id
        FROM customer AS c
        LEFT JOIN sale_order AS o ON o.customer_id = c.id AND c.id = 1
        ORDER BY c.id, o.id
        """,
    )

    print("\n=== 6. LEFT JOIN 뒤에 INNER JOIN 을 이으면 ===")
    show(
        conn,
        "6-A LEFT JOIN 만",
        """
        SELECT c.name, o.id
        FROM customer AS c
        LEFT JOIN sale_order AS o ON o.customer_id = c.id AND o.status = '완료'
        ORDER BY c.id, o.id
        """,
    )
    show(
        conn,
        "6-B 이어서 INNER JOIN shipment",
        """
        SELECT c.name, o.id, s.id
        FROM customer AS c
        LEFT JOIN sale_order AS o ON o.customer_id = c.id AND o.status = '완료'
        INNER JOIN shipment AS s ON s.order_id = o.id
        ORDER BY c.id, o.id
        """,
    )
    show(
        conn,
        "6-C 이어서 LEFT JOIN shipment",
        """
        SELECT c.name, o.id, s.id
        FROM customer AS c
        LEFT JOIN sale_order AS o ON o.customer_id = c.id AND o.status = '완료'
        LEFT JOIN shipment AS s ON s.order_id = o.id
        ORDER BY c.id, o.id
        """,
    )

    print("\n=== 7. 실행계획 ===")
    show_plan(
        conn,
        "7-A LEFT JOIN, 조건을 ON 에",
        """
        SELECT c.name, o.id FROM customer AS c
        LEFT JOIN sale_order AS o ON o.customer_id = c.id AND o.status = '완료'
        """,
    )
    show_plan(
        conn,
        "7-B LEFT JOIN, 조건을 WHERE 에",
        """
        SELECT c.name, o.id FROM customer AS c
        LEFT JOIN sale_order AS o ON o.customer_id = c.id
        WHERE o.status = '완료'
        """,
    )

    conn.close()


if __name__ == "__main__":
    main()
