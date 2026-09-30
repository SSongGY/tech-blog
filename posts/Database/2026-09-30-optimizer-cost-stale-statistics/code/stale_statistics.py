"""옵티마이저의 비용 추정이 무엇을 근거로 하는지, 통계가 틀어지면 어떻게 오판하는지 재현한다.

SQLite 는 계획에 비용 숫자를 찍지 않는다. 대신 두 가지를 나란히 본다.
- 옵티마이저가 믿는 것: sqlite_stat1 의 숫자와 그걸로 고른 계획
- 실제로 든 일: 질의 하나가 실행한 가상 머신(VDBE) 명령 수와 걸린 시간

VDBE 명령 수는 set_progress_handler 를 명령 1개마다 불리게 걸어 센다.
시간은 흔들리지만 명령 수는 같은 데이터·같은 계획이면 매번 같다.
"""

import random
import sqlite3
import statistics
import time

from dbshow import print_dataset, print_environment

ROW_COUNT = 100_000
STATUS_COUNT = 1_000
CUSTOMER_COUNT = 100
SEED = 20260930

QUERY = (
    "SELECT COUNT(*), SUM(amount) FROM orders "
    "WHERE status = :status AND customer_id = 42"
)
# 옵티마이저가 고르지 않은 쪽의 실제 일을 재려고 인덱스를 고정한 판
QUERY_BY_CUSTOMER = QUERY.replace(
    "FROM orders", "FROM orders INDEXED BY ix_orders_customer_id"
)
QUERY_BY_STATUS = QUERY.replace("FROM orders", "FROM orders INDEXED BY ix_orders_status")


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """CREATE TABLE orders (
               order_id     INTEGER PRIMARY KEY,
               status       TEXT NOT NULL,
               customer_id  INTEGER NOT NULL,
               amount       INTEGER NOT NULL
           )"""
    )
    rng = random.Random(SEED)
    rows = [
        (i, f"S{i % STATUS_COUNT:03d}", i % CUSTOMER_COUNT + 1, rng.randint(1, 500))
        for i in range(1, ROW_COUNT + 1)
    ]
    conn.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", rows)
    conn.execute("CREATE INDEX ix_orders_status ON orders (status)")
    conn.execute("CREATE INDEX ix_orders_customer_id ON orders (customer_id)")
    conn.commit()
    return conn


def plan_tree(conn, sql, params):
    """EXPLAIN QUERY PLAN 결과를 sqlite3 CLI 가 그리는 트리 모양 그대로 만든다."""
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


def count_vm_steps(conn, sql, params):
    steps = 0

    def tick():
        nonlocal steps
        steps += 1
        return 0

    conn.set_progress_handler(tick, 1)
    result = conn.execute(sql, params).fetchone()
    conn.set_progress_handler(None, 1)
    return result, steps


def median_ms(conn, sql, params, repeat=7):
    samples = []
    for _ in range(repeat):
        start = time.perf_counter()
        conn.execute(sql, params).fetchone()
        samples.append((time.perf_counter() - start) * 1000)
    return statistics.median(samples)


def show_stat1(conn):
    print("   sqlite_stat1")
    print("   tbl    | idx                   | stat")
    rows = conn.execute("SELECT tbl, idx, stat FROM sqlite_stat1 ORDER BY idx").fetchall()
    for tbl, idx, stat in rows:
        print(f"   {tbl:<6} | {str(idx):<21} | {stat}")


def show_distribution(conn):
    rows = conn.execute(
        "SELECT COUNT(DISTINCT status), MAX(c) FROM "
        "(SELECT status, COUNT(*) AS c FROM orders GROUP BY status)"
    ).fetchone()
    print(f"   실제 분포: status 서로 다른 값 {rows[0]}개, 가장 많은 값의 행 수 {rows[1]}")


def measure(conn, label, status, sql=QUERY):
    params = {"status": status}
    print(f"-- {label}  (status = '{status}')")
    print(plan_tree(conn, sql, params))
    result, steps = count_vm_steps(conn, sql, params)
    print(f"   결과 (건수, 합계) = {result}")
    print(f"   VDBE 명령 수 = {steps:,}")
    print(f"   시간 중앙값 = {median_ms(conn, sql, params):.2f} ms")
    print()


def main():
    conn = build_database()
    print_environment({"행 수": f"{ROW_COUNT:,}", "난수 시드": str(SEED)})
    print_dataset(conn)

    print("== 1. 통계를 모은 직후 — 옵티마이저의 믿음과 데이터가 일치한다")
    conn.execute("ANALYZE")
    show_stat1(conn)
    show_distribution(conn)
    measure(conn, "1-a 옵티마이저가 고른 계획", "S041")
    measure(conn, "1-b 고르지 않은 쪽 (customer_id 인덱스 고정)", "S041", QUERY_BY_CUSTOMER)

    print("== 2. 데이터가 바뀌고 통계는 그대로 — 주문 99%가 'DONE' 으로 끝났다")
    conn.execute("UPDATE orders SET status = 'DONE' WHERE order_id % 100 <> 0")
    conn.commit()
    show_stat1(conn)
    show_distribution(conn)
    measure(conn, "2-a 낡은 통계로 고른 계획", "DONE")
    measure(conn, "2-b 고르지 않은 쪽 (customer_id 인덱스 고정)", "DONE", QUERY_BY_CUSTOMER)

    print("== 3. ANALYZE 를 다시 돌린다")
    conn.execute("ANALYZE")
    show_stat1(conn)
    measure(conn, "3-a 새 통계로 고른 계획", "DONE")
    measure(conn, "3-b 같은 통계에서 드문 값", "S100")
    measure(conn, "3-c 드문 값에서 고르지 않은 쪽 (status 인덱스 고정)", "S100", QUERY_BY_STATUS)
    stat4 = [
        opt for (opt,) in conn.execute("PRAGMA compile_options") if "STAT4" in opt
    ]
    print(f"   컴파일 옵션 중 STAT4: {stat4 or '없음'}")
    print()

    print("== 4. 통계를 손으로 바꾼다 — 비용은 데이터가 아니라 이 숫자로 계산된다")
    conn.execute(
        "UPDATE sqlite_stat1 SET stat = '100000 100000' "
        "WHERE idx = 'ix_orders_customer_id'"
    )
    conn.execute("ANALYZE sqlite_schema")
    show_stat1(conn)
    measure(conn, "4-a 조작한 통계", "DONE")

    conn.close()


if __name__ == "__main__":
    main()
