"""맥케이브 순환복잡도를 세 가지 방법으로 계산해 같은 값이 나오는지 검산한다.

1) 제어 흐름 그래프에서 V(G) = E - N + 2P
2) 이진 판단 노드 수 p 에서 V(G) = p + 1
3) 소스 코드의 판단 구문을 세는 방법 (ast)
그리고 기본 경로(선형 독립 경로)의 수가 V(G) 와 같은지, 전체 경로 수와는
얼마나 다른지 본다. 외부 의존성 없이 표준 라이브러리만 쓴다.
"""

import ast
import platform
import sys
from fractions import Fraction

SAMPLE_SOURCE = '''
def classify_order(order, stock):
    if not order.items:
        return "empty"
    total = 0
    for item in order.items:
        if item.qty > stock.get(item.sku, 0) and not item.backorder:
            return "short"
        total += item.price * item.qty
    while total > LIMIT:
        total -= DISCOUNT
    return "ok"
'''

# 위 함수의 제어 흐름 그래프. and 는 단락 평가라 조건 노드를 둘로 나눈다.
NODES = {
    1: "if not order.items",
    2: 'return "empty"',
    3: "total = 0",
    4: "for item in order.items",
    5: "item.qty > stock.get(...)",
    6: "not item.backorder",
    7: 'return "short"',
    8: "total += ...",
    9: "while total > LIMIT",
    10: "total -= DISCOUNT",
    11: 'return "ok"',
    12: "(exit)",
}
EDGES = [
    (1, 2), (1, 3), (2, 12), (3, 4), (4, 5), (4, 9), (5, 6), (5, 8),
    (6, 7), (6, 8), (7, 12), (8, 4), (9, 10), (9, 11), (10, 9), (11, 12),
]
ENTRY, EXIT = 1, 12


def count_decisions(source):
    """소스에서 판단 지점을 센다. 단락 평가 and/or 는 피연산자 수 - 1 만큼 더한다."""
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.If, ast.For, ast.While, ast.IfExp)):
            found.append(type(node).__name__)
        elif isinstance(node, ast.ExceptHandler):
            found.append("except")
        elif isinstance(node, ast.BoolOp):
            op = "and" if isinstance(node.op, ast.And) else "or"
            found.extend([op] * (len(node.values) - 1))
        elif isinstance(node, ast.comprehension):
            found.extend(["comprehension-if"] * len(node.ifs))
    return found


def successors(edges):
    out = {}
    for src, dst in edges:
        out.setdefault(src, []).append(dst)
    return out


def enumerate_paths(edges, entry, exit_node, max_visits=2):
    # 루프 때문에 경로가 무한하므로 노드당 방문 횟수를 묶는다.
    # 기본 경로를 이루는 데는 루프를 0회·1회 도는 경로면 충분하다.
    out = successors(edges)
    paths = []

    def walk(node, path, visits):
        if node == exit_node:
            paths.append(path)
            return
        for nxt in out.get(node, []):
            if visits.get(nxt, 0) < max_visits:
                visits[nxt] = visits.get(nxt, 0) + 1
                walk(nxt, path + [nxt], visits)
                visits[nxt] -= 1

    walk(entry, [entry], {entry: 1})
    return paths


def edge_vector(path, edges):
    index = {edge: i for i, edge in enumerate(edges)}
    vector = [0] * len(edges)
    for a, b in zip(path, path[1:]):
        vector[index[(a, b)]] += 1
    return vector


def rank(vectors):
    rows = [[Fraction(v) for v in vec] for vec in vectors]
    result, col_count = 0, len(rows[0]) if rows else 0
    for col in range(col_count):
        pivot = next((r for r in range(result, len(rows)) if rows[r][col] != 0), None)
        if pivot is None:
            continue
        rows[result], rows[pivot] = rows[pivot], rows[result]
        for r in range(len(rows)):
            if r != result and rows[r][col] != 0:
                factor = rows[r][col] / rows[result][col]
                rows[r] = [x - factor * y for x, y in zip(rows[r], rows[result])]
        result += 1
    return result


def pick_basis(paths, edges):
    # 짧은 경로부터 넣어 보며 랭크가 오를 때만 채택한다.
    basis, vectors = [], []
    for path in sorted(paths, key=len):
        candidate = vectors + [edge_vector(path, edges)]
        if rank(candidate) > len(vectors):
            basis.append(path)
            vectors = candidate
    return basis


def sequential_ifs(count):
    """if 문 count 개가 이어진 함수의 그래프. 노드 i 에서 갈라졌다 i+1 에서 합류한다."""
    edges, node = [], 0
    for _ in range(count):
        branch, join = node + 1, node + 2
        edges += [(node, branch), (branch, join), (node, join)]
        node = join
    return edges, 0, node


def count_dag_paths(edges, entry, exit_node):
    out = successors(edges)
    memo = {}

    def ways(node):
        if node == exit_node:
            return 1
        if node not in memo:
            memo[node] = sum(ways(nxt) for nxt in out.get(node, []))
        return memo[node]

    return ways(entry)


def main():
    print(f"Python {platform.python_version()} / {platform.system()}")
    print("검산 대상 함수:")
    print(SAMPLE_SOURCE.strip("\n"))

    print("\n[1] 제어 흐름 그래프에서 V(G) = E - N + 2P")
    for number, label in NODES.items():
        print(f"  n{number:<2} {label}")
    print("  간선: " + ", ".join(f"{a}->{b}" for a, b in EDGES))
    edge_count, node_count = len(EDGES), len(NODES)
    print(f"  E = {edge_count}, N = {node_count}, P = 1  ->  V(G) = {edge_count - node_count + 2}")

    print("\n[2] 이진 판단 노드 수 p 에서 V(G) = p + 1")
    out = successors(EDGES)
    predicates = [n for n in NODES if len(out.get(n, [])) == 2]
    print(f"  출구가 2개인 노드: {predicates}  ->  p = {len(predicates)}, V(G) = {len(predicates) + 1}")

    print("\n[3] 소스 코드의 판단 구문을 센다 (ast)")
    found = count_decisions(SAMPLE_SOURCE)
    print(f"  판단 지점: {found}  ->  V(G) = {len(found) + 1}")
    without_and = [d for d in found if d not in ("and", "or")]
    print(f"  and/or 를 세지 않으면 V(G) = {len(without_and) + 1}  (단락 평가 분기를 놓친다)")

    print("\n[4] 기본 경로 — 선형 독립인 진입-종료 경로의 최대 개수")
    paths = enumerate_paths(EDGES, ENTRY, EXIT)
    vectors = [edge_vector(p, EDGES) for p in paths]
    print(f"  루프를 최대 1회 도는 경로 {len(paths)}개, 간선 벡터의 랭크 = {rank(vectors)}")
    for i, path in enumerate(pick_basis(paths, EDGES), start=1):
        print(f"  B{i}: " + " -> ".join(str(n) for n in path))

    print("\n[5] 이어진 if 문 k 개: 전체 경로 수와 V(G)")
    print(f"{'k':>4} {'V(G)':>6} {'전체 경로 수':>14}")
    for count in (1, 3, 5, 10, 20):
        edges, entry, exit_node = sequential_ifs(count)
        nodes = {n for e in edges for n in e}
        complexity = len(edges) - len(nodes) + 2
        print(f"{count:>4} {complexity:>6} {count_dag_paths(edges, entry, exit_node):>14}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
