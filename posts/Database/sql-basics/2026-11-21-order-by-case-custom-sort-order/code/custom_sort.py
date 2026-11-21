"""가나다순(문자열 순)이 아닌 업무 순서로 정렬한다.

1) 문자열 그대로 정렬하면 high · low · medium 이 된다
2) ORDER BY CASE 로 순서를 직접 매긴다
3) 목록에 없는 값과 NULL 은 어디로 가는가 — ELSE 를 빠뜨리면 맨 위
4) 순서 표(priority_rank)를 만들어 조인한다
5) instr() 로 순서 문자열 안의 위치를 쓴다
6) 실행계획 — 인덱스가 있어도 CASE 로 정렬하면 임시 B-Tree
7) 식 인덱스로 CASE 정렬에 인덱스를 태운다
"""
import sqlite3

from dbshow import print_dataset, print_environment

CASE_RANK = """CASE priority
               WHEN 'high'   THEN 1
               WHEN 'medium' THEN 2
               WHEN 'low'    THEN 3
           END"""

CASE_RANK_ELSE = """CASE priority
               WHEN 'high'   THEN 1
               WHEN 'medium' THEN 2
               WHEN 'low'    THEN 3
               ELSE 9
           END"""


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE ticket (
            ticket_id  INTEGER PRIMARY KEY,
            title      TEXT NOT NULL,
            priority   TEXT,              -- high / medium / low 를 기대하지만 막지 않았다
            created_at TEXT NOT NULL
        );
        INSERT INTO ticket (ticket_id, title, priority, created_at) VALUES
            (1, 'login fails',        'medium', '2026-11-02'),
            (2, 'typo on footer',     'low',    '2026-11-01'),
            (3, 'payment timeout',    'high',   '2026-11-03'),
            (4, 'slow search',        'medium', '2026-11-01'),
            (5, 'old browser layout', 'low',    '2026-11-04'),
            (6, 'data loss on save',  'high',   '2026-11-02'),
            (7, 'new logo',           'later',  '2026-11-05'),
            (8, 'unknown report',     NULL,     '2026-11-03');

        -- 순서를 데이터로 둔다. 순서가 바뀌면 이 표만 고친다.
        CREATE TABLE priority_rank (
            priority  TEXT PRIMARY KEY,
            sort_rank INTEGER NOT NULL
        );
        INSERT INTO priority_rank (priority, sort_rank) VALUES
            ('high', 1), ('medium', 2), ('low', 3);
        """
    )
    return conn


def show_rows(conn, sql):
    print("  sql> " + " ".join(sql.split())[:150] + " ...")
    cursor = conn.execute(sql)
    print("   ", tuple(d[0] for d in cursor.description))
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

    known_only = "WHERE priority IN ('high', 'medium', 'low')"

    print("\n[1] 문자열 그대로 정렬 — 오름차순과 내림차순")
    show_rows(conn, f"SELECT ticket_id, priority FROM ticket {known_only} "
                    "ORDER BY priority, ticket_id")
    show_rows(conn, f"SELECT ticket_id, priority FROM ticket {known_only} "
                    "ORDER BY priority DESC, ticket_id")

    print("\n[2] ORDER BY CASE — 순서를 직접 매긴다 (같은 순위 안에서는 오래된 것 먼저)")
    show_rows(conn, f"""
        SELECT ticket_id, priority, created_at FROM ticket {known_only}
        ORDER BY {CASE_RANK}, created_at, ticket_id""")

    print("\n[3-1] 목록에 없는 값('later')과 NULL — ELSE 가 없으면")
    show_rows(conn, f"""
        SELECT ticket_id, priority, {CASE_RANK} AS rank_value FROM ticket
        ORDER BY {CASE_RANK}, created_at, ticket_id""")
    print("[3-2] ELSE 9 를 붙이면")
    show_rows(conn, f"""
        SELECT ticket_id, priority, {CASE_RANK_ELSE} AS rank_value FROM ticket
        ORDER BY {CASE_RANK_ELSE}, created_at, ticket_id""")
    print("[3-3] CASE 만 내림차순으로 — DESC 는 그 식 하나에만 붙는다")
    show_rows(conn, f"""
        SELECT ticket_id, priority FROM ticket
        ORDER BY {CASE_RANK} DESC, ticket_id""")

    print("\n[4-1] 순서 표 조인 — INNER JOIN 이면 표에 없는 행이 사라진다")
    show_rows(conn, """
        SELECT t.ticket_id, t.priority, r.sort_rank
        FROM ticket AS t JOIN priority_rank AS r ON r.priority = t.priority
        ORDER BY r.sort_rank, t.created_at, t.ticket_id""")
    print("[4-2] LEFT JOIN + COALESCE 로 표에 없는 값을 맨 뒤로")
    show_rows(conn, """
        SELECT t.ticket_id, t.priority, COALESCE(r.sort_rank, 9) AS sort_rank
        FROM ticket AS t LEFT JOIN priority_rank AS r ON r.priority = t.priority
        ORDER BY COALESCE(r.sort_rank, 9), t.created_at, t.ticket_id""")

    print("\n[5-1] instr() — 순서 문자열 안의 위치")
    show_rows(conn, """
        SELECT ticket_id, priority,
               instr(',high,medium,low,', ',' || priority || ',') AS pos
        FROM ticket
        ORDER BY pos, ticket_id""")
    print("[5-2] 구분자 없이 쓰면 — 'ow' 같은 값이 'low' 안에서 찾아진다")
    show_rows(conn, """
        SELECT value AS priority,
               instr('highmediumlow', value) AS pos_no_comma,
               instr(',high,medium,low,', ',' || value || ',') AS pos_with_comma
        FROM (SELECT 'low' AS value UNION ALL SELECT 'ow' UNION ALL SELECT 'dium')""")

    conn.executescript(
        "CREATE INDEX ticket_priority_created ON ticket (priority, created_at);"
    )
    print("\n[6-1] 실행계획 — 문자열 정렬은 인덱스 순서를 그대로 쓴다")
    plan(conn, "SELECT ticket_id, priority FROM ticket "
               "ORDER BY priority, created_at LIMIT 3")
    print("\n[6-2] 실행계획 — ORDER BY CASE")
    plan(conn, f"SELECT ticket_id, priority FROM ticket "
               f"ORDER BY {CASE_RANK_ELSE}, created_at LIMIT 3")
    print("\n[6-3] 실행계획 — 순서 표 LEFT JOIN")
    plan(conn, """
        SELECT t.ticket_id FROM ticket AS t
        LEFT JOIN priority_rank AS r ON r.priority = t.priority
        ORDER BY COALESCE(r.sort_rank, 9), t.created_at LIMIT 3""")

    conn.executescript(
        f"CREATE INDEX ticket_rank_created ON ticket ({CASE_RANK_ELSE}, created_at);"
    )
    print("\n[7-1] 실행계획 — 같은 CASE 식으로 식 인덱스를 만든 뒤")
    plan(conn, f"SELECT ticket_id, priority FROM ticket "
               f"ORDER BY {CASE_RANK_ELSE}, created_at LIMIT 3")
    show_rows(conn, f"SELECT ticket_id, priority FROM ticket "
                    f"ORDER BY {CASE_RANK_ELSE}, created_at LIMIT 3")
    print("\n[7-2] 실행계획 — WHEN 순서만 바꾼 같은 뜻의 CASE")
    reordered = """CASE priority
               WHEN 'medium' THEN 2
               WHEN 'high'   THEN 1
               WHEN 'low'    THEN 3
               ELSE 9
           END"""
    plan(conn, f"SELECT ticket_id, priority FROM ticket "
               f"ORDER BY {reordered}, created_at LIMIT 3")
    conn.close()


if __name__ == "__main__":
    main()
