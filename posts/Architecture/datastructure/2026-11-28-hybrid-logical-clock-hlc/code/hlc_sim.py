"""하이브리드 논리 시계(HLC)를 Kulkarni 외(2014) Figure 5 그대로 구현해 물리 시계와 비교한다.

1) 메시지 하나 — 시계가 늦은 노드가 받은 뒤 쓴 값이 물리 시각으로는 '더 먼저'가 된다
2) 노드 3개 무작위 시뮬레이션 — 인과 순서 위반 수, l - pt 최댓값, c 최댓값
3) 같은 ms 안에 사건이 몰릴 때 — Figure 3 의 단순 알고리즘은 l - pt 가 계속 커진다
4) 물리 시계가 뒤로 점프할 때 — 물리 시각은 같은 노드 안에서도 거꾸로 가고 HLC 는 그대로 증가
5) 48비트 l + 16비트 c 를 64비트 정수 하나로 묶어도 순서가 같은가
"""
import heapq
import random


class HybridLogicalClock:
    """Figure 5. l 은 지금까지 들은 가장 큰 물리 시각, c 는 l 이 같을 때만 늘어나는 카운터."""

    def __init__(self):
        self.l = 0
        self.c = 0

    def send_or_local(self, pt):
        old_l = self.l
        self.l = max(old_l, pt)
        self.c = self.c + 1 if self.l == old_l else 0
        return (self.l, self.c)

    def receive(self, pt, msg_l, msg_c):
        old_l = self.l
        self.l = max(old_l, msg_l, pt)
        if self.l == old_l == msg_l:
            self.c = max(self.c, msg_c) + 1
        elif self.l == old_l:
            self.c += 1
        elif self.l == msg_l:
            self.c = msg_c + 1
        else:
            self.c = 0
        return (self.l, self.c)


class NaiveClock:
    """Figure 3. 물리 시각과 논리 증가분을 l 하나에 같이 담는다."""

    def __init__(self):
        self.l = 0

    def send_or_local(self, pt):
        self.l = max(self.l + 1, pt)
        return self.l

    def receive(self, pt, msg_l):
        self.l = max(self.l + 1, msg_l + 1, pt)
        return self.l


def single_message():
    print("[1] 메시지 하나 — 노드 A 는 시계가 맞고, 노드 B 는 40ms 늦다 (전송 5ms)")
    a, b = HybridLogicalClock(), HybridLogicalClock()
    true_send, true_recv = 1000, 1005
    pt_a, pt_b = true_send + 0, true_recv - 40
    ts_send = a.send_or_local(pt_a)
    ts_recv = b.receive(pt_b, *ts_send)
    print(f"  A 가 x=1 을 쓰고 보냄   물리 시각 {pt_a}   HLC {ts_send}")
    print(f"  B 가 받고 x=2 로 덮어씀 물리 시각 {pt_b}    HLC {ts_recv}")
    print(f"  물리 시각으로 '나중' 쓰기: x={1 if pt_a > pt_b else 2}  (최종값이 1 로 돌아간다)")
    print(f"  HLC 로 '나중' 쓰기     : x={2 if ts_recv > ts_send else 1}")


def simulate(offsets, events_per_node, seed):
    """참 시각 기준 사건 큐로 돌린다. 각 노드는 1~3ms 마다 지역 사건 또는 송신을 만든다."""
    rng = random.Random(seed)
    nodes = len(offsets)
    clocks = [HybridLogicalClock() for _ in range(nodes)]
    queue = []
    seq = 0
    for n in range(nodes):
        heapq.heappush(queue, (rng.randint(1, 3), seq, n, "tick", None))
        seq += 1
    made = [0] * nodes
    pt_violations = hlc_violations = messages = 0
    max_drift = max_c = 0
    while queue:
        t, _, n, kind, payload = heapq.heappop(queue)
        pt = t + offsets[n]
        if kind == "tick":
            stamp = clocks[n].send_or_local(pt)
            if rng.random() < 0.5:                       # 절반은 다른 노드로 보낸다
                dest = rng.choice([d for d in range(nodes) if d != n])
                delay = rng.randint(1, 20)
                heapq.heappush(queue, (t + delay, seq, dest, "recv", (pt, stamp)))
                seq += 1
            made[n] += 1
            if made[n] < events_per_node:
                heapq.heappush(queue, (t + rng.randint(1, 3), seq, n, "tick", None))
                seq += 1
        else:
            send_pt, send_stamp = payload
            stamp = clocks[n].receive(pt, *send_stamp)
            messages += 1
            pt_violations += pt <= send_pt               # 받은 쪽 물리 시각이 보낸 쪽보다 크지 않다
            hlc_violations += not stamp > send_stamp
        max_drift = max(max_drift, stamp[0] - pt)
        max_c = max(max_c, stamp[1])
    return messages, pt_violations, hlc_violations, max_drift, max_c


def burst_loop(hops_per_ms, total_ms):
    """세 노드가 같은 ms 안에 메시지를 hops_per_ms 번 돌린다. 시계 오차는 없다."""
    hlc = [HybridLogicalClock() for _ in range(3)]
    naive = [NaiveClock() for _ in range(3)]
    h_stamp = hlc[0].send_or_local(0)
    n_stamp = naive[0].send_or_local(0)
    node = 0
    worst_naive = worst_hlc = max_c = 0
    for pt in range(total_ms):
        for _ in range(hops_per_ms):
            node = (node + 1) % 3
            h_stamp = hlc[node].receive(pt, *h_stamp)
            n_stamp = naive[node].receive(pt, n_stamp)
            worst_naive = max(worst_naive, n_stamp - pt)
            worst_hlc = max(worst_hlc, h_stamp[0] - pt)
            max_c = max(max_c, h_stamp[1])
    return worst_naive, worst_hlc, max_c


def backward_jump():
    print("\n[4] 노드 하나의 물리 시계가 t=5 에서 30ms 뒤로 점프 (NTP 보정 등)")
    clock = HybridLogicalClock()
    pts = [100, 101, 102, 103, 104, 75, 76, 77, 105, 106]
    print("  pt   :", pts)
    stamps = [clock.send_or_local(pt) for pt in pts]
    print("  HLC  :", stamps)
    print("  물리 시각이 줄어든 횟수:", sum(b < a for a, b in zip(pts, pts[1:])),
          "  HLC 가 줄어든 횟수:", sum(b <= a for a, b in zip(stamps, stamps[1:])))


def pack(stamp):
    l, c = stamp
    assert l < (1 << 48) and c < (1 << 16)
    return (l << 16) | c


def main():
    single_message()

    print("\n[2] 노드 3개, 노드당 20,000 사건, 전송 지연 1~20ms")
    print(f"  {'시계 오프셋(ms)':<18} {'ε':>4} {'메시지':>7} {'물리 시각 위반':>12} {'HLC 위반':>8}"
          f" {'max(l-pt)':>9} {'max c':>6}")
    for offsets in ([0, 0, 0], [0, -10, 5], [0, -40, 25], [0, -200, 150]):
        eps = max(offsets) - min(offsets)
        m, pv, hv, drift, c = simulate(offsets, 20_000, seed=20261128)
        print(f"  {str(offsets):<18} {eps:>4} {m:>7,} {pv:>12,} {hv:>8} {drift:>9} {c:>6}")

    print("\n[3] 시계 오차 0, 세 노드가 메시지를 돌린다 — 1ms 에 몇 번 도느냐에 따라")
    print(f"  {'1ms 당 홉':>8} {'진행(ms)':>8} {'단순 max(l-pt)':>14} {'HLC max(l-pt)':>13} {'HLC max c':>9}")
    for hops in (1, 2, 4):
        for total in (1_000, 10_000):
            naive, hlc, c = burst_loop(hops, total)
            print(f"  {hops:>8} {total:>8,} {naive:>14,} {hlc:>13} {c:>9}")

    backward_jump()

    print("\n[5] 64비트 묶음 — (l << 16) | c 정수 비교가 (l, c) 사전식 비교와 같은가")
    rng = random.Random(1)
    stamps = [(rng.randint(0, 1_700_000_000_000), rng.randint(0, 5)) for _ in range(20_000)]
    stamps += [(1_764_300_000_000, c) for c in range(10)]
    by_tuple = sorted(stamps)
    by_int = sorted(stamps, key=pack)
    print("  순서 일치:", by_tuple == by_int, f" 표본 {len(stamps):,}개, l 최대 {max(s[0] for s in stamps):,}"
          f" (2^48 = {1 << 48:,})")


if __name__ == "__main__":
    main()
