"""PQ·WRR·DRR·WFQ 네 스케줄러를 같은 입력으로 돌려 바이트 몫과 DRR 적자 카운터를 계산한다.

모든 흐름이 시각 0에 충분히 쌓여 있고(backlogged) 계속 쌓여 있다고 둔다.
이 조건에서는 WFQ의 가상 시간 V(t)가 태그 순서에 영향을 주지 않으므로
태그를 F = F이전 + L/φ 로만 계산해도 전송 순서가 같다.
"""

from collections import deque


def make_queues(spec, count):
    """spec: {흐름: 패킷 길이 목록}. 목록을 count 번 반복해 백로그를 만든다."""
    return {flow: deque(sizes * count) for flow, sizes in spec.items()}


def run_pq(queues, order, budget):
    """엄격 우선순위. order 앞쪽이 높은 순위다."""
    sent = {flow: 0 for flow in queues}
    total = 0
    while total < budget:
        flow = next((f for f in order if queues[f]), None)
        if flow is None:
            break
        size = queues[flow].popleft()
        sent[flow] += size
        total += size
    return sent


def run_wrr(queues, weights, budget):
    """가중 라운드 로빈. 한 라운드에 흐름마다 weight 개의 '패킷'을 보낸다."""
    sent = {flow: 0 for flow in queues}
    total = 0
    while total < budget and any(queues.values()):
        for flow, weight in weights.items():
            for _ in range(weight):
                if not queues[flow] or total >= budget:
                    break
                size = queues[flow].popleft()
                sent[flow] += size
                total += size
    return sent


def run_drr(queues, quantum, budget, trace=False):
    """Shreedhar·Varghese 논문 Figure 4 의 의사코드를 그대로 옮겼다."""
    sent = {flow: 0 for flow in queues}
    deficit = {flow: 0 for flow in queues}
    active = deque(flow for flow in queues if queues[flow])
    total = 0
    round_no = 0
    remaining_in_round = 0
    while active and total < budget:
        if remaining_in_round == 0:
            # 라운드 = 이 시점의 ActiveList 를 한 바퀴 도는 것
            round_no += 1
            remaining_in_round = len(active)
        remaining_in_round -= 1
        flow = active.popleft()
        deficit[flow] += quantum[flow]
        before = deficit[flow]
        sent_now = []
        while deficit[flow] > 0 and queues[flow]:
            size = queues[flow][0]
            if size > deficit[flow]:
                break
            queues[flow].popleft()
            deficit[flow] -= size
            sent[flow] += size
            total += size
            sent_now.append(size)
        if not queues[flow]:
            deficit[flow] = 0  # 빈 큐는 적자를 들고 가지 않는다
        else:
            active.append(flow)
        if trace:
            left = list(queues[flow])
            print(f"  라운드 {round_no}  {flow}: 카운터 {before:4d} → 전송 {sent_now or '없음'}"
                  f" → 남은 카운터 {deficit[flow]:4d}  대기 {left or '비었음'}")
    return sent


def run_wfq(queues, weights, budget):
    """모든 흐름이 시각 0부터 백로그인 경우의 WFQ. 태그가 가장 작은 패킷부터 보낸다."""
    tagged = []
    for flow, packets in queues.items():
        finish = 0.0
        for seq, size in enumerate(packets):
            finish += size / weights[flow]
            tagged.append((finish, flow, seq, size))
    tagged.sort()
    sent = {flow: 0 for flow in queues}
    total = 0
    for _, flow, _, size in tagged:
        if total >= budget:
            break
        sent[flow] += size
        total += size
    return sent


def show_share(label, sent):
    total = sum(sent.values())
    parts = "  ".join(f"{flow} {byte:6d}B ({byte / total:6.1%})" for flow, byte in sent.items())
    print(f"  {label:<24} {parts}")


def scenario_packet_size():
    print("== 1. 패킷 길이가 다른 두 흐름, 가중치 1:1 ==")
    print("  A: 1500B 패킷, B: 100B 패킷. 링크가 30,000B 를 보낼 때까지의 몫")
    spec = {"A": [1500], "B": [100]}
    budget = 30_000
    show_share("PQ (A 우선)", run_pq(make_queues(spec, 400), ["A", "B"], budget))
    show_share("PQ (B 우선)", run_pq(make_queues(spec, 400), ["B", "A"], budget))
    show_share("WRR 1:1 (패킷 수)", run_wrr(make_queues(spec, 400), {"A": 1, "B": 1}, budget))
    show_share("DRR Quantum 1500:1500", run_drr(make_queues(spec, 400), {"A": 1500, "B": 1500}, budget))
    show_share("WFQ φ 1:1", run_wfq(make_queues(spec, 400), {"A": 1, "B": 1}, budget))
    print(f"  WRR 이론값: A:B = Max/Min = {1500 // 100}:1 → A {15 / 16:.1%}")
    print()


def scenario_weight():
    print("== 2. 같은 길이(1000B), 목표 비율 A:B:C = 3:2:1 ==")
    spec = {"A": [1000], "B": [1000], "C": [1000]}
    budget = 60_000
    show_share("WRR 3:2:1", run_wrr(make_queues(spec, 200), {"A": 3, "B": 2, "C": 1}, budget))
    show_share("DRR Quantum 3000:2000:1000",
               run_drr(make_queues(spec, 200), {"A": 3000, "B": 2000, "C": 1000}, budget))
    show_share("WFQ φ 3:2:1", run_wfq(make_queues(spec, 200), {"A": 3, "B": 2, "C": 1}, budget))
    print()
    print("== 2-1. 같은 목표 3:2:1 인데 C 만 패킷이 3000B ==")
    spec = {"A": [1000], "B": [1000], "C": [3000]}
    show_share("WRR 3:2:1", run_wrr(make_queues(spec, 200), {"A": 3, "B": 2, "C": 1}, budget))
    show_share("DRR Quantum 3000:2000:1000",
               run_drr(make_queues(spec, 200), {"A": 3000, "B": 2000, "C": 1000}, budget))
    show_share("WFQ φ 3:2:1", run_wfq(make_queues(spec, 200), {"A": 3, "B": 2, "C": 1}, budget))
    print()


def scenario_drr_trace():
    print("== 3. DRR 적자 카운터 추적, Quantum 500 ==")
    print("  Q1: 200, 750, 300   Q2: 500, 500   Q3: 1200 (Quantum 보다 크다)")
    queues = {"Q1": deque([200, 750, 300]), "Q2": deque([500, 500]), "Q3": deque([1200])}
    run_drr(queues, {"Q1": 500, "Q2": 500, "Q3": 500}, budget=10_000, trace=True)
    print()


if __name__ == "__main__":
    scenario_packet_size()
    scenario_weight()
    scenario_drr_trace()
