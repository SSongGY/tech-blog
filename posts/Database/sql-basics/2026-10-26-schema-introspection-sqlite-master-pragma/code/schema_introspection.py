"""sqlite_master 와 PRAGMA 로 스키마 정의를 질의해 꺼내 본다.

표·인덱스·뷰·트리거가 섞인 작은 스키마를 만들고, 그 정의를
(1) sqlite_master 의 원문 DDL 과 (2) PRAGMA 가 파싱해 준 항목으로
각각 읽어 무엇이 다른지 대조한다.
"""

import sqlite3

from dbshow import print_environment, print_dataset

RULE = "=" * 64

SCHEMA = """
CREATE TABLE author (
    author_id INTEGER PRIMARY KEY,
    name      TEXT NOT NULL UNIQUE,
    country   TEXT DEFAULT 'KR'
);

CREATE TABLE book (
    isbn        TEXT    NOT NULL,
    edition     INTEGER NOT NULL DEFAULT 1,
    title       TEXT    NOT NULL,
    author_id   INTEGER REFERENCES author(author_id) ON DELETE SET NULL,
    price       INTEGER CHECK (price >= 0),
    title_fold  TEXT GENERATED ALWAYS AS (lower(title)) VIRTUAL,
    PRIMARY KEY (isbn, edition)
);

CREATE UNIQUE INDEX ux_book_title ON book(title, edition DESC);
CREATE INDEX ix_book_cheap ON book(price) WHERE price < 20000;

CREATE VIEW v_book_author AS
    SELECT b.title, a.name AS author
    FROM book b LEFT JOIN author a ON a.author_id = b.author_id;

CREATE TRIGGER trg_book_price_floor
AFTER UPDATE OF price ON book
WHEN NEW.price < 0
BEGIN
    SELECT RAISE(ABORT, 'price must not be negative');
END;
"""

ROWS_AUTHOR = [
    (1, "김연수", "KR"),
    (2, "Ursula K. Le Guin", "US"),
]
ROWS_BOOK = [
    ("978-89-001", 1, "파도가 바다의 일이라면", 1, 15000),
    ("978-89-001", 2, "파도가 바다의 일이라면", 1, 17000),
    ("978-00-204", 1, "The Dispossessed", 2, 24000),
]


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO author VALUES (?, ?, ?)", ROWS_AUTHOR)
    conn.executemany(
        "INSERT INTO book (isbn, edition, title, author_id, price) VALUES (?, ?, ?, ?, ?)",
        ROWS_BOOK,
    )
    conn.commit()
    return conn


def section(title):
    print(RULE)
    print(title)
    print(RULE)


def dump(conn, sql, params=()):
    """질의 결과를 컬럼 이름과 함께 찍는다."""
    cur = conn.execute(sql, params)
    names = [d[0] for d in cur.description]
    rows = cur.fetchall()
    widths = [len(n) for n in names]
    cells = [[("NULL" if v is None else str(v)) for v in row] for row in rows]
    for row in cells:
        widths = [max(w, len(c)) for w, c in zip(widths, row)]
    print("  " + " | ".join(n.ljust(w) for n, w in zip(names, widths)))
    print("  " + "-+-".join("-" * w for w in widths))
    for row in cells:
        print("  " + " | ".join(c.ljust(w) for c, w in zip(row, widths)))
    print()


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)

    section("1. sqlite_master — 이 데이터베이스에 무엇이 들어 있는가")
    dump(conn, """
        SELECT type, name, tbl_name, sql IS NULL AS sql_is_null
        FROM sqlite_master
        ORDER BY type, name
    """)

    section("2. sqlite_master.sql — 정의는 친 문장 그대로 남는다")
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE name = 'ix_book_cheap'"
    ).fetchone()
    print(row[0])
    print()

    section("3. PRAGMA table_info(book) — 컬럼 목록")
    dump(conn, "PRAGMA table_info(book)")

    section("4. PRAGMA table_xinfo(book) — 숨은 컬럼까지")
    dump(conn, "PRAGMA table_xinfo(book)")

    section("5. PRAGMA index_list — 이 표에 달린 인덱스")
    dump(conn, "PRAGMA index_list(book)")
    dump(conn, "PRAGMA index_list(author)")

    section("6. PRAGMA index_xinfo(ux_book_title) — 인덱스 안의 컬럼 순서")
    dump(conn, "PRAGMA index_xinfo(ux_book_title)")

    section("7. PRAGMA foreign_key_list(book) — 외래키")
    dump(conn, "PRAGMA foreign_key_list(book)")

    section("8. pragma_ 테이블 값 함수 — 모든 표의 컬럼을 한 번에")
    dump(conn, """
        -- notnull 은 SQLite 에서 후위 연산자 키워드라 따옴표로 감싸야 컬럼으로 읽힌다
        SELECT m.name AS tbl, c.cid, c.name AS col, c.type, c."notnull", c."dflt_value"
        FROM sqlite_master AS m
        JOIN pragma_table_info(m.name) AS c
        WHERE m.type = 'table'
        ORDER BY m.name, c.cid
    """)

    section("9. NOT NULL 인데 기본값이 없는 컬럼 — 적재 전에 걸러낼 것들")
    dump(conn, """
        SELECT m.name AS tbl, c.name AS col
        FROM sqlite_master AS m
        JOIN pragma_table_info(m.name) AS c
        WHERE m.type = 'table'
          AND c."notnull" = 1 AND c."dflt_value" IS NULL AND c.pk = 0
        ORDER BY m.name, c.cid
    """)

    section("10. author_id 는 PK 인데 notnull 이 0 이다 — 정말 NULL 이 들어가나")
    conn.execute("INSERT INTO author (author_id, name) VALUES (NULL, '이름 없음')")
    dump(conn, "SELECT author_id, name FROM author ORDER BY author_id")

    section("11. PRAGMA 인자에 플레이스홀더를 쓸 수 있나")
    try:
        conn.execute("PRAGMA table_info(?)", ("book",)).fetchall()
        print("  PRAGMA table_info(?) — 통과")
    except sqlite3.Error as exc:
        print(f"  PRAGMA table_info(?) — {type(exc).__name__}: {exc}")
    print()
    dump(conn, "SELECT cid, name, type FROM pragma_table_info(?)", ("book",))

    conn.close()


if __name__ == "__main__":
    main()
