"""중첩 서브쿼리를 WITH 절(CTE)로 펴 보고, 펴서 얻는 것과 잃는 것을 실행으로 확인한다.

얻는 것: 같은 중간 결과를 이름 하나로 두 번 쓴다, 위에서 아래로 읽힌다.
잃는 것: MATERIALIZED 로 굳히면 바깥 WHERE 가 안쪽 인덱스까지 내려가지 못한다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

SALES = [
    (1, "김하나", "서울", 300),
    (2, "이두리", "서울", 250),
    (3, "박세나", "서울", 150),
    (4, "최네오", "부산", 400),
    (5, "정다섯", "부산", 100),
    (6, "한여섯", "대구", 120),
    (7, "윤일곱", "대구", 80),
    (8, "조여덟", "광주", 500),
]


def build_database() -> sqlite3.Connection:
    # 같은 문장 텍스트를 캐시하면 앞 실행의 계획이 섞일 수 있어 캐시를 끈다
    conn = sqlite3.connect(":memory:", cached_statements=0)
    conn.execute("""
CREATE TABLE sales (
    sale_id   INTEGER PRIMARY KEY,
    seller    TEXT    NOT NULL,
    region    TEXT    NOT NULL,
    amount    INTEGER NOT NULL
)
""")
    conn.execute("CREATE INDEX idx_sales_region ON sales (region)")
    conn.executemany("INSERT INTO sales VALUES (?, ?, ?, ?)", SALES)
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
    """sqlite3 CLI 가 그리는 모양으로 EXPLAIN QUERY PLAN 을 찍고, 실제로 돈 VDBE 명령 수를 센다."""
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

    # 비용을 찍지 않는 SQLite 에서 실제로 한 일의 양을 비교하려고 명령 수를 센다
    steps = 0

    def count_step() -> int:
        nonlocal steps
        steps += 1
        return 0

    conn.set_progress_handler(count_step, 1)
    try:
        result = conn.execute(sql).fetchall()
    finally:
        conn.set_progress_handler(None, 1)
    print(f"   결과 {result} / VDBE 명령 {steps}개")


REGION_TOTAL = "SELECT region, SUM(amount) AS total FROM sales GROUP BY region"


def main() -> None:
    conn = build_database()
    try:
        print_environment()
        print_dataset(conn)

        run(conn, "1. 지역별 합계 — 모든 질의의 재료", REGION_TOTAL + " ORDER BY region")

        # 같은 집계가 FROM 과 WHERE 안 스칼라 서브쿼리에 두 번 들어간다
        run(conn, "2. 중첩 서브쿼리 — 평균 지역 합계보다 많이 판 지역", f"""
SELECT region, total
FROM ({REGION_TOTAL})
WHERE total > (SELECT AVG(total)
               FROM ({REGION_TOTAL}))
ORDER BY total DESC
""")

        run(conn, "3. 같은 질의를 CTE 로 — 집계는 한 번만 적는다", f"""
WITH region_total AS (
    {REGION_TOTAL}
)
SELECT region, total
FROM region_total
WHERE total > (SELECT AVG(total) FROM region_total)
ORDER BY total DESC
""")

        run(conn, "4. CTE 를 이어 쓰기 — 뒤의 CTE 가 앞의 CTE 를 읽는다", f"""
WITH region_total AS (
    {REGION_TOTAL}
),
avg_total AS (
    SELECT AVG(total) AS avg_value FROM region_total
)
SELECT r.region, r.total, a.avg_value
FROM region_total AS r, avg_total AS a
WHERE r.total > a.avg_value
ORDER BY r.total DESC
""")

        run(conn, "5. 컬럼 이름 목록 — CTE 이름 뒤에 괄호로 붙인다", """
WITH region_total (region_name, sum_amount, seller_count) AS (
    SELECT region, SUM(amount), COUNT(*) FROM sales GROUP BY region
)
SELECT region_name, sum_amount, seller_count
FROM region_total
ORDER BY sum_amount DESC
""")

        run(conn, "6. 중간 단계만 떼어 보기 — 마지막 SELECT 만 바꾼다", f"""
WITH region_total AS (
    {REGION_TOTAL}
),
avg_total AS (
    SELECT AVG(total) AS avg_value FROM region_total
)
SELECT avg_value FROM avg_total
""")

        run(conn, "7. CTE 는 그 문장 안에서만 산다 — 다음 문장에서 부르면", """
SELECT * FROM region_total
""")

        # 실제 테이블과 같은 이름을 붙이면 이 문장 안에서는 CTE 가 테이블을 가린다
        run(conn, "8. 테이블과 같은 이름의 CTE", """
WITH sales AS (
    SELECT 99 AS sale_id, '가짜' AS seller, '서울' AS region, 1 AS amount
)
SELECT COUNT(*) AS row_count, SUM(amount) AS total FROM sales
""")

        run(conn, "9. 선언한 컬럼 수와 SELECT 컬럼 수가 다르면", """
WITH region_total (region_name, sum_amount) AS (
    SELECT region, SUM(amount), COUNT(*) FROM sales GROUP BY region
)
SELECT * FROM region_total
""")

        seoul_sql = """
WITH all_sales AS {hint}(
    SELECT seller, region, amount FROM sales
)
SELECT SUM(amount) FROM all_sales WHERE region = '서울'
"""
        plan(conn, "10. 힌트 없음 — 바깥 WHERE 가 안으로 들어가는지", seoul_sql.format(hint=""))
        plan(conn, "11. MATERIALIZED — CTE 를 먼저 통째로 만든다", seoul_sql.format(hint="MATERIALIZED "))

        plan(conn, "12. 두 번 쓰는 CTE — 힌트 없음", f"""
WITH region_total AS (
    {REGION_TOTAL}
)
SELECT COUNT(*) FROM region_total
WHERE total > (SELECT AVG(total) FROM region_total)
""")
        plan(conn, "13. 중첩 서브쿼리 — 2번과 같은 질의의 계획", f"""
SELECT COUNT(*) FROM ({REGION_TOTAL})
WHERE total > (SELECT AVG(total) FROM ({REGION_TOTAL}))
""")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
