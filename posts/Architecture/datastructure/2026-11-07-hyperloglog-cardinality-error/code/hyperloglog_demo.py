"""HyperLogLog 를 논문 그림 3(32비트 해시 프로그램) 그대로 구현해 오차와 메모리를 잰다.

1) 정확한 집합(set)과 메모리·결과 비교
2) 레지스터 수 m 에 따른 상대 오차 — 이론값 1.04/sqrt(m) 과 비교
3) 작은 범위 보정 — 보정하지 않은 값은 n=0 에서도 약 0.7m 을 낸다
4) 중복 입력과 합치기(union) — 레지스터마다 최댓값을 취하면 합집합 추정이 된다
"""
import hashlib
import math
import statistics
import tracemalloc

HASH_BITS = 32


def hash32(key, salt=b""):
    # 시행마다 salt 를 바꿔 서로 다른 해시 함수를 흉내 낸다
    digest = hashlib.blake2b(key.encode(), digest_size=4, salt=salt).digest()
    return int.from_bytes(digest, "big")


def alpha(m):
    if m == 16:
        return 0.673
    if m == 32:
        return 0.697
    if m == 64:
        return 0.709
    return 0.7213 / (1 + 1.079 / m)


class HyperLogLog:
    def __init__(self, b, salt=b""):
        self.b = b
        self.m = 1 << b
        self.registers = bytearray(self.m)  # 레지스터 하나는 0..(32-b+1) 이라 1바이트면 된다
        self.salt = salt

    def add_hash(self, x):
        j = x >> (HASH_BITS - self.b)
        w = x & ((1 << (HASH_BITS - self.b)) - 1)
        width = HASH_BITS - self.b
        rho = width - w.bit_length() + 1  # 맨 왼쪽 1비트의 위치. w=0 이면 width+1
        if rho > self.registers[j]:
            self.registers[j] = rho

    def add(self, key):
        self.add_hash(hash32(key, self.salt))

    def raw_estimate(self):
        z = sum(2.0 ** -r for r in self.registers)
        return alpha(self.m) * self.m * self.m / z

    def estimate(self):
        e = self.raw_estimate()
        if e <= 2.5 * self.m:
            v = self.registers.count(0)
            if v:
                return self.m * math.log(self.m / v)  # 작은 범위 보정
            return e
        if e <= (1 / 30) * 2 ** 32:
            return e
        return -(2 ** 32) * math.log(1 - e / 2 ** 32)  # 큰 범위 보정

    def merge(self, other):
        merged = HyperLogLog(self.b, self.salt)
        merged.registers = bytearray(max(x, y) for x, y in zip(self.registers, other.registers))
        return merged


def keys(start, stop):
    return [f"user-{i}" for i in range(start, stop)]


def section_set_vs_hll():
    print("== 1) 정확한 집합 vs HyperLogLog (m=2048) ==")
    data = keys(0, 1_000_000)
    tracemalloc.start()
    exact = set(data)
    set_bytes, _ = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    hll = HyperLogLog(11)
    for key in data:
        hll.add(key)
    estimate = hll.estimate()
    print(f"  실제 고유 수     : {len(exact):,}")
    print(f"  set 이 쓴 메모리 : {set_bytes / 1024 / 1024:.1f} MiB (set 구조만, 문자열은 이미 있던 것)")
    print(f"  HLL 추정값       : {estimate:,.0f}  (오차 {100 * (estimate / len(exact) - 1):+.2f}%)")
    print(f"  HLL 레지스터     : {len(hll.registers):,} 바이트 (최댓값 {max(hll.registers)})")
    print()


def section_error_vs_m():
    print("== 2) m 에 따른 상대 오차 (n=20,000, 해시 40벌) ==")
    n = 20_000
    trials = 40
    data = keys(0, n)
    hashed_trials = [
        [hash32(k, salt=t.to_bytes(2, "big")) for k in data] for t in range(trials)]
    print("     m | 이론 1.04/√m | 실측 RMS 오차 | 평균 편향 | ±1σ 안 비율")
    for b in (4, 6, 8, 10, 12):
        m = 1 << b
        errors = []
        for hashes in hashed_trials:
            hll = HyperLogLog(b)
            for x in hashes:
                hll.add_hash(x)
            errors.append(hll.estimate() / n - 1)
        rms = math.sqrt(sum(e * e for e in errors) / trials)
        sigma = 1.04 / math.sqrt(m)
        within = sum(abs(e) <= sigma for e in errors) / trials
        print(f"  {m:>5} | {100 * sigma:>10.2f}% | {100 * rms:>11.2f}% |"
              f" {100 * statistics.mean(errors):>+7.2f}% | {100 * within:>6.1f}%")
    print()


def section_small_range():
    print("== 3) 작은 범위 보정 (m=2048, 보정 기준 2.5m = 5,120) ==")
    print("       n | 보정 전 E | 보정 후 E* | 빈 레지스터 V")
    for n in (0, 100, 1_000, 3_000, 5_000, 10_000, 50_000):
        hll = HyperLogLog(11)
        for key in keys(0, n):
            hll.add(key)
        print(f"  {n:>6,} | {hll.raw_estimate():>9,.0f} | {hll.estimate():>10,.0f} |"
              f" {hll.registers.count(0):>6,}")
    print()


def section_duplicates_and_merge():
    print("== 4) 중복 입력과 합치기 (m=2048) ==")
    a = HyperLogLog(11)
    for key in keys(0, 60_000):
        a.add(key)
    before = a.estimate()
    for key in keys(0, 60_000):  # 같은 키를 한 번 더
        a.add(key)
    print(f"  A = user-0..59999       : {before:,.0f} → 같은 키 재입력 후 {a.estimate():,.0f}")
    b = HyperLogLog(11)
    for key in keys(40_000, 100_000):
        b.add(key)
    union = a.merge(b)
    print(f"  B = user-40000..99999   : {b.estimate():,.0f}")
    print(f"  A ∪ B (레지스터 최댓값) : {union.estimate():,.0f}  (실제 100,000)")
    inter = a.estimate() + b.estimate() - union.estimate()
    print(f"  A ∩ B (포함-배제로 계산): {inter:,.0f}  (실제 20,000)")


def main():
    section_set_vs_hll()
    section_error_vs_m()
    section_small_range()
    section_duplicates_and_merge()


if __name__ == "__main__":
    main()
