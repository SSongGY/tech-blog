"""로그인·로그아웃이 따로 찍힌 이벤트 로그를 한 행짜리 구간으로 묶는다.

1) 방법 A: 상관 부질의 — 로그인마다 "그 뒤 첫 로그아웃"을 찾아온다
2) 방법 B: LEAD — 바로 다음 이벤트가 로그아웃일 때만 짝을 짓는다
3) 짝 없는 로그아웃 찾기 (LAG)
4) 사용자별 접속 시간 합계 — 끝나지 않은 세션이 사라지는 자리
5) 실행계획
6) 행 수를 늘려 VDBE 명령 수를 센다
"""
import random
import sqlite3

from dbshow import print_dataset, print_environment


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE login_event (
            event_id INTEGER PRIMARY KEY,
            user_id  TEXT NOT NULL,
            ts       TEXT NOT NULL,
            kind     TEXT NOT NULL CHECK (kind IN ('in', 'out'))
        );
        CREATE INDEX idx_login_event_user_ts ON login_event (user_id, ts);
        INSERT INTO login_event (user_id, ts, kind) VALUES
            ('U1', '2026-11-28 09:00', 'in'),
            ('U1', '2026-11-28 09:30', 'out'),
            ('U1', '2026-11-28 10:00', 'in'),
            ('U1', '2026-11-28 10:45', 'out'),
            ('U2', '2026-11-28 09:10', 'in'),    -- 로그아웃 기록이 빠졌다
            ('U2', '2026-11-28 11:00', 'in'),
            ('U2', '2026-11-28 11:20', 'out'),
            ('U3', '2026-11-28 09:05', 'out'),   -- 로그 수집 전에 들어온 세션의 끝
            ('U3', '2026-11-28 09:40', 'in');    -- 아직 접속 중
        """
    )
    return conn


def show_rows(conn, sql):
    cursor = conn.execute(sql)
    print("   ", tuple(d[0] for d in cursor.description))
    for row in cursor:
        print("   ", row)


def show_plan(conn, sql):
    """sqlite3 CLI 가 그리는 것과 같은 모양의 트리로 EXPLAIN QUERY PLAN 을 찍는다."""
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    children = {}
    for node_id, parent, _, detail in rows:
        children.setdefault(parent, []).append((node_id, detail))

    def walk(parent, prefix):
        nodes = children.get(parent, [])
        for i, (node_id, detail) in enumerate(nodes):
            last = i == len(nodes) - 1
            print("    " + prefix + ("`--" if last else "|--") + detail)
            walk(node_id, prefix + ("   " if last else "|  "))

    print("    QUERY PLAN")
    walk(0, "")


SQL_SUBQUERY = """
    SELECT i.user_id, i.ts AS login_ts,
           (SELECT MIN(o.ts) FROM login_event o
             WHERE o.user_id = i.user_id
               AND o.kind = 'out'
               AND o.ts > i.ts) AS logout_ts
    FROM login_event i
    WHERE i.kind = 'in'
    ORDER BY i.user_id, i.ts
"""

SQL_LEAD = """
    WITH ordered AS (
        SELECT user_id, ts, kind,
               LEAD(kind) OVER w AS next_kind,
               LEAD(ts)   OVER w AS next_ts
        FROM login_event
        WINDOW w AS (PARTITION BY user_id ORDER BY ts, event_id)
    )
    SELECT user_id, ts AS login_ts,
           CASE WHEN next_kind = 'out' THEN next_ts END AS logout_ts
    FROM ordered
    WHERE kind = 'in'
    ORDER BY user_id, ts
"""

SQL_ORPHAN_OUT = """
    WITH ordered AS (
        SELECT user_id, ts, kind,
               LAG(kind) OVER (PARTITION BY user_id ORDER BY ts, event_id) AS prev_kind
        FROM login_event
    )
    SELECT user_id, ts, prev_kind
    FROM ordered
    WHERE kind = 'out' AND (prev_kind IS NULL OR prev_kind <> 'in')
"""


def total_minutes(pair_sql, open_end=None):
    """짝지은 구간의 분 단위 길이를 사용자별로 더한다."""
    end_expr = "logout_ts" if open_end is None else f"COALESCE(logout_ts, '{open_end}')"
    return f"""
        SELECT user_id,
               COUNT(*) AS sessions,
               COUNT(logout_ts) AS closed,
               SUM(ROUND((julianday({end_expr}) - julianday(login_ts)) * 1440)) AS minutes
        FROM ({pair_sql})
        GROUP BY user_id ORDER BY user_id
    """


def count_vdbe(conn, sql):
    steps = 0

    def tick():
        nonlocal steps
        steps += 1
        return 0

    conn.set_progress_handler(tick, 1)
    rows = conn.execute(sql).fetchall()
    conn.set_progress_handler(None, 1)
    return steps, rows


def build_large(user_count, sessions_per_user, with_index=True):
    """사용자마다 로그인·로그아웃을 번갈아 넣는다. 로그아웃은 없는 경우가 없게 둔다."""
    rng = random.Random(20261128)
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE login_event (event_id INTEGER PRIMARY KEY,"
        " user_id TEXT NOT NULL, ts TEXT NOT NULL, kind TEXT NOT NULL)"
    )
    if with_index:
        conn.execute("CREATE INDEX idx_login_event_user_ts ON login_event (user_id, ts)")
    data = []
    for u in range(user_count):
        minute = 0
        for _ in range(sessions_per_user):
            minute += rng.randint(1, 120)
            data.append((f"U{u:04d}", f"{minute:08d}", "in"))
            minute += rng.randint(1, 120)
            data.append((f"U{u:04d}", f"{minute:08d}", "out"))
    conn.executemany("INSERT INTO login_event (user_id, ts, kind) VALUES (?, ?, ?)", data)
    return conn


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("\n[1] 방법 A — 상관 부질의: 로그인 뒤 첫 로그아웃")
    show_rows(conn, SQL_SUBQUERY)

    print("\n[2] 방법 B — LEAD: 바로 다음 이벤트가 로그아웃일 때만")
    show_rows(conn, SQL_LEAD)

    print("\n[3] 짝 없는 로그아웃 — 바로 앞 이벤트가 로그인이 아닌 것")
    show_rows(conn, SQL_ORPHAN_OUT)

    print("\n[4-1] 사용자별 접속 시간 — 방법 A 결과로")
    show_rows(conn, total_minutes(SQL_SUBQUERY))
    print("\n[4-2] 사용자별 접속 시간 — 방법 B 결과로 (끝나지 않은 세션은 NULL)")
    show_rows(conn, total_minutes(SQL_LEAD))
    print("\n[4-3] 방법 B, 끝나지 않은 세션은 집계 시각 12:00 까지로 친다")
    show_rows(conn, total_minutes(SQL_LEAD, open_end="2026-11-28 12:00"))

    print("\n[5] 실행계획")
    for label, sql in (("A 상관 부질의", SQL_SUBQUERY), ("B LEAD", SQL_LEAD)):
        print(f"  [{label}]")
        show_plan(conn, sql)

    print("\n[6] 사용자 100명 x 세션 수 — VDBE 명령 수 (로그아웃 누락 없음)")
    print(f"  {'이벤트 수':>8} {'A 상관 부질의':>14} {'B LEAD':>12}  결과 일치")
    for sessions in (10, 40, 160):
        big = build_large(100, sessions)
        sa, ra = count_vdbe(big, SQL_SUBQUERY)
        sb, rb = count_vdbe(big, SQL_LEAD)
        print(f"  {100 * sessions * 2:>8,} {sa:>14,} {sb:>12,}  {ra == rb}")
        big.close()

    print("\n[7] (user_id, ts) 인덱스가 없는 표")
    for sessions in (10, 40):
        big = build_large(100, sessions, with_index=False)
        sa, _ = count_vdbe(big, SQL_SUBQUERY)
        sb, _ = count_vdbe(big, SQL_LEAD)
        print(f"  {100 * sessions * 2:>8,}  A 상관 부질의 {sa:>12,}   B LEAD {sb:>10,}")
        if sessions == 40:
            print("  [A 상관 부질의, 인덱스 없음]")
            show_plan(big, SQL_SUBQUERY)
        big.close()
    conn.close()


if __name__ == "__main__":
    main()
