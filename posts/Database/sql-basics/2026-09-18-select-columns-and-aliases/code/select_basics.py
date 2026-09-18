"""SELECT 목록과 별칭이 실제로 무엇을 바꾸는지 SQLite로 확인한다.

1) SELECT * 와 필요한 컬럼만 고른 질의의 실행계획·시간 비교
2) 별칭을 ORDER BY에서 쓸 수 있고 WHERE에서는 쓸 수 없다는 것을 에러로 확인
3) SELECT * 는 컬럼이 추가되면 결과의 컬럼 개수와 위치가 바뀐다는 것 확인

표준 라이브러리만 쓴다.  실행: python select_basics.py
"""

from __future__ import annotations

import random
import sqlite3
import time

ROW_COUNT = 200_000
REPEAT_COUNT = 5
RANDOM_SEED = 20260918  # 시드를 고정해야 측정값이 재현된다

GENRE_NAMES = ["fiction", "essay", "science", "history", "poetry"]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE book (
            book_id     INTEGER PRIMARY KEY,
            genre       TEXT NOT NULL,
            title       TEXT NOT NULL,
            author_name TEXT NOT NULL,
            summary     TEXT NOT NULL,
            price       INTEGER NOT NULL
        )
        """
    )
    rng = random.Random(RANDOM_SEED)
    rows = [
        (
            book_id,
            rng.choice(GENRE_NAMES),
            f"book-{book_id:06d}",
            f"author-{rng.randrange(1, 5_000):04d}",
            "s" * 200,  # 본문 컬럼이 무거울 때 SELECT * 가 무엇을 읽는지 보기 위해서다
            rng.randrange(5_000, 90_000),
        )
        for book_id in range(1, ROW_COUNT + 1)
    ]
    conn.executemany("INSERT INTO book VALUES (?, ?, ?, ?, ?, ?)", rows)
    conn.execute("CREATE INDEX ix_book_genre_title ON book(genre, title)")
    conn.execute("ANALYZE")
    return conn


def plan_of(conn: sqlite3.Connection, sql: str, params: tuple) -> str:
    rows = conn.execute(f"EXPLAIN QUERY PLAN {sql}", params).fetchall()
    return " / ".join(row[3] for row in rows)


def measure(conn: sqlite3.Connection, sql: str, params: tuple) -> tuple[float, int]:
    best_ms = float("inf")
    fetched = 0
    for _ in range(REPEAT_COUNT):
        started = time.perf_counter()
        fetched = len(conn.execute(sql, params).fetchall())
        best_ms = min(best_ms, (time.perf_counter() - started) * 1000)
    return best_ms, fetched


def compare_select_list(conn: sqlite3.Connection) -> None:
    print("\n### 1. SELECT * 와 필요한 컬럼만 고른 질의")
    params = ("science",)
    queries = {
        "SELECT *": "SELECT * FROM book WHERE genre = ?",
        "SELECT title": "SELECT title FROM book WHERE genre = ?",
    }
    for label, sql in queries.items():
        best_ms, fetched = measure(conn, sql, params)
        print(f"  {label:14s} {best_ms:8.2f}ms  {fetched:,}행")
        print(f"      {plan_of(conn, sql, params)}")


def show_alias_rules(conn: sqlite3.Connection) -> None:
    print("\n### 2. 별칭을 쓸 수 있는 자리")
    sql_order_by = (
        "SELECT title AS book_title, price / 1000 AS price_in_thousand "
        "FROM book WHERE genre = ? ORDER BY price_in_thousand DESC LIMIT 3"
    )
    print("  ORDER BY에서 별칭 사용:")
    for row in conn.execute(sql_order_by, ("poetry",)):
        print(f"    {row}")

    # SQL 표준과 PostgreSQL은 WHERE에서 결과 컬럼 별칭을 허용하지 않는다.
    # SQLite가 어떻게 처리하는지는 직접 돌려서 확인한다.
    by_alias = "SELECT COUNT(*) FROM (SELECT price / 1000 AS kw FROM book WHERE kw > 80)"
    by_expression = "SELECT COUNT(*) FROM book WHERE price / 1000 > 80"
    print("  WHERE에서 별칭 사용:")
    try:
        alias_count = conn.execute(by_alias).fetchone()[0]
        expression_count = conn.execute(by_expression).fetchone()[0]
        print(f"    에러 없이 실행됐다. 별칭 {alias_count:,}행 / 식 직접 {expression_count:,}행"
              f" → 같은가: {alias_count == expression_count}")
    except sqlite3.OperationalError as error:
        print(f"    sqlite3.OperationalError: {error}")

    # 별칭이 실제 컬럼명과 같으면 WHERE가 어느 쪽으로 해석하는지 확인한다.
    shadowed = conn.execute(
        "SELECT COUNT(*) FROM (SELECT price / 1000 AS price FROM book WHERE price > 80)"
    ).fetchone()[0]
    base_column = conn.execute("SELECT COUNT(*) FROM book WHERE price > 80").fetchone()[0]
    print(f"  별칭이 컬럼명을 가릴 때 (AS price, WHERE price > 80):")
    print(f"    별칭을 가진 질의 {shadowed:,}행 / 원본 컬럼 기준 {base_column:,}행")

    print("  공백이 있는 별칭은 큰따옴표로 감싼다:")
    cursor = conn.execute('SELECT title AS "책 제목" FROM book LIMIT 1')
    print(f"    컬럼명={[c[0] for c in cursor.description]} 값={cursor.fetchone()}")


def show_star_breaks_on_schema_change(conn: sqlite3.Connection) -> None:
    print("\n### 3. 컬럼이 추가되면 SELECT * 의 결과 모양이 바뀐다")
    cursor = conn.execute("SELECT * FROM book WHERE book_id = 1")
    before = [c[0] for c in cursor.description]
    row_before = cursor.fetchone()
    print(f"  추가 전: {len(before)}컬럼 {before}")
    print(f"           마지막 값 = {row_before[-1]}")

    conn.execute("ALTER TABLE book ADD COLUMN stock_count INTEGER DEFAULT 0")
    cursor = conn.execute("SELECT * FROM book WHERE book_id = 1")
    after = [c[0] for c in cursor.description]
    row_after = cursor.fetchone()
    print(f"  추가 후: {len(after)}컬럼 {after}")
    print(f"           마지막 값 = {row_after[-1]}  ← price를 기대한 코드는 여기서 깨진다")

    cursor = conn.execute("SELECT price FROM book WHERE book_id = 1")
    print(f"  SELECT price: {[c[0] for c in cursor.description]} {cursor.fetchone()}")


def main() -> None:
    print(f"SQLite {sqlite3.sqlite_version} · 행 {ROW_COUNT:,} · 각 질의 {REPEAT_COUNT}회 중 최솟값")
    conn = build_database()
    compare_select_list(conn)
    show_alias_rules(conn)
    show_star_breaks_on_schema_change(conn)
    conn.close()


if __name__ == "__main__":
    main()
