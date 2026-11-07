"""암달의 법칙과 구스타프슨의 법칙을 직접 계산해 원 논문의 수치와 맞춘다.

1) 암달 1967: 순차 비율 40% 와 그것을 1/2, 1/3 로 줄였을 때의 상한 1/s
2) 구스타프슨 1988 그림 1: N = 1024 에서 s 에 따른 암달 속도 향상
3) 같은 s 로 두 법칙을 나란히 — 문제 크기 고정 vs 실행 시간 고정
4) 샌디아 1024 프로세서 사례: s' = 0.4~0.8% 일 때 두 식이 주는 값
5) 두 법칙의 s 는 서로 다른 기준이다 — s' 를 직렬 기준 s 로 바꾸면 같은 값이 나온다
"""
from fractions import Fraction


def amdahl(s, n):
    """문제 크기 고정. s = 직렬 프로세서 기준 순차 시간 비율."""
    return 1 / (s + (1 - s) / n)


def gustafson(s_prime, n):
    """실행 시간 고정. s' = 병렬 시스템 기준 순차 시간 비율."""
    return s_prime + (1 - s_prime) * n


def section_amdahl_1967():
    print("== 1) 암달 1967 — 순차 비율 s 의 상한 1/s ==")
    print("  상황                    | s       | 상한 1/s")
    for label, s in [("논문 관찰값 40%", Fraction(40, 100)),
                     ("절반으로 줄이면", Fraction(20, 100)),
                     ("1/3 로 줄이면", Fraction(40, 300))]:
        print(f"  {label:<14} | {float(s):>7.4f} | {float(1 / s):>6.2f}")
    print()


def section_figure1():
    print("== 2) N = 1024 에서 암달 속도 향상 (구스타프슨 그림 1 과 대조) ==")
    print("  s      | 속도 향상 | 효율 S/N")
    for s in (0.0, 0.0025, 0.005, 0.01, 0.015, 0.02, 0.03, 0.04):
        speedup = amdahl(s, 1024)
        print(f"  {s:>6.2%} | {speedup:>9.1f} | {speedup / 1024:>8.3f}")
    print()


def section_side_by_side():
    print("== 3) 같은 s = 5% 로 두 법칙을 나란히 ==")
    s = 0.05
    print("  N      | 암달(크기 고정) | 구스타프슨(시간 고정)")
    for n in (1, 4, 16, 64, 256, 1024, 10 ** 6):
        print(f"  {n:>6,} | {amdahl(s, n):>15.2f} | {gustafson(s, n):>21.2f}")
    print(f"  N → ∞ 에서 암달의 극한 1/s = {1 / s:.0f}")
    print()


def section_sandia():
    print("== 4) 샌디아 1024 프로세서 — 논문 측정값 1016~1021 ==")
    n = 1024
    print("  s'     | 구스타프슨 N+(1-N)s' | 같은 숫자를 암달 s 로 넣으면")
    for s_prime in (0.004, 0.006, 0.008):
        print(f"  {s_prime:>6.1%} | {gustafson(s_prime, n):>20.1f} |"
              f" {amdahl(s_prime, n):>26.1f}")
    print()


def section_equivalence():
    print("== 5) s' 를 직렬 기준 s 로 바꾸면 ==")
    n = 1024
    print("  s'     | s = s'/(s'+p'N) | 암달(s)  | 구스타프슨(s')")
    for s_prime in (Fraction(4, 1000), Fraction(8, 1000), Fraction(5, 100)):
        p_prime = 1 - s_prime
        s = s_prime / (s_prime + p_prime * n)
        a = 1 / (s + (1 - s) / n)
        g = s_prime + p_prime * n
        print(f"  {float(s_prime):>6.1%} | {float(s):>15.7f} | {float(a):>8.2f} |"
              f" {float(g):>14.2f} | 같은가 {a == g}")
    print()


def main():
    section_amdahl_1967()
    section_figure1()
    section_side_by_side()
    section_sandia()
    section_equivalence()


if __name__ == "__main__":
    main()
