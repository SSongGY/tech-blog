"""UNION과 UNION ALL — 중복 제거가 무엇을 비교하고 얼마를 치르는지 본다.

온라인 회원 표와 매장 회원 표를 합쳐 안내 메일 명단을 만든다. 두 표에 같은 사람이
겹쳐 있고, 한 표 안에도 중복이 있고, 이메일이 비어 있는 행도 있다. 같은 두 표를
UNION과 UNION ALL로 합쳐 행 수와 실행계획을 비교하고, 행을 늘려 시간을 잰다.
"""

import random
import sqlite3
import time

from dbshow import print_dataset, print_environment

ONLINE_MEMBERS = [
    (1, "kim@example.com", "김도윤"),
    (2, "lee@example.com", "이서준"),
    (3, "park@example.com", "박하은"),
    (4, "lee@example.com", "이서준"),  # 같은 사람이 두 번 가입했다
    (5, None, "최유나"),
]

# 매장 회원은 온라인과 번호 체계가 다르다. 이메일만 겹친다
STORE_MEMBERS = [
    (901, "park@example.com", "박하은"),
    (902, "jung@example.com", "정민호"),
    (903, "kim@example.com", "김도윤 "),  # 이름 뒤에 공백이 붙은 채 입력됐다
    (904, None, "최유나"),
]

TIMING_ROWS = 200_000
TIMING_OVERLAP = 0.5  # 매장 회원의 절반은 온라인 회원과 같은 이메일을 쓴다


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE online_member (
            id    INTEGER PRIMARY KEY,
            email TEXT,
            name  TEXT NOT NULL
        );
        CREATE TABLE store_member (
            id    INTEGER PRIMARY KEY,
            email TEXT,
            name  TEXT NOT NULL
        );
        """
    )
    conn.executemany("INSERT INTO online_member VALUES (?, ?, ?)", ONLINE_MEMBERS)
    conn.executemany("INSERT INTO store_member VALUES (?, ?, ?)", STORE_MEMBERS)
    conn.commit()
    return conn


def show(conn: sqlite3.Connection, label: str, sql: str) -> None:
    print(f"\n[{label}]")
    print(f"  {' '.join(sql.split())}")
    try:
        rows = conn.execute(sql).fetchall()
    except sqlite3.Error as exc:
        print(f"  에러: {type(exc).__name__}: {exc}")
        return
    for row in rows:
        print(f"  {row}")
    print(f"  -> {len(rows)}행")


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


def section_rows(conn: sqlite3.Connection) -> None:
    print("\n== 1. 두 표를 합친 결과 ==")
    show(conn, "1-A UNION ALL (이메일만)", """
        SELECT email FROM online_member
        UNION ALL
        SELECT email FROM store_member""")
    show(conn, "1-B UNION (이메일만)", """
        SELECT email FROM online_member
        UNION
        SELECT email FROM store_member""")
    show(conn, "1-C UNION (이메일, 이름)", """
        SELECT email, name FROM online_member
        UNION
        SELECT email, name FROM store_member""")


def section_rules(conn: sqlite3.Connection) -> None:
    print("\n== 2. 합칠 때의 규칙 ==")
    show(conn, "2-A 한쪽 표 안의 중복도 지운다", """
        SELECT email FROM online_member WHERE email = 'lee@example.com'
        UNION
        SELECT email FROM store_member WHERE 0""")
    show(conn, "2-B 컬럼 이름은 첫 SELECT 를 따른다", """
        SELECT email AS contact FROM online_member WHERE id = 1
        UNION ALL
        SELECT name FROM store_member WHERE id = 902""")
    cursor = conn.execute("""
        SELECT email AS contact FROM online_member WHERE id = 1
        UNION ALL
        SELECT name FROM store_member WHERE id = 902""")
    print(f"  컬럼 이름: {[d[0] for d in cursor.description]}")
    show(conn, "2-C 컬럼 수가 다르면", """
        SELECT email, name FROM online_member
        UNION
        SELECT email FROM store_member""")
    show(conn, "2-D ORDER BY 는 합친 결과 전체에 한 번", """
        SELECT email FROM online_member
        UNION
        SELECT email FROM store_member
        ORDER BY email DESC""")


def section_plans(conn: sqlite3.Connection) -> None:
    print("\n== 3. 실행계획 ==")
    show_plan(conn, "3-A UNION ALL", """
        SELECT email FROM online_member
        UNION ALL
        SELECT email FROM store_member""")
    show_plan(conn, "3-B UNION", """
        SELECT email FROM online_member
        UNION
        SELECT email FROM store_member""")


def build_timing_database(row_count: int) -> sqlite3.Connection:
    rng = random.Random(42)
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE online_member (id INTEGER PRIMARY KEY, email TEXT, name TEXT);
        CREATE TABLE store_member  (id INTEGER PRIMARY KEY, email TEXT, name TEXT);
        """
    )
    online = [(i, f"user{i}@example.com", f"회원{i}") for i in range(row_count)]
    store = []
    for i in range(row_count):
        if rng.random() < TIMING_OVERLAP:
            email = f"user{rng.randrange(row_count)}@example.com"
        else:
            email = f"store{i}@example.com"
        store.append((i, email, f"매장{i}"))
    conn.executemany("INSERT INTO online_member VALUES (?, ?, ?)", online)
    conn.executemany("INSERT INTO store_member VALUES (?, ?, ?)", store)
    conn.commit()
    return conn


def measure(conn: sqlite3.Connection, sql: str, repeat: int = 5) -> tuple[int, float]:
    # 가장 빠른 회를 쓴다. 느린 회는 다른 프로세스의 간섭일 가능성이 크다
    best = float("inf")
    row_count = 0
    for _ in range(repeat):
        started = time.perf_counter()
        row_count = len(conn.execute(sql).fetchall())
        best = min(best, time.perf_counter() - started)
    return row_count, best * 1000


def section_timing() -> None:
    print(f"\n== 4. 시간 — 표마다 {TIMING_ROWS:,}행, 5회 중 최솟값 ==")
    conn = build_timing_database(TIMING_ROWS)
    cases = [
        ("UNION ALL", "SELECT email FROM online_member UNION ALL SELECT email FROM store_member"),
        ("UNION    ", "SELECT email FROM online_member UNION SELECT email FROM store_member"),
    ]
    for label, sql in cases:
        row_count, elapsed_ms = measure(conn, sql)
        print(f"  {label}  {row_count:>7,}행  {elapsed_ms:7.1f} ms")


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)
    section_rows(conn)
    section_rules(conn)
    section_plans(conn)
    section_timing()


if __name__ == "__main__":
    main()
