"""라플라스 메커니즘으로 ε의 뜻과 누적 손실을 직접 계산한다.

식은 NIST SP 800-226 부록 B.2(라플라스 메커니즘: 척도 Δ1/ε)와
2.2절(합성: 여러 분석의 ε을 더하면 누적 손실의 상한)을 그대로 옮겼다.
NIST는 직접 구현을 피하고 검증된 라이브러리를 쓰라고 권한다. 이 코드는
수치를 확인하려는 검산용이다.
"""
import math
import random

SEED = 20261003
TRUE_COUNT = 632     # 개수 질의의 참값. NIST SP 800-226 2.1.1절 예시의 숫자를 빌렸다
SENSITIVITY = 1      # 개수 질의: 한 사람을 넣거나 빼면 결과는 최대 1 바뀐다
EPSILONS = [0.1, 0.5, 1.0, 2.0, 10.0]
TRIALS = 20000


def laplace_pdf(x, center, scale):
    return math.exp(-abs(x - center) / scale) / (2 * scale)


def laplace_noise(rng, scale):
    # 지수분포 두 개의 차가 라플라스 분포를 따른다
    return rng.expovariate(1 / scale) - rng.expovariate(1 / scale)


def main():
    rng = random.Random(SEED)

    print("[1] ε별 잡음 척도 b = Δ/ε 와 95% 오차 폭 (P(|잡음| > t) = exp(-t/b) 에서 t = b·ln 20)")
    print("     ε |     b |  95% 오차 폭 | 실측 95% 안 비율")
    for eps in EPSILONS:
        scale = SENSITIVITY / eps
        bound = scale * math.log(20)
        inside = sum(abs(laplace_noise(rng, scale)) <= bound for _ in range(TRIALS)) / TRIALS
        print(f"  {eps:4.1f} | {scale:5.1f} | {bound:11.2f} | {inside:.4f}")
    print()

    print("[2] 이웃 데이터셋 D1(632명) · D2(633명)에서 같은 출력이 나올 확률밀도 비 (ε = 1)")
    scale = SENSITIVITY / 1.0
    print("  출력 o | p(o|D1)  | p(o|D2)  | 비 p1/p2 | e^ε")
    for out in [628.0, 632.0, 632.5, 633.0, 637.0]:
        p1 = laplace_pdf(out, TRUE_COUNT, scale)
        p2 = laplace_pdf(out, TRUE_COUNT + 1, scale)
        print(f"  {out:6.1f} | {p1:.6f} | {p2:.6f} | {p1 / p2:8.4f} | {math.e:.4f}")
    print()

    print("[3] 순차 합성 — 같은 데이터에 대한 분석의 ε을 더한 값이 누적 손실의 상한")
    print(f"  ε=0.1 분석 10회        → 총 ε = {sum([0.1] * 10):.1f}")
    print(f"  ε=1 공개를 한 번 더    → 총 ε = {1.0 + 1.0:.1f}")
    print(f"  사용자-일 단위 ε=1 × 365일 → 1년 총 ε = {1.0 * 365:.0f}")
    print()

    print("[4] 기여 상한 k — 한 사람이 최대 k건을 내면 민감도가 k배, 같은 ε에서 잡음도 k배")
    print("     k |  Δ |  b (ε=1) | 95% 오차 폭")
    for k in [1, 5, 20]:
        scale = k / 1.0
        print(f"  {k:4d} | {k:2d} | {scale:8.1f} | {scale * math.log(20):10.2f}")
    print()

    print("[5] 예산을 나눠 쓰면 — 총 ε=1을 개수 질의 m개에 똑같이 나눌 때 질의당 95% 오차 폭")
    for m in [1, 4, 10]:
        scale = SENSITIVITY / (1.0 / m)
        print(f"  m = {m:2d} → 질의당 ε = {1.0 / m:.2f}, b = {scale:4.1f}, 95% 오차 폭 = {scale * math.log(20):6.2f}")


if __name__ == "__main__":
    main()
