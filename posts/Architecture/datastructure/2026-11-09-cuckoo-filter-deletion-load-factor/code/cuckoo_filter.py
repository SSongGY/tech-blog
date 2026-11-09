"""쿠쿠 필터(Fan 외, CoNEXT 2014)를 표준 라이브러리로 구현해 적재율·오탐률·삭제를 잰다.

python cuckoo_filter.py
"""

import hashlib
import math
import random
import sys

MAX_NUM_KICKS = 500  # 논문 Algorithm 1, §4 실험의 "full" 조건
SEED = 20261109
TOTAL_SLOTS = 16384  # 버킷 수 x 버킷 크기를 고정해 b 끼리 비교한다


def _hash64(data):
    return int.from_bytes(hashlib.blake2b(data, digest_size=8).digest(), "little")


class CuckooFilter:
    def __init__(self, num_buckets, bucket_size, fp_bits, rng, hash_fingerprint=True):
        # i XOR hash(f) 가 다시 0..m-1 안에 들어오려면 m 이 2의 거듭제곱이어야 한다
        assert num_buckets & (num_buckets - 1) == 0
        self.num_buckets = num_buckets
        self.bucket_size = bucket_size
        self.fp_bits = fp_bits
        self.rng = rng
        self.hash_fingerprint = hash_fingerprint
        self.buckets = [[] for _ in range(num_buckets)]
        self.count = 0

    def _fingerprint_and_index(self, item):
        h = _hash64(item.encode())
        # 0 은 "빈 칸" 표시로 쓰는 구현이 많아 지문 값에서 뺀다
        fp = (h >> 32) % ((1 << self.fp_bits) - 1) + 1
        return fp, h % self.num_buckets

    def _alt_index(self, index, fp):
        mixed = _hash64(fp.to_bytes(4, "little")) if self.hash_fingerprint else fp
        return (index ^ mixed) % self.num_buckets

    def insert(self, item):
        fp, i1 = self._fingerprint_and_index(item)
        i2 = self._alt_index(i1, fp)
        for i in (i1, i2):
            if len(self.buckets[i]) < self.bucket_size:
                self.buckets[i].append(fp)
                self.count += 1
                return True
        i = self.rng.choice((i1, i2))
        for _ in range(MAX_NUM_KICKS):
            slot = self.rng.randrange(self.bucket_size)
            fp, self.buckets[i][slot] = self.buckets[i][slot], fp
            i = self._alt_index(i, fp)
            if len(self.buckets[i]) < self.bucket_size:
                self.buckets[i].append(fp)
                self.count += 1
                return True
        # 논문은 여기서 Failure 를 돌려준다. 손에 남은 지문 하나는 버려진다
        return False

    def contains(self, item):
        fp, i1 = self._fingerprint_and_index(item)
        return fp in self.buckets[i1] or fp in self.buckets[self._alt_index(i1, fp)]

    def delete(self, item):
        fp, i1 = self._fingerprint_and_index(item)
        for i in (i1, self._alt_index(i1, fp)):
            if fp in self.buckets[i]:
                self.buckets[i].remove(fp)
                self.count -= 1
                return True
        return False

    def load_factor(self):
        return self.count / (self.num_buckets * self.bucket_size)


class BloomFilter:
    def __init__(self, num_bits, num_hashes):
        self.num_bits = num_bits
        self.num_hashes = num_hashes
        self.bits = bytearray((num_bits + 7) // 8)

    def _positions(self, item):
        digest = hashlib.blake2b(item.encode(), digest_size=16).digest()
        h1 = int.from_bytes(digest[:8], "little")
        h2 = int.from_bytes(digest[8:], "little") | 1
        return [(h1 + k * h2) % self.num_bits for k in range(self.num_hashes)]

    def add(self, item):
        for p in self._positions(item):
            self.bits[p >> 3] |= 1 << (p & 7)

    def contains(self, item):
        return all(self.bits[p >> 3] >> (p & 7) & 1 for p in self._positions(item))


def fill_until_failure(bucket_size, fp_bits, seed, hash_fingerprint=True):
    rng = random.Random(seed)
    cf = CuckooFilter(TOTAL_SLOTS // bucket_size, bucket_size, fp_bits, rng, hash_fingerprint)
    i = 0
    while cf.insert(f"s{seed}-{i}"):
        i += 1
    return cf, i


def false_positive_rate(contains, probes, tag):
    return sum(contains(f"{tag}-{i}") for i in range(probes)) / probes


def main():
    print(f"Python {sys.version.split()[0]} · 해시 blake2b · 시드 {SEED}"
          f" · 전체 칸 {TOTAL_SLOTS:,} · MaxNumKicks {MAX_NUM_KICKS}")

    print("\n### 1. 버킷 크기 b 별 첫 삽입 실패 때의 적재율 (f=12, 5회)")
    print("   b | 버킷 수 | 최소   | 평균   | 최대")
    for b in (1, 2, 4, 8):
        loads = [fill_until_failure(b, 12, SEED + r)[0].load_factor() for r in range(5)]
        print(f"  {b:2d} | {TOTAL_SLOTS // b:6d} | {min(loads):.4f} | "
              f"{sum(loads) / 5:.4f} | {max(loads):.4f}")

    print("\n### 2. 지문 길이 f 별 오탐률 (b=4, 실패 직전까지 채움, 비회원 200,000건 조회)")
    print("   f | 적재율 | 측정 오탐률 | 상한 2b/2^f | 적재율 x 2b/2^f | bits/item = f/α")
    for f in (4, 6, 8, 10, 12):
        cf, _ = fill_until_failure(4, f, SEED)
        fpr = false_positive_rate(cf.contains, 200_000, "absent")
        bound = 2 * 4 / 2 ** f
        print(f"  {f:2d} | {cf.load_factor():.4f} | {fpr:11.6f} | {bound:11.6f} |"
              f" {cf.load_factor() * bound:15.6f} | {f / cf.load_factor():.2f}")

    print("\n### 3. 같은 메모리의 블룸 필터 (n 과 총 비트 수를 맞춤)")
    print("  필터           | n      | 총 비트 | bits/item | k | 측정 오탐률")
    for f in (8, 12):
        cf, n = fill_until_failure(4, f, SEED)
        total_bits = TOTAL_SLOTS * f
        k = max(1, round(total_bits / n * math.log(2)))
        bloom = BloomFilter(total_bits, k)
        for i in range(n):
            bloom.add(f"s{SEED}-{i}")
        cf_fpr = false_positive_rate(cf.contains, 200_000, "absent")
        bl_fpr = false_positive_rate(bloom.contains, 200_000, "absent")
        print(f"  쿠쿠 b=4 f={f:<2d}  | {n:6d} | {total_bits:7d} | {total_bits / n:9.2f} | - | {cf_fpr:.6f}")
        print(f"  블룸           | {n:6d} | {total_bits:7d} | {total_bits / n:9.2f} | {k} | {bl_fpr:.6f}")

    print("\n### 4. 삭제 — 넣은 것을 지우면 (b=4, f=8, 8,000개 넣고 4,000개 지움)")
    rng = random.Random(SEED)
    cf = CuckooFilter(TOTAL_SLOTS // 4, 4, 8, rng)
    members = [f"m-{i}" for i in range(8000)]
    for item in members:
        assert cf.insert(item)
    before = false_positive_rate(cf.contains, 100_000, "absent")
    deleted = members[:4000]
    print(f"  지운 4,000개 중 delete() 가 True: {sum(cf.delete(x) for x in deleted)}")
    kept_missing = sum(not cf.contains(x) for x in members[4000:])
    print(f"  남긴 4,000개 중 contains() 가 False(거짓 음성): {kept_missing}")
    print(f"  지운 4,000개 중 아직 '있다'로 나오는 것: {sum(cf.contains(x) for x in deleted)}")
    after = false_positive_rate(cf.contains, 100_000, "absent")
    print(f"  비회원 오탐률: 삭제 전 {before:.5f} -> 삭제 후 {after:.5f}"
          f" (적재율 {cf.load_factor():.4f})")

    print("\n### 5. 넣지 않은 것을 지우면 — 오탐 항목을 delete()")
    impostors = [f"ghost-{i}" for i in range(100_000) if cf.contains(f"ghost-{i}")]
    print(f"  비회원 100,000개 중 '있다'로 나온 것: {len(impostors)}")
    removed = sum(cf.delete(x) for x in impostors)
    lost = sum(not cf.contains(x) for x in members[4000:])
    print(f"  그것들을 delete(): True {removed}건 -> 남긴 회원 중 거짓 음성 {lost}건")

    print("\n### 6. 같은 항목을 반복해 넣으면 (b=4 -> 2b=8)")
    rng = random.Random(SEED)
    cf = CuckooFilter(TOTAL_SLOTS // 4, 4, 12, rng)
    results = [cf.insert("same-key") for _ in range(10)]
    fp, i1 = cf._fingerprint_and_index("same-key")
    i2 = cf._alt_index(i1, fp)
    print("  " + " ".join("O" if r else "X" for r in results)
          + f"  (성공 {sum(results)}회, 두 버킷의 지문 수 {len(cf.buckets[i1])}·"
          f"{len(cf.buckets[i2])}, 필터 전체 {cf.count}개)")

    print("\n### 7. 대체 버킷을 i XOR f 로(지문을 해시하지 않고) 구하면 (b=4, 5회)")
    print("   f | 해시함 평균 적재율 | 해시 안 함 평균 적재율")
    for f in (4, 6, 8, 12):
        with_hash = [fill_until_failure(4, f, SEED + r)[0].load_factor() for r in range(5)]
        no_hash = [fill_until_failure(4, f, SEED + r, False)[0].load_factor() for r in range(5)]
        print(f"  {f:2d} | {sum(with_hash) / 5:18.4f} | {sum(no_hash) / 5:.4f}")


if __name__ == "__main__":
    main()
