"""Gorilla(VLDB 2015) 시계열 압축을 구현해 점당 비트 수를 잰다.

논문 4.1 절의 규칙을 그대로 따르고, 논문이 정하지 않은 세 곳은 아래처럼 정했다.
  - delta-of-delta 를 7·9·12 비트에 넣는 방식: 범위 하한을 빼서(오프셋) 부호 없는 수로 넣는다
  - 앞자리 0 개수가 31 을 넘으면 5비트에 못 넣으므로 31 로 줄이고 그만큼 의미 비트를 늘린다
  - 의미 비트 길이 64 는 6비트(0~63)에 못 넣으므로 0 으로 적고 64 로 읽는다

1) 논문 Figure 2 재현 — 세 점이 167비트가 되는가
2) 시계열 종류별 점당 비트 — 같은 값, 정수 카운터, 소수 둘째 자리 게이지, 난수
3) 타임스탬프만 — 고른 간격, 1초 흔들림, 빠진 점
4) 논문이 정하지 않은 자리가 실제로 생기는가
"""
import random
import struct
import zlib
from collections import Counter
from datetime import datetime, timezone

SEED = 20261115
DOD_BUCKETS = [  # (머리 비트, 값 비트, 하한, 상한) — 논문 4.1.1 의 (c)~(e)
    ("10", 7, -63, 64),
    ("110", 9, -255, 256),
    ("1110", 12, -2047, 2048),
]


def float_bits(value):
    return struct.unpack(">Q", struct.pack(">d", value))[0]


def bits_float(bits):
    return struct.unpack(">d", struct.pack(">Q", bits))[0]


class BitWriter:
    def __init__(self):
        self.bits = []

    def write(self, value, width):
        self.bits.extend((value >> (width - 1 - i)) & 1 for i in range(width))

    def write_str(self, pattern):
        self.bits.extend(int(ch) for ch in pattern)


class BitReader:
    def __init__(self, bits):
        self.bits, self.pos = bits, 0

    def read(self, width):
        value = 0
        for _ in range(width):
            value = (value << 1) | self.bits[self.pos]
            self.pos += 1
        return value


def encode(header_ts, points, stats=None):
    stats = stats if stats is not None else Counter()
    out = BitWriter()
    out.write(header_ts, 64)
    t0, v0 = points[0]
    out.write(t0 - header_ts, 14)
    out.write(float_bits(v0), 64)
    prev_t, prev_delta, prev_bits = t0, t0 - header_ts, float_bits(v0)
    prev_lead, prev_trail = 65, 65  # 아직 창이 없다
    for t, v in points[1:]:
        delta = t - prev_t
        dod = delta - prev_delta
        if dod == 0:
            out.write_str("0")
            stats["ts 0"] += 1
        else:
            for head, width, low, high in DOD_BUCKETS:
                if low <= dod <= high:
                    out.write_str(head)
                    out.write(dod - low, width)
                    stats[f"ts {head}"] += 1
                    break
            else:
                out.write_str("1111")
                out.write(dod & 0xFFFFFFFF, 32)
                stats["ts 1111"] += 1
        prev_t, prev_delta = t, delta

        bits = float_bits(v)
        xor = bits ^ prev_bits
        if xor == 0:
            out.write_str("0")
            stats["val 0"] += 1
        else:
            lead = 64 - xor.bit_length()
            trail = (xor & -xor).bit_length() - 1
            if lead >= prev_lead and trail >= prev_trail:
                out.write_str("10")
                out.write(xor >> prev_trail, 64 - prev_lead - prev_trail)
                stats["val 10"] += 1
            else:
                if lead > 31:
                    lead = 31
                    stats["lead>31 clamp"] += 1
                length = 64 - lead - trail
                if length == 64:
                    stats["length 64"] += 1
                out.write_str("11")
                out.write(lead, 5)
                out.write(length & 0x3F, 6)
                out.write(xor >> trail, length)
                prev_lead, prev_trail = lead, trail
                stats["val 11"] += 1
        prev_bits = bits
    return out.bits, stats


def decode(bits, count):
    reader = BitReader(bits)
    header_ts = reader.read(64)
    t = header_ts + reader.read(14)
    value_bits = reader.read(64)
    points = [(t, bits_float(value_bits))]
    delta = t - header_ts
    lead, trail = 0, 0
    for _ in range(count - 1):
        head = ""
        while len(head) < 4 and reader.read(1) == 1:
            head += "1"
        head = head + "0" if len(head) < 4 else head
        if head == "0":
            dod = 0
        elif head == "1111":
            dod = reader.read(32)
            dod = dod - (1 << 32) if dod >= 1 << 31 else dod
        else:
            _, width, low, _ = next(b for b in DOD_BUCKETS if b[0] == head)
            dod = reader.read(width) + low
        delta += dod
        t += delta
        if reader.read(1) == 1:
            if reader.read(1) == 1:
                lead = reader.read(5)
                length = reader.read(6) or 64
                trail = 64 - lead - length
            length = 64 - lead - trail
            value_bits ^= reader.read(length) << trail
        points.append((t, bits_float(value_bits)))
    return points


def report(name, header_ts, points):
    bits, stats = encode(header_ts, points)
    assert decode(bits, len(points)) == points, name
    raw = b"".join(struct.pack(">qd", t, v) for t, v in points)
    zlib_bytes = len(zlib.compress(raw, 9))
    per_point = len(bits) / len(points)
    print(f"  {name:<24} {per_point:6.1f} 비트/점  {per_point / 8:5.2f} 바이트/점"
          f"  zlib {zlib_bytes / len(points):5.2f} 바이트/점  복원 일치")
    return stats


def figure2():
    header = int(datetime(2015, 3, 24, 2, 0, 0, tzinfo=timezone.utc).timestamp())
    points = [(header + 62, 12.0), (header + 122, 12.0), (header + 182, 24.0)]
    bits, stats = encode(header, points)
    xor = float_bits(12.0) ^ float_bits(24.0)
    print("[1] 논문 Figure 2 — 02:01:02 12, 02:02:02 12, 02:03:02 24")
    print(f"  12.0 = 0x{float_bits(12.0):016x}, 24.0 = 0x{float_bits(24.0):016x}")
    print(f"  XOR  = 0x{xor:016x}  앞자리 0 {64 - xor.bit_length()}개, 의미 비트 1개")
    print("  머리 64 + 첫 delta 14 + 첫 값 64 + (dod -2: 9) + (값 같음: 1)"
          " + (dod 0: 1) + (XOR: 2+5+6+1=14)")
    print(f"  전체 {len(bits)} 비트 = {len(bits) / 8:.2f} 바이트 (원래 {len(points) * 16} 바이트)")
    print(f"  유형별 {dict(sorted(stats.items()))}")
    print(f"  복원 일치: {decode(bits, len(points)) == points}")
    print()


def series_compare():
    rng = random.Random(SEED)
    header = 1_700_000_000 // 7200 * 7200  # 두 시간 경계에 맞춘 머리
    times = [header + 60 * (i + 1) for i in range(120)]  # 2시간 블록, 60초 간격
    level = [42.0 if rng.random() > 0.05 else 43.0 for _ in times]
    counter, total = [], 0
    for _ in times:
        total += rng.randint(0, 20)
        counter.append(float(total))
    gauge, current = [], 37.25
    for _ in times:
        current = round(current + rng.choice((-0.25, 0.0, 0.25, 0.5)), 2)
        gauge.append(current)
    cents, current = [], 37.25
    for _ in times:
        current = round(current + rng.choice((-0.03, 0.0, 0.01, 0.07)), 2)
        cents.append(current)
    noise = [rng.random() * 100 for _ in times]

    print("[2] 2시간 블록 120점, 60초 간격 — 값 종류별")
    all_stats = {}
    for name, values in [
        ("같은 값(가끔 43)", level),
        ("정수 카운터", counter),
        ("0.25 단위 게이지", gauge),
        ("0.01 단위 게이지", cents),
        ("균등 난수 0~100", noise),
    ]:
        all_stats[name] = report(name, header, list(zip(times, values)))
    print()
    print("  값 유형 분포 (val 0 = 같은 값 1비트, 10 = 창 재사용, 11 = 새 창)")
    for name, stats in all_stats.items():
        cases = {k: stats.get(k, 0) for k in ("val 0", "val 10", "val 11")}
        print(f"  {name:<24} {cases}")
    print()
    return rng, header


def timestamp_compare(rng, header):
    print("[3] 타임스탬프 — 값은 전부 같게 두고 시각만 바꿈")
    regular = [header + 60 * (i + 1) for i in range(120)]
    jitter = [t + (rng.choice((-1, 1)) if rng.random() < 0.1 else 0) for t in regular]
    missing = [t for i, t in enumerate(regular) if i % 17 != 16]
    irregular, t = [], header
    for _ in range(120):
        t += rng.randint(1, 600)
        irregular.append(t)
    for name, times in [
        ("고른 60초", regular),
        ("10% 가 ±1초", jitter),
        ("17점마다 1점 빠짐", missing),
        ("1~600초 무작위", irregular),
    ]:
        stats = report(name, header, [(t, 1.0) for t in times])
        ts = {k: v for k, v in sorted(stats.items()) if k.startswith("ts")}
        print(f"    {ts}")
    print()


def gap_cases():
    print("[4] 논문이 정하지 않은 자리")
    header = 0
    sign_flip = [(60, 1.0), (120, -1.0000000000000002)]
    bits, stats = encode(header, sign_flip)
    xor = float_bits(1.0) ^ float_bits(-1.0000000000000002)
    print(f"  1.0 -> -1.0000000000000002 : XOR 0x{xor:016x}, 의미 비트 {xor.bit_length()}개")
    print(f"    {dict(stats)}  복원 일치: {decode(bits, 2) == sign_flip}")
    tiny = [(60, 1.0), (120, 1.0000000000000002), (180, 1.0)]
    bits, stats = encode(header, tiny)
    print(f"  1.0 -> 1.0000000000000002 (마지막 비트만 다름): {dict(stats)}"
          f"  복원 일치: {decode(bits, 3) == tiny}")
    print(f"  7비트 2의 보수 범위 = [-64, 63], 논문 범위 = [-63, 64] -> 64 는 2의 보수로 못 넣는다")
    edge = [(60, 1.0), (120, 1.0), (244, 1.0)]  # delta 60 -> 124, dod 64
    bits, stats = encode(header, edge)
    print(f"  dod = 64 : {dict(stats)}  복원 일치: {decode(bits, 3) == edge}")


if __name__ == "__main__":
    print(f"zlib {zlib.ZLIB_RUNTIME_VERSION} (비교용, 압축 수준 9)")
    print()
    figure2()
    rng, header = series_compare()
    timestamp_compare(rng, header)
    gap_cases()
