"""차등 맨체스터 부호화 검산.

비트 하나를 반 비트 두 칸(+1/-1)으로 표현한다. 규약은 두 가지를 나란히 둔다.

- IEEE 802.5 (Token Ring): 중간 천이는 항상 있다. 비트 경계에서 천이가 있으면 0, 없으면 1.
- IEEE 802.3cg 10BASE-T1S: 비트 시작의 천이는 항상 있다. 중간 천이가 있으면 1, 없으면 0.
"""

import sys

BITS = [0, 1, 0, 0, 1, 1, 1, 0]


def encode_8025(bits, level=1):
    halves = []
    for bit in bits:
        if bit == 0:
            level = -level  # 0 만 경계에서 뒤집는다
        halves.append(level)
        level = -level  # 중간 천이는 비트 값과 무관하게 넣는다
        halves.append(level)
    return halves


def encode_t1s(bits, level=1):
    halves = []
    for bit in bits:
        level = -level  # 클록 천이: 모든 비트의 시작
        halves.append(level)
        if bit == 1:
            level = -level  # 데이터 천이: 1 일 때만 비트 중간
        halves.append(level)
    return halves


def decode_8025(halves, prev_level):
    # 극성은 보지 않고 경계 천이 유무만 본다
    bits = []
    for i in range(0, len(halves), 2):
        bits.append(0 if halves[i] != prev_level else 1)
        prev_level = halves[i + 1]
    return bits


def decode_t1s(halves):
    return [0 if halves[i] == halves[i + 1] else 1 for i in range(0, len(halves), 2)]


def waveform(halves):
    return "".join("‾" if h > 0 else "_" for h in halves)


def transitions_per_bit(halves, prev_level):
    counts = []
    for i in range(0, len(halves), 2):
        counts.append((halves[i] != prev_level) + (halves[i] != halves[i + 1]))
        prev_level = halves[i + 1]
    return counts


def main():
    print(f"Python {sys.version.split()[0]}")
    print(f"입력 비트      : {''.join(map(str, BITS))}")
    print("반 비트 한 칸 = 문자 하나, ‾ = +1, _ = -1, 시작 전 선로 = +1")
    print()

    for name, encode in (("IEEE 802.5", encode_8025), ("10BASE-T1S", encode_t1s)):
        halves = encode(BITS)
        print(f"[{name}]")
        print(f"  파형          : {waveform(halves)}")
        print(f"  비트당 천이 수: {transitions_per_bit(halves, 1)}")
        print(f"  레벨 합(DC)   : {sum(halves)}")
        print()

    print("[1] 극성 반전 후 복호 — 선로 두 가닥을 바꿔 꽂은 경우")
    h8025 = encode_8025(BITS)
    ht1s = encode_t1s(BITS)
    inv8025 = [-h for h in h8025]
    invt1s = [-h for h in ht1s]
    print(f"  802.5 원본 복호 : {decode_8025(h8025, 1)}")
    print(f"  802.5 반전 복호 : {decode_8025(inv8025, -1)}")
    print(f"  T1S   원본 복호 : {decode_t1s(ht1s)}")
    print(f"  T1S   반전 복호 : {decode_t1s(invt1s)}")
    print()

    print("[2] 같은 비트열을 두 규약으로 보냈을 때 파형이 같은가")
    print(f"  같음: {h8025 == ht1s}")
    print()

    print("[3] IEEE 802.5 부호 위반 심벌 — 시작 구분자 J K 0 J K 0 0 0")
    level = 1
    halves = []
    for sym in "JK0JK000":
        if sym == "0":
            level = -level
            halves += [level, -level]
            level = -level
        elif sym == "J":  # 경계 천이 없음, 중간 천이 없음
            halves += [level, level]
        elif sym == "K":  # 경계 천이 있음, 중간 천이 없음
            level = -level
            halves += [level, level]
    print(f"  파형          : {waveform(halves)}")
    print(f"  비트당 천이 수: {transitions_per_bit(halves, 1)}")
    print("  J·K 칸은 중간 천이가 없다 — 데이터 비트에서는 나올 수 없는 모양")


if __name__ == "__main__":
    main()
