"""MinHash 로 자카드 유사도를 추정하고, LSH 밴딩의 후보 확률을 시뮬레이션과 맞춰 본다.

근거: Rajaraman & Ullman, Mining of Massive Datasets 3장
  3.3.3 민해시 값이 같을 확률 = 자카드 유사도
  3.3.5 행 순열 대신 해시 함수로 서명을 만든다
  3.4.2 밴드 b 개, 행 r 개일 때 후보가 될 확률 1-(1-s^r)^b, 임계값 근사 (1/b)^(1/r)

[1] 서명 길이 k 에 따른 추정 오차 — 이항분포 표준편차 sqrt(s(1-s)/k) 와 비교
[2] b=20, r=5 밴딩 — 공식과 시뮬레이션의 후보 확률
[3] 같은 서명 길이 100 을 (b, r) 로 나누는 방법에 따라 임계값이 어디로 가는가
[4] 문서 2,000 개에서 비교 쌍이 얼마나 줄고, 무엇을 놓치는가
"""
import math
import random
import statistics
import time

PRIME = (1 << 61) - 1  # 메르센 소수. 원소 id 보다 커야 h(x) 가 서로 다른 값으로 퍼진다
SEED = 20261118


def make_hash_functions(k, rng):
    """h(x) = (a*x + b) mod p. 3.3.5 의 '무작위 행 순열을 흉내 내는 해시 함수' k 개."""
    return [(rng.randrange(1, PRIME), rng.randrange(0, PRIME)) for _ in range(k)]


def signature(items, hash_functions):
    return [min((a * x + b) % PRIME for x in items) for a, b in hash_functions]


def jaccard(set_a, set_b):
    return len(set_a & set_b) / len(set_a | set_b)


def estimate(sig_a, sig_b):
    return sum(x == y for x, y in zip(sig_a, sig_b)) / len(sig_a)


def make_pair(similarity, union_size, rng):
    """자카드 유사도가 정확히 similarity 인 두 집합. 원소는 서로 겹치지 않는 큰 정수."""
    common = round(similarity * union_size)
    rest = union_size - common
    ids = rng.sample(range(1, 10**12), union_size)
    shared = set(ids[:common])
    only_a = set(ids[common : common + rest // 2])
    only_b = set(ids[common + rest // 2 :])
    return shared | only_a, shared | only_b


def is_candidate(sig_a, sig_b, bands, rows):
    return any(
        sig_a[i * rows : (i + 1) * rows] == sig_b[i * rows : (i + 1) * rows]
        for i in range(bands)
    )


def band_probability(s, bands, rows):
    return 1 - (1 - s**rows) ** bands


def part1(rng):
    print("\n[1] 서명 길이 k 와 추정 오차 (s=0.5, 합집합 100, 쌍 200개)")
    print("     k  평균 추정   표준편차   이론 sqrt(s(1-s)/k)   |오차|>0.1 비율")
    s = 0.5
    pairs = [make_pair(s, 100, rng) for _ in range(200)]
    for k in (16, 64, 256, 1024):
        functions = make_hash_functions(k, rng)
        values = [estimate(signature(a, functions), signature(b, functions)) for a, b in pairs]
        spread = statistics.pstdev(values)
        theory = math.sqrt(s * (1 - s) / k)
        miss = sum(abs(v - s) > 0.1 for v in values) / len(values)
        print(f"  {k:5d}  {statistics.mean(values):8.4f}  {spread:9.4f}  {theory:13.4f}  {miss:14.3f}")


def part2(rng):
    print("\n[2] b=20, r=5 (서명 100) — 후보가 될 확률, 유사도마다 쌍 300개")
    print("     s   공식 1-(1-s^5)^20   시뮬레이션")
    functions = make_hash_functions(100, rng)
    for s in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
        hits = 0
        for _ in range(300):
            a, b = make_pair(s, 100, rng)
            hits += is_candidate(signature(a, functions), signature(b, functions), 20, 5)
        print(f"   {s:.1f}   {band_probability(s, 20, 5):17.4f}   {hits / 300:10.4f}")


def part3():
    print("\n[3] 서명 100 을 나누는 방법과 임계값")
    print("     b    r   (1/b)^(1/r)   확률이 0.5 가 되는 s   s=0.5 일 때   s=0.8 일 때")
    for bands, rows in ((100, 1), (50, 2), (25, 4), (20, 5), (10, 10), (5, 20)):
        approx = (1 / bands) ** (1 / rows)
        low, high = 0.0, 1.0
        for _ in range(60):  # 단조 증가 함수라 이분 탐색으로 0.5 지점을 찾는다
            mid = (low + high) / 2
            if band_probability(mid, bands, rows) < 0.5:
                low = mid
            else:
                high = mid
        print(
            f"   {bands:3d}  {rows:3d}   {approx:11.4f}   {low:19.4f}"
            f"   {band_probability(0.5, bands, rows):10.4f}   {band_probability(0.8, bands, rows):10.4f}"
        )


def part4(rng):
    print("\n[4] 문서 2,000 개 (각 원소 100개) 중 유사 쌍 30개를 심어 두고 b=20, r=5 로 찾기")
    universe = range(1, 10**12)
    documents = [set(rng.sample(universe, 100)) for _ in range(2000)]
    planted = {}
    for i, s in enumerate([0.9] * 10 + [0.7] * 10 + [0.5] * 10):
        a, b = make_pair(s, 150, rng)
        documents[2 * i], documents[2 * i + 1] = a, b
        planted[(2 * i, 2 * i + 1)] = s

    functions = make_hash_functions(100, rng)
    started = time.perf_counter()
    signatures = [signature(doc, functions) for doc in documents]
    buckets = {}
    for doc_id, sig in enumerate(signatures):
        for band in range(20):
            key = (band, tuple(sig[band * 5 : (band + 1) * 5]))
            buckets.setdefault(key, []).append(doc_id)
    candidates = set()
    for members in buckets.values():
        for x in range(len(members)):
            for y in range(x + 1, len(members)):
                candidates.add((members[x], members[y]))
    elapsed = time.perf_counter() - started

    total = len(documents) * (len(documents) - 1) // 2
    print(f"  전체 쌍 {total:,}개 → 후보 쌍 {len(candidates):,}개 (서명·버킷 {elapsed:.1f}초)")
    for s in (0.9, 0.7, 0.5):
        group = [pair for pair, value in planted.items() if value == s]
        found = sum(pair in candidates for pair in group)
        print(f"  심은 유사도 {s}: {len(group)}쌍 중 {found}쌍 후보, 이론 {band_probability(s, 20, 5):.4f}")
    false_pairs = [p for p in candidates if p not in planted]
    if false_pairs:
        worst = max(jaccard(documents[x], documents[y]) for x, y in false_pairs)
        print(f"  심지 않은 후보 {len(false_pairs)}쌍, 그중 최대 실제 자카드 {worst:.4f}")
    else:
        print("  심지 않은 후보 0쌍")


def main():
    rng = random.Random(SEED)
    part1(rng)
    part2(rng)
    part3()
    part4(rng)


if __name__ == "__main__":
    main()
