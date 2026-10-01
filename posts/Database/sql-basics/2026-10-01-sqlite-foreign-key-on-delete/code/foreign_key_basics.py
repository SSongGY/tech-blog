"""외래 키가 무엇을 막고, 부모 행을 지울 때 자식 행에 무슨 일이 일어나는지 하나씩 부딪혀 본다.

문장마다 성공/에러를 찍고, 바뀐 뒤의 표를 다시 찍는다.
에러 메시지는 SQLite 가 돌려준 문구 그대로다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

SCHEMA = """
CREATE TABLE customer (
  customer_id INTEGER PRIMARY KEY,
  name        TEXT    NOT NULL
);
CREATE TABLE sale_order (
  order_id    INTEGER PRIMARY KEY,
  customer_id INTEGER REFERENCES customer (customer_id),
  amount      INTEGER NOT NULL
);
INSERT INTO customer VALUES (1, '김서준'), (2, '이하윤'), (3, '박도윤');
INSERT INTO sale_order VALUES (101, 1, 120), (102, 1, 80), (103, 2, 150);
"""


def run(conn: sqlite3.Connection, sql: str) -> None:
    print(f"   {sql}")
    try:
        cur = conn.execute(sql)
        print(f"   성공 · 바뀐 행 {cur.rowcount}")
    except sqlite3.Error as exc:
        print(f"   에러: {exc}")


def show(conn: sqlite3.Connection, sql: str) -> None:
    print(f"   {sql}")
    rows = conn.execute(sql).fetchall()
    for row in rows:
        print("   " + " | ".join("NULL" if v is None else str(v) for v in row))
    if not rows:
        print("   (행 없음)")


def section(title: str) -> None:
    print(f"\n-- {title}")


def fresh(child_clause: str, default: str = "") -> sqlite3.Connection:
    """자식 표의 REFERENCES 절만 바꿔 같은 데이터로 새로 만든다."""
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.execute("PRAGMA foreign_keys = ON")
    # ON DELETE 는 REFERENCES 절의 일부라서 DEFAULT 는 그 앞에 와야 한다
    column = f"{default} REFERENCES customer (customer_id) {child_clause}"
    conn.executescript(SCHEMA.replace(
        "REFERENCES customer (customer_id)", column.strip()))
    print(f"   [customer_id INTEGER {column.strip()}]")
    return conn


def count_steps(conn: sqlite3.Connection, sql: str) -> int:
    # 계획에는 외래 키 검사가 안 보이므로, 엔진이 실제로 돈 명령 수로 일의 양을 잰다
    steps = 0

    def tick() -> int:
        nonlocal steps
        steps += 1
        return 0

    conn.set_progress_handler(tick, 1)
    conn.execute(sql)
    conn.set_progress_handler(None, 1)
    return steps


def main() -> None:
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.executescript(SCHEMA)
    print_environment()
    print_dataset(conn)

    section("1. 기본값 — 외래 키 검사가 꺼져 있다")
    show(conn, "PRAGMA foreign_keys")
    run(conn, "INSERT INTO sale_order VALUES (104, 99, 70)")
    run(conn, "DELETE FROM customer WHERE customer_id = 2")
    show(conn, "SELECT * FROM sale_order ORDER BY order_id")

    section("2. 켜도 이미 들어간 행은 검사하지 않는다")
    run(conn, "PRAGMA foreign_keys = ON")
    show(conn, "PRAGMA foreign_keys")
    show(conn, "PRAGMA foreign_key_check")
    print("   -- 표·rowid·부모 표·몇 번째 외래 키인지")

    section("3. 트랜잭션 안에서는 켜고 끌 수 없다")
    run(conn, "BEGIN")
    run(conn, "PRAGMA foreign_keys = OFF")
    show(conn, "PRAGMA foreign_keys")
    run(conn, "ROLLBACK")

    section("4. 켠 뒤 — 없는 부모를 가리키는 행을 막는다")
    conn = fresh("")
    run(conn, "INSERT INTO sale_order VALUES (104, 99, 70)")
    run(conn, "INSERT INTO sale_order VALUES (104, NULL, 70)")
    run(conn, "UPDATE sale_order SET customer_id = 98 WHERE order_id = 101")

    section("5. 켠 뒤 — 자식이 있는 부모를 못 지운다 (기본 동작 NO ACTION)")
    run(conn, "DELETE FROM customer WHERE customer_id = 1")
    run(conn, "DELETE FROM customer WHERE customer_id = 3")
    run(conn, "UPDATE customer SET customer_id = 10 WHERE customer_id = 2")

    for clause in ("ON DELETE CASCADE", "ON DELETE SET NULL"):
        section(f"6. {clause}")
        conn = fresh(clause)
        run(conn, "DELETE FROM customer WHERE customer_id = 1")
        show(conn, "SELECT * FROM sale_order ORDER BY order_id")

    section("7. ON DELETE SET DEFAULT — 기본값도 부모에 있어야 한다")
    conn = fresh("ON DELETE SET DEFAULT", default="DEFAULT 3")
    run(conn, "DELETE FROM customer WHERE customer_id = 1")
    show(conn, "SELECT * FROM sale_order ORDER BY order_id")
    conn = fresh("ON DELETE SET DEFAULT", default="DEFAULT 0")
    run(conn, "DELETE FROM customer WHERE customer_id = 1")

    section("8. NO ACTION 과 RESTRICT — 지연 제약에서 갈린다")
    for clause in ("ON DELETE NO ACTION", "ON DELETE RESTRICT"):
        conn = fresh(f"{clause} DEFERRABLE INITIALLY DEFERRED")
        run(conn, "BEGIN")
        run(conn, "DELETE FROM customer WHERE customer_id = 1")
        run(conn, "INSERT INTO customer VALUES (1, '김서준(재등록)')")
        run(conn, "COMMIT")
        if conn.in_transaction:
            run(conn, "ROLLBACK")

    section("9. 부모 키는 PRIMARY KEY 나 UNIQUE 여야 한다")
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("CREATE TABLE customer (customer_id INTEGER PRIMARY KEY, email TEXT)")
    conn.execute("CREATE TABLE sale_order (order_id INTEGER PRIMARY KEY, "
                 "email TEXT REFERENCES customer (email))")
    run(conn, "INSERT INTO customer VALUES (1, 'a@example.com')")
    run(conn, "INSERT INTO sale_order VALUES (101, 'a@example.com')")

    section("10. 자식 키 인덱스 — 부모 한 행을 지울 때 엔진이 돈 명령 수")
    for indexed in (False, True):
        conn = fresh("")
        conn.execute("INSERT INTO customer VALUES (4, '최시우')")
        conn.execute("WITH RECURSIVE n(i) AS (SELECT 1 UNION ALL SELECT i + 1 FROM n "
                     "WHERE i < 20000) INSERT INTO sale_order "
                     "SELECT 1000 + i, 1 + i % 3, i FROM n")
        if indexed:
            conn.execute("CREATE INDEX sale_order_customer_id ON sale_order (customer_id)")
        steps = count_steps(conn, "DELETE FROM customer WHERE customer_id = 4")
        label = "인덱스 있음" if indexed else "인덱스 없음"
        print(f"   자식 20003행 · {label}: {steps}")


if __name__ == "__main__":
    main()
