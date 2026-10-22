"""gzip(zlib)·bzip2·lzma 를 같은 입력 세 가지로 대조한다.

표준 라이브러리만 쓴다. 입력은 시드를 고정해 만들므로 몇 번 돌려도 같은
바이트열이 나온다. 시간은 환경마다 다르지만 크기는 같아야 한다.
"""

from __future__ import annotations

import bz2
import gzip
import json
import lzma
import platform
import random
import sys
import time
import zlib

SEED = 7
LOG_LINES = 30_000
JSON_RECORDS = 12_000
REPEAT = 5


def make_log(rng: random.Random) -> bytes:
    levels = ["INFO"] * 8 + ["WARN", "ERROR"]
    paths = ["/api/orders", "/api/users", "/api/items", "/health", "/api/cart"]
    lines = []
    for i in range(LOG_LINES):
        second = i // 10
        lines.append(
            f"2026-10-23T08:{second // 60 % 60:02d}:{second % 60:02d}.{rng.randint(0, 999):03d}Z "
            f"{rng.choice(levels):<5} [worker-{rng.randint(1, 8)}] "
            f"GET {rng.choice(paths)}/{rng.randint(1, 99999)} "
            f"{rng.choice([200, 200, 200, 201, 404, 500])} {rng.randint(1, 900)}ms "
            f"user=u{rng.randint(1, 5000):05d}"
        )
    return ("\n".join(lines) + "\n").encode()


def make_json(rng: random.Random) -> bytes:
    records = []
    for i in range(JSON_RECORDS):
        records.append(
            {
                "order_id": 100000 + i,
                "customer": {"id": rng.randint(1, 5000), "tier": rng.choice(["gold", "silver", "basic"])},
                "items": [
                    {"sku": f"SKU-{rng.randint(1, 800):04d}", "qty": rng.randint(1, 5),
                     "price": round(rng.uniform(1, 300), 2)}
                    for _ in range(rng.randint(1, 4))
                ],
                "status": rng.choice(["paid", "shipped", "cancelled"]),
            }
        )
    return "\n".join(json.dumps(r) for r in records).encode()


CODECS = {
    "gzip": (lambda data, level: gzip.compress(data, compresslevel=level, mtime=0),
             gzip.decompress, range(1, 10), 6),
    "bzip2": (lambda data, level: bz2.compress(data, compresslevel=level),
              bz2.decompress, range(1, 10), 9),
    "lzma": (lambda data, level: lzma.compress(data, preset=level),
             lzma.decompress, range(0, 10), 6),
}


def best_time(func, *args) -> tuple[float, bytes]:
    # 여러 번 돌려 가장 빠른 값을 쓴다. 다른 프로세스가 끼어든 회차를 버리려는 것이다.
    best = float("inf")
    result = b""
    for _ in range(REPEAT):
        start = time.perf_counter()
        result = func(*args)
        best = min(best, time.perf_counter() - start)
    return best, result


def measure(name: str, data: bytes, level: int) -> tuple[int, float, float]:
    compress, decompress, _, _ = CODECS[name]
    c_sec, packed = best_time(compress, data, level)
    d_sec, unpacked = best_time(decompress, packed)
    assert unpacked == data, f"{name} level {level} 왕복 실패"
    return len(packed), c_sec, d_sec


def mb_per_sec(size: int, sec: float) -> float:
    return size / sec / 1_000_000


def print_environment() -> None:
    print("환경")
    print(f"  Python {platform.python_version()} / {platform.system()} {platform.release()}")
    print(f"  zlib  {zlib.ZLIB_RUNTIME_VERSION}")
    print(f"  반복 {REPEAT}회 중 최솟값, 시드 {SEED}")
    print()


def main() -> None:
    print_environment()
    rng = random.Random(SEED)
    log_data = make_log(rng)
    json_data = make_json(rng)
    # 이미 압축된 입력 — 로그를 zlib 로 한 번 눌러 둔 것. 이미지·동영상·zip 과 같은 처지다.
    packed_data = zlib.compress(log_data, 9)
    inputs = {"로그": log_data, "JSON": json_data, "압축된 바이너리": packed_data}

    print("1. 입력")
    for label, data in inputs.items():
        print(f"  {label:<10} {len(data):>10,} 바이트")
    print("  로그 첫 줄 :", log_data.split(b"\n", 1)[0].decode())
    print("  JSON 첫 줄 :", json_data.split(b"\n", 1)[0].decode()[:100], "...")
    print()

    print("2. 명령행 도구의 기본 수준(gzip -6, bzip2 -9, xz -6)으로 세 입력 대조 (비율 = 압축 후 / 원본)")
    print(f"  {'입력':<10} {'코덱':<6} {'수준':>4} {'크기':>11} {'비율':>7} {'압축 MB/s':>10} {'해제 MB/s':>10}")
    for label, data in inputs.items():
        for name, (_, _, _, default_level) in CODECS.items():
            size, c_sec, d_sec = measure(name, data, default_level)
            print(f"  {label:<10} {name:<6} {default_level:>4} {size:>11,} {size / len(data):>7.3f}"
                  f" {mb_per_sec(len(data), c_sec):>10.1f} {mb_per_sec(len(data), d_sec):>10.1f}")
    print()

    print("3. 로그 입력에서 수준을 올릴 때 — 한 단계 올려서 줄어든 바이트와 늘어난 압축 시간")
    for name, (_, _, levels, _) in CODECS.items():
        print(f"  [{name}]")
        print(f"  {'수준':>4} {'크기':>11} {'비율':>7} {'압축 ms':>9} {'해제 ms':>9} {'직전 대비 줄어든 바이트':>22}")
        previous = None
        for level in levels:
            size, c_sec, d_sec = measure(name, log_data, level)
            saved = "" if previous is None else f"{previous - size:,}"
            print(f"  {level:>4} {size:>11,} {size / len(log_data):>7.4f}"
                  f" {c_sec * 1000:>9.1f} {d_sec * 1000:>9.1f} {saved:>22}")
            previous = size
    print()
    print("파이썬:", sys.version.split()[0])


if __name__ == "__main__":
    main()
