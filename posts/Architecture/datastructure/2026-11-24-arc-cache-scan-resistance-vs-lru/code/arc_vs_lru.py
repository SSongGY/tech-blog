"""ARC(Megiddo·Modha, FAST 2003 그림 4)를 그대로 옮겨 LRU·벨러디 최적과 적중률을 비교한다.

1) 접근열 네 가지에서 LRU / ARC / OPT(벨러디, 미래를 아는 최적) 적중률
2) 뜨거운 키 + 주기적 순차 스캔에서 스캔 직후 뜨거운 키가 캐시에 몇 개 남는가
3) 같은 접근열에서 적응 변수 p 와 네 목록 크기의 변화
4) 모든 요청 뒤에 논문의 불변식을 검사한 결과
"""
import random
from collections import OrderedDict

SEED = 20031


class LruCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.pages = OrderedDict()

    def access(self, key):
        if key in self.pages:
            self.pages.move_to_end(key)
            return True
        if len(self.pages) >= self.capacity:
            self.pages.popitem(last=False)
        self.pages[key] = None
        return False

    def __contains__(self, key):
        return key in self.pages


class ArcCache:
    """논문 그림 4. OrderedDict 의 앞이 LRU, 뒤가 MRU 다."""

    def __init__(self, capacity):
        self.c = capacity
        self.p = 0.0
        self.t1, self.t2 = OrderedDict(), OrderedDict()   # 캐시에 있는 페이지
        self.b1, self.b2 = OrderedDict(), OrderedDict()   # 쫓겨난 페이지의 이름만

    def __contains__(self, key):
        return key in self.t1 or key in self.t2

    def _replace(self, key):
        t1_len = len(self.t1)
        if t1_len and (t1_len > self.p or (key in self.b2 and t1_len == self.p)):
            old, _ = self.t1.popitem(last=False)
            self.b1[old] = None
        else:
            old, _ = self.t2.popitem(last=False)
            self.b2[old] = None

    def access(self, key):
        # Case I: 캐시 적중 — 두 번째 이상 본 페이지이므로 T2 의 MRU 로
        if key in self.t1 or key in self.t2:
            (self.t1 if key in self.t1 else self.t2).pop(key)
            self.t2[key] = None
            return True
        # Case II: B1 유령 적중 — 최근성 쪽을 더 키웠으면 맞았을 것이다
        if key in self.b1:
            delta = 1 if len(self.b1) >= len(self.b2) else len(self.b2) / len(self.b1)
            self.p = min(self.p + delta, self.c)
            self._replace(key)
            self.b1.pop(key)
            self.t2[key] = None
            return False
        # Case III: B2 유령 적중 — 빈도 쪽을 더 키웠으면 맞았을 것이다
        if key in self.b2:
            delta = 1 if len(self.b2) >= len(self.b1) else len(self.b1) / len(self.b2)
            self.p = max(self.p - delta, 0)
            self._replace(key)
            self.b2.pop(key)
            self.t2[key] = None
            return False
        # Case IV: 처음 보는 페이지
        if len(self.t1) + len(self.b1) == self.c:
            if len(self.t1) < self.c:
                self.b1.popitem(last=False)
                self._replace(key)
            else:
                self.t1.popitem(last=False)
        else:
            total = len(self.t1) + len(self.t2) + len(self.b1) + len(self.b2)
            if total >= self.c:
                if total == 2 * self.c:
                    self.b2.popitem(last=False)
                self._replace(key)
        self.t1[key] = None
        return False

    def invariant_errors(self):
        """논문 3절의 DBL 불변식과 캐시 크기 한도."""
        errors = 0
        errors += len(self.t1) + len(self.t2) > self.c
        errors += len(self.t1) + len(self.b1) > self.c
        errors += len(self.t1) + len(self.t2) + len(self.b1) + len(self.b2) > 2 * self.c
        errors += not 0 <= self.p <= self.c
        return errors


def opt_hits(trace, capacity):
    """벨러디 최적: 다음에 가장 늦게 쓰일 페이지를 내보낸다. 상한선으로만 쓴다."""
    next_use, upcoming = [0] * len(trace), {}
    for i in range(len(trace) - 1, -1, -1):
        next_use[i] = upcoming.get(trace[i], float("inf"))
        upcoming[trace[i]] = i
    cache, hits = {}, 0
    for i, key in enumerate(trace):
        if key in cache:
            hits += 1
        elif len(cache) >= capacity:
            victim = max(cache, key=cache.get)
            del cache[victim]
        cache[key] = next_use[i]
    return hits


def hot_with_scans(rng, rounds, hot_size, hot_reads, scan_len):
    """뜨거운 키를 여러 번 읽다가, 한 번만 읽고 버릴 새 키를 순서대로 훑는다."""
    trace, scan_starts, next_cold = [], [], 10_000
    for _ in range(rounds):
        trace += [rng.randrange(hot_size) for _ in range(hot_reads)]
        scan_starts.append(len(trace))
        trace += list(range(next_cold, next_cold + scan_len))
        next_cold += scan_len
    return trace, scan_starts


def main():
    capacity = 100
    rng = random.Random(SEED)
    workloads = {}
    workloads["hot_only"] = [rng.randrange(80) for _ in range(20_000)]
    workloads["hot_with_scans"], scan_starts = hot_with_scans(
        random.Random(SEED), rounds=20, hot_size=60, hot_reads=1_000, scan_len=200)
    workloads["loop_120"] = [i % 120 for i in range(20_000)]
    zipf_keys = list(range(1_000))
    weights = [1 / (k + 1) for k in zipf_keys]
    workloads["zipf_1000"] = rng.choices(zipf_keys, weights, k=20_000)

    print(f"[1] 캐시 {capacity}칸, 적중률 (%) — seed={SEED}")
    print(f"    {'workload':<16}{'requests':>9}{'LRU':>8}{'ARC':>8}{'OPT':>8}")
    for name, trace in workloads.items():
        lru, arc = LruCache(capacity), ArcCache(capacity)
        lru_hits = sum(lru.access(k) for k in trace)
        arc_hits = sum(arc.access(k) for k in trace)
        best = opt_hits(trace, capacity)
        n = len(trace)
        print(f"    {name:<16}{n:>9}{100 * lru_hits / n:>8.1f}"
              f"{100 * arc_hits / n:>8.1f}{100 * best / n:>8.1f}")

    trace = workloads["hot_with_scans"]
    print("\n[2] 뜨거운 키 60개 중 스캔(200개)이 끝난 직후 캐시에 남은 수")
    print("    (round, LRU, ARC)")
    lru, arc = LruCache(capacity), ArcCache(capacity)
    scan_ends = {s + 200 for s in scan_starts}
    trace_log, bad = [], 0
    for i, key in enumerate(trace):
        lru.access(key)
        arc.access(key)
        bad += arc.invariant_errors()
        if i + 1 in scan_ends:
            round_no = len(trace_log) + 1
            lru_left = sum(k in lru for k in range(60))
            arc_left = sum(k in arc for k in range(60))
            trace_log.append((round_no, lru_left, arc_left,
                              round(arc.p, 2), len(arc.t1), len(arc.t2),
                              len(arc.b1), len(arc.b2)))
    for row in trace_log[:3] + trace_log[-2:]:
        print("   ", row[:3])

    print("\n[3] 스캔 직후 ARC 상태 (round, p, |T1|, |T2|, |B1|, |B2|)")
    for row in trace_log[:3] + trace_log[-2:]:
        print("   ", (row[0],) + row[3:])

    print(f"\n[4] 요청 {len(trace)}건마다 불변식 검사 — 위반 {bad}건")

    print("\n[5] zipf_1000 에서 p 와 유령 적중 (2,000건마다)")
    print("    (requests, p, |T1|, |T2|, |B1|, |B2|, B1_hits, B2_hits)")
    arc, b1_hits, b2_hits, bad = ArcCache(capacity), 0, 0, 0
    for i, key in enumerate(workloads["zipf_1000"], start=1):
        b1_hits += key in arc.b1
        b2_hits += key in arc.b2
        arc.access(key)
        bad += arc.invariant_errors()
        if i % 2_000 == 0:
            print("   ", (i, round(arc.p, 2), len(arc.t1), len(arc.t2),
                          len(arc.b1), len(arc.b2), b1_hits, b2_hits))
    print(f"    불변식 위반 {bad}건")


if __name__ == "__main__":
    main()
