"""BEGIN 의 세 모드가 잠금을 언제 잡는지 두 연결로 대조한다.

연결 A 가 트랜잭션을 열고, 연결 B 가 읽거나 쓰려고 시도한다.
B 가 통과하는지 SQLITE_BUSY 를 받는지를 모드마다 기록한다.

timeout 을 0 으로 두는 이유는, 기본값(5초)이면 B 가 기다리다 성공해 버려서
"잠금을 잡았다"는 사실 자체가 출력에 안 나타나기 때문이다.
"""

from __future__ import annotations

import os
import sqlite3

from dbshow import print_dataset, print_environment

WORK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "probe_work")
DB_PATH = os.path.join(WORK_DIR, "ledger.db")

SCHEMA = """
CREATE TABLE account (
    id      INTEGER PRIMARY KEY,
    owner   TEXT    NOT NULL,
    balance INTEGER NOT NULL
);
"""

ROWS = [
    (1, "김서준", 120000),
    (2, "이하은", 80000),
    (3, "박도윤", 45000),
]


def build_database() -> sqlite3.Connection:
    """빈 파일에서 다시 만든다. 앞 시나리오가 남긴 상태를 물려받지 않게."""
    os.makedirs(WORK_DIR, exist_ok=True)
    for suffix in ("", "-journal", "-wal", "-shm"):
        path = DB_PATH + suffix
        if os.path.exists(path):
            os.remove(path)

    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO account VALUES (?, ?, ?)", ROWS)
    return conn


def open_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH, timeout=0, isolation_level=None)


def attempt(who: str, conn: sqlite3.Connection, sql: str) -> None:
    """한 문장을 실행하고 통과했는지 어떤 오류로 막혔는지 한 줄로 찍는다."""
    label = f"  {who}: {sql}"
    try:
        conn.execute(sql)
    except sqlite3.Error as exc:
        print(f"{label}\n       -> {type(exc).__name__}: {exc}")
    else:
        print(f"{label}\n       -> OK")


def scenario(title: str) -> None:
    print()
    print("-" * 64)
    print(title)
    print("-" * 64)


def run_deferred_delays_the_lock() -> None:
    scenario("1. DEFERRED — BEGIN 만으로는 아무것도 잡지 않는다")
    a, b = open_connection(), open_connection()
    attempt("A", a, "BEGIN DEFERRED")
    attempt("B", b, "UPDATE account SET balance = balance - 1 WHERE id = 3")
    print("       (A 가 아직 아무 문장도 안 돌렸으므로 B 의 쓰기가 통과한다)")
    attempt("A", a, "SELECT SUM(balance) FROM account")
    attempt("B", b, "UPDATE account SET balance = balance - 1 WHERE id = 3")
    attempt("A", a, "COMMIT")
    a.close()
    b.close()


def run_deferred_upgrade_fails() -> None:
    scenario("2. DEFERRED — 읽다가 쓰기로 올라가는 순간 막힐 수 있다")
    a, b = open_connection(), open_connection()
    attempt("A", a, "BEGIN DEFERRED")
    attempt("A", a, "SELECT balance FROM account WHERE id = 1")
    attempt("B", b, "BEGIN IMMEDIATE")
    attempt("A", a, "UPDATE account SET balance = balance + 1 WHERE id = 1")
    print("       (A 는 읽기로 시작해 쓰기 권한이 없고, 그 사이 B 가 가져갔다)")
    attempt("B", b, "ROLLBACK")
    attempt("A", a, "ROLLBACK")
    a.close()
    b.close()


def run_immediate_takes_write_lock() -> None:
    scenario("3. IMMEDIATE — BEGIN 하는 순간 쓰기 자리를 잡는다")
    a, b = open_connection(), open_connection()
    attempt("A", a, "BEGIN IMMEDIATE")
    attempt("B", b, "SELECT COUNT(*) FROM account")
    attempt("B", b, "BEGIN IMMEDIATE")
    attempt("B", b, "UPDATE account SET balance = 0 WHERE id = 2")
    attempt("A", a, "COMMIT")
    a.close()
    b.close()


def run_exclusive_blocks_readers() -> None:
    scenario("4. EXCLUSIVE — 읽기까지 막는다 (rollback journal 모드)")
    a, b = open_connection(), open_connection()
    attempt("A", a, "BEGIN EXCLUSIVE")
    attempt("B", b, "SELECT COUNT(*) FROM account")
    attempt("A", a, "COMMIT")
    attempt("B", b, "SELECT COUNT(*) FROM account")
    a.close()
    b.close()


def run_exclusive_under_wal() -> None:
    scenario("5. 같은 EXCLUSIVE 를 WAL 모드에서")
    setup = open_connection()
    mode = setup.execute("PRAGMA journal_mode = WAL").fetchone()[0]
    print(f"  journal_mode -> {mode}")
    setup.close()

    a, b = open_connection(), open_connection()
    attempt("A", a, "BEGIN EXCLUSIVE")
    attempt("B", b, "SELECT COUNT(*) FROM account")
    attempt("B", b, "UPDATE account SET balance = 0 WHERE id = 2")
    attempt("A", a, "COMMIT")
    a.close()
    b.close()

    # journal_mode 를 되돌리는 쪽은 파일을 혼자 잡아야 한다.
    # 위 두 연결을 먼저 닫지 않으면 이 PRAGMA 가 SQLITE_BUSY 로 떨어진다.
    restore = open_connection()
    mode = restore.execute("PRAGMA journal_mode = DELETE").fetchone()[0]
    print(f"  journal_mode -> {mode}")
    restore.close()


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)
    conn.close()

    run_deferred_delays_the_lock()
    run_deferred_upgrade_fails()
    run_immediate_takes_write_lock()
    run_exclusive_blocks_readers()
    run_exclusive_under_wal()

    print()
    print("-" * 64)
    print("마지막 상태")
    print("-" * 64)
    final = sqlite3.connect(DB_PATH, isolation_level=None)
    print_dataset(final)
    final.close()


if __name__ == "__main__":
    main()
