"""k0 와 k1 척도로 만든 t-digest 의 분위수 오차를 정확한 분위수와 비교한다."""

import bisect
import math
import random
import sys

from tdigest import TDigest

SEED = 20261122
SAMPLE_COUNT = 1_000_000
DELTA = 100
QUANTILES = (0.001, 0.01, 0.1, 0.5, 0.9, 0.99, 0.999)


def make_samples():
    rng = random.Random(SEED)
    # 응답 시간처럼 오른쪽 꼬리가 긴 분포
    return [rng.lognormvariate(3.0, 1.0) for _ in range(SAMPLE_COUNT)]


def rank_error(sorted_values, estimate, q):
    """추정값의 실제 순위(0~1)와 목표 q 의 차이."""
    actual_q = bisect.bisect_left(sorted_values, estimate) / len(sorted_values)
    return actual_q - q


def build(samples, scale):
    digest = TDigest(DELTA, scale)
    for value in samples:
        digest.add(value)
    digest.count()
    return digest


def report_errors(label, digest, sorted_values):
    print(f"\n[{label}] 클러스터 {len(digest.centroids)}개 (⌈δ⌉ = {math.ceil(DELTA)})")
    print(f"{'q':>6} {'정확값':>10} {'추정값':>10} {'순위 오차':>10} "
          f"{'오차/min(q,1-q)':>16}")
    for q in QUANTILES:
        exact = sorted_values[min(len(sorted_values) - 1, int(q * len(sorted_values)))]
        estimate = digest.quantile(q)
        error = rank_error(sorted_values, estimate, q)
        print(f"{q:>6} {exact:>10.3f} {estimate:>10.3f} {error:>+10.6f} "
              f"{abs(error) / min(q, 1 - q):>16.4f}")


def report_cluster_sizes(label, digest):
    counts = [c[1] for c in digest.centroids]
    mid = len(counts) // 2
    print(f"  {label} 클러스터 크기: 앞 5개 {counts[:5]}  가운데 {counts[mid]}"
          f"  뒤 5개 {counts[-5:]}")


def main():
    print(f"Python {sys.version.split()[0]} · 표본 {SAMPLE_COUNT:,}개 · δ = {DELTA}"
          f" · 로그정규(μ=3, σ=1) · 시드 {SEED}")
    samples = make_samples()
    sorted_values = sorted(samples)

    digests = {}
    for scale in ("k0", "k1"):
        digests[scale] = build(samples, scale)
        report_errors(f"척도 {scale}", digests[scale], sorted_values)

    print("\n[클러스터 크기]")
    for scale in ("k0", "k1"):
        report_cluster_sizes(scale, digests[scale])

    print("\n[나눠 만든 다이제스트 병합 — k1, 10조각]")
    parts = [build(samples[i::10], "k1") for i in range(10)]
    combined = parts[0]
    for part in parts[1:]:
        combined.merge_digest(part)
    report_errors("10조각 병합", combined, sorted_values)

    print("\n[정렬된 순서로 넣기 — k1]")
    report_errors("오름차순 입력", build(sorted_values, "k1"), sorted_values)


if __name__ == "__main__":
    main()
