"""저수지 표본추출(reservoir sampling) — Vitter(1985)의 Algorithm R 과 X.

1) 균일한가: 원소 20개에서 5개 뽑기를 10만 번 반복해 원소별 뽑힌 횟수를 센다
   (흔한 실수인 randint(0, t) 경계 오류도 같이 돌린다)
2) 난수를 몇 번 부르는가: 스트림 길이 N 을 늘려 가며 R 과 X 의 호출 수를 센다
3) 저수지에 들어간 횟수는 n(H_N - H_n) 과 맞는가
4) 걸린 시간 — 같은 스트림을 끝까지 읽는 비용은 둘 다 O(N) 이다
"""
import math
import platform
import random
import time
from itertools import islice

SEED = 20261109


class CountingRandom(random.Random):
    """random() 호출 횟수를 센다. 두 알고리즘의 비용 차이가 여기서 난다."""

    def __init__(self, seed):
        super().__init__(seed)
        self.calls = 0

    def random(self):
        self.calls += 1
        return super().random()


def algorithm_r(stream, n, rng):
    """Vitter 1985 §2 Algorithm R. 레코드마다 난수 한 번."""
    it = iter(stream)
    reservoir = list(islice(it, n))
    replaced = 0
    t = n
    for record in it:
        t += 1
        m = int(t * rng.random())  # 0 <= m <= t-1
        if m < n:
            reservoir[m] = record
            replaced += 1
    return reservoir, replaced


def algorithm_r_off_by_one(stream, n, rng):
    """흔한 실수: 0..t 를 뽑아 t+1 가지가 된다. 받아들일 확률이 n/(t+1) 로 줄어든다."""
    it = iter(stream)
    reservoir = list(islice(it, n))
    t = n
    for record in it:
        t += 1
        m = rng.randint(0, t)
        if m < n:
            reservoir[m] = record
    return reservoir, None


def algorithm_x(stream, n, rng):
    """Vitter 1985 §4 Algorithm X (§8 코드의 앞부분). 건너뛸 개수 S 를 한 번에 정한다."""
    it = iter(stream)
    reservoir = list(islice(it, n))
    replaced = 0
    t = n
    num = 0  # 항상 t - n
    while True:
        v = rng.random()
        skip = 0
        t += 1
        num += 1
        quot = num / t  # 이번 레코드가 뽑히지 않을 확률
        while quot > v:
            skip += 1
            t += 1
            num += 1
            quot = quot * num / t
        # skip 개를 읽어 버리고 그다음 레코드를 저수지에 넣는다
        for _ in islice(it, skip):
            pass
        record = next(it, None)
        if record is None:
            return reservoir, replaced
        reservoir[int(n * rng.random())] = record
        replaced += 1


def chi_square(counts, expected):
    return sum((c - expected) ** 2 / expected for c in counts)


def section_uniformity():
    print("== 1) 균일한가 — N=20 에서 n=5, 100,000회 ==")
    population, n, trials = 20, 5, 100_000
    expected = trials * n / population
    print(f"  원소마다 기대 횟수 = {trials} * {n} / {population} = {expected:,.0f}")
    print(f"  카이제곱 통계량의 기댓값 = 자유도 = {population - 1}")
    print()
    print("  알고리즘            | 0번 원소 | 9번 원소 | 19번 원소 |  최소  |  최대  | 카이제곱")
    for label, func in (("R", algorithm_r), ("X", algorithm_x),
                        ("R, randint(0,t) 실수", algorithm_r_off_by_one)):
        rng = CountingRandom(SEED)
        counts = [0] * population
        for _ in range(trials):
            sample, _ = func(range(population), n, rng)
            for x in sample:
                counts[x] += 1
        print(f"  {label:<18} | {counts[0]:>8,} | {counts[9]:>8,} | {counts[19]:>9,} |"
              f" {min(counts):>6,} | {max(counts):>6,} | {chi_square(counts, expected):>9.1f}")
    print()


def harmonic(k):
    return sum(1 / i for i in range(1, k + 1))


def section_random_calls():
    print("== 2) 난수 호출 수 — n=100 ==")
    n = 100
    print("        N    | R 호출      | X 호출  | X 의 호출/저장 | 2n·ln(N/n)")
    for exponent in range(3, 8):
        size = 10 ** exponent
        rng_r = CountingRandom(SEED)
        algorithm_r(range(size), n, rng_r)
        rng_x = CountingRandom(SEED)
        _, replaced = algorithm_x(range(size), n, rng_x)
        approx = 2 * n * math.log(size / n)
        print(f"  {size:>11,} | {rng_r.calls:>11,} | {rng_x.calls:>7,} |"
              f" {rng_x.calls / replaced:>14.3f} | {approx:>10,.0f}")
    print()


def section_replacements():
    print("== 3) 저수지에 넣은 횟수 — n(H_N - H_n) 과 비교, 시드 20개 평균 ==")
    n = 100
    print("        N    | 공식 n(H_N-H_n) | R 평균    | X 평균    | n·ln(N/n)")
    for exponent in (3, 4, 5, 6):
        size = 10 ** exponent
        formula = n * (harmonic(size) - harmonic(n))
        r_total = x_total = 0
        for k in range(20):
            _, r_rep = algorithm_r(range(size), n, CountingRandom(SEED + k))
            _, x_rep = algorithm_x(range(size), n, CountingRandom(SEED + k))
            r_total += r_rep
            x_total += x_rep
        print(f"  {size:>11,} | {formula:>15.1f} | {r_total / 20:>9.1f} |"
              f" {x_total / 20:>9.1f} | {n * math.log(size / n):>9.1f}")
    print()


def section_timing():
    print("== 4) 걸린 시간 — N=10,000,000, n=100, 3회 중 최소 ==")
    size, n = 10_000_000, 100
    for label, func in (("R", algorithm_r), ("X", algorithm_x)):
        best = math.inf
        for k in range(3):
            rng = CountingRandom(SEED + k)
            start = time.perf_counter()
            func(range(size), n, rng)
            best = min(best, time.perf_counter() - start)
        print(f"  {label}: {best:.2f} 초")
    print("  -- 비교 기준: 같은 스트림을 읽기만 할 때")
    best = math.inf
    for _ in range(3):
        start = time.perf_counter()
        for _ in range(size):
            pass
        best = min(best, time.perf_counter() - start)
    print(f"  읽기만: {best:.2f} 초")
    print()


def main():
    print(f"Python {platform.python_version()} / {platform.system()} {platform.release()}")
    print(f"시드 {SEED}")
    print()
    section_uniformity()
    section_random_calls()
    section_replacements()
    section_timing()


if __name__ == "__main__":
    main()
