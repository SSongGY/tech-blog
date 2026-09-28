"""거리벡터와 링크상태 — 링크 하나가 끊겼을 때 몇 라운드 만에 바로잡히는가.

동기 라운드 모델이다. 한 라운드에 모든 라우터가 이웃에게 한 번씩 알리고, 받은 것으로
경로를 다시 계산한다. RIP 의 타이머(30초 주기, triggered update)는 넣지 않았다.
라운드 수를 세어 두 방식이 수렴하는 방식의 차이를 본다.

- 거리벡터: 이웃이 알린 거리 + 링크 비용의 최솟값 (분산 Bellman-Ford). 무한은 16 (RFC 2453)
- 링크상태: 끊긴 링크 양 끝이 새 LSA 를 만들고, LSA 는 한 라운드에 한 홉씩 퍼진다.
  LSA 를 받은 라우터는 자기 데이터베이스로 최단 경로 트리를 다시 계산한다 (Dijkstra)
"""

import heapq

INFINITY = 16  # RFC 2453 §3.4.1 — 도달 불가를 뜻하는 메트릭
MAX_ROUNDS = 40


def neighbors_of(links: dict[frozenset, int], node: str) -> dict[str, int]:
    result = {}
    for pair, cost in links.items():
        if node in pair:
            (other,) = pair - {node}
            result[other] = cost
    return result


# ---------------------------------------------------------------- 거리벡터


def advertise(table: dict, to_node: str, mode: str) -> dict[str, int]:
    """table: {목적지: (거리, 다음 홉)} 을 to_node 에게 알릴 벡터로 바꾼다."""
    vector = {}
    for dest, (dist, next_hop) in table.items():
        if next_hop == to_node and mode == "split-horizon":
            continue  # 그 이웃에게서 배운 경로는 그 이웃에게 알리지 않는다
        if next_hop == to_node and mode == "poisoned-reverse":
            vector[dest] = INFINITY  # 알리되 무한으로 알린다
            continue
        vector[dest] = dist
    return vector


def recompute(node: str, links: dict, received: dict) -> dict:
    table = {node: (0, node)}
    for neighbor, cost in neighbors_of(links, node).items():
        for dest, dist in received.get(neighbor, {}).items():
            if dest == node:
                continue
            candidate = min(dist + cost, INFINITY)
            if candidate >= INFINITY:
                # 도달 불가 경로는 다음 홉을 두지 않는다. 두면 무한끼리 다음 홉만
                # 바뀌어도 변화로 잡혀 수렴 판정이 흔들린다
                table.setdefault(dest, (INFINITY, "-"))
                continue
            best = table.get(dest)
            # 같은 거리면 이름 순으로 고정해 결과가 흔들리지 않게 한다
            if best is None or (candidate, neighbor) < best:
                table[dest] = (candidate, neighbor)
    return table


def run_distance_vector(
    nodes: list[str], links: dict, broken: frozenset, dest: str, mode: str
) -> None:
    tables = {n: {n: (0, n)} for n in nodes}
    for _ in range(MAX_ROUNDS):  # 끊기기 전 상태로 먼저 수렴시킨다
        received = {
            n: {m: advertise(tables[n], m, mode) for m in neighbors_of(links, n)}
            for n in nodes
        }
        tables = {
            n: recompute(n, links, {m: received[m][n] for m in neighbors_of(links, n)})
            for n in nodes
        }

    links = {pair: c for pair, c in links.items() if pair != broken}
    print(f"  라운드 0 (끊긴 직후): " + fmt_dv(tables, nodes, dest))
    for round_no in range(1, MAX_ROUNDS + 1):
        received = {
            n: {m: advertise(tables[n], m, mode) for m in neighbors_of(links, n)}
            for n in nodes
        }
        new_tables = {
            n: recompute(n, links, {m: received[m][n] for m in neighbors_of(links, n)})
            for n in nodes
        }
        changed = routing_state(new_tables, nodes) != routing_state(tables, nodes)
        tables = new_tables
        if changed:
            print(f"  라운드 {round_no:>2}: " + fmt_dv(tables, nodes, dest))
        else:
            print(f"  -> 라운드 {round_no - 1} 이후 변화 없음 (수렴)")
            return
    print(f"  -> {MAX_ROUNDS} 라운드 안에 수렴하지 않음")


def routing_state(tables: dict, nodes: list[str]) -> dict:
    # 항목이 없는 것과 무한인 것은 같은 상태다. 알려 준 이웃이 없어 항목이 빠진
    # 라운드와 누가 16을 알려 준 라운드를 다른 상태로 세지 않는다
    return {
        n: {d: tables[n].get(d, (INFINITY, "-")) for d in nodes} for n in nodes
    }


def fmt_dv(tables: dict, nodes: list[str], dest: str) -> str:
    cells = []
    for n in nodes:
        if n == dest:
            continue
        dist, next_hop = tables[n].get(dest, (INFINITY, "-"))
        shown = "무한" if dist >= INFINITY else f"{dist}({next_hop})"
        cells.append(f"{n}→{dest}={shown}")
    return "  ".join(cells)


# ---------------------------------------------------------------- 링크상태


def dijkstra(links: dict, source: str) -> dict[str, int]:
    dist = {source: 0}
    heap = [(0, source)]
    while heap:
        d, node = heapq.heappop(heap)
        if d > dist.get(node, float("inf")):
            continue
        for other, cost in neighbors_of(links, node).items():
            if d + cost < dist.get(other, float("inf")):
                dist[other] = d + cost
                heapq.heappush(heap, (d + cost, other))
    return dist


def run_link_state(nodes: list[str], links: dict, broken: frozenset, dest: str) -> None:
    after = {pair: c for pair, c in links.items() if pair != broken}
    knows_failure = set(broken)  # 끊긴 링크의 양 끝은 바로 안다
    print(f"  라운드 0 (끊긴 직후): LSA 보유 {sorted(knows_failure)}  " + fmt_ls(
        nodes, links, after, knows_failure, dest))
    for round_no in range(1, MAX_ROUNDS + 1):
        # 새 LSA 를 가진 라우터가 모든 이웃에게 넘긴다 — 한 라운드에 한 홉
        reached = {m for n in knows_failure for m in neighbors_of(after, n)}
        if reached <= knows_failure:
            print(f"  -> 라운드 {round_no - 1} 이후 변화 없음 (수렴)")
            return
        knows_failure |= reached
        print(f"  라운드 {round_no:>2}: LSA 보유 {sorted(knows_failure)}  " + fmt_ls(
            nodes, links, after, knows_failure, dest))


def fmt_ls(nodes, before, after, knows_failure, dest) -> str:
    cells = []
    for n in nodes:
        if n == dest:
            continue
        view = after if n in knows_failure else before
        dist = dijkstra(view, n).get(dest)
        cells.append(f"{n}→{dest}={'무한' if dist is None else dist}")
    return "  ".join(cells)


# ---------------------------------------------------------------- 시나리오


def link(a: str, b: str) -> frozenset:
    return frozenset((a, b))


def main() -> None:
    line_nodes = ["A", "B", "D"]
    line_links = {link("A", "B"): 1, link("B", "D"): 1}
    print("== 1. 선형 A - B - D, B-D 링크가 끊긴다 ==")
    for mode in ("none", "split-horizon", "poisoned-reverse"):
        print(f"\n[1-{mode}] 거리벡터")
        run_distance_vector(line_nodes, line_links, link("B", "D"), "D", mode)
    print("\n[1-link-state] 링크상태")
    run_link_state(line_nodes, line_links, link("B", "D"), "D")

    tri_nodes = ["A", "B", "C", "D"]
    tri_links = {link("A", "B"): 1, link("A", "C"): 1, link("B", "C"): 1,
                 link("C", "D"): 1}
    print("\n== 2. 삼각형 A-B-C 에 C - D, C-D 링크가 끊긴다 ==")
    for mode in ("split-horizon", "poisoned-reverse"):
        print(f"\n[2-{mode}] 거리벡터")
        run_distance_vector(tri_nodes, tri_links, link("C", "D"), "D", mode)
    print("\n[2-link-state] 링크상태")
    run_link_state(tri_nodes, tri_links, link("C", "D"), "D")


if __name__ == "__main__":
    main()
