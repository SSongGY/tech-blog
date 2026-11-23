"""게임 기록에서 '자기 최고점을 갱신한 판'만 고른다.

1) 직전까지의 누적 MAX 를 창 함수로 구해 나란히 본다
2) score > 직전 MAX 로 거르면 첫 판이 빠진다 (NULL 비교)
3) 첫 판을 넣는 두 방법 — IS NULL 을 더하거나 COALESCE 로 바닥값을 둔다
4) 같은 점수(동점)를 갱신으로 볼지 — > 와 >= 의 차이
5) 정렬 키가 같은 판이 있을 때 — ROWS 는 순서에 기대고 GROUPS 는 같은 날을 통째로 뺀다
6) 상관 부질의 두 가지 — > (SELECT MAX ...) 와 NOT EXISTS
7) 실행계획과 VDBE 명령 수 — 행이 늘 때 두 방식이 갈리는 정도
"""
import sqlite3

from dbshow import print_dataset, print_environment

PREV_MAX = """MAX(score) OVER (PARTITION BY player ORDER BY play_id
                     ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING)"""


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE play_log (
            play_id   INTEGER PRIMARY KEY,   -- 들어온 순서
            player    TEXT    NOT NULL,
            played_on TEXT    NOT NULL,      -- 하루에 여러 판을 할 수 있다
            score     INTEGER NOT NULL
        );
        INSERT INTO play_log (player, played_on, score) VALUES
            ('mina', '2026-11-01', 120), ('mina', '2026-11-02', 150),
            ('mina', '2026-11-03', 140), ('mina', '2026-11-04', 150),
            ('mina', '2026-11-05', 180), ('mina', '2026-11-05', 210),
            ('mina', '2026-11-06', 200),
            ('jun',  '2026-11-01', 300), ('jun',  '2026-11-02', 280),
            ('jun',  '2026-11-03', 310), ('jun',  '2026-11-03', 305),
            ('jun',  '2026-11-04', 330);
        """
    )
    return conn


def show_rows(conn, sql):
    print("  sql> " + " ".join(sql.split())[:150] + " ...")
    cursor = conn.execute(sql)
    print("   ", tuple(d[0] for d in cursor.description))
    for row in cursor:
        print("   ", row)


def show_plan(conn, sql):
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    # sqlite3 CLI 와 같은 모양으로 그린다: 조상이 형제 중 마지막이 아니면 그 자리에 "|  " 를 남긴다
    last_child = {parent_id: node_id for node_id, parent_id, _, _ in rows}
    prefix = {0: ""}
    print("  QUERY PLAN")
    for node_id, parent_id, _, detail in rows:
        is_last = last_child[parent_id] == node_id
        lead = prefix.get(parent_id, "")
        print("  " + lead + ("`--" if is_last else "|--") + detail)
        prefix[node_id] = lead + ("   " if is_last else "|  ")


def count_vdbe_steps(conn, sql):
    """질의 하나가 끝날 때까지 실행한 VDBE 명령 수 — 시간과 달리 매번 같은 값이 나온다."""
    steps = 0

    def tick():
        nonlocal steps
        steps += 1
        return 0

    conn.set_progress_handler(tick, 1)
    conn.execute(sql).fetchall()
    conn.set_progress_handler(None, 1)
    return steps


WINDOW_SQL = f"""
    SELECT play_id, player, score FROM (
        SELECT play_id, player, score, {PREV_MAX} AS prev_best
        FROM play_log)
    WHERE prev_best IS NULL OR score > prev_best"""

NOT_EXISTS_SQL = """
    SELECT p.play_id, p.player, p.score
    FROM play_log AS p
    WHERE NOT EXISTS (SELECT 1 FROM play_log AS e
                      WHERE e.player = p.player AND e.play_id < p.play_id
                        AND e.score >= p.score)"""


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("\n[1] 판마다 직전까지의 최고점을 나란히")
    show_rows(conn, f"""
        SELECT play_id, player, score, {PREV_MAX} AS prev_best
        FROM play_log ORDER BY player, play_id""")

    print("\n[2] score > prev_best 로만 거른다 — 첫 판이 빠진다")
    show_rows(conn, f"""
        SELECT play_id, player, score, prev_best FROM (
            SELECT play_id, player, score, {PREV_MAX} AS prev_best FROM play_log)
        WHERE score > prev_best ORDER BY player, play_id""")
    print("[2-1] 첫 판의 비교 결과는 거짓이 아니라 NULL 이다")
    show_rows(conn, "SELECT 120 > NULL AS cmp, (120 > NULL) IS NULL AS is_null")

    print("\n[3-1] prev_best IS NULL 을 더한다")
    show_rows(conn, WINDOW_SQL + " ORDER BY player, play_id")
    print("[3-2] COALESCE 로 바닥값을 둔다 — 점수가 음수가 될 수 없을 때만 안전하다")
    show_rows(conn, f"""
        SELECT play_id, player, score FROM (
            SELECT play_id, player, score, {PREV_MAX} AS prev_best FROM play_log)
        WHERE score > COALESCE(prev_best, -1) ORDER BY player, play_id""")

    print("\n[4] 동점을 갱신으로 볼 때 (>=) — mina 4번 판 150 이 끼어든다")
    show_rows(conn, f"""
        SELECT play_id, player, score FROM (
            SELECT play_id, player, score, {PREV_MAX} AS prev_best FROM play_log)
        WHERE prev_best IS NULL OR score >= prev_best ORDER BY player, play_id""")

    print("\n[5-1] 날짜만으로 정렬한 ROWS — 같은 날 두 판의 순서는 질의가 정하지 않았다")
    show_rows(conn, """
        SELECT play_id, player, played_on, score,
               MAX(score) OVER (PARTITION BY player ORDER BY played_on
                   ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS prev_rows
        FROM play_log ORDER BY player, played_on, play_id""")
    print("[5-2] GROUPS — 같은 날 판은 서로를 보지 않는다 ('전날까지의 최고점')")
    show_rows(conn, """
        SELECT play_id, player, played_on, score,
               MAX(score) OVER (PARTITION BY player ORDER BY played_on
                   GROUPS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS prev_days
        FROM play_log ORDER BY player, played_on, play_id""")

    print("\n[6-1] 상관 부질의 > (SELECT MAX ...) — [2] 와 같은 NULL 함정")
    show_rows(conn, """
        SELECT p.play_id, p.player, p.score FROM play_log AS p
        WHERE p.score > (SELECT MAX(e.score) FROM play_log AS e
                         WHERE e.player = p.player AND e.play_id < p.play_id)
        ORDER BY p.player, p.play_id""")
    print("[6-2] NOT EXISTS — 앞선 판이 없으면 참이라 첫 판이 저절로 들어온다")
    show_rows(conn, NOT_EXISTS_SQL + " ORDER BY p.player, p.play_id")

    print("\n[7-1] 실행계획 — 창 함수")
    show_plan(conn, WINDOW_SQL)
    print("[7-2] 실행계획 — NOT EXISTS")
    show_plan(conn, NOT_EXISTS_SQL)

    print("\n[7-3] 판 수를 늘려 가며 VDBE 명령 수 (선수 1명)")
    # 난수 대신 고정 규칙: 같은 입력이면 늘 같은 점수열이 나온다
    patterns = {
        "mixed": lambda i: (i * 7919) % 1000,   # 오르내림이 섞인 점수
        "rising": lambda i: i,                  # 판마다 기록을 갱신하는 최악의 경우
    }
    print("    (pattern, rows, records, window, not_exists)")
    for name, score_of in patterns.items():
        for total in (200, 400, 800):
            big = sqlite3.connect(":memory:")
            big.execute("CREATE TABLE play_log (play_id INTEGER PRIMARY KEY,"
                        " player TEXT, played_on TEXT, score INTEGER)")
            big.executemany(
                "INSERT INTO play_log (player, played_on, score) VALUES ('p', '', ?)",
                [(score_of(i),) for i in range(total)])
            records = len(big.execute(WINDOW_SQL).fetchall())
            window_steps = count_vdbe_steps(big, WINDOW_SQL)
            exists_steps = count_vdbe_steps(big, NOT_EXISTS_SQL)
            print("   ", (name, total, records, window_steps, exists_steps))
            big.close()
    conn.close()


if __name__ == "__main__":
    main()
