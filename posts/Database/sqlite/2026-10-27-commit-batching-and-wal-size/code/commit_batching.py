"""같은 1만 건 INSERT 를 커밋 횟수만 바꿔 넣고 시간과 WAL 크기를 잰다.

표준 라이브러리만 쓴다. 측정마다 임시 폴더에 새 DB 파일을 만들고 끝나면 지운다.
시간은 환경에 따라 흔들리므로 절대값이 아니라 조합 사이의 배수를 본다.
"""

import os
import shutil
import sqlite3
import tempfile
import time

from dbshow import print_environment

ROWS = 10_000
WAL_HEADER = 32        # WAL 파일 머리말 (SQLite WAL Format §1)
FRAME_HEADER = 24      # 프레임마다 붙는 머리말


def insert_rows(path, *, journal_mode, synchronous, batch, autocheckpoint=None):
    """ROWS 건을 batch 건마다 커밋하며 넣고, 걸린 시간과 WAL 크기를 돌려준다."""
    conn = sqlite3.connect(path, isolation_level=None)  # 커밋 시점을 직접 잡는다
    mode = conn.execute(f"PRAGMA journal_mode={journal_mode}").fetchone()[0]
    conn.execute(f"PRAGMA synchronous={synchronous}")
    if autocheckpoint is not None:
        conn.execute(f"PRAGMA wal_autocheckpoint={autocheckpoint}")
    page_size = conn.execute("PRAGMA page_size").fetchone()[0]
    conn.execute("CREATE TABLE measurement(id INTEGER PRIMARY KEY, label TEXT)")

    start = time.perf_counter()
    conn.execute("BEGIN")
    for i in range(ROWS):
        conn.execute("INSERT INTO measurement(label) VALUES (?)", (f"row-{i}",))
        if (i + 1) % batch == 0:
            conn.execute("COMMIT")
            conn.execute("BEGIN")
    conn.execute("COMMIT")
    elapsed = time.perf_counter() - start

    wal_path = path + "-wal"
    wal_bytes = os.path.getsize(wal_path) if os.path.exists(wal_path) else 0
    conn.close()                                        # 닫으면 체크포인트가 돈다
    frames = (wal_bytes - WAL_HEADER) // (page_size + FRAME_HEADER) if wal_bytes else 0
    return {"mode": mode, "elapsed": elapsed, "wal_bytes": wal_bytes,
            "frames": frames, "page_size": page_size}


def measure(**kwargs):
    workdir = tempfile.mkdtemp(prefix="commit-batching-")
    try:
        return insert_rows(os.path.join(workdir, "bench.db"), **kwargs)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def section(title):
    print("=" * 72)
    print(title)
    print("=" * 72)


def row(label, result, baseline=None):
    ratio = f"{result['elapsed'] / baseline:6.1f}x" if baseline else "      -"
    print(f"  {label:26s} {result['elapsed']:8.3f}s {ratio}  "
          f"WAL {result['wal_bytes']:>9,}B  프레임 {result['frames']:>5,}")


def main():
    print_environment({"행 수": f"{ROWS:,}건"})

    section("1. journal_mode=WAL · synchronous=FULL — 커밋 횟수만 바꾼다")
    print(f"  {'커밋 횟수':26s} {'소요':>9s} {'1회 대비':>8s}  "
          f"{'최종 WAL 파일':>17s}  {'프레임':>9s}")
    base = None
    for batch in (ROWS, 1000, 100, 10, 1):
        result = measure(journal_mode="WAL", synchronous="FULL", batch=batch)
        base = base or result["elapsed"]
        row(f"{ROWS // batch:,}회 ({batch:,}건마다)", result, base)
    print()

    section("2. synchronous 를 낮추면 격차가 어떻게 달라지나 (WAL)")
    for sync in ("FULL", "NORMAL", "OFF"):
        print(f"  [synchronous={sync}]")
        base = None
        for batch in (ROWS, 100, 1):
            result = measure(journal_mode="WAL", synchronous=sync, batch=batch)
            base = base or result["elapsed"]
            row(f"  {ROWS // batch:,}회", result, base)
    print()

    section("3. 같은 조건을 DELETE 저널로 (synchronous=FULL)")
    base = None
    for batch in (ROWS, 100, 1):
        result = measure(journal_mode="DELETE", synchronous="FULL", batch=batch)
        base = base or result["elapsed"]
        row(f"{ROWS // batch:,}회 · {result['mode']}", result, base)
    print()

    section("4. wal_autocheckpoint 를 끄면 WAL 이 어디까지 커지나")
    print("  기본값 1000 — 켠 채로")
    for batch in (ROWS, 100, 1):
        row(f"{ROWS // batch:,}회",
            measure(journal_mode="WAL", synchronous="NORMAL", batch=batch))
    print("  wal_autocheckpoint=0 — 꺼 두고")
    for batch in (ROWS, 100, 1):
        row(f"{ROWS // batch:,}회",
            measure(journal_mode="WAL", synchronous="NORMAL", batch=batch,
                    autocheckpoint=0))
    print()

    section("5. 한 번에 넣을 때 executemany 는 무엇을 줄이나")
    workdir = tempfile.mkdtemp(prefix="commit-batching-")
    try:
        path = os.path.join(workdir, "many.db")
        conn = sqlite3.connect(path, isolation_level=None)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=FULL")
        conn.execute("CREATE TABLE measurement(id INTEGER PRIMARY KEY, label TEXT)")
        rows = [(f"row-{i}",) for i in range(ROWS)]
        start = time.perf_counter()
        conn.execute("BEGIN")
        conn.executemany("INSERT INTO measurement(label) VALUES (?)", rows)
        conn.execute("COMMIT")
        print(f"  executemany · 커밋 1회       {time.perf_counter() - start:8.3f}s")
        conn.close()
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    result = measure(journal_mode="WAL", synchronous="FULL", batch=ROWS)
    print(f"  execute 반복 · 커밋 1회      {result['elapsed']:8.3f}s")


if __name__ == "__main__":
    main()
