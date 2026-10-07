"""INSERT ... ON CONFLICT(UPSERT)가 어떤 행을 갱신하고 어떤 행을 그대로 두는지 확인한다.

재고 표(stock)에 입고를 반영하고, 회원 표(member)에서 충돌 대상을 무엇으로 잡느냐에 따라
결과가 갈리는 것을 본다. INSERT OR REPLACE와도 나란히 비교한다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

SCHEMA = """
CREATE TABLE stock (
    sku         TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    qty         INTEGER NOT NULL DEFAULT 0,
    memo        TEXT,
    updated_at  TEXT NOT NULL
);
CREATE TABLE member (
    id           INTEGER PRIMARY KEY,
    email        TEXT NOT NULL UNIQUE,
    nickname     TEXT,
    login_count  INTEGER NOT NULL DEFAULT 0
);
"""

STOCK_SEED = [
    ("A-100", "볼펜", 10, "창고 2층", "2026-10-01"),
    ("B-200", "공책", 5, None, "2026-10-01"),
]
MEMBER_SEED = [
    (1, "a@example.com", "도윤", 3),
    (2, "b@example.com", "서준", 1),
]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO stock VALUES (?, ?, ?, ?, ?)", STOCK_SEED)
    conn.executemany("INSERT INTO member VALUES (?, ?, ?, ?)", MEMBER_SEED)
    conn.commit()
    return conn


def run(conn: sqlite3.Connection, sql: str) -> None:
    """에러도 결과로 찍는다. rowcount 는 그 문장이 넣거나 바꾼 행 수다."""
    shown = " ".join(sql.split())
    try:
        cur = conn.execute(sql)
        print(f"  성공  {shown}\n        -> 바뀐 행 {cur.rowcount}")
    except sqlite3.Error as exc:
        print(f"  에러  {shown}\n        -> {type(exc).__name__}: {exc}")


def query(conn: sqlite3.Connection, label: str, sql: str) -> None:
    print(f"\n[{label}]")
    print(f"  {' '.join(sql.split())}")
    cur = conn.execute(sql)
    print(f"  {tuple(col[0] for col in cur.description)}")
    for row in cur.fetchall():
        print(f"  {row}")


def show_stock(conn: sqlite3.Connection, label: str) -> None:
    query(conn, label, "SELECT rowid, sku, qty, memo, updated_at FROM stock ORDER BY sku")


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("\n== 1. 그냥 INSERT 는 같은 키에서 멈춘다 ==")
    run(conn, "INSERT INTO stock VALUES ('A-100', '볼펜', 3, NULL, '2026-10-05')")

    print("\n== 2. DO NOTHING — 있으면 넘어가고 없으면 넣는다 ==")
    run(conn, """INSERT INTO stock (sku, name, qty, updated_at)
                 VALUES ('A-100', '볼펜', 3, '2026-10-05')
                 ON CONFLICT (sku) DO NOTHING""")
    run(conn, """INSERT INTO stock (sku, name, qty, updated_at)
                 VALUES ('C-300', '지우개', 7, '2026-10-05')
                 ON CONFLICT (sku) DO NOTHING""")
    show_stock(conn, "2-A 결과")

    print("\n== 3. DO UPDATE — excluded 는 넣으려던 값, 컬럼 이름만 쓰면 기존 값 ==")
    run(conn, """INSERT INTO stock (sku, name, qty, updated_at)
                 VALUES ('A-100', '볼펜', 3, '2026-10-05')
                 ON CONFLICT (sku) DO UPDATE
                 SET qty = qty + excluded.qty, updated_at = excluded.updated_at""")
    show_stock(conn, "3-A A-100 은 10 + 3, 메모는 그대로")

    print("\n== 4. DO UPDATE ... WHERE — 조건이 거짓이면 아무것도 안 한다 ==")
    run(conn, """INSERT INTO stock (sku, name, qty, updated_at)
                 VALUES ('B-200', '공책', 0, '2026-09-30')
                 ON CONFLICT (sku) DO UPDATE
                 SET qty = excluded.qty, updated_at = excluded.updated_at
                 WHERE excluded.updated_at > stock.updated_at""")
    run(conn, """INSERT INTO stock (sku, name, qty, updated_at)
                 VALUES ('B-200', '공책', 0, '2026-10-06')
                 ON CONFLICT (sku) DO UPDATE
                 SET qty = excluded.qty, updated_at = excluded.updated_at
                 WHERE excluded.updated_at > stock.updated_at""")
    show_stock(conn, "4-A 오래된 값은 무시, 새 값만 반영")

    print("\n== 5. INSERT OR REPLACE 는 지우고 새로 넣는다 ==")
    run(conn, """INSERT OR REPLACE INTO stock (sku, name, qty, updated_at)
                 VALUES ('A-100', '볼펜', 20, '2026-10-07')""")
    show_stock(conn, "5-A 메모가 사라지고 rowid 가 바뀐다")

    print("\n== 6. 같은 문장 안에서 같은 키가 두 번 나오면 ==")
    run(conn, """INSERT INTO stock (sku, name, qty, updated_at)
                 VALUES ('D-400', '자', 1, '2026-10-07'),
                        ('D-400', '자', 2, '2026-10-07')
                 ON CONFLICT (sku) DO UPDATE SET qty = qty + excluded.qty""")
    query(conn, "6-A 두 번째 행이 첫 번째 행과 충돌한다", "SELECT sku, qty FROM stock WHERE sku = 'D-400'")

    print("\n== 7. 충돌 대상을 무엇으로 잡는가 ==")
    run(conn, """INSERT INTO member (id, email, nickname) VALUES (3, 'a@example.com', '도윤2')
                 ON CONFLICT (email) DO UPDATE SET login_count = login_count + 1""")
    run(conn, """INSERT INTO member (id, email, nickname) VALUES (1, 'new@example.com', '새회원')
                 ON CONFLICT (email) DO UPDATE SET login_count = login_count + 1""")
    run(conn, """INSERT INTO member (id, email, nickname) VALUES (1, 'new@example.com', '새회원')
                 ON CONFLICT (nickname) DO NOTHING""")
    run(conn, """INSERT INTO member (id, email, nickname) VALUES (1, 'new@example.com', '새회원')
                 ON CONFLICT (email) DO UPDATE SET login_count = login_count + 1
                 ON CONFLICT (id) DO NOTHING""")
    run(conn, """INSERT INTO member (id, email, nickname) VALUES (2, 'x@example.com', '서준2')
                 ON CONFLICT DO UPDATE SET login_count = login_count + 1""")
    run(conn, """INSERT INTO member (id, email, nickname) VALUES (9, 'b@example.com', '서준3')
                 ON CONFLICT DO UPDATE SET login_count = login_count + 1""")
    query(conn, "7-A 회원 표", "SELECT id, email, nickname, login_count FROM member ORDER BY id")

    print("\n== 8. INSERT ... SELECT 에 붙일 때 ==")
    conn.execute("CREATE TABLE incoming (sku TEXT, name TEXT, qty INTEGER)")
    conn.execute("INSERT INTO incoming VALUES ('B-200', '공책', 4), ('E-500', '풀', 2)")
    run(conn, """INSERT INTO stock (sku, name, qty, updated_at)
                 SELECT sku, name, qty, '2026-10-07' FROM incoming
                 ON CONFLICT (sku) DO UPDATE SET qty = qty + excluded.qty""")
    run(conn, """INSERT INTO stock (sku, name, qty, updated_at)
                 SELECT sku, name, qty, '2026-10-07' FROM incoming WHERE true
                 ON CONFLICT (sku) DO UPDATE SET qty = qty + excluded.qty""")
    show_stock(conn, "8-A 최종 재고")
    conn.close()


if __name__ == "__main__":
    main()
