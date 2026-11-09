"""Apriori 와 FP-growth 로 같은 거래 데이터의 빈발 항목집합을 찾고 비용을 비교한다.

Apriori 는 Agrawal·Srikant(VLDB 1994) Figure 1 과 §2.1.1 apriori-gen(join·prune)을,
FP-growth 는 Han·Pei·Yin(SIGMOD 2000) §2 FP-tree 구축과 §3 조건부 패턴 기반 채굴을 옮겼다.
예제 거래는 FP-growth 논문 Table 1(거래 5건, 최소 지지 개수 3)이다.
"""
from collections import Counter, defaultdict
from itertools import combinations

TRANSACTIONS = [
    "f a c d g i m p",
    "a b c f l m o",
    "b f h j o",
    "b c k s p",
    "a f c e l p m n",
]
MIN_SUPPORT = 3  # 논문처럼 비율이 아니라 거래 건수로 센다


class Scanner:
    """데이터베이스를 몇 번 훑었는지 센다."""

    def __init__(self, transactions):
        self.transactions = [frozenset(t.split()) for t in transactions]
        self.scans = 0

    def scan(self):
        self.scans += 1
        return iter(self.transactions)


def fmt(itemset):
    return "{" + ",".join(sorted(itemset)) + "}"


def apriori_gen(prev_large, k):
    """join: 앞 k-2 개가 같은 두 집합을 잇는다. prune: (k-1) 부분집합이 하나라도 빈발하지 않으면 지운다."""
    ordered = sorted(tuple(sorted(s)) for s in prev_large)
    joined = []
    for i, p in enumerate(ordered):
        for q in ordered[i + 1:]:
            if p[:k - 2] == q[:k - 2] and p[k - 2] < q[k - 2]:
                joined.append(frozenset(p + (q[k - 2],)))
    pruned = [c for c in joined
              if all(frozenset(s) in prev_large for s in combinations(sorted(c), k - 1))]
    return joined, pruned


def apriori(db, verbose=True):
    counts = Counter(item for t in db.scan() for item in t)
    large = {frozenset([i]): n for i, n in counts.items() if n >= MIN_SUPPORT}
    result = dict(large)
    counted = len(counts)
    if verbose:
        print(f"1회차: 항목 {len(counts)}개를 세어 L1 {len(large)}개 -> "
              + " ".join(f"{fmt(s)}:{n}" for s, n in sorted(large.items(), key=lambda x: sorted(x[0]))))
    k = 2
    while large:
        joined, candidates = apriori_gen(set(large), k)
        if not candidates:
            if verbose:
                print(f"{k}회차: join {len(joined)}개, prune 후 0개 -> 종료 (DB 를 읽지 않는다)")
            break
        support = Counter()
        for t in db.scan():
            for c in candidates:
                if c <= t:
                    support[c] += 1
        counted += len(candidates)
        large = {c: support[c] for c in candidates if support[c] >= MIN_SUPPORT}
        result.update(large)
        if verbose:
            removed = [fmt(c) for c in joined if c not in candidates]
            print(f"{k}회차: join {len(joined)}개, prune {len(joined) - len(candidates)}개"
                  f"{' ' + ' '.join(removed) if removed else ''}, 센 후보 {len(candidates)}개 -> L{k} {len(large)}개")
            if large:
                print("        " + " ".join(f"{fmt(s)}:{n}" for s, n in
                                         sorted(large.items(), key=lambda x: sorted(x[0]))))
        k += 1
    return result, counted


# ---------- FP-growth ----------
class FPNode:
    __slots__ = ("item", "count", "parent", "children")

    def __init__(self, item, parent):
        self.item, self.count, self.parent, self.children = item, 0, parent, {}


def build_fp_tree(weighted_transactions, order):
    """order: 항목 -> 순위(빈도 내림차순). header 는 항목별 노드 목록(논문의 node-link)."""
    root = FPNode(None, None)
    header = defaultdict(list)
    node_count = 0
    for items, weight in weighted_transactions:
        node = root
        for item in sorted((i for i in items if i in order), key=order.get):
            child = node.children.get(item)
            if child is None:
                child = node.children[item] = FPNode(item, node)
                header[item].append(child)
                node_count += 1
            child.count += weight
            node = child
    return root, header, node_count


def fp_growth_mine(header, order, suffix, result, trace):
    # 빈도가 낮은 항목부터 접미사로 삼는다 (논문 §3)
    for item in sorted(header, key=order.get, reverse=True):
        pattern = suffix | {item}
        result[frozenset(pattern)] = sum(n.count for n in header[item])
        base = []  # 조건부 패턴 기반: 이 항목 노드에서 루트까지의 접두 경로
        for node in header[item]:
            path, parent = [], node.parent
            while parent.item is not None:
                path.append(parent.item)
                parent = parent.parent
            if path:
                base.append((path, node.count))
        counts = Counter()
        for path, weight in base:
            for i in path:
                counts[i] += weight
        local = {i: n for i, n in counts.items() if n >= MIN_SUPPORT}
        if trace is not None and not suffix:
            trace.append((item, base, local))
        if local:
            local_order = {i: r for r, i in enumerate(sorted(local, key=lambda x: (-local[x], order[x])))}
            _, sub_header, _ = build_fp_tree(base, local_order)
            fp_growth_mine(sub_header, local_order, pattern, result, None)


def fp_growth(db):
    counts = Counter(item for t in db.scan() for item in t)
    frequent = {i: n for i, n in counts.items() if n >= MIN_SUPPORT}
    # 같은 빈도는 논문 Figure 1 의 헤더 순서(f, c, a, b, m, p)를 따르도록 c 를 f 뒤에 둔다
    tie = {"f": 0, "c": 1, "a": 2, "b": 3, "m": 4, "p": 5}
    order = {i: r for r, i in enumerate(sorted(frequent, key=lambda x: (-frequent[x], tie.get(x, 9))))}
    root, header, node_count = build_fp_tree(((t, 1) for t in db.scan()), order)
    result, trace = {}, []
    fp_growth_mine(header, order, set(), result, trace)
    return result, order, root, node_count, trace


def print_tree(node, depth=0):
    for child in node.children.values():
        print("  " * depth + f"  {child.item}:{child.count}")
        print_tree(child, depth + 1)


def main():
    print("== 0. 거래 데이터 (최소 지지 개수 3) ==")
    for tid, t in zip(range(100, 600, 100), TRANSACTIONS):
        print(f"  {tid}: {t}")
    items = sorted({i for t in TRANSACTIONS for i in t.split()})
    print(f"  서로 다른 항목 {len(items)}개 -> 공집합을 뺀 모든 항목집합 2^{len(items)}-1 = {2 ** len(items) - 1:,}개")

    print("\n== 1. Apriori: 회차마다 join -> prune -> DB 한 번 훑어 세기 ==")
    db = Scanner(TRANSACTIONS)
    ap_result, counted = apriori(db)
    print(f"DB 스캔 {db.scans}회, 지지도를 센 집합 {counted}개, 빈발 항목집합 {len(ap_result)}개")

    print("\n== 2. prune 단계 예: 논문 §2.1.1 의 L3 ==")
    l3 = {frozenset(s.split()) for s in ("1 2 3", "1 2 4", "1 3 4", "1 3 5", "2 3 4")}
    joined, pruned = apriori_gen(l3, 4)
    print("L3 =", " ".join(fmt(s) for s in sorted(l3, key=sorted)))
    print("join 결과 =", " ".join(fmt(s) for s in joined))
    print("prune 결과 =", " ".join(fmt(s) for s in pruned), " ({1,4,5} 가 L3 에 없어 {1,3,4,5} 삭제)")

    print("\n== 3. FP-growth: DB 두 번 훑어 FP-tree 를 만들고 트리만 채굴 ==")
    db = Scanner(TRANSACTIONS)
    fp_result, order, root, node_count, trace = fp_growth(db)
    print("빈도순 항목:", " ".join(sorted(order, key=order.get)))
    print(f"FP-tree (노드 {node_count}개, 거래 5건의 빈발 항목 총 {sum(len([i for i in t.split() if i in order]) for t in TRANSACTIONS)}개):")
    print_tree(root)
    print("접미사별 조건부 패턴 기반 -> 그 안의 빈발 항목")
    for item, base, local in trace:
        base_text = "; ".join(f"{''.join(reversed(p))}:{w}" for p, w in base) or "(없음)"
        local_text = " ".join(f"{i}:{n}" for i, n in sorted(local.items())) or "없음"
        print(f"  {item}: {base_text:24s} -> {local_text}")
    print(f"DB 스캔 {db.scans}회, 빈발 항목집합 {len(fp_result)}개")

    print("\n== 4. 두 결과 비교 ==")
    same = ap_result == fp_result
    print(f"항목집합과 지지 개수가 모두 같은가: {same}")
    for size in range(1, max(len(s) for s in ap_result) + 1):
        group = sorted((s for s in ap_result if len(s) == size), key=sorted)
        print(f"  {size}-항목집합 {len(group)}개: " + " ".join(f"{fmt(s)}:{ap_result[s]}" for s in group))


if __name__ == "__main__":
    main()
