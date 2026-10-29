"""1만 건을 넣는 네 가지 방법의 소요 시간을 잰다.

갈리는 것은 "한 번에 몇 건을 보내느냐"가 아니라 "커밋을 몇 번 하느냐"다.
그 사실을 보이려고 커밋 횟수만 다른 조합과, 디스크 플러시를 끈 조합을
나란히 돌린다.
"""

from __future__ import annotations

import sqlite3
import tempfile
import time
import unicodedata
from pathlib import Path

from dbshow import print_environment, print_table

ROW_COUNT = 10_000
CHUNK_SIZE = 500

SCHEMA = """
CREATE TABLE measurement (
    id         INTEGER PRIMARY KEY,
    sensor_id  INTEGER NOT NULL,
    reading    REAL    NOT NULL,
    taken_at   TEXT    NOT NULL
);
"""


def make_rows(count: int) -> list[tuple[int, float, str]]:
    """값은 인덱스에서 바로 만든다. 난수를 쓰면 회차마다 데이터가 달라진다."""
    return [
        (i % 50, 20.0 + (i % 97) / 10.0, f"2026-10-28T{i // 3600 % 24:02d}:00:00")
        for i in range(count)
    ]


def fresh_connection(db_path: Path, *, synchronous: str, journal: str) -> sqlite3.Connection:
    """매번 빈 파일에서 시작해야 앞 측정의 파일 크기가 다음에 섞이지 않는다."""
    for suffix in ("", "-journal", "-wal", "-shm"):
        stale = db_path.with_name(db_path.name + suffix)
        if stale.exists():
            stale.unlink()
    conn = sqlite3.connect(db_path, isolation_level=None)  # 커밋 시점을 직접 잡는다
    conn.execute(f"PRAGMA journal_mode = {journal}")
    conn.execute(f"PRAGMA synchronous = {synchronous}")
    conn.executescript(SCHEMA)
    return conn


def insert_per_row_commit(conn: sqlite3.Connection, rows: list[tuple]) -> int:
    """건마다 커밋한다. 입문자가 for 문 안에 commit() 을 넣으면 이 모양이 된다."""
    sql = "INSERT INTO measurement (sensor_id, reading, taken_at) VALUES (?, ?, ?)"
    for row in rows:
        conn.execute("BEGIN")
        conn.execute(sql, row)
        conn.execute("COMMIT")
    return len(rows)


def insert_chunk_commit(conn: sqlite3.Connection, rows: list[tuple]) -> int:
    """CHUNK_SIZE 건마다 커밋한다. 커밋 횟수가 1/CHUNK_SIZE 로 줄어든다."""
    sql = "INSERT INTO measurement (sensor_id, reading, taken_at) VALUES (?, ?, ?)"
    commits = 0
    for start in range(0, len(rows), CHUNK_SIZE):
        conn.execute("BEGIN")
        conn.executemany(sql, rows[start:start + CHUNK_SIZE])
        conn.execute("COMMIT")
        commits += 1
    return commits


def insert_single_commit_loop(conn: sqlite3.Connection, rows: list[tuple]) -> int:
    """한 트랜잭션 안에서 execute 를 1만 번 부른다. 커밋은 한 번."""
    sql = "INSERT INTO measurement (sensor_id, reading, taken_at) VALUES (?, ?, ?)"
    conn.execute("BEGIN")
    for row in rows:
        conn.execute(sql, row)
    conn.execute("COMMIT")
    return 1


def insert_single_commit_many(conn: sqlite3.Connection, rows: list[tuple]) -> int:
    """한 트랜잭션 안에서 executemany 한 번. 커밋도 한 번."""
    sql = "INSERT INTO measurement (sensor_id, reading, taken_at) VALUES (?, ?, ?)"
    conn.execute("BEGIN")
    conn.executemany(sql, rows)
    conn.execute("COMMIT")
    return 1


# (설명, 넣는 함수, journal_mode, synchronous)
CASES = [
    ("건마다 커밋", insert_per_row_commit, "DELETE", "FULL"),
    (f"{CHUNK_SIZE}건마다 커밋", insert_chunk_commit, "DELETE", "FULL"),
    ("한 번만 커밋 (execute 루프)", insert_single_commit_loop, "DELETE", "FULL"),
    ("한 번만 커밋 (executemany)", insert_single_commit_many, "DELETE", "FULL"),
    # 아래 셋은 건별 커밋의 비용이 어디서 나오는지 가르려고 하나씩만 바꾼 것이다
    ("건마다 커밋", insert_per_row_commit, "DELETE", "OFF"),
    ("건마다 커밋", insert_per_row_commit, "WAL", "FULL"),
    ("건마다 커밋", insert_per_row_commit, "WAL", "NORMAL"),
]


def _width(text: str) -> int:
    """한글은 터미널에서 두 칸을 차지한다. len 으로 재면 표가 어긋난다."""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def _pad(text: str, width: int) -> str:
    return text + " " * max(0, width - _width(text))


def main() -> None:
    rows = make_rows(ROW_COUNT)
    print_environment({"행 수": f"{ROW_COUNT:,}건", "묶음": f"{CHUNK_SIZE}건"})

    with tempfile.TemporaryDirectory() as work_dir:
        db_path = Path(work_dir) / "bench.db"

        # 표 정의를 먼저 보여 준다. 아래 측정이 어떤 표에 넣는 것인지 알고 읽도록
        probe = fresh_connection(db_path, synchronous="FULL", journal="DELETE")
        print_table(probe, "measurement")
        probe.close()

        results = []
        for label, run, journal, synchronous in CASES:
            conn = fresh_connection(db_path, synchronous=synchronous, journal=journal)
            started = time.perf_counter()
            commits = run(conn, rows)
            elapsed = time.perf_counter() - started
            inserted = conn.execute("SELECT COUNT(*) FROM measurement").fetchone()[0]
            conn.close()
            results.append((label, journal, synchronous, commits, inserted, elapsed))

        baseline = results[0][5]
        label_width = max(_width(r[0]) for r in results) + 2
        print("=" * 78)
        print(f"{ROW_COUNT:,}건 삽입 소요 시간")
        print("=" * 78)
        print(
            f"  {_pad('방식', label_width)}{_pad('journal', 8)}"
            f"{_pad('sync', 8)}{'커밋':>8}{'행':>9}{'초':>10}{'배수':>10}"
        )
        print("  " + "-" * (label_width + 50))
        for label, journal, synchronous, commits, inserted, elapsed in results:
            print(
                f"  {_pad(label, label_width)}{_pad(journal, 8)}{_pad(synchronous, 8)}"
                f"{commits:>8,}{inserted:>9,}{elapsed:>10.3f}"
                f"{baseline / elapsed:>9.1f}x"
            )
        print()


if __name__ == "__main__":
    main()
