"""SUM() OVER 로 누적합과 이동평균을 구하고, 프레임(ROWS·RANGE·GROUPS)에 따라 값이 갈리는 자리를 본다.

프레임 종류는 ORDER BY 값이 같은 행(피어)이 있을 때만 차이가 난다.
그래서 같은 날짜에 주문이 두 건씩 들어온 날(10-03, 10-05)을 일부러 넣는다.
10-04 는 주문이 없는 날이라 "최근 3일"이 행 3개인지 날짜 3일인지가 갈린다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

ORDERS = [
    (1, "2026-10-01", 1, 100),
    (2, "2026-10-02", 2, 200),
    (3, "2026-10-03", 3, 300),
    (4, "2026-10-03", 3, 50),
    (5, "2026-10-05", 5, 400),
    (6, "2026-10-05", 5, 10),
    (7, "2026-10-06", 6, 500),
]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    # day_no 는 10월의 일(日)이다. RANGE n PRECEDING 은 숫자 거리로 범위를 잡으므로 날짜 문자열 대신 쓴다
    conn.execute("""
CREATE TABLE daily_order (
    order_id   INTEGER PRIMARY KEY,
    order_date TEXT    NOT NULL,
    day_no     INTEGER NOT NULL,
    amount     INTEGER NOT NULL
)
""")
    conn.executemany("INSERT INTO daily_order VALUES (?, ?, ?, ?)", ORDERS)
    return conn


def run(conn: sqlite3.Connection, title: str, sql: str) -> None:
    print(f"\n-- {title}")
    for line in sql.strip().splitlines():
        print(f"   {line}")
    try:
        cursor = conn.execute(sql)
    except sqlite3.Error as exc:
        print(f"   에러: {exc}")
        return
    header = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    print("   => " + " | ".join(header))
    for row in rows:
        print("      " + " | ".join(str(v) for v in row))
    print(f"   ({len(rows)}행)")


def main() -> None:
    conn = build_database()
    try:
        print_environment()
        print_dataset(conn)

        run(conn, "1. 누적합 — 프레임을 안 적으면", """
SELECT order_id, order_date, amount,
       SUM(amount) OVER (ORDER BY order_date) AS running_total
FROM daily_order
ORDER BY order_date, order_id
""")

        run(conn, "2. 기본 프레임을 풀어 쓴 것과 ROWS 로 바꾼 것을 나란히", """
SELECT order_id, order_date, amount,
       SUM(amount) OVER (ORDER BY order_date
                         RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS range_total,
       SUM(amount) OVER (ORDER BY order_date
                         ROWS  BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS rows_total
FROM daily_order
ORDER BY order_date, order_id
""")

        # ROWS 누적합은 피어 사이 순서가 정해지지 않으면 그 사이 값이 흔들린다. 키를 하나 더 준다
        run(conn, "3. ROWS 누적합에 동점 처리 기준(order_id)을 더하면", """
SELECT order_id, order_date, amount,
       SUM(amount) OVER (ORDER BY order_date, order_id
                         ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS rows_total
FROM daily_order
ORDER BY order_date, order_id
""")

        run(conn, "4. OVER () — ORDER BY 가 없으면 프레임이 파티션 전체", """
SELECT order_id, amount,
       SUM(amount) OVER () AS grand_total,
       ROUND(100.0 * amount / SUM(amount) OVER (), 1) AS pct
FROM daily_order
ORDER BY order_id
""")

        run(conn, "5. 최근 3일 이동평균 — 행 3개(ROWS) / 날짜 3일(RANGE) / 날짜 묶음 3개(GROUPS)", """
SELECT order_id, day_no, amount,
       SUM(amount) OVER (ORDER BY day_no, order_id
                         ROWS   BETWEEN 2 PRECEDING AND CURRENT ROW) AS rows_3,
       SUM(amount) OVER (ORDER BY day_no
                         RANGE  BETWEEN 2 PRECEDING AND CURRENT ROW) AS range_3,
       SUM(amount) OVER (ORDER BY day_no
                         GROUPS BETWEEN 2 PRECEDING AND CURRENT ROW) AS groups_3
FROM daily_order
ORDER BY day_no, order_id
""")

        run(conn, "6. 프레임에 들어간 행 수를 COUNT(*) 로 확인", """
SELECT order_id, day_no,
       COUNT(*) OVER (ORDER BY day_no, order_id
                      ROWS   BETWEEN 2 PRECEDING AND CURRENT ROW) AS rows_n,
       COUNT(*) OVER (ORDER BY day_no
                      RANGE  BETWEEN 2 PRECEDING AND CURRENT ROW) AS range_n,
       COUNT(*) OVER (ORDER BY day_no
                      GROUPS BETWEEN 2 PRECEDING AND CURRENT ROW) AS groups_n
FROM daily_order
ORDER BY day_no, order_id
""")

        run(conn, "7. 이동평균은 AVG — 행이 모자란 첫 줄도 평균을 낸다", """
SELECT order_id, day_no, amount,
       ROUND(AVG(amount) OVER (ORDER BY day_no, order_id
                               ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS moving_avg_3
FROM daily_order
ORDER BY day_no, order_id
""")

        run(conn, "8. RANGE n PRECEDING 에 ORDER BY 키가 둘이면", """
SELECT order_id,
       SUM(amount) OVER (ORDER BY day_no, order_id
                         RANGE BETWEEN 2 PRECEDING AND CURRENT ROW) AS range_3
FROM daily_order
""")

        run(conn, "9. RANGE n PRECEDING 에 문자열 날짜를 쓰면", """
SELECT order_id, order_date,
       SUM(amount) OVER (ORDER BY order_date
                         RANGE BETWEEN 2 PRECEDING AND CURRENT ROW) AS range_3
FROM daily_order
ORDER BY order_date, order_id
""")

        run(conn, "10. 프레임 끝을 앞쪽에 두면 — CURRENT ROW AND 1 PRECEDING", """
SELECT order_id,
       SUM(amount) OVER (ORDER BY order_id
                         ROWS BETWEEN CURRENT ROW AND 1 PRECEDING) AS bad_frame
FROM daily_order
""")

        run(conn, "11. 파티션마다 누적 — 같은 날 안에서만 누적", """
SELECT order_id, order_date, amount,
       SUM(amount) OVER (PARTITION BY order_date ORDER BY order_id) AS day_running
FROM daily_order
ORDER BY order_date, order_id
""")

        # 9번과 같은 문자열 날짜를 julianday() 로 숫자로 바꾸면 5번의 range_3 과 같아져야 한다
        run(conn, "12. 문자열 날짜를 julianday() 로 숫자로 바꿔 RANGE 를 걸면", """
SELECT order_id, order_date,
       SUM(amount) OVER (ORDER BY julianday(order_date)
                         RANGE BETWEEN 2 PRECEDING AND CURRENT ROW) AS range_3
FROM daily_order
ORDER BY order_date, order_id
""")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
