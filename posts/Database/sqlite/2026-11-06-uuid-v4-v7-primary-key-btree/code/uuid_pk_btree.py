"""UUID v4·v7·정수 키를 기본키로 넣고 B-Tree 리프 페이지가 얼마나 차는지 잰다.

dbstat 가상 테이블이 없는 빌드라서 SQLite 파일 포맷 명세(§1.6 B-tree Pages)대로
페이지 헤더를 직접 읽어 리프 페이지 수와 빈 바이트를 센다.
"""
import os
import random
import sqlite3
import struct
import tempfile
import time
import uuid

ROW_COUNT = 100_000
BATCH_SIZE = 1_000
ROWS_PER_MS = 8          # v7 시각 필드: 1ms 동안 들어오는 행 수를 흉내 낸다
START_MS = 1_762_387_200_000  # 2025-11-06 00:00:00 UTC
SEED = 42

LEAF_TYPES = {0x0A, 0x0D}
INTERIOR_TYPES = {0x02, 0x05}


def make_uuid4(rng):
    return uuid.UUID(int=rng.getrandbits(128), version=4)


def make_uuid7(rng, n):
    # RFC 9562 §5.7: unix_ts_ms(48) | ver(4) | rand_a(12) | var(2) | rand_b(62)
    unix_ts_ms = START_MS + n // ROWS_PER_MS
    value = (unix_ts_ms << 80) | (0x7 << 76) | (rng.getrandbits(12) << 64)
    value |= (0b10 << 62) | rng.getrandbits(62)
    return uuid.UUID(int=value)


def read_btree(data, page_size, root):
    """루트부터 내려가며 (리프 수, 내부 노드 수, 리프 셀 수, 리프 빈 바이트)를 센다."""
    leaf = interior = cells = unused = 0
    stack = [root]
    while stack:
        pgno = stack.pop()
        base = (pgno - 1) * page_size
        hdr = base + (100 if pgno == 1 else 0)
        kind = data[hdr]
        first_free, ncell, content = struct.unpack(">HHH", data[hdr + 1:hdr + 7])
        fragmented = data[hdr + 7]
        content = content or 65536
        if kind in INTERIOR_TYPES:
            interior += 1
            stack.append(struct.unpack(">I", data[hdr + 8:hdr + 12])[0])
            ptrs = hdr + 12
            for i in range(ncell):
                off = struct.unpack(">H", data[ptrs + 2 * i:ptrs + 2 * i + 2])[0]
                stack.append(struct.unpack(">I", data[base + off:base + off + 4])[0])
            continue
        assert kind in LEAF_TYPES, kind
        leaf += 1
        cells += ncell
        gap = (base + content) - (hdr + 8 + 2 * ncell)
        free = 0
        while first_free:
            nxt, size = struct.unpack(">HH", data[base + first_free:base + first_free + 4])
            free += size
            first_free = nxt
        unused += gap + free + fragmented
    return leaf, interior, cells, unused


def run_case(label, ddl, keys, workdir):
    path = os.path.join(workdir, label + ".db")
    conn = sqlite3.connect(path)
    try:
        # WAL 은 커밋마다 바뀐 페이지를 프레임으로 덧붙인다. 체크포인트를 끄면
        # WAL 크기가 곧 "삽입하는 동안 디스크에 쓴 페이지 수"가 된다.
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA wal_autocheckpoint=0")
        conn.execute(ddl)
        sql = "INSERT INTO t(id, payload) VALUES (?, ?)"
        t0 = time.perf_counter()
        for start in range(0, ROW_COUNT, BATCH_SIZE):
            batch = ((keys[i], "payload-%06d" % i) for i in range(start, start + BATCH_SIZE))
            conn.executemany(sql, batch)
            conn.commit()
        elapsed = time.perf_counter() - t0
        page_size = conn.execute("PRAGMA page_size").fetchone()[0]
        page_count = conn.execute("PRAGMA page_count").fetchone()[0]
        roots = conn.execute(
            "SELECT type, name, rootpage FROM sqlite_master ORDER BY rootpage"
        ).fetchall()
        wal_bytes = os.path.getsize(path + "-wal")
    finally:
        conn.close()  # 마지막 연결이 닫히며 체크포인트 → 본 파일에 전부 반영된다
    with open(path, "rb") as f:
        data = f.read()
    frames = (wal_bytes - 32) // (page_size + 24)
    print("\n[%s]  삽입 %.2f초 · 파일 %d페이지 (%.1f MB) · WAL 프레임 %d (커밋당 %.1f)" % (
        label, elapsed, page_count, page_count * page_size / 1024 / 1024,
        frames, frames / (ROW_COUNT / BATCH_SIZE)))
    print("  %-26s %8s %8s %10s %8s" % ("B-Tree", "리프", "내부", "셀/리프", "채움률"))
    for kind, name, root in roots:
        leaf, interior, cells, unused = read_btree(data, page_size, root)
        fill = 1 - unused / (leaf * page_size)
        print("  %-26s %8d %8d %10.1f %7.1f%%" % (
            kind + " " + name, leaf, interior, cells / leaf, fill * 100))


def main():
    print("SQLite %s / Python %s" % (sqlite3.sqlite_version, ".".join(map(str, __import__("sys").version_info[:3]))))
    print("행 %d개, %d행마다 커밋, page_size 기본값" % (ROW_COUNT, BATCH_SIZE))
    rng = random.Random(SEED)
    v4 = [make_uuid4(rng).bytes for _ in range(ROW_COUNT)]
    v7 = [make_uuid7(rng, n).bytes for n in range(ROW_COUNT)]
    print("\n앞의 세 키")
    for i in range(3):
        print("  v4 %s   v7 %s" % (uuid.UUID(bytes=v4[i]), uuid.UUID(bytes=v7[i])))
    print("  v7 버전 필드:", uuid.UUID(bytes=v7[0]).version, " 변형:", uuid.UUID(bytes=v7[0]).variant)

    rowid_ddl = "CREATE TABLE t (id {0} PRIMARY KEY, payload TEXT NOT NULL)"
    with tempfile.TemporaryDirectory() as workdir:
        run_case("int", rowid_ddl.format("INTEGER"), list(range(1, ROW_COUNT + 1)), workdir)
        run_case("v4-rowid", rowid_ddl.format("BLOB"), v4, workdir)
        run_case("v7-rowid", rowid_ddl.format("BLOB"), v7, workdir)
        run_case("v4-without-rowid", rowid_ddl.format("BLOB") + " WITHOUT ROWID", v4, workdir)
        run_case("v7-without-rowid", rowid_ddl.format("BLOB") + " WITHOUT ROWID", v7, workdir)


if __name__ == "__main__":
    main()
