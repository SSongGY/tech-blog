"""은행가 알고리즘 — 답안에 실을 예제를 직접 돌려 검산한다.

교재(Operating System Concepts 10th ed. Ch.8)의 안전성 알고리즘과
자원 요청 알고리즘을 그대로 옮겨 구현하고, 답안에 쓸 3프로세스·2자원 예제에
대해 ① 현재 상태가 안전한지 ② 어떤 요청이 승인되고 어떤 요청이 거절되는지를
전부 뽑는다. 손으로 센 안전 순서가 맞는지도 전수 탐색으로 대조한다.
"""

from itertools import permutations

PROCESSES = ["P0", "P1", "P2"]
RESOURCES = ["A", "B"]

# 교재 표기 그대로: Max(최대 요구), Allocation(현재 할당), Available(가용)
# 전체 자원은 A 10개, B 5개. Available 은 전체에서 Allocation 합을 뺀 값이다.
MAX = {"P0": (5, 4), "P1": (5, 2), "P2": (9, 2)}
ALLOCATION = {"P0": (0, 1), "P1": (3, 0), "P2": (2, 1)}
AVAILABLE = (5, 3)


def need(allocation):
    """Need = Max - Allocation (교재 8.34)"""
    return {p: tuple(MAX[p][j] - allocation[p][j] for j in range(len(RESOURCES)))
            for p in PROCESSES}


def le(a, b):
    return all(x <= y for x, y in zip(a, b))


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def safety(available, allocation, trace=False):
    """안전성 알고리즘 (교재 8.31). 완료 순서를 돌려준다. 불안전이면 None."""
    work = available
    finish = {p: False for p in PROCESSES}
    order = []
    while True:
        for p in PROCESSES:
            if not finish[p] and le(need(allocation)[p], work):
                if trace:
                    print(f"    Work={work} 에서 Need{p}={need(allocation)[p]} 충족 "
                          f"→ {p} 완료, Work={add(work, allocation[p])}")
                work = add(work, allocation[p])
                finish[p] = True
                order.append(p)
                break
        else:
            return order if all(finish.values()) else None


def all_safe_sequences(available, allocation):
    """안전 순서가 유일하지 않다는 것을 보이려고 전수 탐색한다."""
    found = []
    for seq in permutations(PROCESSES):
        work = available
        ok = True
        for p in seq:
            if not le(need(allocation)[p], work):
                ok = False
                break
            work = add(work, allocation[p])
        if ok:
            found.append(seq)
    return found


def request(pid, req):
    """자원 요청 알고리즘 (교재 8.32). 판정 사유까지 문자열로 돌려준다."""
    n = need(ALLOCATION)[pid]
    if not le(req, n):
        return f"오류 — Request{req} > Need{n}. 최대 요구를 넘었다"
    if not le(req, AVAILABLE):
        return f"대기 — Request{req} > Available{AVAILABLE}. 지금 줄 자원이 없다"
    trial = dict(ALLOCATION)
    trial[pid] = add(ALLOCATION[pid], req)
    trial_available = sub(AVAILABLE, req)
    order = safety(trial_available, trial)
    if order:
        return f"승인 — 가장 할당 후 Available={trial_available}, 안전 순서 <{', '.join(order)}>"
    return f"거절 — 가장 할당 후 Available={trial_available} 이 불안전. 원래 상태로 되돌린다"


def main():
    print("= 상태 =")
    print(f"{'':4} {'Max':>8} {'Allocation':>12} {'Need':>8}")
    for p in PROCESSES:
        print(f"{p:4} {str(MAX[p]):>8} {str(ALLOCATION[p]):>12} "
              f"{str(need(ALLOCATION)[p]):>8}")
    print(f"Available = {AVAILABLE}")

    print("\n= 안전성 알고리즘 추적 =")
    order = safety(AVAILABLE, ALLOCATION, trace=True)
    print(f"  결과: {'안전' if order else '불안전'}"
          + (f", 순서 <{', '.join(order)}>" if order else ""))

    seqs = all_safe_sequences(AVAILABLE, ALLOCATION)
    print(f"\n= 안전 순서 전수 탐색 = {len(seqs)}가지 / 전체 {6}가지")
    for s in seqs:
        print(f"  <{', '.join(s)}>")

    print("\n= 자원 요청 판정 =")
    for pid, req in [("P1", (2, 2)), ("P2", (5, 0)), ("P2", (6, 1)), ("P0", (6, 0))]:
        print(f"  {pid} Request{req}")
        print(f"    {request(pid, req)}")


if __name__ == "__main__":
    main()
