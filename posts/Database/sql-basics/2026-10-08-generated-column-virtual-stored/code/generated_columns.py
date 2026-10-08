"""생성 컬럼(generated column)의 VIRTUAL 과 STORED 를 SQLite 로 돌려 본다.

보는 것: 값이 따라 바뀌는 것, 직접 넣을 때의 에러, ALTER TABLE 로 추가되는 쪽,
PRAGMA table_info 와 table_xinfo 의 차이, 쓸 수 없는 식, 생성 컬럼 위의 인덱스와
실행계획, 10만 행에서의 저장 공간과 조회 시간.
"""

import os
import sqlite3
import tempfile
import time

from dbshow import print_dataset, print_environment

BULK_ROWS = 100_000
REPEAT = 5

SCHEMA = """
CREATE TABLE order_item (
    order_item_id INTEGER PRIMARY KEY,
    product       TEXT    NOT NULL,
    unit_price    INTEGER NOT NULL,
    quantity      INTEGER NOT NULL,
    ordered_at    TEXT    NOT NULL,
    line_total    INTEGER GENERATED ALWAYS AS (unit_price * quantity) VIRTUAL,
    order_month   TEXT    GENERATED ALWAYS AS (substr(ordered_at, 1, 7)) STORED
);
"""

ITEMS = [
    (1, "키보드", 45000, 2, "2026-09-03 10:20:00"),
    (2, "마우스", 25000, 1, "2026-09-03 10:20:00"),
    (3, "모니터", 320000, 1, "2026-09-18 15:02:00"),
    (4, "케이블", 8000, 5, "2026-10-01 09:11:00"),
    (5, "허브", 39000, 3, "2026-10-02 18:40:00"),
]


def build_database(path: str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO order_item VALUES (?, ?, ?, ?, ?)", ITEMS)
    conn.commit()
    return conn


def run(conn: sqlite3.Connection, title: str, sql: str) -> None:
    print(f"\n-- {title}")
    for line in sql.strip().splitlines():
        print(f"   {line}")
    try:
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
    except sqlite3.Error as exc:
        print(f"   에러: {exc}")
        return
    if cursor.description is None:
        print("   (결과 없음)")
        return
    header = [d[0] for d in cursor.description]
    print("   => " + " | ".join(header))
    for row in rows:
        print("      " + " | ".join("NULL" if v is None else str(v) for v in row))
    print(f"   ({len(rows)}행)")


def plan(conn: sqlite3.Connection, title: str, sql: str) -> None:
    """sqlite3 CLI 가 그리는 모양으로 EXPLAIN QUERY PLAN 을 찍는다."""
    print(f"\n-- {title}")
    for line in sql.strip().splitlines():
        print(f"   {line}")
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    children: dict[int, list[tuple[int, str]]] = {}
    for node_id, parent, _, detail in rows:
        children.setdefault(parent, []).append((node_id, detail))

    def draw(parent: int, prefix: str) -> None:
        kids = children.get(parent, [])
        for i, (node_id, detail) in enumerate(kids):
            last = i == len(kids) - 1
            print(f"   {prefix}{'`--' if last else '|--'}{detail}")
            draw(node_id, prefix + ("   " if last else "|  "))

    print("   QUERY PLAN")
    draw(0, "")


def print_generated_columns(conn: sqlite3.Connection, table: str) -> None:
    """dbshow 는 PRAGMA table_info 를 쓰므로 생성 컬럼이 빠진다. 따로 찍는다."""
    print(f"[{table} 의 생성 컬럼]  (PRAGMA table_xinfo 의 hidden: 2=VIRTUAL, 3=STORED)")
    sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE name = ?", (table,)
    ).fetchone()[0]
    for line in sql.splitlines():
        if "GENERATED" in line:
            print("  " + line.strip())
    print()


def try_create(conn: sqlite3.Connection, title: str, ddl: str) -> None:
    print(f"\n-- {title}")
    for line in ddl.strip().splitlines():
        print(f"   {line}")
    try:
        conn.execute(ddl)
        print("   => 만들어짐")
        conn.execute("DROP TABLE IF EXISTS probe")
    except sqlite3.Error as exc:
        print(f"   에러: {exc}")


def measure(conn: sqlite3.Connection, sql: str) -> float:
    best = float("inf")
    for _ in range(REPEAT):
        started = time.perf_counter()
        conn.execute(sql).fetchall()
        best = min(best, time.perf_counter() - started)
    return best


def bulk_compare() -> None:
    """같은 10만 행을 VIRTUAL 과 STORED 로 나눠 담고 파일 크기와 조회 시간을 잰다."""
    print("\n-- 11. 10만 행 — 저장 공간과 조회 시간 (VIRTUAL vs STORED)")
    with tempfile.TemporaryDirectory() as workdir:
        for kind in ("VIRTUAL", "STORED"):
            path = os.path.join(workdir, f"{kind.lower()}.db")
            conn = sqlite3.connect(path)
            try:
                conn.execute(f"""
CREATE TABLE sale (
    sale_id    INTEGER PRIMARY KEY,
    unit_price INTEGER NOT NULL,
    quantity   INTEGER NOT NULL,
    sold_at    TEXT    NOT NULL,
    line_total INTEGER GENERATED ALWAYS AS (unit_price * quantity) {kind},
    sold_month TEXT    GENERATED ALWAYS AS (substr(sold_at, 1, 7)) {kind},
    label      TEXT    GENERATED ALWAYS AS (printf('%s/%d', sold_at, unit_price)) {kind}
)""")
                # 값을 결정적으로 만든다 — 난수 없이 행 번호에서 계산.
                # 파이썬 내장 SQLite 에는 generate_series 확장이 없어 재귀 CTE 로 번호를 만든다.
                conn.execute(f"""
WITH RECURSIVE seq (value) AS (
    SELECT 1
    UNION ALL
    SELECT value + 1 FROM seq WHERE value < {BULK_ROWS}
)
INSERT INTO sale (sale_id, unit_price, quantity, sold_at)
SELECT value,
       (value % 97) * 100 + 100,
       value % 7 + 1,
       '2026-' || printf('%02d', value % 12 + 1) || '-' || printf('%02d', value % 28 + 1)
FROM seq""")
                conn.commit()
                conn.execute("VACUUM")
                page_count = conn.execute("PRAGMA page_count").fetchone()[0]
                page_size = conn.execute("PRAGMA page_size").fetchone()[0]
                size_kb = page_count * page_size // 1024
                sum_sec = measure(conn, "SELECT SUM(line_total) FROM sale")
                filter_sec = measure(conn, "SELECT COUNT(*) FROM sale WHERE sold_month = '2026-03'")
                label_sec = measure(conn, "SELECT COUNT(*) FROM sale WHERE label LIKE '2026-03%'")
                raw_sec = measure(conn, "SELECT SUM(unit_price * quantity) FROM sale")
                print(f"   {kind:7s}: 파일 {size_kb:>6,} KB ({page_count:,} 페이지) · "
                      f"SUM(line_total) {sum_sec * 1000:7.1f} ms · "
                      f"WHERE sold_month {filter_sec * 1000:7.1f} ms · "
                      f"WHERE label LIKE {label_sec * 1000:7.1f} ms · "
                      f"SUM(식 직접) {raw_sec * 1000:7.1f} ms")
            finally:
                conn.close()
    print("   (각 시간은 5회 중 가장 짧은 값. 절대값은 환경마다 다르고 비율만 본다)")


def main() -> None:
    conn = build_database()
    try:
        print_environment()
        print_dataset(conn)
        print_generated_columns(conn, "order_item")

        run(conn, "1. 생성 컬럼을 모르면 — 식을 질의마다 되풀이해 쓴다", """
SELECT product, unit_price * quantity AS line_total
FROM order_item
WHERE unit_price * quantity >= 50000
ORDER BY unit_price * quantity DESC
""")

        run(conn, "2. 생성 컬럼은 보통 컬럼처럼 읽는다 — SELECT * 에도 나온다", """
SELECT * FROM order_item ORDER BY order_item_id
""")

        run(conn, "3. 원본 컬럼을 고치면 두 생성 컬럼이 따라 바뀐다", """
UPDATE order_item SET quantity = 4, ordered_at = '2026-11-05 11:00:00'
WHERE order_item_id = 1
""")
        run(conn, "3-A. 고친 뒤", """
SELECT order_item_id, quantity, line_total, ordered_at, order_month
FROM order_item WHERE order_item_id = 1
""")

        run(conn, "4-A. 생성 컬럼에 값을 직접 넣으면", """
INSERT INTO order_item (product, unit_price, quantity, ordered_at, line_total)
VALUES ('독', 1000, 1, '2026-10-03 00:00:00', 999)
""")
        run(conn, "4-B. UPDATE 로 바꾸려 해도", """
UPDATE order_item SET line_total = 0 WHERE order_item_id = 2
""")
        run(conn, "4-C. 컬럼 목록을 생략한 INSERT 는 생성 컬럼을 세지 않는다 (값 5개)", """
INSERT INTO order_item VALUES (6, '거치대', 15000, 2, '2026-10-03 12:00:00')
""")

        run(conn, "5-A. ALTER TABLE 로 VIRTUAL 생성 컬럼은 더할 수 있다", """
ALTER TABLE order_item
ADD COLUMN unit_price_with_vat INTEGER GENERATED ALWAYS AS (unit_price * 11 / 10) VIRTUAL
""")
        run(conn, "5-B. STORED 는 더할 수 없다", """
ALTER TABLE order_item
ADD COLUMN line_total_stored INTEGER GENERATED ALWAYS AS (unit_price * quantity) STORED
""")

        run(conn, "6-A. PRAGMA table_info — 생성 컬럼이 빠진다", """
SELECT cid, name, type FROM pragma_table_info('order_item')
""")
        run(conn, "6-B. PRAGMA table_xinfo — hidden 이 2(VIRTUAL)·3(STORED)", """
SELECT cid, name, type, hidden FROM pragma_table_xinfo('order_item')
""")

        run(conn, "7. 생성 컬럼이 다른 생성 컬럼을 참조할 수 있다 (순환만 아니면)", """
SELECT product, line_total, line_total * 11 / 10 AS with_vat
FROM order_item WHERE order_item_id IN (1, 3)
""")
        try_create(conn, "7-A. 참조 사슬 — tax 가 line_total 을 쓴다", """
CREATE TABLE probe (
    unit_price INTEGER, quantity INTEGER,
    line_total INTEGER AS (unit_price * quantity),
    tax        INTEGER AS (line_total / 10)
)""")
        try_create(conn, "7-B. 순환 참조", """
CREATE TABLE probe (
    a INTEGER AS (b + 1),
    b INTEGER AS (a + 1),
    c INTEGER
)""")

        try_create(conn, "8-A. 쓸 수 없는 것 — DEFAULT", """
CREATE TABLE probe (x INTEGER, y INTEGER AS (x * 2) DEFAULT 0)""")
        try_create(conn, "8-B. 쓸 수 없는 것 — PRIMARY KEY", """
CREATE TABLE probe (x INTEGER, y INTEGER AS (x * 2) PRIMARY KEY)""")
        try_create(conn, "8-C. 쓸 수 없는 것 — 결정적이지 않은 함수", """
CREATE TABLE probe (x INTEGER, y INTEGER AS (x + random()))""")
        try_create(conn, "8-D. 쓸 수 없는 것 — 서브쿼리", """
CREATE TABLE probe (x INTEGER, y INTEGER AS ((SELECT MAX(order_item_id) FROM order_item)))""")
        try_create(conn, "8-E. 쓸 수 없는 것 — 생성 컬럼만 있는 표", """
CREATE TABLE probe (y INTEGER AS (1 + 1))""")
        try_create(conn, "8-F. 되는 것 — CHECK 와 NOT NULL 은 생성 컬럼에도 붙는다", """
CREATE TABLE probe (
    unit_price INTEGER, quantity INTEGER,
    line_total INTEGER AS (unit_price * quantity) STORED CHECK (line_total >= 0)
)""")
        conn.execute("""
CREATE TABLE probe (
    unit_price INTEGER, quantity INTEGER,
    line_total INTEGER AS (unit_price * quantity) STORED CHECK (line_total >= 0)
)""")
        run(conn, "8-G. 그 CHECK 는 원본 컬럼을 넣을 때 검사된다", """
INSERT INTO probe (unit_price, quantity) VALUES (1000, -1)
""")
        conn.execute("DROP TABLE probe")

        run(conn, "9-A. 생성 컬럼 위의 인덱스 — STORED(order_month) 는 보통 인덱스", """
CREATE INDEX ix_order_item_order_month ON order_item (order_month)
""")
        run(conn, "9-B. VIRTUAL(line_total) 위의 인덱스는 식 인덱스로 저장된다", """
CREATE INDEX ix_order_item_line_total ON order_item (line_total)
""")
        run(conn, "9-C. sqlite_master 에 남는 정의", """
SELECT name, sql FROM sqlite_master WHERE type = 'index' AND tbl_name = 'order_item'
""")
        plan(conn, "10-A. STORED 컬럼 조건 — 인덱스를 탄다", """
SELECT product FROM order_item WHERE order_month = '2026-09'
""")
        plan(conn, "10-B. VIRTUAL 컬럼 조건 — 식 인덱스를 탄다", """
SELECT product FROM order_item WHERE line_total >= 50000
""")
        plan(conn, "10-C. 컬럼 이름 대신 같은 식을 직접 쓰면", """
SELECT product FROM order_item WHERE unit_price * quantity >= 50000
""")
        plan(conn, "10-D. 식의 순서를 바꾸면", """
SELECT product FROM order_item WHERE quantity * unit_price >= 50000
""")

        run(conn, "12-A. 생성 컬럼을 지우는 것은 된다 (SQLite 3.35.0+)", """
ALTER TABLE order_item DROP COLUMN unit_price_with_vat
""")
        run(conn, "12-B. 생성 컬럼이 참조하는 원본 컬럼은 지울 수 없다", """
ALTER TABLE order_item DROP COLUMN quantity
""")
        run(conn, "12-C. 인덱스가 걸린 생성 컬럼도 지울 수 없다", """
ALTER TABLE order_item DROP COLUMN order_month
""")
    finally:
        conn.close()

    bulk_compare()


if __name__ == "__main__":
    main()
