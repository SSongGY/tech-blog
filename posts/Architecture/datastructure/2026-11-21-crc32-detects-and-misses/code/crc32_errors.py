"""CRC-32 가 반드시 잡는 오류와 놓치는 오류를 센다.

1) RFC 1952 §8 의 표 방식 CRC-32 를 그대로 옮겨 zlib.crc32 와 맞춘다
2) 선형성 — 같은 길이면 crc(a ^ b) = crc(a) ^ crc(b) ^ crc(0...)
3) 1비트·2비트·3비트·4비트·5비트 오류를 '신드롬'으로 전수 검사한다
   Koopman(2002) 표의 경계 — HD=6 은 268비트까지, HD=5 는 2974비트까지 — 를 양옆에서 확인한다
4) 길이 32 이하의 버스트는 표본 전부 잡히고, 생성 다항식 모양의 33비트 버스트는 놓친다
5) 끝에 4바이트만 덧붙여 원하는 CRC 를 만든다 — 변조 방지에 못 쓰는 이유
6) 순수 파이썬 구현과 zlib 의 속도
"""
import random
import sys
import time
import zlib

REFLECTED_POLY = 0xEDB88320  # RFC 1952 §8 표 생성 코드의 상수


def make_crc_table():
    table = []
    for n in range(256):
        c = n
        for _ in range(8):
            c = (c >> 1) ^ REFLECTED_POLY if c & 1 else c >> 1
        table.append(c)
    return table


CRC_TABLE = make_crc_table()


def update_crc(crc, data):
    # RFC 1952 §8 update_crc(): 앞뒤 1의 보수(0xffffffff XOR)를 함수 안에서 한다
    c = crc ^ 0xFFFFFFFF
    for byte in data:
        c = CRC_TABLE[(c ^ byte) & 0xFF] ^ (c >> 8)
    return c ^ 0xFFFFFFFF


def crc32_rfc1952(data):
    return update_crc(0, data)


def flip_bit(data, bit_position):
    """비트 위치는 CRC 가 읽는 순서다 — 바이트 0 의 최하위 비트가 0번."""
    changed = bytearray(data)
    changed[bit_position // 8] ^= 1 << (bit_position % 8)
    return bytes(changed)


def syndromes(length_bytes):
    """길이 length_bytes 의 메시지에서 비트 하나를 뒤집었을 때 CRC 가 바뀌는 양.

    선형성 덕분에 이 값은 메시지 내용과 무관하다. 저장된 CRC 32비트가 뒤집히는
    경우는 그 비트 하나만 바뀌므로 1 << k 를 더한다. 이 목록이 코드어 전체의
    '비트 위치 → 신드롬' 표다.
    """
    zeros = bytes(length_bytes)
    base = zlib.crc32(zeros)
    data_part = [zlib.crc32(flip_bit(zeros, i)) ^ base for i in range(length_bytes * 8)]
    crc_part = [1 << k for k in range(32)]
    return data_part + crc_part


def smallest_undetected(syndrome_list, max_weight):
    """신드롬 XOR 이 0 이 되는 가장 작은 비트 수를 찾는다. 없으면 None.

    반환: (무게, 비트 위치 튜플)
    """
    n = len(syndrome_list)
    first_index = {}
    for i, s in enumerate(syndrome_list):
        if s == 0:
            return 1, (i,)
        if s in first_index:
            return 2, (first_index[s], i)
        first_index[s] = i
    if max_weight < 3:
        return None
    # 3비트: 두 신드롬의 XOR 이 세 번째 신드롬과 같은가
    for i in range(n):
        si = syndrome_list[i]
        for j in range(i + 1, n):
            k = first_index.get(si ^ syndrome_list[j])
            if k is not None and k != i and k != j:
                return 3, tuple(sorted((i, j, k)))
    if max_weight < 4:
        return None
    # 4비트: XOR 값이 같은 서로 다른 두 쌍이 있는가.
    # 쌍이 수백만 개라 사전 대신 (XOR, i, j) 를 정수 하나로 묶어 정렬한다.
    packed = sorted(
        ((syndrome_list[i] ^ syndrome_list[j]) << 24) | (i << 12) | j
        for i in range(n) for j in range(i + 1, n)
    )
    for left, right in zip(packed, packed[1:]):
        if left >> 24 == right >> 24:
            quad = {left >> 12 & 0xFFF, left & 0xFFF, right >> 12 & 0xFFF, right & 0xFFF}
            return 4, tuple(sorted(quad))
    del packed
    if max_weight < 5:
        return None
    pair_owner = {}
    for i in range(n):
        for j in range(i + 1, n):
            pair_owner[syndrome_list[i] ^ syndrome_list[j]] = (i, j)
    for i in range(n):
        si = syndrome_list[i]
        for j in range(i + 1, n):
            sij = si ^ syndrome_list[j]
            for k in range(j + 1, n):
                other = pair_owner.get(sij ^ syndrome_list[k])
                if other is not None and not set(other) & {i, j, k}:
                    return 5, tuple(sorted(other + (i, j, k)))
    return None


def show_hd(length_bytes, max_weight):
    started = time.perf_counter()
    result = smallest_undetected(syndromes(length_bytes), max_weight)
    elapsed = time.perf_counter() - started
    bits = length_bytes * 8
    if result is None:
        verdict = f"{max_weight}비트 이하 오류는 전부 잡힌다 → HD ≥ {max_weight + 1}"
    else:
        weight, positions = result
        verdict = f"{weight}비트 오류를 놓친다 → HD = {weight}  위치 {positions}"
    print(f"  데이터 {bits:5d}비트 ({length_bytes:3d}바이트) : {verdict}  [{elapsed:.1f}초]")
    return result


def verify_miss(message, positions):
    """찾은 위치를 실제 메시지에 적용해 CRC 비교가 통과하는지 확인한다."""
    data_bits = len(message) * 8
    damaged = message
    crc_flip = 0
    for p in positions:
        if p < data_bits:
            damaged = flip_bit(damaged, p)
        else:
            crc_flip ^= 1 << (p - data_bits)
    stored_crc = zlib.crc32(message) ^ crc_flip
    return damaged != message, zlib.crc32(damaged) == stored_crc


def forge_suffix(prefix, target_crc):
    """prefix 뒤에 4바이트를 붙여 CRC 가 target_crc 가 되게 한다 (GF(2) 연립방정식)."""
    base = zlib.crc32(prefix + bytes(4))
    columns = [zlib.crc32(prefix + flip_bit(bytes(4), i)) ^ base for i in range(32)]
    # 미지수 32개(덧붙일 비트) · 식 32개(CRC 비트). 가우스 소거.
    rows = []
    for bit in range(32):
        mask = 0
        for i, col in enumerate(columns):
            if col >> bit & 1:
                mask |= 1 << i
        rows.append([mask, (target_crc ^ base) >> bit & 1])
    pivot_rows = []
    for col in range(32):
        pivot = next((r for r in rows if r[0] >> col & 1 and r not in pivot_rows), None)
        if pivot is None:
            raise ValueError("해가 없다")
        for r in rows:
            if r is not pivot and r[0] >> col & 1:
                r[0] ^= pivot[0]
                r[1] ^= pivot[1]
        pivot_rows.append(pivot)
    solution = 0
    for col, r in enumerate(pivot_rows):
        if r[1]:
            solution |= 1 << col
    return solution.to_bytes(4, "little")


def main():
    print(f"Python {sys.version.split()[0]} · zlib {zlib.ZLIB_RUNTIME_VERSION}")

    print("\n[1] RFC 1952 §8 구현과 zlib.crc32")
    samples = [b"", b"a", b"123456789", b"The quick brown fox jumps over the lazy dog"]
    for sample in samples:
        mine, lib = crc32_rfc1952(sample), zlib.crc32(sample)
        print(f"  {sample[:24]!r:28} RFC1952={mine:08x} zlib={lib:08x} 같음={mine == lib}")

    print("\n[2] 선형성 — 같은 길이의 a, b")
    rng = random.Random(20261121)
    a, b = rng.randbytes(64), rng.randbytes(64)
    xored = bytes(x ^ y for x, y in zip(a, b))
    lhs = zlib.crc32(xored)
    rhs = zlib.crc32(a) ^ zlib.crc32(b) ^ zlib.crc32(bytes(64))
    print(f"  crc(a^b)={lhs:08x}  crc(a)^crc(b)^crc(0..)={rhs:08x}  같음={lhs == rhs}")

    print("\n[3-1] 1비트 오류 — 1500바이트 메시지의 12000비트를 하나씩 뒤집는다")
    message = rng.randbytes(1500)
    original = zlib.crc32(message)
    missed = sum(zlib.crc32(flip_bit(message, i)) == original for i in range(len(message) * 8))
    print(f"  12000개 중 놓친 것: {missed}")

    print("\n[3-2] HD=6 → 5 경계 (Koopman Table 1: HD=6 은 268비트까지)")
    show_hd(33, 5)
    result_272 = show_hd(34, 5)
    print("\n[3-3] HD=5 → 4 경계 (HD=5 는 2974비트까지)")
    show_hd(371, 4)
    result_2976 = show_hd(372, 4)
    print("\n[3-4] 찾은 오류를 실제 메시지에 적용해 본다")
    for length_bytes, (weight, positions) in ((34, result_272), (372, result_2976)):
        message = rng.randbytes(length_bytes)
        changed, passed = verify_miss(message, positions)
        print(f"  {length_bytes}바이트 메시지에 {weight}비트 뒤집기: 내용 바뀜={changed} CRC 통과={passed}")

    print("\n[4-1] 버스트 오류 — 길이 1~32, 위치·모양 무작위 200000개 (1500바이트)")
    message = rng.randbytes(1500)
    value = int.from_bytes(message, "little")
    original = zlib.crc32(message)
    missed = 0
    for _ in range(200_000):
        burst_length = rng.randint(1, 32)
        if burst_length == 1:
            pattern = 1
        else:
            middle = rng.getrandbits(burst_length - 2) if burst_length > 2 else 0
            pattern = 1 | (middle << 1) | (1 << (burst_length - 1))
        offset = rng.randrange(len(message) * 8 - burst_length + 1)
        damaged = (value ^ (pattern << offset)).to_bytes(len(message), "little")
        missed += zlib.crc32(damaged) == original
    print(f"  놓친 것: {missed}")

    print("\n[4-2] 길이 33 버스트 — 생성 다항식 x^32+...+1 의 계수 모양 그대로")
    generator_pattern = 1 | (REFLECTED_POLY << 1)
    print(f"  패턴 비트 수 {generator_pattern.bit_length()} · 1의 개수 {bin(generator_pattern).count('1')}")
    for offset in (0, 1000, 11000):
        damaged = (value ^ (generator_pattern << offset)).to_bytes(len(message), "little")
        print(f"  위치 {offset:5d}: 내용 바뀜={damaged != message} "
              f"crc {zlib.crc32(damaged):08x} == 원본 {original:08x} → {zlib.crc32(damaged) == original}")

    print("\n[5] 4바이트 덧붙여 원하는 CRC 만들기")
    genuine = b"PAY 100 TO ALICE"
    target = zlib.crc32(genuine)
    forged_prefix = b"PAY 900 TO MALLORY"
    suffix = forge_suffix(forged_prefix, target)
    forged = forged_prefix + suffix
    print(f"  원본  {genuine!r:40} crc={target:08x}")
    print(f"  위조  {forged!r:40} crc={zlib.crc32(forged):08x}")
    print(f"  덧붙인 4바이트 {suffix.hex()} · CRC 같음={zlib.crc32(forged) == target}")

    print("\n[6] 속도 — 1 MiB")
    blob = rng.randbytes(1 << 20)
    started = time.perf_counter()
    mine = crc32_rfc1952(blob)
    pure_seconds = time.perf_counter() - started
    started = time.perf_counter()
    for _ in range(100):
        lib = zlib.crc32(blob)
    zlib_seconds = (time.perf_counter() - started) / 100
    print(f"  순수 파이썬 {pure_seconds * 1000:8.1f} ms · zlib {zlib_seconds * 1000:6.3f} ms "
          f"· 배율 {pure_seconds / zlib_seconds:,.0f} · 값 같음={mine == lib}")


if __name__ == "__main__":
    main()
