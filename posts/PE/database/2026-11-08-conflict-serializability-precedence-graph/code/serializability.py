"""스케줄의 충돌 직렬 가능성·뷰 직렬 가능성·2PL 생성 가능성을 판정한다.

정의는 Silberschatz·Korth·Sudarshan, Database System Concepts 7th ed. 17·18장 슬라이드를 따른다.
- 충돌: 서로 다른 트랜잭션이 같은 항목에 접근하고 적어도 하나가 write
- 충돌 직렬 가능 ⇔ 선행 그래프에 사이클이 없다 (위상 정렬이 직렬 순서)
- 뷰 동등: 초기값 읽기·읽은 값의 출처·마지막 쓰기가 같다

선행 그래프 판정은 모든 직렬 순서와 충돌 쌍의 순서를 맞대 보는 전수 검사로 교차 확인한다.
"""
from itertools import permutations, product

# 스케줄은 (트랜잭션, 연산, 항목) 의 나열. 연산은 'r' 또는 'w'.
SCHEDULES = {
    "S1 교차 실행": [
        ("T1", "r", "A"), ("T1", "w", "A"),
        ("T2", "r", "A"), ("T2", "w", "A"),
        ("T1", "r", "B"), ("T1", "w", "B"),
        ("T2", "r", "B"), ("T2", "w", "B"),
    ],
    "S2 갱신 분실": [
        ("T1", "r", "A"), ("T2", "r", "A"),
        ("T1", "w", "A"), ("T2", "w", "A"),
    ],
    "S3 맹목 쓰기": [
        ("T1", "r", "Q"), ("T2", "w", "Q"),
        ("T1", "w", "Q"), ("T3", "w", "Q"),
    ],
    "S4 2PL 불가": [
        ("T1", "r", "X"), ("T2", "w", "X"),
        ("T3", "w", "Y"), ("T1", "r", "Y"),
    ],
}


def fmt(schedule):
    return " ".join(f"{op}{txn[1:]}({item})" for txn, op, item in schedule)


def transactions(schedule):
    return sorted({txn for txn, _, _ in schedule})


def conflict_pairs(schedule):
    """앞 연산 i, 뒤 연산 j 가 충돌하면 (i, j) 를 낸다."""
    for i, (ti, oi, qi) in enumerate(schedule):
        for j in range(i + 1, len(schedule)):
            tj, oj, qj = schedule[j]
            if ti != tj and qi == qj and "w" in (oi, oj):
                yield i, j


def precedence_graph(schedule):
    edges = {}
    for i, j in conflict_pairs(schedule):
        key = (schedule[i][0], schedule[j][0])
        label = f"{schedule[i][1]}{schedule[i][0][1:]}({schedule[i][2]})<{schedule[j][1]}{schedule[j][0][1:]}({schedule[j][2]})"
        edges.setdefault(key, []).append(label)
    return edges


def topological_order(nodes, edges):
    """칸 알고리즘. 사이클이 있으면 None."""
    indegree = {n: 0 for n in nodes}
    for _, dst in edges:
        indegree[dst] += 1
    ready = sorted(n for n in nodes if indegree[n] == 0)
    order = []
    while ready:
        node = ready.pop(0)
        order.append(node)
        for src, dst in sorted(edges):
            if src == node:
                indegree[dst] -= 1
                if indegree[dst] == 0:
                    ready.append(dst)
                    ready.sort()
    return order if len(order) == len(nodes) else None


def serial_schedule(schedule, order):
    return [step for txn in order for step in schedule if step[0] == txn]


def conflict_equivalent_serials(schedule):
    """전수 검사: 충돌 쌍의 앞뒤 순서를 모두 지키는 직렬 순서."""
    found = []
    for order in permutations(transactions(schedule)):
        rank = {t: k for k, t in enumerate(order)}
        if all(rank[schedule[i][0]] < rank[schedule[j][0]] for i, j in conflict_pairs(schedule)):
            found.append(order)
    return found


def view_signature(schedule):
    """읽기마다 읽은 값의 출처(None=초기값)와 항목별 마지막 쓰기."""
    last_writer = {}
    reads = []
    seen = {}
    for txn, op, item in schedule:
        if op == "r":
            # 같은 트랜잭션이 같은 항목을 여러 번 읽으면 순번으로 구분한다
            nth = seen.get((txn, item), 0)
            seen[(txn, item)] = nth + 1
            reads.append((txn, item, nth, last_writer.get(item)))
        else:
            last_writer[item] = txn
    return sorted(reads, key=str), last_writer


def view_equivalent_serials(schedule):
    target = view_signature(schedule)
    return [order for order in permutations(transactions(schedule))
            if view_signature(serial_schedule(schedule, order)) == target]


def two_phase_lockable(schedule):
    """기본 2PL(락 업그레이드 없음)로 이 순서가 나올 수 있는가를 전수로 본다.

    트랜잭션마다 락 포인트 p 를 연산 사이(k - 0.5)에서 고른다. 항목 락은
    [min(첫 접근, p), max(마지막 접근, p)] 동안 잡는다 — 2PL 이 허락하는 가장 짧은 보유 구간이다.
    write 가 있으면 X, 아니면 S. 충돌 모드끼리 구간이 겹치면 그 선택은 불가능하다.
    """
    txns = transactions(schedule)
    access = {}
    for k, (txn, op, item) in enumerate(schedule):
        first, last, mode = access.get((txn, item), (k, k, "S"))
        access[(txn, item)] = (min(first, k), max(last, k), "X" if op == "w" or mode == "X" else "S")
    points = [k - 0.5 for k in range(len(schedule) + 1)]
    for choice in product(points, repeat=len(txns)):
        lock_point = dict(zip(txns, choice))
        holds = []
        for (txn, item), (first, last, mode) in access.items():
            p = lock_point[txn]
            holds.append((txn, item, mode, min(first, p), max(last, p)))
        clash = any(
            a[0] != b[0] and a[1] == b[1] and "X" in (a[2], b[2]) and a[3] < b[4] and b[3] < a[4]
            for idx, a in enumerate(holds) for b in holds[idx + 1:]
        )
        if not clash:
            return lock_point
    return None


def main():
    for name, schedule in SCHEDULES.items():
        print(f"== {name} ==")
        print(f"  스케줄        : {fmt(schedule)}")
        edges = precedence_graph(schedule)
        for (src, dst), labels in sorted(edges.items()):
            print(f"  간선 {src}->{dst}   : {', '.join(labels)}")
        order = topological_order(transactions(schedule), edges)
        print(f"  선행 그래프   : {'사이클 없음, 직렬 순서 ' + '->'.join(order) if order else '사이클 있음'}")
        print(f"  전수(충돌)    : {['->'.join(o) for o in conflict_equivalent_serials(schedule)] or '없음'}")
        print(f"  전수(뷰)      : {['->'.join(o) for o in view_equivalent_serials(schedule)] or '없음'}")
        lock_point = two_phase_lockable(schedule)
        if lock_point:
            print("  2PL 생성 가능 : 예, 락 포인트 " + ", ".join(f"{t}@{p}" for t, p in lock_point.items()))
        else:
            print("  2PL 생성 가능 : 아니오")
        print()


if __name__ == "__main__":
    main()
