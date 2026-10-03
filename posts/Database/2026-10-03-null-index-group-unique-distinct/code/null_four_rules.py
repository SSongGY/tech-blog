"""NULL이 비교·묶기·UNIQUE·집계·인덱스에서 각각 어떻게 다뤄지는지 같은 표 하나로 확인한다.

주문 표의 쿠폰 코드(coupon_code)는 대부분 비어 있다. 같은 NULL 두 개를
비교하면 '알 수 없음', GROUP BY 하면 '같은 값', UNIQUE 에서는 '다른 값'이 된다.
마지막에는 NULL 이 90% 인 컬럼에 일반 인덱스와 부분 인덱스를 걸어 크기를 잰다.
"""

import os
import random
import sqlite3
import tempfile

from dbshow import print_dataset, print_environment

ORDERS = [
    # (id, 고객 id, 쿠폰 코드, 금액)
    (1, 10, "WELCOME", 12000),
    (2, 11, None, 8000),
    (3, 10, None, 15000),
    (4, 12, "WELCOME", 9000),
    (5, 13, "VIP", 30000),
    (6, 11, None, None),
]

BULK_ROWS = 200_000
NULL_RATIO = 0.9
SEED = 20261003


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE orders (
            id           INTEGER PRIMARY KEY,
            customer_id  INTEGER NOT NULL,
            coupon_code  TEXT,
            amount       INTEGER
        );
        CREATE TABLE coupon_use (
            coupon_code  TEXT UNIQUE,
            note         TEXT
        );
        """
    )
    conn.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", ORDERS)
    conn.commit()
    return conn


def query(conn: sqlite3.Connection, label: str, sql: str) -> None:
    print(f"\n[{label}]")
    print(f"  {' '.join(sql.split())}")
    cur = conn.execute(sql)
    print(f"  {tuple(col[0] for col in cur.description)}")
    for row in cur.fetchall():
        print(f"  {row}")


def plan(conn: sqlite3.Connection, label: str, sql: str) -> None:
    """sqlite3 CLI 가 그리는 트리 모양 그대로 찍는다 (id/parent 로 들여쓰기)."""
    print(f"\n[{label}]")
    print(f"  {' '.join(sql.split())}")
    rows = conn.execute(f"EXPLAIN QUERY PLAN {sql}").fetchall()
    depth = {0: -1}
    print("  QUERY PLAN")
    for i, (node_id, parent, _, detail) in enumerate(rows):
        depth[node_id] = depth.get(parent, -1) + 1
        is_last = all(r[1] != parent for r in rows[i + 1:])
        branch = "`--" if is_last else "|--"
        print(f"  {'   ' * depth[node_id]}{branch}{detail}")


def compare_section(conn: sqlite3.Connection) -> None:
    print("\n== 1. 비교: NULL 끼리도 같은지 모른다 ==")
    query(conn, "1-A = 로 찾으면 0행", "SELECT id FROM orders WHERE coupon_code = NULL")
    query(conn, "1-B IS 로 찾으면 3행", "SELECT id FROM orders WHERE coupon_code IS NULL")
    query(
        conn,
        "1-C 자기 자신과 조인해도 NULL 행끼리는 짝이 안 된다",
        """SELECT a.coupon_code, COUNT(*) AS pairs
           FROM orders a JOIN orders b ON a.coupon_code = b.coupon_code
           GROUP BY a.coupon_code ORDER BY a.coupon_code""",
    )


def group_section(conn: sqlite3.Connection) -> None:
    print("\n== 2. 묶기: GROUP BY·DISTINCT·UNION 은 NULL 을 한 덩어리로 본다 ==")
    query(
        conn,
        "2-A GROUP BY",
        "SELECT coupon_code, COUNT(*) AS cnt FROM orders GROUP BY coupon_code",
    )
    query(conn, "2-B DISTINCT", "SELECT DISTINCT coupon_code FROM orders")
    query(
        conn,
        "2-C UNION 은 중복을 지운다",
        "SELECT coupon_code FROM orders WHERE id = 2 UNION SELECT coupon_code FROM orders WHERE id = 3",
    )
    query(
        conn,
        "2-D ORDER BY: NULL 은 맨 앞, NULLS LAST 로 뒤로 보낸다",
        """SELECT group_concat(quote(coupon_code), ' ') AS asc_default
           FROM (SELECT coupon_code FROM orders ORDER BY coupon_code)""",
    )
    query(
        conn,
        "2-E",
        """SELECT group_concat(quote(coupon_code), ' ') AS asc_nulls_last
           FROM (SELECT coupon_code FROM orders ORDER BY coupon_code NULLS LAST)""",
    )


def unique_section(conn: sqlite3.Connection) -> None:
    print("\n== 3. UNIQUE: NULL 은 서로 다른 값이다 ==")
    for code in ("WELCOME", "WELCOME", None, None, None):
        try:
            conn.execute("INSERT INTO coupon_use (coupon_code) VALUES (?)", (code,))
            print(f"  INSERT {code!r:10} -> 성공")
        except sqlite3.IntegrityError as exc:
            print(f"  INSERT {code!r:10} -> 에러: {exc}")
    query(
        conn,
        "3-A 같은 표를 DISTINCT 로 보면 NULL 은 하나",
        "SELECT COUNT(*) AS total_rows, COUNT(DISTINCT coupon_code) AS distinct_non_null, "
        "(SELECT COUNT(*) FROM (SELECT DISTINCT coupon_code FROM coupon_use)) AS distinct_rows "
        "FROM coupon_use",
    )


def aggregate_section(conn: sqlite3.Connection) -> None:
    print("\n== 4. 집계: NULL 을 건너뛴다 ==")
    query(
        conn,
        "4-A 6번 주문의 금액이 NULL",
        """SELECT COUNT(*) AS cnt_star, COUNT(amount) AS cnt_amount,
                  SUM(amount) AS sum_amount, AVG(amount) AS avg_amount,
                  MIN(amount) AS min_amount
           FROM orders""",
    )
    query(
        conn,
        "4-B 모든 값이 NULL 이면 SUM 은 NULL, total 은 0.0",
        """SELECT SUM(amount) AS sum_amount, total(amount) AS total_amount, COUNT(amount) AS cnt
           FROM orders WHERE id = 6""",
    )


def index_section() -> None:
    print("\n== 5. 인덱스: NULL 도 인덱스에 들어가고, IS NULL 로 찾을 수 있다 ==")
    rng = random.Random(SEED)
    rows = [
        (i, None if rng.random() < NULL_RATIO else f"C{rng.randrange(5000):04d}")
        for i in range(1, BULK_ROWS + 1)
    ]
    sizes = {}
    with tempfile.TemporaryDirectory() as tmp:
        for kind, ddl in (
            ("none", None),
            ("full", "CREATE INDEX ix_coupon ON orders (coupon_code)"),
            ("partial", "CREATE INDEX ix_coupon ON orders (coupon_code) WHERE coupon_code IS NOT NULL"),
        ):
            path = os.path.join(tmp, f"{kind}.db")
            conn = sqlite3.connect(path)
            conn.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, coupon_code TEXT)")
            conn.executemany("INSERT INTO orders VALUES (?, ?)", rows)
            if ddl:
                conn.execute(ddl)
            conn.commit()
            conn.execute("VACUUM")
            sizes[kind] = conn.execute("PRAGMA page_count").fetchone()[0]
            page_size = conn.execute("PRAGMA page_size").fetchone()[0]
            if kind == "full":
                nulls = conn.execute("SELECT COUNT(*) FROM orders WHERE coupon_code IS NULL").fetchone()[0]
                print(f"  행 {BULK_ROWS:,}개 중 coupon_code 가 NULL 인 행: {nulls:,}")
                plan(conn, "5-A 일반 인덱스 · IS NULL", "SELECT id FROM orders WHERE coupon_code IS NULL")
                plan(conn, "5-B 일반 인덱스 · = 값", "SELECT id FROM orders WHERE coupon_code = 'C0042'")
                plan(conn, "5-C 일반 인덱스 · MIN", "SELECT MIN(coupon_code) FROM orders")
            if kind == "partial":
                plan(conn, "5-D 부분 인덱스 · = 값", "SELECT id FROM orders WHERE coupon_code = 'C0042'")
                plan(conn, "5-E 부분 인덱스 · IS NULL", "SELECT id FROM orders WHERE coupon_code IS NULL")
                forced = "SELECT id FROM orders INDEXED BY ix_coupon WHERE coupon_code IS NULL"
                print(f"\n[5-G 부분 인덱스를 강제하면]\n  {forced}")
                try:
                    conn.execute(forced).fetchone()
                    print("  -> 실행됨")
                except sqlite3.Error as exc:
                    print(f"  -> {type(exc).__name__}: {exc}")
            conn.close()

    print(f"\n[5-F 파일 크기 — VACUUM 뒤 page_count, 페이지 {page_size}바이트]")
    for kind, label in (("none", "인덱스 없음"), ("full", "일반 인덱스"), ("partial", "부분 인덱스 (IS NOT NULL)")):
        extra = sizes[kind] - sizes["none"]
        print(f"  {label:24} {sizes[kind]:5} 페이지   인덱스 몫 {extra:4} 페이지 ({extra * page_size / 1024:,.0f} KiB)")


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)
    compare_section(conn)
    group_section(conn)
    unique_section(conn)
    aggregate_section(conn)
    index_section()


if __name__ == "__main__":
    main()
