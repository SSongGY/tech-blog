"""여러 행을 한 줄로 합치는 group_concat() 을 SQLite 로 돌려 본다.

보는 것: 기본 구분자, 구분자 지정, 안쪽 ORDER BY (3.44.0+), string_agg 별칭, NULL 처리,
DISTINCT 와 구분자를 같이 못 쓰는 제약, ORDER BY 가 없을 때 순서가 바뀌는 경우,
길이 제한에 걸릴 때의 에러, 구분자가 값 안에 들어 있을 때 되돌릴 수 없는 문제.
"""

import sqlite3

from dbshow import print_dataset, print_environment

EMPLOYEES = [
    (1, "김하나", "백엔드"),
    (2, "이두리", "백엔드"),
    (3, "박세나", "데이터"),
    (4, "최네오", "프런트"),
    (5, "정다섯", "데이터"),
]

# (employee_id, skill, level). 1번은 SQL 이 두 번 들어가 있고(중복 입력),
# 4번은 기술 이름이 비어 있는 행이 하나 있고, 5번은 행이 아예 없다.
SKILLS = [
    (1, "SQL", 3),
    (1, "Python", 2),
    (1, "Go", 1),
    (1, "SQL", 2),
    (2, "Java", 3),
    (2, "SQL", 2),
    (3, "Python", 3),
    (3, "Spark", 2),
    (3, "SQL", 3),
    (4, "React", 2),
    (4, None, 1),
]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript("""
CREATE TABLE employee (
    employee_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    team        TEXT NOT NULL
);
CREATE TABLE employee_skill (
    employee_id INTEGER NOT NULL REFERENCES employee (employee_id),
    skill       TEXT,
    level       INTEGER NOT NULL
);
""")
    conn.executemany("INSERT INTO employee VALUES (?, ?, ?)", EMPLOYEES)
    conn.executemany("INSERT INTO employee_skill VALUES (?, ?, ?)", SKILLS)
    return conn


def run(conn: sqlite3.Connection, title: str, sql: str) -> None:
    print(f"\n-- {title}")
    for line in sql.strip().splitlines():
        print(f"   {line}")
    try:
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
    except sqlite3.Error as exc:
        print(f"   에러: {exc}")
        return
    header = [d[0] for d in cursor.description]
    print("   => " + " | ".join(header))
    for row in rows:
        print("      " + " | ".join("NULL" if v is None else str(v) for v in row))
    print(f"   ({len(rows)}행)")


def plan(conn: sqlite3.Connection, title: str, sql: str) -> None:
    """sqlite3 CLI 가 그리는 모양으로 EXPLAIN QUERY PLAN 을 찍는다."""
    print(f"\n-- {title}")
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    children: dict[int, list[tuple[int, str]]] = {}
    for node_id, parent, _, detail in rows:
        children.setdefault(parent, []).append((node_id, detail))

    def draw(parent: int, prefix: str) -> None:
        kids = children.get(parent, [])
        for i, (node_id, detail) in enumerate(kids):
            last = i == len(kids) - 1
            print(f"   {prefix}{'`--' if last else '|--'}{detail}")
            draw(node_id, prefix + ("   " if last else "|  "))

    print("   QUERY PLAN")
    draw(0, "")


def per_employee_loop(conn: sqlite3.Connection) -> None:
    """group_concat 을 모르면 이렇게 짠다 — 직원 수만큼 질의가 다시 나간다."""
    print("\n-- 1. 직원마다 질의를 한 번씩 — 흔히 먼저 짜는 방법")
    statements = 0
    employees = conn.execute("SELECT employee_id, name FROM employee ORDER BY employee_id").fetchall()
    statements += 1
    for employee_id, name in employees:
        skills = conn.execute(
            "SELECT skill FROM employee_skill WHERE employee_id = ? AND skill IS NOT NULL ORDER BY skill",
            (employee_id,),
        ).fetchall()
        statements += 1
        print(f"   {name}: {', '.join(s for (s,) in skills)}")
    print(f"   (질의 {statements}번 — 직원 {len(employees)}명 + 목록 1번)")


def main() -> None:
    conn = build_database()
    try:
        print_environment()
        print_dataset(conn)

        per_employee_loop(conn)

        run(conn, "2. group_concat 기본 — 구분자를 안 주면 쉼표", """
SELECT e.name, group_concat(s.skill) AS skills
FROM employee AS e
JOIN employee_skill AS s ON s.employee_id = e.employee_id
GROUP BY e.employee_id
ORDER BY e.employee_id
""")

        run(conn, "3. 두 번째 인자가 구분자", """
SELECT e.name, group_concat(s.skill, ' / ') AS skills
FROM employee AS e
JOIN employee_skill AS s ON s.employee_id = e.employee_id
GROUP BY e.employee_id
ORDER BY e.employee_id
""")

        run(conn, "4. 바깥 ORDER BY 는 행의 순서만 정한다 — 문자열 안은 그대로", """
SELECT e.name, group_concat(s.skill, ', ') AS skills
FROM employee AS e
JOIN employee_skill AS s ON s.employee_id = e.employee_id
GROUP BY e.employee_id
ORDER BY s.skill
""")

        run(conn, "5. 함수 안의 ORDER BY 가 문자열 안의 순서를 정한다 (SQLite 3.44.0+)", """
SELECT e.name,
       group_concat(s.skill, ', ' ORDER BY s.skill)                    AS by_name,
       group_concat(s.skill, ', ' ORDER BY s.level DESC, s.skill)      AS by_level
FROM employee AS e
JOIN employee_skill AS s ON s.employee_id = e.employee_id
GROUP BY e.employee_id
ORDER BY e.employee_id
""")

        run(conn, "6. string_agg 는 같은 함수의 다른 이름", """
SELECT e.name, string_agg(s.skill, '; ' ORDER BY s.skill) AS skills
FROM employee AS e
JOIN employee_skill AS s ON s.employee_id = e.employee_id
GROUP BY e.employee_id
ORDER BY e.employee_id
""")

        run(conn, "7. NULL 은 건너뛴다. 전부 NULL 이거나 행이 없으면 결과가 NULL", """
SELECT e.name,
       COUNT(s.employee_id)                                      AS skill_rows,
       group_concat(s.skill, ', ' ORDER BY s.skill)              AS skills,
       COALESCE(group_concat(s.skill, ', ' ORDER BY s.skill), '(없음)') AS shown
FROM employee AS e
LEFT JOIN employee_skill AS s ON s.employee_id = e.employee_id
GROUP BY e.employee_id
ORDER BY e.employee_id
""")

        run(conn, "8-A. DISTINCT 로 중복을 걷어 낸다", """
SELECT e.name, group_concat(DISTINCT s.skill) AS skills
FROM employee AS e
JOIN employee_skill AS s ON s.employee_id = e.employee_id
WHERE e.employee_id = 1
GROUP BY e.employee_id
""")

        run(conn, "8-B. DISTINCT 와 구분자를 같이 쓰면", """
SELECT e.name, group_concat(DISTINCT s.skill, ' / ') AS skills
FROM employee AS e
JOIN employee_skill AS s ON s.employee_id = e.employee_id
WHERE e.employee_id = 1
GROUP BY e.employee_id
""")

        run(conn, "8-C. 중복을 서브쿼리에서 먼저 지우면 구분자도 정렬도 된다", """
SELECT name, group_concat(skill, ' / ' ORDER BY skill) AS skills
FROM (SELECT DISTINCT e.name, s.skill
      FROM employee AS e
      JOIN employee_skill AS s ON s.employee_id = e.employee_id
      WHERE e.employee_id = 1)
GROUP BY name
""")

        # ORDER BY 가 없을 때의 순서는 "임의" 다. 같은 질의를 인덱스 전후로 돌려 비교한다.
        no_order_sql = """
SELECT employee_id, group_concat(skill) AS skills
FROM employee_skill
WHERE employee_id = 3
GROUP BY employee_id
"""
        run(conn, "9-A. ORDER BY 없이 — 인덱스가 없을 때", no_order_sql)
        conn.execute("CREATE INDEX idx_skill_employee_skill_desc ON employee_skill (employee_id, skill DESC)")
        run(conn, "9-B. 같은 질의 — (employee_id, skill DESC) 인덱스를 만든 뒤", no_order_sql)
        plan(conn, "9-C. 계획 — 인덱스를 타면 읽는 순서가 인덱스 순서다", no_order_sql)
        conn.execute("DROP INDEX idx_skill_employee_skill_desc")

        run(conn, "10. 숫자를 합치면 결과는 TEXT", """
SELECT employee_id,
       group_concat(level ORDER BY level DESC) AS levels,
       typeof(group_concat(level))             AS result_type
FROM employee_skill
WHERE employee_id = 1
GROUP BY employee_id
""")

        # 길이 상한을 60바이트로 낮춰 두고 긴 문자열을 만들어 본다. 기본값은 10억 바이트다.
        print("\n-- 11. 길이 제한 — SQLITE_LIMIT_LENGTH 를 60바이트로 낮춘 상태")
        default_limit = conn.getlimit(sqlite3.SQLITE_LIMIT_LENGTH)
        print(f"   기본 상한: {default_limit:,} 바이트")
        conn.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 60)
        run(conn, "11-A. 상한 안에 드는 길이", """
SELECT length(group_concat(skill, ', ')) AS total_length
FROM employee_skill
""")
        run(conn, "11-B. 행마다 50글자를 붙여 상한을 넘기면", """
SELECT length(group_concat(skill || ' 설명 ' || printf('%50s', ''), ', ')) AS total_length
FROM employee_skill
""")
        conn.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, default_limit)

        # 값 안에 구분자가 들어 있으면 합친 뒤 다시 나눌 수 없다
        conn.execute("INSERT INTO employee_skill VALUES (2, 'C, C++', 1)")
        run(conn, "12-A. 값 안에 구분자가 있으면 — 쉼표로 되나누면 세 개가 된다", """
SELECT group_concat(skill, ', ' ORDER BY skill) AS skills
FROM employee_skill
WHERE employee_id = 2
""")
        run(conn, "12-B. 나눠 쓸 것이면 json_group_array — json_each 로 되돌아간다", """
SELECT json_group_array(skill ORDER BY skill) AS skills_json,
       (SELECT COUNT(*) FROM json_each(json_group_array(skill))) AS element_count
FROM employee_skill
WHERE employee_id = 2
""")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
