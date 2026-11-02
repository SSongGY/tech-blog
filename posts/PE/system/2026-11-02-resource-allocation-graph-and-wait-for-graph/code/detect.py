"""자원 할당 그래프를 대기 그래프로 줄이는 변환과, 다중 인스턴스 탐지 알고리즘을 검산한다.

교재(Silberschatz 10th ed. Ch.8)가 슬라이드로만 결론을 적어 둔 세 가지를
실제로 돌려서 확인한다.

  1. 단일 인스턴스 자원만 있는 자원 할당 그래프에서 대기 그래프를 유도하고
     사이클을 찾는다 (슬라이드 8.37~8.38)
  2. 다중 인스턴스 탐지 알고리즘으로 T0 스냅샷이 교착이 아님을 보인다 (8.40~8.42)
  3. P2 가 C 를 하나 더 요청한 뒤 교착이 되는 것을 보인다 (8.43)
"""

import sys


# ── 1. 단일 인스턴스: 자원 할당 그래프 → 대기 그래프 ────────────────────────

def wait_for_graph(holder, requests):
    """자원 할당 그래프를 대기 그래프로 줄인다.

    자원 노드를 들어내고, Pi -> Rj -> Pk 로 이어지던 두 간선을 Pi -> Pk 한 줄로 잇는다.
    자원마다 인스턴스가 하나뿐이어야 이 변환이 성립한다.
    """
    edges = set()
    for proc, wanted in requests.items():
        for resource in wanted:
            owner = holder.get(resource)
            if owner is not None and owner != proc:
                edges.add((proc, owner))
    return edges


def find_cycle(edges):
    """대기 그래프에서 사이클 하나를 찾아 경로로 돌려준다. 없으면 None."""
    adjacency = {}
    for src, dst in edges:
        adjacency.setdefault(src, []).append(dst)

    visiting, done = set(), set()
    path = []

    def walk(node):
        visiting.add(node)
        path.append(node)
        for nxt in sorted(adjacency.get(node, [])):
            if nxt in visiting:
                return path[path.index(nxt):] + [nxt]
            if nxt not in done:
                found = walk(nxt)
                if found:
                    return found
        visiting.discard(node)
        done.add(node)
        path.pop()
        return None

    for node in sorted(adjacency):
        if node not in done:
            found = walk(node)
            if found:
                return found
    return None


# ── 2. 다중 인스턴스: 탐지 알고리즘 (슬라이드 8.40~8.41) ──────────────────────

def detect(available, allocation, request, names):
    """Work/Finish 로 탐지 알고리즘을 돌리고 (환원 순서, 교착 프로세스)를 돌려준다.

    1단계 초기화에서 Allocation_i 가 0 인 프로세스는 Finish 를 곧바로 true 로 둔다.
    교재가 적어 둔 그대로이며, 이 한 줄이 뒤에서 결과를 가른다.
    """
    n, m = len(allocation), len(available)
    work = list(available)
    finish = [all(v == 0 for v in allocation[i]) for i in range(n)]
    order = []

    progressed = True
    while progressed:
        progressed = False
        for i in range(n):
            if finish[i]:
                continue
            if all(request[i][j] <= work[j] for j in range(m)):
                work = [work[j] + allocation[i][j] for j in range(m)]
                finish[i] = True
                order.append(names[i])
                progressed = True

    deadlocked = [names[i] for i in range(n) if not finish[i]]
    return order, deadlocked


def show_matrix(title, names, matrix, columns):
    print(f"  {title}")
    print("        " + "  ".join(f"{c:>2}" for c in columns))
    for name, row in zip(names, matrix):
        print(f"    {name}  " + "  ".join(f"{v:>2}" for v in row))


def main():
    print("=" * 62)
    print("1. 단일 인스턴스 — 자원 할당 그래프를 대기 그래프로 줄인다")
    print("=" * 62)

    holder = {"R1": "P2", "R2": "P3", "R3": "P1"}
    requests = {"P1": ["R1"], "P2": ["R2"], "P3": ["R3"]}

    print("  자원 할당 그래프")
    for resource, owner in sorted(holder.items()):
        print(f"    할당 간선  {resource} -> {owner}")
    for proc, wanted in sorted(requests.items()):
        for resource in wanted:
            print(f"    요청 간선  {proc} -> {resource}")

    edges = wait_for_graph(holder, requests)
    print("\n  대기 그래프 (자원 노드를 들어낸 결과)")
    for src, dst in sorted(edges):
        print(f"    {src} -> {dst}")

    cycle = find_cycle(edges)
    print(f"\n  사이클: {' -> '.join(cycle) if cycle else '없음'}")
    print(f"  판정: {'교착' if cycle else '교착 아님'}"
          "  (단일 인스턴스에서는 사이클이 곧 교착이다)")

    # 요청 하나를 거두면 사이클이 끊긴다
    requests_relaxed = {"P1": ["R1"], "P2": ["R2"], "P3": []}
    edges2 = wait_for_graph(holder, requests_relaxed)
    cycle2 = find_cycle(edges2)
    print("\n  P3 가 R3 요청을 거둔 경우")
    for src, dst in sorted(edges2):
        print(f"    {src} -> {dst}")
    print(f"  사이클: {' -> '.join(cycle2) if cycle2 else '없음'}")
    print(f"  판정: {'교착' if cycle2 else '교착 아님'}")

    print()
    print("=" * 62)
    print("2. 다중 인스턴스 — T0 스냅샷")
    print("=" * 62)

    names = ["P0", "P1", "P2", "P3", "P4"]
    columns = ["A", "B", "C"]
    available = [0, 0, 0]
    allocation = [
        [0, 1, 0],
        [2, 0, 0],
        [3, 0, 3],
        [2, 1, 1],
        [0, 0, 2],
    ]
    request_t0 = [
        [0, 0, 0],
        [2, 0, 2],
        [0, 0, 0],
        [1, 0, 0],
        [0, 0, 2],
    ]

    show_matrix("Allocation", names, allocation, columns)
    print()
    show_matrix("Request", names, request_t0, columns)
    print(f"\n  Available  {available}")

    order, deadlocked = detect(available, allocation, request_t0, names)
    print(f"\n  환원 순서: {' -> '.join(order)}")
    print(f"  교착 프로세스: {deadlocked if deadlocked else '없음'}")
    print(f"  판정: {'교착' if deadlocked else '교착 아님'}")

    print()
    print("=" * 62)
    print("3. 다중 인스턴스 — P2 가 C 를 하나 더 요청한 뒤")
    print("=" * 62)

    request_t1 = [row[:] for row in request_t0]
    request_t1[2] = [0, 0, 1]

    show_matrix("Request", names, request_t1, columns)
    print(f"\n  Available  {available}")

    order, deadlocked = detect(available, allocation, request_t1, names)
    print(f"\n  환원 순서: {' -> '.join(order) if order else '(없음)'}")
    print(f"  교착 프로세스: {deadlocked if deadlocked else '없음'}")
    print(f"  판정: {'교착' if deadlocked else '교착 아님'}")

    print()
    print("=" * 62)
    print("4. 초기화 한 줄이 가르는 것 — Allocation 이 0 인 프로세스")
    print("=" * 62)

    # P4 가 아무 자원도 쥐지 않은 채 C 를 2개 요청하는 상황
    names_b = ["P1", "P2", "P3"]
    allocation_b = [
        [0, 0, 3],
        [0, 0, 3],
        [0, 0, 0],
    ]
    request_b = [
        [0, 0, 3],
        [0, 0, 3],
        [0, 0, 2],
    ]
    show_matrix("Allocation", names_b, allocation_b, columns)
    print()
    show_matrix("Request", names_b, request_b, columns)
    print(f"\n  Available  {available}")

    order, deadlocked = detect(available, allocation_b, request_b, names_b)
    print(f"\n  환원 순서: {' -> '.join(order) if order else '(없음)'}")
    print(f"  교착 프로세스: {deadlocked if deadlocked else '없음'}")
    print("  P3 는 아무것도 못 받고 영원히 기다리지만 Allocation 이 0 이라")
    print("  1단계에서 Finish=true 로 들어가므로 교착 목록에 오르지 않는다.")

    print()
    print(f"파이썬 {sys.version.split()[0]}")


if __name__ == "__main__":
    main()
