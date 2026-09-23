"""SQLite에서 세 가지 읽기 이상 현상을 재현하고, 무엇이 그것을 막는지 확인한다.

실행: python isolation_anomalies.py   (표준 라이브러리만 사용)

두 개의 연결을 한 스레드에서 번갈아 조작한다. 스레드를 쓰면 타이밍에 따라 결과가
흔들려 재현이 안 되므로, 순서를 코드로 고정했다.
"""

import os
import pathlib
import sqlite3

from dbshow import print_dataset, print_environment
import tempfile

WORK_DIR = pathlib.Path(tempfile.mkdtemp(prefix="isolation-"))
DB_PATH = WORK_DIR / "shop.db"
BUSY_TIMEOUT_SEC = 0.5


def reset(journal_mode: str) -> None:
    """매 실험을 같은 상태에서 시작한다. WAL 파일까지 지워야 모드가 확실히 바뀐다."""
    for leftover in WORK_DIR.glob("shop.db*"):
        leftover.unlink()
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.execute(f"PRAGMA journal_mode={journal_mode}")
    conn.execute("CREATE TABLE account (id INTEGER PRIMARY KEY, balance INTEGER NOT NULL)")
    conn.executemany(
        "INSERT INTO account VALUES (?, ?)", [(i, 1000) for i in range(1, 6)]
    )
    conn.close()


def connect() -> sqlite3.Connection:
    # isolation_level=None으로 두면 드라이버가 BEGIN을 대신 넣지 않는다.
    # 트랜잭션 경계를 이 글의 주제로 삼으려면 경계를 직접 그어야 한다.
    return sqlite3.connect(DB_PATH, isolation_level=None, timeout=BUSY_TIMEOUT_SEC)


def balance(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT balance FROM account WHERE id = 1").fetchone()[0]


def rich_count(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM account WHERE balance >= 1000").fetchone()[0]


def attempt(conn: sqlite3.Connection, sql: str, args: tuple = ()) -> str:
    """잠금 충돌을 예외가 아니라 값으로 돌려준다. 실험 표를 그리려면 계속 진행해야 한다."""
    try:
        conn.execute(sql, args)
        return "성공"
    except sqlite3.OperationalError as exc:
        return f"거부({exc})"


def rollback_quietly(conn: sqlite3.Connection) -> None:
    try:
        conn.execute("ROLLBACK")
    except sqlite3.OperationalError:
        pass  # 열린 트랜잭션이 없으면 여기로 온다


def demo_dirty_read() -> None:
    print("### 1. 더티 리드 — 기본값에서는 안 보이고, 공유 캐시에서만 보인다")
    reset("delete")
    writer, reader = connect(), connect()
    writer.execute("BEGIN")
    writer.execute("UPDATE account SET balance = 9999 WHERE id = 1")
    print(f"  기본(캐시 비공유)  커밋 전 읽기 = {balance(reader)}")
    writer.execute("ROLLBACK")
    writer.close()
    reader.close()

    reset("delete")
    uri = f"file:{DB_PATH.as_posix()}?cache=shared"
    writer = sqlite3.connect(uri, uri=True, isolation_level=None)
    reader = sqlite3.connect(uri, uri=True, isolation_level=None)
    reader.execute("PRAGMA read_uncommitted = 1")
    writer.execute("BEGIN")
    writer.execute("UPDATE account SET balance = 9999 WHERE id = 1")
    dirty = balance(reader)
    writer.execute("ROLLBACK")
    print(f"  공유 캐시 + read_uncommitted=1  커밋 전 읽기 = {dirty}")
    print(f"  그 트랜잭션이 롤백된 뒤        다시 읽기 = {balance(reader)}")
    print("  → 읽은 9999는 어느 시점에도 커밋된 적 없는 값이다\n")
    writer.close()
    reader.close()


def demo_repeatable(journal_mode: str) -> None:
    print(f"### 2. 반복 읽기와 팬텀 — journal_mode = {journal_mode}")
    for label, use_begin in (("트랜잭션 안", True), ("autocommit ", False)):
        reset(journal_mode)
        reader, writer = connect(), connect()
        if use_begin:
            reader.execute("BEGIN")
        first = balance(reader)
        wrote = attempt_write(writer, "UPDATE account SET balance = 2000 WHERE id = 1")
        second = balance(reader)
        if use_begin:
            reader.execute("COMMIT")
        print(
            f"  [{label}] 쓰기 {wrote:<32} 1회차 {first} → 2회차 {second}"
            f" → 끝난 뒤 {balance(reader)}"
        )
        reader.close()
        writer.close()

    for label, use_begin in (("트랜잭션 안", True), ("autocommit ", False)):
        reset(journal_mode)
        reader, writer = connect(), connect()
        if use_begin:
            reader.execute("BEGIN")
        first = rich_count(reader)
        wrote = attempt_write(writer, "INSERT INTO account VALUES (99, 5000)")
        second = rich_count(reader)
        if use_begin:
            reader.execute("COMMIT")
        print(
            f"  [{label}] 삽입 {wrote:<32} COUNT {first} → {second}"
            f" → 끝난 뒤 {rich_count(reader)}"
        )
        reader.close()
        writer.close()
    print()


def attempt_write(conn: sqlite3.Connection, sql: str) -> str:
    result = attempt(conn, "BEGIN IMMEDIATE")
    if result != "성공":
        return result
    result = attempt(conn, sql)
    if result == "성공":
        result = attempt(conn, "COMMIT")
    rollback_quietly(conn)
    return result


def demo_lost_update() -> None:
    print("### 3. 갱신 분실 — 막히기는 하는데, 어디서 막히느냐가 다르다")
    for begin in ("BEGIN", "BEGIN IMMEDIATE"):
        for journal_mode in ("delete", "wal"):
            reset(journal_mode)
            a, b = connect(), connect()
            a_begin, b_begin = attempt(a, begin), attempt(b, begin)
            a_read = balance(a) if a_begin == "성공" else None
            b_read = balance(b) if b_begin == "성공" else None
            a_write = attempt(a, "UPDATE account SET balance=? WHERE id=1", (a_read + 100,)) \
                if a_read else "-"
            b_write = attempt(b, "UPDATE account SET balance=? WHERE id=1", (b_read + 100,)) \
                if b_read else "-"
            a_commit = attempt(a, "COMMIT")
            attempt(b, "COMMIT")
            rollback_quietly(a)
            rollback_quietly(b)
            final = balance(a)
            print(
                f"  {begin:<15} / {journal_mode:<6} "
                f"B의 BEGIN {short(b_begin):<10} B의 UPDATE {short(b_write):<10} "
                f"A의 COMMIT {short(a_commit):<10} 최종 잔액 {final}"
            )
            a.close()
            b.close()
    print()


def short(result: str) -> str:
    return "성공" if result == "성공" else ("-" if result == "-" else "거부")


def main() -> None:
    print_environment()
    # 세 실험 모두 이 표를 같은 상태에서 다시 만들어 쓴다
    reset("delete")
    probe = sqlite3.connect(DB_PATH)
    print_dataset(probe)
    probe.close()

    demo_dirty_read()
    demo_repeatable("delete")
    demo_repeatable("wal")
    demo_lost_update()
    for leftover in WORK_DIR.glob("shop.db*"):
        leftover.unlink()
    os.rmdir(WORK_DIR)


if __name__ == "__main__":
    main()
