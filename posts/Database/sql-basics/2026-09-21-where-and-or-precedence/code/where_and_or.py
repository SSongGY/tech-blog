"""WHERE 절의 AND / OR / NOT 우선순위를 같은 데이터로 대조한다.

실행: python where_and_or.py   (표준 라이브러리만 사용)
"""

import random
import sqlite3

RANDOM_SEED = 20260921
ROW_COUNT = 20_000
STATUS_VALUES = ("paid", "pending", "canceled")


def build_database() -> sqlite3.Connection:
    """재현 가능한 주문 데이터를 메모리 DB에 만든다."""
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE customer_order (
            id          INTEGER PRIMARY KEY,
            status      TEXT    NOT NULL,
            amount      INTEGER NOT NULL,
            coupon_code TEXT
        )
        """
    )
    rng = random.Random(RANDOM_SEED)
    rows = []
    for order_id in range(1, ROW_COUNT + 1):
        status = STATUS_VALUES[rng.randrange(len(STATUS_VALUES))]
        amount = rng.randrange(1_000, 100_001, 1_000)
        # 쿠폰은 없는 주문이 더 많다. NULL 동작을 보려면 NULL이 실제로 있어야 한다.
        coupon = f"CP{rng.randrange(1, 6)}" if rng.random() < 0.3 else None
        rows.append((order_id, status, amount, coupon))
    conn.executemany("INSERT INTO customer_order VALUES (?, ?, ?, ?)", rows)
    conn.execute("CREATE INDEX ix_customer_order_status ON customer_order (status)")
    conn.commit()
    return conn


def count(conn: sqlite3.Connection, where: str) -> int:
    sql = f"SELECT COUNT(*) FROM customer_order WHERE {where}"
    return conn.execute(sql).fetchone()[0]


def report(conn: sqlite3.Connection, where: str) -> int:
    """건수를 앞에 두어 한글 라벨 폭에 상관없이 자리가 맞게 찍는다."""
    n = count(conn, where)
    print(f"  {n:>6,}행  WHERE {where}")
    return n


def main() -> None:
    conn = build_database()
    print(f"SQLite {sqlite3.sqlite_version} / 전체 {ROW_COUNT:,}행\n")

    print("### 1. AND와 OR을 섞으면 괄호 유무로 결과가 갈린다")
    no_paren = report(conn, "status = 'canceled' OR status = 'pending' AND amount > 50000")
    or_first = report(conn, "(status = 'canceled' OR status = 'pending') AND amount > 50000")
    and_first = report(conn, "status = 'canceled' OR (status = 'pending' AND amount > 50000)")
    print(f"  괄호 없음 == AND 먼저 : {no_paren == and_first}")
    print(f"  괄호 없음 == OR 먼저  : {no_paren == or_first}")
    print(f"  두 해석의 차이        : {abs(and_first - or_first):,}행\n")

    print("### 2. NOT은 AND보다도 먼저 묶인다")
    not_plain = report(conn, "NOT status = 'paid' AND amount > 50000")
    not_only = report(conn, "(NOT status = 'paid') AND amount > 50000")
    not_whole = report(conn, "NOT (status = 'paid' AND amount > 50000)")
    print(f"  괄호 없음 == NOT 먼저 : {not_plain == not_only}")
    print(f"  괄호 없음 == 전체 부정: {not_plain == not_whole}\n")

    print("### 3. NULL이 섞이면 OR과 AND가 서로 다르게 삼킨다")
    total = count(conn, "1=1")
    has_coupon = count(conn, "coupon_code IS NOT NULL")
    null_coupon = count(conn, "coupon_code IS NULL")
    print(f"  쿠폰 있음 {has_coupon:,}행 / 쿠폰 NULL {null_coupon:,}행 / 합계 {total:,}행")
    eq = report(conn, "coupon_code = 'CP1'")
    ne = report(conn, "coupon_code <> 'CP1'")
    print(f"  = 와 <> 의 합 {eq + ne:,}행 → 전체 {total:,}행과 같은가: {eq + ne == total}")
    report(conn, "coupon_code = 'CP1' OR 1 = 1")
    report(conn, "coupon_code = 'CP1' AND 1 = 0")
    print()

    print("### 4. 실행계획: OR을 어떻게 쓰느냐로 인덱스 사용이 갈린다")
    for where in (
        "status = 'canceled' OR status = 'pending' AND amount > 50000",
        "status = 'paid' AND amount > 50000",
        "status = 'paid' OR amount > 50000",
        "status = 'paid' OR status = 'pending'",
    ):
        plan = conn.execute(
            f"EXPLAIN QUERY PLAN SELECT id FROM customer_order WHERE {where}"
        ).fetchall()
        print(f"  WHERE {where}")
        for step in plan:
            print(f"      {step[3]}")
        print()
    conn.close()


if __name__ == "__main__":
    main()
