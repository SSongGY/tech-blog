"""EXPLAIN QUERY PLAN 의 줄마다 무엇을 뜻하는지 SQLite 로 하나씩 확인한다.

같은 질의를 인덱스가 없을 때와 있을 때로 나눠 계획을 찍고, 그 계획대로 실제로
얼마나 일했는지를 VDBE 명령 수로 센다. 계획의 낱말이 바뀔 때 일의 양이 같이
바뀌는지 보려는 것이다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

EMPLOYEE_ROWS = 5000
DEPARTMENTS = [
    (1, "영업"), (2, "개발"), (3, "인사"), (4, "재무"), (5, "물류"),
    (6, "법무"), (7, "구매"), (8, "품질"), (9, "디자인"), (10, "고객지원"),
]


def build_database() -> sqlite3.Connection:
    # 같은 문장 텍스트를 캐시하면 DROP INDEX 뒤에도 지운 인덱스를 쓰는 계획이 나온다
    conn = sqlite3.connect(":memory:", cached_statements=0)
    conn.executescript(
        """
        CREATE TABLE department (
            dept_id   INTEGER PRIMARY KEY,
            dept_name TEXT NOT NULL
        );
        CREATE TABLE employee (
            employee_id INTEGER PRIMARY KEY,
            name        TEXT    NOT NULL,
            dept_id     INTEGER NOT NULL,
            salary      INTEGER NOT NULL,
            hired_at    TEXT    NOT NULL
        );
        """
    )
    conn.executemany("INSERT INTO department VALUES (?, ?)", DEPARTMENTS)
    # 난수 대신 식으로 만든다. 다시 돌려도 같은 데이터가 나와야 계획과 명령 수가 같다
    rows = [
        (
            n,
            f"사원{n:04d}",
            n % 10 + 1,
            3000 + (n * 37) % 5000,
            f"20{10 + n % 16:02d}-{n % 12 + 1:02d}-{n % 28 + 1:02d}",
        )
        for n in range(1, EMPLOYEE_ROWS + 1)
    ]
    conn.executemany("INSERT INTO employee VALUES (?, ?, ?, ?, ?)", rows)
    conn.commit()
    return conn


def draw_tree(plan_rows: list[tuple]) -> list[str]:
    """(id, parent, notused, detail) 행을 sqlite3 CLI 가 그리는 트리 모양으로 바꾼다."""
    children: dict[int, list[tuple]] = {}
    for row in plan_rows:
        children.setdefault(row[1], []).append(row)

    lines = ["QUERY PLAN"]

    def walk(parent_id: int, prefix: str) -> None:
        kids = children.get(parent_id, [])
        for index, (node_id, _, _, detail) in enumerate(kids):
            last = index == len(kids) - 1
            lines.append(prefix + ("`--" if last else "|--") + detail)
            walk(node_id, prefix + ("   " if last else "|  "))

    walk(0, "")
    return lines


def count_steps(conn: sqlite3.Connection, sql: str, params=()) -> tuple[int, int]:
    """질의를 끝까지 돌리며 VDBE 명령 수를 센다. 시간은 환경마다 흔들리지만 이 값은 같다."""
    steps = 0

    def tick() -> int:
        nonlocal steps
        steps += 1
        return 0

    conn.set_progress_handler(tick, 1)
    try:
        result = conn.execute(sql, params).fetchall()
    finally:
        conn.set_progress_handler(None, 0)
    return steps, len(result)


def show(conn, label: str, sql: str, params=(), *, measure: bool = True) -> None:
    print(f"\n-- {label}")
    print("   " + " ".join(sql.split()))
    plan = conn.execute("EXPLAIN QUERY PLAN " + sql, params).fetchall()
    for line in draw_tree(plan):
        print("   " + line)
    if measure:
        steps, row_count = count_steps(conn, sql, params)
        print(f"   => 결과 {row_count}행, VDBE 명령 {steps:,}개")


def section(title: str) -> None:
    print(f"\n== {title} ==")


def main() -> None:
    conn = build_database()
    try:
        print_environment()
        print_dataset(conn)

        section("1. 계획은 표다 — 날것의 네 컬럼")
        sql = "SELECT name FROM employee WHERE dept_id = 3 ORDER BY salary"
        print("   " + sql)
        print("   (id, parent, notused, detail)")
        for row in conn.execute("EXPLAIN QUERY PLAN " + sql):
            print(f"   {row}")
        print("   같은 행을 parent 로 이어 그리면:")
        for line in draw_tree(conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()):
            print("   " + line)

        section("2. SCAN 과 SEARCH")
        show(conn, "2-A. 인덱스가 없다", "SELECT name FROM employee WHERE dept_id = 3")
        conn.execute("CREATE INDEX ix_employee_dept ON employee (dept_id)")
        show(conn, "2-B. dept_id 인덱스를 만든 뒤", "SELECT name FROM employee WHERE dept_id = 3")
        show(conn, "2-C. 기본 키로 한 행", "SELECT name FROM employee WHERE employee_id = 3")
        show(conn, "2-D. 인덱스 컬럼만 고른다", "SELECT dept_id FROM employee WHERE dept_id = 3")
        show(conn, "2-E. 조건 없이 인덱스 순서로 다 읽는다",
             "SELECT dept_id, COUNT(*) FROM employee GROUP BY dept_id")
        show(conn, "2-F. 범위 조건", "SELECT name FROM employee WHERE dept_id BETWEEN 3 AND 4")

        section("3. 인덱스가 있어도 SCAN 이 나오는 조건")
        show(conn, "3-A. 컬럼에 연산을 씌운다", "SELECT name FROM employee WHERE dept_id + 0 = 3")
        show(conn, "3-B. 인덱스 없는 컬럼과 OR", "SELECT name FROM employee WHERE dept_id = 3 OR salary = 4000")
        conn.execute("CREATE INDEX ix_employee_salary ON employee (salary)")
        show(conn, "3-C. 양쪽에 인덱스가 생기면", "SELECT name FROM employee WHERE dept_id = 3 OR salary = 4000")

        section("4. USE TEMP B-TREE — 정렬을 따로 한다")
        conn.execute("DROP INDEX ix_employee_salary")
        show(conn, "4-A. 인덱스 없는 컬럼으로 정렬", "SELECT name, salary FROM employee ORDER BY salary")
        show(conn, "4-B. 조건은 인덱스, 정렬은 다른 컬럼",
             "SELECT name, salary FROM employee WHERE dept_id = 3 ORDER BY salary")
        conn.execute("CREATE INDEX ix_employee_dept_salary ON employee (dept_id, salary)")
        show(conn, "4-C. (dept_id, salary) 복합 인덱스를 만든 뒤",
             "SELECT name, salary FROM employee WHERE dept_id = 3 ORDER BY salary")
        show(conn, "4-D. 정렬 앞 컬럼만 인덱스 순서와 맞는다",
             "SELECT name, salary FROM employee ORDER BY dept_id, hired_at")
        show(conn, "4-E. DISTINCT", "SELECT DISTINCT hired_at FROM employee")
        show(conn, "4-F. GROUP BY", "SELECT hired_at, COUNT(*) FROM employee GROUP BY hired_at")
        show(conn, "4-G. LIMIT 이 붙은 정렬",
             "SELECT name, hired_at FROM employee ORDER BY hired_at LIMIT 5")

        section("5. 조인 — 위에 있는 줄이 바깥 반복")
        show(conn, "5-A. 조인 컬럼에 인덱스가 있다",
             "SELECT d.dept_name, e.name FROM department d JOIN employee e ON e.dept_id = d.dept_id "
             "WHERE d.dept_name = '인사'")
        conn.execute("CREATE TABLE evaluation (employee_id INTEGER, grade TEXT)")
        conn.executemany(
            "INSERT INTO evaluation VALUES (?, ?)",
            [(n, "ABCD"[n % 4]) for n in range(1, EMPLOYEE_ROWS + 1, 7)],
        )
        show(conn, "5-B. FROM 에 적은 순서와 계획의 순서",
             "SELECT e.name, v.grade FROM employee e JOIN evaluation v ON v.employee_id = e.employee_id "
             "WHERE e.dept_id = 3")
        conn.execute("CREATE TABLE bonus (employee_id INTEGER, amount INTEGER)")
        conn.executemany(
            "INSERT INTO bonus VALUES (?, ?)",
            [(n, n * 10) for n in range(1, EMPLOYEE_ROWS + 1, 3)],
        )
        show(conn, "5-C. 양쪽 다 조인 컬럼에 인덱스가 없다",
             "SELECT v.grade, b.amount FROM evaluation v JOIN bonus b ON b.employee_id = v.employee_id")

        section("6. 서브쿼리")
        show(conn, "6-A. 바깥 행마다 다시 도는 서브쿼리",
             "SELECT name, (SELECT dept_name FROM department d WHERE d.dept_id = e.dept_id) "
             "FROM employee e WHERE e.dept_id = 3")
        show(conn, "6-B. 한 번만 도는 서브쿼리",
             "SELECT name FROM employee WHERE salary > (SELECT AVG(salary) FROM employee)")
        show(conn, "6-C. FROM 절의 서브쿼리",
             "SELECT dept_id, top_salary FROM (SELECT dept_id, MAX(salary) AS top_salary "
             "FROM employee GROUP BY dept_id) WHERE top_salary > 7000")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
