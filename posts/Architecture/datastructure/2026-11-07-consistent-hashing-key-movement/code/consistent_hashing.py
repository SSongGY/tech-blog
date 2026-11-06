"""나머지 분배·해시 링·가상 노드를 같은 키 10만 개에 돌려
노드를 더하거나 뺄 때 옮겨지는 키와 노드별 부하를 잰다.

1) 나머지 분배 hash % N — N 이 바뀌면 거의 모든 키가 움직인다
2) 해시 링(노드당 점 1개) — 움직이는 키는 새 노드 몫뿐이지만 부하가 고르지 않다
3) 가상 노드 — 노드당 점을 늘리면 부하 편차가 줄어든다
4) 노드 하나가 빠질 때 그 키를 받아 가는 노드 수
"""
import bisect
import hashlib
import statistics

KEY_COUNT = 100_000
NODE_COUNT = 10
KEYS = ["user:%d" % i for i in range(KEY_COUNT)]


def hash64(text):
    # 실행마다 바뀌는 파이썬 내장 hash() 대신 md5 앞 8바이트를 쓴다 — 결과가 재현된다
    return int.from_bytes(hashlib.md5(text.encode()).digest()[:8], "big")


KEY_HASHES = [hash64(k) for k in KEYS]


class ModuloRouter:
    def __init__(self, nodes):
        self.nodes = list(nodes)

    def route(self, key_hash):
        return self.nodes[key_hash % len(self.nodes)]


class HashRing:
    """링 위에서 키 위치의 시계 방향 첫 점이 그 키의 노드다 (Dynamo §4.2)."""

    def __init__(self, nodes, vnode_count=1):
        points = []
        for node in nodes:
            for v in range(vnode_count):
                points.append((hash64("%s#%d" % (node, v)), node))
        points.sort()
        self.positions = [p for p, _ in points]
        self.owners = [n for _, n in points]

    def route(self, key_hash):
        i = bisect.bisect_right(self.positions, key_hash)
        return self.owners[i % len(self.owners)]


def assign(router):
    return [router.route(h) for h in KEY_HASHES]


def node_names(count):
    return ["node-%02d" % i for i in range(count)]


def load_summary(assignment, nodes):
    counts = [0] * len(nodes)
    index = {n: i for i, n in enumerate(nodes)}
    for node in assignment:
        counts[index[node]] += 1
    mean = len(assignment) / len(nodes)
    return {
        "min": min(counts),
        "max": max(counts),
        "max_over_mean": max(counts) / mean,
        "cv": statistics.pstdev(counts) / mean,
    }


def movement(before, after, new_node):
    moved = sum(1 for a, b in zip(before, after) if a != b)
    to_new = sum(1 for a, b in zip(before, after) if a != b and b == new_node)
    return moved, to_new


def section_add_node():
    print("== 1)~3) 노드 %d개 → %d개, 키 %d개 ==" % (NODE_COUNT, NODE_COUNT + 1, KEY_COUNT))
    print("  이상적인 이동 비율 1/%d = %.2f%%" % (NODE_COUNT + 1, 100 / (NODE_COUNT + 1)))
    print("  방식              | 이동 키 | 이동 비율 | 새 노드로 | 노드 사이 | 최대/평균 | 변동계수")
    old_nodes = node_names(NODE_COUNT)
    new_nodes = node_names(NODE_COUNT + 1)
    new_node = new_nodes[-1]
    cases = [("나머지 hash % N", lambda ns: ModuloRouter(ns))]
    for v in (1, 10, 100, 1000):
        cases.append(("링 가상노드 %4d" % v, lambda ns, v=v: HashRing(ns, v)))
    for label, make in cases:
        before = assign(make(old_nodes))
        after = assign(make(new_nodes))
        moved, to_new = movement(before, after, new_node)
        load = load_summary(before, old_nodes)
        print("  %-17s | %7d | %8.2f%% | %9d | %9d | %9.2f | %7.3f"
              % (label, moved, 100 * moved / KEY_COUNT, to_new, moved - to_new,
                 load["max_over_mean"], load["cv"]))
    print()


def section_remove_node():
    print("== 4) node-03 이 빠질 때 그 키를 받아 가는 노드 ==")
    nodes = node_names(NODE_COUNT)
    remaining = [n for n in nodes if n != "node-03"]
    for v in (1, 10, 100):
        before = assign(HashRing(nodes, v))
        after = assign(HashRing(remaining, v))
        receivers = {}
        for a, b in zip(before, after):
            if a == "node-03":
                receivers[b] = receivers.get(b, 0) + 1
        moved_elsewhere = sum(1 for a, b in zip(before, after) if a != b and a != "node-03")
        share = sorted(receivers.values(), reverse=True)
        print("  가상노드 %3d: 넘겨받은 노드 %d개, 가장 많이 받은 노드 %d키 / 전체 %d키, "
              "다른 키 이동 %d"
              % (v, len(receivers), share[0], sum(share), moved_elsewhere))
    print()


def section_ring_size():
    print("== 5) 링의 점 개수 ==")
    for v in (1, 100, 1000):
        ring = HashRing(node_names(NODE_COUNT), v)
        print("  가상노드 %4d: 점 %6d개" % (v, len(ring.positions)))
    print()


def main():
    print("  키 해시: md5 앞 8바이트, 키 이름 user:0 ~ user:%d" % (KEY_COUNT - 1))
    print()
    section_add_node()
    section_remove_node()
    section_ring_size()


if __name__ == "__main__":
    main()
