"""속성 친화도 행렬을 만들고 결합 에너지 알고리즘(BEA)으로 재배열한 뒤 분할 지점을 찾는다.

외부 의존성이 없다. 입력(사용 행렬·접근 빈도)은 글에 그대로 실린 값이다.
"""

ATTRS = ["A1", "A2", "A3", "A4", "A5"]

# 질의별 속성 사용 여부 use(q, A) 와 접근 빈도 acc(q)
USE = {
    "q1": [1, 0, 1, 0, 0],
    "q2": [0, 1, 0, 1, 1],
    "q3": [0, 1, 0, 0, 1],
    "q4": [1, 0, 1, 1, 0],
}
ACC = {"q1": 25, "q2": 40, "q3": 20, "q4": 5}


def affinity_matrix():
    n = len(ATTRS)
    aa = [[0] * n for _ in range(n)]
    for q, row in USE.items():
        for i in range(n):
            for j in range(n):
                aa[i][j] += row[i] * row[j] * ACC[q]
    return aa


def bond(aa, x, y):
    # bond(Ax, Ay) = sum_z aff(Az, Ax) * aff(Az, Ay)
    return sum(aa[z][x] * aa[z][y] for z in range(len(aa)))


def cont(aa, i, k, j):
    # 속성 k 를 i 와 j 사이에 넣을 때 전체 결합 에너지 증가분
    # i 또는 j 가 None 이면 그쪽은 경계(결합 0)
    b_ik = bond(aa, i, k) if i is not None else 0
    b_kj = bond(aa, k, j) if j is not None else 0
    b_ij = bond(aa, i, j) if i is not None and j is not None else 0
    return 2 * b_ik + 2 * b_kj - 2 * b_ij


def bea(aa):
    order = [0, 1]
    log = []
    for k in range(2, len(aa)):
        best_pos, best_val, tried = None, None, []
        for pos in range(len(order) + 1):
            left = order[pos - 1] if pos > 0 else None
            right = order[pos] if pos < len(order) else None
            val = cont(aa, left, k, right)
            tried.append((pos, val))
            if best_val is None or val > best_val:
                best_pos, best_val = pos, val
        order.insert(best_pos, k)
        log.append((k, tried, best_pos))
    return order, log


def global_measure(aa, order):
    # AM = sum_i sum_j aff(i,j) * (aff(i,j-1) + aff(i,j+1)), 경계 밖은 0
    n = len(order)
    total = 0
    for i in order:
        for idx, j in enumerate(order):
            left = aa[i][order[idx - 1]] if idx > 0 else 0
            right = aa[i][order[idx + 1]] if idx < n - 1 else 0
            total += aa[i][j] * (left + right)
    return total


def show(aa, order, title):
    print(title)
    print("      " + "".join(f"{ATTRS[c]:>5}" for c in order))
    for r in order:
        print(f"  {ATTRS[r]:>3} " + "".join(f"{aa[r][c]:>5}" for c in order))


def split_point(aa, order):
    # 질의를 위쪽 블록만 쓰는 TQ, 아래쪽 블록만 쓰는 BQ, 양쪽을 쓰는 OQ 로 나눠
    # z = CTQ * CBQ - COQ^2 를 최대로 하는 분할 지점을 고른다
    results = []
    for cut in range(1, len(order)):
        top = {ATTRS[a] for a in order[:cut]}
        bottom = {ATTRS[a] for a in order[cut:]}
        ctq = cbq = coq = 0
        for q, row in USE.items():
            used = {ATTRS[i] for i, v in enumerate(row) if v}
            if used <= top:
                ctq += ACC[q]
            elif used <= bottom:
                cbq += ACC[q]
            else:
                coq += ACC[q]
        results.append((cut, sorted(top), sorted(bottom), ctq, cbq, coq, ctq * cbq - coq * coq))
    return results


def main():
    print("[1] 사용 행렬 use(q, A) 와 접근 빈도 acc(q)")
    print("      " + "".join(f"{a:>5}" for a in ATTRS) + "  acc")
    for q, row in USE.items():
        print(f"  {q:>3} " + "".join(f"{v:>5}" for v in row) + f"{ACC[q]:>5}")

    aa = affinity_matrix()
    ident = list(range(len(ATTRS)))
    print()
    show(aa, ident, "[2] 속성 친화도 행렬 AA (원래 순서)")
    print(f"  전체 결합 에너지 AM = {global_measure(aa, ident)}")

    print()
    print("[3] BEA — 속성을 하나씩 넣으며 cont 가 가장 큰 자리를 고른다")
    order, log = bea(aa)
    print("  처음 두 열: A1 A2")
    for k, tried, best in log:
        cells = ", ".join(f"자리{p}:{v}" for p, v in tried)
        print(f"  {ATTRS[k]} 삽입 → {cells} → 자리{best} 선택")
    print("  최종 순서: " + " ".join(ATTRS[i] for i in order))

    print()
    show(aa, order, "[4] 군집 행렬 CA (열·행을 같은 순서로 재배열)")
    print(f"  전체 결합 에너지 AM = {global_measure(aa, order)}")

    print()
    print("[5] 분할 지점 — z = CTQ * CBQ - COQ^2")
    for cut, top, bottom, ctq, cbq, coq, z in split_point(aa, order):
        print(f"  {top} | {bottom}  CTQ={ctq} CBQ={cbq} COQ={coq}  z={z}")


if __name__ == "__main__":
    main()
