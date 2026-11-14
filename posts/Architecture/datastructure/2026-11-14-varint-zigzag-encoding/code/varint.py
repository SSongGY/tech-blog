"""Protocol Buffers 인코딩 명세의 varint·지그재그를 표준 라이브러리로 구현하고 바이트 수를 잰다.

1) 명세 예제 검산 — 1 -> 01, 150 -> 96 01
2) 음수를 그대로(2의 보수 64비트) varint 로 넣으면 몇 바이트인가
3) 지그재그 대응표 — 명세 표의 값과 맞는지
4) 바이트 수가 바뀌는 경계값
5) 값 분포별 평균 바이트 — varint · 지그재그 · fixed32/fixed64
6) 정렬된 타임스탬프 — 그대로 vs 차이값(delta) + 지그재그
"""
import random
import struct

MASK64 = (1 << 64) - 1


def encode_varint(value):
    """부호 없는 64비트 정수를 base-128 varint 로. 낮은 7비트 묶음부터 내보낸다."""
    if value < 0 or value > MASK64:
        raise ValueError("unsigned 64-bit only")
    out = bytearray()
    while True:
        low7 = value & 0x7F
        value >>= 7
        if value:
            out.append(low7 | 0x80)  # 최상위 비트 1 = 뒤에 바이트가 더 있다
        else:
            out.append(low7)
            return bytes(out)


def decode_varint(data):
    result = shift = 0
    for count, byte in enumerate(data, start=1):
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return result, count
        shift += 7
        if count == 10:
            break
    raise ValueError("varint longer than 10 bytes or truncated")


def encode_int64(value):
    """int32/int64 필드처럼 음수를 64비트 2의 보수로 바꿔 varint 로."""
    return encode_varint(value & MASK64)


def zigzag32(n):
    # 명세의 (n << 1) ^ (n >> 31) — 파이썬 정수는 무한 길이라 32비트로 잘라 준다
    return ((n << 1) ^ (n >> 31)) & 0xFFFFFFFF


def zigzag64(n):
    return ((n << 1) ^ (n >> 63)) & MASK64


def unzigzag(z):
    return (z >> 1) ^ -(z & 1)


def hex_bytes(data):
    return " ".join(f"{b:02x}" for b in data)


def part1():
    print("[1] 명세 예제 검산")
    for value in (1, 150):
        encoded = encode_varint(value)
        decoded, length = decode_varint(encoded)
        print(f"  {value:>4} -> {hex_bytes(encoded):<6} 다시 읽으면 {decoded} ({length}바이트)")
    print()


def part2():
    print("[2] 음수를 int64 처럼(2의 보수) 넣으면")
    for value in (-1, -2, -150):
        encoded = encode_int64(value)
        print(f"  {value:>5} -> {len(encoded):2d}바이트  {hex_bytes(encoded)}")
    print()


def part3():
    print("[3] 지그재그 대응 (32비트 공식)")
    for n in (0, -1, 1, -2, 2, 0x7FFFFFFF, -0x80000000):
        z = zigzag32(n)
        print(f"  {n:>12} -> {z:>11} (0x{z:08x})  되돌리면 {unzigzag(z)}")
    print("  지그재그 후 바이트 수:")
    for value in (-1, -2, -150):
        encoded = encode_varint(zigzag64(value))
        print(f"  {value:>5} -> {len(encoded)}바이트  {hex_bytes(encoded)}")
    print()


def part4():
    print("[4] 바이트 수가 바뀌는 경계")
    boundaries = [0, 127, 128, 16_383, 16_384, (1 << 21) - 1, 1 << 21,
                  (1 << 28) - 1, 1 << 28, (1 << 56) - 1, 1 << 56, 1 << 63, MASK64]
    for value in boundaries:
        print(f"  {value:>20} -> {len(encode_varint(value)):2d}바이트")
    print()


def average_bytes(values, encoder):
    return sum(len(encoder(v)) for v in values) / len(values)


def part5(seed=20261114, count=10_000):
    rng = random.Random(seed)
    datasets = {
        "작은 개수 0~100": [rng.randint(0, 100) for _ in range(count)],
        "부호 있는 증감 -50~50": [rng.randint(-50, 50) for _ in range(count)],
        "uint32 균등 0~2^32-1": [rng.randint(0, (1 << 32) - 1) for _ in range(count)],
        "밀리초 시각 ~1.76e12": [1_763_000_000_000 + rng.randint(0, 86_400_000) for _ in range(count)],
    }
    print(f"[5] 값 분포별 평균 바이트 ({count}개씩, 시드 {seed})")
    print("  분포                    | int64 varint | 지그재그 varint | fixed32 | fixed64")
    for name, values in datasets.items():
        plain = average_bytes(values, encode_int64)
        zig = average_bytes(values, lambda v: encode_varint(zigzag64(v)))
        fits32 = all(-(1 << 31) <= v < (1 << 32) for v in values)
        fixed32 = f"{len(struct.pack('<I', 0)):7d}" if fits32 else "    -  "
        fixed64 = len(struct.pack("<Q", 0))
        print(f"  {name:<22}| {plain:12.3f} | {zig:15.3f} | {fixed32} | {fixed64:7d}")
    print("  (fixed32 은 값이 32비트에 들어갈 때만)")
    print()


def part6(seed=20261114, count=10_000):
    rng = random.Random(seed)
    timestamps = sorted(1_763_000_000_000 + rng.randint(0, 86_400_000) for _ in range(count))
    deltas = [timestamps[0]] + [b - a for a, b in zip(timestamps, timestamps[1:])]
    raw_total = sum(len(encode_varint(t)) for t in timestamps)
    delta_total = sum(len(encode_varint(zigzag64(d))) for d in deltas)
    # 순서가 섞이면 차이값에 음수가 생긴다 — 지그재그가 필요한 이유
    shuffled = timestamps[:]
    rng.shuffle(shuffled)
    shuffled_deltas = [shuffled[0]] + [b - a for a, b in zip(shuffled, shuffled[1:])]
    shuffled_zig = sum(len(encode_varint(zigzag64(d))) for d in shuffled_deltas)
    shuffled_plain = sum(len(encode_int64(d)) for d in shuffled_deltas)
    print(f"[6] 밀리초 시각 {count}개를 정렬해 저장")
    print(f"  그대로 varint            : {raw_total:7d}바이트")
    print(f"  차이값 + 지그재그 varint : {delta_total:7d}바이트")
    print(f"  최대 차이값              : {max(deltas[1:])}")
    print(f"  섞인 순서의 차이값 — 음수 {sum(d < 0 for d in shuffled_deltas)}개")
    print(f"    지그재그 varint        : {shuffled_zig:7d}바이트")
    print(f"    int64 varint (그대로)  : {shuffled_plain:7d}바이트")
    # 바이트열로 이어 붙였다가 처음부터 읽어 되돌린다 — 길이 정보 없이도 경계가 나뉘는지 확인
    stream = b"".join(encode_varint(zigzag64(d)) for d in shuffled_deltas)
    restored, position, total = [], 0, 0
    while position < len(stream):
        z, length = decode_varint(stream[position:position + 10])
        position += length
        total += unzigzag(z)
        restored.append(total)
    print(f"  섞인 순서 바이트열({len(stream)}바이트)을 읽어 복원 일치: {restored == shuffled}")
    print()


if __name__ == "__main__":
    part1()
    part2()
    part3()
    part4()
    part5()
    part6()
