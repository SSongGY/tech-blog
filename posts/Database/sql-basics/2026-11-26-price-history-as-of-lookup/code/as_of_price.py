"""가격 이력 표에서 주문일에 적용되던 가격을 찾는다.

1) 흔한 실수 — 지금 가격을 과거 주문에 곱한다
2) 방법 A: 상관 부질의 (ORDER BY valid_from DESC LIMIT 1)
3) 방법 B: LEAD 로 끝 날짜를 만들어 구간 조인
4) 방법 C: 주문일 이전 가격을 전부 붙인 뒤 ROW_NUMBER 로 최신 1건
5) 이력이 시작되기 전의 주문 — 세 방법이 갈린다
6) 구간 양 끝을 BETWEEN 으로 닫으면 가격이 바뀐 날 주문이 두 줄이 된다
7) 실행계획
8) 행 수를 늘려 걸린 시간을 잰다
"""
import random
import sqlite3
import time

from dbshow import print_dataset, print_environment


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE price_history (
            product_id TEXT    NOT NULL,
            valid_from TEXT    NOT NULL,     -- 이 날부터 적용 (끝 날짜는 저장하지 않는다)
            price      INTEGER NOT NULL,
            PRIMARY KEY (product_id, valid_from)
        ) WITHOUT ROWID;
        INSERT INTO price_history VALUES
            ('P01', '2026-01-01', 1000), ('P01', '2026-03-01', 1200),
            ('P01', '2026-06-01', 1100),
            ('P02', '2026-02-01', 5000), ('P02', '2026-05-01', 5500);

        CREATE TABLE orders (
            order_id   INTEGER PRIMARY KEY,
            product_id TEXT    NOT NULL,
            order_date TEXT    NOT NULL,
            qty        INTEGER NOT NULL
        );
        INSERT INTO orders VALUES
            (1, 'P01', '2026-01-15', 2),   -- 1000 원 구간
            (2, 'P01', '2026-03-01', 1),   -- 가격이 바뀐 바로 그날
            (3, 'P01', '2026-05-31', 3),   -- 다음 가격 하루 전
            (4, 'P01', '2026-07-10', 1),   -- 마지막 가격 구간
            (5, 'P02', '2026-01-20', 1),   -- P02 이력이 시작되기 전
            (6, 'P02', '2026-05-01', 2);
        """
    )
    return conn


def show_rows(conn, sql):
    print("  sql> " + " ".join(sql.split())[:170] + " ...")
    cursor = conn.execute(sql)
    print("   ", tuple(d[0] for d in cursor.description))
    for row in cursor:
        print("   ", row)


def show_plan(conn, sql):
    """sqlite3 CLI 가 그리는 것과 같은 모양의 트리로 EXPLAIN QUERY PLAN 을 찍는다."""
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    children = {}
    for node_id, parent, _, detail in rows:
        children.setdefault(parent, []).append((node_id, detail))

    def walk(parent, prefix):
        nodes = children.get(parent, [])
        for i, (node_id, detail) in enumerate(nodes):
            last = i == len(nodes) - 1
            print("    " + prefix + ("`--" if last else "|--") + detail)
            walk(node_id, prefix + ("   " if last else "|  "))

    print("    QUERY PLAN")
    walk(0, "")


SQL_SUBQUERY = """
    SELECT o.order_id, o.product_id, o.order_date, o.qty,
           (SELECT p.price FROM price_history p
            WHERE p.product_id = o.product_id
              AND p.valid_from <= o.order_date
            ORDER BY p.valid_from DESC LIMIT 1) AS price
    FROM orders o ORDER BY o.order_id"""

SQL_INTERVAL = """
    WITH price_range AS (
        SELECT product_id, valid_from, price,
               LEAD(valid_from) OVER (PARTITION BY product_id
                                      ORDER BY valid_from) AS valid_to
        FROM price_history)
    SELECT o.order_id, o.product_id, o.order_date, o.qty, r.price
    FROM orders o
    JOIN price_range r
      ON r.product_id = o.product_id
     AND o.order_date >= r.valid_from
     AND (r.valid_to IS NULL OR o.order_date < r.valid_to)
    ORDER BY o.order_id"""

SQL_ROW_NUMBER = """
    SELECT order_id, product_id, order_date, qty, price
    FROM (SELECT o.order_id, o.product_id, o.order_date, o.qty, p.price,
                 ROW_NUMBER() OVER (PARTITION BY o.order_id
                                    ORDER BY p.valid_from DESC) AS rn
          FROM orders o
          JOIN price_history p
            ON p.product_id = o.product_id
           AND p.valid_from <= o.order_date)
    WHERE rn = 1 ORDER BY order_id"""


def build_large(product_count, changes_per_product, order_count):
    """같은 구조에 행만 늘린 DB. 난수 시드를 고정해 매번 같은 데이터가 나온다."""
    rng = random.Random(20261126)
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE price_history (
            product_id TEXT NOT NULL, valid_from TEXT NOT NULL, price INTEGER NOT NULL,
            PRIMARY KEY (product_id, valid_from)) WITHOUT ROWID;
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY, product_id TEXT NOT NULL,
            order_date TEXT NOT NULL, qty INTEGER NOT NULL);
        """
    )
    days = [f"2026-{m:02d}-{d:02d}" for m in range(1, 13) for d in range(1, 29)]
    for n in range(product_count):
        product_id = f"P{n:04d}"
        change_days = sorted(rng.sample(days[1:], changes_per_product - 1))
        for day in [days[0]] + change_days:
            conn.execute("INSERT INTO price_history VALUES (?, ?, ?)",
                         (product_id, day, rng.randrange(1000, 9000, 100)))
    for order_id in range(1, order_count + 1):
        conn.execute("INSERT INTO orders VALUES (?, ?, ?, ?)",
                     (order_id, f"P{rng.randrange(product_count):04d}",
                      rng.choice(days), rng.randint(1, 5)))
    conn.commit()
    return conn


def timed(conn, sql):
    best = None
    rows = None
    for _ in range(3):
        started = time.perf_counter()
        rows = conn.execute(sql).fetchall()
        elapsed = time.perf_counter() - started
        best = elapsed if best is None else min(best, elapsed)
    return best, rows


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("\n[1] 흔한 실수 — 상품별 최신 가격을 모든 주문에 곱한다")
    show_rows(conn, """
        SELECT o.order_id, o.product_id, o.order_date, o.qty, c.price,
               o.qty * c.price AS amount
        FROM orders o
        JOIN (SELECT product_id, price, MAX(valid_from) AS valid_from
              FROM price_history GROUP BY product_id) c
          ON c.product_id = o.product_id
        ORDER BY o.order_id""")

    print("\n[2] 방법 A — 상관 부질의: 주문일 이전 가격 중 가장 늦은 1건")
    show_rows(conn, SQL_SUBQUERY)

    print("\n[3] 방법 B — LEAD 로 끝 날짜를 만든다")
    show_rows(conn, """
        SELECT product_id, valid_from, price,
               LEAD(valid_from) OVER (PARTITION BY product_id
                                      ORDER BY valid_from) AS valid_to
        FROM price_history ORDER BY product_id, valid_from""")
    print("[3-1] 그 구간에 주문일을 넣어 조인 — 시작은 포함, 끝은 제외")
    show_rows(conn, SQL_INTERVAL)

    print("\n[4] 방법 C — 주문일 이전 가격을 전부 붙이고 ROW_NUMBER 로 1건")
    show_rows(conn, SQL_ROW_NUMBER)

    print("\n[5] 이력 시작 전 주문(order_id 5) — 방법별 결과 행 수")
    for name, sql in (("A 상관 부질의", SQL_SUBQUERY), ("B 구간 조인", SQL_INTERVAL),
                      ("C ROW_NUMBER", SQL_ROW_NUMBER)):
        rows = conn.execute(sql).fetchall()
        ids = [row[0] for row in rows]
        print(f"    {name:<14} {len(rows)}행  order_id={ids}")
    print("[5-1] 방법 B 를 LEFT JOIN 으로 바꾸면 주문 5 가 price NULL 로 남는다")
    show_rows(conn, SQL_INTERVAL.replace("JOIN price_range", "LEFT JOIN price_range"))

    print("\n[6] 양 끝을 BETWEEN 으로 닫으면 — 가격이 바뀐 날의 주문 2·6 이 두 줄")
    show_rows(conn, """
        WITH price_range AS (
            SELECT product_id, valid_from, price,
                   LEAD(valid_from) OVER (PARTITION BY product_id
                                          ORDER BY valid_from) AS valid_to
            FROM price_history)
        SELECT o.order_id, o.order_date, r.valid_from, r.valid_to, r.price
        FROM orders o
        JOIN price_range r
          ON r.product_id = o.product_id
         AND o.order_date BETWEEN r.valid_from AND COALESCE(r.valid_to, '9999-12-31')
        ORDER BY o.order_id, r.valid_from""")

    print("\n[7] 실행계획")
    for name, sql in (("A 상관 부질의", SQL_SUBQUERY), ("B 구간 조인", SQL_INTERVAL),
                      ("C ROW_NUMBER", SQL_ROW_NUMBER)):
        print(f"  -- {name}")
        show_plan(conn, sql)
    conn.close()

    print("\n[8] 행을 늘려 잰다 — 상품 200개, 주문 20,000건, 3회 중 가장 빠른 값")
    print("    ", ("changes_per_product", "method", "rows", "seconds"))
    for changes in (5, 50, 300):
        large = build_large(200, changes, 20000)
        results = {}
        for name, sql in (("A", SQL_SUBQUERY), ("B", SQL_INTERVAL), ("C", SQL_ROW_NUMBER)):
            seconds, rows = timed(large, sql)
            results[name] = rows
            print("    ", (changes, name, len(rows), round(seconds, 3)))
        same = results["A"] == results["B"] == results["C"]
        print(f"     가격 이력 {200 * changes}행 — 세 방법의 결과가 같은가: {same}")
        large.close()


if __name__ == "__main__":
    main()
