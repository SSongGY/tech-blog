"""문자열 함수 기본 — 자르기, 붙이기, 바꾸기.

회원 표의 이름·이메일·상품 코드를 SUBSTR·LENGTH·||·REPLACE·TRIM·UPPER 로
다듬어 본다. 뒤쪽에서는 같은 함수를 WHERE 절의 컬럼 쪽에 씌웠을 때
인덱스가 쓰이는지를 EXPLAIN QUERY PLAN 으로 확인한다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

MEMBERS = [
    # (id, 이름, 이메일, 상품 코드, 메모)
    (1, "김도윤", "Doyun.Kim@Example.com", "KOR-1001", "  VIP  "),
    (2, "이서준", "seojun@example.com", "KOR-1002", "\t신규"),
    (3, "박하은", "HAEUN@example.COM", "USA-2001", None),
    (4, "최유나", "yuna@example.com", "kor-1003", "재구매"),
    (5, "Émile", "emile@example.fr", "FRA-3001", "해외"),
]

BULK_ROWS = 2000  # 실행계획이 표 크기에 흔들리지 않도록 행을 넉넉히 넣는다


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE member (
            id            INTEGER PRIMARY KEY,
            member_name   TEXT NOT NULL,
            email         TEXT NOT NULL,
            product_code  TEXT NOT NULL,
            memo          TEXT
        )
        """
    )
    conn.executemany("INSERT INTO member VALUES (?, ?, ?, ?, ?)", MEMBERS)
    conn.execute("CREATE INDEX ix_member_product_code ON member (product_code)")
    conn.execute("CREATE INDEX ix_member_email ON member (email)")
    conn.commit()
    return conn


def add_bulk_rows(conn: sqlite3.Connection) -> None:
    rows = [
        (100 + i, f"회원{i}", f"user{i}@example.com", f"JPN-{i:04d}", None)
        for i in range(BULK_ROWS)
    ]
    conn.executemany("INSERT INTO member VALUES (?, ?, ?, ?, ?)", rows)
    conn.execute("ANALYZE")
    conn.commit()


def show(conn: sqlite3.Connection, label: str, sql: str) -> None:
    print(f"\n[{label}]")
    print(f"  {' '.join(sql.split())}")
    rows = conn.execute(sql).fetchall()
    for row in rows:
        print(f"  {row!r}")
    print(f"  -> {len(rows)}행")


def plan_tree(conn: sqlite3.Connection, sql: str) -> str:
    """EXPLAIN QUERY PLAN 을 sqlite3 CLI 가 그리는 트리 모양으로 만든다."""
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    children: dict[int, list[tuple[int, str]]] = {}
    for node_id, parent_id, _, detail in rows:
        children.setdefault(parent_id, []).append((node_id, detail))
    lines = ["QUERY PLAN"]

    def walk(parent_id: int, prefix: str) -> None:
        items = children.get(parent_id, [])
        for idx, (node_id, detail) in enumerate(items):
            last = idx == len(items) - 1
            lines.append(prefix + ("`--" if last else "|--") + detail)
            walk(node_id, prefix + ("   " if last else "|  "))

    walk(0, "")
    return "\n".join("  " + line for line in lines)


def count_vm_steps(conn: sqlite3.Connection, sql: str) -> tuple[int, int]:
    """질의 한 번에 SQLite 가상 머신이 명령을 몇 개 수행했는지 센다.

    시간은 환경마다 흔들리지만 명령 수는 같은 데이터·같은 계획이면 같다.
    SCAN 과 SEARCH 가 실제로 얼마나 다른 양의 일을 하는지 보려는 것이다.
    """
    steps = 0

    def tick() -> int:
        nonlocal steps
        steps += 1
        return 0

    conn.set_progress_handler(tick, 1)
    rows = conn.execute(sql).fetchall()
    conn.set_progress_handler(None, 1)
    return len(rows), steps


def show_plan(conn: sqlite3.Connection, label: str, sql: str) -> None:
    count, steps = count_vm_steps(conn, sql)
    print(f"\n[{label}]  결과 {count}행 · VM 명령 {steps:,}개")
    print(f"  {' '.join(sql.split())}")
    print(plan_tree(conn, sql))


def section_cut(conn: sqlite3.Connection) -> None:
    print("\n== 1. 자르기 — SUBSTR, LENGTH, INSTR ==")
    show(conn, "1-A 상품 코드 앞 3자리와 하이픈 뒤", """
        SELECT product_code,
               SUBSTR(product_code, 1, 3)  AS country,
               SUBSTR(product_code, 5)     AS serial
        FROM member ORDER BY id
    """)
    show(conn, "1-B 음수 시작 위치 — 뒤에서부터 센다", """
        SELECT product_code, SUBSTR(product_code, -4), SUBSTR(product_code, -4, 2)
        FROM member WHERE id <= 2
    """)
    show(conn, "1-C 이메일에서 @ 앞뒤 나누기", """
        SELECT email,
               INSTR(email, '@')                       AS at_pos,
               SUBSTR(email, 1, INSTR(email, '@') - 1) AS local_part,
               SUBSTR(email, INSTR(email, '@') + 1)    AS domain
        FROM member ORDER BY id
    """)
    show(conn, "1-D LENGTH — 글자 수인가 바이트 수인가", """
        SELECT member_name,
               LENGTH(member_name)            AS chars,
               LENGTH(CAST(member_name AS BLOB)) AS utf8_bytes
        FROM member ORDER BY id
    """)


def section_join(conn: sqlite3.Connection) -> None:
    print("\n== 2. 붙이기 — ||, CONCAT, CONCAT_WS ==")
    show(conn, "2-A || 로 이름과 메모 잇기", """
        SELECT id, member_name || ' / ' || memo FROM member ORDER BY id
    """)
    show(conn, "2-B CONCAT 으로 같은 일", """
        SELECT id, CONCAT(member_name, ' / ', memo) FROM member ORDER BY id
    """)
    show(conn, "2-C CONCAT_WS — 구분자를 한 번만 쓰고 NULL 은 건너뛴다", """
        SELECT id, CONCAT_WS(' / ', member_name, memo, product_code)
        FROM member ORDER BY id
    """)


def section_replace(conn: sqlite3.Connection) -> None:
    print("\n== 3. 바꾸기 — REPLACE, TRIM, UPPER/LOWER ==")
    show(conn, "3-A REPLACE — 대소문자를 구분한다", """
        SELECT email,
               REPLACE(email, 'example.com', 'example.net') AS moved
        FROM member ORDER BY id
    """)
    show(conn, "3-B TRIM — 기본은 공백만 지운다", """
        SELECT id, '[' || memo || ']', '[' || TRIM(memo) || ']',
               '[' || TRIM(memo, ' ' || CHAR(9)) || ']'
        FROM member WHERE id IN (1, 2)
    """)
    show(conn, "3-C UPPER/LOWER — ASCII 밖의 글자는 그대로", """
        SELECT member_name, UPPER(member_name), LOWER(member_name),
               LOWER(email)
        FROM member ORDER BY id
    """)


def section_index(conn: sqlite3.Connection) -> None:
    print("\n== 4. WHERE 절의 함수와 인덱스 ==")
    add_bulk_rows(conn)
    print(f"  (JPN- 코드 회원 {BULK_ROWS}행을 더 넣고 ANALYZE 했다)")
    show_plan(conn, "4-A 컬럼에 SUBSTR 을 씌운 조건", """
        SELECT id FROM member WHERE SUBSTR(product_code, 1, 3) = 'KOR'
    """)
    show_plan(conn, "4-B LIKE 'KOR%'", """
        SELECT id FROM member WHERE product_code LIKE 'KOR%'
    """)
    show_plan(conn, "4-C 범위 조건으로 바꿔 쓴 접두 검색", """
        SELECT id FROM member
        WHERE product_code >= 'KOR' AND product_code < 'KOS'
    """)
    show_plan(conn, "4-D GLOB 'KOR*'", """
        SELECT id FROM member WHERE product_code GLOB 'KOR*'
    """)
    show_plan(conn, "4-E 컬럼에 LOWER 를 씌운 이메일 검색", """
        SELECT id FROM member WHERE LOWER(email) = 'haeun@example.com'
    """)
    conn.execute("CREATE INDEX ix_member_lower_email ON member (LOWER(email))")
    show_plan(conn, "4-F 식 인덱스 LOWER(email) 을 만든 뒤 같은 질의", """
        SELECT id FROM member WHERE LOWER(email) = 'haeun@example.com'
    """)
    show_plan(conn, "4-G 식 인덱스는 그대로 두고 UPPER 로 찾으면", """
        SELECT id FROM member WHERE UPPER(email) = 'HAEUN@EXAMPLE.COM'
    """)


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)
    section_cut(conn)
    section_join(conn)
    section_replace(conn)
    section_index(conn)


if __name__ == "__main__":
    main()
