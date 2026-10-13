"""BETWEEN 과 IN — 범위와 목록을 쓰는 법.

메모리 SQLite 에 주문 기록을 넣고 BETWEEN·IN 의 동작을 하나씩 확인한다.
경계값이 포함되는지, 날짜에 시분초가 붙으면 어디가 잘리는지, 양끝을 뒤집으면
어떻게 되는지, NOT IN 에 NULL 이 섞이면 무슨 일이 나는지를 전부 실행해서 본다.
"""

from __future__ import annotations

import sqlite3

from dbshow import print_dataset, print_environment

SCHEMA = """
CREATE TABLE order_log (
    order_id      INTEGER PRIMARY KEY,
    customer_name TEXT    NOT NULL,
    amount        INTEGER,
    ordered_at    TEXT    NOT NULL,
    status        TEXT    NOT NULL
);

CREATE TABLE refund_request (
    request_id TEXT PRIMARY KEY,
    order_id   INTEGER
);
"""

# 금액 10000 과 50000 은 경계값이다. 3월 31일 주문에는 시각이 붙어 있어
# BETWEEN '2026-03-01' AND '2026-03-31' 이 집는지 보는 데 쓴다.
ORDERS = [
    (1, "김하늘", 9_900, "2026-03-01 09:12:30", "paid"),
    (2, "이도윤", 10_000, "2026-03-05 18:40:00", "paid"),
    (3, "박서준", 23_500, "2026-03-17 11:05:12", "shipped"),
    (4, "최지아", 50_000, "2026-03-31 14:20:00", "paid"),
    (5, "정민재", 50_001, "2026-03-31 23:59:59", "cancelled"),
    (6, "한소윤", None, "2026-04-02 08:00:00", "pending"),
]

# 두 번째 요청은 order_id 가 NULL 이다. NOT IN 하위 질의에 섞여 들어간다.
REFUNDS = [
    ("RF-001", 3),
    ("RF-002", None),
    ("RF-003", 5),
]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO order_log VALUES (?, ?, ?, ?, ?)", ORDERS)
    conn.executemany("INSERT INTO refund_request VALUES (?, ?)", REFUNDS)
    conn.commit()
    return conn


def show(conn: sqlite3.Connection, label: str, sql: str) -> None:
    print(f"-- {label}")
    print("   " + " ".join(sql.split()))
    try:
        rows = conn.execute(sql).fetchall()
    except sqlite3.Error as exc:
        print(f"   에러: {exc}\n")
        return
    if not rows:
        print("   => (0행)\n")
        return
    for row in rows:
        print("   => " + " | ".join("NULL" if v is None else str(v) for v in row))
    print(f"   ({len(rows)}행)\n")


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("### 1. BETWEEN 의 경계값")
    show(conn, "1. 금액 10000 이상 50000 이하 — BETWEEN", """
        SELECT order_id, customer_name, amount FROM order_log
        WHERE amount BETWEEN 10000 AND 50000 ORDER BY order_id
    """)
    show(conn, "2. 같은 조건을 >= 와 <= 로 풀어 쓰면", """
        SELECT order_id, customer_name, amount FROM order_log
        WHERE amount >= 10000 AND amount <= 50000 ORDER BY order_id
    """)
    show(conn, "3. 양끝을 뒤집으면 — BETWEEN 50000 AND 10000", """
        SELECT order_id, amount FROM order_log
        WHERE amount BETWEEN 50000 AND 10000
    """)
    show(conn, "4. NOT BETWEEN — amount 가 NULL 인 행은 어느 쪽에도 없다", """
        SELECT order_id, customer_name, amount FROM order_log
        WHERE amount NOT BETWEEN 10000 AND 50000 ORDER BY order_id
    """)

    print("### 2. 날짜에 BETWEEN 을 쓸 때")
    show(conn, "5. 3월 한 달 — BETWEEN '2026-03-01' AND '2026-03-31'", """
        SELECT order_id, customer_name, ordered_at FROM order_log
        WHERE ordered_at BETWEEN '2026-03-01' AND '2026-03-31' ORDER BY order_id
    """)
    show(conn, "6. 끝을 다음 달 1일로 바꾸고 < 로 끊으면", """
        SELECT order_id, customer_name, ordered_at FROM order_log
        WHERE ordered_at >= '2026-03-01' AND ordered_at < '2026-04-01' ORDER BY order_id
    """)
    show(conn, "7. 3월 31일 주문의 문자열 비교 결과", """
        SELECT '2026-03-31 14:20:00' <= '2026-03-31' AS le_cmp,
               '2026-03-31 14:20:00' <  '2026-04-01' AS lt_cmp
    """)
    show(conn, "8. 날짜 함수로 끊으면 — date(ordered_at)", """
        SELECT order_id, customer_name, ordered_at FROM order_log
        WHERE date(ordered_at) BETWEEN '2026-03-01' AND '2026-03-31' ORDER BY order_id
    """)

    print("### 3. IN — 목록과 하위 질의")
    show(conn, "9. 상태 목록 — IN", """
        SELECT order_id, customer_name, status FROM order_log
        WHERE status IN ('paid', 'shipped') ORDER BY order_id
    """)
    show(conn, "10. 같은 조건을 OR 로 풀어 쓰면", """
        SELECT order_id, customer_name, status FROM order_log
        WHERE status = 'paid' OR status = 'shipped' ORDER BY order_id
    """)
    show(conn, "11. 빈 목록 — IN ()", """
        SELECT order_id FROM order_log WHERE status IN ()
    """)
    show(conn, "12. 환불 요청이 있는 주문 — IN 하위 질의", """
        SELECT order_id, customer_name FROM order_log
        WHERE order_id IN (SELECT order_id FROM refund_request) ORDER BY order_id
    """)
    show(conn, "13. 환불 요청이 없는 주문 — NOT IN 하위 질의 (NULL 이 섞여 있다)", """
        SELECT order_id, customer_name FROM order_log
        WHERE order_id NOT IN (SELECT order_id FROM refund_request) ORDER BY order_id
    """)
    show(conn, "14. NULL 을 걸러낸 NOT IN", """
        SELECT order_id, customer_name FROM order_log
        WHERE order_id NOT IN (
            SELECT order_id FROM refund_request WHERE order_id IS NOT NULL
        ) ORDER BY order_id
    """)
    show(conn, "15. 같은 질문을 NOT EXISTS 로", """
        SELECT o.order_id, o.customer_name FROM order_log o
        WHERE NOT EXISTS (
            SELECT 1 FROM refund_request r WHERE r.order_id = o.order_id
        ) ORDER BY o.order_id
    """)
    show(conn, "16. IN 에 NULL 이 섞여도 찾는 값이 있으면 참이다", """
        SELECT 3 IN (1, 3, NULL) AS found, 2 IN (1, 3, NULL) AS not_found,
               2 NOT IN (1, 3, NULL) AS negated
    """)

    print("### 4. 왼쪽 식은 몇 번 계산되는가")
    calls = {"n": 0}

    def bump() -> int:
        calls["n"] += 1
        return 3

    # deterministic=False 가 기본이라 SQLite 가 호출을 묶지 않는다.
    conn.create_function("bump", 0, bump)

    calls["n"] = 0
    conn.execute("SELECT bump() BETWEEN 1 AND 5").fetchone()
    between_calls = calls["n"]
    calls["n"] = 0
    conn.execute("SELECT bump() >= 1 AND bump() <= 5").fetchone()
    expanded_calls = calls["n"]
    print(f"-- 17. bump() BETWEEN 1 AND 5        → bump() 호출 {between_calls}회")
    print(f"-- 18. bump() >= 1 AND bump() <= 5   → bump() 호출 {expanded_calls}회\n")

    print("### 5. 인덱스를 어떻게 타는가")
    conn.execute("CREATE INDEX ix_order_log_amount ON order_log(amount)")
    conn.execute("CREATE INDEX ix_order_log_status ON order_log(status)")
    conn.execute("ANALYZE")
    for label, sql in [
        ("19. BETWEEN — 범위", "SELECT order_id FROM order_log WHERE amount BETWEEN 10000 AND 50000"),
        ("20. IN 목록 — 값 세 개", "SELECT order_id FROM order_log WHERE status IN ('paid','shipped','pending')"),
        ("21. 컬럼을 함수로 감싸면", "SELECT order_id FROM order_log WHERE abs(amount) BETWEEN 10000 AND 50000"),
    ]:
        print(f"-- {label}")
        print("   " + " ".join(sql.split()))
        for row in conn.execute("EXPLAIN QUERY PLAN " + sql):
            print(f"   {row[3]}")
        print()

    conn.close()


if __name__ == "__main__":
    main()
