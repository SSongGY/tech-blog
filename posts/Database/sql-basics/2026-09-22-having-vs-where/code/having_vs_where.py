"""WHERE와 HAVING이 질의 처리의 어느 단계에서 작용하는지 확인한다.

SQLite 내장 모듈만 쓴다. 외부 의존성 없음.
"""

import sqlite3

SCHEMA = """
CREATE TABLE sale (
    id          INTEGER PRIMARY KEY,
    region      TEXT    NOT NULL,
    channel     TEXT    NOT NULL,
    amount      INTEGER
);
"""

ROWS = [
    (1, "서울", "온라인", 120),
    (2, "서울", "오프라인", 80),
    (3, "서울", "온라인", 200),
    (4, "부산", "온라인", 150),
    (5, "부산", "오프라인", 90),
    (6, "대구", "온라인", 300),
    (7, "대구", "온라인", None),
    (8, "광주", "오프라인", 50),
]


def show(conn, label, sql):
    """질의 하나를 돌려 결과를 라벨과 함께 찍는다. 에러도 그대로 보여준다."""
    print(f"\n--- {label}")
    print(sql.strip())
    try:
        rows = conn.execute(sql).fetchall()
    except sqlite3.Error as exc:
        print(f"  [에러] {type(exc).__name__}: {exc}")
        return
    for row in rows:
        print("  ", row)
    if not rows:
        print("   (0건)")


def main():
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO sale VALUES (?, ?, ?, ?)", ROWS)

    print(f"sqlite3.sqlite_version = {sqlite3.sqlite_version}")

    show(conn, "1. 그룹 전체", """
SELECT region, COUNT(*) AS cnt, SUM(amount) AS total
FROM sale
GROUP BY region
ORDER BY region
""")

    show(conn, "2. WHERE — 그룹을 만들기 전에 행을 버린다", """
SELECT region, COUNT(*) AS cnt, SUM(amount) AS total
FROM sale
WHERE channel = '온라인'
GROUP BY region
ORDER BY region
""")

    show(conn, "3. HAVING — 그룹을 만든 뒤 그룹을 버린다", """
SELECT region, COUNT(*) AS cnt, SUM(amount) AS total
FROM sale
GROUP BY region
HAVING COUNT(*) >= 2
ORDER BY region
""")

    show(conn, "4. WHERE에 집계 함수를 쓰면", """
SELECT region, COUNT(*) AS cnt
FROM sale
WHERE COUNT(*) >= 2
GROUP BY region
""")

    show(conn, "5. GROUP BY 없는 HAVING — 테이블 전체가 한 그룹", """
SELECT COUNT(*) AS cnt, SUM(amount) AS total
FROM sale
HAVING SUM(amount) > 100
""")

    show(conn, "6. GROUP BY 없는 HAVING — 조건이 거짓이면", """
SELECT COUNT(*) AS cnt, SUM(amount) AS total
FROM sale
HAVING SUM(amount) > 100000
""")

    show(conn, "7. SELECT 별칭을 WHERE에서 참조", """
SELECT region, amount AS won
FROM sale
WHERE won > 250
""")

    show(conn, "8. SELECT 별칭을 HAVING에서 참조", """
SELECT region, SUM(amount) AS total
FROM sale
GROUP BY region
HAVING total > 250
ORDER BY region
""")

    show(conn, "9. 집계 함수는 NULL을 세지 않는다", """
SELECT region,
       COUNT(*)      AS cnt_all,
       COUNT(amount) AS cnt_amount,
       SUM(amount)   AS total,
       AVG(amount)   AS avg_amount
FROM sale
WHERE region = '대구'
GROUP BY region
""")

    show(conn, "10. HAVING에 집계가 아닌 조건 — 실행은 된다", """
SELECT region, COUNT(*) AS cnt
FROM sale
GROUP BY region
HAVING region <> '서울'
ORDER BY region
""")

    show(conn, "11. 그룹 안에서 값이 갈리는 컬럼을 HAVING에 쓰면", """
SELECT region, COUNT(*) AS cnt, GROUP_CONCAT(channel) AS channels
FROM sale
GROUP BY region
HAVING channel = '온라인'
ORDER BY region
""")

    # 인덱스를 만들어야 WHERE와 HAVING의 실행계획 차이가 드러난다.
    conn.execute("CREATE INDEX ix_sale_region ON sale(region)")
    conn.execute("ANALYZE")

    for label, sql in [
        ("12-A. WHERE region = '서울'",
         "SELECT region, COUNT(*) FROM sale WHERE region = '서울' GROUP BY region"),
        ("12-B. HAVING region = '서울'",
         "SELECT region, COUNT(*) FROM sale GROUP BY region HAVING region = '서울'"),
    ]:
        print(f"\n--- {label}")
        print(sql)
        print("QUERY PLAN")
        for _, _, _, detail in conn.execute("EXPLAIN QUERY PLAN " + sql):
            print(f"`--{detail}")

    conn.close()


if __name__ == "__main__":
    main()
