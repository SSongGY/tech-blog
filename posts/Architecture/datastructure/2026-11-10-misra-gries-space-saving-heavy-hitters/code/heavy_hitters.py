"""Misra-Gries 와 Space-Saving 를 원 논문 의사코드대로 구현하고 오차 상한을 직접 센다.

칸 수 m 으로 맞춰 비교한다.
- Misra-Gries(m 칸): 과소 추정만 한다. 오차 <= n/(m+1)
- Space-Saving(m 칸): 과대 추정만 한다. 오차 <= min <= n/m
난수는 시드를 고정해 매번 같은 스트림을 만든다.
"""
import random
from collections import Counter

STREAM_LENGTH = 100_000
DISTINCT_ITEMS = 1_000
ZIPF_EXPONENT = 1.1
SEED = 42


def misra_gries(stream, counter_count):
    """Cormode·Hadjieleftheriou(2008) Algorithm 3.1 FREQUENT. k-1 = counter_count."""
    counters = {}
    decrement_steps = 0
    for item in stream:
        if item in counters:
            counters[item] += 1
        elif len(counters) < counter_count:
            counters[item] = 1
        else:
            decrement_steps += 1
            for key in list(counters):
                counters[key] -= 1
                if counters[key] == 0:
                    del counters[key]
    return counters, decrement_steps


def space_saving(stream, counter_count):
    """Metwally 외(2005) Figure 1. 값은 (count, epsilon) — epsilon 은 들어올 때 물려받은 min."""
    counters = {}
    for item in stream:
        if item in counters:
            count, error = counters[item]
            counters[item] = (count + 1, error)
        elif len(counters) < counter_count:
            counters[item] = (1, 0)
        else:
            victim = min(counters, key=lambda key: counters[key][0])
            evicted_count = counters.pop(victim)[0]
            counters[item] = (evicted_count + 1, evicted_count)
    return counters


def zipf_stream():
    rng = random.Random(SEED)
    items = [f"k{rank:04d}" for rank in range(1, DISTINCT_ITEMS + 1)]
    weights = [1 / rank**ZIPF_EXPONENT for rank in range(1, DISTINCT_ITEMS + 1)]
    return rng.choices(items, weights=weights, k=STREAM_LENGTH)


def compare(stream, counter_count, label):
    n = len(stream)
    exact = Counter(stream)
    mg, steps = misra_gries(stream, counter_count)
    ss = space_saving(stream, counter_count)
    ss_min = min(count for count, _ in ss.values())

    print(f"== {label}: n={n:,}, 고유 항목 {len(exact):,}, 칸 m={counter_count} ==")
    print(f"  MG 상한 n/(m+1) = {n / (counter_count + 1):,.1f} · 감소 단계 d = {steps:,}")
    print(f"  SS 상한 n/m     = {n / counter_count:,.1f} · 현재 min = {ss_min:,}")
    print(f"  검산 MG: 칸 합 {sum(mg.values()):,} + (m+1)*d {(counter_count + 1) * steps:,}"
          f" = {sum(mg.values()) + (counter_count + 1) * steps:,}")
    print(f"  검산 SS: 칸 합 {sum(c for c, _ in ss.values()):,} (Lemma 1: = n)")

    mg_errors = [exact[key] - mg.get(key, 0) for key in exact]
    ss_errors = [ss[key][0] - exact[key] for key in ss]
    print(f"  MG 최대 과소 {max(mg_errors):,} · 과대 {sum(e < 0 for e in mg_errors)}건")
    print(f"  SS 최대 과대 {max(ss_errors):,} · 과소 {sum(e < 0 for e in ss_errors)}건")

    threshold = n / (counter_count + 1)
    heavy = [key for key, f in exact.items() if f > threshold]
    print(f"  실제 빈도 > n/(m+1) 항목 {len(heavy)}개 — "
          f"MG 보유 {sum(k in mg for k in heavy)} · SS 보유 {sum(k in ss for k in heavy)}")

    print("  상위 8개 (실제 순위)")
    print("    항목  | 실제   | MG     | SS     | SS-eps")
    for key, f in exact.most_common(8):
        mg_value = mg.get(key, 0)
        ss_count, ss_error = ss.get(key, (0, 0))
        print(f"    {key} | {f:6,} | {mg_value:6,} | {ss_count:6,} | {ss_count - ss_error:6,}")

    same = all(ss.get(key, (ss_min, 0))[0] - ss_min == mg.get(key, 0) for key in exact)
    print(f"  관찰: 모든 항목에서 SS(m) 값 - min == MG(m) 값 ? {same}")
    wider = space_saving(stream, counter_count + 1)
    wider_min = min(count for count, _ in wider.values())
    mismatches = sum(
        max(wider.get(key, (wider_min, 0))[0] - wider_min, 0) != mg.get(key, 0)
        for key in exact
    )
    print(f"  관찰: SS(m+1) 값 - min 과 MG(m) 값이 다른 항목 {mismatches}개"
          f" (SS(m+1) min = {wider_min:,}, MG d = {steps:,})")
    print()


def burst_at_end():
    """끝부분에 새 항목이 몰려 들어오면 SS 상위 목록에 무엇이 오르는가."""
    rng = random.Random(SEED)
    stream = ["hot"] * 3_000 + [f"x{i}" for i in range(6_000)]
    rng.shuffle(stream)
    stream += [f"late{i}" for i in range(9)]
    counter_count = 10
    exact = Counter(stream)
    ss = space_saving(stream, counter_count)
    mg, _ = misra_gries(stream, counter_count)
    print(f"== 끝에 새 항목 9개: n={len(stream):,}, m={counter_count} ==")
    print("    항목   | 실제  | SS    | eps   | SS-eps | MG")
    for key, (count, error) in sorted(ss.items(), key=lambda kv: -kv[1][0]):
        print(f"    {key:7} | {exact[key]:5,} | {count:5,} | {error:5,} | {count - error:6,}"
              f" | {mg.get(key, 0):,}")
    print()


def main():
    stream = zipf_stream()
    compare(stream, 9, "Zipf s=1.1")
    compare(stream, 49, "Zipf s=1.1")
    rng = random.Random(SEED)
    uniform = [f"u{rng.randrange(DISTINCT_ITEMS):04d}" for _ in range(STREAM_LENGTH)]
    compare(uniform, 49, "균등 분포")
    burst_at_end()


if __name__ == "__main__":
    main()
