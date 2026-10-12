"""트리거 기본 — BEFORE·AFTER, NEW·OLD, 실패 전파, 숨은 비용을 SQLite 로 돌려 본다.

보는 것: 변경 이력 표가 트리거로 채워지는 것, 여러 행 UPDATE 에서 트리거가 행마다
도는 것, 트리거가 실패하면 원래 문장 전체가 되돌아가는 것, RAISE(IGNORE) 가 에러 없이
행을 버리는 것, UPDATE OF 에 틀린 컬럼 이름을 써도 받아들여지는 것, rowcount 에
트리거의 변경이 안 잡히는 것, 10만 행 UPDATE 에서 트리거가 더하는 시간,
여러 행 UPDATE 에서 BEFORE·AFTER 가 행마다 번갈아 도는 순서.
"""

import sqlite3
import time

from dbshow import print_dataset, print_environment

BULK_ROWS = 100_000
REPEAT = 5

SCHEMA = """
CREATE TABLE account (
    account_id INTEGER PRIMARY KEY,
    owner      TEXT    NOT NULL,
    balance    INTEGER NOT NULL
);
CREATE TABLE account_history (
    history_id  INTEGER PRIMARY KEY,
    account_id  INTEGER NOT NULL,
    action      TEXT    NOT NULL,
    old_balance INTEGER,
    new_balance INTEGER
);
"""

ACCOUNTS = [
    (1, "김하나", 50000),
    (2, "이두리", 120000),
    (3, "박세미", 8000),
]

# 이력 트리거 셋. INSERT 에는 OLD 가, DELETE 에는 NEW 가 없다.
AUDIT_TRIGGERS = """
CREATE TRIGGER tr_account_insert AFTER INSERT ON account
BEGIN
    INSERT INTO account_history (account_id, action, old_balance, new_balance)
    VALUES (NEW.account_id, 'INSERT', NULL, NEW.balance);
END;
CREATE TRIGGER tr_account_update AFTER UPDATE OF balance ON account
WHEN OLD.balance IS NOT NEW.balance
BEGIN
    INSERT INTO account_history (account_id, action, old_balance, new_balance)
    VALUES (NEW.account_id, 'UPDATE', OLD.balance, NEW.balance);
END;
CREATE TRIGGER tr_account_delete AFTER DELETE ON account
BEGIN
    INSERT INTO account_history (account_id, action, old_balance, new_balance)
    VALUES (OLD.account_id, 'DELETE', OLD.balance, NULL);
END;
"""


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO account VALUES (?, ?, ?)", ACCOUNTS)
    return conn


def run(conn: sqlite3.Connection, title: str, sql: str) -> None:
    print(f"\n-- {title}")
    for line in sql.strip().splitlines():
        print(f"   {line}")
    try:
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
    except sqlite3.Error as exc:
        print(f"   에러: {exc}")
        return
    if cursor.description is None:
        print(f"   (rowcount={cursor.rowcount})")
        return
    header = [d[0] for d in cursor.description]
    print("   => " + " | ".join(header))
    for row in rows:
        print("      " + " | ".join("NULL" if v is None else str(v) for v in row))
    print(f"   ({len(rows)}행)")


def show(conn: sqlite3.Connection, title: str, sql: str) -> None:
    """확인용 조회. 질의문은 찍지 않고 결과만 찍는다."""
    print(f"   [{title}]")
    cursor = conn.execute(sql)
    header = [d[0] for d in cursor.description]
    print("      " + " | ".join(header))
    for row in cursor.fetchall():
        print("      " + " | ".join("NULL" if v is None else str(v) for v in row))


def section_audit(conn: sqlite3.Connection) -> None:
    print("\n=== 1. AFTER 트리거로 변경 이력 채우기 ===")
    conn.executescript(AUDIT_TRIGGERS)
    run(conn, "1-A. 새 계좌", "INSERT INTO account VALUES (4, '최네모', 30000)")
    run(conn, "1-B. 한 행 출금", "UPDATE account SET balance = balance - 10000 WHERE account_id = 1")
    run(conn, "1-C. 세 행에 이자", "UPDATE account SET balance = balance + 100 WHERE account_id IN (1, 2, 3)")
    run(conn, "1-D. 잔액이 그대로인 UPDATE (WHEN 조건)", "UPDATE account SET balance = balance WHERE account_id = 2")
    run(conn, "1-E. 이름만 바꾸는 UPDATE (UPDATE OF balance)", "UPDATE account SET owner = '김하나나' WHERE account_id = 1")
    run(conn, "1-F. 계좌 해지", "DELETE FROM account WHERE account_id = 4")
    show(conn, "이력 표", "SELECT * FROM account_history ORDER BY history_id")
    print(f"   [total_changes] {conn.total_changes}  (트리거가 넣은 이력 행까지 센다)")


def section_before_guard(conn: sqlite3.Connection) -> None:
    print("\n=== 2. BEFORE 트리거로 막기 — RAISE(ABORT) ===")
    conn.execute("""
        CREATE TRIGGER tr_account_no_overdraft BEFORE UPDATE OF balance ON account
        WHEN NEW.balance < 0
        BEGIN
            SELECT RAISE(ABORT, '잔액이 음수가 된다');
        END
    """)
    before = conn.execute("SELECT count(*) FROM account_history").fetchone()[0]
    run(conn, "2-A. 잔액보다 많이 출금", "UPDATE account SET balance = balance - 9000 WHERE account_id = 3")
    run(conn, "2-B. 세 행 중 한 행만 음수가 되는 UPDATE",
        "UPDATE account SET balance = balance - 9000 WHERE account_id IN (1, 2, 3)")
    show(conn, "계좌 — 2-B 뒤", "SELECT account_id, balance FROM account ORDER BY account_id")
    after = conn.execute("SELECT count(*) FROM account_history").fetchone()[0]
    print(f"   [이력 행 수] 전 {before} → 후 {after}")


def section_after_failure(conn: sqlite3.Connection) -> None:
    print("\n=== 3. AFTER 트리거가 실패하면 원래 문장도 실패한다 ===")
    # 트리거 안의 INSERT 가 셋째 행(3번 계좌)에서만 PK 충돌로 깨지게 만든다.
    conn.executescript("""
        CREATE TABLE audit_lock (account_id INTEGER PRIMARY KEY);
        INSERT INTO audit_lock VALUES (3);
        CREATE TRIGGER tr_account_audit_lock AFTER UPDATE OF balance ON account
        WHEN NEW.account_id = 3
        BEGIN
            INSERT INTO audit_lock VALUES (NEW.account_id);
        END;
    """)
    show(conn, "계좌 — 실행 전", "SELECT account_id, balance FROM account ORDER BY account_id")
    history_before = conn.execute("SELECT count(*) FROM account_history").fetchone()[0]
    run(conn, "3-A. 세 행 UPDATE — 트리거가 3번 행에서 PK 충돌",
        "UPDATE account SET balance = balance + 1 WHERE account_id IN (1, 2, 3)")
    show(conn, "계좌 — 실행 뒤", "SELECT account_id, balance FROM account ORDER BY account_id")
    history_after = conn.execute("SELECT count(*) FROM account_history").fetchone()[0]
    print(f"   [이력 행 수] 전 {history_before} → 후 {history_after}")
    conn.execute("DROP TRIGGER tr_account_audit_lock")


def section_ignore(conn: sqlite3.Connection) -> None:
    print("\n=== 4. RAISE(IGNORE) — 에러 없이 행을 버린다 ===")
    conn.execute("""
        CREATE TRIGGER tr_account_skip_blank BEFORE INSERT ON account
        WHEN trim(NEW.owner) = ''
        BEGIN
            SELECT RAISE(IGNORE);
        END
    """)
    run(conn, "4-A. 이름이 빈 계좌", "INSERT INTO account VALUES (5, '  ', 1000)")
    run(conn, "4-B. 정상 계좌", "INSERT INTO account VALUES (6, '정여섯', 1000)")
    show(conn, "계좌", "SELECT account_id, owner FROM account WHERE account_id >= 5")


def section_update_of_typo(conn: sqlite3.Connection) -> None:
    print("\n=== 5. UPDATE OF 에 없는 컬럼 이름 ===")
    run(conn, "5-A. balanse (오타) 로 트리거 만들기", """
CREATE TRIGGER tr_account_typo AFTER UPDATE OF balanse ON account
BEGIN
    INSERT INTO account_history (account_id, action) VALUES (NEW.account_id, 'TYPO');
END""")
    run(conn, "5-B. balance 를 바꾸는 UPDATE", "UPDATE account SET balance = balance + 5 WHERE account_id = 6")
    run(conn, "5-C. TYPO 이력이 생겼는가", "SELECT count(*) AS typo_rows FROM account_history WHERE action = 'TYPO'")
    conn.execute("DROP TRIGGER tr_account_typo")


def section_rowcount(conn: sqlite3.Connection) -> None:
    print("\n=== 6. rowcount 는 트리거의 변경을 세지 않는다 ===")
    total_before = conn.total_changes
    cursor = conn.execute("UPDATE account SET balance = balance + 1 WHERE account_id IN (1, 2)")
    print(f"   UPDATE ... WHERE account_id IN (1, 2)")
    print(f"   rowcount={cursor.rowcount}, total_changes 증가분={conn.total_changes - total_before}")


def section_order() -> None:
    print("\n=== 9. 여러 행 UPDATE 에서 BEFORE·AFTER 가 도는 순서 ===")
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.executescript("""
        CREATE TABLE item (item_id INTEGER PRIMARY KEY, qty INTEGER NOT NULL);
        INSERT INTO item VALUES (1, 10), (2, 20), (3, 30);
        CREATE TABLE fire_log (seq INTEGER PRIMARY KEY, step TEXT, item_id INTEGER,
                               qty_sum INTEGER);
        CREATE TRIGGER tr_item_before BEFORE UPDATE ON item
        BEGIN
            INSERT INTO fire_log (step, item_id, qty_sum)
            VALUES ('BEFORE', NEW.item_id, (SELECT sum(qty) FROM item));
        END;
        CREATE TRIGGER tr_item_after AFTER UPDATE ON item
        BEGIN
            INSERT INTO fire_log (step, item_id, qty_sum)
            VALUES ('AFTER', NEW.item_id, (SELECT sum(qty) FROM item));
        END;
    """)
    print("   UPDATE item SET qty = qty + 1   (qty 합계 60 에서 시작)")
    conn.execute("UPDATE item SET qty = qty + 1")
    show(conn, "fire_log — qty_sum 은 트리거가 돈 순간의 표 합계", "SELECT * FROM fire_log ORDER BY seq")


def section_find_triggers(conn: sqlite3.Connection) -> None:
    print("\n=== 7. 표에 걸린 트리거 찾기 ===")
    run(conn, "7-A. sqlite_master", """
SELECT name, tbl_name FROM sqlite_master
WHERE type = 'trigger' ORDER BY name""")
    run(conn, "7-B. PRAGMA recursive_triggers (기본값)", "PRAGMA recursive_triggers")


def time_update(conn: sqlite3.Connection) -> float:
    best = float("inf")
    for _ in range(REPEAT):
        conn.execute("BEGIN")
        started = time.perf_counter()
        conn.execute("UPDATE bulk_account SET balance = balance + 1")
        best = min(best, time.perf_counter() - started)
        conn.execute("ROLLBACK")
    return best * 1000


def section_cost() -> None:
    print(f"\n=== 8. 숨은 비용 — {BULK_ROWS:,}행 UPDATE ===")
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.executescript("""
        CREATE TABLE bulk_account (account_id INTEGER PRIMARY KEY, balance INTEGER NOT NULL);
        CREATE TABLE bulk_history (
            history_id INTEGER PRIMARY KEY, account_id INTEGER,
            old_balance INTEGER, new_balance INTEGER);
    """)
    conn.executemany(
        "INSERT INTO bulk_account VALUES (?, ?)",
        ((i, i % 1000) for i in range(1, BULK_ROWS + 1)),
    )
    without_ms = time_update(conn)
    conn.execute("""
        CREATE TRIGGER tr_bulk_update AFTER UPDATE ON bulk_account
        BEGIN
            INSERT INTO bulk_history (account_id, old_balance, new_balance)
            VALUES (NEW.account_id, OLD.balance, NEW.balance);
        END
    """)
    with_ms = time_update(conn)
    print(f"   트리거 없음  {without_ms:8.1f} ms")
    print(f"   트리거 있음  {with_ms:8.1f} ms   ({with_ms / without_ms:.1f}배)")
    print(f"   (각 {REPEAT}회 중 최솟값, 매번 ROLLBACK)")


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)
    section_audit(conn)
    section_before_guard(conn)
    section_after_failure(conn)
    section_ignore(conn)
    section_update_of_typo(conn)
    section_rowcount(conn)
    section_find_triggers(conn)
    section_cost()
    section_order()


if __name__ == "__main__":
    main()
