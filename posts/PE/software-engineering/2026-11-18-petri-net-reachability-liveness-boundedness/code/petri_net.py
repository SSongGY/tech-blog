"""페트리 넷의 발화 규칙, 도달성 그래프, 유계성·활성·가역성, 코버러빌리티 트리를 계산한다.

근거: Murata (1989) Petri Nets: Properties, Analysis and Applications
  - Table 2 형식 정의, 발화 규칙 (p.543)
  - IV 절 행위 속성: 도달성, 유계성, 활성 L0~L4, 가역성 (p.547-548)
  - V-A 코버러빌리티 트리 알고리즘 (p.550), V-B 결합 행렬과 상태 방정식 (p.551-552)

[1] 상호 배제 넷   — 도달 마킹, 안전성, L4 활성, 가역성, S-불변식
[2] 교착 넷        — 자원 둘을 반대 순서로 잡으면 죽은 마킹이 생긴다
[3] 순서 통일 넷   — 같은 순서로 잡으면 죽은 마킹이 사라진다
[4] 무한 넷        — 코버러빌리티 트리에 ω 가 나타나는지 (Murata 의 예와 대조)
"""
from collections import deque

OMEGA = float("inf")


class PetriNet:
    def __init__(self, places, transitions):
        # transitions: {이름: (입력 {플레이스: 가중치}, 출력 {플레이스: 가중치})}
        self.places = places
        self.transitions = transitions

    def enabled(self, marking, name):
        pre, _ = self.transitions[name]
        return all(marking[self.places.index(p)] >= w for p, w in pre.items())

    def fire(self, marking, name):
        pre, post = self.transitions[name]
        result = list(marking)
        for p, w in pre.items():
            result[self.places.index(p)] -= w
        for p, w in post.items():
            result[self.places.index(p)] += w
        return tuple(result)

    def enabled_list(self, marking):
        return [t for t in self.transitions if self.enabled(marking, t)]

    def reachability_graph(self, initial):
        """유계 넷 전용. 모든 도달 마킹과 발화 간선을 너비 우선으로 모은다."""
        edges = {initial: []}
        queue = deque([initial])
        while queue:
            marking = queue.popleft()
            for t in self.enabled_list(marking):
                nxt = self.fire(marking, t)
                edges[marking].append((t, nxt))
                if nxt not in edges:
                    edges[nxt] = []
                    queue.append(nxt)
        return edges

    def incidence_matrix(self):
        """a_ij = w(t_i, p_j) - w(p_j, t_i). 행이 트랜지션, 열이 플레이스 (Murata V-B)."""
        rows = []
        for name in self.transitions:
            pre, post = self.transitions[name]
            rows.append([post.get(p, 0) - pre.get(p, 0) for p in self.places])
        return rows


def can_reach(edges, sources, targets):
    """sources 의 각 마킹에서 targets 중 하나로 갈 수 있는지."""
    reverse = {m: [] for m in edges}
    for m, outs in edges.items():
        for _, nxt in outs:
            reverse[nxt].append(m)
    seen = set(targets)
    queue = deque(targets)
    while queue:
        m = queue.popleft()
        for prev in reverse[m]:
            if prev not in seen:
                seen.add(prev)
                queue.append(prev)
    return all(m in seen for m in sources)


def analyze(net, initial, title):
    print(f"\n{title}")
    print("  플레이스:", ", ".join(net.places))
    print("  M0 =", initial)
    edges = net.reachability_graph(initial)
    markings = list(edges)
    print(f"  도달 마킹 {len(markings)}개")
    for m in markings:
        outs = ", ".join(f"{t}->{n}" for t, n in edges[m]) or "(발화 가능 없음)"
        print(f"    {m}  {outs}")

    bound = max(max(m) for m in markings)
    print(f"  유계성: {bound}-유계" + (" (안전)" if bound <= 1 else ""))

    dead = [m for m in markings if not edges[m]]
    print("  죽은 마킹:", dead if dead else "없음")

    fired = {t for outs in edges.values() for t, _ in outs}
    for t in net.transitions:
        enabling = [m for m in markings if net.enabled(m, t)]
        if t not in fired:
            level = "L0 (죽음)"
        elif can_reach(edges, markings, enabling):
            level = "L4 (활성)"
        else:
            level = "L1 이상, L4 아님"
        print(f"    {t}: {level}")

    reversible = can_reach(edges, markings, [initial])
    print("  가역성:", "있음" if reversible else "없음")
    return edges


def check_invariant(net, edges, weights):
    matrix = net.incidence_matrix()
    product = [sum(a * y for a, y in zip(row, weights)) for row in matrix]
    print("  결합 행렬 A (행=트랜지션, 열=플레이스)")
    for name, row in zip(net.transitions, matrix):
        print(f"    {name:8s} {row}")
    print("  y =", weights, " A·y =", product)
    sums = {sum(m * y for m, y in zip(marking, weights)) for marking in edges}
    print("  모든 도달 마킹에서 y·M 값:", sorted(sums))


def coverability_tree(net, initial):
    """Murata V-A 의 알고리즘. 경로 위 조상보다 크거나 같으면 커진 자리를 ω 로 바꾼다."""
    print("  코버러빌리티 트리 (부모 -[트랜지션]-> 자식, 꼬리표)")
    stack = [(initial, [initial])]
    while stack:
        marking, path = stack.pop()
        for t in net.enabled_list(marking):
            child = list(net.fire(marking, t))
            for ancestor in path:
                if all(c >= a for c, a in zip(child, ancestor)) and tuple(child) != ancestor:
                    child = [OMEGA if c > a else c for c, a in zip(child, ancestor)]
            child = tuple(child)
            if child in path:
                tag = "old"
            elif not net.enabled_list(child):
                tag = "dead-end"
            else:
                tag = "new"
                stack.append((child, path + [child]))
            print(f"    {show(marking)} -[{t}]-> {show(child)}  {tag}")


def show(marking):
    return "(" + " ".join("ω" if v == OMEGA else str(v) for v in marking) + ")"


def main():
    mutex = PetriNet(
        ["idle1", "cs1", "idle2", "cs2", "mutex"],
        {
            "enter1": ({"idle1": 1, "mutex": 1}, {"cs1": 1}),
            "exit1": ({"cs1": 1}, {"idle1": 1, "mutex": 1}),
            "enter2": ({"idle2": 1, "mutex": 1}, {"cs2": 1}),
            "exit2": ({"cs2": 1}, {"idle2": 1, "mutex": 1}),
        },
    )
    edges = analyze(mutex, (1, 0, 1, 0, 1), "[1] 상호 배제 넷")
    check_invariant(mutex, edges, [0, 1, 0, 1, 1])

    places = ["idle1", "a1", "ab1", "idle2", "b2", "ba2", "res_a", "res_b"]
    opposite = PetriNet(
        places,
        {
            "p1_get_a": ({"idle1": 1, "res_a": 1}, {"a1": 1}),
            "p1_get_b": ({"a1": 1, "res_b": 1}, {"ab1": 1}),
            "p1_release": ({"ab1": 1}, {"idle1": 1, "res_a": 1, "res_b": 1}),
            "p2_get_b": ({"idle2": 1, "res_b": 1}, {"b2": 1}),
            "p2_get_a": ({"b2": 1, "res_a": 1}, {"ba2": 1}),
            "p2_release": ({"ba2": 1}, {"idle2": 1, "res_a": 1, "res_b": 1}),
        },
    )
    start = (1, 0, 0, 1, 0, 0, 1, 1)
    analyze(opposite, start, "[2] 교착 넷 — P1 은 a→b, P2 는 b→a 순서로 잡는다")

    same_order = PetriNet(
        places,
        {
            "p1_get_a": ({"idle1": 1, "res_a": 1}, {"a1": 1}),
            "p1_get_b": ({"a1": 1, "res_b": 1}, {"ab1": 1}),
            "p1_release": ({"ab1": 1}, {"idle1": 1, "res_a": 1, "res_b": 1}),
            # P2 도 a 를 먼저 잡는다. b2 는 'a 를 쥔 상태'로 이름만 그대로 쓴다
            "p2_get_a": ({"idle2": 1, "res_a": 1}, {"b2": 1}),
            "p2_get_b": ({"b2": 1, "res_b": 1}, {"ba2": 1}),
            "p2_release": ({"ba2": 1}, {"idle2": 1, "res_a": 1, "res_b": 1}),
        },
    )
    analyze(same_order, start, "[3] 순서 통일 넷 — 둘 다 a→b 순서로 잡는다")

    print("\n[4] 무한 넷 — t3 가 발화할 때마다 p2 에 토큰이 쌓인다")
    unbounded = PetriNet(
        ["p1", "p2", "p3"],
        {
            "t1": ({"p1": 1}, {"p3": 1}),
            "t2": ({"p2": 1, "p3": 1}, {"p3": 1}),
            "t3": ({"p1": 1}, {"p1": 1, "p2": 1}),
        },
    )
    coverability_tree(unbounded, (1, 0, 0))


if __name__ == "__main__":
    main()
