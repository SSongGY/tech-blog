"""관계 나눗셈 — '필수 과목을 전부 이수한 학생'을 두 가지 방법으로 찾는다.

1) 이중 NOT EXISTS 와 GROUP BY HAVING COUNT 가 같은 답을 내는 기본 경우
2) 필수가 아닌 과목까지 세면 틀리는 자리
3) 같은 과목을 두 번 들은 행(재수강)이 섞이면 COUNT(*) 가 틀리는 자리
4) 필수 목록이 비었을 때 두 방법이 정반대로 갈리는 자리
5) 두 질의의 실행계획
6) 안쪽 부질의가 쓰는 인덱스를 만든 뒤의 실행계획
"""
import sqlite3

from dbshow import print_dataset, print_environment

# 이중 NOT EXISTS: "이 학생이 듣지 않은 필수 과목이 하나도 없다"
NOT_EXISTS_SQL = """
SELECT s.name
FROM student AS s
WHERE NOT EXISTS (
    SELECT 1 FROM required_course AS r
    WHERE NOT EXISTS (
        SELECT 1 FROM enrollment AS e
        WHERE e.student_id = s.student_id
          AND e.course = r.course))
ORDER BY s.name
"""

# 교재식 표기: "필수 과목 - 들은 과목 = 공집합" 이면 필수 ⊆ 들은 과목
EXCEPT_SQL = """
SELECT s.name
FROM student AS s
WHERE NOT EXISTS (
    SELECT course FROM required_course
    EXCEPT
    SELECT e.course FROM enrollment AS e WHERE e.student_id = s.student_id)
ORDER BY s.name
"""

# GROUP BY: "필수 과목 가운데 이 학생이 들은 서로 다른 과목 수 = 필수 과목 수"
GROUP_BY_SQL = """
SELECT s.name
FROM student AS s
JOIN enrollment AS e ON e.student_id = s.student_id
JOIN required_course AS r ON r.course = e.course
GROUP BY s.student_id
HAVING COUNT(DISTINCT e.course) = (SELECT COUNT(*) FROM required_course)
ORDER BY s.name
"""

# 흔히 쓰는 잘못된 형태 두 가지
COUNT_ALL_COURSES_SQL = """
SELECT s.name
FROM student AS s
JOIN enrollment AS e ON e.student_id = s.student_id
GROUP BY s.student_id
HAVING COUNT(*) = (SELECT COUNT(*) FROM required_course)
ORDER BY s.name
"""

COUNT_STAR_SQL = """
SELECT s.name
FROM student AS s
JOIN enrollment AS e ON e.student_id = s.student_id
JOIN required_course AS r ON r.course = e.course
GROUP BY s.student_id
HAVING COUNT(*) = (SELECT COUNT(*) FROM required_course)
ORDER BY s.name
"""


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE student (
            student_id INTEGER PRIMARY KEY,
            name       TEXT NOT NULL
        );
        INSERT INTO student VALUES
            (1, 'kim'), (2, 'lee'), (3, 'park'), (4, 'choi');

        CREATE TABLE required_course (
            course TEXT PRIMARY KEY
        );
        INSERT INTO required_course VALUES ('db'), ('network'), ('os');

        -- 재수강을 허용하는 수강 이력이라 (학생, 과목) 이 겹칠 수 있다
        CREATE TABLE enrollment (
            enrollment_id INTEGER PRIMARY KEY,
            student_id    INTEGER NOT NULL REFERENCES student(student_id),
            course        TEXT NOT NULL,
            term          TEXT NOT NULL
        );
        INSERT INTO enrollment(student_id, course, term) VALUES
            (1, 'db',      '2025-1'),
            (1, 'network', '2025-1'),
            (1, 'os',      '2025-2'),
            (2, 'db',      '2025-1'),
            (2, 'os',      '2025-2'),
            (2, 'ai',      '2025-2'),
            (3, 'db',      '2025-1'),
            (3, 'network', '2025-2');
        """
    )
    return conn


def names(conn, sql):
    return [row[0] for row in conn.execute(sql)]


def section_basic(conn):
    print("== 1) 기본 — 두 방법이 같은 답을 낸다 ==")
    print("  NOT EXISTS :", names(conn, NOT_EXISTS_SQL))
    print("  GROUP BY   :", names(conn, GROUP_BY_SQL))
    print("  EXCEPT     :", names(conn, EXCEPT_SQL))
    print()


def section_extra_course(conn):
    print("== 2) 필수가 아닌 과목까지 세면 ==")
    print("  lee 의 수강 과목:", names(
        conn, "SELECT course FROM enrollment WHERE student_id = 2 ORDER BY course"))
    print("  required_course 와 조인하지 않고 COUNT(*) :",
          names(conn, COUNT_ALL_COURSES_SQL))
    print("  required_course 와 조인한 GROUP BY       :",
          names(conn, GROUP_BY_SQL))
    print()


def section_duplicate(conn):
    print("== 3) park 이 db 를 한 번 더 들으면 ==")
    conn.execute(
        "INSERT INTO enrollment(student_id, course, term) VALUES (3, 'db', '2026-1')")
    print("  park 의 수강 행:", conn.execute(
        "SELECT course, term FROM enrollment WHERE student_id = 3 "
        "ORDER BY enrollment_id").fetchall())
    print("  COUNT(*)              :", names(conn, COUNT_STAR_SQL))
    print("  COUNT(DISTINCT course):", names(conn, GROUP_BY_SQL))
    print("  NOT EXISTS            :", names(conn, NOT_EXISTS_SQL))
    print()


def section_empty_divisor(conn):
    print("== 4) 필수 과목이 하나도 없으면 ==")
    conn.execute("SAVEPOINT empty_divisor")
    conn.execute("DELETE FROM required_course")
    print("  required_course 행 수:",
          conn.execute("SELECT COUNT(*) FROM required_course").fetchone()[0])
    print("  NOT EXISTS :", names(conn, NOT_EXISTS_SQL))
    print("  GROUP BY   :", names(conn, GROUP_BY_SQL))
    print("  EXCEPT     :", names(conn, EXCEPT_SQL))
    conn.execute("ROLLBACK TO empty_divisor")
    conn.execute("RELEASE empty_divisor")
    print()


def print_plan(conn, title, sql):
    # sqlite3 CLI 와 같은 방식으로 (id, parent) 를 따라 트리를 그린다
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    children = {}
    for node_id, parent_id, _, detail in rows:
        children.setdefault(parent_id, []).append((node_id, detail))

    def draw(parent_id, prefix):
        items = children.get(parent_id, [])
        for i, (node_id, detail) in enumerate(items):
            last = i == len(items) - 1
            print(prefix + ("`--" if last else "|--") + detail)
            draw(node_id, prefix + ("   " if last else "|  "))

    print("  [" + title + "]")
    print("  QUERY PLAN")
    draw(0, "  ")
    print()


def section_plan(conn):
    print("== 5) 실행계획 ==")
    print_plan(conn, "이중 NOT EXISTS", NOT_EXISTS_SQL)
    print_plan(conn, "GROUP BY HAVING", GROUP_BY_SQL)


def section_plan_with_index(conn):
    print("== 6) (student_id, course) 인덱스를 만든 뒤 ==")
    conn.execute(
        "CREATE INDEX ix_enrollment_student_id_course "
        "ON enrollment(student_id, course)")
    print_plan(conn, "이중 NOT EXISTS", NOT_EXISTS_SQL)
    print("  NOT EXISTS :", names(conn, NOT_EXISTS_SQL))
    print()


def main():
    conn = build_database()
    try:
        print_environment()
        print_dataset(conn)
        section_basic(conn)
        section_extra_course(conn)
        section_duplicate(conn)
        section_empty_divisor(conn)
        section_plan(conn)
        section_plan_with_index(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
