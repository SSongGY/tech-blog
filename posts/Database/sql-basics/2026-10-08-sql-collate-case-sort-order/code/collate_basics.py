"""같은 데이터가 정렬 규칙(collation)에 따라 다른 순서·다른 결과로 나오는 것을 본다.

SQLite 의 내장 규칙 BINARY·NOCASE·RTRIM 을 비교하고, 컬럼에 붙인 규칙과
식에 붙인 COLLATE 중 무엇이 이기는지, 인덱스가 규칙이 다르면 쓰이지 않는지,
UNIQUE 가 규칙을 따르는지, 파이썬에서 만든 규칙이 연결 밖에서는 없는 것이
되는지를 차례로 확인한다.
"""

import os
import re
import sqlite3
import tempfile

from dbshow import print_dataset, print_environment

# 대문자로 시작하는 이름, 소문자로 시작하는 이름, 대소문자만 다른 이름,
# 뒤에 공백이 붙은 이름, 밑줄로 시작하는 이름, 한글, 숫자가 섞인 이름을 넣었다
MEMBERS = [
    (1, "apple", "apple"),
    (2, "Banana", "Banana"),
    (3, "APPLE", "APPLE"),
    (4, "cherry", "cherry"),
    (5, "_admin", "_admin"),
    (6, "kim ", "kim "),
    (7, "kim", "kim"),
    (8, "나래", "나래"),
    (9, "가람", "가람"),
    (10, "file10", "file10"),
    (11, "file2", "file2"),
    (12, "Éclair", "Éclair"),
]


def build_database() -> sqlite3.Connection:
    # 문장 캐시가 지운 인덱스를 계획에 남기는 일이 있어 캐시를 끈다
    conn = sqlite3.connect(":memory:", cached_statements=0)
    conn.execute("""
CREATE TABLE member (
    member_id  INTEGER PRIMARY KEY,
    name       TEXT,
    name_nc    TEXT COLLATE NOCASE
)""")
    conn.executemany("INSERT INTO member VALUES (?, ?, ?)", MEMBERS)
    return conn


def show(value: object) -> str:
    # 뒤 공백이 눈에 보이도록 문자열은 따옴표로 감싼다
    return repr(value) if isinstance(value, str) or value is None else str(value)


def run(conn: sqlite3.Connection, title: str, sql: str) -> None:
    print(f"\n-- {title}")
    print(f"   {sql.strip()}")
    try:
        rows = conn.execute(sql).fetchall()
    except sqlite3.Error as exc:
        print(f"   에러: {exc}")
        return
    for row in rows:
        print("      " + " | ".join(show(v) for v in row))
    print(f"   ({len(rows)}행)")


def run_list(conn: sqlite3.Connection, title: str, sql: str) -> None:
    # 정렬 결과는 한 줄로 늘어놓아야 순서를 비교하기 쉽다
    print(f"\n-- {title}")
    print(f"   {sql.strip()}")
    rows = conn.execute(sql).fetchall()
    print("      " + ", ".join(show(r[0]) for r in rows))


def show_plan(conn: sqlite3.Connection, title: str, sql: str) -> None:
    # sqlite3 CLI 가 그리는 트리 모양을 그대로 흉내 낸다 (id·parent 로 깊이를 잡는다)
    print(f"\n-- {title}")
    print(f"   {sql.strip()}")
    plan = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    prefix = {0: ""}
    print("   QUERY PLAN")
    for i, (node_id, parent, _, detail) in enumerate(plan):
        is_last = all(r[1] != parent for r in plan[i + 1 :])
        lead = prefix.get(parent, "")
        print(f"   {lead}{'`--' if is_last else '|--'}{detail}")
        prefix[node_id] = lead + ("   " if is_last else "|  ")


def natural_key(text: str) -> list:
    # 숫자 덩어리는 정수로, 나머지는 소문자로 바꿔 file2 가 file10 앞에 오게 한다
    return [int(part) if part.isdigit() else part.lower()
            for part in re.split(r"(\d+)", text)]


def natural_collation(left: str, right: str) -> int:
    a, b = natural_key(left), natural_key(right)
    return (a > b) - (a < b)


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)
    # dbshow 는 컬럼의 정렬 규칙을 찍지 않으므로 표 정의 원문을 따로 보인다
    print("\n[표 정의 원문]")
    print(conn.execute(
        "SELECT sql FROM sqlite_master WHERE name = 'member'").fetchone()[0])

    print("\n==== 1부. 같은 데이터, 세 가지 정렬 ====")
    run_list(conn, "1. BINARY (기본값) — 바이트 값 순서",
             "SELECT name FROM member ORDER BY name")
    run_list(conn, "2. COLLATE NOCASE — ASCII 대소문자 무시",
             "SELECT name FROM member ORDER BY name COLLATE NOCASE, member_id")
    run_list(conn, "3. 컬럼에 NOCASE 를 붙인 name_nc — COLLATE 없이 정렬",
             "SELECT name_nc FROM member ORDER BY name_nc, member_id")
    run(conn, "4. 첫 글자의 코드 값 — 왜 그 순서인가",
        "SELECT DISTINCT substr(name, 1, 1), unicode(substr(name, 1, 1)) "
        "FROM member WHERE member_id IN (1, 2, 5, 9, 8, 12) ORDER BY 2")

    print("\n==== 2부. 비교(=)도 규칙을 따른다 ====")
    run(conn, "5. name = 'apple' (BINARY)",
        "SELECT member_id, name FROM member WHERE name = 'apple'")
    run(conn, "6. name_nc = 'apple' (컬럼 규칙 NOCASE)",
        "SELECT member_id, name_nc FROM member WHERE name_nc = 'apple'")
    run(conn, "7. name = 'apple' COLLATE NOCASE (식에 붙인 규칙)",
        "SELECT member_id, name FROM member WHERE name = 'apple' COLLATE NOCASE")
    run(conn, "8. name_nc = 'apple' COLLATE BINARY (식이 컬럼을 이긴다)",
        "SELECT member_id, name_nc FROM member WHERE name_nc = 'apple' COLLATE BINARY")
    run(conn, "9. 'kim' 을 RTRIM 으로 — 뒤 공백 무시",
        "SELECT member_id, name FROM member WHERE name = 'kim' COLLATE RTRIM")
    run(conn, "10. NOCASE 는 ASCII 만 — 'éclair' 로 Éclair 를 찾으면",
        "SELECT member_id, name FROM member WHERE name = 'éclair' COLLATE NOCASE")
    run(conn, "11. lower() 도 ASCII 만 바꾼다",
        "SELECT lower('APPLE'), lower('Éclair'), upper('éclair')")

    print("\n==== 3부. 규칙이 정해지는 순서 ====")
    run(conn, "12. 컬럼끼리 비교: name = name_nc (왼쪽 컬럼 BINARY)",
        "SELECT a.member_id, b.member_id FROM member a JOIN member b "
        "ON a.name = b.name_nc WHERE a.member_id IN (1, 3)")
    run(conn, "13. 순서만 바꿔서: name_nc = name (왼쪽 컬럼 NOCASE)",
        "SELECT a.member_id, b.member_id FROM member a JOIN member b "
        "ON b.name_nc = a.name WHERE a.member_id IN (1, 3)")
    run(conn, "14. IN 목록은 왼쪽 값의 규칙을 쓴다",
        "SELECT member_id, name_nc FROM member WHERE name_nc IN ('APPLE', 'banana')")
    run(conn, "15. GROUP BY 도 규칙을 따른다",
        "SELECT name_nc, COUNT(*) FROM member GROUP BY name_nc HAVING COUNT(*) > 1")
    run(conn, "16. DISTINCT 도 — name 과 name_nc 의 개수",
        "SELECT (SELECT COUNT(DISTINCT name) FROM member), "
        "(SELECT COUNT(DISTINCT name_nc) FROM member)")

    print("\n==== 4부. 인덱스와 UNIQUE ====")
    conn.execute("CREATE INDEX ix_member_name ON member (name)")
    show_plan(conn, "17. BINARY 인덱스, BINARY 비교",
              "SELECT member_id FROM member WHERE name = 'apple'")
    show_plan(conn, "18. BINARY 인덱스, NOCASE 비교",
              "SELECT member_id FROM member WHERE name = 'apple' COLLATE NOCASE")
    conn.execute("CREATE INDEX ix_member_name_nc ON member (name COLLATE NOCASE)")
    show_plan(conn, "19. NOCASE 인덱스를 하나 더 만든 뒤 같은 질의",
              "SELECT member_id FROM member WHERE name = 'apple' COLLATE NOCASE")
    show_plan(conn, "20. ORDER BY name COLLATE NOCASE",
              "SELECT name FROM member ORDER BY name COLLATE NOCASE")

    conn.execute("CREATE TABLE login_id (user_id TEXT COLLATE NOCASE UNIQUE)")
    conn.execute("INSERT INTO login_id VALUES ('Admin')")
    run(conn, "21. NOCASE + UNIQUE 컬럼에 'ADMIN' 을 넣으면",
        "INSERT INTO login_id VALUES ('ADMIN') RETURNING user_id")
    conn.execute("CREATE TABLE login_id_bin (user_id TEXT UNIQUE)")
    conn.execute("INSERT INTO login_id_bin VALUES ('Admin')")
    run(conn, "22. BINARY + UNIQUE 컬럼에 'ADMIN' 을 넣으면",
        "INSERT INTO login_id_bin VALUES ('ADMIN') RETURNING user_id")

    print("\n==== 5부. 직접 만든 정렬 규칙 ====")
    run_list(conn, "23. file2 와 file10 — BINARY",
             "SELECT name FROM member WHERE name LIKE 'file%' ORDER BY name")
    conn.create_collation("natural", natural_collation)
    run(conn, "24. 규칙 이름을 natural 로 지으면",
        "SELECT name FROM member WHERE name LIKE 'file%' ORDER BY name COLLATE natural")
    run(conn, "24-1. 큰따옴표로 감싸면",
        "SELECT name FROM member WHERE name LIKE 'file%' ORDER BY name COLLATE \"natural\"")
    conn.create_collation("natsort", natural_collation)
    run_list(conn, "24-2. 키워드가 아닌 이름 natsort 로 등록",
             "SELECT name FROM member WHERE name LIKE 'file%' ORDER BY name COLLATE natsort")

    # 등록한 규칙은 연결에만 있다. 파일에 규칙을 박은 표를 만들고 새 연결로 열어 본다
    with tempfile.TemporaryDirectory() as work_dir:
        path = os.path.join(work_dir, "natsort.db")
        writer = sqlite3.connect(path)
        try:
            writer.create_collation("natsort", natural_collation)
            writer.execute("CREATE TABLE doc (title TEXT COLLATE natsort)")
            writer.executemany("INSERT INTO doc VALUES (?)",
                               [("v10",), ("v2",), ("v1",)])
            writer.commit()
            run_list(writer, "25. 규칙을 등록한 연결에서 ORDER BY title",
                     "SELECT title FROM doc ORDER BY title")
        finally:
            writer.close()

        reader = sqlite3.connect(path)
        try:
            run(reader, "26. 규칙을 등록하지 않은 새 연결에서 같은 질의",
                "SELECT title FROM doc ORDER BY title")
            run(reader, "27. 같은 연결에서 정렬 없이 읽기",
                "SELECT title FROM doc")
        finally:
            reader.close()

    conn.close()


if __name__ == "__main__":
    main()
