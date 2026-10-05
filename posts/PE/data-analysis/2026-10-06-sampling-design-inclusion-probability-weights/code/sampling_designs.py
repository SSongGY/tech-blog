"""모집단 12개, 표본 4개로 다섯 가지 표본설계를 전수 열거해 비교한다.

가능한 표본을 전부 나열하고 각 표본이 뽑힐 확률을 곱해 기댓값과 분산을 낸다.
난수를 쓰지 않으므로 몇 번을 돌려도 같은 값이 나온다 — 근사가 아니라 정확한 값이다.
"""
import math
import platform
import sys
from fractions import Fraction
from itertools import combinations

# 단위 이름, 값, 층. 층 B 는 수는 적고 값은 크다 — 학습데이터의 희소 클래스와 같은 모양
POPULATION = [
    ("a1", 2, "A"), ("a2", 3, "A"), ("a3", 3, "A"), ("a4", 4, "A"), ("a5", 4, "A"),
    ("a6", 5, "A"), ("a7", 5, "A"), ("a8", 6, "A"), ("a9", 6, "A"),
    ("b1", 20, "B"), ("b2", 24, "B"), ("b3", 28, "B"),
]
SAMPLE_SIZE = 4

# 집락: 값이 비슷한 이웃끼리 묶었다. 같은 환자·같은 사용자에서 나온 기록이 비슷한 것과 같다
CLUSTERS = [("a1", "a2"), ("a3", "a4"), ("a5", "a6"), ("a7", "a8"), ("a9", "b1"), ("b2", "b3")]

VALUE = {name: value for name, value, _ in POPULATION}
STRATUM = {name: stratum for name, _, stratum in POPULATION}
N = len(POPULATION)
TRUE_MEAN = Fraction(sum(VALUE.values()), N)


def summarize(label, outcomes):
    """outcomes: (확률, 추정값) 목록. 기댓값·편향·표준편차를 찍는다."""
    total_prob = sum(p for p, _ in outcomes)
    assert total_prob == 1, f"{label}: 확률 합이 1이 아니다 ({total_prob})"
    expected = sum(p * est for p, est in outcomes)
    variance = sum(p * (est - expected) ** 2 for p, est in outcomes)
    bias = expected - TRUE_MEAN
    print(f"{label:<34} {len(outcomes):>5} {float(expected):>8.3f} "
          f"{float(bias):>+8.3f} {math.sqrt(variance):>7.3f}")


def inclusion_probabilities(outcomes_with_units):
    """각 단위가 표본에 들어갈 확률 π_i = 그 단위를 포함한 표본 확률의 합."""
    pi = {name: Fraction(0) for name in VALUE}
    for prob, units in outcomes_with_units:
        for name in units:
            pi[name] += prob
    return pi


def srs():
    samples = list(combinations(VALUE, SAMPLE_SIZE))
    p = Fraction(1, len(samples))
    return [(p, s) for s in samples]


def stratified(n_a, n_b):
    a_units = [n for n in VALUE if STRATUM[n] == "A"]
    b_units = [n for n in VALUE if STRATUM[n] == "B"]
    samples = [sa + sb for sa in combinations(a_units, n_a) for sb in combinations(b_units, n_b)]
    p = Fraction(1, len(samples))
    return [(p, s) for s in samples]


def cluster(n_clusters):
    samples = [sum(c, ()) for c in combinations(CLUSTERS, n_clusters)]
    p = Fraction(1, len(samples))
    return [(p, s) for s in samples]


def mean_unweighted(units):
    return Fraction(sum(VALUE[u] for u in units), len(units))


def mean_weighted(units, pi):
    # 호비츠-톰슨: 각 값에 가중치 1/π 를 곱해 총계를 추정하고 N 으로 나눈다
    return sum(Fraction(VALUE[u]) / pi[u] for u in units) / N


def main():
    print(f"Python {platform.python_version()} ({sys.platform})")
    print()
    print("[모집단]")
    for stratum in ("A", "B"):
        values = [VALUE[n] for n in VALUE if STRATUM[n] == stratum]
        print(f"  층 {stratum}: {len(values)}개  값 {values}  합 {sum(values)}")
    print(f"  N = {N}, 참 평균 = {sum(VALUE.values())}/{N} = {float(TRUE_MEAN):.3f}")
    print(f"  집락(값이 비슷한 이웃 2개씩): {CLUSTERS}")
    print()

    designs = {
        "단순무작위 n=4": srs(),
        "층화 비례배분 A3+B1": stratified(3, 1),
        "층화 불균등배분 A2+B2": stratified(2, 2),
        "집락 2개(4단위)": cluster(2),
    }

    print("[포함확률 π] 설계가 정한다. 합은 언제나 표본 크기 n 이다")
    for label, outcomes in designs.items():
        pi = inclusion_probabilities(outcomes)
        a_pi, b_pi = pi["a1"], pi["b1"]
        print(f"  {label:<24} π(a1)={str(a_pi):<5} π(b1)={str(b_pi):<5} "
              f"가중치 1/π: {str(1 / a_pi):<4} / {str(1 / b_pi):<4} Σπ={sum(pi.values())}")
    print()

    print(f"{'설계 · 추정량':<34} {'표본수':>5} {'기댓값':>8} {'편향':>8} {'표준편차':>7}")
    for label, outcomes in designs.items():
        pi = inclusion_probabilities(outcomes)
        if label.startswith("층화 불균등"):
            summarize(label + " · 가중치 무시", [(p, mean_unweighted(s)) for p, s in outcomes])
            summarize(label + " · 가중(1/π)", [(p, mean_weighted(s, pi)) for p, s in outcomes])
        else:
            summarize(label, [(p, mean_unweighted(s)) for p, s in outcomes])

    # 할당추출: 층별 개수는 비례배분과 같지만, 층 안에서 '연락이 잘 닿는' 앞쪽 단위만 고른다
    quota_units = ("a1", "a2", "a3", "b1")
    summarize("할당 A3+B1 (닿기 쉬운 단위)", [(Fraction(1), mean_unweighted(quota_units))])
    print()
    print("할당추출의 포함확률: a1·a2·a3·b1 은 1, 나머지 8개는 0 → 가중치를 정의할 수 없다")


if __name__ == "__main__":
    main()
