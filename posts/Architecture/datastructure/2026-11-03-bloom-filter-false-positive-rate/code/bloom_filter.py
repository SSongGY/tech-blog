"""블룸 필터를 직접 만들어 실측 오탐률을 이론식과 맞춰 본다.

SQLite 와 무관하며 표준 라이브러리만 쓴다. 해시는 BLAKE2b 하나를 쓰고
시드만 바꿔 k개를 만든다 (Kirsch-Mitzenmacher 이중해싱은 쓰지 않는다).
"""

import hashlib
import math
import random
import sys

SEED = 20261103


class BloomFilter:
    """비트 배열 m 비트, 해시 k 개."""

    def __init__(self, num_bits: int, num_hashes: int) -> None:
        self.num_bits = num_bits
        self.num_hashes = num_hashes
        self.bits = bytearray((num_bits + 7) // 8)
        self.num_items = 0

    def _positions(self, item: str):
        data = item.encode("utf-8")
        # BLAKE2b 를 두 번 돌려 128바이트를 얻고 8바이트씩 잘라 쓴다.
        # 해시 함수를 k 번 부르는 것과 결과가 같으면서 호출 수가 2로 줄어든다.
        digest = (hashlib.blake2b(data, digest_size=64).digest()
                  + hashlib.blake2b(data, digest_size=64,
                                    salt=b"\x01" * 8).digest())
        for index in range(self.num_hashes):
            chunk = digest[index * 8:index * 8 + 8]
            yield int.from_bytes(chunk, "little") % self.num_bits

    def add(self, item: str) -> None:
        for pos in self._positions(item):
            self.bits[pos // 8] |= 1 << (pos % 8)
        self.num_items += 1

    def __contains__(self, item: str) -> bool:
        return all(self.bits[pos // 8] >> (pos % 8) & 1
                   for pos in self._positions(item))

    def fill_ratio(self) -> float:
        set_bits = sum(bin(byte).count("1") for byte in self.bits)
        return set_bits / self.num_bits


def theoretical_rate(num_bits: int, num_items: int, num_hashes: int) -> float:
    """(1 - e^(-kn/m))^k — 비트가 서로 독립이라고 가정한 근사식."""
    return (1 - math.exp(-num_hashes * num_items / num_bits)) ** num_hashes


def optimal_hashes(num_bits: int, num_items: int) -> float:
    """오탐률을 최소로 만드는 k = (m/n)·ln2."""
    return (num_bits / num_items) * math.log(2)


def measure(num_bits: int, num_items: int, num_hashes: int,
            num_probes: int, rng: random.Random) -> tuple[float, float]:
    bloom = BloomFilter(num_bits, num_hashes)
    members = {f"member-{i}" for i in range(num_items)}
    for item in members:
        bloom.add(item)

    false_positives = 0
    for _ in range(num_probes):
        probe = f"probe-{rng.randrange(10 ** 12)}"
        if probe in members:          # 설계상 일어나지 않지만 확인해 둔다
            continue
        if probe in bloom:
            false_positives += 1
    return false_positives / num_probes, bloom.fill_ratio()


def main() -> None:
    print(f"Python {sys.version.split()[0]}")
    rng = random.Random(SEED)

    num_items = 10000
    num_probes = 100000

    print(f"\n[1] 원소 {num_items:,}개 · 시행 {num_probes:,}회 · k 를 바꿔 본다 (m = 100,000비트)")
    num_bits = 100000
    print(f"    최적 k = (m/n)·ln2 = {optimal_hashes(num_bits, num_items):.2f}")
    print(f"    {'k':>3} | {'이론 오탐률':>12} | {'실측 오탐률':>12} | {'비트 채움':>9}")
    print(f"    {'-' * 3}-+-{'-' * 12}-+-{'-' * 12}-+-{'-' * 9}")
    for num_hashes in range(1, 11):
        expected = theoretical_rate(num_bits, num_items, num_hashes)
        actual, fill = measure(num_bits, num_items, num_hashes, num_probes, rng)
        print(f"    {num_hashes:>3} | {expected:>11.4%} | {actual:>11.4%} | {fill:>8.2%}")

    print(f"\n[2] k 를 7로 고정하고 비트 수를 바꾼다")
    num_hashes = 7
    print(f"    {'m':>9} | {'m/n':>5} | {'이론 오탐률':>12} | {'실측 오탐률':>12}")
    print(f"    {'-' * 9}-+-{'-' * 5}-+-{'-' * 12}-+-{'-' * 12}")
    for num_bits in [40000, 60000, 80000, 100000, 140000, 200000]:
        expected = theoretical_rate(num_bits, num_items, num_hashes)
        actual, _ = measure(num_bits, num_items, num_hashes, num_probes, rng)
        print(f"    {num_bits:>9,} | {num_bits / num_items:>5.1f} | "
              f"{expected:>11.4%} | {actual:>11.4%}")

    print(f"\n[3] 같은 메모리로 집합을 그대로 들고 있으면")
    num_bits = 100000
    bloom = BloomFilter(num_bits, 7)
    members = [f"member-{i}" for i in range(num_items)]
    for item in members:
        bloom.add(item)
    exact = set(members)
    print(f"    블룸 필터 비트 배열  {sys.getsizeof(bloom.bits):>9,} 바이트 "
          f"({num_bits:,}비트)")
    print(f"    같은 원소를 담은 set {sys.getsizeof(exact):>9,} 바이트 "
          f"(문자열 본문 제외)")
    body = sum(sys.getsizeof(item) for item in exact)
    print(f"    set 의 문자열 본문   {body:>9,} 바이트")
    print(f"    합계 대비 비율       {sys.getsizeof(bloom.bits) / (sys.getsizeof(exact) + body):>9.2%}")

    print(f"\n[4] 거짓 음성이 하나라도 나오는지, 넣은 원소 전부를 되묻는다")
    missing = [item for item in members if item not in bloom]
    print(f"    넣은 원소 {len(members):,}개 중 '없다'고 답한 것: {len(missing)}개")


if __name__ == "__main__":
    main()
