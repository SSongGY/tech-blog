"""기본 키(PRIMARY KEY)와 UNIQUE가 무엇을 똑같이 막고 무엇을 다르게 다루는지 본다.

회원 표에 회원 코드(member_code)를 기본 키로, 이메일(email)을 UNIQUE로 걸고 같은 값·NULL을
넣어 본다. SQLite는 옛 버전과의 호환 때문에 정수가 아닌 기본 키 컬럼에 NULL을 받아 주므로,
NOT NULL·STRICT·WITHOUT ROWID를 붙인 표와 나란히 놓고 차이를 확인한다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

MEMBERS = [
    # (회원 코드, 이메일, 이름)
    ("M001", "kim@example.com", "김도윤"),
    ("M002", "lee@example.com", "이서준"),
    ("M003", None, "박하은"),
]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE member (
            member_code TEXT PRIMARY KEY,
            email       TEXT UNIQUE,
            name        TEXT NOT NULL
        );
        """
    )
    conn.executemany("INSERT INTO member VALUES (?, ?, ?)", MEMBERS)
    conn.commit()
    return conn


def run(conn: sqlite3.Connection, sql: str) -> None:
    print(f"   {' '.join(sql.split())}")
    try:
        cursor = conn.execute(sql)
    except sqlite3.Error as exc:
        print(f"   에러: {exc}")
        return
    if cursor.description is None:
        print(f"   성공 · 바뀐 행 {cursor.rowcount}")
        return
    for row in cursor.fetchall():
        print("   " + " | ".join("NULL" if v is None else str(v) for v in row))


def section_duplicate(conn: sqlite3.Connection) -> None:
    print("\n-- 1. 같은 값 — 둘 다 막는다")
    run(conn, "INSERT INTO member VALUES ('M001', 'new@example.com', '최유나')")
    run(conn, "INSERT INTO member VALUES ('M004', 'kim@example.com', '최유나')")


def section_null(conn: sqlite3.Connection) -> None:
    print("\n-- 2. NULL — UNIQUE 는 여러 개 받는다")
    run(conn, "INSERT INTO member VALUES ('M004', NULL, '최유나')")
    run(conn, "SELECT COUNT(*) FROM member WHERE email IS NULL")

    print("\n-- 3. NULL — 정수가 아닌 기본 키도 받아 준다 (SQLite 호환 동작)")
    run(conn, "INSERT INTO member VALUES (NULL, 'jung@example.com', '정민호')")
    run(conn, "INSERT INTO member VALUES (NULL, 'han@example.com', '한지우')")
    run(conn, "SELECT member_code, name FROM member WHERE member_code IS NULL")
    run(conn, "SELECT COUNT(*) FROM member WHERE member_code = NULL")


def section_null_blocked(conn: sqlite3.Connection) -> None:
    print("\n-- 4. 기본 키의 NULL 을 막는 세 가지 방법")
    conn.executescript(
        """
        CREATE TABLE member_nn (member_code TEXT NOT NULL PRIMARY KEY, name TEXT);
        CREATE TABLE member_strict (member_code TEXT PRIMARY KEY, name TEXT) STRICT;
        CREATE TABLE member_wr (member_code TEXT PRIMARY KEY, name TEXT) WITHOUT ROWID;
        """
    )
    run(conn, "INSERT INTO member_nn VALUES (NULL, '정민호')")
    run(conn, "INSERT INTO member_strict VALUES (NULL, '정민호')")
    run(conn, "INSERT INTO member_wr VALUES (NULL, '정민호')")

    print("\n-- 5. INTEGER PRIMARY KEY 에 NULL 을 넣으면 번호를 매긴다")
    conn.execute("CREATE TABLE board (post_id INTEGER PRIMARY KEY, title TEXT)")
    run(conn, "INSERT INTO board VALUES (NULL, '첫 글')")
    run(conn, "INSERT INTO board VALUES (10, '열 번째 글')")
    run(conn, "INSERT INTO board VALUES (NULL, '그다음 글')")
    run(conn, "SELECT post_id, title FROM board")


def section_count(conn: sqlite3.Connection) -> None:
    print("\n-- 6. 개수 — 기본 키는 표에 하나, UNIQUE 는 여럿")
    run(conn, "CREATE TABLE t_two_pk (a TEXT PRIMARY KEY, b TEXT PRIMARY KEY)")
    run(conn, "CREATE TABLE t_two_uq (a TEXT UNIQUE, b TEXT UNIQUE, c TEXT)")
    print("   - 컬럼 둘을 묶은 기본 키 하나는 된다")
    run(conn, """CREATE TABLE enrollment (
                   student_id TEXT, course_id TEXT, PRIMARY KEY (student_id, course_id))""")
    run(conn, "INSERT INTO enrollment VALUES ('S1', 'DB101')")
    run(conn, "INSERT INTO enrollment VALUES ('S1', 'OS201')")
    run(conn, "INSERT INTO enrollment VALUES ('S1', 'DB101')")


def section_index(conn: sqlite3.Connection) -> None:
    print("\n-- 7. 둘 다 고유 인덱스를 만든다 (origin: pk = 기본 키, u = UNIQUE)")
    run(conn, "SELECT name, \"unique\", origin FROM pragma_index_list('member') ORDER BY name")
    run(conn, "SELECT name, origin FROM pragma_index_list('t_two_uq') ORDER BY name")
    print("   - INTEGER PRIMARY KEY 는 따로 인덱스가 없다 (행 번호 자체가 키)")
    run(conn, "SELECT COUNT(*) FROM pragma_index_list('board')")


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)
    section_duplicate(conn)
    section_null(conn)
    section_null_blocked(conn)
    section_count(conn)
    section_index(conn)


if __name__ == "__main__":
    main()
