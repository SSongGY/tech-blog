"""프로세스 3개의 송수신 사건에 램포트 시계와 벡터 시계를 매기고 검산한다.

1) 사건마다 램포트 값(IR1·IR2)과 벡터 값(Mattern §7)을 매긴다
2) 정답 "happened before" 를 사건 그래프의 도달 가능성으로 직접 구한다
3) 램포트: a→b 이면 L(a)<L(b) (Clock Condition) 은 늘 성립, 역은 성립하지 않음을 센다
4) 벡터: a→b ⟺ V(a)<V(b), a∥b ⟺ V(a)∥V(b) (Mattern 정리 10) 가 모든 쌍에서 맞는지 본다
5) 램포트 값 + 프로세스 번호로 만든 전순서(Lamport ⇒)
"""
from itertools import combinations

PROCESS_NAMES = ["P1", "P2", "P3"]

# 프로세스별 사건 순서. (사건 이름, 종류, 메시지 이름)
SCENARIO = {
    "P1": [("a1", "local", None), ("a2", "send", "m1"),
           ("a3", "local", None), ("a4", "recv", "m3")],
    "P2": [("b1", "local", None), ("b2", "recv", "m1"),
           ("b3", "send", "m2"), ("b4", "local", None)],
    "P3": [("c1", "local", None), ("c2", "local", None),
           ("c3", "recv", "m2"), ("c4", "send", "m3")],
}


def schedule():
    """수신은 송신이 끝난 뒤에만 처리할 수 있으므로 그 순서를 지켜 사건을 늘어놓는다."""
    cursor = {p: 0 for p in PROCESS_NAMES}
    sent = set()
    order = []
    while len(order) < sum(len(v) for v in SCENARIO.values()):
        progressed = False
        for p in PROCESS_NAMES:
            if cursor[p] == len(SCENARIO[p]):
                continue
            name, kind, message = SCENARIO[p][cursor[p]]
            if kind == "recv" and message not in sent:
                continue
            if kind == "send":
                sent.add(message)
            order.append((p, name, kind, message))
            cursor[p] += 1
            progressed = True
        if not progressed:
            raise RuntimeError("수신할 메시지가 없어 진행할 수 없다")
    return order


def assign_clocks(order):
    n = len(PROCESS_NAMES)
    lamport = {p: 0 for p in PROCESS_NAMES}
    vector = {p: [0] * n for p in PROCESS_NAMES}
    in_flight = {}  # 메시지 이름 -> (램포트 타임스탬프, 벡터 타임스탬프)
    stamps = {}
    for p, name, kind, message in order:
        i = PROCESS_NAMES.index(p)
        if kind == "recv":
            t_lamport, t_vector = in_flight[message]
            # IR1(현재보다 크게)과 IR2(b)(Tm 보다 크게)를 함께 만족하는 가장 작은 정수
            lamport[p] = max(lamport[p], t_lamport) + 1
            vector[p][i] += 1
            vector[p] = [max(x, y) for x, y in zip(vector[p], t_vector)]
        else:
            lamport[p] += 1
            vector[p][i] += 1
        if kind == "send":
            in_flight[message] = (lamport[p], list(vector[p]))
        stamps[name] = (p, kind, message, lamport[p], tuple(vector[p]))
    return stamps


def happened_before_truth():
    """Lamport 정의 3조건(같은 프로세스 순서·송수신·추이)으로 관계를 직접 만든다."""
    edges = set()
    senders = {}
    receivers = {}
    for p in PROCESS_NAMES:
        events = SCENARIO[p]
        for (a, _, _), (b, _, _) in zip(events, events[1:]):
            edges.add((a, b))
        for name, kind, message in events:
            if kind == "send":
                senders[message] = name
            elif kind == "recv":
                receivers[message] = name
    for message, sender in senders.items():
        edges.add((sender, receivers[message]))
    names = [e[0] for p in PROCESS_NAMES for e in SCENARIO[p]]
    reach = {(a, b) for a, b in edges}
    changed = True
    while changed:  # 추이 폐포
        changed = False
        for a, b in list(reach):
            for c, d in list(reach):
                if b == c and (a, d) not in reach:
                    reach.add((a, d))
                    changed = True
    return names, reach


def vector_less(u, v):
    return all(x <= y for x, y in zip(u, v)) and u != v


def main():
    order = schedule()
    stamps = assign_clocks(order)
    names, truth = happened_before_truth()

    print("== 1) 사건별 시계 값 (처리 순서대로) ==")
    print("  사건 | 프로세스 | 종류       | 램포트 | 벡터")
    for p, name, kind, message in order:
        _, _, _, lam, vec = stamps[name]
        label = kind if message is None else f"{kind} {message}"
        print(f"  {name:<4} | {p:<8} | {label:<10} | {lam:>6} | {vec}")
    print()

    pairs = list(combinations(names, 2))
    causal = [(a, b) for a, b in pairs if (a, b) in truth or (b, a) in truth]
    concurrent = [(a, b) for a, b in pairs if (a, b) not in causal]
    print("== 2) 정답 관계 (그래프 도달 가능성) ==")
    print(f"  사건 {len(names)}개 · 쌍 {len(pairs)}개 · 인과 {len(causal)}쌍 · 동시 {len(concurrent)}쌍")
    print()

    print("== 3) 램포트 시계 ==")
    clock_condition = all(stamps[a][3] < stamps[b][3] for a, b in truth)
    print(f"  a→b 인 {len(truth)}쌍 모두 L(a)<L(b) (Clock Condition): {clock_condition}")
    misleading = []
    for a, b in concurrent:
        la, lb = stamps[a][3], stamps[b][3]
        if la != lb:
            misleading.append((a, b) if la < lb else (b, a))
    same = [(a, b) for a, b in concurrent if stamps[a][3] == stamps[b][3]]
    print(f"  동시 {len(concurrent)}쌍 중 램포트 값이 다른 쌍: {len(misleading)}  같은 쌍: {len(same)}")
    for x, y in misleading[:4]:
        print(f"    {x}({stamps[x][3]}) < {y}({stamps[y][3]}) 이지만 {x}→{y} 아님")
    print(f"    같은 값 예: {same[:3]}")
    print()

    print("== 4) 벡터 시계 (Mattern 정리 10 검산) ==")
    mismatch = 0
    for a, b in pairs:
        va, vb = stamps[a][4], stamps[b][4]
        by_vector = "a→b" if vector_less(va, vb) else "b→a" if vector_less(vb, va) else "∥"
        by_truth = "a→b" if (a, b) in truth else "b→a" if (b, a) in truth else "∥"
        if by_vector != by_truth:
            mismatch += 1
    print(f"  {len(pairs)}쌍 비교 · 정답과 다른 쌍: {mismatch}")
    for a, b in [("a3", "b4"), ("a1", "c4"), ("b1", "c2")]:
        va, vb = stamps[a][4], stamps[b][4]
        verdict = "→" if vector_less(va, vb) else "←" if vector_less(vb, va) else "∥"
        print(f"    {a}{va} {verdict} {b}{vb}")
    print()

    print("== 5) 전순서 ⇒ (램포트 값, 같으면 프로세스 번호) ==")
    total = sorted(names, key=lambda e: (stamps[e][3], PROCESS_NAMES.index(stamps[e][0])))
    print("  " + " ⇒ ".join(f"{e}({stamps[e][3]})" for e in total))
    respects = all(total.index(a) < total.index(b) for a, b in truth)
    print(f"  모든 a→b 가 전순서에서도 앞선다: {respects}")


if __name__ == "__main__":
    main()
