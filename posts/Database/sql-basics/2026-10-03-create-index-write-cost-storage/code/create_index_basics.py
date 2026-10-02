"""CREATE INDEX 로 인덱스를 만들고, 읽기에서 얻는 것과 쓰기·저장에서 내는 것을 잰다.

주문 표 20,000행을 만든 뒤 인덱스가 없을 때와 있을 때의 실행계획·VM 명령 수를 비교한다.
시간은 실행할 때마다 흔들리므로 SQLite 가상 머신(VDBE)이 실행한 명령 수를 함께 센다.
이 값은 같은 버전·같은 데이터에서 매번 같다.
"""

import random
import sqlite3
import time

from dbshow import print_dataset, print_environment

ROW_COUNT = 20_000
CUSTOMER_COUNT = 2_000
STATUSES = ["paid", "shipped", "cancelled"]


def make_rows() -> list[tuple]:
    # 시드를 고정해 실행할 때마다 같은 주문 표가 나오게 한다
    rng = random.Random(42)
    rows = []
    for order_id in range(1, ROW_COUNT + 1):
        customer_id = rng.randint(1, CUSTOMER_COUNT)
        status = rng.choice(STATUSES)
        day = rng.randint(1, 30)
        rows.append((order_id, customer_id, status, f"2026-09-{day:02d}", rng.randint(1, 500) * 100))
    return rows


TABLE_DDL = """
CREATE TABLE {name} (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    status      TEXT    NOT NULL,
    ordered_on  TEXT    NOT NULL,
    amount      INTEGER NOT NULL
)
"""


def count_steps(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> tuple[int, list]:
    steps = 0

    def tick() -> int:
        nonlocal steps
        steps += 1
        return 0

    conn.set_progress_handler(tick, 1)
    rows = conn.execute(sql, params).fetchall()
    conn.set_progress_handler(None, 1)
    return steps, rows


def show_plan(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> None:
    # sqlite3 CLI 가 그리는 트리 모양을 그대로 흉내 낸다 (id·parent 로 깊이를 잡는다)
    plan = conn.execute("EXPLAIN QUERY PLAN " + sql, params).fetchall()
    prefix = {0: ""}
    print("   QUERY PLAN")
    for i, (node_id, parent, _, detail) in enumerate(plan):
        is_last = all(r[1] != parent for r in plan[i + 1 :])
        lead = prefix.get(parent, "")
        print(f"   {lead}{'`--' if is_last else '|--'}{detail}")
        prefix[node_id] = lead + ("   " if is_last else "|  ")


def run(conn: sqlite3.Connection, sql: str) -> None:
    print(f"   {' '.join(sql.split())}")
    try:
        cursor = conn.execute(sql)
    except sqlite3.Error as exc:
        print(f"   에러: {exc}")
        return
    if cursor.description is None:
        print("   성공")
        return
    for row in cursor.fetchall():
        print("   " + " | ".join("NULL" if v is None else str(v) for v in row))


def build_database(cached_statements: int = 128) -> sqlite3.Connection:
    # 128 은 파이썬 sqlite3 의 기본값이다. 같은 문장 텍스트는 준비된 문장을 다시 쓴다
    conn = sqlite3.connect(":memory:", cached_statements=cached_statements)
    conn.execute(TABLE_DDL.format(name="orders"))
    conn.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", make_rows())
    conn.commit()
    return conn


CUSTOMER_SQL = "SELECT order_id, amount FROM orders WHERE customer_id = ?"


def section_create(conn: sqlite3.Connection) -> None:
    print("\n-- 1. 인덱스가 없을 때 — 고객 777의 주문")
    show_plan(conn, CUSTOMER_SQL, (777,))
    steps, rows = count_steps(conn, CUSTOMER_SQL, (777,))
    print(f"   결과 {len(rows)}행 · VM 명령 {steps:,}개")

    print("\n-- 2. CREATE INDEX 로 만든 뒤")
    run(conn, "CREATE INDEX ix_orders_customer_id ON orders (customer_id)")
    show_plan(conn, CUSTOMER_SQL, (777,))
    steps, rows = count_steps(conn, CUSTOMER_SQL, (777,))
    print(f"   결과 {len(rows)}행 · VM 명령 {steps:,}개")

    print("\n-- 3. 만든 인덱스 확인과 같은 이름으로 한 번 더")
    run(conn, "SELECT name, \"unique\", origin FROM pragma_index_list('orders')")
    run(conn, "SELECT seqno, name FROM pragma_index_info('ix_orders_customer_id')")
    run(conn, "CREATE INDEX ix_orders_customer_id ON orders (customer_id)")
    run(conn, "CREATE INDEX IF NOT EXISTS ix_orders_customer_id ON orders (customer_id)")

    print("\n-- 4. UNIQUE INDEX — 이미 겹치는 값이 있으면 만들어지지 않는다")
    run(conn, "CREATE UNIQUE INDEX ux_orders_customer_id ON orders (customer_id)")
    run(conn, "SELECT COUNT(*) FROM pragma_index_list('orders')")


STATUS_SQL = "SELECT COUNT(*), SUM(amount) FROM orders WHERE status = 'paid'"
STATUS_SQL_NO_INDEX = (
    "SELECT COUNT(*), SUM(amount) FROM orders NOT INDEXED WHERE status = 'paid'"
)


def section_low_selectivity(conn: sqlite3.Connection) -> None:
    print("\n-- 5. 값이 3가지뿐인 컬럼 — status")
    run(conn, "SELECT status, COUNT(*) FROM orders GROUP BY status")
    run(conn, "CREATE INDEX ix_orders_status ON orders (status)")
    show_plan(conn, STATUS_SQL)
    for label, sql in [("인덱스 사용", STATUS_SQL), ("NOT INDEXED", STATUS_SQL_NO_INDEX)]:
        steps, rows = count_steps(conn, sql)
        print(f"   {label} · 결과 {rows[0]} · VM 명령 {steps:,}개 · {best_ms(conn, sql):.2f} ms")

    print("\n-- 6. ANALYZE 로 통계를 만든 뒤")
    run(conn, "ANALYZE")
    run(conn, "SELECT idx, stat FROM sqlite_stat1 ORDER BY idx")
    show_plan(conn, STATUS_SQL)
    show_plan(conn, CUSTOMER_SQL, (777,))


def best_ms(conn: sqlite3.Connection, sql: str, repeat: int = 30) -> float:
    # 한 번 잰 시간은 흔들리므로 30번 중 가장 빠른 값을 쓴다
    best = float("inf")
    for _ in range(repeat):
        started = time.perf_counter()
        conn.execute(sql).fetchall()
        best = min(best, time.perf_counter() - started)
    return best * 1000


def page_count(conn: sqlite3.Connection) -> int:
    return conn.execute("PRAGMA page_count").fetchone()[0]


def section_storage() -> None:
    print("\n-- 8. 저장 공간 — 인덱스를 하나씩 더할 때 늘어나는 페이지")
    conn = build_database()
    page_size = conn.execute("PRAGMA page_size").fetchone()[0]
    print(f"   page_size {page_size} 바이트")
    before = page_count(conn)
    print(f"   표만: {before:,} 페이지")
    for ddl in [
        "CREATE INDEX ix_orders_customer_id ON orders (customer_id)",
        "CREATE INDEX ix_orders_status ON orders (status)",
        "CREATE INDEX ix_orders_ordered_on ON orders (ordered_on)",
        "CREATE INDEX ix_orders_customer_ordered ON orders (customer_id, ordered_on)",
    ]:
        conn.execute(ddl)
        after = page_count(conn)
        print(f"   + {ddl.split()[2]:<28} {after:,} 페이지 (+{after - before})")
        before = after
    conn.close()


INDEX_SETS = {
    "인덱스 0개": [],
    "인덱스 1개": ["customer_id"],
    "인덱스 3개": ["customer_id", "status", "ordered_on"],
}


def load_once(rows: list[tuple], columns: list[str], index_after: bool, counting: bool):
    """빈 표에 rows 를 넣는다. index_after 면 다 넣은 뒤에 인덱스를 만든다."""
    conn = sqlite3.connect(":memory:")
    conn.execute(TABLE_DDL.format(name="orders"))
    ddls = [f"CREATE INDEX ix_orders_{c} ON orders ({c})" for c in columns]
    if not index_after:
        for ddl in ddls:
            conn.execute(ddl)
    steps = 0

    def tick() -> int:
        nonlocal steps
        steps += 1
        return 0

    if counting:
        conn.set_progress_handler(tick, 1)
    started = time.perf_counter()
    conn.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", rows)
    if index_after:
        for ddl in ddls:
            conn.execute(ddl)
    conn.commit()
    elapsed_ms = (time.perf_counter() - started) * 1000
    pages = page_count(conn)
    conn.close()
    return steps, pages, elapsed_ms


def load(columns: list[str], *, index_after: bool) -> tuple[int, int, float]:
    rows = make_rows()
    steps, pages, _ = load_once(rows, columns, index_after, counting=True)
    # 명령마다 파이썬 콜백이 불리면 시간이 몇 배로 늘어나므로, 시간은 세지 않는 실행에서 잰다
    elapsed_ms = min(load_once(rows, columns, index_after, counting=False)[2] for _ in range(5))
    return steps, pages, elapsed_ms


def section_write_cost() -> None:
    print(f"\n-- 9. 쓰기 비용 — 같은 {ROW_COUNT:,}행을 인덱스 수만 바꿔 INSERT")
    cases = [(label, columns, False) for label, columns in INDEX_SETS.items()]
    cases.append(("0개로 넣고 3개를 나중에", INDEX_SETS["인덱스 3개"], True))
    for label, columns, index_after in cases:
        steps, pages, elapsed_ms = load(columns, index_after=index_after)
        print(f"   {label}: VM 명령 {steps:>9,}개 · {pages:>4} 페이지 · {elapsed_ms:6.1f} ms")

    print("   - INSERT 한 행을 컴파일한 프로그램에서 Insert(표)·IdxInsert(인덱스) 명령")
    for label, columns in INDEX_SETS.items():
        conn = sqlite3.connect(":memory:")
        conn.execute(TABLE_DDL.format(name="orders"))
        for column in columns:
            conn.execute(f"CREATE INDEX ix_orders_{column} ON orders ({column})")
        ops = [r[1] for r in conn.execute("EXPLAIN INSERT INTO orders VALUES (1, 1, 'paid', '2026-09-01', 100)")]
        print(f"     {label}: Insert {ops.count('Insert')}개 · IdxInsert {ops.count('IdxInsert')}개")
        conn.close()

    print("   - 이미 행이 있는 표에 CREATE INDEX 를 컴파일한 프로그램의 정렬 명령")
    conn = build_database()
    ops = [r[1] for r in conn.execute("EXPLAIN CREATE INDEX ix_orders_status ON orders (status)")]
    print("     " + " · ".join(op for op in dict.fromkeys(ops) if op.startswith("Sorter")))
    conn.close()


def section_update_cost() -> None:
    print("\n-- 10. UPDATE — 인덱스에 없는 컬럼을 바꿀 때와 있는 컬럼을 바꿀 때")
    conn = build_database()
    for column in INDEX_SETS["인덱스 3개"]:
        conn.execute(f"CREATE INDEX ix_orders_{column} ON orders ({column})")
    for sql in [
        "UPDATE orders SET amount = amount + 100 WHERE order_id <= 1000",
        "UPDATE orders SET customer_id = customer_id + 1 WHERE order_id <= 1000",
    ]:
        steps, _ = count_steps(conn, sql)
        print(f"   {sql}")
        print(f"   VM 명령 {steps:,}개")
    conn.close()


def section_drop(conn: sqlite3.Connection) -> None:
    print("\n-- 7. DROP INDEX")
    run(conn, "DROP INDEX ix_orders_customer_id")
    run(conn, "DROP INDEX ix_orders_customer_id")
    run(conn, "DROP INDEX IF EXISTS ix_orders_customer_id")
    print("   - 지운 뒤 같은 연결에서 1번과 같은 EXPLAIN QUERY PLAN 을 다시 돌리면")
    show_plan(conn, CUSTOMER_SQL, (777,))
    print("   - 문장 캐시를 끈 연결(cached_statements=0)에서 만들고 지운 뒤 돌리면")
    fresh = build_database(cached_statements=0)
    fresh.execute("CREATE INDEX ix_orders_customer_id ON orders (customer_id)")
    fresh.execute("DROP INDEX ix_orders_customer_id")
    show_plan(fresh, CUSTOMER_SQL, (777,))
    fresh.close()


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn, max_rows=5)
    section_create(conn)
    section_low_selectivity(conn)
    section_drop(conn)
    section_storage()
    section_write_cost()
    section_update_cost()


if __name__ == "__main__":
    main()
