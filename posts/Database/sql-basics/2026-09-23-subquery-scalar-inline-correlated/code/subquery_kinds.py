"""서브쿼리 세 가지 — 스칼라, 인라인 뷰, 상관 서브쿼리를 한 데이터로 비교한다.

메모리 SQLite에 부서 3개·직원 8명을 넣고, 같은 질문(부서 평균보다 급여가 많은 직원)을
세 방식으로 푼다. 서브쿼리 안에 호출 횟수를 세는 함수 tick()을 넣어
서브쿼리 본문이 실제로 몇 번 도는지를 숫자로 찍는다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

DEPARTMENTS = [
    (10, "개발"),
    (20, "영업"),
    (30, "인사"),
]

EMPLOYEES = [
    (1, "한지우", 10, 700),
    (2, "오민재", 10, 500),
    (3, "윤서아", 10, 600),
    (4, "장하준", 20, 400),
    (5, "임채원", 20, 800),
    (6, "서도윤", 20, 600),
    (7, "배수아", 30, 450),
    (8, "문태오", 30, 550),
]

tick_count = 0


def tick() -> int:
    # 서브쿼리 WHERE 에 끼워 넣어, 서브쿼리가 행 하나를 볼 때마다 1씩 센다
    global tick_count
    tick_count += 1
    return 1


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE department (
            id   INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );
        CREATE TABLE employee (
            id      INTEGER PRIMARY KEY,
            name    TEXT NOT NULL,
            dept_id INTEGER NOT NULL REFERENCES department(id),
            salary  INTEGER NOT NULL
        );
        """
    )
    conn.executemany("INSERT INTO department VALUES (?, ?)", DEPARTMENTS)
    conn.executemany("INSERT INTO employee VALUES (?, ?, ?, ?)", EMPLOYEES)
    conn.commit()
    # deterministic=False 로 두어 SQLite 가 호출을 한 번으로 줄이지 못하게 한다
    conn.create_function("tick", 0, tick, deterministic=False)
    return conn


def show(conn: sqlite3.Connection, label: str, sql: str) -> None:
    global tick_count
    tick_count = 0
    print(f"\n[{label}]")
    print(f"  {' '.join(sql.split())}")
    try:
        rows = conn.execute(sql).fetchall()
    except sqlite3.Error as exc:
        print(f"  오류: {type(exc).__name__}: {exc}")
        return
    for row in rows:
        print(f"  {row}")
    print(f"  -> {len(rows)}행, tick() 호출 {tick_count}회")


def show_plan(conn: sqlite3.Connection, label: str, sql: str) -> None:
    # sqlite3 CLI 가 그리는 트리 모양을 그대로 흉내 낸다 (id·parent 로 깊이를 잡는다)
    print(f"\n[{label}]")
    # 조상이 뒤에 형제를 더 가지면 "|  ", 아니면 "   " 을 앞에 쌓는다
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    prefix = {0: ""}
    print("  QUERY PLAN")
    for i, (node_id, parent, _, detail) in enumerate(rows):
        is_last = all(r[1] != parent for r in rows[i + 1 :])
        branch = "`--" if is_last else "|--"
        lead = prefix.get(parent, "")
        print(f"  {lead}{branch}{detail}")
        prefix[node_id] = lead + ("   " if is_last else "|  ")


SCALAR_SQL = """
    SELECT e.name, e.salary,
           (SELECT AVG(salary) FROM employee WHERE tick()) AS company_avg
    FROM employee AS e
    ORDER BY e.id
"""

# tick() 을 앞에 둔다 — 뒤에 두면 dept_id 가 맞는 행에서만 불려 "훑은 행 수"가 안 보인다
CORRELATED_SQL = """
    SELECT e.name, e.dept_id, e.salary
    FROM employee AS e
    WHERE e.salary > (SELECT AVG(x.salary) FROM employee AS x
                      WHERE tick() AND x.dept_id = e.dept_id)
    ORDER BY e.id
"""

CORRELATED_TICK_LAST_SQL = """
    SELECT e.name, e.dept_id, e.salary
    FROM employee AS e
    WHERE e.salary > (SELECT AVG(x.salary) FROM employee AS x
                      WHERE x.dept_id = e.dept_id AND tick())
    ORDER BY e.id
"""

INLINE_VIEW_SQL = """
    SELECT e.name, e.dept_id, e.salary, d.avg_salary
    FROM employee AS e
    INNER JOIN (SELECT dept_id, AVG(salary) AS avg_salary
                FROM employee WHERE tick()
                GROUP BY dept_id) AS d
            ON d.dept_id = e.dept_id
    WHERE e.salary > d.avg_salary
    ORDER BY e.id
"""


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("\n=== 1. 스칼라 서브쿼리 — 값 하나 ===")
    show(conn, "1-A 회사 평균을 옆 칸에", SCALAR_SQL)
    show(
        conn,
        "1-B 부서 이름을 스칼라 서브쿼리로",
        """
        SELECT e.name,
               (SELECT d.name FROM department AS d WHERE d.id = e.dept_id) AS dept
        FROM employee AS e
        WHERE e.id <= 3
        ORDER BY e.id
        """,
    )
    show(
        conn,
        "1-C 결과가 0행이면 NULL",
        """
        SELECT d.name,
               (SELECT e.name FROM employee AS e
                WHERE e.dept_id = d.id AND e.salary > 750) AS over_750
        FROM department AS d
        ORDER BY d.id
        """,
    )
    show(
        conn,
        "1-D 결과가 여러 행이면? (SQLite)",
        """
        SELECT d.name,
               (SELECT e.name FROM employee AS e WHERE e.dept_id = d.id) AS someone
        FROM department AS d
        ORDER BY d.id
        """,
    )

    show(
        conn,
        "1-E 비교 대상이 NULL 이면 행이 빠진다",
        """
        SELECT e.name FROM employee AS e
        WHERE e.salary > (SELECT x.salary FROM employee AS x WHERE x.id = 99)
        """,
    )

    print("\n=== 2. 상관 서브쿼리 — 바깥 행마다 다시 돈다 ===")
    show(conn, "2-A 부서 평균보다 많이 받는 직원", CORRELATED_SQL)
    show(conn, "2-B tick() 을 조건 뒤에 두면", CORRELATED_TICK_LAST_SQL)

    print("\n=== 3. 인라인 뷰 — 부서 평균을 한 번 만들어 조인 ===")
    show(
        conn,
        "3-A 인라인 뷰만 따로",
        """
        SELECT dept_id, AVG(salary) AS avg_salary
        FROM employee GROUP BY dept_id ORDER BY dept_id
        """,
    )
    show(conn, "3-B 같은 질문을 인라인 뷰로", INLINE_VIEW_SQL)

    print("\n=== 4. 실행계획 ===")
    show_plan(conn, "4-A 스칼라 (비상관)", SCALAR_SQL)
    show_plan(conn, "4-B 상관", CORRELATED_SQL)
    show_plan(conn, "4-C 인라인 뷰", INLINE_VIEW_SQL)

    print("\n=== 5. dept_id 인덱스를 만든 뒤 ===")
    conn.execute("CREATE INDEX ix_employee_dept_id ON employee(dept_id)")
    show_plan(conn, "5-A 상관 (인덱스 있음)", CORRELATED_SQL)
    show(conn, "5-B 상관 (인덱스 있음)", CORRELATED_SQL)

    conn.close()


if __name__ == "__main__":
    main()
