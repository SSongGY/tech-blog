"""클릭 로그를 '30분 넘게 쉬면 새 세션'으로 끊고 세션 번호를 매긴다.

1) LAG 로 같은 사용자의 바로 앞 클릭과의 간격(초)을 구한다
2) 간격이 30분을 넘거나 첫 클릭이면 1, 아니면 0 인 끊는 표시를 만든다
3) 끊는 표시를 누적 SUM 하면 그 값이 곧 세션 번호다
4) 세션마다 시작·끝·클릭 수·길이를 묶는다
5) 틀리기 쉬운 자리 — 경계값, 첫 행의 NULL, PARTITION 누락, 문자열 뺄셈
6) (user_id, clicked_at) 인덱스가 있으면 정렬 단계가 빠지는지 실행계획으로 본다
"""
import sqlite3

from dbshow import print_dataset, print_environment

SESSION_GAP_SECONDS = 30 * 60

# 같은 시각 클릭이 있어도 순서가 흔들리지 않게 click_id 를 두 번째 정렬 키로 둔다
USER_WINDOW = "PARTITION BY user_id ORDER BY clicked_at, click_id"

GAP_SQL = f"""
    SELECT click_id, user_id, clicked_at,
           unixepoch(clicked_at)
             - unixepoch(LAG(clicked_at) OVER ({USER_WINDOW})) AS gap_sec
    FROM click_log
"""

FLAG_SQL = f"""
    SELECT *,
           CASE WHEN gap_sec IS NULL OR gap_sec > {SESSION_GAP_SECONDS}
                THEN 1 ELSE 0 END AS is_new
    FROM ({GAP_SQL})
"""

SESSION_SQL = f"""
    SELECT *,
           SUM(is_new) OVER ({USER_WINDOW} ROWS UNBOUNDED PRECEDING) AS session_no
    FROM ({FLAG_SQL})
"""


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE click_log (
            click_id   INTEGER PRIMARY KEY,
            user_id    INTEGER NOT NULL,
            clicked_at TEXT    NOT NULL,   -- 'YYYY-MM-DD HH:MM:SS' (UTC)
            page       TEXT    NOT NULL
        );
        INSERT INTO click_log (click_id, user_id, clicked_at, page) VALUES
            (1,  1, '2026-11-19 09:00:00', '/'),
            (2,  2, '2026-11-19 09:05:00', '/'),
            (3,  1, '2026-11-19 09:10:00', '/item/7'),
            (4,  1, '2026-11-19 09:39:59', '/cart'),
            (5,  2, '2026-11-19 09:20:00', '/item/3'),
            (6,  1, '2026-11-19 10:09:59', '/item/9'),
            (7,  1, '2026-11-19 11:00:00', '/'),
            (8,  2, '2026-11-19 10:30:00', '/'),
            (9,  2, '2026-11-19 10:45:00', '/order'),
            (10, 1, '2026-11-19 23:50:00', '/'),
            (11, 1, '2026-11-20 00:10:00', '/item/7'),
            (12, 2, '2026-11-19 10:45:00', '/order/done');
        """
    )
    return conn


def show_rows(conn, sql, header=None):
    print("  sql> " + " ".join(sql.split())[:150] + " ...")
    cursor = conn.execute(sql)
    names = header or [d[0] for d in cursor.description]
    print("   ", tuple(names))
    for row in cursor:
        print("   ", row)


def plan(conn, sql):
    """sqlite3 CLI 의 .eqp 와 같은 트리 모양으로 찍는다 (|-- 와 `--)."""
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    children = {}
    for node_id, parent_id, _, detail in rows:
        children.setdefault(parent_id, []).append((node_id, detail))

    def draw(parent_id, indent):
        siblings = children.get(parent_id, [])
        for position, (node_id, detail) in enumerate(siblings):
            is_last = position == len(siblings) - 1
            print(f"    {indent}{'`--' if is_last else '|--'}{detail}")
            draw(node_id, indent + ("   " if is_last else "|  "))

    print("    QUERY PLAN")
    draw(0, "")


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("\n[1] LAG — 같은 사용자의 바로 앞 클릭과의 간격(초)")
    show_rows(conn, GAP_SQL + " ORDER BY user_id, clicked_at, click_id")

    print("\n[2] 끊는 표시 is_new — 첫 클릭이거나 1800초 초과")
    print("[3] 누적 SUM — 끊는 표시를 더해 가면 세션 번호")
    show_rows(
        conn,
        SESSION_SQL + " ORDER BY user_id, clicked_at, click_id",
    )

    print("\n[4] 세션마다 묶기")
    show_rows(
        conn,
        f"""
        SELECT user_id, session_no,
               MIN(clicked_at) AS started_at, MAX(clicked_at) AS ended_at,
               COUNT(*) AS clicks,
               unixepoch(MAX(clicked_at)) - unixepoch(MIN(clicked_at)) AS length_sec
        FROM ({SESSION_SQL})
        GROUP BY user_id, session_no
        ORDER BY user_id, session_no
        """,
    )

    print("\n[5-1] 경계 — 정확히 1800초인 행을 > 와 >= 로")
    show_rows(
        conn,
        f"""
        SELECT click_id, user_id, gap_sec,
               gap_sec > {SESSION_GAP_SECONDS} AS gt,
               gap_sec >= {SESSION_GAP_SECONDS} AS ge
        FROM ({GAP_SQL})
        WHERE gap_sec BETWEEN 1790 AND 1810
        """,
    )

    print("\n[5-2] 첫 행 NULL 을 빠뜨리면 — is_new 가 NULL, 첫 세션이 0 번")
    show_rows(
        conn,
        f"""
        SELECT click_id, user_id, gap_sec, is_new,
               SUM(is_new) OVER ({USER_WINDOW} ROWS UNBOUNDED PRECEDING) AS session_no
        FROM (SELECT *, gap_sec > {SESSION_GAP_SECONDS} AS is_new FROM ({GAP_SQL}))
        WHERE user_id = 2
        ORDER BY clicked_at, click_id
        """,
    )

    print("\n[5-3] PARTITION BY user_id 를 빠뜨리면 — 사용자별 세션 수")
    no_partition = SESSION_SQL.replace(USER_WINDOW, "ORDER BY clicked_at, click_id")
    show_rows(
        conn,
        f"""
        SELECT 'with_partition' AS version, COUNT(DISTINCT user_id || '-' || session_no)
        FROM ({SESSION_SQL})
        UNION ALL
        SELECT 'no_partition', COUNT(DISTINCT session_no) FROM ({no_partition})
        """,
        header=["version", "sessions"],
    )
    show_rows(
        conn,
        no_partition + " ORDER BY clicked_at, click_id LIMIT 6",
    )

    print("\n[5-4] 시각 문자열을 그대로 빼면")
    show_rows(
        conn,
        """
        SELECT '2026-11-19 10:09:59' - '2026-11-19 09:39:59' AS text_minus,
               unixepoch('2026-11-19 10:09:59')
                 - unixepoch('2026-11-19 09:39:59') AS unixepoch_minus,
               typeof('2026-11-19 10:09:59' - '2026-11-19 09:39:59') AS type
        """,
    )

    print("\n[6] 실행계획 — 인덱스 없을 때")
    plan(conn, SESSION_SQL)
    conn.execute(
        "CREATE INDEX ix_click_log_user_id_clicked_at "
        "ON click_log (user_id, clicked_at, click_id)"
    )
    print("\n[6] 실행계획 — (user_id, clicked_at, click_id) 인덱스를 만든 뒤")
    plan(conn, SESSION_SQL)


if __name__ == "__main__":
    main()
