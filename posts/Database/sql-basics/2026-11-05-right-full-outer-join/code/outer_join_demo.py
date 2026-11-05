"""RIGHT JOIN 과 FULL OUTER JOIN 을 주문-입금 대사 예제로 확인한다."""

import sqlite3

from dbshow import print_dataset, print_environment

SCHEMA = """
CREATE TABLE customer_order (
    order_id INTEGER PRIMARY KEY,
    amount   INTEGER NOT NULL
);
CREATE TABLE payment (
    payment_id INTEGER PRIMARY KEY,
    order_id   INTEGER NOT NULL,
    paid       INTEGER NOT NULL
);
"""

ORDERS = [(1, 1000), (2, 2000), (3, 3000), (4, 4000)]
PAYMENTS = [(10, 1, 1000), (11, 2, 2000), (12, 2, 500), (13, 9, 700)]


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO customer_order VALUES (?, ?)", ORDERS)
    conn.executemany("INSERT INTO payment VALUES (?, ?, ?)", PAYMENTS)
    return conn


def show(conn, title, sql):
    print(f"\n-- {title}")
    print(sql.strip())
    try:
        for row in conn.execute(sql):
            print("  ", row)
    except sqlite3.Error as exc:
        print("   오류:", exc)


def show_plan(conn, title, sql):
    print(f"\n-- {title}")
    print(sql.strip())
    for _id, _parent, _unused, detail in conn.execute("EXPLAIN QUERY PLAN " + sql):
        print("  ", detail)


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)

    show(conn, "1. LEFT JOIN: 주문 기준 (입금 없는 주문은 보이지만 주문 없는 입금은 사라진다)", """
SELECT o.order_id, o.amount, p.payment_id, p.paid
FROM customer_order o LEFT JOIN payment p ON p.order_id = o.order_id
ORDER BY o.order_id, p.payment_id""")

    show(conn, "2. RIGHT JOIN: 입금 기준 (같은 결과를 표 순서만 바꿔 얻는다)", """
SELECT o.order_id, o.amount, p.payment_id, p.paid
FROM customer_order o RIGHT JOIN payment p ON p.order_id = o.order_id
ORDER BY p.payment_id""")

    show(conn, "3. FULL OUTER JOIN: 양쪽 모두 남긴다", """
SELECT o.order_id, o.amount, p.payment_id, p.paid
FROM customer_order o FULL OUTER JOIN payment p ON p.order_id = o.order_id
ORDER BY o.order_id, p.payment_id""")

    show(conn, "4. 예전 우회 방식: LEFT JOIN 에 반대편 짝 없는 행을 UNION ALL", """
SELECT o.order_id, o.amount, p.payment_id, p.paid
FROM customer_order o LEFT JOIN payment p ON p.order_id = o.order_id
UNION ALL
SELECT NULL, NULL, p.payment_id, p.paid
FROM payment p LEFT JOIN customer_order o ON p.order_id = o.order_id
WHERE o.order_id IS NULL
ORDER BY 1, 3""")

    show(conn, "5. 대사 결과만: 어느 한쪽에 짝이 없는 행", """
SELECT o.order_id, o.amount, p.payment_id, p.paid
FROM customer_order o FULL OUTER JOIN payment p ON p.order_id = o.order_id
WHERE o.order_id IS NULL OR p.payment_id IS NULL
ORDER BY o.order_id, p.payment_id""")

    show(conn, "6. 조건을 ON 에 두면: 입금액 1000 이상인 짝만 맺는다", """
SELECT o.order_id, p.payment_id, p.paid
FROM customer_order o LEFT JOIN payment p
  ON p.order_id = o.order_id AND p.paid >= 1000
ORDER BY o.order_id, p.payment_id""")

    show(conn, "6'. 같은 조건을 WHERE 에 두면: 짝 없는 주문이 사라진다", """
SELECT o.order_id, p.payment_id, p.paid
FROM customer_order o LEFT JOIN payment p ON p.order_id = o.order_id
WHERE p.paid >= 1000
ORDER BY o.order_id, p.payment_id""")

    show(conn, "7. 입금 합계로 주문 금액과 대조 (주문당 입금이 여러 건이면 먼저 합친다)", """
SELECT o.order_id, o.amount, s.total_paid
FROM customer_order o
FULL OUTER JOIN (
    SELECT order_id, SUM(paid) AS total_paid FROM payment GROUP BY order_id
) s ON s.order_id = o.order_id
ORDER BY COALESCE(o.order_id, s.order_id)""")

    show_plan(conn, "8. 실행계획: FULL OUTER JOIN", """
SELECT o.order_id, p.payment_id
FROM customer_order o FULL OUTER JOIN payment p ON p.order_id = o.order_id""")


if __name__ == "__main__":
    main()
