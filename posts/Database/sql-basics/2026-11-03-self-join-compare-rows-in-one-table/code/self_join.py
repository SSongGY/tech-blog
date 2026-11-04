"""자기 조인 — 같은 표를 두 번 불러 행끼리 비교한다.

SQLite 3.49.1 / Python 3.13.5 에서 돌렸다. 외부 의존성은 없다.
"""

import sqlite3

from dbshow import print_dataset, print_environment


def build_database() -> sqlite3.Connection:
    """직원 7명. 정사원은 일부러 팀장보다 급여가 많게, 3월 4일 매출은 일부러 뺐다."""
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE employee (
            emp_id     INTEGER PRIMARY KEY,
            name       TEXT    NOT NULL,
            dept       TEXT    NOT NULL,
            salary     INTEGER NOT NULL,
            manager_id INTEGER REFERENCES employee(emp_id)
        )
        """
    )
    conn.executemany(
        "INSERT INTO employee VALUES (?, ?, ?, ?, ?)",
        [
            (1, "김대표", "경영", 900, None),
            (2, "이부장", "개발", 600, 1),
            (3, "박팀장", "개발", 500, 2),
            (4, "최사원", "개발", 350, 3),
            (5, "정사원", "개발", 520, 3),
            (6, "한부장", "영업", 580, 1),
            (7, "오대리", "영업", 400, 6),
        ],
    )
    conn.execute(
        """
        CREATE TABLE daily_sale (
            sale_day TEXT    PRIMARY KEY,
            amount   INTEGER NOT NULL
        )
        """
    )
    conn.executemany(
        "INSERT INTO daily_sale VALUES (?, ?)",
        [
            ("2026-03-01", 100),
            ("2026-03-02", 120),
            ("2026-03-03", 90),
            ("2026-03-05", 130),
            ("2026-03-06", 130),
        ],
    )
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


def section(title: str) -> None:
    print()
    print("=" * 62)
    print(title)
    print("=" * 62)


def run_or_error(conn: sqlite3.Connection, label: str, sql: str) -> None:
    try:
        rows = conn.execute(sql).fetchall()
        print(f"  OK   {label}: {len(rows)}행")
    except sqlite3.OperationalError as exc:
        print(f"  에러 {label}: {exc}")


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)

    section("1. 별칭 없이 같은 표를 두 번 부르면 어느 쪽인지 가릴 수 없다")
    run_or_error(
        conn,
        "별칭 없음",
        "SELECT name FROM employee JOIN employee "
        "ON employee.manager_id = employee.emp_id",
    )
    run_or_error(
        conn,
        "별칭 e, m",
        "SELECT e.name FROM employee AS e JOIN employee AS m "
        "ON e.manager_id = m.emp_id",
    )

    section("2. 직원 옆에 상사 이름 붙이기 — JOIN 과 LEFT JOIN 의 차이")
    inner_sql = """
        SELECT e.name AS employee, m.name AS manager
        FROM employee AS e JOIN employee AS m ON e.manager_id = m.emp_id
        ORDER BY e.emp_id
    """
    print("-- JOIN: 상사가 있는 직원만")
    for employee, manager in conn.execute(inner_sql):
        print(f"  {employee:<6} 상사 {manager}")
    left_sql = """
        SELECT e.name AS employee, COALESCE(m.name, '(없음)') AS manager
        FROM employee AS e LEFT JOIN employee AS m ON e.manager_id = m.emp_id
        ORDER BY e.emp_id
    """
    print("-- LEFT JOIN: 상사가 없는 대표까지")
    for employee, manager in conn.execute(left_sql):
        print(f"  {employee:<6} 상사 {manager}")

    section("3. 상사보다 급여가 많은 직원 — 두 행의 값을 한 줄에서 비교한다")
    over_sql = """
        SELECT e.name, e.salary, m.name AS manager, m.salary AS manager_salary
        FROM employee AS e JOIN employee AS m ON e.manager_id = m.emp_id
        WHERE e.salary > m.salary
    """
    for name, salary, manager, manager_salary in conn.execute(over_sql):
        print(f"  {name} {salary} > {manager} {manager_salary}")

    section("4. 같은 부서 직원끼리 짝짓기 — <> 와 < 는 행 수가 두 배 차이 난다")
    for operator in ("<>", "<"):
        pair_sql = f"""
            SELECT a.dept, a.name, b.name
            FROM employee AS a JOIN employee AS b
              ON a.dept = b.dept AND a.emp_id {operator} b.emp_id
            ORDER BY a.dept, a.emp_id, b.emp_id
        """
        rows = conn.execute(pair_sql).fetchall()
        print(f"-- a.emp_id {operator} b.emp_id : {len(rows)}행")
        for dept, left, right in rows:
            if dept == "영업":
                print(f"  {dept} {left}-{right}")

    section("5. 전날과 비교하기 — 자기 조인은 '전날', LAG 는 '이전 행'을 가져온다")
    prev_day_sql = """
        SELECT cur.sale_day, cur.amount, prev.sale_day AS prev_day, prev.amount AS prev_amount
        FROM daily_sale AS cur
        LEFT JOIN daily_sale AS prev ON prev.sale_day = date(cur.sale_day, '-1 day')
        ORDER BY cur.sale_day
    """
    print("-- 자기 조인: prev.sale_day = date(cur.sale_day, '-1 day')")
    for sale_day, amount, prev_day, prev_amount in conn.execute(prev_day_sql):
        print(f"  {sale_day} {amount:>4}  전날 {str(prev_day):<10} {str(prev_amount):>4}")
    lag_sql = """
        SELECT sale_day, amount,
               LAG(sale_day) OVER (ORDER BY sale_day) AS prev_day,
               LAG(amount)   OVER (ORDER BY sale_day) AS prev_amount
        FROM daily_sale ORDER BY sale_day
    """
    print("-- LAG(): 정렬 순서에서 바로 앞 행")
    for sale_day, amount, prev_day, prev_amount in conn.execute(lag_sql):
        print(f"  {sale_day} {amount:>4}  앞행 {str(prev_day):<10} {str(prev_amount):>4}")

    section("6. 조건을 어느 별칭에 거느냐로 결과가 갈린다")
    run_or_error(
        conn,
        "WHERE dept = '개발' (별칭 없음)",
        "SELECT e.name FROM employee AS e JOIN employee AS m "
        "ON e.manager_id = m.emp_id WHERE dept = '개발'",
    )
    for alias, meaning in (("e", "개발부 직원"), ("m", "상사가 개발부")):
        count = conn.execute(
            "SELECT COUNT(*) FROM employee AS e JOIN employee AS m "
            f"ON e.manager_id = m.emp_id WHERE {alias}.dept = '개발'"
        ).fetchone()[0]
        print(f"  WHERE {alias}.dept = '개발' → {count}행 ({meaning})")

    section("7. 질의 계획 — 두 번째 employee 는 기본키로 찾아간다")
    show_plan(conn, inner_sql)
    print("-- 짝짓기 조인: 부서에 인덱스가 없을 때")
    pair_plan_sql = """
        SELECT a.name, b.name FROM employee AS a JOIN employee AS b
          ON a.dept = b.dept AND a.emp_id < b.emp_id
    """
    show_plan(conn, pair_plan_sql)
    conn.execute("CREATE INDEX ix_employee_dept ON employee(dept)")
    print("-- 부서에 인덱스를 만든 뒤")
    show_plan(conn, pair_plan_sql)

    conn.close()


if __name__ == "__main__":
    main()
