"""두 명단에서 겹치는 사람과 한쪽에만 있는 사람을 INTERSECT·EXCEPT 로 구한다.

명단 두 개를 일부러 비틀어 둔다.
- 사내 교육 신청자 명단에 같은 사람이 두 번 들어가 있다 (중복 신청)
- 두 명단 모두에 이메일이 비어 있는(NULL) 사람이 있다
- 출석부의 사번은 TEXT 로 들어와 있다 (엑셀에서 옮기면서 타입이 바뀌었다)
"""

import sqlite3

from dbshow import print_dataset, print_environment

SIGNUPS = [
    (101, "김하늘", "sky@example.com"),
    (102, "이도윤", "doyun@example.com"),
    (102, "이도윤", "doyun@example.com"),
    (103, "박서준", None),
    (104, "최지아", "jia@example.com"),
]

ATTENDANCE = [
    (101, "김하늘", "sky@example.com"),
    (103, "박서준", None),
    (105, "정민재", "minjae@example.com"),
]

ATTENDANCE_TEXT_ID = [
    ("101", "김하늘"),
    ("105", "정민재"),
]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript("""
CREATE TABLE signup (
    employee_id INTEGER NOT NULL,
    name        TEXT    NOT NULL,
    email       TEXT
);
CREATE TABLE attendance (
    employee_id INTEGER NOT NULL,
    name        TEXT    NOT NULL,
    email       TEXT
);
CREATE TABLE attendance_sheet (
    employee_id TEXT NOT NULL,
    name        TEXT NOT NULL
);
""")
    conn.executemany("INSERT INTO signup VALUES (?, ?, ?)", SIGNUPS)
    conn.executemany("INSERT INTO attendance VALUES (?, ?, ?)", ATTENDANCE)
    conn.executemany(
        "INSERT INTO attendance_sheet VALUES (?, ?)", ATTENDANCE_TEXT_ID
    )
    return conn


def run(conn: sqlite3.Connection, title: str, sql: str) -> list[tuple]:
    print(f"\n-- {title}")
    for line in sql.strip().splitlines():
        print(f"   {line}")
    try:
        cursor = conn.execute(sql)
    except sqlite3.Error as exc:
        print(f"   에러: {exc}")
        return []
    header = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    print("   => " + " | ".join(header))
    for row in rows:
        print("      " + " | ".join(str(v) for v in row))
    print(f"   ({len(rows)}행)")
    return rows


def main() -> None:
    conn = build_database()
    try:
        print_environment()
        print_dataset(conn)

        run(conn, "1. 신청도 하고 출석도 한 사람 — INTERSECT", """
SELECT employee_id, name FROM signup
INTERSECT
SELECT employee_id, name FROM attendance
""")

        run(conn, "2. 신청만 하고 안 온 사람 — EXCEPT", """
SELECT employee_id, name FROM signup
EXCEPT
SELECT employee_id, name FROM attendance
""")

        # 방향을 바꾸면 결과가 완전히 달라진다. EXCEPT 는 교환법칙이 성립하지 않는다
        run(conn, "3. 신청 없이 온 사람 — 순서를 뒤집은 EXCEPT", """
SELECT employee_id, name FROM attendance
EXCEPT
SELECT employee_id, name FROM signup
""")

        # 이도윤은 신청 표에 두 번 있다. EXCEPT 결과에서 몇 번 나오는지 본다
        run(conn, "4. 중복 행 — UNION ALL 과 EXCEPT 의 행 수 비교", """
SELECT 'signup 전체' AS source, COUNT(*) AS row_count FROM signup
UNION ALL
SELECT 'EXCEPT 결과', COUNT(*) FROM (
    SELECT employee_id, name FROM signup
    EXCEPT
    SELECT employee_id, name FROM attendance)
""")

        run(conn, "5. INTERSECT ALL 은 있는가", """
SELECT employee_id, name FROM signup
INTERSECT ALL
SELECT employee_id, name FROM attendance
""")

        # 박서준은 두 표 모두 email 이 NULL 이다. = 비교라면 NULL = NULL 은 참이 아니다
        run(conn, "6. NULL 이 든 행 — INTERSECT 는 NULL 끼리 같다고 본다", """
SELECT employee_id, name, email FROM signup
INTERSECT
SELECT employee_id, name, email FROM attendance
""")

        run(conn, "7. 같은 일을 JOIN 으로 — email 까지 = 로 비교하면", """
SELECT DISTINCT s.employee_id, s.name, s.email
FROM signup AS s
JOIN attendance AS a
  ON a.employee_id = s.employee_id
 AND a.name = s.name
 AND a.email = s.email
""")

        run(conn, "8. NOT IN 으로 차집합 — 하위 질의에 NULL 이 섞이면", """
SELECT employee_id, name FROM signup
WHERE email NOT IN (SELECT email FROM attendance)
""")

        run(conn, "9. 같은 질문을 EXCEPT 로", """
SELECT email FROM signup
EXCEPT
SELECT email FROM attendance
""")

        run(conn, "10. 컬럼 수가 다르면", """
SELECT employee_id, name FROM signup
INTERSECT
SELECT employee_id FROM attendance
""")

        # 컬럼 수만 맞으면 이름·뜻이 달라도 비교한다. 자리 순서로 맞춘다
        run(conn, "11. 컬럼 순서가 바뀌면 — 에러 없이 0행", """
SELECT employee_id, name FROM signup
INTERSECT
SELECT name, employee_id FROM attendance
""")

        # attendance_sheet.employee_id 는 TEXT 다. 101 과 '101' 을 같다고 볼까
        run(conn, "12. 타입이 다른 컬럼 — INTEGER 101 과 TEXT '101'", """
SELECT employee_id, name FROM signup
INTERSECT
SELECT employee_id, name FROM attendance_sheet
""")

        run(conn, "13. 같은 비교를 JOIN = 로 하면", """
SELECT DISTINCT s.employee_id, s.name
FROM signup AS s
JOIN attendance_sheet AS t
  ON t.employee_id = s.employee_id AND t.name = s.name
""")

        run(conn, "14. CAST 로 타입을 맞춘 INTERSECT", """
SELECT employee_id, name FROM signup
INTERSECT
SELECT CAST(employee_id AS INTEGER), name FROM attendance_sheet
""")

        # 표준 SQL 은 INTERSECT 가 EXCEPT·UNION 보다 먼저 묶인다.
        # SQLite 문서는 왼쪽부터 차례로 묶는다고 적는다
        run(conn, "15. 섞어 쓰면 — signup EXCEPT attendance INTERSECT attendance_sheet", """
SELECT employee_id FROM signup
EXCEPT
SELECT employee_id FROM attendance
INTERSECT
SELECT CAST(employee_id AS INTEGER) FROM attendance_sheet
""")

        run(conn, "16. 괄호로 오른쪽을 먼저 묶으려 하면", """
SELECT employee_id FROM signup
EXCEPT
(SELECT employee_id FROM attendance
 INTERSECT
 SELECT CAST(employee_id AS INTEGER) FROM attendance_sheet)
""")

        run(conn, "17. 하위 질의로 오른쪽을 먼저 계산한다", """
SELECT employee_id FROM signup
EXCEPT
SELECT employee_id FROM (
    SELECT employee_id FROM attendance
    INTERSECT
    SELECT CAST(employee_id AS INTEGER) FROM attendance_sheet)
""")

        run(conn, "18. 개별 SELECT 에 ORDER BY 를 붙이면", """
SELECT employee_id, name FROM signup ORDER BY name
EXCEPT
SELECT employee_id, name FROM attendance
""")

        run(conn, "19. ORDER BY 는 맨 끝에 한 번 — 전체 결과를 정렬한다", """
SELECT employee_id, name FROM signup
EXCEPT
SELECT employee_id, name FROM attendance
ORDER BY name DESC
""")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
