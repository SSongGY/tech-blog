"""4비트 S-box 의 차분 분포표(DDT)와 선형 근사표(LAT)를 계산한다.

S-box 는 Heys 튜토리얼 Table 1 의 것(DES 첫 S-box 의 첫 행)이다.
튜토리얼이 적은 값(DDT 최댓값 8 이 ΔX=B, ΔY=2 에서 나온다, 3라운드 특성 확률
27/1024, 선형 근사 편향 -1/32)을 직접 다시 계산해 맞는지 본다.
비교용으로 선형(아핀) S-box 를 하나 두어, 비선형성이 없으면 표가 어떻게 되는지 보인다.
"""

from fractions import Fraction

HEYS_SBOX = [0xE, 0x4, 0xD, 0x1, 0x2, 0xF, 0xB, 0x8,
             0x3, 0xA, 0x6, 0xC, 0x5, 0x9, 0x0, 0x7]

# 출력 = 입력 XOR 상수. 차분이 그대로 통과하므로 최악의 S-box 다.
AFFINE_SBOX = [x ^ 0x5 for x in range(16)]


def parity(value):
    return bin(value).count("1") & 1


def difference_distribution_table(sbox):
    table = [[0] * 16 for _ in range(16)]
    for delta_in in range(16):
        for x in range(16):
            delta_out = sbox[x] ^ sbox[x ^ delta_in]
            table[delta_in][delta_out] += 1
    return table


def linear_approximation_table(sbox):
    # 칸 값 = (입력 마스크·x == 출력 마스크·S(x) 인 x 의 개수) - 8. 16으로 나누면 편향이다.
    table = [[0] * 16 for _ in range(16)]
    for in_mask in range(16):
        for out_mask in range(16):
            matches = sum(
                1 for x in range(16)
                if parity(x & in_mask) == parity(sbox[x] & out_mask)
            )
            table[in_mask][out_mask] = matches - 8
    return table


def print_table(title, table, row_label, col_label):
    print(f"[{title}]  행={row_label}, 열={col_label}")
    print("    " + " ".join(f"{c:>3X}" for c in range(16)))
    for r, row in enumerate(table):
        print(f"{r:>2X} |" + " ".join(f"{v:>3d}" for v in row))
    print()


def summarize(name, sbox):
    ddt = difference_distribution_table(sbox)
    lat = linear_approximation_table(sbox)
    # (0,0) 칸은 자명하므로 뺀다
    ddt_max = max(ddt[i][j] for i in range(1, 16) for j in range(16))
    lat_max = max(abs(lat[i][j]) for i in range(16) for j in range(1, 16))
    ddt_cells = [(i, j) for i in range(1, 16) for j in range(16) if ddt[i][j] == ddt_max]
    zero_cells = sum(1 for i in range(1, 16) for j in range(16) if ddt[i][j] == 0)
    print(f"== {name} ==")
    print(f"차분 균일도(DDT 최댓값)     : {ddt_max} / 16  → 최대 차분 확률 {Fraction(ddt_max, 16)}")
    print(f"최댓값이 나온 칸 (ΔX,ΔY)    : {', '.join(f'({i:X},{j:X})' for i, j in ddt_cells)}")
    print(f"ΔX≠0 인 행의 0 칸 수        : {zero_cells} / 240")
    print(f"LAT 절댓값 최대             : {lat_max} / 16  → 최대 |편향| {Fraction(lat_max, 16)}")
    print()
    return ddt, lat


def piling_up(biases):
    """Matsui 의 적층 보조정리: n 개 독립 근사의 XOR 편향 = 2^(n-1) × Π ε_i."""
    result = Fraction(2) ** (len(biases) - 1)
    for bias in biases:
        result *= bias
    return result


def main():
    ddt, lat = summarize("Heys S-box (DES S1 첫 행)", HEYS_SBOX)
    summarize("아핀 S-box (x XOR 5)", AFFINE_SBOX)

    print_table("Heys S-box 차분 분포표 DDT", ddt, "ΔX", "ΔY")
    print_table("Heys S-box 선형 근사표 LAT (일치 수 - 8)", lat, "입력 마스크", "출력 마스크")

    # Heys §3.4 의 경로: 네 개의 S-box 근사 (S12, S22, S32, S34)
    path = [(0xB, 0x4), (0x4, 0x5), (0x4, 0x5), (0x4, 0x5)]
    biases = [Fraction(lat[a][b], 16) for a, b in path]
    total_bias = piling_up(biases)
    print("[선형 경로] 활성 S-box 4개 — (입력 마스크, 출력 마스크) → 편향")
    for (a, b), e in zip(path, biases):
        print(f"  ({a:X},{b:X}) → {e}")
    print(f"  적층 보조정리 2^(4-1) × Π ε = {total_bias}")
    print(f"  필요한 기지 평문 N_L ≈ 1/ε² = {1 / total_bias ** 2}")
    print()

    # Heys §4.3 의 차분 특성: 활성 S-box 4개
    char = [(0xB, 0x2), (0x4, 0x6), (0x2, 0x5), (0x2, 0x5)]
    probs = [Fraction(ddt[a][b], 16) for a, b in char]
    p_d = Fraction(1)
    for p in probs:
        p_d *= p
    print("[차분 특성] 활성 S-box 4개 — (ΔX, ΔY) → 확률")
    for (a, b), p in zip(char, probs):
        print(f"  ({a:X},{b:X}) → {p}")
    print(f"  특성 확률 p_D = Π β = {p_d}  (= {float(p_d):.5f})")
    print(f"  필요한 선택 평문 쌍 N_D ≈ c/p_D = c × {float(1 / p_d):.1f}")


if __name__ == "__main__":
    main()
