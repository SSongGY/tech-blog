"""집계 함수의 FILTER 절과 CASE WHEN 을 같은 질의로 맞대어 본다.

같은 숫자를 뽑는 두 가지 쓰기를 나란히 돌려 결과가 일치하는지 확인하고,
둘이 갈리는 자리(ELSE 생략, 빈 집합, WHERE 와의 차이)를 따로 찍는다.
"""

import sqlite3
import sys

from dbshow import print_dataset, print_environment

SCHEMA = """
CREATE TABLE support_ticket (
    ticket_id        INTEGER PRIMARY KEY,
    channel          TEXT    NOT NULL,
    status           TEXT    NOT NULL,
    priority         TEXT    NOT NULL,
    response_minutes INTEGER
);
"""

TICKETS = [
    (1, "전화", "closed", "high", 8),
    (2, "전화", "closed", "normal", 42),
    (3, "전화", "open", "high", None),
    (4, "이메일", "closed", "normal", 180),
    (5, "이메일", "closed", "high", 35),
    (6, "이메일", "open", "normal", None),
    (7, "챗봇", "closed", "normal", 3),
    (8, "챗봇", "closed", "normal", 5),
    (9, "챗봇", "closed", "high", 2),
    (10, "챗봇", "closed", "normal", 7),
    (11, "SNS", "closed", "normal", 95),
    (12, "SNS", "open", "normal", None),
]

CASE_WHEN_QUERY = """
SELECT channel,
       COUNT(*)                                                    AS 전체,
       COUNT(CASE WHEN status = 'open' THEN 1 END)                 AS 미처리,
       COUNT(CASE WHEN status = 'closed' THEN 1 END)               AS 처리완료,
       AVG(CASE WHEN priority = 'high' THEN response_minutes END)  AS 긴급평균
  FROM support_ticket
 GROUP BY channel
 ORDER BY channel
"""

FILTER_QUERY = """
SELECT channel,
       COUNT(*)                                             AS 전체,
       COUNT(*) FILTER (WHERE status = 'open')              AS 미처리,
       COUNT(*) FILTER (WHERE status = 'closed')            AS 처리완료,
       AVG(response_minutes) FILTER (WHERE priority = 'high') AS 긴급평균
  FROM support_ticket
 GROUP BY channel
 ORDER BY channel
"""


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO support_ticket VALUES (?, ?, ?, ?, ?)", TICKETS)
    return conn


def show(conn, title, sql):
    print(f"\n-- {title}")
    cur = conn.execute(sql)
    headers = [d[0] for d in cur.description]
    rows = cur.fetchall()
    print("  " + " | ".join(headers))
    for row in rows:
        print("  " + " | ".join("NULL" if v is None else str(v) for v in row))
    return rows


def show_plan(conn, title, sql):
    print(f"\n-- {title}")
    for _, _, _, detail in conn.execute("EXPLAIN QUERY PLAN " + sql):
        print("  " + detail)


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("\n" + "=" * 64)
    print("1. 같은 숫자를 두 가지로 쓴다")
    print("=" * 64)
    case_rows = show(conn, "CASE WHEN", CASE_WHEN_QUERY)
    filter_rows = show(conn, "FILTER", FILTER_QUERY)
    print(f"\n  두 결과가 같은가: {case_rows == filter_rows}")

    print("\n" + "=" * 64)
    print("2. ELSE 를 빠뜨리면 갈린다 — 해당 행이 하나도 없는 그룹")
    print("=" * 64)
    show(conn, "SUM(CASE ... THEN 1 END) vs COUNT(*) FILTER", """
SELECT channel,
       SUM(CASE WHEN status = 'open' THEN 1 END)       AS sum_case,
       SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) AS sum_case_else,
       COUNT(*) FILTER (WHERE status = 'open')          AS count_filter
  FROM support_ticket
 GROUP BY channel
 ORDER BY channel
""")

    print("\n" + "=" * 64)
    print("3. ELSE 0 을 넣으면 평균이 망가진다")
    print("=" * 64)
    show(conn, "AVG 의 세 가지 쓰기", """
SELECT channel,
       AVG(CASE WHEN priority = 'high' THEN response_minutes ELSE 0 END) AS avg_else0,
       AVG(CASE WHEN priority = 'high' THEN response_minutes END)        AS avg_else_null,
       AVG(response_minutes) FILTER (WHERE priority = 'high')            AS avg_filter
  FROM support_ticket
 GROUP BY channel
 ORDER BY channel
""")

    print("\n" + "=" * 64)
    print("4. 빈 집합에서 COUNT 와 나머지 집계가 다르게 답한다")
    print("=" * 64)
    show(conn, "high 가 한 건도 없는 SNS", """
SELECT channel,
       COUNT(*) FILTER (WHERE priority = 'high')              AS cnt,
       SUM(response_minutes) FILTER (WHERE priority = 'high') AS sum_,
       AVG(response_minutes) FILTER (WHERE priority = 'high') AS avg_,
       MAX(response_minutes) FILTER (WHERE priority = 'high') AS max_
  FROM support_ticket
 WHERE channel = 'SNS'
 GROUP BY channel
""")

    print("\n" + "=" * 64)
    print("5. WHERE 로 옮기면 다른 집계까지 줄어든다")
    print("=" * 64)
    show(conn, "FILTER — 전체는 그대로", """
SELECT channel,
       COUNT(*)                                  AS 전체,
       COUNT(*) FILTER (WHERE priority = 'high') AS 긴급
  FROM support_ticket
 GROUP BY channel
 ORDER BY channel
""")
    show(conn, "WHERE — 전체까지 긴급 건수가 된다", """
SELECT channel,
       COUNT(*) AS 전체,
       COUNT(*) AS 긴급
  FROM support_ticket
 WHERE priority = 'high'
 GROUP BY channel
 ORDER BY channel
""")

    print("\n" + "=" * 64)
    print("6. FILTER 조건이 NULL 이면 그 행은 빠진다")
    print("=" * 64)
    show(conn, "response_minutes 가 NULL 인 행의 취급", """
SELECT COUNT(*)                                         AS 전체,
       COUNT(*) FILTER (WHERE response_minutes > 10)    AS 참,
       COUNT(*) FILTER (WHERE NOT response_minutes > 10) AS 거짓,
       COUNT(*) FILTER (WHERE response_minutes IS NULL) AS 널
  FROM support_ticket
""")

    print("\n" + "=" * 64)
    print("7. DISTINCT · 윈도우 함수와 함께 쓸 수 있는가")
    print("=" * 64)
    for title, sql in [
        ("COUNT(DISTINCT ...) FILTER", """
SELECT COUNT(DISTINCT channel) FILTER (WHERE priority = 'high') AS 긴급채널수
  FROM support_ticket
"""),
        ("윈도우 함수 + FILTER", """
SELECT channel,
       status,
       COUNT(*) FILTER (WHERE status = 'closed')
           OVER (PARTITION BY channel) AS 채널내_처리완료
  FROM support_ticket
 ORDER BY channel, ticket_id
"""),
    ]:
        try:
            show(conn, title, sql)
        except sqlite3.Error as exc:
            print(f"\n-- {title}")
            print(f"  {type(exc).__name__}: {exc}")

    print("\n" + "=" * 64)
    print("8. 실행계획은 달라지는가")
    print("=" * 64)
    show_plan(conn, "CASE WHEN", CASE_WHEN_QUERY)
    show_plan(conn, "FILTER", FILTER_QUERY)

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
