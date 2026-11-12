"""SJF·SRT(CPU)와 SSTF·SLTF(디스크)를 같은 '가장 짧은 것 먼저' 규칙으로 검산한다.

시간은 정수 단위로만 흉내 낸다. 교재가 정하지 않은 동률은
'기준 값 → 도착 시각 → 목록 순서' 순으로 깬다.
"""

import platform
import sys
from fractions import Fraction


# ---------------------------------------------------------------- CPU 쪽
PROCESSES = [  # (이름, 도착, 실행 시간) — Silberschatz 10판 SRTF 예제와 같은 묶음
    ("P1", 0, 8),
    ("P2", 1, 4),
    ("P3", 2, 9),
    ("P4", 3, 5),
]


def simulate_cpu(processes, preemptive):
    """preemptive=False 면 SJF, True 면 SRT. 1단위씩 진행한다."""
    remaining = {name: burst for name, _, burst in processes}
    arrival = {name: arr for name, arr, _ in processes}
    order = {name: i for i, (name, _, _) in enumerate(processes)}
    finish, first_run, gantt = {}, {}, []
    current, time = None, 0
    while len(finish) < len(processes):
        ready = [n for n in remaining if arrival[n] <= time and n not in finish]
        if not ready:
            time += 1
            continue
        # 비선점은 돌던 프로세스가 끝나기 전에는 다시 고르지 않는다
        if preemptive or current is None or current in finish:
            current = min(ready, key=lambda n: (remaining[n], arrival[n], order[n]))
        first_run.setdefault(current, time)
        if gantt and gantt[-1][0] == current:
            gantt[-1][2] = time + 1
        else:
            gantt.append([current, time, time + 1])
        remaining[current] -= 1
        time += 1
        if remaining[current] == 0:
            finish[current] = time
    return gantt, finish, first_run


def report_cpu(label, preemptive):
    gantt, finish, first_run = simulate_cpu(PROCESSES, preemptive)
    print(f"[{label}]")
    print("  간트 :", "  ".join(f"{n} {s}-{e}" for n, s, e in gantt))
    waits, turns, resps = [], [], []
    for name, arr, burst in PROCESSES:
        turn = finish[name] - arr
        waits.append(turn - burst)
        turns.append(turn)
        resps.append(first_run[name] - arr)
        print(f"  {name}: 도착 {arr} 실행 {burst} 종료 {finish[name]:>2}"
              f"  반환 {turn:>2}  대기 {turn - burst:>2}  응답 {first_run[name] - arr:>2}")
    n = len(PROCESSES)
    print(f"  평균 대기 {Fraction(sum(waits), n)} = {sum(waits) / n:.2f}"
          f"  평균 반환 {sum(turns) / n:.2f}  평균 응답 {sum(resps) / n:.2f}"
          f"  CPU 넘김 {len(gantt) - 1}회")
    print()


# ---------------------------------------------------------------- 디스크 쪽: SSTF
QUEUE = [98, 183, 37, 122, 14, 124, 65, 67]  # Silberschatz 10판 Ch.11 예제
HEAD = 53


def sstf(head, queue):
    pending, path, moved = list(queue), [], 0
    while pending:
        # 동률이면 큐에 먼저 들어온 쪽 (list 순서)
        nxt = min(pending, key=lambda c: (abs(c - head), pending.index(c)))
        moved += abs(nxt - head)
        head = nxt
        path.append(nxt)
        pending.remove(nxt)
    return path, moved


def fcfs_seek(head, queue):
    moved = 0
    for c in queue:
        moved += abs(c - head)
        head = c
    return moved


# ---------------------------------------------------------------- 디스크 쪽: SLTF
SECTORS = 8           # 트랙 하나의 섹터 수. 섹터 하나가 헤드 아래를 지나는 데 1단위
SAME_CYLINDER = [6, 1, 4, 7, 2]   # 한 실린더 안의 요청. 도착 순서. 각 1섹터
START_ANGLE = 0       # 지금 섹터 0의 시작이 헤드 아래에 있다


def rotate_wait(angle, sector):
    return (sector - angle) % SECTORS


def run_rotational(order, angle):
    """주어진 순서로 처리할 때 회전 지연 합과 걸린 시간."""
    total_latency, steps = 0, []
    for s in order:
        wait = rotate_wait(angle, s)
        total_latency += wait
        steps.append(f"{s}(대기 {wait})")
        angle = (s + 1) % SECTORS  # 1섹터 읽고 나면 다음 섹터 시작에 서 있다
    return steps, total_latency, total_latency + len(order)


def sltf_order(requests, angle):
    pending, order = list(requests), []
    while pending:
        nxt = min(pending, key=lambda s: (rotate_wait(angle, s), pending.index(s)))
        order.append(nxt)
        pending.remove(nxt)
        angle = (nxt + 1) % SECTORS
    return order


# ---------------------------------------------------------------- 탐색만 볼 때의 함정
SEEK_PER_CYL = Fraction(1, 2)   # 실린더 1칸 이동 = 0.5단위 (회전 한 바퀴 = 8단위)
FAR_SIDE = [("A", 12, 0), ("B", 16, 4)]  # (이름, 실린더, 섹터)
HEAD_CYL = 10


def positioning(head_cyl, angle, cyl, sector):
    seek = abs(cyl - head_cyl) * SEEK_PER_CYL
    arrive_angle = (angle + seek) % SECTORS
    latency = (sector - arrive_angle) % SECTORS
    return seek, latency


# ---------------------------------------------------------------- 기아 시험
def starve_sstf(limit=200):
    """헤드 옆(+3·-3 번갈아)에 새 요청이 계속 들어올 때 멀리 있는 190번이 처리되는가."""
    head, pending, sign = 100, [190, 103], 1
    for served in range(1, limit + 1):
        nxt = min(pending, key=lambda c: (abs(c - head), pending.index(c)))
        pending.remove(nxt)
        head = nxt
        if nxt == 190:
            return served
        sign = -sign
        pending.append(head + 3 * sign)
    return None


def starve_sltf(limit=200):
    """매번 헤드 바로 아래 섹터에 새 요청이 들어올 때, 가장 먼 섹터 7의 요청이 처리되는가."""
    angle, pending, seq = 0, [("old", 7)], 0
    for served in range(1, limit + 1):
        seq += 1
        pending.append((f"new{seq}", angle))  # 대기 0 — 늘 가장 먼저 뽑힐 자리
        nxt = min(pending, key=lambda r: (rotate_wait(angle, r[1]), pending.index(r)))
        pending.remove(nxt)
        angle = (nxt[1] + 1) % SECTORS
        if nxt[0] == "old":
            return served
    return None


def main():
    print(f"환경: Python {platform.python_version()} / {platform.system()} {platform.release()}")
    print("=" * 64)
    print("1. CPU — SJF(비선점)와 SRT(선점), 같은 4개 프로세스")
    print("=" * 64)
    report_cpu("SJF", preemptive=False)
    report_cpu("SRT", preemptive=True)

    print("=" * 64)
    print("2. 디스크 탐색 — SSTF, 헤드 53, 큐", QUEUE)
    print("=" * 64)
    path, moved = sstf(HEAD, QUEUE)
    print(f"  FCFS 이동 {fcfs_seek(HEAD, QUEUE)}")
    print(f"  SSTF 이동 {moved}  순서 {path}")
    print()

    print("=" * 64)
    print(f"3. 디스크 회전 — SLTF, 한 실린더, 트랙당 {SECTORS}섹터, 시작 각도 {START_ANGLE}")
    print("=" * 64)
    for label, order in (("FCFS", SAME_CYLINDER), ("SLTF", sltf_order(SAME_CYLINDER, START_ANGLE))):
        steps, latency, elapsed = run_rotational(order, START_ANGLE)
        print(f"  {label}: {' → '.join(steps)}")
        print(f"        회전 지연 합 {latency}  걸린 시간 {elapsed} (= {Fraction(elapsed, SECTORS)} 바퀴)")
    print()

    print("=" * 64)
    print(f"4. 탐색만 보면 생기는 일 — 헤드 실린더 {HEAD_CYL}, 각도 0, 1칸 탐색 {SEEK_PER_CYL}")
    print("=" * 64)
    costs = {}
    for name, cyl, sec in FAR_SIDE:
        seek, lat = positioning(HEAD_CYL, 0, cyl, sec)
        costs[name] = (seek, seek + lat)
        print(f"  {name}: 실린더 {cyl} 섹터 {sec}  탐색 {float(seek):.1f} + 회전 {float(lat):.1f}"
              f" = 위치 결정 {float(seek + lat):.1f}")
    by_seek = min(costs, key=lambda n: costs[n][0])
    by_total = min(costs, key=lambda n: costs[n][1])
    print(f"  SSTF 선택(탐색 최소): {by_seek}   탐색+회전 최소 선택: {by_total}")
    print()

    print("=" * 64)
    print("5. 기아 시험 — 200회 안에 처리 못 하면 None")
    print("=" * 64)
    print(f"  SSTF: 190번 요청이 처리된 순번 = {starve_sstf()}")
    print(f"  SLTF: 섹터 7 요청이 처리된 순번 = {starve_sltf()}  (한 바퀴 {SECTORS}섹터)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
