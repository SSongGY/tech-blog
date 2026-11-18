"""Jump 일관 해시(Lamping·Veach 2014)를 파이썬으로 옮겨 링 해시와 비교한다.

1) 한 키의 버킷이 버킷 수에 따라 어떻게 "점프"하는가
2) 버킷 10 → 11, 10 → 12 로 늘릴 때 옮겨 가는 키 비율과 행선지
3) 버킷 100 개에 키를 나눴을 때 버킷별 편차 — 링(가상 노드 k 개)과 비교
4) 버킷 하나를 더할 때 기존 버킷 중 몇 개가 키를 내주는가
5) 버킷 수를 줄이면 어느 버킷의 키가 움직이는가 — 가운데 버킷은 뺄 수 없다
6) 반복 횟수와 ln(n)+1, 그리고 한 번 계산하는 시간·메모리
"""
import bisect
import hashlib
import math
import platform
import random
import statistics
import time
import tracemalloc

MASK_64 = (1 << 64) - 1
LCG_MULTIPLIER = 2862933555777941757  # 논문 Figure 1 의 상수 (L'Ecuyer 표)
KEY_COUNT = 1_000_000
SEED = 20261117


def jump_hash(key, num_buckets):
    """논문 Figure 1 을 그대로 옮겼다. C 의 uint64 넘침을 MASK_64 로 흉내 낸다."""
    bucket, next_bucket = -1, 0
    while next_bucket < num_buckets:
        bucket = next_bucket
        key = (key * LCG_MULTIPLIER + 1) & MASK_64
        next_bucket = int((bucket + 1) * (float(1 << 31) / float((key >> 33) + 1)))
    return bucket


def jump_iterations(key, num_buckets):
    bucket, next_bucket, iterations = -1, 0, 0
    while next_bucket < num_buckets:
        iterations += 1
        bucket = next_bucket
        key = (key * LCG_MULTIPLIER + 1) & MASK_64
        next_bucket = int((bucket + 1) * (float(1 << 31) / float((key >> 33) + 1)))
    return iterations


def point_of(bucket, replica):
    digest = hashlib.blake2b(f"{bucket}-{replica}".encode(), digest_size=8).digest()
    return int.from_bytes(digest, "big")


class HashRing:
    """Karger 방식: 버킷마다 원 위에 점 k 개, 키에서 시계 방향 첫 점의 버킷."""

    def __init__(self, num_buckets, points_per_bucket):
        pairs = sorted(
            (point_of(b, r), b)
            for b in range(num_buckets)
            for r in range(points_per_bucket)
        )
        self.points = [p for p, _ in pairs]
        self.owners = [b for _, b in pairs]

    def lookup(self, key):
        index = bisect.bisect_left(self.points, key)
        return self.owners[index % len(self.points)]

    def key_space_share(self, num_buckets):
        """키 공간(원 둘레) 중 각 버킷이 차지하는 몫. 표본 없이 정확히 계산한다."""
        share = [0] * num_buckets
        previous = self.points[-1] - (1 << 64)
        for point, owner in zip(self.points, self.owners):
            share[owner] += point - previous
            previous = point
        return [s / (1 << 64) for s in share]


def relative_std(values):
    return statistics.pstdev(values) / statistics.fmean(values)


def main():
    print(f"Python {platform.python_version()} / {platform.system()} {platform.release()}")
    rng = random.Random(SEED)
    keys = [rng.getrandbits(64) for _ in range(KEY_COUNT)]
    print(f"키 {KEY_COUNT:,}개 (64비트 난수, 시드 {SEED})")

    print("\n[1] 버킷 수 1~14 에서 세 키의 버킷")
    print("    n : " + " ".join(f"{n:>2}" for n in range(1, 15)))
    for number, key in enumerate(keys[:3], start=1):
        row = " ".join(f"{jump_hash(key, n):>2}" for n in range(1, 15))
        print(f"    key{number}: {row}")

    print("\n[2] 버킷을 늘릴 때 옮겨 가는 키")
    before = [jump_hash(k, 10) for k in keys]
    for grown in (11, 12):
        after = [jump_hash(k, grown) for k in keys]
        moved = [(a, b) for a, b in zip(before, after) if a != b]
        targets = sorted({b for _, b in moved})
        ideal = 1 - 10 / grown
        print(f"    10 -> {grown}: 옮긴 키 {len(moved) / KEY_COUNT:.4%}"
              f" (이론 {ideal:.4%}), 행선지 버킷 {targets}")
    mod_moved = sum(1 for k in keys if k % 10 != k % 12)
    print(f"    비교 — key mod 10 -> mod 12: 옮긴 키 {mod_moved / KEY_COUNT:.4%}")

    print("\n[3] 버킷 100개 — 버킷 크기의 상대 표준편차(σ/μ)")
    buckets = 100
    counts = [0] * buckets
    for k in keys:
        counts[jump_hash(k, buckets)] += 1
    print(f"    jump  키 개수 기준       : {relative_std(counts):.4f}"
          f"  (최소 {min(counts):,} · 최대 {max(counts):,})")
    print(f"    참고: 키 {KEY_COUNT:,}개를 완전히 고르게 뿌려도 표본 오차만 약 "
          f"{math.sqrt((buckets - 1) / KEY_COUNT):.4f}")
    for points in (1, 10, 100, 1000):
        ring = HashRing(buckets, points)
        share = ring.key_space_share(buckets)
        ring_counts = [0] * buckets
        for k in keys:
            ring_counts[ring.lookup(k)] += 1
        print(f"    ring  k={points:<4} 키 공간 몫  : {relative_std(share):.4f}"
              f"  · 키 개수 기준 {relative_std(ring_counts):.4f}"
              f"  (최소 {min(ring_counts):,} · 최대 {max(ring_counts):,})")

    print("\n[4] 버킷 100 -> 101: 키를 내준 기존 버킷 수와 내준 비율")
    jump_before = [jump_hash(k, 100) for k in keys]
    jump_after = [jump_hash(k, 101) for k in keys]
    report_donors("jump", jump_before, jump_after)
    for points in (10, 100):
        ring_before = HashRing(100, points)
        ring_after = HashRing(101, points)
        report_donors(f"ring k={points}",
                      [ring_before.lookup(k) for k in keys],
                      [ring_after.lookup(k) for k in keys])

    print("\n[5] 버킷 10 -> 9: 어느 버킷의 키가 움직이는가")
    before = [jump_hash(k, 10) for k in keys]
    after = [jump_hash(k, 9) for k in keys]
    sources = sorted({a for a, b in zip(before, after) if a != b})
    stay_3 = sum(1 for a, b in zip(before, after) if a == 3 and b == 3)
    total_3 = before.count(3)
    print(f"    움직인 키의 원래 버킷: {sources}")
    print(f"    버킷 3 의 키 중 그대로 3 에 남은 비율: {stay_3 / total_3:.2%}")

    print("\n[6] 반복 횟수·시간·메모리")
    sample = keys[:200_000]
    for n in (10, 1000, 100_000, 1 << 30):
        mean_iter = statistics.fmean(jump_iterations(k, n) for k in sample)
        start = time.perf_counter()
        for k in sample:
            jump_hash(k, n)
        elapsed = (time.perf_counter() - start) / len(sample) * 1e9
        print(f"    jump n={n:<11,} 평균 반복 {mean_iter:5.2f}회"
              f" (ln n + 1 = {math.log(n) + 1:5.2f}) · 한 번 {elapsed:6.0f} ns")
    for n in (10, 1000):
        tracemalloc.start()
        ring = HashRing(n, 1000)
        _, peak = tracemalloc.get_traced_memory()
        current = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()
        start = time.perf_counter()
        for k in sample:
            ring.lookup(k)
        elapsed = (time.perf_counter() - start) / len(sample) * 1e9
        print(f"    ring n={n:<5} k=1000 점 {len(ring.points):>9,}개 · 남은 메모리"
              f" {current / 1024 / 1024:6.1f} MiB (최대 {peak / 1024 / 1024:6.1f})"
              f" · 한 번 {elapsed:6.0f} ns")


def report_donors(label, before, after):
    donated = {}
    per_bucket = {}
    for a in before:
        per_bucket[a] = per_bucket.get(a, 0) + 1
    for a, b in zip(before, after):
        if a != b:
            donated[a] = donated.get(a, 0) + 1
    fractions = [donated[b] / per_bucket[b] for b in donated]
    print(f"    {label:<10}: 내준 버킷 {len(donated):>3}개 / 100,"
          f" 내준 비율 최소 {min(fractions):.2%} · 최대 {max(fractions):.2%}")


if __name__ == "__main__":
    main()
