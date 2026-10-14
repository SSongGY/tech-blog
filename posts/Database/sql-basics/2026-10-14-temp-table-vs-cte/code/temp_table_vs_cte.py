"""CTE·서브쿼리·임시 테이블이 각각 몸체를 몇 번 도는지 센다.

집계 함수 자리에 tally() 를 끼워 넣어, 그 자리를 지나간 행 수를 직접 센다.
EXPLAIN QUERY PLAN 이 CO-ROUTINE 이라고 말하는지 MATERIALIZE 라고 말하는지와
실제 호출 횟수를 나란히 본다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

SCHEMA = """
CREATE TABLE sale (
    sale_id INTEGER PRIMARY KEY,
    region  TEXT    NOT NULL,
    sold_on TEXT    NOT NULL,
    amount  INTEGER NOT NULL
);
"""

REGIONS = ["서울", "부산", "대구", "광주"]
ROW_COUNT = 240

# tally() 호출 횟수. SQL 안에서 셀 방법이 없어 파이썬 쪽에 둔다.
counter = {"calls": 0}


def tally(value: int) -> int:
    counter["calls"] += 1
    return value


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    rows = [
        (
            i,
            REGIONS[i % len(REGIONS)],
            f"2026-{(i % 6) + 1:02d}-10",
            1000 + (i * 37) % 900,
        )
        for i in range(1, ROW_COUNT + 1)
    ]
    conn.executemany("INSERT INTO sale VALUES (?, ?, ?, ?)", rows)
    conn.commit()
    conn.create_function("tally", 1, tally)
    return conn


def run(conn: sqlite3.Connection, label: str, sql: str) -> None:
    """질의를 돌려 tally() 호출 수를 세고, 그 질의의 실행계획을 그대로 찍는다."""
    counter["calls"] = 0
    rows = conn.execute(sql).fetchall()
    calls = counter["calls"]
    print(f"[{label}]")
    print(f"  tally() 호출 {calls}회 · 결과 {len(rows)}행")
    print("  QUERY PLAN")
    for _, _, _, detail in conn.execute("EXPLAIN QUERY PLAN " + sql):
        print(f"  |--{detail}")
    print()


AGGREGATE_BODY = "SELECT region, SUM(tally(amount)) AS total FROM sale GROUP BY region"

ONCE = f"""
WITH region_total AS ({AGGREGATE_BODY})
SELECT region, total FROM region_total ORDER BY region
"""

TWICE = """
WITH region_total AS ({body})
SELECT a.region, a.total AS 지역합, b.total AS 서울합
  FROM region_total a JOIN region_total b ON b.region = '서울'
 ORDER BY a.region
"""

SUBQUERY_TWICE = f"""
SELECT a.region, a.total AS 지역합, b.total AS 서울합
  FROM ({AGGREGATE_BODY}) a
  JOIN ({AGGREGATE_BODY}) b ON b.region = '서울'
 ORDER BY a.region
"""

# 집계가 없는 CTE. 힌트가 실제로 먹는지 보려고 따로 둔다.
PLAIN_BODY = "SELECT sale_id, region, tally(amount) AS amount FROM sale WHERE amount > 1400"

PLAIN_TWICE = """
WITH big AS ({body})
SELECT (SELECT COUNT(*) FROM big) AS 건수,
       (SELECT MAX(amount) FROM big) AS 최대액
"""


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)
    print()

    run(conn, "CTE 를 한 번만 참조", ONCE)
    run(conn, "CTE 를 두 번 참조 (힌트 없음)", TWICE.format(body=AGGREGATE_BODY))
    run(
        conn,
        "CTE 를 두 번 참조 (NOT MATERIALIZED)",
        TWICE.format(body=AGGREGATE_BODY).replace(
            "region_total AS (", "region_total AS NOT MATERIALIZED (", 1
        ),
    )
    run(
        conn,
        "CTE 를 두 번 참조 (MATERIALIZED)",
        TWICE.format(body=AGGREGATE_BODY).replace(
            "region_total AS (", "region_total AS MATERIALIZED (", 1
        ),
    )
    run(conn, "같은 서브쿼리를 두 번 적음", SUBQUERY_TWICE)
    run(
        conn,
        "같은 서브쿼리를 두 번 적음 (상수 조건 없음)",
        SUBQUERY_TWICE.replace("b.region = '서울'", "b.region = a.region"),
    )

    run(conn, "집계 없는 CTE 를 두 번 참조 (힌트 없음)", PLAIN_TWICE.format(body=PLAIN_BODY))
    run(
        conn,
        "집계 없는 CTE 를 두 번 참조 (NOT MATERIALIZED)",
        PLAIN_TWICE.format(body=PLAIN_BODY).replace(
            "big AS (", "big AS NOT MATERIALIZED (", 1
        ),
    )

    counter["calls"] = 0
    conn.execute(f"CREATE TEMP TABLE region_total AS {AGGREGATE_BODY}")
    print(f"[TEMP TABLE 생성] tally() 호출 {counter['calls']}회")
    print()
    run(
        conn,
        "TEMP TABLE 을 두 번 참조",
        """
SELECT a.region, a.total AS 지역합, b.total AS 서울합
  FROM region_total a JOIN region_total b ON b.region = '서울'
 ORDER BY a.region
""",
    )
    run(
        conn,
        "TEMP TABLE 을 다음 질의에서 또 참조",
        "SELECT region, total FROM region_total ORDER BY total DESC",
    )
    conn.execute("DROP TABLE region_total")


if __name__ == "__main__":
    main()
