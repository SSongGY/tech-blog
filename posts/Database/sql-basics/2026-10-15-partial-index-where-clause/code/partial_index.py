"""부분 인덱스(partial index) — 인덱스에 WHERE 를 붙여 일부 행만 색인한다.

같은 질의를 세 상태(인덱스 없음 / 전체 인덱스 / 부분 인덱스)에서 각각 재고,
인덱스가 차지하는 페이지 수를 함께 찍는다. 뒤이어 부분 인덱스가 **안 쓰이는**
질의 모양을 모아 실행계획으로 확인하고, 마지막으로 UNIQUE 부분 인덱스가
소프트 삭제에 어떻게 쓰이는지 본다.

난수를 쓰지 않는다. 200,000 행 중 id 가 100 의 배수인 행만 'pending' 이므로
몇 번을 돌려도 같은 데이터가 나온다.
"""

from __future__ import annotations

import os
import sqlite3
import statistics
import time

from dbshow import print_dataset, print_environment, print_table

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "partial.db")

ROWS = 200_000
PENDING_EVERY = 100          # 100 행에 1 행만 미처리 — 전형적인 작업 큐 분포
REPEAT = 9
RULE = "=" * 64

LIST_PENDING = """
SELECT id, customer_id, ordered_at
  FROM order_tbl
 WHERE status = 'pending'
 ORDER BY ordered_at
 LIMIT 20
"""


def build(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE order_tbl (
            id          INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            status      TEXT    NOT NULL,
            amount      INTEGER NOT NULL,
            ordered_at  TEXT    NOT NULL
        );
        """
    )
    conn.executemany(
        "INSERT INTO order_tbl VALUES (?, ?, ?, ?, ?)",
        [
            (
                i,
                i % 5000 + 1,
                "pending" if i % PENDING_EVERY == 0 else "done",
                (i * 37) % 90000 + 1000,
                # 날짜를 고르게 흩어 놔야 ORDER BY 가 정렬을 실제로 하게 된다
                f"2026-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
            )
            for i in range(1, ROWS + 1)
        ],
    )
    conn.commit()


def plan_of(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[str]:
    return [row[3] for row in conn.execute("EXPLAIN QUERY PLAN " + sql, params)]


def show_plan(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> None:
    details = plan_of(conn, sql, params)
    print("QUERY PLAN")
    for i, detail in enumerate(details):
        print(f"{'`--' if i == len(details) - 1 else '|--'}{detail}")


def median_ms(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> tuple[float, list]:
    samples = []
    rows: list = []
    for _ in range(REPEAT):
        start = time.perf_counter()
        rows = conn.execute(sql, params).fetchall()
        samples.append((time.perf_counter() - start) * 1000)
    return statistics.median(samples), rows


def page_count(conn: sqlite3.Connection) -> int:
    conn.execute("VACUUM")          # 지운 자리를 돌려줘야 증감이 그대로 보인다
    return conn.execute("PRAGMA page_count").fetchone()[0]


def drop_indexes(conn: sqlite3.Connection) -> None:
    for (name,) in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"
    ).fetchall():
        conn.execute(f"DROP INDEX {name}")
    conn.commit()


def part1_size_and_speed(conn: sqlite3.Connection) -> None:
    print(RULE)
    print("1. 인덱스 없음 / 전체 인덱스 / 부분 인덱스 — 크기와 속도")
    print(RULE)

    page_size = conn.execute("PRAGMA page_size").fetchone()[0]
    print(f"페이지 크기 {page_size} 바이트\n")

    base = page_count(conn)
    print(f"[인덱스 없음]  표만 있을 때 {base} 페이지")
    show_plan(conn, LIST_PENDING)
    none_ms, rows = median_ms(conn, LIST_PENDING)
    print(f"중앙값 {none_ms:.2f} ms · {len(rows)}행 반환\n")

    conn.execute("CREATE INDEX idx_full ON order_tbl(status, ordered_at)")
    conn.commit()
    full = page_count(conn)
    print(f"[전체 인덱스]  CREATE INDEX idx_full ON order_tbl(status, ordered_at)")
    print(f"  {full} 페이지 — 인덱스 몫 {full - base} 페이지 "
          f"({(full - base) * page_size / 1024:.0f} KB)")
    show_plan(conn, LIST_PENDING)
    full_ms, _ = median_ms(conn, LIST_PENDING)
    print(f"중앙값 {full_ms:.2f} ms\n")

    drop_indexes(conn)
    conn.execute(
        "CREATE INDEX idx_pending ON order_tbl(ordered_at) WHERE status = 'pending'"
    )
    conn.commit()
    part = page_count(conn)
    print("[부분 인덱스]  CREATE INDEX idx_pending ON order_tbl(ordered_at)"
          " WHERE status = 'pending'")
    print(f"  {part} 페이지 — 인덱스 몫 {part - base} 페이지 "
          f"({(part - base) * page_size / 1024:.0f} KB)")
    show_plan(conn, LIST_PENDING)
    part_ms, _ = median_ms(conn, LIST_PENDING)
    print(f"중앙값 {part_ms:.2f} ms\n")

    total = conn.execute("SELECT COUNT(*) FROM order_tbl").fetchone()[0]
    pending = conn.execute(
        "SELECT COUNT(*) FROM order_tbl WHERE status = 'pending'"
    ).fetchone()[0]
    print(f"색인 대상 행   전체 {total} 중 {pending} ({pending / total:.1%})")
    print(f"인덱스 페이지  전체 {full - base} → 부분 {part - base} "
          f"({(part - base) / (full - base):.1%})")
    print(f"질의 중앙값    없음 {none_ms:.2f} ms · 전체 {full_ms:.2f} ms "
          f"· 부분 {part_ms:.2f} ms\n")


def part2_when_unused(conn: sqlite3.Connection) -> None:
    print(RULE)
    print("2. 같은 부분 인덱스에 질의만 바꾼다 — 언제 안 쓰이는가")
    print(RULE)
    print("인덱스: CREATE INDEX idx_pending ON order_tbl(ordered_at)"
          " WHERE status = 'pending'\n")

    cases: list[tuple[str, str, tuple]] = [
        (
            "조건에 리터럴 'pending' 을 그대로 쓴다",
            "SELECT id FROM order_tbl WHERE status = 'pending' ORDER BY ordered_at",
            (),
        ),
        (
            "같은 조건을 바인딩 파라미터로 넘긴다",
            "SELECT id FROM order_tbl WHERE status = ? ORDER BY ordered_at",
            ("pending",),
        ),
        (
            "AND 로 다른 조건이 더 붙는다",
            "SELECT id FROM order_tbl WHERE status = 'pending' AND amount > 50000",
            (),
        ),
        (
            "OR 로 다른 상태를 함께 찾는다",
            "SELECT id FROM order_tbl WHERE status = 'pending' OR status = 'done'",
            (),
        ),
        (
            "IN 으로 하나만 적는다",
            "SELECT id FROM order_tbl WHERE status IN ('pending')",
            (),
        ),
        (
            "색인 밖의 상태를 찾는다",
            "SELECT id FROM order_tbl WHERE status = 'done' ORDER BY ordered_at",
            (),
        ),
        (
            "상태 조건이 아예 없다",
            "SELECT id FROM order_tbl ORDER BY ordered_at",
            (),
        ),
    ]

    for label, sql, params in cases:
        used = any("idx_pending" in d for d in plan_of(conn, sql, params))
        print(f"{label}  →  {'쓴다' if used else '안 쓴다'}")
        print("  " + " ".join(sql.split()))
        for line in plan_of(conn, sql, params):
            print(f"    {line}")
        print()


def part3_unique_partial(conn: sqlite3.Connection) -> None:
    print(RULE)
    print("3. UNIQUE 부분 인덱스 — 살아 있는 행에만 유일성을 건다")
    print(RULE)
    conn.executescript(
        """
        CREATE TABLE member (
            id         INTEGER PRIMARY KEY,
            email      TEXT NOT NULL,
            deleted_at TEXT
        );
        CREATE UNIQUE INDEX idx_live_email
            ON member(email) WHERE deleted_at IS NULL;
        """
    )
    print("CREATE UNIQUE INDEX idx_live_email ON member(email)"
          " WHERE deleted_at IS NULL\n")

    steps = [
        ("가입",
         "INSERT INTO member VALUES (1, 'a@example.com', NULL)"),
        ("같은 주소로 또 가입 — 막혀야 한다",
         "INSERT INTO member VALUES (2, 'a@example.com', NULL)"),
        ("1번을 탈퇴 처리 (행은 남긴다)",
         "UPDATE member SET deleted_at = '2026-10-15' WHERE id = 1"),
        ("같은 주소로 재가입 — 이제 통과해야 한다",
         "INSERT INTO member VALUES (3, 'a@example.com', NULL)"),
        ("탈퇴한 행이 둘이 돼도 상관없다",
         "INSERT INTO member VALUES (4, 'a@example.com', '2026-10-15')"),
    ]
    for label, sql in steps:
        try:
            conn.execute(sql)
            conn.commit()
            print(f"[성공] {label}")
        except sqlite3.IntegrityError as exc:
            conn.rollback()
            print(f"[거부] {label}")
            print(f"       sqlite3.IntegrityError: {exc}")
    print()
    print_table(conn, "member")


def main() -> None:
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    build(conn)

    print_environment()
    print_dataset(conn)

    part1_size_and_speed(conn)
    part2_when_unused(conn)
    part3_unique_partial(conn)
    conn.close()


if __name__ == "__main__":
    main()
