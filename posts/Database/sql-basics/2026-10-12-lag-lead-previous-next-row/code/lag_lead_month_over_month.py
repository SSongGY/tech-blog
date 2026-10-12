"""매장별 월 매출에 LAG·LEAD 를 붙여 전월 대비 증감을 구한다.

함정이 드러나도록 데이터를 일부러 비틀어 둔다.
- 강남점 4월 매출은 집계 전이라 NULL 이다 (행은 있고 값이 비었다)
- 판교점은 3월 행이 아예 없다 (행이 없다)
LAG 는 "앞 행" 을 보지 "앞 달" 을 보지 않으므로 이 두 경우가 서로 다르게 나온다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

MONTHLY_SALES = [
    ("강남점", "2026-01", 120),
    ("강남점", "2026-02", 150),
    ("강남점", "2026-03", 135),
    ("강남점", "2026-04", None),
    ("강남점", "2026-05", 160),
    ("판교점", "2026-01", 80),
    ("판교점", "2026-02", 95),
    ("판교점", "2026-04", 110),
    ("판교점", "2026-05", 105),
]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("""
CREATE TABLE monthly_sales (
    store       TEXT    NOT NULL,
    sales_month TEXT    NOT NULL,
    amount      INTEGER,
    PRIMARY KEY (store, sales_month)
)
""")
    conn.executemany("INSERT INTO monthly_sales VALUES (?, ?, ?)", MONTHLY_SALES)
    return conn


def run(conn: sqlite3.Connection, title: str, sql: str) -> list[tuple]:
    print(f"\n-- {title}")
    for line in sql.strip().splitlines():
        print(f"   {line}")
    try:
        cursor = conn.execute(sql)
    except sqlite3.Error as exc:
        print(f"   에러: {exc}")
        return []
    header = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    print("   => " + " | ".join(header))
    for row in rows:
        print("      " + " | ".join(str(v) for v in row))
    print(f"   ({len(rows)}행)")
    return rows


def main() -> None:
    conn = build_database()
    try:
        print_environment()
        print_dataset(conn)

        run(conn, "1. 한 매장 안에서 앞 행과 뒤 행", """
SELECT sales_month, amount,
       LAG(amount)  OVER (ORDER BY sales_month) AS prev_amount,
       LEAD(amount) OVER (ORDER BY sales_month) AS next_amount
FROM monthly_sales
WHERE store = '판교점'
ORDER BY sales_month
""")

        # PARTITION BY 가 없으면 두 매장이 한 줄로 이어져 다른 매장의 값을 끌어온다
        run(conn, "2. PARTITION BY 없이 두 매장을 한꺼번에", """
SELECT store, sales_month, amount,
       LAG(amount) OVER (ORDER BY store, sales_month) AS prev_amount
FROM monthly_sales
ORDER BY store, sales_month
""")

        run(conn, "3. PARTITION BY store — 매장이 바뀌면 첫 행은 NULL", """
SELECT store, sales_month, amount,
       LAG(amount) OVER (PARTITION BY store ORDER BY sales_month) AS prev_amount,
       amount - LAG(amount) OVER (PARTITION BY store ORDER BY sales_month) AS diff
FROM monthly_sales
ORDER BY store, sales_month
""")

        # 세 번째 인자는 "앞 행이 없을 때" 만 쓰인다. 앞 행의 값이 NULL 인 것과는 다르다
        run(conn, "4. 기본값 인자 LAG(amount, 1, 0)", """
SELECT store, sales_month, amount,
       LAG(amount, 1, 0) OVER (PARTITION BY store ORDER BY sales_month) AS prev_or_zero,
       amount - LAG(amount, 1, 0) OVER (PARTITION BY store ORDER BY sales_month) AS diff
FROM monthly_sales
WHERE store = '강남점'
ORDER BY sales_month
""")

        run(conn, "5. offset 을 바꾸면 — 0, 1, 2", """
SELECT sales_month, amount,
       LAG(amount, 0) OVER w AS lag0,
       LAG(amount, 1) OVER w AS lag1,
       LAG(amount, 2) OVER w AS lag2
FROM monthly_sales
WHERE store = '판교점'
WINDOW w AS (ORDER BY sales_month)
ORDER BY sales_month
""")

        # 판교점 4월의 "앞 행" 은 3월이 아니라 2월이다
        run(conn, "6. 빠진 달 — 앞 행의 달도 같이 꺼내 본다", """
SELECT store, sales_month, amount,
       LAG(sales_month) OVER (PARTITION BY store ORDER BY sales_month) AS prev_month,
       LAG(amount)      OVER (PARTITION BY store ORDER BY sales_month) AS prev_amount
FROM monthly_sales
WHERE store = '판교점'
ORDER BY sales_month
""")

        # 달력 표를 만들어 LEFT JOIN 하면 빠진 달이 NULL 행으로 들어와 LAG 가 바로 앞 달을 본다
        run(conn, "7. 달력을 먼저 깔고 LAG", """
WITH RECURSIVE calendar(sales_month) AS (
    SELECT '2026-01'
    UNION ALL
    SELECT strftime('%Y-%m', sales_month || '-01', '+1 month')
    FROM calendar
    WHERE sales_month < '2026-05'
)
SELECT c.sales_month, s.amount,
       LAG(s.amount) OVER (ORDER BY c.sales_month) AS prev_amount
FROM calendar AS c
LEFT JOIN monthly_sales AS s
       ON s.sales_month = c.sales_month AND s.store = '판교점'
ORDER BY c.sales_month
""")

        run(conn, "8. WHERE 에 LAG 를 바로 쓰면", """
SELECT store, sales_month, amount
FROM monthly_sales
WHERE amount > LAG(amount) OVER (PARTITION BY store ORDER BY sales_month)
""")

        run(conn, "9. 서브쿼리로 감싸서 거른다 — 전월보다 늘어난 달", """
SELECT store, sales_month, amount, prev_amount
FROM (SELECT store, sales_month, amount,
             LAG(amount) OVER (PARTITION BY store ORDER BY sales_month) AS prev_amount
      FROM monthly_sales)
WHERE amount > prev_amount
ORDER BY store, sales_month
""")

        run(conn, "10. offset 에 음수를 주면", """
SELECT sales_month, LAG(amount, -1) OVER (ORDER BY sales_month) AS prev_amount
FROM monthly_sales
WHERE store = '판교점'
""")

        # 문서는 lag·lead 가 프레임을 무시한다고 적는다. 현재 행만 담는 프레임을 줘 본다
        run(conn, "11. 프레임을 현재 행 하나로 좁혀도", """
SELECT sales_month, amount,
       LAG(amount) OVER (ORDER BY sales_month
                         ROWS BETWEEN CURRENT ROW AND CURRENT ROW) AS prev_amount,
       FIRST_VALUE(amount) OVER (ORDER BY sales_month
                         ROWS BETWEEN CURRENT ROW AND CURRENT ROW) AS first_in_frame
FROM monthly_sales
WHERE store = '판교점'
ORDER BY sales_month
""")

        # 같은 결과를 자기 조인으로 — "바로 앞 달" 을 찾는 하위 질의가 행마다 돈다
        self_join = run(conn, "12. 자기 조인으로 같은 값을 구하면", """
SELECT cur.store, cur.sales_month, cur.amount,
       prev.amount AS prev_amount
FROM monthly_sales AS cur
LEFT JOIN monthly_sales AS prev
       ON prev.store = cur.store
      AND prev.sales_month = (SELECT MAX(p.sales_month)
                              FROM monthly_sales AS p
                              WHERE p.store = cur.store
                                AND p.sales_month < cur.sales_month)
ORDER BY cur.store, cur.sales_month
""")
        window = conn.execute("""
SELECT store, sales_month, amount,
       LAG(amount) OVER (PARTITION BY store ORDER BY sales_month)
FROM monthly_sales
ORDER BY store, sales_month
""").fetchall()
        print(f"\n   자기 조인 결과와 LAG 결과가 같은가: {self_join == window}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
