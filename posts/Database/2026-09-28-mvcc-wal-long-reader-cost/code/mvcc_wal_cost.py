"""MVCC가 읽기 잠금을 없앤 대가 — SQLite WAL에서 오래 열린 읽기 트랜잭션의 비용을 잰다.

1. rollback journal(DELETE) 모드: 읽는 쪽이 잡은 공유 잠금이 쓰는 쪽의 COMMIT을 막는다
2. WAL 모드: 같은 상황에서 COMMIT이 통과하고, 읽는 쪽은 시작 시점의 값을 계속 본다
3. 대가: 읽기 트랜잭션이 열려 있는 동안 체크포인트가 멈추고 WAL 파일이 계속 커진다

두 연결은 같은 파일 DB를 연다. timeout=0 으로 두어 잠금에 걸리면 기다리지 않고 바로
에러를 받는다. 어디서 막히는지를 보려는 것이다.
"""

import os
import sqlite3
import tempfile

from dbshow import print_dataset, print_environment

ACCOUNT_COUNT = 100
WRITE_BATCHES = 6
COMMITS_PER_BATCH = 200


def open_conn(path: str) -> sqlite3.Connection:
    # isolation_level=None: 파이썬 모듈이 BEGIN 을 몰래 넣지 않게 하고 직접 적는다
    return sqlite3.connect(path, timeout=0, isolation_level=None)


def build_database(path: str, journal_mode: str) -> sqlite3.Connection:
    conn = open_conn(path)
    conn.execute(f"PRAGMA journal_mode = {journal_mode}")
    conn.execute(
        "CREATE TABLE account (id INTEGER PRIMARY KEY, owner TEXT NOT NULL,"
        " balance INTEGER NOT NULL)"
    )
    conn.execute("BEGIN")
    conn.executemany(
        "INSERT INTO account VALUES (?, ?, ?)",
        [(i, f"고객{i}", 1000) for i in range(1, ACCOUNT_COUNT + 1)],
    )
    conn.execute("COMMIT")
    return conn


def try_step(label: str, conn: sqlite3.Connection, sql: str) -> None:
    try:
        rows = conn.execute(sql).fetchall()
        shown = f" -> {rows}" if rows else ""
        print(f"  {label:<4} {sql:<48} 성공{shown}")
    except sqlite3.OperationalError as exc:
        print(f"  {label:<4} {sql:<48} 에러: {exc}")


def section_read_lock(workdir: str) -> None:
    print("\n== 1. rollback journal(DELETE) 모드 — 읽기가 쓰기를 막는다 ==")
    path = os.path.join(workdir, "delete_mode.db")
    writer = build_database(path, "delete")
    reader = open_conn(path)
    print(f"  journal_mode = {writer.execute('PRAGMA journal_mode').fetchone()[0]}")
    try_step("읽기", reader, "BEGIN")
    try_step("읽기", reader, "SELECT balance FROM account WHERE id = 1")
    try_step("쓰기", writer, "BEGIN")
    try_step("쓰기", writer, "UPDATE account SET balance = 900 WHERE id = 1")
    try_step("쓰기", writer, "COMMIT")
    try_step("읽기", reader, "COMMIT")
    try_step("쓰기", writer, "COMMIT")
    try_step("읽기", reader, "SELECT balance FROM account WHERE id = 1")
    reader.close()
    writer.close()


def section_snapshot(workdir: str) -> None:
    print("\n== 2. WAL 모드 — 쓰기가 통과하고 읽기는 시작 시점을 본다 ==")
    path = os.path.join(workdir, "wal_snapshot.db")
    writer = build_database(path, "wal")
    reader = open_conn(path)
    print(f"  journal_mode = {writer.execute('PRAGMA journal_mode').fetchone()[0]}")
    try_step("읽기", reader, "BEGIN")
    try_step("읽기", reader, "SELECT balance FROM account WHERE id = 1")
    try_step("쓰기", writer, "BEGIN")
    try_step("쓰기", writer, "UPDATE account SET balance = 900 WHERE id = 1")
    try_step("쓰기", writer, "COMMIT")
    try_step("쓰기", writer, "SELECT balance FROM account WHERE id = 1")
    try_step("읽기", reader, "SELECT balance FROM account WHERE id = 1")
    try_step("읽기", reader, "COMMIT")
    try_step("읽기", reader, "SELECT balance FROM account WHERE id = 1")
    reader.close()
    writer.close()


def run_writes(writer: sqlite3.Connection, batch: int) -> None:
    # 한 커밋에 한 행만 바꾼다. 커밋마다 바뀐 페이지가 WAL 끝에 새 프레임으로 붙는다
    for n in range(COMMITS_PER_BATCH):
        account_id = (batch * COMMITS_PER_BATCH + n) % ACCOUNT_COUNT + 1
        writer.execute("BEGIN")
        writer.execute(
            "UPDATE account SET balance = balance - 1 WHERE id = ?", (account_id,)
        )
        writer.execute("COMMIT")


def measure_wal_growth(workdir: str, hold_reader: bool) -> None:
    title = "읽기 트랜잭션을 연 채" if hold_reader else "읽기 트랜잭션 없이"
    print(f"\n[{title}] 커밋 {COMMITS_PER_BATCH}번마다 PASSIVE 체크포인트 결과와 WAL 크기")
    path = os.path.join(workdir, f"wal_growth_{int(hold_reader)}.db")
    writer = build_database(path, "wal")
    writer.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    reader = open_conn(path)
    if hold_reader:
        reader.execute("BEGIN")
        start_sum = reader.execute("SELECT SUM(balance) FROM account").fetchone()[0]
        print(f"  읽는 쪽 시작 시점 SUM(balance) = {start_sum}")
    print("  커밋 누계 | busy | log | checkpointed | WAL 크기(바이트)")
    for batch in range(WRITE_BATCHES):
        run_writes(writer, batch)
        busy, log, done = writer.execute("PRAGMA wal_checkpoint(PASSIVE)").fetchone()
        size = os.path.getsize(path + "-wal")
        total = (batch + 1) * COMMITS_PER_BATCH
        print(f"  {total:>9,} | {busy:>4} | {log:>3} | {done:>12} | {size:>14,}")
    if hold_reader:
        same_sum = reader.execute("SELECT SUM(balance) FROM account").fetchone()[0]
        print(f"  읽는 쪽이 지금 보는 SUM(balance) = {same_sum}")
        reader.execute("COMMIT")
    latest = writer.execute("SELECT SUM(balance) FROM account").fetchone()[0]
    print(f"  최신 SUM(balance) = {latest}")
    busy, log, done = writer.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
    size = os.path.getsize(path + "-wal")
    print(f"  읽기 종료 후 TRUNCATE 체크포인트: busy={busy} log={log}"
          f" checkpointed={done} WAL 크기={size:,}")
    reader.close()
    writer.close()


def section_cost(workdir: str) -> None:
    print("\n== 3. 대가 — 열린 읽기 트랜잭션이 체크포인트를 멈춘다 ==")
    probe = build_database(os.path.join(workdir, "probe.db"), "wal")
    page_size = probe.execute("PRAGMA page_size").fetchone()[0]
    auto = probe.execute("PRAGMA wal_autocheckpoint").fetchone()[0]
    print(f"  page_size = {page_size}, wal_autocheckpoint = {auto}")
    probe.close()
    measure_wal_growth(workdir, hold_reader=False)
    measure_wal_growth(workdir, hold_reader=True)


def main() -> None:
    print_environment()
    with tempfile.TemporaryDirectory() as workdir:
        # 표 정의와 데이터는 모든 절이 같으므로 한 번만 찍는다
        shown = build_database(os.path.join(workdir, "shown.db"), "delete")
        print_dataset(shown)
        shown.close()
        section_read_lock(workdir)
        section_snapshot(workdir)
        section_cost(workdir)


if __name__ == "__main__":
    main()
