"""카테고리별 매출이 전체에서 몇 %인지(구성비)를 SQL 로 구한다.

1) 정수끼리 나누면 소수가 버려진다 — 100 을 곱하는 자리와 100.0 의 차이
2) 전체 합을 붙이는 세 가지 방법 — 스칼라 부질의 · CROSS JOIN · SUM() OVER ()
3) GROUP BY 결과에 창 함수를 얹는 SUM(SUM(amount)) OVER ()
4) 지역 안에서의 비율 — PARTITION BY region
5) 반올림한 비율을 더하면 100 이 안 된다
6) 최대 나머지 방식으로 정수 % 의 합을 100 에 맞춘다
7) 틀리기 쉬운 자리 — WHERE 가 분모를 바꾸는 것, 합이 0 일 때
8) 세 방법의 실행계획
"""
import sqlite3

from dbshow import print_dataset, print_environment

BY_CATEGORY = """
    SELECT category, SUM(amount) AS amount
    FROM sale
    GROUP BY category
"""

SCALAR_SQL = f"""
    SELECT category, amount,
           ROUND(amount * 100.0 / (SELECT SUM(amount) FROM sale), 2) AS pct
    FROM ({BY_CATEGORY})
    ORDER BY category
"""

CROSS_SQL = f"""
    SELECT c.category, c.amount,
           ROUND(c.amount * 100.0 / t.total, 2) AS pct
    FROM ({BY_CATEGORY}) AS c
    CROSS JOIN (SELECT SUM(amount) AS total FROM sale) AS t
    ORDER BY c.category
"""

WINDOW_SQL = """
    SELECT category, SUM(amount) AS amount,
           ROUND(SUM(amount) * 100.0 / SUM(SUM(amount)) OVER (), 2) AS pct
    FROM sale
    GROUP BY category
    ORDER BY category
"""

# 반올림 합이 100 에서 어긋나는 두 묶음. 칸 이름은 sale 을 묶은 결과와 같게 맞춘다.
THREE_EQUAL = "SELECT 'a' AS category, 1 AS amount UNION ALL SELECT 'b', 1 UNION ALL SELECT 'c', 1"
HALF_TIES = "SELECT 'a' AS category, 125 AS amount UNION ALL SELECT 'b', 125 UNION ALL SELECT 'c', 750"

ROUND_SUM_SQL = """
    SELECT category, amount * 100.0 / SUM(amount) OVER () AS pct_exact,
           ROUND(amount * 100.0 / SUM(amount) OVER (), 0) AS pct_round0
    FROM ({parts})
"""


def largest_remainder_sql(parts_sql):
    """정수 % 를 최대 나머지 방식으로 나눠 준다.

    내림한 값의 합이 100 에 모자란 만큼, 버려진 소수 부분이 큰 순서로 1 씩 더한다.
    parts_sql 은 (category, amount) 두 칸을 내는 질의다.
    """
    return f"""
    WITH raw AS (
        SELECT category,
               SUM(amount) * 100.0 / SUM(SUM(amount)) OVER () AS exact_pct
        FROM ({parts_sql})
        GROUP BY category
    ),
    floored AS (
        SELECT category, exact_pct,
               CAST(exact_pct AS INTEGER) AS floor_pct,
               exact_pct - CAST(exact_pct AS INTEGER) AS remainder
        FROM raw
    ),
    ranked AS (
        SELECT *,
               100 - SUM(floor_pct) OVER () AS seats_left,
               ROW_NUMBER() OVER (ORDER BY remainder DESC, category) AS remainder_rank
        FROM floored
    )
    SELECT category, ROUND(exact_pct, 4) AS exact_pct, floor_pct,
           ROUND(remainder, 4) AS remainder, remainder_rank,
           floor_pct + (remainder_rank <= seats_left) AS final_pct
    FROM ranked
    ORDER BY category
"""


LARGEST_REMAINDER_SQL = largest_remainder_sql("SELECT category, amount FROM sale")


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE sale (
            sale_id  INTEGER PRIMARY KEY,
            region   TEXT    NOT NULL,
            category TEXT    NOT NULL,
            amount   INTEGER NOT NULL      -- 원 단위, 정수
        );
        INSERT INTO sale (sale_id, region, category, amount) VALUES
            (1,  'seoul', 'book',    1200),
            (2,  'seoul', 'food',    3300),
            (3,  'seoul', 'clothes', 2100),
            (4,  'seoul', 'toy',      700),
            (5,  'busan', 'book',     800),
            (6,  'busan', 'food',    1400),
            (7,  'busan', 'clothes',  900),
            (8,  'busan', 'toy',      600),
            (9,  'seoul', 'food',     500),
            (10, 'busan', 'stationery', 500);
        """
    )
    return conn


def show_rows(conn, sql, header=None):
    print("  sql> " + " ".join(sql.split())[:150] + " ...")
    cursor = conn.execute(sql)
    names = header or [d[0] for d in cursor.description]
    print("   ", tuple(names))
    for row in cursor:
        print("   ", row)


def plan(conn, sql):
    """sqlite3 CLI 의 .eqp 와 같은 트리 모양으로 찍는다 (|-- 와 `--)."""
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

    print("\n[1] 정수끼리 나누면 — 100 을 어디서 곱하느냐")
    show_rows(
        conn,
        f"""
        SELECT category, amount,
               amount / (SELECT SUM(amount) FROM sale) * 100      AS div_then_mul,
               amount * 100 / (SELECT SUM(amount) FROM sale)      AS mul_then_div,
               amount * 100.0 / (SELECT SUM(amount) FROM sale)    AS real_pct
        FROM ({BY_CATEGORY})
        ORDER BY category
        """,
    )

    print("\n[2-1] 스칼라 부질의로 전체 합을 붙인다")
    show_rows(conn, SCALAR_SQL)
    print("\n[2-2] CROSS JOIN 으로 전체 합을 붙인다")
    show_rows(conn, CROSS_SQL)
    print("\n[2-3] SUM(SUM(amount)) OVER () — GROUP BY 결과 위에 창 함수")
    show_rows(conn, WINDOW_SQL)

    print("\n[3] 지역 안에서의 비율 — PARTITION BY region")
    show_rows(
        conn,
        """
        SELECT region, category, SUM(amount) AS amount,
               ROUND(SUM(amount) * 100.0
                     / SUM(SUM(amount)) OVER (PARTITION BY region), 2) AS pct_in_region,
               ROUND(SUM(amount) * 100.0 / SUM(SUM(amount)) OVER (), 2) AS pct_of_all
        FROM sale
        GROUP BY region, category
        ORDER BY region, category
        """,
    )

    print("\n[4] 반올림한 비율을 더하면")
    show_rows(
        conn,
        f"""
        SELECT SUM(ROUND(pct_exact, 0)) AS sum_round0,
               SUM(ROUND(pct_exact, 1)) AS sum_round1,
               SUM(pct_exact)           AS sum_exact
        FROM (
            SELECT SUM(amount) * 100.0 / SUM(SUM(amount)) OVER () AS pct_exact
            FROM sale GROUP BY category
        )
        """,
    )
    show_rows(
        conn,
        """
        SELECT category, SUM(amount) * 100.0 / SUM(SUM(amount)) OVER () AS pct_exact,
               ROUND(SUM(amount) * 100.0 / SUM(SUM(amount)) OVER (), 0) AS pct_round0
        FROM sale GROUP BY category ORDER BY category
        """,
    )

    print("\n[4-2] 세 몫이 똑같을 때 (1:1:1)")
    show_rows(conn, ROUND_SUM_SQL.format(parts=THREE_EQUAL))
    show_rows(
        conn,
        f"SELECT SUM(pct_round0) AS sum_round0 FROM ({ROUND_SUM_SQL.format(parts=THREE_EQUAL)})",
    )
    print("\n[4-3] .5 가 둘 있을 때 (125:125:750)")
    show_rows(conn, ROUND_SUM_SQL.format(parts=HALF_TIES))
    show_rows(
        conn,
        f"SELECT SUM(pct_round0) AS sum_round0 FROM ({ROUND_SUM_SQL.format(parts=HALF_TIES)})",
    )

    print("\n[5-1] 최대 나머지 방식 — sale 표")
    show_rows(conn, LARGEST_REMAINDER_SQL)
    show_rows(
        conn,
        f"SELECT SUM(final_pct) AS sum_final FROM ({LARGEST_REMAINDER_SQL})",
    )
    for label, parts in (("1:1:1", THREE_EQUAL), ("125:125:750", HALF_TIES)):
        print(f"\n[5-2] 최대 나머지 방식 — {label}")
        sql = largest_remainder_sql(parts)
        show_rows(conn, sql)
        show_rows(conn, f"SELECT SUM(final_pct) AS sum_final FROM ({sql})")

    print("\n[6-1] WHERE 로 거르면 분모도 바뀐다 — 창 함수는 WHERE 뒤에 계산된다")
    show_rows(
        conn,
        """
        SELECT category, SUM(amount) AS amount,
               ROUND(SUM(amount) * 100.0 / SUM(SUM(amount)) OVER (), 2) AS pct
        FROM sale
        WHERE category IN ('book', 'toy')
        GROUP BY category
        ORDER BY category
        """,
    )
    print("[6-2] 전체 대비 비율을 유지하려면 거르기 전에 계산하고 바깥에서 거른다")
    show_rows(
        conn,
        f"SELECT * FROM ({WINDOW_SQL}) WHERE category IN ('book', 'toy')",
    )

    print("\n[7] 합이 0 이면 — 0 으로 나누기")
    show_rows(
        conn,
        """
        SELECT 1200 * 100.0 / 0 AS div_zero,
               typeof(1200 * 100.0 / 0) AS type,
               1200 * 100.0 / NULLIF(0, 0) AS with_nullif
        """,
    )

    print("\n[8-1] 실행계획 — 스칼라 부질의")
    plan(conn, SCALAR_SQL)
    print("\n[8-2] 실행계획 — CROSS JOIN")
    plan(conn, CROSS_SQL)
    print("\n[8-3] 실행계획 — SUM(SUM(amount)) OVER ()")
    plan(conn, WINDOW_SQL)
    conn.close()


if __name__ == "__main__":
    main()
