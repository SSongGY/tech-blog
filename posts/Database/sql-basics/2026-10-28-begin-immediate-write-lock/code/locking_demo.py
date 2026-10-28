"""BEGIN 과 BEGIN IMMEDIATE 가 쓰기 잠금을 언제 잡는지 두 연결로 재현한다.

같은 파일에 두 연결을 붙여 놓고, 트랜잭션을 여는 방식만 바꿔 가며
어느 문장에서 SQLITE_BUSY 가 나오는지를 본다.
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
import time

from dbshow import print_dataset, print_environment

DB_PATH = os.path.join(tempfile.gettempdir(), "begin_immediate_demo.db")

SCHEMA = """
CREATE TABLE account (
    id      INTEGER PRIMARY KEY,
    owner   TEXT    NOT NULL,
    balance INTEGER NOT NULL CHECK (balance >= 0)
);
INSERT INTO account (id, owner, balance) VALUES
    (1, '가나',  1000),
    (2, '다라',   500);
"""


def build_database(journal_mode: str) -> None:
    """매 실험마다 같은 상태에서 출발하도록 파일을 다시 만든다."""
    for suffix in ("", "-wal", "-shm", "-journal"):
        path = DB_PATH + suffix
        if os.path.exists(path):
            os.remove(path)
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.execute(f"PRAGMA journal_mode = {journal_mode}")
    conn.executescript(SCHEMA)
    conn.close()


def connect(busy_timeout_ms: int = 0) -> sqlite3.Connection:
    # isolation_level=None 이라야 BEGIN 을 내가 직접 친다. 파이썬이 끼어들면
    # 어느 시점에 트랜잭션이 열렸는지가 흐려져서 이 실험이 성립하지 않는다.
    return sqlite3.connect(
        DB_PATH, isolation_level=None, timeout=busy_timeout_ms / 1000
    )


def step(label: str, conn: sqlite3.Connection, sql: str) -> None:
    started = time.perf_counter()
    try:
        conn.execute(sql)
        outcome = "OK"
    except sqlite3.Error as exc:
        outcome = exc.sqlite_errorname
    elapsed = time.perf_counter() - started
    print(f"  {label:<13} {sql:<56} {outcome:<22} {elapsed:5.2f}s")


def header(title: str) -> None:
    print()
    print(title)
    print("  " + "-" * 99)
    print(f"  {'연결':<11} {'문장':<54} {'결과':<20} {'소요':>6}")


# ----------------------------------------------------------------------
build_database("delete")
print_environment({"journal_mode": "delete (롤백 저널, 기본값)"})
initial = sqlite3.connect(DB_PATH)
print_dataset(initial)
initial.close()

header("[1] 롤백 저널 모드 · 두 연결 모두 BEGIN (= DEFERRED)")
a, b = connect(), connect()
step("A", a, "BEGIN")
step("B", b, "BEGIN")
step("A", a, "SELECT balance FROM account WHERE id = 1")
step("B", b, "SELECT balance FROM account WHERE id = 2")
step("A", a, "UPDATE account SET balance = balance - 100 WHERE id = 1")
step("B", b, "UPDATE account SET balance = balance + 100 WHERE id = 2")
step("A", a, "COMMIT")
step("B", b, "COMMIT")
step("A", a, "COMMIT")
a.close()
b.close()

# ----------------------------------------------------------------------
build_database("wal")
header("[2] WAL 모드 · 두 연결 모두 BEGIN (= DEFERRED)")
a, b = connect(), connect()
step("A", a, "BEGIN")
step("B", b, "BEGIN")
step("A", a, "SELECT balance FROM account WHERE id = 1")
step("B", b, "SELECT balance FROM account WHERE id = 2")
step("A", a, "UPDATE account SET balance = balance - 100 WHERE id = 1")
step("A", a, "COMMIT")
step("B", b, "UPDATE account SET balance = balance + 100 WHERE id = 2")
step("B", b, "ROLLBACK")
a.close()
b.close()

# ----------------------------------------------------------------------
build_database("wal")
header("[3] WAL 모드 · 두 연결 모두 BEGIN IMMEDIATE")
a, b = connect(), connect()
step("A", a, "BEGIN IMMEDIATE")
step("B", b, "BEGIN IMMEDIATE")
step("A", a, "SELECT balance FROM account WHERE id = 1")
step("A", a, "UPDATE account SET balance = balance - 100 WHERE id = 1")
step("A", a, "COMMIT")
step("B", b, "BEGIN IMMEDIATE")
step("B", b, "UPDATE account SET balance = balance + 100 WHERE id = 2")
step("B", b, "COMMIT")
a.close()
b.close()

# ----------------------------------------------------------------------
build_database("wal")
header("[4] busy_timeout 3000ms · 같은 충돌을 두 방식으로")
a, b = connect(3000), connect(3000)
step("A", a, "BEGIN IMMEDIATE")
step("B(IMMEDIATE)", b, "BEGIN IMMEDIATE")
step("A", a, "COMMIT")
b.close()

b = connect(3000)
step("B(DEFERRED)", b, "BEGIN")
step("B(DEFERRED)", b, "SELECT balance FROM account WHERE id = 2")
step("A", a, "UPDATE account SET balance = balance - 1 WHERE id = 1")
step("B(DEFERRED)", b, "UPDATE account SET balance = balance + 1 WHERE id = 2")
step("B(DEFERRED)", b, "ROLLBACK")
a.close()
b.close()

print()
print("최종 상태")
final = sqlite3.connect(DB_PATH)
print_dataset(final)
final.close()
