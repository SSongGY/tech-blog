"""NOT NULL과 DEFAULT가 언제 작동하고 언제 작동하지 않는지 실제 INSERT·UPDATE로 확인한다.

회원 가입 표에 닉네임·상태·전화번호 컬럼을 두고, 값을 빼먹었을 때·NULL을 직접 넣었을 때·
빈 문자열을 넣었을 때 각각 무엇이 저장되는지 본다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

SCHEMA = """
CREATE TABLE member (
    id        INTEGER PRIMARY KEY,
    email     TEXT NOT NULL,
    nickname  TEXT NOT NULL DEFAULT '손님',
    status    TEXT NOT NULL DEFAULT 'active',
    phone     TEXT
);
"""

SEED = [
    (1, "a@example.com", "도윤", "active", "010-1111-2222"),
    (2, "b@example.com", "서준", "active", ""),
    (3, "c@example.com", "하은", "dormant", None),
]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO member VALUES (?, ?, ?, ?, ?)", SEED)
    conn.commit()
    return conn


def run(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> None:
    """에러도 결과로 찍는다. 어떤 INSERT가 막히는지가 이 글의 내용이다."""
    shown = " ".join(sql.split())
    if params:
        shown += f"   값={params!r}"
    try:
        conn.execute(sql, params)
        print(f"  성공  {shown}")
    except sqlite3.Error as exc:
        print(f"  에러  {shown}\n        -> {type(exc).__name__}: {exc}")


def query(conn: sqlite3.Connection, label: str, sql: str) -> None:
    print(f"\n[{label}]")
    print(f"  {' '.join(sql.split())}")
    cur = conn.execute(sql)
    print(f"  {tuple(col[0] for col in cur.description)}")
    for row in cur.fetchall():
        print(f"  {row}")


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("\n== 1. DEFAULT 는 컬럼을 빼먹었을 때만 들어간다 ==")
    run(conn, "INSERT INTO member (id, email) VALUES (4, 'd@example.com')")
    run(conn, "INSERT INTO member (id, email, nickname) VALUES (5, 'e@example.com', NULL)")
    run(conn, "INSERT INTO member (id, email, nickname) VALUES (?, ?, ?)", (6, "f@example.com", None))
    run(conn, "INSERT INTO member (id, email, nickname) VALUES (7, 'g@example.com', DEFAULT)")
    query(conn, "1-A 들어간 행", "SELECT id, nickname, status FROM member WHERE id >= 4")

    print("\n== 2. 빈 문자열은 NOT NULL 을 통과한다 ==")
    run(conn, "INSERT INTO member (id, email, nickname) VALUES (8, '', '')")
    query(
        conn,
        "2-A 빈 문자열과 NULL 은 다른 값이다",
        """SELECT id, quote(phone) AS phone, phone IS NULL AS is_null,
                  phone = '' AS is_empty, length(phone) AS len
           FROM member WHERE id <= 3""",
    )
    query(
        conn,
        "2-B 세는 방법에 따라 '전화번호 없는 회원' 수가 갈린다",
        """SELECT COUNT(*) AS total,
                  COUNT(phone) AS count_col,
                  SUM(phone IS NULL) AS null_cnt,
                  SUM(phone = '') AS empty_cnt,
                  SUM(COALESCE(phone, '') = '') AS null_or_empty
           FROM member WHERE id <= 3""",
    )

    print("\n== 3. CHECK 로 빈 문자열까지 막는다 ==")
    conn.execute(
        """CREATE TABLE member_strict (
               id     INTEGER PRIMARY KEY,
               email  TEXT NOT NULL CHECK (trim(email) <> '')
           )"""
    )
    run(conn, "INSERT INTO member_strict VALUES (1, 'a@example.com')")
    run(conn, "INSERT INTO member_strict VALUES (2, '')")
    # 공백만 든 값은 SQL 문자열에 쓰면 출력에서 한 칸으로 보이므로 바인딩으로 넘긴다
    run(conn, "INSERT INTO member_strict VALUES (?, ?)", (3, "   "))
    run(conn, "INSERT INTO member_strict VALUES (4, NULL)")

    print("\n== 4. 그냥 UPDATE 는 막히고, OR REPLACE 는 기본값으로 바꾼다 ==")
    run(conn, "UPDATE member SET nickname = NULL WHERE id = 1")
    run(conn, "UPDATE OR REPLACE member SET nickname = NULL WHERE id = 1")
    run(conn, "INSERT OR REPLACE INTO member (id, email, nickname) VALUES (9, 'i@example.com', NULL)")
    query(conn, "4-A OR REPLACE 뒤의 값", "SELECT id, nickname FROM member WHERE id IN (1, 9)")

    print("\n== 5. 이미 행이 있는 표에 NOT NULL 컬럼을 더할 때 ==")
    run(conn, "ALTER TABLE member ADD COLUMN grade TEXT NOT NULL")
    run(conn, "ALTER TABLE member ADD COLUMN grade TEXT NOT NULL DEFAULT 'basic'")
    run(conn, "ALTER TABLE member ADD COLUMN joined TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP")
    query(conn, "5-A 기존 행에도 기본값이 보인다", "SELECT id, grade FROM member WHERE id <= 3")


if __name__ == "__main__":
    main()
