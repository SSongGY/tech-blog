"""은행원 알고리즘과 교착 탐지 알고리즘을 교재 예제로 검산한다.

예제 값은 Silberschatz, Operating System Concepts 10th ed. 8장 슬라이드
(S. Weiss 2020 개정판) 8.33~8.35, 8.42~8.43 에서 가져왔다.
"""

from itertools import permutations

RESOURCE_NAMES = ("A", "B", "C")

# 슬라이드 8.33 — 자원 A 10개, B 5개, C 7개
ALLOCATION = [(0, 1, 0), (2, 0, 0), (3, 0, 2), (2, 1, 1), (0, 0, 2)]
MAXIMUM = [(7, 5, 3), (3, 2, 2), (9, 0, 2), (2, 2, 2), (4, 3, 3)]
AVAILABLE = (3, 3, 2)

# 슬라이드 8.42 — 자원 A 7개, B 2개, C 6개
DETECT_ALLOCATION = [(0, 1, 0), (2, 0, 0), (3, 0, 3), (2, 1, 1), (0, 0, 2)]
DETECT_REQUEST = [(0, 0, 0), (2, 0, 2), (0, 0, 0), (1, 0, 0), (0, 0, 2)]
DETECT_AVAILABLE = (0, 0, 0)


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def fits(a, b):
    return all(x <= y for x, y in zip(a, b))


def need_matrix(maximum, allocation):
    return [sub(m, a) for m, a in zip(maximum, allocation)]


def fmt(vector):
    return " ".join(str(v) for v in vector)


def safety_restart(available, allocation, need, trace=False):
    """2단계 "Finish 가 false 이고 Need <= Work 인 i 를 찾는다" 를
    매번 P0 부터 다시 찾는 방식으로 구현한다."""
    work = available
    finish = [False] * len(allocation)
    order = []
    while True:
        for i in range(len(allocation)):
            if not finish[i] and fits(need[i], work):
                if trace:
                    print(f"     P{i}: Need({fmt(need[i])}) <= Work({fmt(work)})"
                          f" -> Work += Allocation({fmt(allocation[i])})"
                          f" = {fmt(add(work, allocation[i]))}")
                work = add(work, allocation[i])
                finish[i] = True
                order.append(i)
                break
        else:
            break
    return all(finish), order


def safety_sweep(available, allocation, need):
    """같은 2단계를 P0..P4 를 한 바퀴씩 훑으며, 찾은 뒤에도 다음 번호부터 이어서 보는 방식."""
    work = available
    finish = [False] * len(allocation)
    order = []
    progressed = True
    while progressed:
        progressed = False
        for i in range(len(allocation)):
            if not finish[i] and fits(need[i], work):
                work = add(work, allocation[i])
                finish[i] = True
                order.append(i)
                progressed = True
    return all(finish), order


def is_safe_sequence(sequence, available, allocation, need):
    work = available
    for i in sequence:
        if not fits(need[i], work):
            return False
        work = add(work, allocation[i])
    return True


def request(pid, req, available, allocation, need):
    """자원 요청 알고리즘 3단계. 승인되면 새 상태를, 아니면 None 을 돌려준다."""
    print(f"\n-- P{pid} 가 ({fmt(req)}) 를 요청")
    if not fits(req, need[pid]):
        print(f"   1단계: Request > Need({fmt(need[pid])}) -> 오류 (최대 요구 초과)")
        return None
    print(f"   1단계: Request <= Need({fmt(need[pid])}) 통과")
    if not fits(req, available):
        print(f"   2단계: Request > Available({fmt(available)}) -> 대기")
        return None
    print(f"   2단계: Request <= Available({fmt(available)}) 통과")
    new_available = sub(available, req)
    new_allocation = list(allocation)
    new_allocation[pid] = add(allocation[pid], req)
    new_need = list(need)
    new_need[pid] = sub(need[pid], req)
    print(f"   3단계: 가상 할당 -> Available = {fmt(new_available)}")
    safe, order = safety_restart(new_available, new_allocation, new_need)
    if safe:
        print("   안전 -> 할당. 안전 순서 "
              + "<" + ", ".join(f"P{i}" for i in order) + ">")
        return new_available, new_allocation, new_need
    finished = ", ".join(f"P{i}" for i in order) or "없음"
    print(f"   불안전 -> 대기, 이전 상태로 복원 (끝까지 갈 수 있는 프로세스: {finished})")
    return None


def detect(available, allocation, req, label):
    """탐지 알고리즘. Allocation 이 0 인 프로세스는 처음부터 Finish = true."""
    work = available
    finish = [alloc == (0, 0, 0) for alloc in allocation]
    order = []
    while True:
        for i in range(len(allocation)):
            if not finish[i] and fits(req[i], work):
                work = add(work, allocation[i])
                finish[i] = True
                order.append(i)
                break
        else:
            break
    stuck = [f"P{i}" for i, done in enumerate(finish) if not done]
    print(f"\n-- 탐지: {label}")
    print("   끝낸 순서 <" + ", ".join(f"P{i}" for i in order) + ">")
    print("   교착: " + (", ".join(stuck) if stuck else "없음"))


def main() -> None:
    need = need_matrix(MAXIMUM, ALLOCATION)
    print("== 1. 슬라이드 8.33 의 시각 T0 상태")
    print("   프로세스 | Allocation | Max   | Need")
    for i in range(len(ALLOCATION)):
        print(f"   P{i}       | {fmt(ALLOCATION[i])}      | {fmt(MAXIMUM[i])} "
              f"| {fmt(need[i])}")
    total = AVAILABLE
    for alloc in ALLOCATION:
        total = add(total, alloc)
    print(f"   Available = {fmt(AVAILABLE)}, 전체 = {fmt(total)} (교재: 10 5 7)")

    print("\n== 2. 안전 알고리즘 — 매번 P0 부터 다시 찾기")
    safe, order = safety_restart(AVAILABLE, ALLOCATION, need, trace=True)
    print(f"   안전: {safe}, 순서 <" + ", ".join(f"P{i}" for i in order) + ">")

    safe, order = safety_sweep(AVAILABLE, ALLOCATION, need)
    print("\n== 3. 안전 알고리즘 — 한 바퀴씩 이어서 훑기")
    print(f"   안전: {safe}, 순서 <" + ", ".join(f"P{i}" for i in order) + ">")

    textbook = (1, 3, 4, 2, 0)
    print("\n== 4. 교재의 안전 순서 <P1, P3, P4, P2, P0> 가 실제로 안전한가: "
          f"{is_safe_sequence(textbook, AVAILABLE, ALLOCATION, need)}")

    all_orders = list(permutations(range(len(ALLOCATION))))
    safe_orders = [p for p in all_orders
                   if is_safe_sequence(p, AVAILABLE, ALLOCATION, need)]
    print(f"\n== 5. 5! = {len(all_orders)} 가지 순서 중 안전 순서: {len(safe_orders)}개")
    for p in safe_orders:
        print("   <" + ", ".join(f"P{i}" for i in p) + ">")
    firsts = sorted({p[0] for p in safe_orders})
    print("   맨 앞에 올 수 있는 프로세스: " + ", ".join(f"P{i}" for i in firsts))

    print("\n== 6. 자원 요청 알고리즘 — 슬라이드 8.35")
    state = request(1, (1, 0, 2), AVAILABLE, ALLOCATION, need)
    available, allocation, need_after = state
    request(4, (3, 3, 0), available, allocation, need_after)
    request(0, (0, 2, 0), available, allocation, need_after)
    request(1, (1, 2, 1), available, allocation, need_after)

    print("\n== 7. 불안전 상태는 곧 교착인가 — P0 (0,2,0) 을 그냥 줬다면")
    unsafe_available = sub(available, (0, 2, 0))
    unsafe_allocation = list(allocation)
    unsafe_allocation[0] = add(allocation[0], (0, 2, 0))
    unsafe_need = list(need_after)
    unsafe_need[0] = sub(need_after[0], (0, 2, 0))
    print(f"   Available = {fmt(unsafe_available)}")
    detect(unsafe_available, unsafe_allocation, unsafe_need,
           "모든 프로세스가 남은 최대치(Need)를 한꺼번에 요청하면")
    modest = [(0, 0, 0)] * 5
    modest[3] = (0, 1, 0)
    detect(unsafe_available, unsafe_allocation, modest,
           "P3 만 B 1개를 요청하고 나머지는 지금 가진 것으로 끝낸다면")

    print("\n== 8. 탐지 알고리즘 — 슬라이드 8.42~8.43")
    detect(DETECT_AVAILABLE, DETECT_ALLOCATION, DETECT_REQUEST, "시각 T0")
    extra = list(DETECT_REQUEST)
    extra[2] = (0, 0, 1)
    detect(DETECT_AVAILABLE, DETECT_ALLOCATION, extra, "P2 가 C 1개를 더 요청")


if __name__ == "__main__":
    main()
