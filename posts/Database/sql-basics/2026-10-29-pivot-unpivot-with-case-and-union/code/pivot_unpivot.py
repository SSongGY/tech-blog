"""행을 열로 펴고(피벗) 다시 행으로 되돌리는(언피벗) 질의를 실제로 돌려 본다.

SQLite 에는 PIVOT 구문이 없다. 표준 SQL 에도 없다. 그래서 집계 함수 안에서
CASE 로 값을 갈라 넣는 방식과, 그 역방향으로 UNION ALL 을 쌓는 방식을 쓴다.
여기서는 두 방식의 출력과 실행계획을 나란히 찍는다.
"""

import sqlite3
import unicodedata

from dbshow import print_dataset, print_environment

SCHEMA = """
CREATE TABLE sale (
    region  TEXT    NOT NULL,
    quarter INTEGER NOT NULL,
    amount  INTEGER NOT NULL
);
"""

# 대구 4분기 행을 일부러 비워 둔다 — 피벗했을 때 그 칸이 0 이 아니라
# NULL 로 나오는 것을 보이기 위해서다.
ROWS = [
    ("서울", 1, 120), ("서울", 2, 150), ("서울", 3, 90),  ("서울", 4, 200),
    ("부산", 1, 80),  ("부산", 2, 70),  ("부산", 3, 110), ("부산", 4, 60),
    ("대구", 1, 40),  ("대구", 2, 55),  ("대구", 3, 30),
]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO sale VALUES (?, ?, ?)", ROWS)
    conn.commit()
    return conn


def _width(text: str) -> int:
    """한글은 두 칸을 차지한다. len 으로 재면 칸이 어긋난다."""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def show(conn: sqlite3.Connection, title: str, sql: str) -> None:
    print("-" * 64)
    print(title)
    print("-" * 64)
    print(sql.strip())
    print()
    cur = conn.execute(sql)
    headers = [d[0] for d in cur.description]
    cells = [["NULL" if v is None else str(v) for v in row] for row in cur.fetchall()]
    widths = [
        max([_width(headers[i])] + [_width(r[i]) for r in cells])
        for i in range(len(headers))
    ]
    print("  " + " | ".join(h + " " * (w - _width(h)) for h, w in zip(headers, widths)))
    print("  " + "-+-".join("-" * w for w in widths))
    for row in cells:
        print("  " + " | ".join(
            " " * (w - _width(c)) + c for c, w in zip(row, widths)
        ))
    print()


def show_plan(conn: sqlite3.Connection, title: str, sql: str) -> None:
    """sqlite3 CLI 가 그리는 것과 같은 트리로 찍는다.

    EXPLAIN QUERY PLAN 은 (id, parent, notused, detail) 을 돌려준다. CLI 는
    parent 를 따라 들여쓰고 마지막 자식에 `-- 를 붙인다. 중첩이 드러나야
    CO-ROUTINE 이 몇 번 도는지 같은 것이 보인다.
    """
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    children: dict[int, list[tuple[int, str]]] = {}
    for node_id, parent, _notused, detail in rows:
        children.setdefault(parent, []).append((node_id, detail))

    print("-" * 64)
    print(title)
    print("-" * 64)
    print("QUERY PLAN")

    def walk(parent: int, prefix: str) -> None:
        kids = children.get(parent, [])
        for pos, (node_id, detail) in enumerate(kids):
            last = pos == len(kids) - 1
            print(prefix + ("`--" if last else "|--") + detail)
            walk(node_id, prefix + ("   " if last else "|  "))

    walk(0, "")
    print()


PIVOT_CASE = """
SELECT region,
       SUM(CASE WHEN quarter = 1 THEN amount END) AS q1,
       SUM(CASE WHEN quarter = 2 THEN amount END) AS q2,
       SUM(CASE WHEN quarter = 3 THEN amount END) AS q3,
       SUM(CASE WHEN quarter = 4 THEN amount END) AS q4
  FROM sale
 GROUP BY region
 ORDER BY region
"""

PIVOT_FILTER = """
SELECT region,
       SUM(amount) FILTER (WHERE quarter = 1) AS q1,
       SUM(amount) FILTER (WHERE quarter = 2) AS q2,
       SUM(amount) FILTER (WHERE quarter = 3) AS q3,
       SUM(amount) FILTER (WHERE quarter = 4) AS q4
  FROM sale
 GROUP BY region
 ORDER BY region
"""

PIVOT_WITHOUT_AGGREGATE = """
SELECT region,
       CASE WHEN quarter = 1 THEN amount END AS q1,
       CASE WHEN quarter = 2 THEN amount END AS q2
  FROM sale
 WHERE region = '서울'
"""

PIVOT_COUNT = """
SELECT region,
       COUNT(CASE WHEN quarter = 4 THEN amount END) AS q4_cnt,
       SUM(CASE WHEN quarter = 4 THEN amount END)   AS q4_sum,
       COALESCE(SUM(CASE WHEN quarter = 4 THEN amount END), 0) AS q4_zero
  FROM sale
 GROUP BY region
 ORDER BY region
"""

WIDE_VIEW = """
CREATE VIEW sale_wide AS
SELECT region,
       SUM(CASE WHEN quarter = 1 THEN amount END) AS q1,
       SUM(CASE WHEN quarter = 2 THEN amount END) AS q2,
       SUM(CASE WHEN quarter = 3 THEN amount END) AS q3,
       SUM(CASE WHEN quarter = 4 THEN amount END) AS q4
  FROM sale
 GROUP BY region
"""

UNPIVOT_UNION = """
SELECT region, 1 AS quarter, q1 AS amount FROM sale_wide WHERE q1 IS NOT NULL
UNION ALL
SELECT region, 2, q2 FROM sale_wide WHERE q2 IS NOT NULL
UNION ALL
SELECT region, 3, q3 FROM sale_wide WHERE q3 IS NOT NULL
UNION ALL
SELECT region, 4, q4 FROM sale_wide WHERE q4 IS NOT NULL
ORDER BY region, quarter
"""

UNPIVOT_JOIN = """
WITH quarter_no(quarter) AS (VALUES (1), (2), (3), (4))
SELECT w.region,
       q.quarter,
       CASE q.quarter WHEN 1 THEN w.q1 WHEN 2 THEN w.q2
                      WHEN 3 THEN w.q3 ELSE w.q4 END AS amount
  FROM sale_wide AS w
  CROSS JOIN quarter_no AS q
 WHERE CASE q.quarter WHEN 1 THEN w.q1 WHEN 2 THEN w.q2
                      WHEN 3 THEN w.q3 ELSE w.q4 END IS NOT NULL
 ORDER BY w.region, q.quarter
"""


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)

    show(conn, "1. 집계 없이 CASE 만 쓰면 — 행 수가 그대로다", PIVOT_WITHOUT_AGGREGATE)
    show(conn, "2. 피벗 — SUM(CASE WHEN ...)", PIVOT_CASE)
    show(conn, "3. 같은 결과를 FILTER 절로", PIVOT_FILTER)
    show(conn, "4. 빈 칸은 0 이 아니라 NULL 이다", PIVOT_COUNT)

    conn.executescript(WIDE_VIEW)
    show(conn, "5. 언피벗 — UNION ALL", UNPIVOT_UNION)
    show(conn, "6. 언피벗 — 분기 번호 목록과 교차 조인", UNPIVOT_JOIN)

    show_plan(conn, "7-1. UNION ALL 언피벗의 실행계획", UNPIVOT_UNION)
    show_plan(conn, "7-2. 교차 조인 언피벗의 실행계획", UNPIVOT_JOIN)

    conn.close()


if __name__ == "__main__":
    main()
