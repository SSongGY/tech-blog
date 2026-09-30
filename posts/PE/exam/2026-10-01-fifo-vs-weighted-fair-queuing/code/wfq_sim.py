"""FIFO, GPS(유체 모델), WFQ(PGPS) 세 가지 스케줄러를 같은 도착 패턴에 돌려 비교한다.

- GPS 와 WFQ 는 Parekh & Gallager(1993)의 정의를 그대로 구현한다
- 첫 시나리오는 그 논문 Table I 의 도착 패턴이다. 결과가 논문 값과 같은지 확인한다
- 시간·가상 시간은 Fraction 으로 계산한다. 부동소수 오차로 동률 판정이 흔들리지 않게 하려는 것이다
"""

import platform
import sys
from dataclasses import dataclass, field
from fractions import Fraction as Fr


@dataclass
class Packet:
    session: int
    arrival: Fr
    size: Fr
    seq: int                  # 세션 안에서 몇 번째 패킷인가 (1부터)
    tag: Fr = field(default=None)       # 가상 종료 시각 F = max(F_prev, V(a)) + L/φ
    gps_done: Fr = field(default=None)  # GPS 에서 전송이 끝나는 실제 시각


def run_gps(packets, phi, rate=Fr(1)):
    """가상 시간 V(t)를 따라가며 GPS 종료 시각과 가상 종료 태그를 구한다.

    V(t)는 백로그된 세션 집합 B 의 가중치 합으로 나눈 속도(rate / Σφ_B)로 증가한다.
    패킷은 V(t)가 자기 태그에 닿는 순간 GPS 에서 전송을 마친다.
    """
    arrivals = sorted(packets, key=lambda p: (p.arrival, p.session))
    last_tag = {s: Fr(0) for s in phi}
    pending = []              # 도착했지만 GPS 에서 아직 안 끝난 패킷
    t, v, i = Fr(0), Fr(0), 0
    while i < len(arrivals) or pending:
        while i < len(arrivals) and arrivals[i].arrival == t:
            p = arrivals[i]
            p.tag = max(last_tag[p.session], v) + p.size / phi[p.session]
            last_tag[p.session] = p.tag
            pending.append(p)
            i += 1
        backlogged = {p.session for p in pending}
        next_arrival = arrivals[i].arrival - t if i < len(arrivals) else None
        if not backlogged:
            t = arrivals[i].arrival   # 유휴 구간: V 는 멈춘다
            continue
        v_speed = rate / sum(phi[s] for s in backlogged)
        next_tag = min(p.tag for p in pending)
        dt = (next_tag - v) / v_speed
        if next_arrival is not None and next_arrival < dt:
            dt = next_arrival
        t, v = t + dt, v + dt * v_speed
        for p in [p for p in pending if p.tag == v]:
            p.gps_done = t
            pending.remove(p)


def run_wfq(packets, rate=Fr(1)):
    """서버가 비는 순간 도착해 있는 패킷 가운데 태그가 가장 작은 것을 통째로 보낸다 (비선점)."""
    waiting = sorted(packets, key=lambda p: (p.arrival, p.session))
    done, t = {}, Fr(0)
    while waiting:
        ready = [p for p in waiting if p.arrival <= t]
        if not ready:
            t = waiting[0].arrival
            continue
        p = min(ready, key=lambda q: (q.tag, q.arrival, q.session))
        t += p.size / rate
        done[id(p)] = t
        waiting.remove(p)
    return done


def run_fifo(packets, rate=Fr(1)):
    done, t = {}, Fr(0)
    for p in sorted(packets, key=lambda p: (p.arrival, p.session)):
        t = max(t, p.arrival) + p.size / rate
        done[id(p)] = t
    return done


def make(spec):
    """spec: {세션: [(도착, 크기), ...]} → Packet 목록"""
    return [Packet(s, Fr(a), Fr(l), k + 1)
            for s, pkts in spec.items() for k, (a, l) in enumerate(pkts)]


def fmt(x):
    return str(x.numerator) if x.denominator == 1 else f"{float(x):.2f}"


def simulate(spec, phi):
    packets = make(spec)
    run_gps(packets, phi)
    wfq, fifo = run_wfq(packets), run_fifo(packets)
    return packets, wfq, fifo


def print_table(packets, wfq, fifo):
    print("  패킷  도착  크기  태그F   GPS종료  WFQ종료  FIFO종료  WFQ지연  FIFO지연")
    for p in sorted(packets, key=lambda p: (p.session, p.seq)):
        w, f = wfq[id(p)], fifo[id(p)]
        print(f"  {p.session}-{p.seq:<3} {fmt(p.arrival):>4} {fmt(p.size):>5} {fmt(p.tag):>6}"
              f" {fmt(p.gps_done):>8} {fmt(w):>8} {fmt(f):>9}"
              f" {fmt(w - p.arrival):>8} {fmt(f - p.arrival):>9}")


def by_session(packets, done):
    return {s: [done[id(p)] for p in sorted(packets, key=lambda p: p.seq) if p.session == s]
            for s in sorted({p.session for p in packets})}


def scenario_paper_table1():
    # Parekh & Gallager(1993) Fig. 1 / Table I 의 도착 패턴. 서버 속도 r = 1
    spec = {1: [(1, 1), (2, 1), (3, 2), (11, 2)],
            2: [(0, 3), (5, 2), (9, 2)]}
    paper = {  # 논문 Table I 의 값 (세션별 출발 시각)
        "φ1 = φ2": ({1: 1, 2: 1},
                    {1: [3, 5, 9, 13], 2: [5, 9, 11]},
                    {1: [4, 5, 7, 13], 2: [3, 9, 11]}),
        "2φ1 = φ2": ({1: 1, 2: 2},
                     {1: [4, 5, 9, 13], 2: [4, 8, 11]},
                     {1: [4, 5, 9, 13], 2: [3, 7, 11]}),
    }
    print("[1] 논문 Table I 재현 — 세션 1·2, 서버 속도 1")
    for label, (phi, gps_expect, wfq_expect) in paper.items():
        packets, wfq, fifo = simulate(spec, phi)
        print(f"\n  가중치 {label}")
        print_table(packets, wfq, fifo)
        gps_got = by_session(packets, {id(p): p.gps_done for p in packets})
        wfq_got = by_session(packets, wfq)
        ok = gps_got == gps_expect and wfq_got == wfq_expect
        print(f"  논문 Table I 과 일치: {'예' if ok else '아니오'}")
        lag = max(wfq[id(p)] - p.gps_done for p in packets)
        lmax = max(p.size for p in packets)
        print(f"  WFQ 가 GPS 보다 늦은 최대 시간 = {fmt(lag)}  (정리 1 상한 Lmax/r = {fmt(lmax)})")


def scenario_greedy_flow():
    # 세션 1 이 한꺼번에 8개를 쏟아 넣고, 세션 2 는 드문드문 1개씩 보낸다
    spec = {1: [(0, 1)] * 8,
            2: [(Fr(1, 2), 1), (3, 1)]}
    packets, wfq, fifo = simulate(spec, {1: 1, 2: 1})
    print("\n[2] 폭주하는 세션과 드문드문 보내는 세션 — 가중치 1:1")
    print_table(packets, wfq, fifo)
    for s in (1, 2):
        mine = [p for p in packets if p.session == s]
        print(f"  세션 {s} 평균 지연  WFQ {fmt(sum(wfq[id(p)] - p.arrival for p in mine) / len(mine))}"
              f"  FIFO {fmt(sum(fifo[id(p)] - p.arrival for p in mine) / len(mine))}")


def scenario_weights():
    # 두 세션이 동시에 12개씩 쌓아 두고 경쟁한다. 세션 2 의 버스트가 큐에 먼저 들어갔다
    spec = {1: [(0, 1)] * 12, 2: [(0, 1)] * 12}
    phi = {1: 3, 2: 1}
    packets = make(spec)
    run_gps(packets, phi)
    wfq = run_wfq(packets)
    # 도착 시각이 같으므로 FIFO 순서는 큐에 들어간 순서, 곧 세션 2 의 버스트가 먼저다
    fifo, t = {}, Fr(0)
    for p in sorted(packets, key=lambda p: p.session != 2):
        t += p.size
        fifo[id(p)] = t
    print("\n[3] 가중치 3:1 인 두 세션이 동시에 백로그 — 처음 8 시간 동안 보낸 패킷 수")
    for name, done in (("WFQ", wfq), ("FIFO", fifo)):
        sent = {s: sum(1 for p in packets if p.session == s and done[id(p)] <= 8) for s in (1, 2)}
        print(f"  {name:<4}  세션1(φ=3) {sent[1]}개  세션2(φ=1) {sent[2]}개")


if __name__ == "__main__":
    print(f"Python {platform.python_version()} / {platform.system()} {platform.release()}\n")
    scenario_paper_table1()
    scenario_greedy_flow()
    scenario_weights()
    sys.exit(0)
