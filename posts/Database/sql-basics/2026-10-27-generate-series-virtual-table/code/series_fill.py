"""없는 행을 만들어 쓰는 세 가지 방법 — generate_series · 재귀 CTE · 집계용 보조 표.

일별 집계에서 주문이 없던 날이 통째로 빠지는 문제를 고치면서,
기준 행을 만들어 내는 방법들을 같은 데이터 위에서 대조한다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

SCHEMA = """
CREATE TABLE order_log (
    order_id   INTEGER PRIMARY KEY,
    ordered_on TEXT    NOT NULL,
    amount     INTEGER NOT NULL
);
"""

ORDER_ROWS = [
    (1, "2026-03-01", 12000),
    (2, "2026-03-01", 8000),
    (3, "2026-03-02", 31000),
    (4, "2026-03-05", 5000),
    (5, "2026-03-05", 27000),
    (6, "2026-03-05", 9000),
    (7, "2026-03-06", 14000),
    (8, "2026-03-09", 22000),
    (9, "2026-03-10", 6000),
]

FIRST_DAY = "2026-03-01"
LAST_DAY = "2026-03-10"


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO order_log VALUES (?, ?, ?)", ORDER_ROWS)
    return conn


def section(title: str) -> None:
    print()
    print("=" * 64)
    print(title)
    print("=" * 64)


def show_rows(conn: sqlite3.Connection, sql: str, params=()) -> None:
    cursor = conn.execute(sql, params)
    headers = [d[0] for d in cursor.description]
    rows = [["NULL" if v is None else str(v) for v in row] for row in cursor.fetchall()]
    widths = [
        max(len(headers[i]), *(len(r[i]) for r in rows)) if rows else len(headers[i])
        for i in range(len(headers))
    ]
    print("  " + " | ".join(h.ljust(w) for h, w in zip(headers, widths)))
    print("  " + "-+-".join("-" * w for w in widths))
    for row in rows:
        print("  " + " | ".join(c.rjust(w) for c, w in zip(row, widths)))
    print(f"  ({len(rows)}행)")


def show_plan(conn: sqlite3.Connection, title: str, sql: str, params=()) -> None:
    """EXPLAIN QUERY PLAN 의 id/parent 를 그대로 살려 트리로 찍는다."""
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql, params).fetchall()
    children: dict[int, list[tuple[int, str]]] = {}
    for node_id, parent, _unused, detail in rows:
        children.setdefault(parent, []).append((node_id, detail))

    print(f"\n-- {title}")
    print("  QUERY PLAN")

    def walk(parent: int, prefix: str) -> None:
        items = children.get(parent, [])
        for index, (node_id, detail) in enumerate(items):
            last = index == len(items) - 1
            print(f"  {prefix}{'`--' if last else '|--'} {detail}")
            walk(node_id, prefix + ("    " if last else "|   "))

    walk(0, "")


def step_check_generate_series(conn: sqlite3.Connection) -> None:
    section("1. 이 빌드에 generate_series 가 있는가")
    modules = [name for (name,) in conn.execute(
        "SELECT name FROM pragma_module_list ORDER BY name"
    )]
    print("  등록된 가상 테이블 모듈:", ", ".join(modules))
    try:
        rows = conn.execute("SELECT value FROM generate_series(1, 5)").fetchall()
        print("  generate_series(1, 5) ->", [r[0] for r in rows])
    except sqlite3.Error as exc:
        print(f"  generate_series(1, 5) -> {type(exc).__name__}: {exc}")


def step_naive_group_by(conn: sqlite3.Connection) -> None:
    section("2. 그냥 GROUP BY 하면 — 주문 없는 날이 사라진다")
    show_rows(conn, """
        SELECT ordered_on AS day, COUNT(*) AS orders, SUM(amount) AS total
          FROM order_log
         GROUP BY ordered_on
         ORDER BY day
    """)


def step_recursive_calendar(conn: sqlite3.Connection) -> None:
    section("3. 재귀 CTE 로 달력을 만든다")
    calendar_sql = """
        WITH RECURSIVE calendar(day) AS (
            SELECT ?
            UNION ALL
            SELECT date(day, '+1 day') FROM calendar WHERE day < ?
        )
        SELECT day FROM calendar
    """
    show_rows(conn, calendar_sql, (FIRST_DAY, LAST_DAY))

    print("\n  달력을 왼쪽에 두고 주문을 붙인다")
    filled_sql = """
        WITH RECURSIVE calendar(day) AS (
            SELECT ?
            UNION ALL
            SELECT date(day, '+1 day') FROM calendar WHERE day < ?
        )
        SELECT c.day,
               COUNT(o.order_id)          AS orders,
               COALESCE(SUM(o.amount), 0) AS total
          FROM calendar c
          LEFT JOIN order_log o ON o.ordered_on = c.day
         GROUP BY c.day
         ORDER BY c.day
    """
    show_rows(conn, filled_sql, (FIRST_DAY, LAST_DAY))
    show_plan(conn, "달력 LEFT JOIN 의 실행계획", filled_sql, (FIRST_DAY, LAST_DAY))


def step_stop_condition(conn: sqlite3.Connection) -> None:
    section("4. 멈추는 조건 — WHERE 를 빠뜨리면")
    print("  WHERE 없이 LIMIT 만으로 멈추는 형태 (공식 문서가 권하는 안전장치)")
    show_rows(conn, """
        WITH RECURSIVE cnt(x) AS (
            SELECT 1
            UNION ALL
            SELECT x + 1 FROM cnt
            LIMIT 5
        )
        SELECT x FROM cnt
    """)

    print("\n  WHERE 도 LIMIT 도 없으면 — 끝나지 않으므로 바깥 LIMIT 으로 잘라 본다")
    rows = conn.execute("""
        SELECT x FROM (
            WITH RECURSIVE cnt(x) AS (
                SELECT 1
                UNION ALL
                SELECT x + 1 FROM cnt
            )
            SELECT x FROM cnt
        ) LIMIT 3
    """).fetchall()
    print("  바깥 LIMIT 3 으로 받은 값:", [r[0] for r in rows])
    print("  바깥 LIMIT 이 없었다면 이 질의는 스스로 멈추지 않는다")


def step_tally_table(conn: sqlite3.Connection) -> None:
    section("5. 보조 표(tally table) — 재귀 없이 자리를 만든다")
    tally_sql = """
        WITH digit(d) AS (
            VALUES (0),(1),(2),(3),(4),(5),(6),(7),(8),(9)
        ),
        seq(n) AS (
            SELECT tens.d * 10 + ones.d FROM digit tens, digit ones
        )
        SELECT date(?, '+' || n || ' day') AS day
          FROM seq
         WHERE n <= CAST(julianday(?) - julianday(?) AS INTEGER)
         ORDER BY day
    """
    show_rows(conn, tally_sql, (FIRST_DAY, LAST_DAY, FIRST_DAY))
    show_plan(conn, "보조 표 방식의 실행계획", tally_sql, (FIRST_DAY, LAST_DAY, FIRST_DAY))


def step_join_direction(conn: sqlite3.Connection) -> None:
    section("6. 조인 방향을 뒤집으면 — 빈칸이 다시 사라진다")
    print("  calendar 를 오른쪽에 두고 LEFT JOIN 하면 기준이 order_log 가 된다")
    show_rows(conn, """
        WITH RECURSIVE calendar(day) AS (
            SELECT ?
            UNION ALL
            SELECT date(day, '+1 day') FROM calendar WHERE day < ?
        )
        SELECT o.ordered_on AS day, COUNT(*) AS orders
          FROM order_log o
          LEFT JOIN calendar c ON c.day = o.ordered_on
         GROUP BY o.ordered_on
         ORDER BY day
    """, (FIRST_DAY, LAST_DAY))


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)

    step_check_generate_series(conn)
    step_naive_group_by(conn)
    step_recursive_calendar(conn)
    step_stop_condition(conn)
    step_tally_table(conn)
    step_join_direction(conn)


if __name__ == "__main__":
    main()
