"""INSERT·UPDATE·DELETE 뒤에 RETURNING 을 붙이면 무엇이 돌아오는지 확인한다.

주문 표(order_item)에 행을 넣고 고치고 지우면서, 자동으로 매겨진 키와 기본값을
다시 조회하지 않고 받는 법을 본다. 트리거가 바꾼 값과 트리거가 쓴 다른 표의 행이
RETURNING 에 나오는지, 결과를 다 읽지 않아도 변경은 이미 끝났는지도 본다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

SCHEMA = """
CREATE TABLE order_item (
    order_id  INTEGER PRIMARY KEY,
    customer  TEXT    NOT NULL,
    amount    INTEGER NOT NULL,
    status    TEXT    NOT NULL DEFAULT '접수'
);
CREATE TABLE order_log (
    log_id    INTEGER PRIMARY KEY,
    order_id  INTEGER NOT NULL,
    note      TEXT    NOT NULL
);
CREATE TABLE daily_total (
    customer  TEXT PRIMARY KEY,
    total     INTEGER NOT NULL
);
-- 큰 금액 주문은 넣자마자 상태를 '검토'로 바꾸고 기록을 남긴다
CREATE TRIGGER trg_order_review AFTER INSERT ON order_item
WHEN NEW.amount >= 100000
BEGIN
    UPDATE order_item SET status = '검토' WHERE order_id = NEW.order_id;
    INSERT INTO order_log (order_id, note) VALUES (NEW.order_id, '고액 주문 검토');
END;
"""

SEED = [
    (1, "김하늘", 12000, "접수"),
    (2, "이바다", 8000, "배송"),
]


def build_database() -> sqlite3.Connection:
    # autocommit=True: 문장마다 바로 반영해 트랜잭션 상태가 결과에 섞이지 않게 한다
    conn = sqlite3.connect(":memory:", autocommit=True)
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO order_item VALUES (?, ?, ?, ?)", SEED)
    conn.execute("INSERT INTO daily_total VALUES ('김하늘', 12000)")
    return conn


def heading(title: str) -> None:
    print(f"\n-- {title}")


def run(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> None:
    """돌린 문장과 돌아온 행을 찍는다. 에러도 결과로 찍는다."""
    print(f"   {' '.join(sql.split())}")
    try:
        rows = conn.execute(sql, params).fetchall()
    except sqlite3.Error as exc:
        print(f"   에러: {type(exc).__name__}: {exc}")
        return
    for row in rows:
        print("      " + " | ".join("NULL" if v is None else repr(v) for v in row))
    print(f"   ({len(rows)}행)")


def show(conn: sqlite3.Connection, sql: str) -> None:
    run(conn, sql)


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)
    print("=" * 64)
    print("질의")
    print("=" * 64)

    heading("1. RETURNING 없이 — 넣고 나서 lastrowid 로 키를 얻고 다시 조회")
    cur = conn.execute(
        "INSERT INTO order_item (customer, amount) VALUES ('박구름', 15000)"
    )
    print(f"   cursor.lastrowid = {cur.lastrowid}")
    show(conn, f"SELECT order_id, status FROM order_item WHERE order_id = {cur.lastrowid}")

    heading("2. RETURNING — 키와 기본값을 한 문장으로")
    run(conn, "INSERT INTO order_item (customer, amount) VALUES ('최노을', 9000) "
              "RETURNING order_id, status")

    heading("3. 여러 행을 한 번에 넣으면 — lastrowid 는 마지막 하나뿐")
    cur = conn.execute(
        "INSERT INTO order_item (customer, amount) VALUES "
        "('정새벽', 3000), ('정새벽', 4000), ('정새벽', 5000)"
    )
    print(f"   cursor.lastrowid = {cur.lastrowid}")
    run(conn, "INSERT INTO order_item (customer, amount) VALUES "
              "('한별', 1000), ('한별', 2000), ('한별', 3000) RETURNING order_id")

    heading("4. 식과 별칭, * 도 쓸 수 있다")
    run(conn, "INSERT INTO order_item (customer, amount) VALUES ('윤솔', 22000) "
              "RETURNING order_id AS new_id, amount / 11 AS vat, upper('ok') AS mark")
    run(conn, "INSERT INTO order_item (customer, amount) VALUES ('윤솔', 1500) RETURNING *")

    heading("5. UPDATE 는 바뀐 뒤 값, DELETE 는 지우기 전 값을 돌려준다")
    run(conn, "UPDATE order_item SET amount = amount + 500 WHERE customer = '정새벽' "
              "RETURNING order_id, amount")
    run(conn, "DELETE FROM order_item WHERE customer = '한별' RETURNING order_id, amount")
    run(conn, "UPDATE order_item SET status = '취소' WHERE customer = '없는사람' "
              "RETURNING order_id")

    heading("6. 트리거가 바꾼 값은 RETURNING 에 나오지 않는다")
    run(conn, "INSERT INTO order_item (customer, amount) VALUES ('강바람', 150000) "
              "RETURNING order_id, status")
    show(conn, "SELECT order_id, status FROM order_item WHERE customer = '강바람'")
    show(conn, "SELECT log_id, order_id, note FROM order_log")

    heading("7. 결과를 한 행만 읽어도 변경은 이미 전부 끝나 있다")
    before = conn.execute("SELECT COUNT(*) FROM order_item").fetchone()[0]
    cur = conn.execute(
        "INSERT INTO order_item (customer, amount) VALUES "
        "('서이슬', 100), ('서이슬', 200), ('서이슬', 300) RETURNING order_id"
    )
    first = cur.fetchone()
    after = conn.execute("SELECT COUNT(*) FROM order_item").fetchone()[0]
    print(f"   읽은 첫 행 = {first}, 넣기 전 {before}행 -> 한 행만 읽은 뒤 {after}행")
    print(f"   남은 결과 = {cur.fetchall()}")

    heading("8. UPSERT 는 새로 넣은 행과 갱신한 행을 함께 돌려준다")
    run(conn, "INSERT INTO daily_total (customer, total) VALUES "
              "('김하늘', 3000), ('윤솔', 22000) "
              "ON CONFLICT (customer) DO UPDATE SET total = total + excluded.total "
              "RETURNING customer, total")

    heading("9. 안 되는 것 — 집계 함수, 하위 질의로 쓰기, 다른 표 참조")
    run(conn, "UPDATE order_item SET status = '배송' WHERE customer = '정새벽' "
              "RETURNING count(*)")
    run(conn, "SELECT * FROM (INSERT INTO order_item (customer, amount) "
              "VALUES ('오류', 1) RETURNING order_id)")
    run(conn, "UPDATE order_item SET status = '배송' FROM daily_total d "
              "WHERE order_item.customer = d.customer RETURNING d.total")

    heading("10. 파이썬 executemany 에는 RETURNING 을 쓸 수 없다")
    try:
        conn.executemany(
            "INSERT INTO order_item (customer, amount) VALUES (?, ?) RETURNING order_id",
            [("문가람", 10), ("문가람", 20)],
        )
        print("   성공")
    except sqlite3.Error as exc:
        print(f"   에러: {type(exc).__name__}: {exc}")
    show(conn, "SELECT order_id, customer, amount FROM order_item WHERE customer = '문가람'")

    heading("10-2. 기본 트랜잭션 모드에서 같은 executemany — 에러 뒤 트랜잭션 상태")
    legacy = sqlite3.connect(":memory:")  # autocommit 을 주지 않은 파이썬 기본 동작
    legacy.execute("CREATE TABLE t (t_id INTEGER PRIMARY KEY, v INTEGER)")
    try:
        legacy.executemany("INSERT INTO t (v) VALUES (?) RETURNING t_id", [(10,), (20,)])
    except sqlite3.Error as exc:
        print(f"   에러: {type(exc).__name__}: {exc}")
    count = legacy.execute("SELECT COUNT(*) FROM t").fetchone()[0]
    print(f"   in_transaction = {legacy.in_transaction}, 표의 행 수 = {count}")
    legacy.rollback()
    count = legacy.execute("SELECT COUNT(*) FROM t").fetchone()[0]
    print(f"   rollback() 뒤 행 수 = {count}")
    legacy.close()

    heading("11. rowcount 는 결과를 다 읽어야 바뀐다")
    cur = conn.execute(
        "UPDATE order_item SET amount = amount + 1 WHERE customer = '서이슬' "
        "RETURNING order_id"
    )
    print(f"   읽기 전 rowcount = {cur.rowcount}")
    rows = cur.fetchall()
    print(f"   fetchall() {len(rows)}행 읽은 뒤 rowcount = {cur.rowcount}")

    heading("최종 상태")
    show(conn, "SELECT * FROM order_item ORDER BY order_id")
    show(conn, "SELECT * FROM daily_total ORDER BY customer")
    conn.close()


if __name__ == "__main__":
    main()
