"""OFFSET 페이지네이션과 키셋 페이지네이션을 같은 데이터에서 비교한다.

확인하는 것은 네 가지다.

1. 두 방식이 같은 페이지를 돌려주는가
2. 페이지를 넘기는 사이 앞쪽에 행이 들어오면 무엇이 달라지는가
3. 페이지가 깊어질수록 걸리는 시간이 어떻게 변하는가
4. 실행계획에서 무엇이 달라지는가 (SCAN 인가 SEARCH 인가)

측정 시간은 기계마다 다르다. 같아야 하는 것은 실행계획과 결과 행이다.
"""

from __future__ import annotations

import sqlite3
import statistics
import time

from dbshow import print_dataset, print_environment

PAGE_SIZE = 4           # 작은 표에서 눈으로 따라갈 수 있는 크기
BIG_ROWS = 200_000      # 깊은 페이지를 만들려면 이 정도는 있어야 한다
BIG_PAGE = 20
REPEAT = 7              # 중앙값을 쓴다. 한 번만 재면 첫 호출의 캐시 효과가 섞인다

RULE = "=" * 64


def build_small() -> sqlite3.Connection:
    """눈으로 셀 수 있는 12행짜리 글 목록."""
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE article (
            id        INTEGER PRIMARY KEY,
            posted_at TEXT NOT NULL,
            title     TEXT NOT NULL
        )
        """
    )
    # 같은 시각에 올라온 글을 일부러 섞는다. 정렬키가 유일하지 않을 때
    # 무슨 일이 생기는지가 이 글의 핵심 중 하나다.
    rows = [
        (1, "2026-10-01 09:00", "인덱스 첫 글"),
        (2, "2026-10-01 09:00", "인덱스 둘째 글"),
        (3, "2026-10-02 11:30", "트랜잭션 격리"),
        (4, "2026-10-03 08:15", "조인 순서"),
        (5, "2026-10-04 17:40", "실행계획 읽기"),
        (6, "2026-10-05 10:05", "통계 수집"),
        (7, "2026-10-06 13:20", "부분 인덱스"),
        (8, "2026-10-07 21:00", "커버링 인덱스"),
        (9, "2026-10-08 07:45", "윈도 함수"),
        (10, "2026-10-09 15:10", "재귀 CTE"),
        (11, "2026-10-10 12:00", "UPSERT"),
        (12, "2026-10-11 19:25", "트리거"),
    ]
    conn.executemany("INSERT INTO article VALUES (?, ?, ?)", rows)
    conn.execute(
        "CREATE INDEX idx_article_posted ON article(posted_at DESC, id DESC)"
    )
    conn.commit()
    return conn


def build_big() -> sqlite3.Connection:
    """깊은 페이지를 만들기 위한 20만 행."""
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE article (
            id        INTEGER PRIMARY KEY,
            posted_at TEXT NOT NULL,
            title     TEXT NOT NULL
        )
        """
    )
    # 하루에 100건씩 쌓인 목록. 같은 분에 올라온 글이 여럿 생기도록 만든다.
    rows = [
        (
            i,
            f"2020-01-01 {i // 3600 % 24:02d}:{i // 60 % 60:02d}",
            f"글 {i}",
        )
        for i in range(1, BIG_ROWS + 1)
    ]
    conn.executemany("INSERT INTO article VALUES (?, ?, ?)", rows)
    conn.execute(
        "CREATE INDEX idx_article_posted ON article(posted_at DESC, id DESC)"
    )
    conn.commit()
    return conn


def median_ms(conn: sqlite3.Connection, sql: str, params: tuple) -> tuple[float, list]:
    """같은 질의를 REPEAT 번 돌려 중앙값(ms)과 마지막 결과를 돌려준다."""
    samples = []
    rows: list = []
    for _ in range(REPEAT):
        start = time.perf_counter()
        rows = conn.execute(sql, params).fetchall()
        samples.append((time.perf_counter() - start) * 1000)
    return statistics.median(samples), rows


def show_plan(conn: sqlite3.Connection, sql: str, params: tuple) -> None:
    """sqlite3 CLI 가 그리는 트리 모양 그대로 찍는다."""
    plan = conn.execute("EXPLAIN QUERY PLAN " + sql, params).fetchall()
    print("QUERY PLAN")
    for i, (_node, _parent, _aux, detail) in enumerate(plan):
        branch = "`--" if i == len(plan) - 1 else "|--"
        print(f"{branch}{detail}")
    print()


OFFSET_SQL = """
SELECT id, posted_at, title
  FROM article
 ORDER BY posted_at DESC, id DESC
 LIMIT ? OFFSET ?
"""

KEYSET_SQL = """
SELECT id, posted_at, title
  FROM article
 WHERE (posted_at, id) < (?, ?)
 ORDER BY posted_at DESC, id DESC
 LIMIT ?
"""

KEYSET_SQL_OR = """
SELECT id, posted_at, title
  FROM article
 WHERE posted_at < ?
    OR (posted_at = ? AND id < ?)
 ORDER BY posted_at DESC, id DESC
 LIMIT ?
"""


def part1_same_page(conn: sqlite3.Connection) -> None:
    print(RULE)
    print("1. 같은 2페이지를 두 가지 방법으로 읽는다")
    print(RULE)

    page1 = conn.execute(OFFSET_SQL, (PAGE_SIZE, 0)).fetchall()
    print(f"1페이지 (OFFSET 0 LIMIT {PAGE_SIZE})")
    for row in page1:
        print(f"  {row}")
    last_posted_at, last_id = page1[-1][1], page1[-1][0]
    print(f"  → 마지막 행의 커서: posted_at={last_posted_at!r}, id={last_id}\n")

    by_offset = conn.execute(OFFSET_SQL, (PAGE_SIZE, PAGE_SIZE)).fetchall()
    print(f"2페이지 — OFFSET {PAGE_SIZE} LIMIT {PAGE_SIZE}")
    for row in by_offset:
        print(f"  {row}")
    print()

    by_keyset = conn.execute(
        KEYSET_SQL, (last_posted_at, last_id, PAGE_SIZE)
    ).fetchall()
    print(f"2페이지 — 키셋 (posted_at, id) < ({last_posted_at!r}, {last_id})")
    for row in by_keyset:
        print(f"  {row}")
    print()
    print(f"두 결과가 같은가: {by_offset == by_keyset}\n")

    by_or = conn.execute(
        KEYSET_SQL_OR, (last_posted_at, last_posted_at, last_id, PAGE_SIZE)
    ).fetchall()
    print(f"행 값 비교 대신 OR 로 풀어 쓴 결과도 같은가: {by_or == by_keyset}\n")


def part2_shifting(conn: sqlite3.Connection) -> None:
    print(RULE)
    print("2. 1페이지를 읽은 뒤 2페이지를 읽기 전에 새 글이 올라오면")
    print(RULE)

    page1 = conn.execute(OFFSET_SQL, (PAGE_SIZE, 0)).fetchall()
    last_posted_at, last_id = page1[-1][1], page1[-1][0]
    print("1페이지를 읽은 직후 — 독자가 본 id:", [r[0] for r in page1])

    conn.execute(
        "INSERT INTO article VALUES (?, ?, ?)",
        (99, "2026-10-12 08:00", "방금 올라온 글"),
    )
    conn.commit()
    print("그 사이 id=99 가 목록 맨 앞에 들어왔다.\n")

    by_offset = conn.execute(OFFSET_SQL, (PAGE_SIZE, PAGE_SIZE)).fetchall()
    by_keyset = conn.execute(
        KEYSET_SQL, (last_posted_at, last_id, PAGE_SIZE)
    ).fetchall()

    seen = {r[0] for r in page1}
    offset_ids = [r[0] for r in by_offset]
    keyset_ids = [r[0] for r in by_keyset]
    print(f"2페이지 — OFFSET {PAGE_SIZE}: {offset_ids}")
    print(f"           1페이지와 겹치는 id: {sorted(seen & set(offset_ids))}")
    print(f"2페이지 — 키셋          : {keyset_ids}")
    print(f"           1페이지와 겹치는 id: {sorted(seen & set(keyset_ids))}")
    print()

    conn.execute("DELETE FROM article WHERE id = 99")
    conn.commit()


def part3_depth(conn: sqlite3.Connection) -> None:
    print(RULE)
    print(f"3. {BIG_ROWS:,}행에서 페이지 깊이에 따른 소요 시간")
    print(RULE)
    print(f"   한 페이지 {BIG_PAGE}행, 같은 질의를 {REPEAT}번 돌린 중앙값(ms)\n")

    print("  건너뛴 행 |    OFFSET | 키셋(행 값) |  키셋(OR) | 세 결과가 같은가")
    print("  ----------+-----------+-------------+-----------+-----------------")
    for skip in (0, 1_000, 10_000, 50_000, 100_000, BIG_ROWS - BIG_PAGE):
        offset_ms, offset_rows = median_ms(conn, OFFSET_SQL, (BIG_PAGE, skip))

        # 키셋은 그 페이지 바로 앞 행의 값을 커서로 쓴다.
        if skip == 0:
            cursor = ("9999-99-99", 1 << 62)   # 어떤 값보다도 큰 커서
        else:
            prev = conn.execute(OFFSET_SQL, (1, skip - 1)).fetchone()
            cursor = (prev[1], prev[0])
        keyset_ms, keyset_rows = median_ms(
            conn, KEYSET_SQL, (cursor[0], cursor[1], BIG_PAGE)
        )
        or_ms, or_rows = median_ms(
            conn, KEYSET_SQL_OR, (cursor[0], cursor[0], cursor[1], BIG_PAGE)
        )

        same = offset_rows == keyset_rows == or_rows
        print(
            f"  {skip:9,} | {offset_ms:7.2f}ms | {keyset_ms:9.2f}ms |"
            f" {or_ms:6.2f}ms | {same}"
        )
    print()


def part4_plans(conn: sqlite3.Connection) -> None:
    print(RULE)
    print("4. 실행계획 — 같은 인덱스를 쓰는데 하는 일이 다르다")
    print(RULE)

    print("OFFSET 방식")
    show_plan(conn, OFFSET_SQL, (BIG_PAGE, 100_000))

    print("키셋 방식 (행 값 비교)")
    show_plan(conn, KEYSET_SQL, ("2020-01-01 12:00", 100_000, BIG_PAGE))

    print("키셋 방식 (OR 로 풀어 쓴 것)")
    show_plan(
        conn, KEYSET_SQL_OR,
        ("2020-01-01 12:00", "2020-01-01 12:00", 100_000, BIG_PAGE),
    )


def part5_unstable_sort(conn: sqlite3.Connection) -> None:
    print(RULE)
    print("5. 정렬키가 유일하지 않으면 — id 를 떼면 무슨 일이 생기는가")
    print(RULE)

    dup = conn.execute(
        "SELECT posted_at, COUNT(*) FROM article "
        "GROUP BY posted_at HAVING COUNT(*) > 1"
    ).fetchall()
    print(f"같은 posted_at 을 가진 묶음: {dup}\n")

    unstable = """
    SELECT id, posted_at FROM article
     WHERE posted_at < ?
     ORDER BY posted_at DESC
     LIMIT ?
    """
    print("커서를 posted_at 하나로만 잡고 '< 커서' 로 다음 페이지를 읽으면")
    rows = conn.execute(unstable, ("2026-10-01 09:00", 5)).fetchall()
    print(f"  posted_at < '2026-10-01 09:00' → {rows}")
    print("  같은 시각의 id=1, id=2 가 통째로 사라진다.\n")

    print("'<=' 로 바꾸면 이번에는 이미 본 행이 다시 나온다")
    rows = conn.execute(
        unstable.replace("posted_at <", "posted_at <="), ("2026-10-01 09:00", 5)
    ).fetchall()
    print(f"  posted_at <= '2026-10-01 09:00' → {rows}\n")

    print("id 를 정렬키에 더해 커서를 (posted_at, id) 로 잡으면 둘 다 생기지 않는다")
    rows = conn.execute(KEYSET_SQL, ("2026-10-01 09:00", 2, 5)).fetchall()
    print(f"  (posted_at, id) < ('2026-10-01 09:00', 2) → {[(r[0], r[1]) for r in rows]}\n")


def main() -> None:
    print_environment()

    small = build_small()
    print_dataset(small)
    part1_same_page(small)
    part2_shifting(small)
    part5_unstable_sort(small)

    big = build_big()
    part3_depth(big)
    part4_plans(big)


if __name__ == "__main__":
    main()
