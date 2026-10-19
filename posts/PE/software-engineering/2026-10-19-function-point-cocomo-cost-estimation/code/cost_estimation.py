"""기능점수 방식과 COCOMO가 규모를 어떻게 돈·노력으로 바꾸는지 직접 계산한다.

둘 다 '규모 → 비용'을 잇는 식이지만 규모를 재는 자가 다르고, 규모가 커질 때
단위당 값이 움직이는 방향도 다르다. 그 차이를 수치로 확인한다.

근거
  - 기능점수 가중치·단가·보정계수 : 소프트웨어사업 대가산정 가이드 2024년 개정판
    (한국소프트웨어산업협회) 표 3-8, 3-12, 3-13, 3-18, 3-20, 3-21
  - COCOMO 81 계수 : B. Boehm, Software Engineering Economics, Prentice-Hall, 1981
"""

from __future__ import annotations

import math

RULE = "=" * 70

FP_UNIT_PRICE = 605_784  # 기능점수당 단가(원) — 2024년 개정판 표 3-21

# 간이법 평균복잡도 가중치 (표 3-8, 3-13)
SIMPLE_WEIGHT = {"ILF": 7.5, "EIF": 5.4, "EI": 4.0, "EO": 5.2, "EQ": 3.9}

# 정통법 복잡도별 가중치 (표 3-12, 3-18) — 낮음 / 보통 / 높음
FULL_WEIGHT = {
    "ILF": (7, 10, 15),
    "EIF": (5, 7, 10),
    "EI": (3, 4, 6),
    "EO": (4, 5, 7),
    "EQ": (3, 4, 6),
}

# 예시로 세운 가상 시스템의 기능 개수. (낮음, 보통, 높음)
SYSTEM = {
    "ILF": (4, 6, 2),
    "EIF": (3, 1, 0),
    "EI": (14, 9, 3),
    "EO": (5, 4, 1),
    "EQ": (10, 6, 0),
}

# COCOMO 81 기본형 계수 — a, b(노력), c, d(기간)
COCOMO81 = {
    "organic": (2.4, 1.05, 2.5, 0.38),
    "semi-detached": (3.0, 1.12, 2.5, 0.35),
    "embedded": (3.6, 1.20, 2.5, 0.32),
}


def simple_fp() -> float:
    """간이법 — 복잡도를 가리지 않고 평균 가중치 하나로 센다."""
    return sum(sum(counts) * SIMPLE_WEIGHT[kind] for kind, counts in SYSTEM.items())


def full_fp() -> float:
    """정통법 — 기능마다 DET·RET(또는 FTR)로 복잡도를 가려 가중치를 매긴다."""
    return sum(
        sum(n * w for n, w in zip(counts, FULL_WEIGHT[kind]))
        for kind, counts in SYSTEM.items()
    )


def size_factor(fp: float) -> float:
    """규모 보정계수. 500FP 미만은 1.28로 고정한다 (가이드 각주)."""
    if fp < 500:
        return 1.28
    return 0.4057 * (math.log(fp) - 7.1978) ** 2 + 0.8878


def show_fp_sizing() -> None:
    simple, full = simple_fp(), full_fp()
    print(f"  간이법 총 기능점수  {simple:8.1f} FP")
    print(f"  정통법 총 기능점수  {full:8.1f} FP")
    print(f"  차이                {full - simple:+8.1f} FP  ({(full / simple - 1) * 100:+.1f}%)")
    print()
    print("  기능유형별 대조 (간이법 / 정통법)")
    for kind, counts in SYSTEM.items():
        s = sum(counts) * SIMPLE_WEIGHT[kind]
        f = sum(n * w for n, w in zip(counts, FULL_WEIGHT[kind]))
        print(f"    {kind:4s} 개수 {sum(counts):3d}개 → {s:7.1f} / {f:7.1f}")
    print()


def show_size_factor_curve() -> None:
    """규모 보정계수가 단조 증가인지 확인한다."""
    print("  기능점수   규모보정계수   FP당 보정후 원가(원)")
    for fp in (100, 300, 500, 800, 1_336, 2_000, 5_000, 10_000, 20_000):
        factor = size_factor(fp)
        print(f"  {fp:8,d}   {factor:12.4f}   {FP_UNIT_PRICE * factor:16,.0f}")
    print()

    bottom = math.exp(7.1978)
    print(f"  식의 최소점   FP = e^7.1978 = {bottom:,.1f} FP, 이때 계수 {size_factor(bottom):.4f}")
    print(f"  500FP 에서의 계수 {size_factor(500.0000001):.4f} — 가이드가 하한으로 못박은 1.28 과 같은 값")
    print()


def show_cocomo() -> None:
    print("  KLOC    모드            노력(PM)    기간(개월)   평균 인원   KLOC당 노력")
    for kloc in (10, 50, 100, 400):
        for mode, (a, b, c, d) in COCOMO81.items():
            effort = a * kloc**b
            duration = c * effort**d
            print(
                f"  {kloc:5d}   {mode:14s}  {effort:9.1f}   {duration:9.1f}   "
                f"{effort / duration:9.1f}   {effort / kloc:11.2f}"
            )
        print()


def main() -> None:
    print(RULE)
    print("1. 같은 시스템을 간이법과 정통법으로 센다")
    print(RULE)
    show_fp_sizing()

    print(RULE)
    print("2. 규모 보정계수 — 커질수록 단가가 내려가기만 하는가")
    print(RULE)
    show_size_factor_curve()

    print(RULE)
    print("3. COCOMO 81 기본형 — 규모가 커질 때 KLOC당 노력")
    print(RULE)
    show_cocomo()


if __name__ == "__main__":
    main()
