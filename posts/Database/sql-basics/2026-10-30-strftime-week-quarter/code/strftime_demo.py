"""strftime 으로 주차·분기를 뽑을 때 걸리는 자리를 실제로 돌려 확인한다.

파이썬 코드는 질의를 던지고 결과를 찍는 역할만 한다. 계산은 전부 SQLite 안에서
일어나므로, 아래 SQL 을 sqlite3 CLI 에 그대로 붙여 넣어도 같은 값이 나온다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

RULE = "=" * 64

SCHEMA = """
CREATE TABLE orders (
    id       INTEGER PRIMARY KEY,
    ordered  TEXT NOT NULL,   -- ISO-8601 문자열. SQLite 에는 날짜 타입이 없다
    amount   INTEGER NOT NULL
);
"""

# 연말·연초를 일부러 걸치게 깔았다. 주차 계산이 갈리는 구간이 여기다.
ROWS = [
    (1, "2025-12-28", 12000),   # 일
    (2, "2025-12-29", 8000),    # 월
    (3, "2025-12-31", 30000),   # 수
    (4, "2026-01-01", 5000),    # 목
    (5, "2026-01-03", 7000),    # 토
    (6, "2026-01-04", 9000),    # 일
    (7, "2026-01-05", 11000),   # 월
    (8, "2026-02-14", 21000),
    (9, "2026-04-01", 15000),
    (10, "2026-07-31", 42000),
    (11, "2026-10-30", 18000),
    (12, "2026-12-31", 25000),
]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO orders VALUES (?, ?, ?)", ROWS)
    conn.commit()
    return conn


def section(title: str) -> None:
    print(RULE)
    print(title)
    print(RULE)


def run(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> None:
    """질의문을 먼저 보이고 결과를 그 아래 찍는다."""
    print(sql.strip())
    print("-" * 64)
    cursor = conn.execute(sql, params)
    names = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    widths = [max(len(n), *(len(str(r[i])) for r in rows)) if rows else len(n)
              for i, n in enumerate(names)]
    print("  " + " | ".join(n.ljust(w) for n, w in zip(names, widths)))
    print("  " + "-+-".join("-" * w for w in widths))
    for row in rows:
        print("  " + " | ".join(str(v).ljust(w) for v, w in zip(row, widths)))
    print()


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)

    section("1. 포맷 문자 하나하나가 무엇을 내놓는가")
    # 같은 한 시각에 모든 치환 문자를 적용해 본다. 지원하지 않는 문자는 NULL 이다.
    run(conn, """
        SELECT strftime('%Y', t) AS "%Y",
               strftime('%m', t) AS "%m",
               strftime('%d', t) AS "%d",
               strftime('%j', t) AS "%j",
               strftime('%H:%M:%S', t) AS "%H:%M:%S",
               strftime('%s', t) AS "%s",
               strftime('%J', t) AS "%J"
        FROM (SELECT '2026-01-03 14:05:06' AS t)
    """)
    run(conn, """
        SELECT strftime('%w', t) AS "%w",
               strftime('%u', t) AS "%u",
               strftime('%U', t) AS "%U",
               strftime('%V', t) AS "%V",
               strftime('%W', t) AS "%W",
               strftime('%G', t) AS "%G",
               strftime('%g', t) AS "%g"
        FROM (SELECT '2026-01-03 14:05:06' AS t)
    """)
    run(conn, """
        SELECT strftime('%a', t) AS "%a",
               strftime('%b', t) AS "%b",
               strftime('%y', t) AS "%y",
               strftime('%D', t) AS "%D"
        FROM (SELECT '2026-01-03' AS t)
    """)

    section("2. 연초 경계 -- %U %V %W %G 가 서로 다른 답을 낸다")
    run(conn, """
        SELECT ordered,
               strftime('%u', ordered) AS iso요일,
               strftime('%Y', ordered) AS 달력연도,
               strftime('%U', ordered) AS "%U",
               strftime('%V', ordered) AS "%V",
               strftime('%W', ordered) AS "%W",
               strftime('%G', ordered) AS "%G"
        FROM orders
        WHERE ordered BETWEEN '2025-12-28' AND '2026-01-05'
        ORDER BY ordered
    """)

    section("3. 분기 -- 전용 포맷 문자가 없으므로 월에서 계산한다")
    run(conn, """
        SELECT ordered,
               CAST(strftime('%m', ordered) AS INTEGER) AS 월,
               (CAST(strftime('%m', ordered) AS INTEGER) + 2) / 3 AS 분기
        FROM orders
        ORDER BY ordered
    """)
    # 틀린 질의. || 가 / 보다 먼저 묶여 라벨이 숫자 하나로 뭉개진다.
    run(conn, """
        SELECT strftime('%Y', ordered) || '-Q'
                 || (CAST(strftime('%m', ordered) AS INTEGER) + 2) / 3 AS 분기,
               COUNT(*) AS 건수,
               SUM(amount) AS 합계
        FROM orders
        GROUP BY 분기
        ORDER BY 분기
    """)
    # 나눗셈 전체를 괄호로 묶어야 한다.
    run(conn, """
        SELECT strftime('%Y', ordered) || '-Q'
                 || ((CAST(strftime('%m', ordered) AS INTEGER) + 2) / 3) AS 분기,
               COUNT(*) AS 건수,
               SUM(amount) AS 합계
        FROM orders
        GROUP BY 분기
        ORDER BY 분기
    """)

    section("4. 주 단위 집계 -- 주의 시작일로 묶는 쪽이 안전하다")
    # %V 로 묶으면 연도를 함께 묶지 않는 한 2025-W52 와 2026-W52 가 한 칸에 들어간다.
    run(conn, """
        SELECT strftime('%G-W%V', ordered) AS iso주,
               date(ordered, '-6 days', 'weekday 1') AS 주시작,
               COUNT(*) AS 건수,
               SUM(amount) AS 합계
        FROM orders
        WHERE ordered < '2026-02-01'
        GROUP BY iso주
        ORDER BY iso주
    """)
    # 일요일 시작으로 묶으려면 weekday 0 에서 7일을 뺀다.
    run(conn, """
        SELECT ordered,
               date(ordered, '-6 days', 'weekday 1') AS 월요일시작,
               date(ordered, 'weekday 0', '-7 days') AS 일요일시작
        FROM orders
        WHERE ordered < '2026-02-01'
        ORDER BY ordered
    """)

    section("5. 월초·월말과 +N months")
    run(conn, """
        SELECT ordered,
               date(ordered, 'start of month') AS 월초,
               date(ordered, 'start of month', '+1 month', '-1 day') AS 월말
        FROM orders
        WHERE ordered IN ('2026-02-14', '2026-07-31', '2026-12-31')
        ORDER BY ordered
    """)
    # 월말에 +1 month 를 더하면 없는 날짜가 다음 달로 넘어간다. 기본값이 ceiling 이다.
    run(conn, """
        SELECT d,
               date(d, '+1 month') AS 기본값,
               date(d, '+1 month', 'floor') AS floor,
               date(d, '+1 month', 'ceiling') AS ceiling
        FROM (SELECT '2026-01-31' AS d
              UNION ALL SELECT '2026-03-31'
              UNION ALL SELECT '2024-01-29')
        ORDER BY d
    """)

    section("6. 이 버전에 없는 수정자는 조용히 NULL 이 된다")
    run(conn, """
        SELECT date('2026-03-15', 'end of month') AS "end of month",
               strftime('%Q', '2026-03-15')       AS "%Q",
               date('2026-03-15', 'weekday -1')   AS "weekday -1"
    """)

    section("7. 반환값은 문자열이다 -- 숫자처럼 쓰면 비교가 틀어진다")
    run(conn, """
        SELECT typeof(strftime('%m', '2026-10-30'))        AS 반환타입,
               strftime('%m', '2026-01-30') > 9            AS "'01' > 9",
               CAST(strftime('%m', '2026-01-30') AS INTEGER) > 9 AS "CAST 후",
               '2026-Q1' / 3                               AS "'2026-Q1' / 3",
               CAST('2026-Q1' AS INTEGER)                  AS "CAST('2026-Q1')"
    """)

    conn.close()


if __name__ == "__main__":
    main()
