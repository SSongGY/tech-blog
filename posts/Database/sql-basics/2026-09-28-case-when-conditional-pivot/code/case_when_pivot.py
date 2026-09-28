"""CASE WHEN — 조건에 따라 값을 고르고, 그것으로 행을 열로 돌린다.

지점별·월별 매출이 한 줄에 한 건씩 쌓인 표를 "지점을 열로" 놓은 보고서로 바꾼다.
그 전에 CASE 가 위에서부터 첫 번째로 맞는 WHEN 하나만 고른다는 것, ELSE 가 없으면
NULL 이 된다는 것, 단순 CASE 로는 NULL 을 찾을 수 없다는 것을 차례로 확인한다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

SALES = [
    # (id, sale_month, branch, amount) — 부산은 2월 매출이 없다
    (1, "2026-01", "서울", 120),
    (2, "2026-01", "서울", 80),
    (3, "2026-01", "부산", 40),
    (4, "2026-01", "대구", 55),
    (5, "2026-02", "서울", 95),
    (6, "2026-02", "대구", 30),
    (7, "2026-03", "서울", 60),
    (8, "2026-03", "부산", 150),
    (9, "2026-03", "대구", None),  # 금액이 아직 확정되지 않았다
]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE sale (
            id         INTEGER PRIMARY KEY,
            sale_month TEXT NOT NULL,
            branch     TEXT NOT NULL,
            amount     INTEGER
        )
        """
    )
    conn.executemany("INSERT INTO sale VALUES (?, ?, ?, ?)", SALES)
    conn.commit()
    return conn


def show(conn: sqlite3.Connection, label: str, sql: str) -> None:
    print(f"\n[{label}]")
    cursor = conn.execute(sql)
    print("  " + " | ".join(d[0] for d in cursor.description))
    for row in cursor.fetchall():
        print(f"  {row}")


def show_plan(conn: sqlite3.Connection, label: str, sql: str) -> None:
    # sqlite3 CLI 가 그리는 트리 모양을 그대로 흉내 낸다 (id·parent 로 깊이를 잡는다)
    print(f"\n[{label}]")
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    prefix = {0: ""}
    print("  QUERY PLAN")
    for i, (node_id, parent, _, detail) in enumerate(rows):
        is_last = all(r[1] != parent for r in rows[i + 1 :])
        branch = "`--" if is_last else "|--"
        lead = prefix.get(parent, "")
        print(f"  {lead}{branch}{detail}")
        prefix[node_id] = lead + ("   " if is_last else "|  ")


def section_value(conn: sqlite3.Connection) -> None:
    print("\n== 1. 조건에 따라 값을 고른다 ==")
    show(conn, "1-A 검색 CASE — 위에서부터 첫 번째로 맞는 WHEN", """
        SELECT id, amount,
               CASE WHEN amount >= 100 THEN '대형'
                    WHEN amount >= 50  THEN '중형'
                    ELSE '소형'
               END AS size_grade
        FROM sale ORDER BY id""")
    show(conn, "1-B WHEN 순서를 뒤집으면", """
        SELECT id, amount,
               CASE WHEN amount >= 50  THEN '중형'
                    WHEN amount >= 100 THEN '대형'
                    ELSE '소형'
               END AS size_grade
        FROM sale ORDER BY id""")
    show(conn, "1-C ELSE 를 빼면", """
        SELECT id, amount,
               CASE WHEN amount >= 100 THEN '대형' END AS size_grade
        FROM sale ORDER BY id""")


def section_null(conn: sqlite3.Connection) -> None:
    print("\n== 2. NULL 을 찾을 때 ==")
    show(conn, "2-A 단순 CASE 로 NULL 을 찾으면", """
        SELECT id, amount,
               CASE amount WHEN NULL THEN '미확정' ELSE '확정' END AS state
        FROM sale WHERE id IN (8, 9) ORDER BY id""")
    show(conn, "2-B 검색 CASE 에 IS NULL", """
        SELECT id, amount,
               CASE WHEN amount IS NULL THEN '미확정' ELSE '확정' END AS state
        FROM sale WHERE id IN (8, 9) ORDER BY id""")


def section_pivot(conn: sqlite3.Connection) -> None:
    print("\n== 3. 행을 열로 돌린다 (수동 피벗) ==")
    show(conn, "3-A 피벗 전 — 월·지점별 합계", """
        SELECT sale_month, branch, SUM(amount) AS total
        FROM sale GROUP BY sale_month, branch ORDER BY sale_month, branch""")
    pivot_sql = """
        SELECT sale_month,
               SUM(CASE WHEN branch = '서울' THEN amount END) AS seoul,
               SUM(CASE WHEN branch = '부산' THEN amount END) AS busan,
               SUM(CASE WHEN branch = '대구' THEN amount END) AS daegu
        FROM sale GROUP BY sale_month ORDER BY sale_month"""
    show(conn, "3-B CASE 피벗 — ELSE 없음", pivot_sql)
    show(conn, "3-C CASE 피벗 — ELSE 0", """
        SELECT sale_month,
               SUM(CASE WHEN branch = '서울' THEN amount ELSE 0 END) AS seoul,
               SUM(CASE WHEN branch = '부산' THEN amount ELSE 0 END) AS busan,
               SUM(CASE WHEN branch = '대구' THEN amount ELSE 0 END) AS daegu
        FROM sale GROUP BY sale_month ORDER BY sale_month""")
    show_plan(conn, "3-D CASE 피벗의 실행계획", pivot_sql)


def section_count(conn: sqlite3.Connection) -> None:
    print("\n== 4. 건수를 셀 때 ==")
    show(conn, "4-A COUNT(CASE ... THEN 1 END)", """
        SELECT sale_month,
               COUNT(CASE WHEN branch = '서울' THEN 1 END) AS seoul_cnt
        FROM sale GROUP BY sale_month ORDER BY sale_month""")
    show(conn, "4-B COUNT(CASE ... THEN 1 ELSE 0 END)", """
        SELECT sale_month,
               COUNT(CASE WHEN branch = '서울' THEN 1 ELSE 0 END) AS seoul_cnt
        FROM sale GROUP BY sale_month ORDER BY sale_month""")
    show(conn, "4-C 같은 일을 FILTER 절로", """
        SELECT sale_month,
               COUNT(*) FILTER (WHERE branch = '서울') AS seoul_cnt,
               SUM(amount) FILTER (WHERE branch = '서울') AS seoul
        FROM sale GROUP BY sale_month ORDER BY sale_month""")


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)
    section_value(conn)
    section_null(conn)
    section_pivot(conn)
    section_count(conn)


if __name__ == "__main__":
    main()
