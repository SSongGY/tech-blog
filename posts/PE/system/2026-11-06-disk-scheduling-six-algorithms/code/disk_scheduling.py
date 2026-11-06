"""디스크 스케줄링 여섯 가지의 헤드 이동 거리를 교재 예제로 검산한다.

python disk_scheduling.py

교재 예제(Silberschatz): 실린더 0~199, 큐 98,183,37,122,14,124,65,67, 헤드 53.
"""

QUEUE = [98, 183, 37, 122, 14, 124, 65, 67]
HEAD = 53
MIN_CYL = 0
MAX_CYL = 199


def fcfs(head, queue):
    return [head] + list(queue)


def sstf(head, queue):
    pending = list(queue)
    path = [head]
    while pending:
        # 거리가 같으면 먼저 들어온 요청을 고른다 — min 은 앞쪽을 돌려준다
        nearest = min(pending, key=lambda c: abs(c - path[-1]))
        pending.remove(nearest)
        path.append(nearest)
    return path


def scan(head, queue, toward_low=True):
    """끝 실린더까지 간 뒤 방향을 바꾼다."""
    low = sorted(c for c in queue if c < head)
    high = sorted(c for c in queue if c >= head)
    if toward_low:
        return [head] + low[::-1] + [MIN_CYL] + high
    return [head] + high + [MAX_CYL] + low[::-1]


def look(head, queue, toward_low=True):
    """마지막 요청에서 바로 방향을 바꾼다."""
    low = sorted(c for c in queue if c < head)
    high = sorted(c for c in queue if c >= head)
    if toward_low:
        return [head] + low[::-1] + high
    return [head] + high + low[::-1]


def c_scan(head, queue):
    """높은 쪽으로만 서비스하고, 끝에서 0번으로 돌아가 다시 올라간다."""
    low = sorted(c for c in queue if c < head)
    high = sorted(c for c in queue if c >= head)
    return [head] + high + [MAX_CYL, MIN_CYL] + low


def c_look(head, queue):
    low = sorted(c for c in queue if c < head)
    high = sorted(c for c in queue if c >= head)
    return [head] + high + low


def distance(path, skip_jump=None):
    """skip_jump=(a, b) 이면 a→b 복귀 구간을 빼고 센다."""
    total = 0
    for a, b in zip(path, path[1:]):
        if skip_jump == (a, b):
            continue
        total += abs(b - a)
    return total


def served(path, queue):
    return [c for c in path[1:] if c in queue]


def part1_textbook():
    print("### 1. 교재 예제 — 헤드 이동 거리")
    print(f"  큐 {QUEUE}, 헤드 {HEAD}, 실린더 {MIN_CYL}~{MAX_CYL}")
    cases = [
        ("FCFS", fcfs(HEAD, QUEUE), None),
        ("SSTF", sstf(HEAD, QUEUE), None),
        ("SCAN  (0 쪽으로)", scan(HEAD, QUEUE, True), None),
        ("SCAN  (199 쪽으로)", scan(HEAD, QUEUE, False), None),
        ("LOOK  (0 쪽으로)", look(HEAD, QUEUE, True), None),
        ("LOOK  (199 쪽으로)", look(HEAD, QUEUE, False), None),
        ("C-SCAN 복귀 포함", c_scan(HEAD, QUEUE), None),
        ("C-SCAN 복귀 제외", c_scan(HEAD, QUEUE), (MAX_CYL, MIN_CYL)),
        ("C-LOOK 복귀 포함", c_look(HEAD, QUEUE), None),
        ("C-LOOK 복귀 제외", c_look(HEAD, QUEUE), (183, 14)),
    ]
    for name, path, skip in cases:
        print(f"  {name:<18} {distance(path, skip):4d}  순서 {served(path, QUEUE)}")


def part2_textbook_numbers():
    print("\n### 2. 교재 슬라이드가 적은 수치와 맞춰 보기")
    stated = {"FCFS": 640, "SSTF": 236, "SCAN": 208}
    computed = {
        "FCFS": distance(fcfs(HEAD, QUEUE)),
        "SSTF": distance(sstf(HEAD, QUEUE)),
        "SCAN": distance(scan(HEAD, QUEUE, True)),
    }
    for name, value in stated.items():
        print(f"  {name}: 슬라이드 {value} / 계산 {computed[name]}  일치={value == computed[name]}")
    print(f"  208 과 같은 값이 나오는 경로: LOOK(0 쪽으로) = {distance(look(HEAD, QUEUE, True))}")
    print("  SCAN(0 쪽으로) 구간별:", " + ".join(
        str(abs(b - a)) for a, b in zip(scan(HEAD, QUEUE, True), scan(HEAD, QUEUE, True)[1:])))


def part3_sstf_starvation():
    """헤드 근처에 요청이 계속 들어오면 먼 요청이 언제 처리되나."""
    print("\n### 3. SSTF 기아 — 헤드 근처에 요청이 계속 들어올 때")
    far = 190
    for name in ("SSTF", "LOOK"):
        head = 100
        pending = [far, 105]
        direction = 1
        served_count = 0
        far_served_at = None
        for step in range(200):
            if name == "SSTF":
                nxt = min(pending, key=lambda c: abs(c - head))
            else:
                ahead = [c for c in pending if (c - head) * direction >= 0]
                if not ahead:
                    direction = -direction
                    ahead = [c for c in pending if (c - head) * direction >= 0]
                nxt = min(ahead, key=lambda c: abs(c - head))
            pending.remove(nxt)
            head = nxt
            served_count += 1
            if nxt == far:
                far_served_at = served_count
                break
            # 서비스할 때마다 현재 위치 ±3 안쪽에 새 요청이 하나 들어온다(번갈아 위아래)
            pending.append(head + (3 if step % 2 == 0 else -3))
        print(f"  {name}: 190번 요청이 처리된 순번 = {far_served_at}  (200회 안에 처리 못 하면 None)")


def part4_wait_by_position():
    """헤드가 쉬지 않고 왕복할 때, 실린더 위치별로 다음 방문까지 최대 몇 칸을 기다리나."""
    print("\n### 4. 위치별 최대 대기 — 헤드가 쉬지 않고 쓸고 다닐 때 (이동 1칸 = 1)")
    span = MAX_CYL - MIN_CYL
    print("  위치 | SCAN 최대 대기 | C-SCAN 최대 대기(복귀 199칸 포함)")
    for x in (0, 50, 100, 150, 199):
        # SCAN: x 를 지나간 직후 반대 끝을 찍고 돌아올 때까지 = 2 × (먼 쪽 끝까지 거리)
        scan_wait = 2 * max(x - MIN_CYL, MAX_CYL - x)
        # C-SCAN: 한 바퀴(올라가기 199 + 복귀 199)가 지나야 다시 온다 — 위치와 무관
        c_scan_wait = span + span
        print(f"  {x:4d} | {scan_wait:14d} | {c_scan_wait:d}")


def main():
    part1_textbook()
    part2_textbook_numbers()
    part3_sstf_starvation()
    part4_wait_by_position()


if __name__ == "__main__":
    main()
