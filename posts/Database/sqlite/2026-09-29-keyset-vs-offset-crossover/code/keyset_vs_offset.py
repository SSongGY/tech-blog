"""OFFSET 페이지네이션과 키셋(커서) 페이지네이션을 페이지 깊이별로 잰다.

정렬 키는 동점이 있는 created_at 과 동점을 가르는 id 두 개다. 키셋 조건을 쓰는
세 가지 방식이 같은 행을 돌려주는지, 비용은 어떻게 갈리는지를 본다.
비용은 SQLite 가상 머신 명령 개수와 실행 시간 중앙값 두 가지로 센다.
명령 개수는 같은 데이터·같은 질의면 매번 같고, 시간은 환경에 따라 흔들린다.
"""

import sqlite3
import statistics
import time

from dbshow import print_dataset, print_environment

ROW_COUNT = 200_000
PAGE_SIZE = 10
TIMING_RUNS = 5
BASE_EPOCH = 1_700_000_000
DEPTHS = (10, 100, 1_000, 10_000, 100_000, 199_990)
SORTER_OPCODES = {
    "OpenEphemeral", "Integer", "OffsetLimit", "IfNotZero",
    "Last", "IdxLE", "Delete", "IdxInsert",
}

COLUMNS = "SELECT id, created_at, title FROM post"
ORDER = "ORDER BY created_at DESC, id DESC LIMIT ?"
OFFSET_SQL = f"{COLUMNS} {ORDER} OFFSET ?"
# 키셋 조건을 쓰는 방식. 뜻이 같은지(또는 다른지)는 실습 2에서 결과로 확인한다
KEYSET_SQL = {
    "행 값 비교": f"{COLUMNS} WHERE (created_at, id) < (?, ?) {ORDER}",
    "OR 로 풀어 쓴 조건": (
        f"{COLUMNS} WHERE created_at < ? OR (created_at = ? AND id < ?) {ORDER}"
    ),
    "created_at 만 비교": f"{COLUMNS} WHERE created_at < ? {ORDER}",
}


def keyset_params(label, cursor):
    created_at, post_id = cursor
    if label == "OR 로 풀어 쓴 조건":
        return (created_at, created_at, post_id, PAGE_SIZE)
    if label == "created_at 만 비교":
        return (created_at, PAGE_SIZE)
    return (created_at, post_id, PAGE_SIZE)


def build_sample(conn):
    conn.execute(
        "CREATE TABLE post ("
        "  id INTEGER PRIMARY KEY,"
        "  created_at INTEGER NOT NULL,"
        "  title TEXT NOT NULL)"
    )
    # 한 초에 글 4개씩 몰리게 해 동점을 만든다. 7919 를 곱해 id 순서와 시간 순서를 섞는다
    conn.executemany(
        "INSERT INTO post (id, created_at, title) VALUES (?, ?, ?)",
        (
            (i, BASE_EPOCH + (i * 7919 % ROW_COUNT) // 4, f"글 {i:06d}")
            for i in range(1, ROW_COUNT + 1)
        ),
    )
    conn.execute("CREATE INDEX ix_post_created_at_id ON post (created_at, id)")
    conn.commit()


def measure(conn, sql, params):
    """(가상 머신 명령 개수, 실행 시간 중앙값 ms, 결과 행) 을 돌려준다."""
    steps = 0

    def tick():
        nonlocal steps
        steps += 1
        return 0

    conn.set_progress_handler(tick, 1)
    rows = conn.execute(sql, params).fetchall()
    conn.set_progress_handler(None, 0)

    elapsed = []
    for _ in range(TIMING_RUNS):
        started = time.perf_counter()
        conn.execute(sql, params).fetchall()
        elapsed.append((time.perf_counter() - started) * 1000)
    return steps, statistics.median(elapsed), rows


def cursor_before(conn, offset):
    """OFFSET 페이지의 바로 앞 행 — 앞 페이지를 읽은 쪽이 들고 있을 커서 값."""
    return conn.execute(
        f"SELECT created_at, id FROM post {ORDER} OFFSET ?", (1, offset - 1)
    ).fetchone()


def plan_tree(conn, sql, params):
    """EXPLAIN QUERY PLAN 을 sqlite3 CLI 가 그리는 트리 모양으로 만든다."""
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql, params).fetchall()
    children = {}
    for node_id, parent_id, _, detail in rows:
        children.setdefault(parent_id, []).append((node_id, detail))
    lines = ["QUERY PLAN"]

    def walk(parent_id, prefix):
        items = children.get(parent_id, [])
        for index, (node_id, detail) in enumerate(items):
            last = index == len(items) - 1
            lines.append(prefix + ("`--" if last else "|--") + detail)
            walk(node_id, prefix + ("   " if last else "|  "))

    walk(0, "")
    return "\n".join("   " + line for line in lines)


def show_plans(conn):
    print("-- 1. 실행 계획")
    cursor = cursor_before(conn, 100_000)
    print("   OFFSET")
    print(plan_tree(conn, OFFSET_SQL, (PAGE_SIZE, 100_000)))
    for label, sql in KEYSET_SQL.items():
        print(f"   키셋 — {label}")
        print(plan_tree(conn, sql, keyset_params(label, cursor)))
    print()


def compare_by_depth(conn):
    print("-- 2. 페이지 깊이별 비용 (명령 개수 / 시간 중앙값 ms) — 결과가 OFFSET 과 같은가")
    for letter, label in zip("ABC", KEYSET_SQL):
        print(f"   키셋 {letter} = {label}")
    header = "   건너뛴 행 |            OFFSET"
    for letter in "ABC":
        header += f" |          키셋 {letter}  "
    print(header)
    for offset in DEPTHS:
        steps, ms, expected = measure(conn, OFFSET_SQL, (PAGE_SIZE, offset))
        line = f"   {offset:>9,} | {steps:>9,} {ms:>7.3f}"
        cursor = cursor_before(conn, offset)
        for label, sql in KEYSET_SQL.items():
            steps, ms, rows = measure(conn, sql, keyset_params(label, cursor))
            mark = "=" if rows == expected else "≠"
            line += f" | {steps:>9,} {ms:>7.3f} {mark}"
        print(line)
    print("   (= 는 OFFSET 과 같은 10행, ≠ 는 다른 행)")
    print()


def walk_all_pages(conn, label):
    """첫 페이지부터 커서로 끝까지 넘기며 몇 행을 받았는지 센다."""
    seen = set()
    rows = conn.execute(f"{COLUMNS} {ORDER}", (PAGE_SIZE,)).fetchall()
    pages = 0
    while rows:
        pages += 1
        seen.update(row[0] for row in rows)
        last = rows[-1]
        cursor = (last[1], last[0])
        rows = conn.execute(KEYSET_SQL[label], keyset_params(label, cursor)).fetchall()
    return pages, len(seen)


def check_full_walk(conn):
    print("-- 3. 커서로 끝까지 넘겼을 때 받은 행 수")
    for label in ("행 값 비교", "created_at 만 비교"):
        pages, received = walk_all_pages(conn, label)
        print(
            f"   {label:<16} 페이지 {pages:>6,}개  받은 행 {received:>7,}"
            f"  빠진 행 {ROW_COUNT - received:>6,}"
        )
    print()


def compare_without_index(conn):
    print("-- 4. 정렬을 받쳐 줄 인덱스가 없으면")
    conn.execute("DROP INDEX ix_post_created_at_id")
    cursor_sql = KEYSET_SQL["행 값 비교"]
    for offset in DEPTHS:
        cursor = cursor_before(conn, offset)
        offset_steps, offset_ms, expected = measure(conn, OFFSET_SQL, (PAGE_SIZE, offset))
        keyset_steps, keyset_ms, rows = measure(
            conn, cursor_sql, keyset_params("행 값 비교", cursor)
        )
        mark = "=" if rows == expected else "≠"
        print(
            f"   건너뛴 행 {offset:>7,} | OFFSET {offset_steps:>9,} {offset_ms:>7.3f}"
            f" | 키셋 {keyset_steps:>9,} {keyset_ms:>7.3f} {mark}"
        )
    print(plan_tree(conn, cursor_sql, keyset_params("행 값 비교", cursor)))
    print()
    # 1만에서 10만 사이의 급증이 임시 B-트리가 디스크로 넘쳐서인지 가른다
    print("   임시 저장소를 메모리로 바꾼 뒤 OFFSET 만 다시 잰다")
    for store in ("DEFAULT", "MEMORY"):
        conn.execute(f"PRAGMA temp_store = {store}")
        for offset in (10_000, 100_000, 199_990):
            steps, ms, _ = measure(conn, OFFSET_SQL, (PAGE_SIZE, offset))
            print(f"   temp_store={store:<7} 건너뛴 행 {offset:>7,} | {steps:>9,} {ms:>8.3f}")
    conn.execute("PRAGMA temp_store = DEFAULT")
    print()
    # 임시 B-트리에 몇 행을 붙잡아 두는지는 실행 계획에 안 나온다. 바이트코드를 본다
    for label, sql, params in (
        ("OFFSET", OFFSET_SQL, (PAGE_SIZE, 100_000)),
        ("키셋 A", cursor_sql, keyset_params("행 값 비교", cursor)),
    ):
        print(f"   {label} 질의의 바이트코드 (EXPLAIN) — 임시 B-트리 크기를 정하는 줄만")
        print("   addr  opcode         p1    p2    p3    p4")
        for addr, opcode, p1, p2, p3, p4, *_ in conn.execute("EXPLAIN " + sql, params):
            if opcode in SORTER_OPCODES:
                print(f"   {addr:<5} {opcode:<14} {p1:<5} {p2:<5} {p3:<5} {p4 or ''}")
    conn.execute("CREATE INDEX ix_post_created_at_id ON post (created_at, id)")
    print()


def insert_between_pages(conn):
    print("-- 5. 1페이지와 2페이지 사이에 새 글이 들어오면")
    first_page = conn.execute(OFFSET_SQL, (PAGE_SIZE, 0)).fetchall()
    last = first_page[-1]
    print(f"   1페이지 마지막 행  id={last[0]} created_at={last[1]}")
    newest = conn.execute("SELECT MAX(created_at) FROM post").fetchone()[0] + 1
    conn.execute(
        "INSERT INTO post (id, created_at, title) VALUES (?, ?, ?)",
        (ROW_COUNT + 1, newest, "새 글"),
    )
    by_offset = conn.execute(OFFSET_SQL, (PAGE_SIZE, PAGE_SIZE)).fetchall()
    by_cursor = conn.execute(
        KEYSET_SQL["행 값 비교"], keyset_params("행 값 비교", (last[1], last[0]))
    ).fetchall()
    for label, rows in (("OFFSET 10", by_offset), ("키셋", by_cursor)):
        repeated = [row[0] for row in rows if row in first_page]
        print(f"   2페이지 {label:<9} 첫 행 id={rows[0][0]}  1페이지와 겹친 id {repeated}")
    conn.rollback()
    print()


def main():
    print_environment()
    conn = sqlite3.connect(":memory:")
    build_sample(conn)
    print_dataset(conn)
    print(f"한 페이지 {PAGE_SIZE}행 · 시간은 {TIMING_RUNS}회 실행의 중앙값")
    print()

    show_plans(conn)
    compare_by_depth(conn)
    check_full_walk(conn)
    compare_without_index(conn)
    insert_between_pages(conn)
    conn.close()


if __name__ == "__main__":
    main()
