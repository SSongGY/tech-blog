"""GROUP BY 에 컬럼을 하나씩 더하거나 순서를 바꿔 가며 결과 행 수를 나란히 센다.

묶는 단위는 "컬럼 값의 조합" 이다. 그래서 컬럼을 더하면 행 수가 늘 수 있고,
순서를 바꾸는 것만으로는 조합이 바뀌지 않는다. 이것을 같은 데이터로 확인한다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

# 부산에는 키보드 판매가 없다. 그래서 지역 3 x 상품 3 = 9 가 아니라 8 조합만 생긴다.
# 대구 매장 1건은 channel 이 NULL 이다 (입력 누락).
SALES = [
    (1, "서울", "노트북", "온라인", 1200),
    (2, "서울", "노트북", "매장", 1100),
    (3, "서울", "모니터", "온라인", 300),
    (4, "서울", "키보드", "온라인", 50),
    (5, "부산", "노트북", "매장", 1150),
    (6, "부산", "모니터", "매장", 280),
    (7, "부산", "모니터", "온라인", 310),
    (8, "대구", "노트북", "온라인", 1250),
    (9, "대구", "모니터", "매장", 290),
    (10, "대구", "키보드", "매장", 45),
    (11, "대구", "키보드", None, 40),
    (12, "서울", "노트북", "온라인", 1180),
]


def build_database() -> sqlite3.Connection:
    # 같은 문장 텍스트를 캐시하면 인덱스를 지운 뒤에도 옛 계획이 보일 수 있다
    conn = sqlite3.connect(":memory:", cached_statements=0)
    conn.execute("""
CREATE TABLE sale (
    sale_id INTEGER PRIMARY KEY,
    region  TEXT    NOT NULL,
    product TEXT    NOT NULL,
    channel TEXT,
    amount  INTEGER NOT NULL
)
""")
    conn.executemany("INSERT INTO sale VALUES (?, ?, ?, ?, ?)", SALES)
    return conn


def run(conn: sqlite3.Connection, title: str, sql: str) -> None:
    print(f"\n-- {title}")
    for line in sql.strip().splitlines():
        print(f"   {line}")
    try:
        cursor = conn.execute(sql)
    except sqlite3.Error as exc:
        print(f"   에러: {exc}")
        return
    header = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    print("   => " + " | ".join(header))
    for row in rows:
        print("      " + " | ".join(str(v) for v in row))
    print(f"   ({len(rows)}행)")


def plan(conn: sqlite3.Connection, title: str, sql: str) -> None:
    """sqlite3 CLI 가 그리는 모양으로 EXPLAIN QUERY PLAN 을 찍는다."""
    print(f"\n-- {title}")
    print(f"   SQL : {sql}")
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


def main() -> None:
    conn = build_database()
    try:
        print_environment()
        print_dataset(conn)

        run(conn, "1. 한 컬럼으로 묶기 — region", """
SELECT region, COUNT(*) AS cnt, SUM(amount) AS total
FROM sale
GROUP BY region
ORDER BY region
""")

        run(conn, "2. 두 컬럼으로 묶기 — region, product", """
SELECT region, product, COUNT(*) AS cnt, SUM(amount) AS total
FROM sale
GROUP BY region, product
ORDER BY region, product
""")

        run(conn, "3. 순서만 바꾸기 — product, region", """
SELECT product, region, COUNT(*) AS cnt, SUM(amount) AS total
FROM sale
GROUP BY product, region
ORDER BY product, region
""")

        # 그룹 수는 서로 다른 조합의 수다. 곱이 아니다
        run(conn, "4. 그룹 수와 고유값 개수 비교", """
SELECT COUNT(DISTINCT region)  AS regions,
       COUNT(DISTINCT product) AS products,
       (SELECT COUNT(*) FROM (SELECT 1 FROM sale GROUP BY region, product))
                               AS region_product_groups,
       (SELECT COUNT(*) FROM (SELECT 1 FROM sale GROUP BY product, region))
                               AS product_region_groups
FROM sale
""")

        run(conn, "5. 세 컬럼 — region, product, channel", """
SELECT region, product, channel, COUNT(*) AS cnt, SUM(amount) AS total
FROM sale
GROUP BY region, product, channel
ORDER BY region, product, channel
""")

        run(conn, "6. 묶는 컬럼별 그룹 수", """
SELECT 'region'                   AS group_columns, COUNT(*) AS groups
  FROM (SELECT 1 FROM sale GROUP BY region)
UNION ALL
SELECT 'region, product',          COUNT(*)
  FROM (SELECT 1 FROM sale GROUP BY region, product)
UNION ALL
SELECT 'region, product, channel', COUNT(*)
  FROM (SELECT 1 FROM sale GROUP BY region, product, channel)
UNION ALL
SELECT 'sale_id',                  COUNT(*)
  FROM (SELECT 1 FROM sale GROUP BY sale_id)
""")

        # 상위 단위 합계는 하위 단위 합계를 다시 더한 것과 같아야 한다
        run(conn, "7. 두 단계 집계 — region, product 합계를 region 으로 다시 묶기", """
SELECT region, SUM(total) AS total, COUNT(*) AS product_groups
FROM (SELECT region, product, SUM(amount) AS total
      FROM sale
      GROUP BY region, product)
GROUP BY region
ORDER BY region
""")

        run(conn, "8. 묶지 않은 컬럼을 SELECT 에 두면 — product 를 빼고 묶었는데 product 를 찍는다", """
SELECT region, product, SUM(amount) AS total
FROM sale
GROUP BY region
ORDER BY region
""")

        run(conn, "9. ORDER BY 없이 순서를 바꿔 묶으면 결과 순서는", """
SELECT product, region, COUNT(*) AS cnt
FROM sale
GROUP BY product, region
""")

        plan(conn, "10. 인덱스 없을 때 계획", "SELECT region, product, COUNT(*) FROM sale GROUP BY region, product")

        conn.execute("CREATE INDEX ix_sale_region_product ON sale (region, product)")
        plan(conn, "11. 인덱스 (region, product) 를 만든 뒤 — 같은 순서",
             "SELECT region, product, COUNT(*) FROM sale GROUP BY region, product")
        plan(conn, "12. 인덱스 (region, product) 를 만든 뒤 — 순서를 바꿔서",
             "SELECT product, region, COUNT(*) FROM sale GROUP BY product, region")
        plan(conn, "13. 인덱스 (region, product) 를 만든 뒤 — product 하나로",
             "SELECT product, COUNT(*) FROM sale GROUP BY product")

        run(conn, "14. 순서를 바꿔 묶고 인덱스가 있을 때 ORDER BY 없이 나온 순서", """
SELECT product, region, COUNT(*) AS cnt
FROM sale
GROUP BY product, region
""")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
