"""SQLite 의 ALTER TABLE 이 되는 변경과 안 되는 변경, 안 되는 변경의 우회 절차를 확인한다.

되는 것은 넷(RENAME TO, RENAME COLUMN, ADD COLUMN, DROP COLUMN)이고 각각 조건이 붙는다.
그 밖의 변경은 새 표를 만들어 옮기는 절차로 한다. 절차의 순서를 바꾸면 무엇이 깨지는지도 본다.
"""

import sqlite3

from dbshow import print_dataset, print_environment, print_table

SCHEMA = """
CREATE TABLE member (
    member_id  INTEGER PRIMARY KEY,
    name       TEXT,
    phone      TEXT
);
CREATE TABLE orders (
    order_id   INTEGER PRIMARY KEY,
    member_id  INTEGER REFERENCES member (member_id),
    amount     INTEGER NOT NULL
);
CREATE INDEX ix_member_phone ON member (phone);
CREATE VIEW v_member_order AS
    SELECT m.name, o.amount FROM member m JOIN orders o ON o.member_id = m.member_id;
INSERT INTO member VALUES (1, '김하나', '010-1111'), (2, '이두리', NULL), (3, '박세찬', '010-3333');
INSERT INTO orders VALUES (10, 1, 5000), (11, 3, 7000);
"""


def build_database():
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def attempt(conn, sql):
    """실패해도 멈추지 않고 SQLite 가 돌려준 오류 문구를 그대로 찍는다."""
    try:
        conn.execute(sql)
        print(f"   [성공] {sql}")
    except sqlite3.Error as exc:
        print(f"   [실패] {sql}")
        print(f"          → {type(exc).__name__}: {exc}")


def show(conn, sql):
    print(f"   {sql}")
    for row in conn.execute(sql).fetchall():
        print("   " + " | ".join("NULL" if v is None else str(v) for v in row))
    print()


def schema_sql(conn, name):
    row = conn.execute("SELECT sql FROM sqlite_schema WHERE name = ?", (name,)).fetchone()
    return row[0] if row else None


def main():
    print_environment()
    conn = build_database()
    print_dataset(conn)

    print("-- 1. ADD COLUMN — 끝에 붙고, 기존 행은 기본값을 받는다")
    attempt(conn, "ALTER TABLE member ADD COLUMN grade TEXT DEFAULT 'basic'")
    show(conn, "SELECT member_id, name, grade FROM member")

    print("-- 2. ADD COLUMN 이 거절하는 네 가지")
    attempt(conn, "ALTER TABLE member ADD COLUMN email TEXT NOT NULL")
    attempt(conn, "ALTER TABLE member ADD COLUMN email TEXT UNIQUE")
    attempt(conn, "ALTER TABLE member ADD COLUMN joined_at TEXT DEFAULT CURRENT_TIMESTAMP")
    attempt(conn, "ALTER TABLE member ADD COLUMN point INTEGER DEFAULT 0 CHECK (point > 0)")
    attempt(conn, "ALTER TABLE member ADD COLUMN email TEXT NOT NULL DEFAULT ''")
    print()

    print("-- 3. RENAME COLUMN — 인덱스와 뷰의 정의까지 바뀐다")
    attempt(conn, "ALTER TABLE member RENAME COLUMN name TO member_name")
    print(f"   뷰 정의: {schema_sql(conn, 'v_member_order')}")
    print()

    print("-- 4. DROP COLUMN — 인덱스가 걸린 컬럼은 못 지운다")
    attempt(conn, "ALTER TABLE member DROP COLUMN phone")
    attempt(conn, "ALTER TABLE member DROP COLUMN email")
    print()

    print("-- 5. 그 밖의 변경 — 이 판에는 문법이 없다")
    attempt(conn, "ALTER TABLE member ALTER COLUMN member_name SET NOT NULL")
    attempt(conn, "ALTER TABLE member ALTER COLUMN phone TYPE INTEGER")
    print()

    print("-- 6. 우회 절차 — 문서의 단계 번호 순서 그대로 (뷰는 9단계에서 다시 만든다)")
    rebuild(conn, drop_view_first=False)
    print(f"   ROLLBACK 뒤 member 컬럼: {columns_of(conn, 'member')}")
    print()

    print("-- 7. 우회 절차 — 뷰를 옛 표보다 먼저 지운다")
    rebuild(conn, drop_view_first=True)
    print_table(conn, "member")
    show(conn, "SELECT * FROM v_member_order")
    show(conn, "PRAGMA foreign_key_check")
    attempt(conn, "INSERT INTO member (member_id, member_name) VALUES (4, NULL)")
    print()

    print("-- 8. 순서를 바꾸면 — 옛 표 이름을 먼저 바꾼다")
    conn.close()
    rebuild_wrong_order()


def columns_of(conn, table):
    return [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]


def rebuild(conn, *, drop_view_first):
    """member_name 에 NOT NULL 을 더한다. 공식 문서의 새 표 → 복사 → 삭제 → 이름 바꾸기 순서다."""
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("BEGIN")
    # 문서 3단계의 조회. 뷰는 tbl_name 이 뷰 자신의 이름이라 여기에 안 걸린다
    saved = conn.execute(
        "SELECT type, name FROM sqlite_schema WHERE tbl_name = 'member' AND type <> 'table'"
    ).fetchall()
    print(f"   tbl_name = 'member' 로 찾은 객체: {saved}")
    view_sql = schema_sql(conn, "v_member_order")
    if drop_view_first:
        conn.execute("DROP VIEW v_member_order")
    conn.execute("""
        CREATE TABLE new_member (
            member_id    INTEGER PRIMARY KEY,
            member_name  TEXT NOT NULL,
            phone        TEXT,
            grade        TEXT DEFAULT 'basic'
        )""")
    conn.execute("INSERT INTO new_member SELECT member_id, member_name, phone, grade "
                 "FROM member")
    conn.execute("DROP TABLE member")
    try:
        conn.execute("ALTER TABLE new_member RENAME TO member")
    except sqlite3.Error as exc:
        print("   [실패] ALTER TABLE new_member RENAME TO member")
        print(f"          → {type(exc).__name__}: {exc}")
        conn.execute("ROLLBACK")
        conn.execute("PRAGMA foreign_keys = ON")
        return
    conn.execute("CREATE INDEX ix_member_phone ON member (phone)")
    if drop_view_first:
        conn.execute(view_sql)
    conn.execute("COMMIT")
    conn.execute("PRAGMA foreign_keys = ON")
    print("   [성공] 새 표 → 복사 → DROP TABLE member → RENAME → 인덱스·뷰 재생성 → COMMIT")
    print(f"   orders 정의: {schema_sql(conn, 'orders')}")
    print()


def rebuild_wrong_order():
    conn = build_database()
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("BEGIN")
    conn.execute("ALTER TABLE member RENAME TO old_member")
    print(f"   이름을 바꾼 직후 orders 정의: {schema_sql(conn, 'orders')}")
    conn.execute("CREATE TABLE member (member_id INTEGER PRIMARY KEY, name TEXT NOT NULL, "
                 "phone TEXT)")
    conn.execute("INSERT INTO member SELECT * FROM old_member")
    conn.execute("DROP TABLE old_member")
    conn.execute("COMMIT")
    conn.execute("PRAGMA foreign_keys = ON")
    print(f"   끝난 뒤 orders 정의: {schema_sql(conn, 'orders')}")
    attempt(conn, "SELECT * FROM v_member_order")
    attempt(conn, "INSERT INTO orders VALUES (12, 2, 3000)")
    conn.close()


if __name__ == "__main__":
    main()
