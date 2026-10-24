"""보안관제 경보의 사후확률을 베이즈 정리로 계산하고, 모집단을 세어 검산한다.

분모가 전확률 공식이라는 점과, 사후확률이 다음 관측의 사전확률이 된다는 점을
숫자로 확인하는 것이 목적이다. 반올림 오차를 섞지 않으려고 Fraction 으로 센다.
"""

import sys
from fractions import Fraction


def posterior(prior, sensitivity, false_positive_rate):
    """경보가 울렸을 때 실제 침입일 확률 P(H|E).

    분모는 전확률 공식 P(E) = P(E|H)P(H) + P(E|~H)P(~H) 이다.
    """
    evidence = prior * sensitivity + (1 - prior) * false_positive_rate
    return prior * sensitivity / evidence


def posterior_by_counting(population, prior, sensitivity, false_positive_rate):
    """같은 값을 모집단을 세어 구한다. 공식을 믿지 않고 확인하는 쪽이다."""
    intrusions = population * prior
    normals = population - intrusions
    true_alerts = intrusions * sensitivity
    false_alerts = normals * false_positive_rate
    return true_alerts / (true_alerts + false_alerts)


def percent(value):
    return f"{float(value) * 100:.4f}%"


def main():
    print(f"Python {sys.version.split()[0]}")
    print()

    prior = Fraction(1, 1000)              # P(H)   침입 세션의 비율 0.1%
    sensitivity = Fraction(99, 100)        # P(E|H) 탐지율 99%
    false_positive_rate = Fraction(1, 100)  # P(E|~H) 오탐율 1%

    print("[입력]")
    print(f"  P(H)    사전확률(침입 비율) = {prior} = {percent(prior)}")
    print(f"  P(E|H)  가능도(탐지율)      = {sensitivity} = {percent(sensitivity)}")
    print(f"  P(E|~H) 오탐율              = {false_positive_rate} = {percent(false_positive_rate)}")
    print()

    evidence = prior * sensitivity + (1 - prior) * false_positive_rate
    print("[1차 경보]")
    print(f"  P(E)   전확률(경보가 울릴 확률) = {evidence} = {percent(evidence)}")

    first = posterior(prior, sensitivity, false_positive_rate)
    print(f"  P(H|E) 사후확률                 = {first} = {percent(first)}")
    print()

    counted = posterior_by_counting(
        Fraction(1_000_000), prior, sensitivity, false_positive_rate
    )
    print("[검산] 100만 세션을 직접 세어 같은 값이 나오는지 본다")
    print(f"  침입 {int(Fraction(1_000_000) * prior)}건 중 탐지 "
          f"{int(Fraction(1_000_000) * prior * sensitivity)}건")
    print(f"  정상 {int(Fraction(1_000_000) * (1 - prior))}건 중 오탐 "
          f"{int(Fraction(1_000_000) * (1 - prior) * false_positive_rate)}건")
    print(f"  세어서 구한 값 = {counted} = {percent(counted)}")
    print(f"  공식과 일치하는가: {counted == first}")
    print()

    second = posterior(first, sensitivity, false_positive_rate)
    print("[2차 경보] 1차 사후확률을 사전확률로 삼아 한 번 더 갱신한다")
    print(f"  P(H)   = {percent(first)}  ->  P(H|E) = {percent(second)}")

    third = posterior(second, sensitivity, false_positive_rate)
    print(f"  P(H)   = {percent(second)}  ->  P(H|E) = {percent(third)}")


if __name__ == "__main__":
    main()
