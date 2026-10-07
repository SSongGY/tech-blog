"""옵티마이저 힌트를 쓰기 전에 확인할 세 가지를 SQLite 로 재현한다.

SQLite 의 "힌트"는 INDEXED BY / NOT INDEXED, 단항 +, likelihood() 셋이다.
Tibero·Oracle 의 /*+ ... */ 와 모양은 다르지만, 힌트가 나중에 되돌아오는 길은 같다.

  확인 1. 통계가 맞는가      — 힌트 없이 ANALYZE 만으로 풀리는 문제인지
  확인 2. 데이터가 바뀌어도 맞는가 — 힌트는 데이터를 안 본다. 분포가 뒤집히면 힌트가 느린 쪽이 된다
  확인 3. 스키마가 바뀌어도 사는가 — 인덱스를 지우거나 조건을 바꾸면 힌트가 질의를 깨뜨린다

실제 일의 양은 VDBE 명령 수(set_progress_handler 를 명령 1개마다)로 센다.
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
SEED = 20261007

QUERY = (
    "SELECT COUNT(*), SUM(amount) FROM orders "
    "WHERE status = :status AND customer_id = 42"
)
HINT_STATUS = QUERY.replace("FROM orders", "FROM orders INDEXED BY ix_orders_status")
HINT_CUSTOMER = QUERY.replace("FROM orders", "FROM orders INDEXED BY ix_orders_customer_id")
PLUS_STATUS = QUERY.replace("WHERE status", "WHERE +status")


def build_database():
    conn = sqlite3.connect(":memory:", cached_statements=0)
    conn.executescript(
        """CREATE TABLE orders (
               order_id     INTEGER PRIMARY KEY,
               status       TEXT NOT NULL,
               customer_id  INTEGER NOT NULL,
               amount       INTEGER NOT NULL
           );
           CREATE TABLE product (
               sku   INTEGER PRIMARY KEY,
               code  TEXT NOT NULL,
               name  TEXT NOT NULL
           );"""
    )
    rng = random.Random(SEED)
    rows = [
        (i, f"S{i % STATUS_COUNT:03d}", i % CUSTOMER_COUNT + 1, rng.randint(1, 500))
        for i in range(1, ROW_COUNT + 1)
    ]
    conn.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", rows)
    conn.executemany(
        "INSERT INTO product VALUES (?, ?, ?)",
        [(1, "5", "볼트"), (2, "05", "너트"), (3, "7", "와셔"), (4, "5.0", "핀")],
    )
    conn.execute("CREATE INDEX ix_orders_status ON orders (status)")
    conn.execute("CREATE INDEX ix_orders_customer_id ON orders (customer_id)")
    conn.execute("CREATE INDEX ix_product_code ON product (code)")
    conn.commit()
    return conn


def plan_tree(conn, sql, params=None):
    """EXPLAIN QUERY PLAN 결과를 sqlite3 CLI 가 그리는 트리 모양 그대로 만든다."""
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql, params or {}).fetchall()
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
    try:
        result = conn.execute(sql, params).fetchone()
    finally:
        conn.set_progress_handler(None, 1)
    return result, steps


def median_ms(conn, sql, params, repeat=7):
    samples = []
    for _ in range(repeat):
        start = time.perf_counter()
        conn.execute(sql, params).fetchone()
        samples.append((time.perf_counter() - start) * 1000)
    return statistics.median(samples)


def measure(conn, label, status, sql=QUERY):
    params = {"status": status}
    print(f"-- {label}  (status = '{status}')")
    try:
        print(plan_tree(conn, sql, params))
    except sqlite3.Error as exc:
        print(f"   -> {type(exc).__name__}: {exc}")
        print()
        return
    result, steps = count_vm_steps(conn, sql, params)
    print(f"   결과 (건수, 합계) = {result}")
    print(f"   VDBE 명령 수 = {steps:,}")
    print(f"   시간 중앙값 = {median_ms(conn, sql, params):.2f} ms")
    print()


def show_stat1(conn):
    print("   sqlite_stat1")
    rows = conn.execute("SELECT tbl, idx, stat FROM sqlite_stat1 ORDER BY idx").fetchall()
    for tbl, idx, stat in rows:
        print(f"   {tbl:<6} | {str(idx):<21} | {stat}")


def show_distribution(conn, status):
    (n,) = conn.execute("SELECT COUNT(*) FROM orders WHERE status = ?", (status,)).fetchone()
    (m,) = conn.execute("SELECT COUNT(*) FROM orders WHERE customer_id = 42").fetchone()
    print(f"   실제 분포: status = '{status}' {n:,}행, customer_id = 42 {m:,}행")


def run_rows(conn, label, sql):
    print(f"-- {label}")
    print(f"   {sql}")
    try:
        print(plan_tree(conn, sql))
        rows = conn.execute(sql).fetchall()
        print(f"   결과 {len(rows)}행: {rows}")
    except sqlite3.Error as exc:
        print(f"   -> {type(exc).__name__}: {exc}")
    print()


def main():
    conn = build_database()
    print_environment({"행 수": f"{ROW_COUNT:,}", "난수 시드": str(SEED)})
    print_dataset(conn)

    print("== 확인 1. 통계가 맞는가 — 힌트 없이 풀리는 문제인지 먼저 본다")
    conn.execute("ANALYZE")
    show_stat1(conn)
    print("   (주문 99%를 'DONE' 으로 바꾼다. 통계는 그대로 둔다)")
    conn.execute("UPDATE orders SET status = 'DONE' WHERE order_id % 100 <> 0")
    conn.commit()
    show_distribution(conn, "DONE")
    measure(conn, "1-a 낡은 통계로 고른 계획", "DONE")
    measure(conn, "1-b 힌트로 customer_id 인덱스를 강제", "DONE", HINT_CUSTOMER)
    conn.execute("ANALYZE")
    show_stat1(conn)
    measure(conn, "1-c ANALYZE 뒤 힌트 없이", "DONE")

    print("== 확인 2. 데이터가 바뀌어도 맞는가 — 힌트는 데이터를 보지 않는다")
    print("   (주문을 원래 분포로 되돌린다. status 1,000가지가 100행씩)")
    conn.execute("UPDATE orders SET status = 'S' || substr('000' || (order_id % 1000), -3)")
    conn.execute("ANALYZE")
    conn.commit()
    show_distribution(conn, "S041")
    measure(conn, "2-a 지금 데이터에서 옵티마이저가 고른 계획", "S041")
    measure(conn, "2-b 같은 계획을 힌트로 못 박음", "S041", HINT_STATUS)
    print("   (반년 뒤. 주문 99%가 'DONE'. 이번엔 통계도 다시 모았다)")
    conn.execute("UPDATE orders SET status = 'DONE' WHERE order_id % 100 <> 0")
    conn.execute("ANALYZE")
    conn.commit()
    show_distribution(conn, "DONE")
    measure(conn, "2-c 힌트 없는 질의 — 새 통계로 계획을 바꿨다", "DONE")
    measure(conn, "2-d 못 박아 둔 힌트 — 그대로 status 인덱스", "DONE", HINT_STATUS)

    print("== 확인 3. 스키마가 바뀌어도 사는가 — INDEXED BY 는 요구이지 권고가 아니다")
    print("   (질의에서 status 조건이 빠졌다. 힌트는 그대로 status 인덱스를 가리킨다)")
    measure(conn, "3-a 힌트 없이", "DONE",
            "SELECT COUNT(*) FROM orders WHERE customer_id = 42")
    measure(conn, "3-b 조건이 못 쓰는 인덱스를 힌트로 지정", "DONE",
            "SELECT COUNT(*) FROM orders INDEXED BY ix_orders_status WHERE customer_id = 42")
    print("   ('DONE' 주문만 담는 부분 인덱스를 만들고 힌트로 못 박았다. 뒤에 조건 값이 바뀐다)")
    conn.execute("CREATE INDEX ix_orders_done_customer ON orders (customer_id) WHERE status = 'DONE'")
    conn.execute("ANALYZE")
    conn.commit()
    partial_hint = QUERY.replace("FROM orders", "FROM orders INDEXED BY ix_orders_done_customer")
    measure(conn, "3-c 부분 인덱스 힌트, 조건 값 'DONE' 을 글자로 적음", "DONE",
            partial_hint.replace(":status", "'DONE'"))
    measure(conn, "3-d 같은 힌트, 조건 값 'S041' 을 글자로 적음", "S041",
            partial_hint.replace(":status", "'S041'"))
    measure(conn, "3-d' 같은 힌트, 조건 값을 바인딩 변수로 넘김 (값은 'DONE')", "DONE", partial_hint)
    print("   (운영자가 status 인덱스를 새 이름으로 다시 만들었다. ANALYZE 는 돌리지 않았다)")
    conn.execute("DROP INDEX ix_orders_done_customer")
    conn.execute("DROP INDEX ix_orders_status")
    conn.execute("CREATE INDEX ix_orders_status_v2 ON orders (status)")
    conn.commit()
    show_stat1(conn)
    measure(conn, "3-e 힌트 없는 질의 — 통계 없는 새 인덱스를 골랐다", "DONE")
    measure(conn, "3-f 옛 이름을 적은 힌트 — 질의 자체가 실패한다", "DONE", HINT_STATUS)
    conn.execute("ANALYZE")
    show_stat1(conn)
    measure(conn, "3-g ANALYZE 뒤 힌트 없는 질의", "DONE")
    measure(conn, "3-h NOT INDEXED — 인덱스를 전부 막는다", "DONE",
            QUERY.replace("FROM orders", "FROM orders NOT INDEXED"))

    print("== 덤. 단항 + 는 인덱스만 막는 것이 아니다 — 타입 친화도도 벗긴다")
    run_rows(conn, "4-a code = 5 (TEXT 컬럼에 숫자 리터럴)", "SELECT sku, code FROM product WHERE code = 5")
    run_rows(conn, "4-b +code = 5 (인덱스를 막으려고 + 를 붙였다)", "SELECT sku, code FROM product WHERE +code = 5")
    run_rows(conn, "4-c +code = '5' (문자열 리터럴이면 같은 결과)", "SELECT sku, code FROM product WHERE +code = '5'")

    print("== 덤. likelihood() — 확률을 알려주는 힌트는 인덱스가 없어져도 질의를 깨뜨리지 않는다")
    soft = QUERY.replace("customer_id = 42", "likelihood(customer_id = 42, 0.9)")
    measure(conn, "5-a 힌트 없이 (통계: customer_id 1,000행, status 9,091행)", "DONE")
    measure(conn, "5-b customer_id = 42 가 90% 참이라고 알려줌", "DONE", soft)
    conn.execute("DROP INDEX ix_orders_status_v2")
    measure(conn, "5-c status 인덱스를 지운 뒤 같은 질의 — 계획만 바뀌고 실패하지 않는다", "DONE", soft)

    conn.close()


if __name__ == "__main__":
    main()
