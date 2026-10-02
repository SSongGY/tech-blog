"""SQLite WAL 파일을 바이트 단위로 열어, 커밋이 데이터 파일보다 WAL에 먼저 쌓이는 것을 확인한다.

WAL 헤더와 프레임 헤더를 파일 포맷 명세대로 직접 해석하고, 누적 체크섬을 직접 계산해
SQLite가 적은 값과 맞춰 본다. 마지막에 연결을 닫지 않은 채 파일을 복사해 '프로세스가 죽은
순간'을 흉내 내고, 복사본을 열었을 때 어떤 커밋이 살아남는지 본다.
"""

import shutil
import sqlite3
import struct
import tempfile
from pathlib import Path

PAGE_SIZE = 4096
WAL_HEADER_SIZE = 32
FRAME_HEADER_SIZE = 24
MAGIC_LITTLE_ENDIAN = 0x377F0682


def wal_checksum(data: bytes, s0: int, s1: int, endian: str) -> tuple[int, int]:
    # 명세의 checksum 알고리즘: 32비트 정수 두 개씩 묶어 누적한다
    words = struct.unpack(f"{endian}{len(data) // 4}I", data)
    for i in range(0, len(words), 2):
        s0 = (s0 + words[i] + s1) & 0xFFFFFFFF
        s1 = (s1 + words[i + 1] + s0) & 0xFFFFFFFF
    return s0, s1


def read_wal(wal_path: Path) -> tuple[dict, list[dict]]:
    raw = wal_path.read_bytes()
    if len(raw) < WAL_HEADER_SIZE:
        return {}, []
    magic, version, page_size, ckpt_seq, salt1, salt2, ck1, ck2 = struct.unpack(
        ">8I", raw[:WAL_HEADER_SIZE]
    )
    endian = "<" if magic == MAGIC_LITTLE_ENDIAN else ">"
    s0, s1 = wal_checksum(raw[:24], 0, 0, endian)
    header = {
        "magic": hex(magic), "version": version, "page_size": page_size,
        "ckpt_seq": ckpt_seq, "salt1": salt1, "salt2": salt2,
        "header_checksum_ok": (s0, s1) == (ck1, ck2),
    }
    frames = []
    offset = WAL_HEADER_SIZE
    chain_ok = True
    while offset + FRAME_HEADER_SIZE + page_size <= len(raw):
        fh = raw[offset:offset + FRAME_HEADER_SIZE]
        page = raw[offset + FRAME_HEADER_SIZE:offset + FRAME_HEADER_SIZE + page_size]
        pgno, commit_size, f_salt1, f_salt2, f_ck1, f_ck2 = struct.unpack(">6I", fh)
        salt_ok = (f_salt1, f_salt2) == (salt1, salt2)
        s0, s1 = wal_checksum(fh[:8] + page, s0, s1, endian)
        # 체크섬은 앞 프레임에서 이어지므로, 한 번 끊기면 뒤는 전부 무효다
        chain_ok = chain_ok and salt_ok and (s0, s1) == (f_ck1, f_ck2)
        frames.append({
            "no": len(frames), "pgno": pgno, "commit_size": commit_size,
            "salt_ok": salt_ok, "valid": chain_ok, "page": page,
        })
        offset += FRAME_HEADER_SIZE + page_size
    return header, frames


def show_files(label: str, db_path: Path, markers: list[bytes]) -> None:
    wal_path = Path(f"{db_path}-wal")
    db_bytes = db_path.read_bytes()
    wal_bytes = wal_path.read_bytes() if wal_path.exists() else b""
    print(f"\n[{label}]")
    print(f"  db  파일 {len(db_bytes):>6} 바이트   wal 파일 {len(wal_bytes):>6} 바이트")
    for marker in markers:
        print(f"  {marker.decode():<7} db에 {'있음' if marker in db_bytes else '없음'}"
              f"   wal에 {'있음' if marker in wal_bytes else '없음'}")


def show_wal(label: str, db_path: Path, markers: list[bytes]) -> None:
    header, frames = read_wal(Path(f"{db_path}-wal"))
    print(f"\n[{label}]")
    if not header:
        print("  WAL 비어 있음")
        return
    print(f"  헤더: magic={header['magic']} version={header['version']} "
          f"page_size={header['page_size']} ckpt_seq={header['ckpt_seq']} "
          f"salt1={header['salt1']} 헤더체크섬={'일치' if header['header_checksum_ok'] else '불일치'}")
    print("  frame | page | commit_size | salt | 유효 | 들어 있는 표식")
    for f in frames:
        found = ",".join(m.decode() for m in markers if m in f["page"]) or "-"
        print(f"  {f['no']:>5} | {f['pgno']:>4} | {f['commit_size']:>11} | "
              f"{'같음' if f['salt_ok'] else '다름'} | {'예' if f['valid'] else '아니오':<4} | {found}")


def open_copy(label: str, src: Path, dst_dir: Path, with_wal: bool, corrupt: int = -1) -> None:
    dst_dir.mkdir()
    dst = dst_dir / "app.db"
    shutil.copyfile(src, dst)
    if with_wal:
        wal_copy = Path(f"{dst}-wal")
        shutil.copyfile(Path(f"{src}-wal"), wal_copy)
        if corrupt >= 0:
            data = bytearray(wal_copy.read_bytes())
            data[corrupt] ^= 0xFF
            wal_copy.write_bytes(bytes(data))
    conn = sqlite3.connect(dst)
    rows = conn.execute("SELECT id, body FROM note ORDER BY id").fetchall()
    conn.close()
    print(f"\n[{label}]")
    print(f"  {rows}")


def main() -> None:
    print(f"SQLite {sqlite3.sqlite_version}")
    markers = [b"MARK-A", b"MARK-B", b"MARK-C"]
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        db_path = work / "app.db"
        conn = sqlite3.connect(db_path, isolation_level=None)
        conn.execute(f"PRAGMA page_size = {PAGE_SIZE}")
        print("journal_mode =", conn.execute("PRAGMA journal_mode = WAL").fetchone()[0])
        # 자동 체크포인트를 끄고 손으로 돌려야 옮겨지는 시점을 볼 수 있다
        conn.execute("PRAGMA wal_autocheckpoint = 0")
        print("synchronous  =", conn.execute("PRAGMA synchronous").fetchone()[0])

        conn.execute("CREATE TABLE note (id INTEGER PRIMARY KEY, body TEXT)")
        conn.execute("INSERT INTO note VALUES (1, 'MARK-A')")
        show_files("1 CREATE·INSERT 커밋 직후", db_path, markers)
        show_wal("1 WAL 프레임", db_path, markers)

        conn.execute("UPDATE note SET body = 'MARK-B' WHERE id = 1")
        show_wal("2 같은 행을 UPDATE — 페이지 2가 프레임으로 한 번 더 붙는다", db_path, markers)

        busy, log, moved = conn.execute("PRAGMA wal_checkpoint(PASSIVE)").fetchone()
        print(f"\n[3 체크포인트] busy={busy} log={log} checkpointed={moved}")
        show_files("3 체크포인트 직후", db_path, markers)

        conn.execute("INSERT INTO note VALUES (2, 'MARK-C')")
        show_files("4 다음 커밋 — WAL이 처음부터 다시 쓰인다", db_path, markers)
        show_wal("4 WAL 프레임", db_path, markers)

        _, frames = read_wal(Path(f"{db_path}-wal"))
        last_commit = max(f["no"] for f in frames if f["valid"] and f["commit_size"])
        corrupt_at = WAL_HEADER_SIZE + last_commit * (FRAME_HEADER_SIZE + PAGE_SIZE) + 100
        print(f"\n마지막 유효 커밋 프레임 = {last_commit}, 뒤집을 바이트 오프셋 = {corrupt_at}")

        # 연결을 열어 둔 채 복사한다 = 체크포인트 없이 프로세스가 사라진 상태
        open_copy("5-A db 파일만 복사해 열면", db_path, work / "a", with_wal=False)
        open_copy("5-B db + wal 을 복사해 열면", db_path, work / "b", with_wal=True)
        open_copy("5-C 마지막 커밋 프레임의 1바이트를 뒤집으면", db_path, work / "c",
                  with_wal=True, corrupt=corrupt_at)

        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        show_files("6 TRUNCATE 체크포인트 후", db_path, markers)
        conn.close()


if __name__ == "__main__":
    main()
