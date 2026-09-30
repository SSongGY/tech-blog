"""SQLite 에서 COMMIT·ROLLBACK·SAVEPOINT 가 어떻게 동작하는지 두 세션으로 확인한다.

두 연결이 같은 파일을 보게 하려고 메모리 DB 대신 임시 폴더의 파일 DB 를 쓴다.
isolation_level=None 으로 열어 파이썬 모듈이 BEGIN 을 몰래 끼워 넣지 않게 한다.
그래야 화면에 찍힌 문장이 SQLite 가 받은 문장 전부가 된다.
"""

import os
import sqlite3
import tempfile

from dbshow import print_dataset, print_environment

SCHEMA = """
CREATE TABLE account (
    account_id  INTEGER PRIMARY KEY,
    owner       TEXT NOT NULL,
    balance     INTEGER NOT NULL CHECK (balance >= 0)
);
CREATE TABLE transfer_log (
    log_id      INTEGER PRIMARY KEY,
    memo        TEXT NOT NULL
);
INSERT INTO account VALUES (1, '김하나', 10000), (2, '이두리', 5000);
"""


def open_session(path):
    # timeout=0: 잠금을 만나면 기다리지 않고 바로 오류를 돌려받는다
    return sqlite3.connect(path, isolation_level=None, timeout=0)


def run(label, conn, sql):
    """실패해도 멈추지 않는다. 세션 이름과 트랜잭션 진행 여부를 함께 찍는다."""
    try:
        conn.execute(sql)
        result = "성공"
    except sqlite3.Error as exc:
        result = f"{type(exc).__name__}: {exc}"
    state = "진행 중" if conn.in_transaction else "없음"
    print(f"   [{label}] {sql:<58} → {result}  (트랜잭션 {state})")


def balances(label, conn):
    rows = conn.execute("SELECT account_id, balance FROM account ORDER BY 1").fetchall()
    text = ", ".join(f"{a}번={b}" for a, b in rows)
    print(f"   [{label}] 잔액 조회 → {text}")


def memos(label, conn):
    rows = conn.execute("SELECT memo FROM transfer_log ORDER BY log_id").fetchall()
    print(f"   [{label}] transfer_log → {[r[0] for r in rows]}")


def section(title):
    print()
    print(f"== {title}")


def main():
    folder = tempfile.mkdtemp()
    path = os.path.join(folder, "bank.db")
    a = open_session(path)
    a.executescript(SCHEMA)
    b = open_session(path)

    print_environment({"journal_mode": a.execute("PRAGMA journal_mode").fetchone()[0]})
    print_dataset(a)

    section("1. BEGIN 없이 쓰면 문장마다 바로 저장된다 (자동 커밋)")
    run("A", a, "UPDATE account SET balance = balance + 100 WHERE account_id = 1")
    balances("B", b)
    run("A", a, "UPDATE account SET balance = balance - 100 WHERE account_id = 1")

    section("2. BEGIN ~ COMMIT — 끝나기 전에는 다른 세션에 안 보인다")
    run("A", a, "BEGIN")
    run("A", a, "UPDATE account SET balance = balance - 3000 WHERE account_id = 1")
    run("A", a, "UPDATE account SET balance = balance + 3000 WHERE account_id = 2")
    balances("A", a)
    balances("B", b)
    run("A", a, "COMMIT")
    balances("B", b)

    section("3. ROLLBACK — BEGIN 이후 한 일을 전부 되돌린다")
    run("A", a, "BEGIN")
    run("A", a, "UPDATE account SET balance = 0 WHERE account_id = 1")
    balances("A", a)
    run("A", a, "ROLLBACK")
    balances("A", a)

    section("4. 쓰는 중인 트랜잭션이 있으면 다른 세션은 쓰지 못한다")
    run("A", a, "BEGIN")
    run("A", a, "UPDATE account SET balance = balance - 1 WHERE account_id = 1")
    run("B", b, "UPDATE account SET balance = balance + 1 WHERE account_id = 2")
    balances("B", b)
    run("A", a, "ROLLBACK")
    run("B", b, "UPDATE account SET balance = balance + 0 WHERE account_id = 2")

    section("5. SAVEPOINT — 중간 지점까지만 되돌린다")
    run("A", a, "BEGIN")
    run("A", a, "INSERT INTO transfer_log (memo) VALUES ('첫째')")
    run("A", a, "SAVEPOINT sp1")
    run("A", a, "INSERT INTO transfer_log (memo) VALUES ('둘째')")
    memos("A", a)
    run("A", a, "ROLLBACK TO sp1")
    memos("A", a)
    run("A", a, "INSERT INTO transfer_log (memo) VALUES ('셋째')")
    run("A", a, "ROLLBACK TO sp1")
    memos("A", a)
    run("A", a, "INSERT INTO transfer_log (memo) VALUES ('넷째')")
    run("A", a, "RELEASE sp1")
    run("A", a, "ROLLBACK TO sp1")
    run("A", a, "COMMIT")
    memos("B", b)

    section("6. BEGIN 없이 SAVEPOINT 로 시작하면 RELEASE 가 COMMIT 이 된다")
    run("A", a, "SAVEPOINT outer_sp")
    run("A", a, "INSERT INTO transfer_log (memo) VALUES ('다섯째')")
    memos("B", b)
    run("A", a, "RELEASE outer_sp")
    memos("B", b)

    section("7. 트랜잭션 도중 한 문장이 실패하면")
    run("A", a, "BEGIN")
    run("A", a, "UPDATE account SET balance = balance + 500 WHERE account_id = 2")
    run("A", a, "UPDATE account SET balance = balance - 99999 WHERE account_id = 1")
    balances("A", a)
    run("A", a, "ROLLBACK")
    balances("A", a)

    section("8. COMMIT 없이 연결을 닫으면")
    c = open_session(path)
    run("C", c, "BEGIN")
    run("C", c, "UPDATE account SET balance = 1 WHERE account_id = 1")
    c.close()
    print("   [C] 연결 종료 (COMMIT 하지 않음)")
    balances("A", a)

    b.close()
    a.close()


if __name__ == "__main__":
    main()
