"""쪽 데이터와 전체 건수를 한 질의로 받기 — COUNT(*) OVER () 와 LIMIT 의 평가 순서.

1) 두 질의로 받기 — 쪽 질의 + COUNT(*) 질의
2) 한 질의로 받기 — COUNT(*) OVER () 는 LIMIT 전의 행을 센다
3) 범위 밖 쪽 — 행이 0개면 건수도 같이 사라진다
4) LIMIT 을 부질의 안에 넣으면 — 창 함수가 LIMIT 뒤의 5행만 센다
5) 일량 — 인덱스로 5행에서 멈추던 쪽 질의가 조건에 맞는 행을 전부 읽는다
6) 실행계획
"""
import sqlite3
from datetime import datetime, timedelta

from dbshow import _render, print_dataset, print_environment

PAGE_SQL = """
    SELECT article_id, title, created_at
    FROM article
    WHERE category = 'db'
    ORDER BY created_at DESC
    LIMIT 3 OFFSET {offset}
"""

TOTAL_SQL = "SELECT COUNT(*) AS total FROM article WHERE category = 'db'"

COMBINED_SQL = """
    SELECT article_id, title, created_at,
           COUNT(*) OVER () AS total
    FROM article
    WHERE category = 'db'
    ORDER BY created_at DESC
    LIMIT 3 OFFSET {offset}
"""


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE article (
            article_id INTEGER PRIMARY KEY,
            category   TEXT NOT NULL,
            title      TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        INSERT INTO article VALUES
            (1,  'db',    '인덱스 기초',      '2026-11-01'),
            (2,  'web',   'HTTP 캐시',        '2026-11-02'),
            (3,  'db',    '조인 순서',        '2026-11-03'),
            (4,  'db',    '실행계획 읽기',    '2026-11-04'),
            (5,  'linux', 'grep 옵션',        '2026-11-05'),
            (6,  'db',    '트랜잭션',         '2026-11-06'),
            (7,  'web',   '쿠키와 세션',      '2026-11-07'),
            (8,  'db',    '창 함수',          '2026-11-08'),
            (9,  'db',    'NULL 비교',        '2026-11-09'),
            (10, 'linux', 'tar 묶기',         '2026-11-10'),
            (11, 'db',    '페이징',           '2026-11-11');
        """
    )
    return conn


def show(conn, sql):
    print("  sql> " + " ".join(sql.split()))
    cursor = conn.execute(sql)
    headers = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    print("  " + " | ".join(headers))
    for row in rows:
        print("  " + " | ".join("NULL" if v is None else str(v) for v in row))
    print(f"  ({len(rows)}행)")
    print()


def show_plan(conn, sql):
    print("  sql> " + " ".join(sql.split()))
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    # sqlite3 CLI 와 같은 모양으로 그린다: 부모 id 로 깊이를, 형제 중 마지막인지로 가지 모양을 정한다
    depth = {0: -1}
    last_child = {parent_id: node_id for node_id, parent_id, _, _ in rows}
    print("  QUERY PLAN")
    for node_id, parent_id, _, detail in rows:
        depth[node_id] = depth.get(parent_id, -1) + 1
        branch = "`--" if last_child[parent_id] == node_id else "|--"
        print("  " + "   " * depth[node_id] + branch + detail)
    print()


def count_vdbe_steps(conn, sql):
    """질의 하나가 끝날 때까지 실행한 VDBE 명령 수 — 시간과 달리 매번 같은 값이 나온다."""
    steps = 0

    def tick():
        nonlocal steps
        steps += 1
        return 0

    conn.set_progress_handler(tick, 1)
    rows = conn.execute(sql).fetchall()
    conn.set_progress_handler(None, 1)
    return steps, len(rows)


def build_large_database(row_count):
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE article (
            article_id INTEGER PRIMARY KEY,
            category   TEXT NOT NULL,
            title      TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE INDEX ix_article_category_created_at ON article (category, created_at);
        """
    )
    categories = ("db", "web", "linux", "ai")
    start = datetime(2026, 1, 1)
    conn.executemany(
        "INSERT INTO article VALUES (?, ?, ?, ?)",
        (
            (
                i,
                categories[i % 4],
                f"글 {i}",
                # 초 단위로 하나씩 늘려 created_at 이 겹치지 않게 한다
                (start + timedelta(seconds=i)).strftime("%Y-%m-%d %H:%M:%S"),
            )
            for i in range(1, row_count + 1)
        ),
    )
    conn.commit()
    return conn


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("[1] 두 질의로 받기 — 1쪽(3행)과 전체 건수")
    show(conn, PAGE_SQL.format(offset=0))
    show(conn, TOTAL_SQL)

    print("[2] 한 질의로 받기 — COUNT(*) OVER ()")
    show(conn, COMBINED_SQL.format(offset=0))
    print("[2] 같은 질의의 3쪽 (OFFSET 6)")
    show(conn, COMBINED_SQL.format(offset=6))

    print("[3] 범위 밖 쪽 (OFFSET 9) — 두 질의 방식과 한 질의 방식")
    show(conn, PAGE_SQL.format(offset=9))
    show(conn, TOTAL_SQL)
    show(conn, COMBINED_SQL.format(offset=9))

    print("[4] LIMIT 을 부질의 안에 넣으면 — 창 함수는 LIMIT 뒤의 행을 센다")
    show(
        conn,
        """
        SELECT article_id, title, COUNT(*) OVER () AS total
        FROM (SELECT article_id, title, created_at
              FROM article
              WHERE category = 'db'
              ORDER BY created_at DESC
              LIMIT 3)
        """,
    )

    print("[5] 일량 — 20만 행, (category, created_at) 인덱스, 1쪽 3행")
    big = build_large_database(200_000)
    matched = big.execute(TOTAL_SQL).fetchone()[0]
    print(f"  category = 'db' 인 행: {matched:,}")
    cases = [
        ("쪽 질의만", PAGE_SQL.format(offset=0)),
        ("COUNT(*) 질의만", TOTAL_SQL),
        ("한 질의 (COUNT(*) OVER ())", COMBINED_SQL.format(offset=0)),
    ]
    result_rows = []
    for label, sql in cases:
        steps, returned = count_vdbe_steps(big, sql)
        result_rows.append((label, f"{steps:,}", returned))
    for line in _render(["질의", "VDBE 명령 수", "반환 행"], result_rows, [False, True, True]):
        print("  " + line)
    print()

    print("[6] 실행계획 — 20만 행 표")
    show_plan(big, PAGE_SQL.format(offset=0))
    show_plan(big, TOTAL_SQL)
    show_plan(big, COMBINED_SQL.format(offset=0))
    big.close()
    conn.close()


if __name__ == "__main__":
    main()
