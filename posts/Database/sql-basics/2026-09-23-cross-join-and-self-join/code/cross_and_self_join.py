"""CROSS JOIN 과 SELF JOIN — 실제로 쓰는 자리 두 가지를 확인한다.

메모리 SQLite에 매장 2곳과 닷새치 매출, 직원 5명을 넣고
빠진 날짜를 0으로 채우는 질의(CROSS JOIN)와 같은 표끼리 비교하는 질의(SELF JOIN)를 돌린다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

STORES = [
    (1, "강남점"),
    (2, "판교점"),
]

# 판교점은 09-02·09-04 에 매출이 없고, 두 매장 모두 09-05 에 매출이 없다
SALES = [
    (1, 1, "2026-09-01", 120),
    (2, 1, "2026-09-01", 30),
    (3, 1, "2026-09-02", 80),
    (4, 1, "2026-09-03", 60),
    (5, 1, "2026-09-04", 90),
    (6, 2, "2026-09-01", 50),
    (7, 2, "2026-09-03", 70),
]

# manager_id 가 NULL 인 사람이 대표 — SELF JOIN 에서 짝이 없는 행이 된다
EMPLOYEES = [
    (1, "한지우", None, "경영", 900),
    (2, "오민재", 1, "개발", 700),
    (3, "윤서아", 2, "개발", 750),
    (4, "장하준", 2, "개발", 500),
    (5, "임채원", 1, "영업", 600),
]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE store (
            id   INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );
        CREATE TABLE sale (
            id       INTEGER PRIMARY KEY,
            store_id INTEGER NOT NULL REFERENCES store(id),
            sold_on  TEXT NOT NULL,
            amount   INTEGER NOT NULL
        );
        CREATE TABLE employee (
            id         INTEGER PRIMARY KEY,
            name       TEXT NOT NULL,
            manager_id INTEGER REFERENCES employee(id),
            dept       TEXT NOT NULL,
            salary     INTEGER NOT NULL
        );
        """
    )
    conn.executemany("INSERT INTO store VALUES (?, ?)", STORES)
    conn.executemany("INSERT INTO sale VALUES (?, ?, ?, ?)", SALES)
    conn.executemany("INSERT INTO employee VALUES (?, ?, ?, ?, ?)", EMPLOYEES)
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


# 09-01 부터 닷새를 만든다 — 달력 표가 없을 때 재귀 CTE 로 대신한다
CALENDAR_CTE = """
    WITH RECURSIVE calendar(day) AS (
        SELECT '2026-09-01'
        UNION ALL
        SELECT date(day, '+1 day') FROM calendar WHERE day < '2026-09-05'
    )
"""


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("\n=== 1. CROSS JOIN 의 행 수 ===")
    show(
        conn,
        "1-A 매장 x 날짜",
        CALENDAR_CTE
        + """
        SELECT t.name, c.day
        FROM store AS t
        CROSS JOIN calendar AS c
        ORDER BY t.id, c.day
        """,
    )

    print("\n=== 2. 매장별 일 매출 — 빠진 날짜 ===")
    show(
        conn,
        "2-A sale 만 GROUP BY",
        """
        SELECT t.name, s.sold_on, SUM(s.amount)
        FROM sale AS s
        INNER JOIN store AS t ON t.id = s.store_id
        GROUP BY t.id, s.sold_on
        ORDER BY t.id, s.sold_on
        """,
    )
    show(
        conn,
        "2-B 달력 LEFT JOIN sale (매장 구분 없이)",
        CALENDAR_CTE
        + """
        SELECT c.day, s.store_id, COALESCE(SUM(s.amount), 0)
        FROM calendar AS c
        LEFT JOIN sale AS s ON s.sold_on = c.day
        GROUP BY c.day, s.store_id
        ORDER BY c.day, s.store_id
        """,
    )
    show(
        conn,
        "2-C 매장 CROSS JOIN 달력 LEFT JOIN sale",
        CALENDAR_CTE
        + """
        SELECT t.name, c.day, COALESCE(SUM(s.amount), 0)
        FROM store AS t
        CROSS JOIN calendar AS c
        LEFT JOIN sale AS s ON s.store_id = t.id AND s.sold_on = c.day
        GROUP BY t.id, c.day
        ORDER BY t.id, c.day
        """,
    )

    print("\n=== 3. 조건을 빠뜨린 쉼표 조인 ===")
    show(
        conn,
        "3-A 조인 조건 있음",
        """
        SELECT t.name, SUM(s.amount)
        FROM store AS t, sale AS s
        WHERE s.store_id = t.id
        GROUP BY t.id ORDER BY t.id
        """,
    )
    show(
        conn,
        "3-B 조인 조건 빠짐",
        """
        SELECT t.name, SUM(s.amount)
        FROM store AS t, sale AS s
        GROUP BY t.id ORDER BY t.id
        """,
    )

    print("\n=== 4. SELF JOIN — 직원과 상사 ===")
    show(
        conn,
        "4-A INNER JOIN",
        """
        SELECT e.name, m.name AS manager
        FROM employee AS e
        INNER JOIN employee AS m ON m.id = e.manager_id
        ORDER BY e.id
        """,
    )
    show(
        conn,
        "4-B LEFT JOIN",
        """
        SELECT e.name, m.name AS manager
        FROM employee AS e
        LEFT JOIN employee AS m ON m.id = e.manager_id
        ORDER BY e.id
        """,
    )
    show(
        conn,
        "4-C 상사보다 급여가 많은 직원",
        """
        SELECT e.name, e.salary, m.name, m.salary
        FROM employee AS e
        INNER JOIN employee AS m ON m.id = e.manager_id
        WHERE e.salary > m.salary
        """,
    )

    print("\n=== 5. SELF JOIN — 같은 부서 짝 ===")
    show(
        conn,
        "5-A 조건 없이 같은 부서",
        """
        SELECT a.name, b.name
        FROM employee AS a
        INNER JOIN employee AS b ON b.dept = a.dept
        WHERE a.dept = '개발'
        ORDER BY a.id, b.id
        """,
    )
    show(
        conn,
        "5-B a.id <> b.id",
        """
        SELECT a.name, b.name
        FROM employee AS a
        INNER JOIN employee AS b ON b.dept = a.dept AND a.id <> b.id
        WHERE a.dept = '개발'
        ORDER BY a.id, b.id
        """,
    )
    show(
        conn,
        "5-C a.id < b.id",
        """
        SELECT a.name, b.name
        FROM employee AS a
        INNER JOIN employee AS b ON b.dept = a.dept AND a.id < b.id
        WHERE a.dept = '개발'
        ORDER BY a.id, b.id
        """,
    )

    print("\n=== 6. 실행계획 — CROSS JOIN 은 순서를 고정한다 ===")
    # store 를 먼저 적었다 — INNER JOIN 이면 옵티마이저가 순서를 바꿀 수 있고, CROSS JOIN 이면 못 바꾼다
    show_plan(
        conn,
        "6-A store INNER JOIN sale",
        """
        SELECT s.id, t.name FROM store AS t
        INNER JOIN sale AS s ON s.store_id = t.id
        """,
    )
    show_plan(
        conn,
        "6-B store CROSS JOIN sale",
        """
        SELECT s.id, t.name FROM store AS t
        CROSS JOIN sale AS s
        WHERE s.store_id = t.id
        """,
    )
    show(
        conn,
        "6-C 6-A 의 결과",
        """
        SELECT s.id, t.name FROM store AS t
        INNER JOIN sale AS s ON s.store_id = t.id
        ORDER BY s.id
        """,
    )
    show(
        conn,
        "6-D 6-B 의 결과",
        """
        SELECT s.id, t.name FROM store AS t
        CROSS JOIN sale AS s
        WHERE s.store_id = t.id
        ORDER BY s.id
        """,
    )

    conn.close()


if __name__ == "__main__":
    main()
