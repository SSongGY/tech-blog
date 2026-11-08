"""SQLite 에서 중앙값을 구한다 — 함수 유무 확인부터 홀짝·그룹·NULL·동점까지.

1) median() 같은 함수가 있는가
2) 평균과 중앙값 — 큰 값 하나가 평균만 끌어올린다
3) ROW_NUMBER + COUNT 로 전체 중앙값 — 가운데 행 번호가 어떻게 정해지는가
4) 부서별 중앙값 — PARTITION BY
5) 틀리기 쉬운 자리 — NULL 을 세는 COUNT(*), RANK 로 매긴 번호, 정수 나눗셈
6) 창 함수 없이 — LIMIT/OFFSET 으로 같은 값을 구해 맞춰 본다
"""
import sqlite3
import statistics

from dbshow import print_dataset, print_environment


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE employee (
            emp_id  INTEGER PRIMARY KEY,
            dept    TEXT NOT NULL,
            name    TEXT NOT NULL,
            salary  INTEGER          -- 미정이면 NULL
        );
        INSERT INTO employee(dept, name, salary) VALUES
            ('sales', 'kim',   3200),
            ('sales', 'lee',   3500),
            ('sales', 'park',  3500),
            ('sales', 'choi',  4100),
            ('sales', 'jung', 12000),
            ('dev',   'kang',  4200),
            ('dev',   'yoon',  4500),
            ('dev',   'jang',  4601),
            ('dev',   'lim',   5300),
            ('ops',   'han',   3900),
            ('ops',   'oh',    NULL),
            ('ops',   'seo',   4300);
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


def section_builtin(conn):
    print("== 1) 중앙값 함수가 있는가 ==")
    show(conn, "SELECT median(salary) FROM employee")
    show(conn, "SELECT percentile_cont(salary, 0.5) FROM employee")


def section_mean_vs_median(conn):
    print("== 2) 평균과 중앙값 — 비교용 정답은 파이썬 statistics.median ==")
    show(conn, "SELECT dept, count(salary) AS n, avg(salary) AS mean FROM employee GROUP BY dept ORDER BY dept")
    for dept in ("dev", "ops", "sales"):
        values = [r[0] for r in conn.execute(
            "SELECT salary FROM employee WHERE dept = ? AND salary IS NOT NULL", (dept,))]
        print(f"  python median {dept:5} {sorted(values)} -> {statistics.median(values)}")
    print()


OVERALL_ORDERED = """
    SELECT salary,
           ROW_NUMBER() OVER (ORDER BY salary) AS rn,
           COUNT(*) OVER () AS cnt,
           (COUNT(*) OVER () + 1) / 2 AS lo,
           (COUNT(*) OVER () + 2) / 2 AS hi
    FROM employee
    WHERE salary IS NOT NULL
"""


def section_overall(conn):
    print("== 3) 전체 중앙값 — 가운데 번호 lo, hi ==")
    show(conn, OVERALL_ORDERED)
    show(conn, f"WITH ordered AS ({OVERALL_ORDERED}) SELECT avg(salary) AS median FROM ordered WHERE rn IN (lo, hi)")
    values = [r[0] for r in conn.execute("SELECT salary FROM employee WHERE salary IS NOT NULL")]
    print(f"  python median 전체 {len(values)}개 -> {statistics.median(values)}")
    print()


GROUP_MEDIAN = """
    WITH ordered AS (
        SELECT dept, salary,
               ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary) AS rn,
               COUNT(*) OVER (PARTITION BY dept) AS cnt
        FROM employee
        WHERE salary IS NOT NULL
    )
    SELECT dept, cnt, avg(salary) AS median
    FROM ordered
    WHERE rn IN ((cnt + 1) / 2, (cnt + 2) / 2)
    GROUP BY dept
    ORDER BY dept
"""


def section_group(conn):
    print("== 4) 부서별 중앙값 ==")
    show(conn, GROUP_MEDIAN)


def section_pitfalls(conn):
    print("== 5-a) WHERE salary IS NOT NULL 을 빼면 — ops 부서 ==")
    show(conn, """
        SELECT name, salary,
               ROW_NUMBER() OVER (ORDER BY salary) AS rn,
               COUNT(*) OVER () AS cnt
        FROM employee WHERE dept = 'ops'
    """)
    show(conn, """
        WITH ordered AS (
            SELECT salary, ROW_NUMBER() OVER (ORDER BY salary) AS rn, COUNT(*) OVER () AS cnt
            FROM employee WHERE dept = 'ops')
        SELECT avg(salary) AS median FROM ordered WHERE rn IN ((cnt + 1) / 2, (cnt + 2) / 2)
    """)

    print("== 5-b) ROW_NUMBER 대신 RANK — sales 부서, 3500 이 둘 ==")
    show(conn, """
        SELECT name, salary,
               RANK() OVER (ORDER BY salary) AS rk,
               ROW_NUMBER() OVER (ORDER BY salary) AS rn
        FROM employee WHERE dept = 'sales'
    """)
    show(conn, """
        WITH ordered AS (
            SELECT salary, RANK() OVER (ORDER BY salary) AS rk, COUNT(*) OVER () AS cnt
            FROM employee WHERE dept = 'sales' AND salary <> 3200)
        SELECT count(*) AS hit_rows, avg(salary) AS median
        FROM ordered WHERE rk IN ((cnt + 1) / 2, (cnt + 2) / 2)
    """)

    print("== 5-c) 두 값을 더해 2 로 나누면 — dev 부서 4500, 4601 ==")
    show(conn, "SELECT (4500 + 4601) / 2 AS int_div, (4500 + 4601) / 2.0 AS real_div, avg(x) AS by_avg FROM (SELECT 4500 AS x UNION ALL SELECT 4601)")


LIMIT_OFFSET = """
    SELECT avg(salary) AS median FROM (
        SELECT salary FROM employee
        WHERE salary IS NOT NULL
        ORDER BY salary
        LIMIT 2 - (SELECT count(salary) FROM employee) % 2
        OFFSET (SELECT (count(salary) - 1) / 2 FROM employee)
    )
"""


def section_limit_offset(conn):
    print("== 6) 창 함수 없이 LIMIT/OFFSET ==")
    show(conn, LIMIT_OFFSET)
    conn.execute("DELETE FROM employee WHERE name = 'lim'")
    print("  -- lim 을 지워 10개(짝수)로 만든 뒤 두 방법을 다시 비교")
    show(conn, LIMIT_OFFSET)
    show(conn, f"WITH ordered AS ({OVERALL_ORDERED}) SELECT avg(salary) AS median FROM ordered WHERE rn IN (lo, hi)")
    values = [r[0] for r in conn.execute("SELECT salary FROM employee WHERE salary IS NOT NULL")]
    print(f"  python median 전체 {len(values)}개 -> {statistics.median(values)}")


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)
    section_builtin(conn)
    section_mean_vs_median(conn)
    section_overall(conn)
    section_group(conn)
    section_pitfalls(conn)
    section_limit_offset(conn)


if __name__ == "__main__":
    main()
