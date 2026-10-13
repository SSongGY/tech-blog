"""ORDER BY가 별칭과 표현식을 어떻게 읽는지 확인한다.

SELECT에서 만든 별칭을 ORDER BY는 쓸 수 있는데 WHERE에서는 어떻게 되는지,
정수를 쓰면 무슨 뜻인지, 별칭이 실제 컬럼 이름과 겹치면 어느 쪽이 이기는지,
DISTINCT와 UNION이 붙으면 무엇이 막히는지를 전부 직접 돌려서 본다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

SCHEMA = """
CREATE TABLE employee (
    emp_id      INTEGER PRIMARY KEY,
    emp_name    TEXT    NOT NULL,
    dept        TEXT    NOT NULL,
    base_salary INTEGER NOT NULL,
    bonus_rate  REAL    NOT NULL
);
"""

EMPLOYEES = [
    (1, "김하늘", "개발", 4200000, 0.15),
    (2, "이도윤", "개발", 3800000, 0.20),
    (3, "박서준", "영업", 3500000, 0.30),
    (4, "최지아", "영업", 4500000, 0.10),
    (5, "정민재", "운영", 3200000, 0.25),
]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO employee VALUES (?, ?, ?, ?, ?)", EMPLOYEES)
    return conn


def run(conn: sqlite3.Connection, label: str, sql: str) -> None:
    """질의 하나를 돌려 결과나 에러 메시지를 그대로 찍는다."""
    print(f"-- {label}")
    print(f"   {' '.join(sql.split())}")
    try:
        rows = conn.execute(sql).fetchall()
    except sqlite3.Error as exc:
        # 에러도 결과다. 어떤 메시지가 나오는지가 이 글의 내용이다.
        print(f"   [{type(exc).__name__}] {exc}")
    else:
        for row in rows:
            print(f"   {row}")
        if not rows:
            print("   (0행)")
    print()


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("=" * 64)
    print("1부 — ORDER BY는 별칭을 읽는다")
    print("=" * 64)
    run(conn, "1. 별칭을 ORDER BY에서 쓴다", """
        SELECT emp_name, base_salary * 12 AS annual_pay
        FROM employee
        ORDER BY annual_pay DESC
    """)
    run(conn, "2. 같은 표현식을 ORDER BY에 다시 적는다 (결과 동일)", """
        SELECT emp_name, base_salary * 12 AS annual_pay
        FROM employee
        ORDER BY base_salary * 12 DESC
    """)
    run(conn, "3. 정수 2는 두 번째 결과 컬럼을 뜻한다", """
        SELECT emp_name, base_salary * 12 AS annual_pay
        FROM employee
        ORDER BY 2 DESC
    """)
    run(conn, "4. 범위를 벗어난 정수", """
        SELECT emp_name, base_salary FROM employee ORDER BY 3
    """)
    run(conn, "5. 정수를 식으로 감싸면 자리 번호가 아니라 상수다", """
        SELECT emp_name, base_salary * 12 AS annual_pay
        FROM employee
        ORDER BY 2 + 0 DESC
    """)

    print("=" * 64)
    print("2부 — WHERE는 별칭을 읽는가")
    print("=" * 64)
    run(conn, "6. WHERE에서 별칭을 쓴다", """
        SELECT emp_name, base_salary * 12 AS annual_pay
        FROM employee
        WHERE annual_pay > 48000000
    """)
    run(conn, "7. 별칭이 가리키는 식을 WHERE에 직접 적는다", """
        SELECT emp_name, base_salary * 12 AS annual_pay
        FROM employee
        WHERE base_salary * 12 > 48000000
    """)
    run(conn, "8. 별칭을 쓰려고 만든 하위 질의 — 어느 엔진에서나 통한다", """
        SELECT emp_name, annual_pay
        FROM (SELECT emp_name, base_salary * 12 AS annual_pay FROM employee)
        WHERE annual_pay > 48000000
    """)
    run(conn, "9. GROUP BY에서 별칭을 쓴다", """
        SELECT dept AS team, COUNT(*) AS head_count
        FROM employee
        GROUP BY team
        ORDER BY head_count DESC, team
    """)
    run(conn, "10. HAVING에서 집계 별칭을 쓴다", """
        SELECT dept, COUNT(*) AS head_count
        FROM employee
        GROUP BY dept
        HAVING head_count >= 2
    """)

    print("=" * 64)
    print("3부 — 별칭이 실제 컬럼 이름과 겹치면")
    print("=" * 64)
    run(conn, "11. bonus_rate 라는 이름의 별칭을 다른 식에 붙인다", """
        SELECT emp_name, base_salary * 2 AS bonus_rate
        FROM employee
        ORDER BY bonus_rate
    """)
    run(conn, "12. 같은 별칭을 WHERE에 쓴다", """
        SELECT emp_name, base_salary * 2 AS bonus_rate
        FROM employee
        WHERE bonus_rate < 1
    """)
    run(conn, "13. 결과에 없는 컬럼으로 정렬한다", """
        SELECT emp_name FROM employee ORDER BY bonus_rate DESC
    """)
    run(conn, "14. 별칭을 식 안에 넣어 정렬한다", """
        SELECT emp_name, base_salary * 12 AS annual_pay
        FROM employee
        ORDER BY annual_pay / 1000000
    """)
    run(conn, "14b. 같은 이름을 GROUP BY가 읽으면 — 별칭인가 원래 컬럼인가", """
        SELECT dept AS bonus_rate, COUNT(*) AS n
        FROM employee
        GROUP BY bonus_rate
    """)

    print("=" * 64)
    print("4부 — DISTINCT와 UNION이 붙으면 막히는 것")
    print("=" * 64)
    run(conn, "15. DISTINCT + 결과에 없는 컬럼으로 정렬", """
        SELECT DISTINCT dept FROM employee ORDER BY base_salary
    """)
    run(conn, "15b. 그 정렬 키가 부서마다 하나로 정해지는지 확인", """
        SELECT dept, MIN(base_salary) AS lo, MAX(base_salary) AS hi
        FROM employee GROUP BY dept ORDER BY dept
    """)
    run(conn, "16. DISTINCT + 결과 컬럼의 식으로 정렬", """
        SELECT DISTINCT dept FROM employee ORDER BY length(dept), dept
    """)
    run(conn, "17. UNION ALL + 별칭으로 정렬", """
        SELECT emp_name AS who, base_salary AS amount FROM employee WHERE dept = '개발'
        UNION ALL
        SELECT emp_name, base_salary FROM employee WHERE dept = '영업'
        ORDER BY amount DESC
    """)
    run(conn, "18. UNION ALL + 식으로 정렬", """
        SELECT emp_name AS who, base_salary AS amount FROM employee WHERE dept = '개발'
        UNION ALL
        SELECT emp_name, base_salary FROM employee WHERE dept = '영업'
        ORDER BY amount * -1
    """)
    run(conn, "19. UNION ALL + 자리 번호로 정렬", """
        SELECT emp_name AS who, base_salary AS amount FROM employee WHERE dept = '개발'
        UNION ALL
        SELECT emp_name, base_salary FROM employee WHERE dept = '영업'
        ORDER BY 2 DESC
    """)

    print("=" * 64)
    print("5부 — 별칭 두 번째 쓰임: 정렬 키를 결과에서 감추기")
    print("=" * 64)
    run(conn, "20. 정렬 키를 결과에 넣지 않는다", """
        SELECT emp_name
        FROM employee
        ORDER BY base_salary * (1 + bonus_rate) DESC
    """)
    run(conn, "21. 같은 정렬을 별칭으로 적되 키도 함께 보여 준다", """
        SELECT emp_name, CAST(base_salary * (1 + bonus_rate) AS INTEGER) AS total_pay
        FROM employee
        ORDER BY total_pay DESC
    """)

    print("=" * 64)
    print("6부 — 실행계획 (EXPLAIN QUERY PLAN의 detail 원문)")
    print("=" * 64)
    conn.execute("CREATE INDEX ix_employee_salary ON employee(base_salary)")
    conn.execute("ANALYZE")
    for label, sql in [
        ("22. ORDER BY base_salary", "SELECT emp_id FROM employee ORDER BY base_salary"),
        ("23. ORDER BY 별칭(= 그냥 컬럼)",
         "SELECT base_salary AS pay FROM employee ORDER BY pay"),
        ("24. ORDER BY 별칭(= 계산식)",
         "SELECT base_salary * 12 AS pay FROM employee ORDER BY pay"),
    ]:
        print(f"-- {label}")
        print(f"   {sql}")
        for row in conn.execute("EXPLAIN QUERY PLAN " + sql):
            print(f"   {row[3]}")
        print()

    conn.close()


if __name__ == "__main__":
    main()
