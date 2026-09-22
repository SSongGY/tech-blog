"""잭나이프(delete-1) 재표집을 유리수로 계산해 답안의 수식을 검산한다.

부동소수점으로 돌리면 "보정값이 불편분산과 정확히 같다"를 말할 수 없어
Fraction 으로 계산한다. 근사가 아니라 항등이라는 점이 이 예제의 요지다.
"""

from fractions import Fraction
from statistics import median


def leave_one_out(sample):
    return [sample[:i] + sample[i + 1:] for i in range(len(sample))]


def plugin_variance(sample):
    """1/n 로 나누는 표본분산. 모분산을 -sigma^2/n 만큼 낮게 추정한다."""
    n = len(sample)
    mean = sum(sample) / n
    return sum((x - mean) ** 2 for x in sample) / n


def unbiased_variance(sample):
    n = len(sample)
    mean = sum(sample) / n
    return sum((x - mean) ** 2 for x in sample) / (n - 1)


def jackknife(sample, statistic):
    n = len(sample)
    replicates = [statistic(s) for s in leave_one_out(sample)]
    mean_rep = sum(replicates) / n
    estimate = statistic(sample)
    bias = (n - 1) * (mean_rep - estimate)
    variance = Fraction(n - 1, n) * sum((r - mean_rep) ** 2 for r in replicates)
    return {
        "replicates": replicates,
        "mean_rep": mean_rep,
        "estimate": estimate,
        "bias": bias,
        "corrected": estimate - bias,
        "variance": variance,
    }


def show(label, value):
    print(f"  {label:<22} {value}  = {float(value):.6f}")


sample = [Fraction(v) for v in (2, 4, 4, 5, 10)]
n = len(sample)
print(f"표본 x = {[int(v) for v in sample]}  (n={n})\n")

print("[1] 편향 감소 — 추정량은 1/n 로 나눈 표본분산")
jack = jackknife(sample, plugin_variance)
print("  잭나이프 복제값        " + ", ".join(str(r) for r in jack["replicates"]))
show("복제값 평균", jack["mean_rep"])
show("원 추정값", jack["estimate"])
show("편향 추정", jack["bias"])
show("보정 추정값", jack["corrected"])
show("불편분산 S^2", unbiased_variance(sample))
print(f"  보정값 == S^2 ?        {jack['corrected'] == unbiased_variance(sample)}")
# 이론상 편향 추정은 -S^2/n 으로 정리된다. 항등인지 본다.
show("-S^2/n", -unbiased_variance(sample) / n)
print(f"  편향 == -S^2/n ?       {jack['bias'] == -unbiased_variance(sample) / n}\n")

print("[2] 분산 추정 — 추정량은 표본평균")
jack_mean = jackknife(sample, lambda s: sum(s) / len(s))
show("잭나이프 분산", jack_mean["variance"])
show("S^2/n", unbiased_variance(sample) / n)
print(f"  두 값이 같은가 ?       {jack_mean['variance'] == unbiased_variance(sample) / n}")
print(f"  잭나이프 표준오차      {float(jack_mean['variance']) ** 0.5:.6f}\n")

print("[3] 한계 — 추정량이 중앙값이면")
jack_med = jackknife(sample, median)
print("  잭나이프 복제값        " + ", ".join(str(r) for r in jack_med["replicates"]))
print(f"  서로 다른 값의 개수    {len(set(jack_med['replicates']))}")
show("잭나이프 분산", jack_med["variance"])
