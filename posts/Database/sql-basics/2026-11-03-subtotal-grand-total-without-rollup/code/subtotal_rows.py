"""GROUP BY 결과에 소계·총계 행을 붙이는 방법을 SQLite 로 돌려 본다.

SQLite 3.49.1 / Python 3.13.5 에서 돌렸다. 외부 의존성은 없다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

SALES = [
    ("서울", "노트북", 300), ("서울", "노트북", 200), ("서울", "모니터", 150),
    ("부산", "노트북", 250), ("부산", "모니터", 100),
    ("화성", "모니터", 120), ("화성", "키보드", 30),
]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE sale (
            sale_id INTEGER PRIMARY KEY,
            region  TEXT    NOT NULL,
            product TEXT    NOT NULL,
            amount  INTEGER NOT NULL
        )
        """
    )
    conn.executemany("INSERT INTO sale(region, product, amount) VALUES (?, ?, ?)", SALES)
    conn.commit()
    return conn


def show_plan(conn: sqlite3.Connection, sql: str) -> None:
    """sqlite3 CLI 가 그리는 트리와 같은 모양으로 detail 을 찍는다."""
    rows = list(conn.execute("EXPLAIN QUERY PLAN " + sql))
    children: dict[int, list[tuple[int, str]]] = {}
    for node_id, parent_id, _, detail in rows:
        children.setdefault(parent_id, []).append((node_id, detail))

    def walk(parent_id: int, prefix: str) -> None:
        kids = children.get(parent_id, [])
        for index, (node_id, detail) in enumerate(kids):
            last = index == len(kids) - 1
            print(f"{prefix}{'`--' if last else '|--'}{detail}")
            walk(node_id, prefix + ("   " if last else "|  "))

    print("QUERY PLAN")
    walk(0, "")


def show_rows(conn: sqlite3.Connection, sql: str) -> None:
    for row in conn.execute(sql):
        cells = ["NULL" if v is None else str(v) for v in row]
        print("  " + "  ".join(f"{c:<6}" if not c.lstrip('-').isdigit() else f"{c:>5}"
                               for c in cells))


def section(title: str) -> None:
    print()
    print("=" * 62)
    print(title)
    print("=" * 62)


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)

    section("1. 지역별 합계 — 여기까지는 GROUP BY 한 줄이다")
    show_rows(conn, "SELECT region, SUM(amount) FROM sale GROUP BY region ORDER BY region")

    section("2. ROLLUP 은 SQLite 3.49.1 에 없다")
    try:
        conn.execute("SELECT region, SUM(amount) FROM sale GROUP BY ROLLUP(region)")
    except sqlite3.OperationalError as exc:
        print(f"  GROUP BY ROLLUP(region) → {exc}")

    section("3. UNION ALL 로 총계 행을 붙인다 — 그런데 줄이 중간에 낀다")
    naive = """
        SELECT region, SUM(amount) AS total FROM sale GROUP BY region
        UNION ALL
        SELECT '합계', SUM(amount) FROM sale
        ORDER BY region
    """
    show_rows(conn, naive)
    print("  → ORDER BY region 이 '합계' 도 지역 이름처럼 정렬했다")

    section("4. 정렬 키 컬럼을 따로 둔다")
    keyed = """
        SELECT 0 AS ord, region, SUM(amount) AS total FROM sale GROUP BY region
        UNION ALL
        SELECT 1, '합계', SUM(amount) FROM sale
        ORDER BY ord, region
    """
    show_rows(conn, keyed)

    section("5. 두 단계 — 지역×제품, 지역 소계, 총계를 한 결과에")
    wrong_order = """
        SELECT region, product, SUM(amount) AS total, 0 AS lvl
        FROM sale GROUP BY region, product
        UNION ALL
        SELECT region, NULL, SUM(amount), 1 FROM sale GROUP BY region
        UNION ALL
        SELECT NULL, NULL, SUM(amount), 2 FROM sale
        ORDER BY region IS NULL, region, lvl, product
    """
    try:
        show_rows(conn, wrong_order)
    except sqlite3.OperationalError as exc:
        print(f"  ORDER BY region IS NULL, ... → {exc}")
    print("  → UNION 으로 묶인 질의의 ORDER BY 에는 식을 못 쓴다. 결과 컬럼만 가리킨다")
    two_level = """
        SELECT region, product, SUM(amount) AS total, 0 AS lvl, 0 AS is_total
        FROM sale GROUP BY region, product
        UNION ALL
        SELECT region, NULL, SUM(amount), 1, 0 FROM sale GROUP BY region
        UNION ALL
        SELECT NULL, NULL, SUM(amount), 2, 1 FROM sale
        ORDER BY is_total, region, lvl, product
    """
    show_rows(conn, two_level)
    print("  → NULL 이 '소계·총계' 표시다. 보일 때만 COALESCE(product, '소계') 로 바꾼다")

    section("6. 질의 계획 — UNION ALL 은 표를 읽는 횟수만큼 SCAN 이 찍힌다")
    show_plan(conn, keyed)

    section("7. 집계를 CTE 에 한 번만 하고, 총계는 그 위에서 더한다")
    cte = """
        WITH by_region AS (
            SELECT region, SUM(amount) AS total FROM sale GROUP BY region
        )
        SELECT 0 AS ord, region, total FROM by_region
        UNION ALL
        SELECT 1, '합계', SUM(total) FROM by_region
        ORDER BY ord, region
    """
    show_rows(conn, cte)
    show_plan(conn, cte)
    print("  → 힌트를 안 붙여도 두 번 참조되는 CTE 는 MATERIALIZE 로 한 번만 읽었다")
    print("-- NOT MATERIALIZED 를 붙이면")
    show_plan(conn, cte.replace("by_region AS (", "by_region AS NOT MATERIALIZED ("))

    section("8. 행을 더하지 않고 칸을 더한다 — SUM() OVER ()")
    window = """
        SELECT region, SUM(amount) AS total,
               SUM(SUM(amount)) OVER () AS grand_total,
               ROUND(100.0 * SUM(amount) / SUM(SUM(amount)) OVER (), 1) AS pct
        FROM sale GROUP BY region ORDER BY region
    """
    show_rows(conn, window)
    print("  → 집계 결과 위에 윈도우가 한 번 더 걸린다. 비율을 같은 줄에 적을 때 쓴다")

    section("9. 소계가 틀리기 쉬운 자리 — AVG 의 소계는 평균의 평균이 아니다")
    show_rows(
        conn,
        """
        SELECT 0 AS ord, region, AVG(amount) AS avg_amount FROM sale GROUP BY region
        UNION ALL
        SELECT 1, '평균의 평균', AVG(a) FROM (SELECT AVG(amount) AS a FROM sale GROUP BY region)
        UNION ALL
        SELECT 2, '전체 평균', AVG(amount) FROM sale
        ORDER BY ord, region
        """,
    )
    conn.close()


if __name__ == "__main__":
    main()
