"""선로 부호 5가지 검산.

같은 비트열을 NRZ-L, NRZI, 맨체스터, 차등 맨체스터, 4B5B+NRZI 로 부호화해
천이 수, 천이 없이 버티는 최장 구간, 레벨 합(DC)을 나란히 본다.
반 비트 한 칸 = +1/-1 하나. NRZ 계열도 비교를 위해 한 비트를 두 칸으로 늘려 적는다.
"""

import itertools
import sys

BITS = [1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1]

# IEEE 802.3cg Table 147-1 (4B/5B Encoding) 의 데이터 부호 16개
FOUR_B_FIVE_B = {
    0x0: "11110", 0x1: "01001", 0x2: "10100", 0x3: "10101",
    0x4: "01010", 0x5: "01011", 0x6: "01110", 0x7: "01111",
    0x8: "10010", 0x9: "10011", 0xA: "10110", 0xB: "10111",
    0xC: "11010", 0xD: "11011", 0xE: "11100", 0xF: "11101",
}


def nrz_l(bits):
    return [h for b in bits for h in ((1, 1) if b else (-1, -1))]


def nrzi(bits, level=-1, toggle_on=1):
    # toggle_on=1: 1 에서 뒤집는다. toggle_on=0: USB 처럼 0 에서 뒤집는다
    halves = []
    for b in bits:
        if b == toggle_on:
            level = -level
        halves += [level, level]
    return halves


def manchester(bits, one_rising=True):
    # IEEE 802.3 규약은 1 = 중간 상승, G.E. Thomas 규약은 그 반대
    halves = []
    for b in bits:
        rising = (b == 1) == one_rising
        halves += [-1, 1] if rising else [1, -1]
    return halves


def diff_manchester(bits, level=-1):
    # 10BASE-T1S 규약: 비트 시작은 항상 천이, 1 이면 중간에도 천이
    halves = []
    for b in bits:
        level = -level
        halves.append(level)
        if b == 1:
            level = -level
        halves.append(level)
    return halves


def transitions(halves, prev=-1):
    count = 0
    for h in halves:
        count += h != prev
        prev = h
    return count


def longest_flat(halves, prev=-1):
    # 천이 없이 같은 레벨이 이어진 최장 길이. 반 비트 단위
    run = best = 0
    for h in halves:
        run = run + 1 if h == prev else 1
        best = max(best, run)
        prev = h
    return best


def peak_running_sum(halves):
    # 레벨 누적 합이 한쪽으로 얼마나 쏠렸나. 커지면 교류 결합 선로에서 기준선이 흘러간다
    total = peak = 0
    for h in halves:
        total += h
        peak = max(peak, abs(total))
    return peak


def wave(halves):
    return "".join("‾" if h > 0 else "_" for h in halves)


def to_4b5b(bits):
    out = []
    for i in range(0, len(bits), 4):
        nibble = int("".join(map(str, bits[i:i + 4])), 2)
        out += [int(c) for c in FOUR_B_FIVE_B[nibble]]
    return out


def report(name, halves, bit_count):
    t = transitions(halves)
    print(f"{name:<22}{wave(halves)}")
    print(f"{'':<22}천이 {t}번 / {bit_count}비트, "
          f"최장 무천이 {longest_flat(halves) / 2:g}비트, "
          f"레벨 합 {sum(halves):+d}, 누적 합 최대 {peak_running_sum(halves)}")


def main():
    print(f"Python {sys.version.split()[0]}")
    print(f"입력 16비트: {''.join(map(str, BITS))}")
    print("‾ = +1, _ = -1, 반 비트 한 칸 = 문자 하나, 시작 전 선로 = -1")
    print()

    print("[1] 같은 16비트를 부호별로")
    report("NRZ-L", nrz_l(BITS), 16)
    report("NRZI (1=천이)", nrzi(BITS), 16)
    report("NRZI (0=천이, USB)", nrzi(BITS, toggle_on=0), 16)
    report("맨체스터 IEEE 802.3", manchester(BITS), 16)
    report("맨체스터 G.E. Thomas", manchester(BITS, one_rising=False), 16)
    report("차등 맨체스터(T1S)", diff_manchester(BITS), 16)
    coded = to_4b5b(BITS)
    print(f"{'4B5B 부호 비트':<22}{''.join(map(str, coded))}  ({len(coded)}비트)")
    report("4B5B + NRZI(1=천이)", nrzi(coded), 20)
    print()

    print("[2] 극성을 뒤집으면 — 선로 두 가닥을 바꿔 꽂은 경우")
    for name, enc in (("맨체스터", manchester(BITS)),
                      ("차등 맨체스터", diff_manchester(BITS))):
        inv = [-h for h in enc]
        if name == "맨체스터":
            dec = [1 if inv[i] < inv[i + 1] else 0 for i in range(0, len(inv), 2)]
        else:
            dec = [int(inv[i] != inv[i + 1]) for i in range(0, len(inv), 2)]
        print(f"  {name:<12} 복호 일치: {dec == BITS}")
    print()

    print("[3] 4B5B 데이터 부호 16개의 성질 (IEEE 802.3cg Table 147-1)")
    codes = list(FOUR_B_FIVE_B.values())
    ones = [c.count("1") for c in codes]
    print(f"  부호당 1의 개수: 최소 {min(ones)}, 최대 {max(ones)}")
    worst = max(len(max(("".join(p)).split("1"), key=len))
                for p in itertools.product(codes, repeat=2))
    print(f"  데이터 부호 2개를 이었을 때 0 연속 최대: {worst}")
    print(f"  부호율: 4/5 = {4 / 5:.0%}, 10 Mb/s → {10 * 5 / 4:g} MBd")


if __name__ == "__main__":
    main()
