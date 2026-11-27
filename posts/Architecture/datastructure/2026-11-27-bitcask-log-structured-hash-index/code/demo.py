"""Bitcask 최소 구현으로 공간 증폭·병합·힌트 파일·잘린 꼬리 복구를 잰다.

1) 데이터 항목 하나의 바이트 배치
2) 같은 키 1,000개를 20번씩 덮어쓴다 — 디스크 사용량과 살아 있는 데이터의 비율
3) get 한 번이 파일을 몇 번 읽는가
4) 병합 전후 파일 수·크기
5) 다시 열 때 keydir 를 만들려고 읽는 바이트 — 데이터 파일 대 힌트 파일
6) 마지막 항목이 반쯤 쓰이다 끊긴 파일을 다시 연다
7) 삭제(묘비)가 병합 뒤에 어떻게 되는가
8) keydir 가 키 하나에 쓰는 메모리
"""
import os
import platform
import random
import shutil
import sys
import tracemalloc

from bitcask_store import DATA_HEADER, HINT_HEADER, Bitcask, KeydirEntry

WORK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "probe_store")
KEY_COUNT = 1_000
ROUNDS = 20
VALUE_SIZE = 100


def fresh_dir():
    shutil.rmtree(WORK_DIR, ignore_errors=True)
    return WORK_DIR


def make_value(rng):
    return bytes(rng.randrange(97, 123) for _ in range(VALUE_SIZE))


def live_bytes(db):
    # 살아 있는 키마다 항목 하나(헤더 + 키 + 값)가 있으면 충분하다
    return sum(DATA_HEADER.size + len(k) + e.value_sz for k, e in db.keydir.items())


def main():
    print(f"Python {platform.python_version()} / {platform.system()} {platform.release()}")
    rng = random.Random(20261127)

    print("\n[1] 데이터 항목 하나 — put(b'user:0001', b'hello')")
    db = Bitcask(fresh_dir())
    db.put(b"user:0001", b"hello")
    db.close()
    with open(os.path.join(WORK_DIR, "000001.data"), "rb") as f:
        raw = f.read()
    print(f"  헤더 {DATA_HEADER.size}바이트 + 키 9바이트 + 값 5바이트 = {len(raw)}바이트")
    print("  crc      tstamp   key_sz value_sz key / value")
    print(f"  {raw[0:4].hex()} {raw[4:8].hex()} {raw[8:10].hex()}   {raw[10:14].hex()} "
          f"{raw[14:23]!r} / {raw[23:]!r}")

    print(f"\n[2] 키 {KEY_COUNT:,}개 x {ROUNDS}번 덮어쓰기, 값 {VALUE_SIZE}바이트, 파일 한도 64KiB")
    db = Bitcask(fresh_dir())
    keys = [f"user:{i:04d}".encode() for i in range(KEY_COUNT)]
    for _ in range(ROUNDS):
        for key in keys:
            db.put(key, make_value(rng))
    data_files, hint_files = db.file_summary()
    used = db.disk_usage()
    live = live_bytes(db)
    print(f"  데이터 파일 {data_files}개, 힌트 파일 {hint_files}개")
    print(f"  디스크 사용 {used:,}바이트 / 살아 있는 데이터 {live:,}바이트 = {used / live:.2f}배")

    print("\n[3] 무작위 키 1,000번 get")
    db.read_calls = 0
    for _ in range(1000):
        db.get(rng.choice(keys))
    print(f"  파일 읽기 호출 {db.read_calls:,}번 — get 한 번에 {db.read_calls / 1000:.0f}번")

    print("\n[4] 병합")
    active_before = db.active_id
    db.merge()
    data_files, hint_files = db.file_summary()
    used_after = db.disk_usage()
    print(f"  병합 전 활성 파일 번호 {active_before}, 병합 뒤 활성 파일 번호 {db.active_id}")
    print(f"  데이터 파일 {data_files}개, 힌트 파일 {hint_files}개")
    print(f"  디스크 사용 {used:,} → {used_after:,}바이트 ({used_after / live:.2f}배)")
    for name in sorted(os.listdir(WORK_DIR)):
        size = os.path.getsize(os.path.join(WORK_DIR, name))
        role = "활성" if name == f"{db.active_id:06d}.data" else "병합 결과"
        print(f"    {name}  {size:>7,}바이트  {role}")
    in_active = sum(1 for e in db.keydir.values() if e.file_id == db.active_id)
    print(f"  키 위치: 병합 결과 {len(db.keydir) - in_active}개, 활성 파일 {in_active}개")
    sample = keys[123]
    before_close = db.get(sample)
    db.close()

    print("\n[5] 다시 열기 — keydir 를 만들려고 읽은 바이트")
    db = Bitcask(WORK_DIR)
    print(f"  힌트 파일이 있는 상태: {db.startup_bytes:,}바이트, 키 {len(db.keydir):,}개")
    print(f"  같은 값을 읽는가: {db.get(sample) == before_close}")
    db.close()
    for name in os.listdir(WORK_DIR):
        if name.endswith(".hint"):
            os.remove(os.path.join(WORK_DIR, name))
    db = Bitcask(WORK_DIR)
    print(f"  힌트 파일을 지운 상태: {db.startup_bytes:,}바이트, 키 {len(db.keydir):,}개")
    db.close()
    print(f"  힌트 항목 = 고정 {HINT_HEADER.size}바이트 + 키, 데이터 항목 = 고정 {DATA_HEADER.size}바이트 + 키 + 값")

    print("\n[6] 마지막 항목이 반쯤 쓰이다 끊긴 파일")
    db = Bitcask(fresh_dir())
    db.put(b"order:1", b"paid")
    db.put(b"order:2", b"paid")
    db.put(b"order:1", b"refunded")
    db.close()
    path = os.path.join(WORK_DIR, "000001.data")
    size = os.path.getsize(path)
    with open(path, "r+b") as f:
        f.truncate(size - 5)  # 마지막 항목의 값 끝 5바이트가 디스크에 닿기 전에 멈췄다
    print(f"  파일 {size}바이트 → {size - 5}바이트로 자름")
    db = Bitcask(WORK_DIR)
    print(f"  order:1 = {db.get(b'order:1')!r}, order:2 = {db.get(b'order:2')!r}")
    db.close()

    print("\n[7] 삭제 — 묘비 항목")
    db = Bitcask(fresh_dir(), max_file_size=200)
    db.put(b"session:a", b"x" * 40)
    db.put(b"session:b", b"y" * 40)
    db.delete(b"session:a")
    db.put(b"session:c", b"z" * 40)  # 활성 파일을 넘겨 앞 파일들이 닫히게 한다
    db.put(b"session:d", b"w" * 40)
    print(f"  병합 전 디스크 {db.disk_usage()}바이트, keydir 키 {sorted(db.keydir)}")
    db.merge()
    print(f"  병합 후 디스크 {db.disk_usage()}바이트, keydir 키 {sorted(db.keydir)}")
    db.close()
    db = Bitcask(WORK_DIR, max_file_size=200)
    print(f"  다시 열기 — session:a = {db.get(b'session:a')!r}, 키 {sorted(db.keydir)}")
    db.close()

    print("\n[8] keydir 메모리 — 키 100,000개 (키 길이 9바이트)")
    tracemalloc.start()
    keydir = {}
    for i in range(100_000):
        keydir[f"user:{i:04d}".encode()] = KeydirEntry(1, VALUE_SIZE, i * 127, i)
    current, _ = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"  {current:,}바이트, 키 하나에 {current / 100_000:.0f}바이트 (값 크기와 무관)")
    print(f"  sys.getsizeof(KeydirEntry) = {sys.getsizeof(KeydirEntry(1, 1, 1, 1))}")

    shutil.rmtree(WORK_DIR, ignore_errors=True)


if __name__ == "__main__":
    main()
