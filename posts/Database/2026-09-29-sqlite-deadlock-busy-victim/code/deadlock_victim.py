"""SQLite 에서 교착이 만들어지는 순서와, 어느 쪽이 SQLITE_BUSY 를 받는지 잰다.

두 연결 모두 busy_timeout 을 1초로 둔다. 그러면 걸린 시간만 보고도
"잠금을 기다리다 포기했다(약 1초)"와 "기다리지 않고 바로 돌려받았다(약 0초)"가
갈린다. 교착을 알아챘는지는 이 차이로만 드러난다.
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
import threading
import time

from dbshow import print_dataset, print_environment

BUSY_TIMEOUT_S = 1.0
LATE_COMMIT_S = 0.3

SCHEMA = """
CREATE TABLE account (
  account_id INTEGER PRIMARY KEY,
  owner      TEXT    NOT NULL,
  balance    INTEGER NOT NULL
);
INSERT INTO account VALUES (1, 'A', 100), (2, 'B', 100);
"""


# 윈도우는 열린 파일을 지우지 못하므로 임시 폴더를 치우기 전에 전부 닫는다
opened: list[sqlite3.Connection] = []


def open_conn(path: str) -> sqlite3.Connection:
    # isolation_level=None: 파이썬 모듈이 BEGIN 을 몰래 끼워 넣지 않게 한다
    conn = sqlite3.connect(path, timeout=BUSY_TIMEOUT_S, isolation_level=None,
                           check_same_thread=False)
    opened.append(conn)
    return conn


def step(label: str, conn: sqlite3.Connection, sql: str) -> None:
    started = time.perf_counter()
    try:
        conn.execute(sql).fetchall()
        outcome = "성공"
    except sqlite3.OperationalError as exc:
        outcome = f"{exc.sqlite_errorname}"
    elapsed = time.perf_counter() - started
    state = "트랜잭션 열림" if conn.in_transaction else "트랜잭션 없음"
    print(f"  {label:<3}{sql:<64}{outcome:<22}{elapsed:6.3f}s  {state}")


def fresh_db(root: str, name: str, journal_mode: str) -> tuple:
    path = os.path.join(root, name)
    setup = sqlite3.connect(path, isolation_level=None)
    setup.execute(f"PRAGMA journal_mode={journal_mode}")
    setup.executescript(SCHEMA)
    setup.close()
    return open_conn(path), open_conn(path)


def case_plain_contention(root: str) -> None:
    print("\n[1] 교착 없는 경합 — B 는 아직 아무것도 읽지 않았다 (rollback 저널)")
    a, b = fresh_db(root, "c1.db", "DELETE")
    step("A", a, "BEGIN IMMEDIATE")
    step("A", a, "UPDATE account SET balance = balance - 10 WHERE account_id = 1")
    step("B", b, "BEGIN IMMEDIATE")
    step("A", a, "COMMIT")


def case_deadlock(root: str, first: str) -> None:
    second = "B" if first == "A" else "A"
    print(f"\n[2-{first}] 교착 — 둘 다 읽은 뒤 {first} 가 먼저 쓴다 (rollback 저널)")
    a, b = fresh_db(root, f"c2{first}.db", "DELETE")
    conns = {"A": a, "B": b}
    step("A", a, "BEGIN")
    step("A", a, "SELECT balance FROM account WHERE account_id = 1")
    step("B", b, "BEGIN")
    step("B", b, "SELECT balance FROM account WHERE account_id = 2")
    own_row = {"A": 1, "B": 2}
    step(first, conns[first],
         f"UPDATE account SET balance = 90 WHERE account_id = {own_row[first]}")
    step(second, conns[second],
         f"UPDATE account SET balance = 90 WHERE account_id = {own_row[second]}")
    step(first, conns[first], "COMMIT")
    step(second, conns[second], "ROLLBACK")
    step(first, conns[first], "COMMIT")


def case_immediate_fix(root: str) -> None:
    print(f"\n[3] BEGIN IMMEDIATE — A 가 {LATE_COMMIT_S}초 뒤 커밋한다 (rollback 저널)")
    a, b = fresh_db(root, "c3.db", "DELETE")
    step("A", a, "BEGIN IMMEDIATE")
    step("A", a, "UPDATE account SET balance = 90 WHERE account_id = 1")
    timer = threading.Timer(LATE_COMMIT_S, lambda: a.execute("COMMIT"))
    timer.start()
    step("B", b, "BEGIN IMMEDIATE")
    timer.join()
    step("B", b, "UPDATE account SET balance = 90 WHERE account_id = 2")
    step("B", b, "COMMIT")


def case_wal(root: str) -> None:
    print("\n[4] 같은 순서를 WAL 에서")
    a, b = fresh_db(root, "c4.db", "WAL")
    step("A", a, "BEGIN")
    step("A", a, "SELECT balance FROM account WHERE account_id = 1")
    step("B", b, "BEGIN")
    step("B", b, "SELECT balance FROM account WHERE account_id = 2")
    step("A", a, "UPDATE account SET balance = 90 WHERE account_id = 1")
    step("B", b, "UPDATE account SET balance = 90 WHERE account_id = 2")
    step("A", a, "COMMIT")
    step("B", b, "UPDATE account SET balance = 90 WHERE account_id = 2")
    step("B", b, "ROLLBACK")


def main() -> None:
    print_environment({"timeout": f"busy_timeout {BUSY_TIMEOUT_S:.0f}초 (두 연결 모두)"})
    with tempfile.TemporaryDirectory() as root:
        a, _ = fresh_db(root, "show.db", "DELETE")
        print_dataset(a)
        a.close()
        print(f"  {'연결':<2} {'SQL':<64}{'결과':<20}{'시간':>5}   그 뒤 상태")
        case_plain_contention(root)
        case_deadlock(root, "A")
        case_deadlock(root, "B")
        case_immediate_fix(root)
        case_wal(root)
        for conn in opened:
            conn.close()


if __name__ == "__main__":
    main()
