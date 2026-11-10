"""1:N 표 두 개를 한 번에 조인하면 SUM 이 왜 부풀려지는가.

1) 고객마다 주문 수 m, 결제 수 n 과 조인 결과 행 수를 나란히 센다
2) 그대로 SUM 하면 주문액은 n 배, 결제액은 m 배가 된다
3) DISTINCT 로 막으려 하면 COUNT 는 맞고 SUM 은 틀린다
4) 먼저 집계하고 조인한다
5) 상관 부질의로 고객마다 따로 집계한다
6) 두 방법의 실행계획
7) 조인 전에 부풀림을 알아내는 방법
"""
import sqlite3

from dbshow import print_dataset, print_environment


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE customer (
            customer_id INTEGER PRIMARY KEY,
            name        TEXT NOT NULL
        );
        CREATE TABLE orders (
            order_id    INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL REFERENCES customer(customer_id),
            amount      INTEGER NOT NULL
        );
        CREATE TABLE payment (
            payment_id  INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL REFERENCES customer(customer_id),
            paid        INTEGER NOT NULL
        );
        INSERT INTO customer VALUES (1, 'kim'), (2, 'lee'), (3, 'park');
        -- kim 은 금액이 같은 주문 두 건을 둔다. DISTINCT 가 무엇을 지우는지 보려는 것이다
        INSERT INTO orders VALUES
            (101, 1, 10000), (102, 1, 10000), (103, 1, 5000),
            (104, 2, 7000),  (105, 2, 3000),
            (106, 3, 20000);
        -- lee 는 결제가 없다
        INSERT INTO payment VALUES
            (201, 1, 15000), (202, 1, 10000),
            (203, 3, 12000), (204, 3, 8000);
        """
    )
    return conn


def show(conn, sql):
    print("  sql> " + " ".join(sql.split()))
    cursor = conn.execute(sql)
    headers = [d[0] for d in cursor.description]
    print("  " + " | ".join(headers))
    for row in cursor.fetchall():
        print("  " + " | ".join("NULL" if v is None else str(v) for v in row))
    print()


def show_plan(conn, sql):
    """EXPLAIN QUERY PLAN 의 (id, parent) 로 sqlite3 CLI 와 같은 트리를 그린다."""
    print("  sql> " + " ".join(sql.split()))
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    children = {}
    for node_id, parent, _, detail in rows:
        children.setdefault(parent, []).append((node_id, detail))

    def draw(parent, prefix):
        kids = children.get(parent, [])
        for i, (node_id, detail) in enumerate(kids):
            last = i == len(kids) - 1
            print("  " + prefix + ("`--" if last else "|--") + detail)
            draw(node_id, prefix + ("   " if last else "|  "))

    print("  QUERY PLAN")
    draw(0, "")
    print()


NAIVE_JOIN = """
    SELECT c.name, o.order_id, o.amount, p.payment_id, p.paid
    FROM customer c
    LEFT JOIN orders  o ON o.customer_id = c.customer_id
    LEFT JOIN payment p ON p.customer_id = c.customer_id
    ORDER BY c.customer_id, o.order_id, p.payment_id
"""

PRE_AGGREGATE = """
    SELECT c.name, o.order_total, p.paid_total
    FROM customer c
    LEFT JOIN (SELECT customer_id, SUM(amount) AS order_total
               FROM orders GROUP BY customer_id) o
           ON o.customer_id = c.customer_id
    LEFT JOIN (SELECT customer_id, SUM(paid) AS paid_total
               FROM payment GROUP BY customer_id) p
           ON p.customer_id = c.customer_id
    ORDER BY c.customer_id
"""

CORRELATED = """
    SELECT c.name,
           (SELECT SUM(amount) FROM orders  o WHERE o.customer_id = c.customer_id)
               AS order_total,
           (SELECT SUM(paid)   FROM payment p WHERE p.customer_id = c.customer_id)
               AS paid_total
    FROM customer c
    ORDER BY c.customer_id
"""


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("== 1) 조인 결과 행 수 = 주문 수 x 결제 수 ==")
    show(conn, NAIVE_JOIN)
    show(
        conn,
        """
        SELECT c.name,
               (SELECT COUNT(*) FROM orders  o WHERE o.customer_id = c.customer_id) AS m,
               (SELECT COUNT(*) FROM payment p WHERE p.customer_id = c.customer_id) AS n,
               COUNT(*) AS joined_rows
        FROM customer c
        LEFT JOIN orders  o ON o.customer_id = c.customer_id
        LEFT JOIN payment p ON p.customer_id = c.customer_id
        GROUP BY c.customer_id ORDER BY c.customer_id
        """,
    )

    print("== 2) 그대로 집계하면 ==")
    show(
        conn,
        """
        SELECT c.name, COUNT(o.order_id) AS order_count,
               SUM(o.amount) AS order_total, SUM(p.paid) AS paid_total
        FROM customer c
        LEFT JOIN orders  o ON o.customer_id = c.customer_id
        LEFT JOIN payment p ON p.customer_id = c.customer_id
        GROUP BY c.customer_id ORDER BY c.customer_id
        """,
    )

    print("== 3) DISTINCT 로 막으려 하면 ==")
    show(
        conn,
        """
        SELECT c.name, COUNT(DISTINCT o.order_id) AS order_count,
               SUM(DISTINCT o.amount) AS order_total,
               SUM(DISTINCT p.paid) AS paid_total
        FROM customer c
        LEFT JOIN orders  o ON o.customer_id = c.customer_id
        LEFT JOIN payment p ON p.customer_id = c.customer_id
        GROUP BY c.customer_id ORDER BY c.customer_id
        """,
    )

    print("== 4) 먼저 집계하고 조인 ==")
    show(conn, PRE_AGGREGATE)

    print("== 5) 상관 부질의 ==")
    show(conn, CORRELATED)

    print("== 기준값 — 표마다 따로 합계 ==")
    show(conn, "SELECT customer_id, SUM(amount) FROM orders GROUP BY customer_id")
    show(conn, "SELECT customer_id, SUM(paid) FROM payment GROUP BY customer_id")

    print("== 6) 실행계획 ==")
    show_plan(conn, PRE_AGGREGATE)
    show_plan(conn, CORRELATED)

    print("== 7) 조인 전에 알아내기 — 조인 키가 한쪽에서 유일한가 ==")
    show(
        conn,
        """
        SELECT customer_id, COUNT(*) AS rows_per_key
        FROM payment GROUP BY customer_id HAVING COUNT(*) > 1
        """,
    )
    show(
        conn,
        """
        SELECT (SELECT COUNT(*) FROM orders) AS order_rows,
               (SELECT COUNT(*) FROM orders o
                  LEFT JOIN payment p ON p.customer_id = o.customer_id) AS after_join
        """,
    )
    conn.close()


if __name__ == "__main__":
    main()
