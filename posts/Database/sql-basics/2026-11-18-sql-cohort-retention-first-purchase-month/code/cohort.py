"""첫 구매 월로 고객을 묶고, 몇 달 뒤에 다시 샀는지 세는 코호트 표를 만든다.

1) 고객마다 첫 구매 월을 구한다 (MIN + GROUP BY)
2) 주문마다 첫 구매 월로부터 몇 달 지났는지 — 일수/30 과 연*12+월 을 나란히
3) 코호트 x 경과 월로 세기 — COUNT(*) 와 COUNT(DISTINCT customer_id)
4) 세로로 나온 결과를 CASE 로 가로 표(M0~M3)로 펼친다
5) 비율로 바꾸기 — 정수 나눗셈이면 0 이 된다
6) 첫 구매 월을 창 함수로 구하면 GROUP BY + JOIN 이 필요 없다
"""
import sqlite3

from dbshow import print_dataset, print_environment

# 'YYYY-MM-DD' 를 연*12+월 하나의 정수로 바꾼다. 두 값의 차가 곧 달력상 몇 달 차이다
MONTH_INDEX = (
    "(CAST(strftime('%Y', {col}) AS INTEGER) * 12"
    " + CAST(strftime('%m', {col}) AS INTEGER))"
)

FIRST_ORDER_SQL = """
    SELECT customer_id, MIN(order_date) AS first_date
    FROM customer_order
    GROUP BY customer_id
"""


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE customer_order (
            order_id    INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            order_date  TEXT    NOT NULL   -- 'YYYY-MM-DD'
        );
        INSERT INTO customer_order (order_id, customer_id, order_date) VALUES
            (1, 1, '2026-01-05'), (2, 1, '2026-01-20'), (3, 1, '2026-02-03'),
            (4, 1, '2026-04-11'), (5, 2, '2026-01-31'), (6, 2, '2026-02-01'),
            (7, 3, '2026-01-15'), (8, 9, '2026-01-08'), (9, 9, '2026-03-31'),
            (10, 4, '2026-02-10'), (11, 4, '2026-03-09'), (12, 4, '2026-03-28'),
            (13, 5, '2026-02-28'), (14, 5, '2026-04-01'), (15, 6, '2026-02-14'),
            (16, 7, '2026-03-03'), (17, 7, '2026-04-30'), (18, 8, '2026-03-20');
        """
    )
    return conn


def show_rows(conn, sql, header=None):
    print("  sql> " + " ".join(sql.split()))
    cursor = conn.execute(sql)
    names = header or [d[0] for d in cursor.description]
    print("   ", tuple(names))
    for row in cursor:
        print("   ", row)


def plan(conn, sql):
    """sqlite3 CLI 의 .eqp 와 같은 트리 모양으로 찍는다 (|-- 와 `--)."""
    print("  plan> " + " ".join(sql.split())[:70] + " ...")
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    children = {}
    for node_id, parent_id, _, detail in rows:
        children.setdefault(parent_id, []).append((node_id, detail))

    def draw(parent_id, indent):
        siblings = children.get(parent_id, [])
        for position, (node_id, detail) in enumerate(siblings):
            is_last = position == len(siblings) - 1
            print(f"    {indent}{'`--' if is_last else '|--'}{detail}")
            draw(node_id, indent + ("   " if is_last else "|  "))

    print("    QUERY PLAN")
    draw(0, "")


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("\n[1] 고객마다 첫 구매 월")
    show_rows(
        conn,
        f"""
        SELECT customer_id, first_date, strftime('%Y-%m', first_date) AS cohort
        FROM ({FIRST_ORDER_SQL})
        ORDER BY customer_id
        """,
    )

    month_of_first = MONTH_INDEX.format(col="f.first_date")
    month_of_order = MONTH_INDEX.format(col="o.order_date")
    offset_by_month = f"{month_of_order} - {month_of_first}"
    offset_by_days = (
        "CAST((julianday(o.order_date) - julianday(f.first_date)) / 30 AS INTEGER)"
    )
    joined = f"customer_order AS o JOIN ({FIRST_ORDER_SQL}) AS f USING (customer_id)"

    print("\n[2] 경과 월 — 일수/30 과 달력 월 차이가 갈리는 주문만")
    show_rows(
        conn,
        f"""
        SELECT o.customer_id, f.first_date, o.order_date,
               julianday(o.order_date) - julianday(f.first_date) AS days,
               {offset_by_days} AS by_days,
               {offset_by_month} AS by_month
        FROM {joined}
        WHERE {offset_by_days} <> {offset_by_month}
        ORDER BY o.customer_id, o.order_date
        """,
        header=["customer_id", "first_date", "order_date", "days", "by_days", "by_month"],
    )

    print("\n[3] 코호트 x 경과 월 — COUNT(*) 와 COUNT(DISTINCT)")
    show_rows(
        conn,
        f"""
        SELECT strftime('%Y-%m', f.first_date) AS cohort,
               {offset_by_month} AS month_no,
               COUNT(*) AS order_rows,
               COUNT(DISTINCT o.customer_id) AS customers
        FROM {joined}
        GROUP BY cohort, month_no
        ORDER BY cohort, month_no
        """,
        header=["cohort", "month_no", "order_rows", "customers"],
    )

    pivot_columns = ",\n".join(
        f"COUNT(DISTINCT CASE WHEN {offset_by_month} = {n} "
        f"THEN o.customer_id END) AS m{n}"
        for n in range(4)
    )
    pivot_sql = f"""
        SELECT strftime('%Y-%m', f.first_date) AS cohort,
               {pivot_columns}
        FROM {joined}
        GROUP BY cohort
        ORDER BY cohort
    """
    print("\n[4] 가로 표로 펼치기 — 경과 월마다 CASE 한 칸")
    show_rows(conn, pivot_sql, header=["cohort", "m0", "m1", "m2", "m3"])

    print("\n[5] 비율 — 정수끼리 나누면")
    show_rows(
        conn,
        f"""
        SELECT cohort, m0, m1, m1 / m0 AS int_div, ROUND(100.0 * m1 / m0, 1) AS pct
        FROM ({pivot_sql})
        """,
    )

    print("\n[6] 첫 구매일을 창 함수로 — 행마다 그 고객의 MIN 을 붙인다")
    window_sql = """
        SELECT customer_id, order_date,
               MIN(order_date) OVER (PARTITION BY customer_id) AS first_date
        FROM customer_order
        WHERE customer_id IN (1, 2)
        ORDER BY customer_id, order_date
    """
    show_rows(conn, window_sql)
    plan(conn, f"SELECT o.customer_id FROM {joined}")
    plan(conn, window_sql)


if __name__ == "__main__":
    main()
