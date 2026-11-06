"""ON, USING, NATURAL JOIN 을 같은 데이터로 돌려 결과 컬럼과 행 수를 비교한다.

1) 세 구문이 같은 행을 주지만 결과 컬럼 수가 다른 것
2) 짝이 없는 행(dept_id 가 NULL 인 사원, 사원이 없는 부서)이 LEFT JOIN 에서 어떻게 남는지
3) 양쪽 표에 같은 이름의 컬럼이 하나 더 생기면 NATURAL JOIN 결과가 조용히 바뀌는 것
4) USING 은 같은 상황에서 결과가 그대로인 것
"""
import sqlite3

from dbshow import print_dataset, print_environment

SCHEMA = """
CREATE TABLE dept (
    dept_id   INTEGER PRIMARY KEY,
    dept_name TEXT NOT NULL
);
CREATE TABLE emp (
    emp_id   INTEGER PRIMARY KEY,
    emp_name TEXT NOT NULL,
    dept_id  INTEGER REFERENCES dept (dept_id)
);
INSERT INTO dept VALUES (10, '개발'), (20, '영업'), (30, '인사');
INSERT INTO emp VALUES
    (1, '김하늘', 10),
    (2, '이서준', 10),
    (3, '박지우', 20),
    (4, '최민재', NULL);
"""


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    return conn


def show(conn: sqlite3.Connection, title: str, sql: str) -> None:
    """질의문과 결과를 컬럼 이름까지 그대로 찍는다."""
    cursor = conn.execute(sql)
    headers = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    print(f"\n-- {title}")
    print(f"   {sql.strip()}")
    print(f"   컬럼 {len(headers)}개: {', '.join(headers)}")
    for row in rows:
        print("   ", row)
    print(f"   ({len(rows)}행)")


def part_one(conn: sqlite3.Connection) -> None:
    print("\n### 1. 같은 행, 다른 컬럼 수")
    show(conn, "ON", "SELECT * FROM emp JOIN dept ON emp.dept_id = dept.dept_id")
    show(conn, "USING", "SELECT * FROM emp JOIN dept USING (dept_id)")
    show(conn, "NATURAL JOIN", "SELECT * FROM emp NATURAL JOIN dept")


def part_two(conn: sqlite3.Connection) -> None:
    print("\n### 2. 짝이 없는 행")
    show(conn, "LEFT JOIN USING",
         "SELECT * FROM emp LEFT JOIN dept USING (dept_id)")
    show(conn, "부서 기준 LEFT JOIN USING",
         "SELECT * FROM dept LEFT JOIN emp USING (dept_id)")


def part_three(conn: sqlite3.Connection) -> None:
    print("\n### 3. 양쪽에 note 컬럼이 생긴 뒤")
    conn.execute("ALTER TABLE emp ADD COLUMN note TEXT")
    conn.execute("ALTER TABLE dept ADD COLUMN note TEXT")
    show(conn, "NATURAL JOIN (note 추가 후)", "SELECT * FROM emp NATURAL JOIN dept")
    show(conn, "USING (note 추가 후)",
         "SELECT emp_name, dept_name FROM emp JOIN dept USING (dept_id)")
    print("\n-- 이름이 겹치는 컬럼에 값을 채우면")
    conn.execute("UPDATE emp SET note = '' ")
    conn.execute("UPDATE dept SET note = '' ")
    show(conn, "NATURAL JOIN (note 가 둘 다 빈 문자열)",
         "SELECT emp_name, dept_name FROM emp NATURAL JOIN dept")
    conn.execute("UPDATE dept SET note = '본사' WHERE dept_id = 10")
    show(conn, "NATURAL JOIN (개발 부서 note 만 다름)",
         "SELECT emp_name, dept_name FROM emp NATURAL JOIN dept")


def part_four(conn: sqlite3.Connection) -> None:
    print("\n### 4. 실행계획 (EXPLAIN QUERY PLAN 의 detail 원문)")
    for title, sql in [
        ("ON", "SELECT * FROM emp JOIN dept ON emp.dept_id = dept.dept_id"),
        ("USING", "SELECT * FROM emp JOIN dept USING (dept_id)"),
    ]:
        print(f"\n-- {title}")
        for row in conn.execute("EXPLAIN QUERY PLAN " + sql):
            print("   ", row[3])


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)
    part_one(conn)
    part_two(conn)
    part_three(conn)
    part_four(conn)


if __name__ == "__main__":
    main()
