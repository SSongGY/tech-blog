"""부서별 최고 연봉자를 GROUP BY 와 ROW_NUMBER 두 방식으로 뽑아 비교한다.

같은 질문을 두 방식으로 풀면 GROUP BY 는 행을 접고, 윈도우 함수는 행을 그대로 두고
옆에 값을 붙인다는 차이가 결과 행 수와 컬럼으로 드러난다.
동점자를 일부러 넣어 두 방식이 동점을 어떻게 다루는지도 본다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

# 영업부에 최고 연봉 동점자(6100)가 둘 있다
EMPLOYEES = [
    (1, "김하늘", "개발", 7200),
    (2, "이도윤", "개발", 6800),
    (3, "박서준", "개발", 5400),
    (4, "최유나", "영업", 6100),
    (5, "정민호", "영업", 6100),
    (6, "한지우", "영업", 4800),
    (7, "윤채원", "인사", 5200),
    (8, "장태오", "인사", 4600),
    (9, "오세린", "인사", 4100),
]

TABLE_DDL = """
CREATE TABLE {name} (
    employee_id INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL,
    dept_name   TEXT    NOT NULL,
    salary      INTEGER NOT NULL
)
"""


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(TABLE_DDL.format(name="employee"))
    conn.executemany("INSERT INTO employee VALUES (?, ?, ?, ?)", EMPLOYEES)
    return conn


def show_plan(conn: sqlite3.Connection, sql: str) -> None:
    # sqlite3 CLI 가 그리는 트리 모양을 그대로 흉내 낸다 (id·parent 로 깊이를 잡는다)
    plan = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    prefix = {0: ""}
    print("   QUERY PLAN")
    for i, (node_id, parent, _, detail) in enumerate(plan):
        is_last = all(r[1] != parent for r in plan[i + 1 :])
        lead = prefix.get(parent, "")
        print(f"   {lead}{'`--' if is_last else '|--'}{detail}")
        prefix[node_id] = lead + ("   " if is_last else "|  ")


def run(conn: sqlite3.Connection, title: str, sql: str) -> None:
    print(f"\n-- {title}")
    for line in sql.strip().splitlines():
        print(f"   {line}")
    try:
        cursor = conn.execute(sql)
    except sqlite3.Error as exc:
        print(f"   에러: {exc}")
        return
    header = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    print("   => " + " | ".join(header))
    for row in rows:
        print("      " + " | ".join(str(v) for v in row))
    print(f"   ({len(rows)}행)")


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)

    run(conn, "1. GROUP BY — 부서별 최고 연봉", """
SELECT dept_name, MAX(salary) AS top_salary
FROM employee
GROUP BY dept_name
""")

    run(conn, "2. GROUP BY 에 이름을 같이 달라고 하면 (SQLite 전용 동작)", """
SELECT dept_name, name, MAX(salary) AS top_salary
FROM employee
GROUP BY dept_name
""")

    run(conn, "3. GROUP BY 결과를 원래 표에 다시 붙이기", """
SELECT e.dept_name, e.name, e.salary
FROM employee AS e
JOIN (SELECT dept_name, MAX(salary) AS top_salary
      FROM employee GROUP BY dept_name) AS m
  ON m.dept_name = e.dept_name AND m.top_salary = e.salary
ORDER BY e.dept_name
""")

    run(conn, "4. ROW_NUMBER — 행은 그대로, 옆에 순번이 붙는다", """
SELECT dept_name, name, salary,
       ROW_NUMBER() OVER (PARTITION BY dept_name ORDER BY salary DESC) AS rn
FROM employee
""")

    run(conn, "5. WHERE 에서 바로 거르면", """
SELECT dept_name, name, salary
FROM employee
WHERE ROW_NUMBER() OVER (PARTITION BY dept_name ORDER BY salary DESC) = 1
""")

    run(conn, "6. 별칭 rn 을 WHERE 에서 쓰면", """
SELECT dept_name, name, salary,
       ROW_NUMBER() OVER (PARTITION BY dept_name ORDER BY salary DESC) AS rn
FROM employee
WHERE rn = 1
""")

    top_one_sql = """
SELECT dept_name, name, salary
FROM (SELECT dept_name, name, salary,
             ROW_NUMBER() OVER (PARTITION BY dept_name
                                ORDER BY salary DESC) AS rn
      FROM employee)
WHERE rn = 1
"""
    run(conn, "7. 서브쿼리로 한 번 감싼 뒤 rn = 1", top_one_sql)

    run(conn, "8. 부서별 상위 2명 — rn <= 2", """
SELECT dept_name, name, salary, rn
FROM (SELECT dept_name, name, salary,
             ROW_NUMBER() OVER (PARTITION BY dept_name
                                ORDER BY salary DESC) AS rn
      FROM employee)
WHERE rn <= 2
""")

    # 같은 행을 거꾸로 넣은 표 — 동점자 중 누가 1번이 되는지가 바뀌는지 본다
    conn.execute(TABLE_DDL.format(name="employee_reversed"))
    conn.executemany(
        "INSERT INTO employee_reversed VALUES (?, ?, ?, ?)",
        [(100 - r[0], r[1], r[2], r[3]) for r in reversed(EMPLOYEES)],
    )
    run(conn, "9. 같은 데이터, employee_id 만 거꾸로 매긴 표에서 7번과 같은 질의", """
SELECT dept_name, name, salary
FROM (SELECT dept_name, name, salary,
             ROW_NUMBER() OVER (PARTITION BY dept_name
                                ORDER BY salary DESC) AS rn
      FROM employee_reversed)
WHERE rn = 1
""")

    run(conn, "10. 동점 순서를 정해 주기 — ORDER BY salary DESC, employee_id", """
SELECT dept_name, name, salary
FROM (SELECT dept_name, name, salary,
             ROW_NUMBER() OVER (PARTITION BY dept_name
                                ORDER BY salary DESC, employee_id) AS rn
      FROM employee_reversed)
WHERE rn = 1
""")

    print("\n-- 11. 7번 질의의 실행계획")
    show_plan(conn, top_one_sql)

    # Tibero 7.2 는 ROW_NUMBER 에 윈도우 절(ROWS ...)을 붙이면 문법 오류를 낸다 — SQLite 는 어떤가
    run(conn, "12. ROW_NUMBER 에 윈도우 절을 붙이면", """
SELECT dept_name, name,
       ROW_NUMBER() OVER (PARTITION BY dept_name ORDER BY salary DESC
                          ROWS BETWEEN 1 PRECEDING AND CURRENT ROW) AS rn
FROM employee
WHERE dept_name = '개발'
""")

    # 윈도우 함수가 WHERE 로 걸러지기 전 9행을 보는지, 걸러진 뒤 행을 보는지
    run(conn, "13. WHERE 로 거른 뒤 COUNT(*) OVER ()", """
SELECT name, COUNT(*) OVER () AS rows_in_window
FROM employee
WHERE dept_name = '개발'
""")


if __name__ == "__main__":
    main()
