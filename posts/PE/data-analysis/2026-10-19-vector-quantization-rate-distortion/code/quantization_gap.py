"""양자화기의 왜곡을 율-왜곡 한계와 비교해 격차를 재어 본다.

표준정규분포(평균 0, 분산 1)를 원천으로 두고 네 가지를 계산한다.

  A. 로이드-맥스 고정률 스칼라 양자화기의 왜곡과 한계 대비 격차
  B. 균일 스칼라 양자화기 + 엔트로피 부호화의 격차
  C. 2차원에서 정사각 격자와 육각 격자의 정규화 2차 모멘트
  D. 상관된 두 성분을 KLT로 돌린 뒤 얻는 이득

모든 적분은 닫힌 형태나 격자 합으로 결정되므로 난수를 쓰지 않는다.
같은 입력이면 어디서 돌려도 같은 값이 나온다.
"""

import math
import platform

SQRT_2PI = math.sqrt(2.0 * math.pi)


def phi(x):
    """표준정규 밀도."""
    return math.exp(-0.5 * x * x) / SQRT_2PI


def big_phi(x):
    """표준정규 누적분포."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def cell_mass(a, b):
    """구간 [a, b] 의 확률."""
    return big_phi(b) - big_phi(a)


def cell_moments(a, b):
    """구간 [a, b] 의 확률·1차 모멘트·2차 모멘트를 닫힌 형태로 구한다.

      ∫ φ    = Φ(b) - Φ(a)
      ∫ x φ  = φ(a) - φ(b)
      ∫ x² φ = (Φ(b) - Φ(a)) + a·φ(a) - b·φ(b)

    수치적분이 필요 없고, 칸이 비어도 값이 무너지지 않는다.
    """
    mass = big_phi(b) - big_phi(a)
    first = phi(a) - phi(b)
    second = mass + a * phi(a) - b * phi(b)
    return mass, first, second


def cell_centroid(a, b):
    """구간 [a, b] 의 조건부 평균. 질량이 0이면 중점으로 둔다."""
    mass, first, _ = cell_moments(a, b)
    if mass <= 1e-300:
        return 0.5 * (a + b)
    return first / mass


# 꼬리를 자르는 지점. 표준정규에서 ±12σ 밖의 확률은 배정밀도 분해능 아래다.
TAIL = 12.0


def normal_quantile(p):
    """Φ⁻¹(p) 를 이분법으로 구한다. 단조함수라 수렴이 보장된다."""
    low, high = -TAIL, TAIL
    for _ in range(200):
        mid = 0.5 * (low + high)
        if big_phi(mid) < p:
            low = mid
        else:
            high = mid
    return 0.5 * (low + high)


def quantizer_distortion(bounds, centers):
    """E[(X - Q(X))²] 를 칸별 모멘트로 합산한다."""
    total = 0.0
    for i, center in enumerate(centers):
        mass, first, second = cell_moments(bounds[i], bounds[i + 1])
        total += second - 2.0 * center * first + center * center * mass
    return total


def lloyd_max(levels, iterations=2000):
    """로이드-맥스 반복으로 최적 고정률 스칼라 양자화기를 구한다.

    최적 조건 두 가지를 번갈아 적용한다.
      ① 최근접 이웃 조건 — 경계는 이웃한 두 대표값의 중점
      ② 중심 조건 — 대표값은 그 칸의 조건부 평균

    초기값은 등확률 분위수로 둔다. 균등 간격으로 두면 꼬리 쪽 칸의 질량이
    0 에 가까워져 대표값이 제자리를 잡지 못한다.
    """
    edges = [-TAIL]
    edges += [normal_quantile((i + 1) / levels) for i in range(levels - 1)]
    edges.append(TAIL)
    centers = [cell_centroid(edges[i], edges[i + 1]) for i in range(levels)]

    for _ in range(iterations):
        bounds = [-TAIL]
        bounds += [0.5 * (centers[i] + centers[i + 1]) for i in range(levels - 1)]
        bounds.append(TAIL)
        moved = [cell_centroid(bounds[i], bounds[i + 1]) for i in range(levels)]
        shift = max(abs(a - b) for a, b in zip(centers, moved))
        centers = moved
        if shift < 1e-14:
            break

    bounds = [-TAIL]
    bounds += [0.5 * (centers[i] + centers[i + 1]) for i in range(levels - 1)]
    bounds.append(TAIL)
    return quantizer_distortion(bounds, centers)


def uniform_entropy_coded(step):
    """폭 step 인 균일 양자화기의 왜곡과 출력 엔트로피를 구한다."""
    half = 0.5 * step
    k_max = int(TAIL / step) + 2
    distortion = 0.0
    entropy = 0.0
    for k in range(-k_max, k_max + 1):
        a, b = k * step - half, k * step + half
        mass, first, second = cell_moments(a, b)
        if mass <= 1e-18:
            continue
        center = first / mass
        distortion += second - 2.0 * center * first + center * center * mass
        entropy -= mass * math.log2(mass)
    return distortion, entropy


def rate_distortion(rate):
    """분산 1인 가우스 원천의 율-왜곡 함수. D(R) = 2^(-2R)."""
    return 2.0 ** (-2.0 * rate)


def to_db(ratio):
    return 10.0 * math.log10(ratio)


def section_a():
    print("[A] 로이드-맥스 고정률 스칼라 양자화기 (분산 1인 가우스 원천)")
    print(
        f"  {'levels':>7} | {'bits R':>6} | {'D(Lloyd)':>10} |"
        f" {'D(R) 한계':>10} | {'격차 dB':>8}"
    )
    print("  " + "-" * 56)
    for bits in range(1, 7):
        levels = 2 ** bits
        measured = lloyd_max(levels)
        bound = rate_distortion(bits)
        print(
            f"  {levels:>7} | {bits:>6} | {measured:>10.6f} |"
            f" {bound:>10.6f} | {to_db(measured / bound):>8.3f}"
        )
    closed_form = 1.0 - 2.0 / math.pi
    print(f"  2레벨 닫힌 형태 1 - 2/π = {closed_form:.6f}  (위 표 첫 줄과 대조)")
    print(f"  고해상도 이론값 10log10(√3·π/2) = {to_db(math.sqrt(3) * math.pi / 2):.3f} dB")
    print("  7비트 이상은 칸 모멘트의 자리수 소거로 배정밀도가 모자라 싣지 않는다.")
    print()


def section_b():
    print("[B] 균일 스칼라 양자화기 + 엔트로피 부호화")
    print(
        f"  {'step Δ':>7} | {'D':>10} | {'엔트로피 H':>10} |"
        f" {'D(H) 한계':>10} | {'격차 dB':>8}"
    )
    print("  " + "-" * 56)
    for step in (1.0, 0.5, 0.25, 0.125, 0.0625, 0.03125):
        distortion, entropy = uniform_entropy_coded(step)
        bound = rate_distortion(entropy)
        print(
            f"  {step:>7.5f} | {distortion:>10.6f} | {entropy:>10.4f} |"
            f" {bound:>10.6f} | {to_db(distortion / bound):>8.3f}"
        )
    print("  고해상도에서 격차가 1.53 dB 로 수렴한다 (Gray·Neuhoff 1998, p.2334).")
    print()


def hexagon_second_moment(samples=3000):
    """넓이 1인 정육각형의 정규화 2차 모멘트를 격자 합으로 구한다.

    2차원 정규화 2차 모멘트는 G = (1/2)·∫‖x‖²dx / A² 이다.
    """
    # 외접원 반지름 1인 정육각형. 변은 y = ±√3/2, 그리고 기울어진 네 변.
    root3 = math.sqrt(3.0)

    def inside(x, y):
        return abs(y) <= root3 / 2 + 1e-12 and abs(root3 * abs(x) + abs(y)) <= root3

    span = 1.0
    grid = 2 * samples
    cell = (2.0 * span) / grid
    area = 0.0
    moment = 0.0
    for i in range(grid):
        x = -span + (i + 0.5) * cell
        for j in range(grid):
            y = -span + (j + 0.5) * cell
            if inside(x, y):
                area += cell * cell
                moment += (x * x + y * y) * cell * cell
    return 0.5 * moment / (area * area), area


def section_c():
    print("[C] 2차원 격자 모양이 만드는 차이 — 정규화 2차 모멘트 G")
    square = 1.0 / 12.0
    hexagon_closed = 5.0 / (36.0 * math.sqrt(3.0))
    hexagon_numeric, area = hexagon_second_moment()
    print(f"  정사각 격자  G = 1/12            = {square:.7f}")
    print(f"  육각 격자    G = 5/(36√3)        = {hexagon_closed:.7f}")
    print(f"  육각 격자    격자 합으로 다시 계산 = {hexagon_numeric:.7f}")
    print(f"    (적분한 육각형 넓이 {area:.5f}, 닫힌 형태 {3 * math.sqrt(3) / 2:.5f})")
    print(f"  정사각 대비 육각의 이득 = {to_db(square / hexagon_closed):.4f} dB")
    print()


def section_d():
    print("[D] 상관된 두 성분 — KLT 로 돌리고 얻는 이득")
    print(f"  {'상관 ρ':>7} | {'고유값':>18} | {'왜곡 비':>9} | {'이득 dB':>8}")
    print("  " + "-" * 50)
    for rho in (0.0, 0.3, 0.5, 0.7, 0.9, 0.95):
        big, small = 1.0 + rho, 1.0 - rho
        ratio = math.sqrt(big * small)  # 기하평균 / 산술평균(=1)
        print(
            f"  {rho:>7.2f} | {big:>8.3f}, {small:>7.3f} |"
            f" {ratio:>9.5f} | {to_db(1.0 / ratio):>8.4f}"
        )
    print("  고유값의 기하평균이 작아진 만큼 같은 비트로 왜곡이 줄어든다.")
    print()


def section_e():
    print("[E] 곱 양자화 — 코드북 항목 수")
    dim, codes_per_sub = 128, 256
    print(f"  벡터 차원 D = {dim}, 부분공간마다 코드북 항목 k* = {codes_per_sub}")
    print(f"  {'분할 m':>7} | {'부분공간 차원':>12} | {'저장할 항목 수':>14} | {'코드 비트':>9}")
    print("  " + "-" * 52)
    for m in (1, 2, 4, 8, 16):
        entries = m * codes_per_sub
        bits = m * math.log2(codes_per_sub)
        print(f"  {m:>7} | {dim // m:>12} | {entries:>14,} | {bits:>9.0f}")
    print("  같은 코드 비트를 통짜 벡터 양자화로 내려면 코드북 항목이")
    print(f"  2^{int(16 * math.log2(codes_per_sub))} 개 필요하다 — 학습도 저장도 불가능하다.")
    print()


def main():
    print(f"[환경] 파이썬 {platform.python_version()} / {platform.system()} {platform.release()}")
    print()
    section_a()
    section_b()
    section_c()
    section_d()
    section_e()


if __name__ == "__main__":
    main()
