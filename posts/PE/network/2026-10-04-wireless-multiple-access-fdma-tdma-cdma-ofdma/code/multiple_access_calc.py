"""무선 다중 접속 4방식이 자원을 나누는 단위와 그 비용을 규격 숫자로 계산한다.

근거
- FDMA: 3GPP TS 45.005 §2 (채널 간격 200 kHz, P-GSM 900 ARFCN 표)
- TDMA: 3GPP TS 45.002 §4.3 (타임슬롯 3/5200 s, 프레임 8슬롯)
- CDMA: 3GPP TS 25.213 §4.3.1 (OVSF 코드 트리), §4.4.1 (칩 속도 3.84 Mcps)
- OFDMA: 3GPP TS 36.211 §4.1, 표 6.12-1 / TS 36.300 §5.1.1 (15 kHz, Ts, CP 길이)
"""

import cmath
import math
import platform
import random

SPEED_OF_LIGHT = 299_792_458  # m/s


def print_section(title):
    print()
    print(f"[{title}]")


def fdma_gsm900():
    # P-GSM 900 상향 890~915 MHz, Fl(n) = 890 + 0.2*n, 1 <= n <= 124
    band_low, band_high, spacing = 890.0, 915.0, 0.2
    arfcns = range(1, 125)
    first, last = 890 + 0.2 * arfcns[0], 890 + 0.2 * arfcns[-1]
    raw_slots = round((band_high - band_low) / spacing)
    print(f"  대역 폭          {band_high - band_low:.0f} MHz / 채널 간격 {spacing * 1000:.0f} kHz"
          f" = {raw_slots} 칸")
    print(f"  배정 ARFCN       1~124 → {len(arfcns)}개 반송파")
    print(f"  첫·끝 반송파     {first:.1f} MHz, {last:.1f} MHz"
          f" (대역 끝과 {first - band_low:.1f} MHz, {band_high - last:.1f} MHz 떨어짐)")
    print(f"  하향 짝          Fu = Fl + 45 → {first + 45:.1f} MHz ~ {last + 45:.1f} MHz")
    return len(arfcns)


def tdma_gsm(carriers):
    slot_s = 3 / 5200
    frame_s = 8 * slot_s
    print(f"  타임슬롯         3/5200 s = {slot_s * 1e6:.1f} us")
    print(f"  TDMA 프레임      8 슬롯 = {frame_s * 1e3:.3f} ms")
    print(f"  같은 단말 다음 차례까지 {frame_s * 1e3:.3f} ms (7 슬롯 쉼)")
    print(f"  물리 채널 수     {carriers} 반송파 x 8 슬롯 = {carriers * 8}")


def ovsf_layer(spreading_factor):
    # TS 25.213 Figure 4: C(2n,2k) = [C(n,k), C(n,k)], C(2n,2k+1) = [C(n,k), -C(n,k)]
    codes = [[1]]
    while len(codes[0]) < spreading_factor:
        next_codes = []
        for code in codes:
            next_codes.append(code + code)
            next_codes.append(code + [-chip for chip in code])
        codes = next_codes
    return codes


def correlate(a, b):
    return sum(x * y for x, y in zip(a, b))


def cdma_ovsf():
    sf4 = ovsf_layer(4)
    for index, code in enumerate(sf4):
        print(f"  C(4,{index})  {' '.join(f'{chip:+d}' for chip in code)}")
    pairs = [(i, j, correlate(sf4[i], sf4[j])) for i in range(4) for j in range(i + 1, 4)]
    print("  같은 층 상관값   " + ", ".join(f"C4,{i}·C4,{j}={v}" for i, j, v in pairs))

    # 데이터 심볼 +1(단말 A, C4,1), -1(단말 B, C4,2)을 칩 단위로 더해 보낸다
    symbol_a, symbol_b = +1, -1
    on_air = [symbol_a * x + symbol_b * y for x, y in zip(sf4[1], sf4[2])]
    print(f"  공중 신호(A+B)   {on_air}")
    print(f"  A 역확산         {correlate(on_air, sf4[1]) / 4:+.0f}"
          f"   B 역확산 {correlate(on_air, sf4[2]) / 4:+.0f}")

    # C(2,1)은 4칩 동안 심볼 2개를 싣는다. 자손 C(4,2)·C(4,3)과는 데이터에 따라 섞인다
    parent = ovsf_layer(2)[1]
    for first, second in ((+1, +1), (+1, -1)):
        parent_signal = [first * chip for chip in parent] + [second * chip for chip in parent]
        values = [correlate(parent_signal, code) for code in sf4]
        print(f"  C(2,1)이 심볼 ({first:+d},{second:+d})을 실을 때 C(4,0..3)과 상관값 {values}")

    chip_rate = 3.84e6
    for sf in (4, 16, 64, 256):
        print(f"  SF {sf:>3}  심볼 속도 {chip_rate / sf / 1e3:>7.1f} ksps")


def ofdma_lte():
    subcarrier_spacing = 15_000
    ts = 1 / (subcarrier_spacing * 2048)
    print(f"  Ts               1/(15000x2048) = {ts * 1e9:.2f} ns")
    print(f"  유효 심볼        2048 Ts = {2048 * ts * 1e6:.2f} us (= 1/15 kHz)")

    normal_slot = (160 + 2048) + 6 * (144 + 2048)
    extended_slot = 6 * (512 + 2048)
    for label, cp, symbols, slot_ts in (
        ("일반 CP #0", 160, 7, normal_slot),
        ("일반 CP #1~6", 144, 7, normal_slot),
        ("확장 CP", 512, 6, extended_slot),
    ):
        cp_us = cp * ts * 1e6
        reach_km = SPEED_OF_LIGHT * cp * ts / 1e3
        print(f"  {label:<12} {cp:>3} Ts = {cp_us:5.2f} us  경로차 {reach_km:4.2f} km까지"
              f"  (슬롯 {symbols}심볼 = {slot_ts} Ts)")
    normal_overhead = (160 + 6 * 144) / normal_slot
    extended_overhead = 6 * 512 / extended_slot
    print(f"  CP 비중          일반 {normal_overhead * 100:.2f}%  확장 {extended_overhead * 100:.2f}%")
    print(f"  자원 블록        12 부반송파 x 15 kHz = {12 * 15} kHz, 0.5 ms 슬롯")


def ofdm_cp_demo():
    # 부반송파 64개짜리 작은 OFDM 심볼로 CP의 효과를 본다
    n = 64
    cp_len = 8
    # 규칙적인 값을 넣으면 시간 신호가 한 점에 몰려 반사파가 겹치지 않으므로 무작위 QPSK를 쓴다
    rng = random.Random(7)
    qpsk = [cmath.exp(1j * cmath.pi * (2 * q + 1) / 4) for q in range(4)]
    symbols = [rng.choice(qpsk) for _ in range(n)]
    previous_symbols = [rng.choice(qpsk) for _ in range(n)]

    def idft(values):
        return [sum(values[k] * cmath.exp(2j * cmath.pi * k * t / n) for k in range(n)) / n
                for t in range(n)]

    def dft(samples):
        return [sum(samples[t] * cmath.exp(-2j * cmath.pi * k * t / n) for t in range(n))
                for k in range(n)]

    body = idft(symbols)
    previous = idft(previous_symbols)

    def receive(delay, prefix_len):
        # 직접파 + delay 샘플 늦은 반사파(세기 0.5)
        channel = [1.0] + [0] * (delay - 1) + [0.5]
        tx = previous + body[n - prefix_len:] + body
        rx = [sum(channel[d] * tx[t - d] for d in range(len(channel)) if t - d >= 0)
              for t in range(len(tx))]
        window = rx[n + prefix_len:n + prefix_len + n]  # CP를 버리고 n 샘플만 DFT
        gains = dft(channel + [0] * (n - len(channel)))
        received = dft(window)
        return max(abs(received[k] / gains[k] - symbols[k]) for k in range(n))

    print(f"  부반송파 {n}개, 무작위 QPSK, 반사파 세기 0.5, 부반송파마다 나눗셈 1번으로 복원")
    for delay, prefix_len in ((3, cp_len), (3, 0), (cp_len, cp_len), (12, cp_len)):
        print(f"  반사파 지연 {delay:>2} 샘플, CP {prefix_len} 샘플 → 최대 오차"
              f" {receive(delay, prefix_len):.2e}")


def papr_demo():
    # 64점 IFFT 중 16 부반송파를 한 단말에 준다. OFDMA는 QPSK를 그대로 싣고,
    # SC-FDMA(DFT-spread OFDM)는 16점 DFT로 먼저 펼친 뒤 같은 자리에 싣는다
    n, m, trials = 64, 16, 400
    rng = random.Random(11)
    qpsk = [cmath.exp(1j * cmath.pi * (2 * q + 1) / 4) for q in range(4)]

    def transform(values, size, sign):
        return [sum(values[k] * cmath.exp(sign * 2j * cmath.pi * k * t / size) for k in range(size))
                for t in range(size)]

    def papr_db(samples):
        powers = [abs(x) ** 2 for x in samples]
        return 10 * math.log10(max(powers) / (sum(powers) / len(powers)))

    results = {"OFDMA": [], "SC-FDMA": []}
    for _ in range(trials):
        data = [rng.choice(qpsk) for _ in range(m)]
        for label, mapped in (("OFDMA", data), ("SC-FDMA", transform(data, m, -1))):
            grid = mapped + [0] * (n - m)
            results[label].append(papr_db(transform(grid, n, +1)))

    print(f"  64점 IFFT, 연속 부반송파 16개, QPSK, 심볼 {trials}개")
    for label, values in results.items():
        values.sort()
        print(f"  {label:<8} PAPR 평균 {sum(values) / trials:5.2f} dB"
              f"  상위 1% {values[int(trials * 0.99)]:5.2f} dB  최대 {values[-1]:5.2f} dB")


def main():
    print(f"Python {platform.python_version()}")
    print_section("FDMA - P-GSM 900 반송파 나누기 (TS 45.005 §2)")
    carriers = fdma_gsm900()
    print_section("TDMA - GSM 타임슬롯 (TS 45.002 §4.3)")
    tdma_gsm(carriers)
    print_section("CDMA - OVSF 채널화 코드 (TS 25.213 §4.3.1)")
    cdma_ovsf()
    print_section("OFDMA - LTE 수치 (TS 36.211 표 6.12-1, TS 36.300 §5.1.1)")
    ofdma_lte()
    print_section("OFDM - 순환 전치(CP)가 다중 경로를 흡수하는지")
    ofdm_cp_demo()
    print_section("상향 - OFDMA와 SC-FDMA의 PAPR (TS 36.300 §5.2.1)")
    papr_demo()


if __name__ == "__main__":
    main()
