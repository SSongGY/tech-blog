"""SQLite 의 맨 컬럼(bare column) — GROUP BY 에 없는 컬럼을 SELECT 에 쓰면 어떤 값이 나오는가.

1) 부서별 최고 연봉과 그 사람 이름 — max() 하나일 때
2) max() 대신 avg()·count() — 이름은 어느 행에서 오는가
3) 동점 — 최고 연봉이 두 명이면
4) min() 과 max() 를 함께 — 이름은 어느 쪽 행을 따르는가
5) GROUP BY 가 없을 때, 그리고 입력 행이 0개일 때
6) 규칙에 기대지 않는 쓰기 — 창 함수와 상관 부질의
"""
import sqlite3

from dbshow import print_dataset, print_environment


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE employee (
            emp_id  INTEGER PRIMARY KEY,
            dept    TEXT NOT NULL,
            name    TEXT NOT NULL,
            salary  INTEGER NOT NULL
        );
        INSERT INTO employee(dept, name, salary) VALUES
            ('sales', 'kim',  3200),
            ('sales', 'lee',  5100),
            ('sales', 'park', 4100),
            ('dev',   'kang', 4200),
            ('dev',   'yoon', 6300),
            ('dev',   'jang', 4600),
            ('ops',   'han',  3900),
            ('ops',   'seo',  4300);
        """
    )
    return conn


def show(conn, sql):
    print("  sql> " + " ".join(sql.split()))
    try:
        cursor = conn.execute(sql)
    except sqlite3.Error as exc:
        print(f"  {type(exc).__name__}: {exc}")
        print()
        return
    headers = [d[0] for d in cursor.description]
    print("  " + " | ".join(headers))
    for row in cursor.fetchall():
        print("  " + " | ".join("NULL" if v is None else repr(v) for v in row))
    print()


def section_max(conn):
    print("== 1) max() 하나 — 이름은 최고 연봉 행에서 온다 ==")
    show(conn, "SELECT dept, name, max(salary) AS top FROM employee GROUP BY dept ORDER BY dept")


def section_other_aggregates(conn):
    print("== 2) max() 가 아닌 집계 — 이름은 그룹 안의 아무 행 ==")
    show(conn, "SELECT dept, name, avg(salary) AS mean FROM employee GROUP BY dept ORDER BY dept")
    show(conn, "SELECT dept, name, count(*) AS n FROM employee GROUP BY dept ORDER BY dept")
    show(conn, "SELECT dept, name, max(salary) + 0 AS top_expr FROM employee GROUP BY dept ORDER BY dept")


def section_tie(conn):
    print("== 3) 동점 — dev 에 6300 을 한 명 더 넣는다 ==")
    conn.execute("INSERT INTO employee(dept, name, salary) VALUES ('dev', 'baek', 6300)")
    show(conn, "SELECT dept, name, max(salary) AS top FROM employee WHERE dept = 'dev' GROUP BY dept")
    show(conn, "SELECT dept, name, emp_id, max(salary) AS top FROM employee WHERE dept = 'dev' GROUP BY dept")
    conn.execute("DELETE FROM employee WHERE name = 'baek'")


def section_min_and_max(conn):
    print("== 4) min() 과 max() 를 함께 ==")
    show(conn, "SELECT dept, name, min(salary) AS low, max(salary) AS top FROM employee GROUP BY dept ORDER BY dept")
    show(conn, "SELECT dept, name, max(salary) AS top, min(salary) AS low FROM employee GROUP BY dept ORDER BY dept")


def section_no_group_by(conn):
    print("== 5) GROUP BY 없이, 그리고 입력 0행 ==")
    show(conn, "SELECT name, max(salary) AS top FROM employee")
    show(conn, "SELECT name, avg(salary) AS mean FROM employee")
    show(conn, "SELECT name, max(salary) AS top FROM employee WHERE dept = 'hr'")
    show(conn, "SELECT dept, name, max(salary) AS top FROM employee WHERE dept = 'hr' GROUP BY dept")


def section_portable(conn):
    print("== 6) 규칙에 기대지 않는 쓰기 — 동점까지 드러난다 ==")
    conn.execute("INSERT INTO employee(dept, name, salary) VALUES ('dev', 'baek', 6300)")
    show(conn, """
        SELECT dept, name, salary FROM (
            SELECT dept, name, salary,
                   RANK() OVER (PARTITION BY dept ORDER BY salary DESC) AS rk
            FROM employee)
        WHERE rk = 1 ORDER BY dept, name
    """)
    show(conn, """
        SELECT e.dept, e.name, e.salary FROM employee AS e
        WHERE e.salary = (SELECT max(salary) FROM employee WHERE dept = e.dept)
        ORDER BY e.dept, e.name
    """)


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)
    section_max(conn)
    section_other_aggregates(conn)
    section_tie(conn)
    section_min_and_max(conn)
    section_no_group_by(conn)
    section_portable(conn)
    conn.close()


if __name__ == "__main__":
    main()
