"""DBSCAN의 여섯 정의를 작은 2차원 표본에서 그대로 따라 계산한다.

원 논문(Ester et al., KDD-96)의 정의 1~6과 보조정리 2, 4.2절의 k-dist 휴리스틱이
실제로 어떤 값을 내는지 확인하는 것이 목적이다. 라이브러리를 쓰지 않고 정의를
그대로 옮겨 적는다 — 중간 판정(핵심점 여부, 도달 가능 여부)을 전부 찍어야
글의 설명과 대조할 수 있기 때문이다.
"""

import math
import platform
import sys

EPS = 1.5
MIN_PTS = 4

POINTS = [
    (1, 0), (1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3), (3, 2), (4, 2),
    (8, 1), (8, 2), (8, 3), (9, 1), (9, 2), (9, 3), (10, 2), (11, 2),
    (5, 5), (5, 6), (6, 8),
]

UNCLASSIFIED = None
NOISE = 0


def dist(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def region_query(points, p, eps):
    """정의 1 — p의 Eps-이웃. p 자신을 포함한다."""
    return [q for q in points if dist(p, q) <= eps]


def is_core(points, p, eps, min_pts):
    """정의 2의 핵심점 조건 |N_Eps(p)| >= MinPts."""
    return len(region_query(points, p, eps)) >= min_pts


def directly_density_reachable(points, p, q, eps, min_pts):
    """정의 2 — p가 q로부터 직접 밀도 도달 가능한가. q가 핵심점이어야 한다."""
    return p in region_query(points, q, eps) and is_core(points, q, eps, min_pts)


def density_reachable_from(points, q, eps, min_pts):
    """정의 3 — q에서 출발해 직접 밀도 도달을 사슬로 이은 모든 점."""
    if not is_core(points, q, eps, min_pts):
        return set()
    reached, frontier = set(), [q]
    while frontier:
        current = frontier.pop()
        for r in region_query(points, current, eps):
            if r not in reached:
                reached.add(r)
                # 사슬은 핵심점을 통해서만 이어진다 (경계점에서는 끊긴다)
                if is_core(points, r, eps, min_pts):
                    frontier.append(r)
    reached.discard(q)
    return reached


def dbscan(points, eps, min_pts):
    """논문 4.1절의 DBSCAN/ExpandCluster를 그대로 옮긴 것."""
    labels = {p: UNCLASSIFIED for p in points}
    cluster_id = NOISE + 1
    for p in points:
        if labels[p] is not UNCLASSIFIED:
            continue
        seeds = region_query(points, p, eps)
        if len(seeds) < min_pts:
            labels[p] = NOISE
            continue
        for s in seeds:
            labels[s] = cluster_id
        seeds = [s for s in seeds if s != p]
        while seeds:
            current = seeds.pop(0)
            result = region_query(points, current, eps)
            if len(result) >= min_pts:
                for r in result:
                    if labels[r] in (UNCLASSIFIED, NOISE):
                        # NOISE 로 찍혔던 점은 경계점이므로 seeds 에 넣지 않는다
                        if labels[r] is UNCLASSIFIED:
                            seeds.append(r)
                        labels[r] = cluster_id
        cluster_id += 1
    return labels


def k_dist(points, p, k):
    """4.2절 — p에서 k번째 최근접 이웃까지의 거리. 자신은 세지 않는다."""
    others = sorted(dist(p, q) for q in points if q != p)
    return others[k - 1]


def kmeans(points, k, initial, rounds=20):
    """비교용 Lloyd 알고리즘. 잡음을 따로 낼 자리가 없다는 것을 보이기 위한 것이다."""
    centers = list(initial)
    assign = {}
    for _ in range(rounds):
        assign = {p: min(range(k), key=lambda i: dist(p, centers[i])) for p in points}
        new_centers = []
        for i in range(k):
            members = [p for p in points if assign[p] == i]
            n = len(members)
            new_centers.append((sum(x for x, _ in members) / n,
                                sum(y for _, y in members) / n))
        if new_centers == centers:
            break
        centers = new_centers
    return assign, centers


def fmt(p):
    return f"({p[0]:>2},{p[1]:>2})"


def main():
    print(f"파이썬  {platform.python_version()} / {sys.platform}")
    print(f"파라미터  Eps={EPS}  MinPts={MIN_PTS}  거리=유클리드")
    print(f"표본  {len(POINTS)}점")
    print()

    print("[1] 정의 1·2 — Eps-이웃 크기와 핵심점 판정")
    print(f"{'점':^9} {'|N_Eps|':>7}  {'판정':<6} 이웃")
    for p in POINTS:
        n = region_query(POINTS, p, EPS)
        kind = "핵심점" if len(n) >= MIN_PTS else "비핵심점"
        others = " ".join(fmt(q) for q in n if q != p) or "-"
        print(f"{fmt(p):^9} {len(n):>7}  {kind:<6} {others}")
    print()

    labels = dbscan(POINTS, EPS, MIN_PTS)
    print("[2] 정의 5·6 — DBSCAN이 낸 군집과 잡음")
    for cid in sorted(set(labels.values())):
        members = [p for p in POINTS if labels[p] == cid]
        name = "잡음" if cid == NOISE else f"군집 {cid}"
        core = [p for p in members if is_core(POINTS, p, EPS, MIN_PTS)]
        border = [p for p in members if p not in core]
        print(f"  {name:<6} {len(members):>2}점")
        print(f"    핵심점 {len(core):>2}: " + " ".join(fmt(p) for p in core))
        if cid != NOISE:
            print(f"    경계점 {len(border):>2}: " + " ".join(fmt(p) for p in border))
    print()

    print("[3] 정의 2 — 직접 밀도 도달의 비대칭")
    q, p = (3, 2), (4, 2)
    f = directly_density_reachable
    print(f"  {fmt(p)} ← {fmt(q)} : {f(POINTS, p, q, EPS, MIN_PTS)}"
          f"  ({fmt(q)}는 핵심점)")
    print(f"  {fmt(q)} ← {fmt(p)} : {f(POINTS, q, p, EPS, MIN_PTS)}"
          f"  ({fmt(p)}는 비핵심점)")
    print()

    print("[4] 정의 3·4 — 두 경계점은 밀도 도달이 안 되지만 밀도 연결은 된다")
    b1, b2 = (1, 0), (4, 2)
    print(f"  {fmt(b2)} ∈ 도달({fmt(b1)}) : {b2 in density_reachable_from(POINTS, b1, EPS, MIN_PTS)}")
    print(f"  {fmt(b1)} ∈ 도달({fmt(b2)}) : {b1 in density_reachable_from(POINTS, b2, EPS, MIN_PTS)}")
    witnesses = [o for o in POINTS
                 if b1 in density_reachable_from(POINTS, o, EPS, MIN_PTS)
                 and b2 in density_reachable_from(POINTS, o, EPS, MIN_PTS)]
    print(f"  둘 다 도달하는 점 o : {len(witnesses)}개 " + " ".join(fmt(o) for o in witnesses))
    print()

    print("[5] 보조정리 2 — 한 군집의 어느 핵심점에서 출발해도 같은 집합이 나온다")
    c1_core = [p for p in POINTS
               if labels[p] == 1 and is_core(POINTS, p, EPS, MIN_PTS)]
    sets = {frozenset(density_reachable_from(POINTS, p, EPS, MIN_PTS) | {p})
            for p in c1_core}
    print(f"  군집 1의 핵심점 {len(c1_core)}개에서 각각 전개 → 서로 다른 집합 {len(sets)}개")
    print(f"  집합 크기 {len(next(iter(sets)))} = 군집 1의 크기 "
          f"{sum(1 for p in POINTS if labels[p] == 1)}")
    print()

    print("[6] 방문 순서를 뒤집었을 때")
    reversed_labels = dbscan(list(reversed(POINTS)), EPS, MIN_PTS)
    same = {p: (labels[p] == NOISE) == (reversed_labels[p] == NOISE) for p in POINTS}
    print(f"  잡음/비잡음 판정이 같은 점 : {sum(same.values())}/{len(POINTS)}")
    print()

    print("[7] 4.2절 — 정렬된 k-dist 그래프 (k=4)")
    rows = sorted(((k_dist(POINTS, p, MIN_PTS), p) for p in POINTS), reverse=True)
    for d, p in rows:
        bar = "#" * round(d * 6)
        print(f"  {fmt(p)}  4-dist={d:5.2f}  {bar}")
    print()

    print("[8] 비교 — 같은 표본에 k-means(k=2)")
    assign, centers = kmeans(POINTS, 2, [(1, 1), (9, 2)])
    for i, c in enumerate(centers):
        members = [p for p in POINTS if assign[p] == i]
        print(f"  군집 {i}  중심=({c[0]:.2f},{c[1]:.2f})  {len(members)}점")
        print("    " + " ".join(fmt(p) for p in members))
    strays = [(5, 5), (5, 6), (6, 8)]
    print("  DBSCAN이 잡음으로 뺀 3점의 k-means 소속 : "
          + " ".join(f"{fmt(p)}→군집 {assign[p]}" for p in strays))


if __name__ == "__main__":
    main()
