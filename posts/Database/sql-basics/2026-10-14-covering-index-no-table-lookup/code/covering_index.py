"""커버링 인덱스 — 표를 안 보고 인덱스만으로 끝나는 경우를 확인한다.

확인하는 것은 네 가지다.

1. 실행계획에 `USING COVERING INDEX` 가 언제 뜨고 언제 안 뜨는가
2. SELECT 에 컬럼 하나를 더하면 그 표시가 어떻게 되는가
3. 커버링이 되는 것과 안 되는 것의 소요 시간 차이
4. 컬럼을 하나 더 넣은 인덱스가 디스크를 얼마나 더 쓰는가

측정 시간과 페이지 수는 기계와 SQLite 판에 따라 흔들린다.
같아야 하는 것은 실행계획 문자열과 결과 행이다.
"""

from __future__ import annotations

import pathlib
import sqlite3
import statistics
import time
import unicodedata

from dbshow import print_environment, print_table

DB_PATH = pathlib.Path(__file__).with_name("covering.db")
BIG_ROWS = 100_000
REPEAT = 7
PAGE_SIZE = 4096

RULE = "=" * 68

SCHEMA = """
CREATE TABLE member (
    id        INTEGER PRIMARY KEY,
    email     TEXT NOT NULL,
    signup_at TEXT NOT NULL,
    nickname  TEXT NOT NULL,
    bio       TEXT NOT NULL
)
"""

# 범위 조회 + 집계. 행 하나만 집으면 표를 보러 가는 비용이 묻혀서 안 보인다.
RANGE_SQL = """
SELECT COUNT(*), MIN(signup_at), MAX(signup_at)
  FROM member
 WHERE email BETWEEN ? AND ?
"""

RANGE_ARGS = ("user_020000@example.com", "user_060000@example.com")


def pad(text: str, width: int) -> str:
    """한글은 터미널에서 두 칸을 차지한다. 그대로 len 으로 재면 표가 어긋난다."""
    used = sum(
        2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text
    )
    return text + " " * max(0, width - used)


def build(conn: sqlite3.Connection, rows: int, bio_len: int = 120) -> None:
    conn.execute(f"PRAGMA page_size = {PAGE_SIZE}")
    conn.executescript(SCHEMA)
    conn.executemany(
        "INSERT INTO member VALUES (?, ?, ?, ?, ?)",
        [
            (
                i,
                f"user_{i:06d}@example.com",
                f"2024-{i % 12 + 1:02d}-{i % 28 + 1:02d}",
                f"닉네임{i}",
                # 본문이 길어야 표가 인덱스보다 훨씬 커진다. 실제 회원 표에 가깝다.
                f"자기소개 {i} " + "가" * bio_len,
            )
            for i in range(1, rows + 1)
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


def median_ms(conn: sqlite3.Connection, sql: str, params: tuple) -> tuple[float, list]:
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


def part1_plans(conn: sqlite3.Connection) -> None:
    print(RULE)
    print("1. 같은 인덱스에 질의만 바꾼다 — 어디서 COVERING 이 사라지는가")
    print(RULE)
    print("인덱스: CREATE INDEX idx_email ON member(email)\n")

    cases = [
        ("SELECT email FROM member WHERE email = ?",
         "인덱스에 있는 컬럼만 고른다"),
        ("SELECT id, email FROM member WHERE email = ?",
         "id 는 INTEGER PRIMARY KEY — 인덱스 항목이 이미 갖고 있다"),
        ("SELECT signup_at FROM member WHERE email = ?",
         "인덱스에 없는 컬럼을 하나 더했다"),
        ("SELECT COUNT(*) FROM member WHERE email BETWEEN ? AND ?",
         "세기만 한다 — 표를 볼 일이 없다"),
    ]
    for sql, note in cases:
        params = RANGE_ARGS if "BETWEEN" in sql else (RANGE_ARGS[0],)
        print(f"{sql}\n  ({note})")
        show_plan(conn, sql, params)
        print()


def part2_timing() -> None:
    print(RULE)
    print(f"2. {BIG_ROWS:,}행 범위 집계 — 인덱스 구성만 바꿔 잰다")
    print(RULE)
    print("질의: SELECT COUNT(*), MIN(signup_at), MAX(signup_at)")
    print("        FROM member WHERE email BETWEEN ? AND ?")
    print(f"      (같은 질의를 {REPEAT}번 돌린 중앙값)\n")

    DB_PATH.unlink(missing_ok=True)
    conn = sqlite3.connect(DB_PATH)
    build(conn, BIG_ROWS)

    base_pages = page_count(conn)
    print(f"인덱스 없는 상태의 DB 페이지 수: {base_pages:,}"
          f"  ({base_pages * PAGE_SIZE / 1024 / 1024:.1f} MB)\n")

    print(f"{pad('인덱스', 26)} {'소요':>8} {'늘어난 페이지':>12}  실행계획")
    print("-" * 104)

    results = []
    for label, ddl in (
        ("(없음)", None),
        ("member(email)", "CREATE INDEX idx_e ON member(email)"),
        ("member(email, signup_at)",
         "CREATE INDEX idx_es ON member(email, signup_at)"),
    ):
        if ddl:
            conn.execute(ddl)
            conn.commit()
        pages = page_count(conn)
        elapsed, rows = median_ms(conn, RANGE_SQL, RANGE_ARGS)
        detail = plan_of(conn, RANGE_SQL, RANGE_ARGS)[0]
        added = pages - base_pages
        print(
            f"{pad(label, 26)} {elapsed:6.2f}ms {added:>10,}쪽  {detail}"
        )
        results.append(rows)
        if ddl:
            conn.execute(f"DROP INDEX {ddl.split()[2]}")
            conn.commit()

    print()
    print(f"세 경우의 결과 행이 모두 같은가: "
          f"{results[0] == results[1] == results[2]}")
    print(f"결과: {results[0]}")
    conn.close()


def part3_small(conn: sqlite3.Connection) -> None:
    print(RULE)
    print("0. 예제가 쓰는 표")
    print(RULE)
    print_table(conn, "member", max_rows=6)


def main() -> None:
    print_environment()

    # 작은 표는 눈으로 읽어야 하므로 bio 를 짧게 만든다. 측정용 표는 120자다.
    small = sqlite3.connect(":memory:")
    build(small, 12, bio_len=6)
    small.execute("CREATE INDEX idx_email ON member(email)")
    small.commit()
    part3_small(small)
    part1_plans(small)

    part2_timing()


if __name__ == "__main__":
    main()
