"""기간이 겹치는 행을 B-tree 인덱스와 R*Tree 가상 테이블로 각각 찾는다.

SQLite 3.49.1 / Python 3.13.5 에서 돌렸다. 외부 의존성은 없다.
난수 시드를 고정했으므로 몇 번을 돌려도 같은 데이터가 만들어진다.
"""

import random
import sqlite3
import time

from dbshow import RULE, print_environment, print_table

BOOKING_COUNT = 200_000
DAY_SPAN = 36_500            # 0일부터 약 100년치 날짜 번호
MAX_STAY_DAYS = 30
QUERY_START, QUERY_END = 18_000, 18_010
REPEAT = 50


def build_database() -> sqlite3.Connection:
    """예약 20만 건을 보통 표와 rtree 가상 테이블에 같은 내용으로 넣는다."""
    random.seed(7)
    rows = []
    for booking_id in range(1, BOOKING_COUNT + 1):
        start_day = random.randint(0, DAY_SPAN)
        rows.append((booking_id, start_day, start_day + random.randint(0, MAX_STAY_DAYS)))

    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE booking (
            booking_id INTEGER PRIMARY KEY,
            start_day  INTEGER NOT NULL,
            end_day    INTEGER NOT NULL
        )
        """
    )
    conn.executemany("INSERT INTO booking VALUES (?, ?, ?)", rows)
    conn.execute("CREATE INDEX ix_booking_start_end ON booking(start_day, end_day)")
    conn.execute(
        "CREATE VIRTUAL TABLE booking_span USING rtree(booking_id, start_day, end_day)"
    )
    conn.executemany("INSERT INTO booking_span VALUES (?, ?, ?)", rows)
    conn.commit()
    return conn


def show_plan(conn: sqlite3.Connection, sql: str, args: tuple = ()) -> None:
    """sqlite3 CLI 가 그리는 트리와 같은 모양으로 detail 을 찍는다."""
    rows = list(conn.execute("EXPLAIN QUERY PLAN " + sql, args))
    children: dict[int, list[tuple[int, str]]] = {}
    for node_id, parent_id, _, detail in rows:
        children.setdefault(parent_id, []).append((node_id, detail))

    def walk(parent_id: int, prefix: str) -> None:
        kids = children.get(parent_id, [])
        for index, (node_id, detail) in enumerate(kids):
            last = index == len(kids) - 1
            print(f"{prefix}{'`--' if last else '|--'}{detail}")
            walk(node_id, prefix + ("   " if last else "|  "))

    print("QUERY PLAN")
    walk(0, "")


def time_query(conn: sqlite3.Connection, sql: str, args: tuple) -> tuple[int, float]:
    """REPEAT 번 돌린 평균 ms 와 결과 행 수를 돌려준다."""
    started = time.perf_counter()
    for _ in range(REPEAT):
        row_count = len(conn.execute(sql, args).fetchall())
    return row_count, (time.perf_counter() - started) / REPEAT * 1000


def section(title: str) -> None:
    print()
    print("=" * 62)
    print(title)
    print("=" * 62)


def main() -> None:
    conn = build_database()
    print_environment()
    print(RULE)
    print("스키마와 데이터 — 아래 질의는 전부 이 표를 대상으로 한다")
    print(RULE)
    print_table(conn, "booking")
    print("[인덱스] ix_booking_start_end ON booking(start_day, end_day)")
    print()
    print("[booking_span]  rtree 가상 테이블. 내용은 booking 과 같다 (앞 5행)")
    for row in conn.execute("SELECT * FROM booking_span LIMIT 5"):
        print(f"  {row}")
    print("  실제 저장은 아래 그림자 표가 맡는다:")
    for name, count in [
        (name, conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0])
        for (name,) in conn.execute(
            "SELECT name FROM sqlite_master WHERE name LIKE 'booking_span_%' ORDER BY name"
        )
    ]:
        print(f"    {name:<20} {count:>7,}행")

    section("1. 겹침 조건을 B-tree 인덱스로 — 절반을 훑는다")
    overlap_args = (QUERY_END, QUERY_START)
    btree_sql = "SELECT booking_id FROM booking WHERE start_day <= ? AND end_day >= ?"
    show_plan(conn, btree_sql, overlap_args)
    half = conn.execute(
        "SELECT COUNT(*) FROM booking WHERE start_day <= ?", (QUERY_END,)
    ).fetchone()[0]
    print(f"  start_day <= {QUERY_END} 인 행: {half:,} / {BOOKING_COUNT:,}")
    print("  → 인덱스는 start_day 조건까지만 쓰고, end_day 는 그 행들을 하나씩 본다")

    section("2. 같은 조건을 rtree 로 — 두 축을 한 번에 쓴다")
    rtree_sql = "SELECT booking_id FROM booking_span WHERE start_day <= ? AND end_day >= ?"
    show_plan(conn, rtree_sql, overlap_args)

    section("3. 결과는 같고 시간은 다르다")
    for label, sql in (("B-tree", btree_sql), ("rtree ", rtree_sql)):
        row_count, elapsed_ms = time_query(conn, sql, overlap_args)
        print(f"  {label}  겹치는 예약 {row_count}건  평균 {elapsed_ms:8.3f} ms")

    section("4. 본 표와 조인 — ANALYZE 전후로 계획이 뒤집힌다")
    join_sql = """
        SELECT b.* FROM booking_span s JOIN booking b ON b.booking_id = s.booking_id
        WHERE s.start_day <= ? AND s.end_day >= ?
    """
    cross_sql = join_sql.replace("JOIN booking", "CROSS JOIN booking")
    for stage in ("ANALYZE 전", "ANALYZE 후"):
        print(f"-- {stage}: JOIN")
        show_plan(conn, join_sql, overlap_args)
        row_count, elapsed_ms = time_query(conn, join_sql, overlap_args)
        print(f"   {row_count}건  평균 {elapsed_ms:8.3f} ms")
        if stage == "ANALYZE 전":
            conn.execute("ANALYZE")
    print("-- ANALYZE 후: CROSS JOIN 으로 순서를 고정")
    show_plan(conn, cross_sql, overlap_args)
    row_count, elapsed_ms = time_query(conn, cross_sql, overlap_args)
    print(f"   {row_count}건  평균 {elapsed_ms:8.3f} ms")

    section("5. 좌표는 32비트 실수로 저장된다 — 큰 정수가 깨진다")
    conn.execute("CREATE VIRTUAL TABLE span_f32 USING rtree(id, lo, hi)")
    conn.execute("CREATE VIRTUAL TABLE span_i32 USING rtree_i32(id, lo, hi)")
    samples = [(1, 16_777_217, 16_777_219), (2, 1_700_000_001, 1_700_000_002)]
    conn.executemany("INSERT INTO span_f32 VALUES (?, ?, ?)", samples)
    conn.executemany("INSERT INTO span_i32 VALUES (?, ?, ?)", samples)
    print("  넣은 값              rtree 가 돌려준 값                rtree_i32")
    for (id_, lo, hi), f32, i32 in zip(
        samples,
        conn.execute("SELECT lo, hi FROM span_f32 ORDER BY id").fetchall(),
        conn.execute("SELECT lo, hi FROM span_i32 ORDER BY id").fetchall(),
    ):
        print(f"  {lo}~{hi}  {f32[0]:.0f}~{f32[1]:.0f}  {i32[0]}~{i32[1]}")
    print("  → 하한은 내림, 상한은 올림. 원래 구간을 품는 쪽으로만 틀린다")

    section("6. 제약 — 하한 > 상한, 컬럼 수")
    for sql in (
        "INSERT INTO span_f32 VALUES (9, 5, 3)",
        "CREATE VIRTUAL TABLE bad USING rtree(id, lo, hi, extra)",
    ):
        try:
            conn.execute(sql)
            print(f"  OK   {sql}")
        except sqlite3.Error as exc:
            print(f"  에러 {sql}\n       {exc}")

    section("7. 쓰기 비용 — 같은 20만 건을 넣는 데 걸린 시간")
    fresh = sqlite3.connect(":memory:")
    fresh.execute("CREATE TABLE b (id INTEGER PRIMARY KEY, lo INTEGER, hi INTEGER)")
    fresh.execute("CREATE INDEX ix_b ON b(lo, hi)")
    fresh.execute("CREATE VIRTUAL TABLE r USING rtree(id, lo, hi)")
    rows = conn.execute("SELECT * FROM booking").fetchall()
    for label, target in (("B-tree 인덱스가 붙은 표", "b"), ("rtree 가상 테이블     ", "r")):
        started = time.perf_counter()
        fresh.executemany(f"INSERT INTO {target} VALUES (?, ?, ?)", rows)
        fresh.commit()
        print(f"  {label}  {time.perf_counter() - started:6.2f} 초")
    node_count, node_bytes = fresh.execute(
        "SELECT COUNT(*), SUM(LENGTH(data)) FROM r_node"
    ).fetchone()
    print(f"  rtree 노드 {node_count:,}개, 노드 데이터 합계 {node_bytes / 1024 / 1024:.1f} MiB")
    check = fresh.execute("SELECT rtreecheck('r')").fetchone()[0]
    print(f"  rtreecheck('r') = {check}")

    conn.close()
    fresh.close()


if __name__ == "__main__":
    main()
