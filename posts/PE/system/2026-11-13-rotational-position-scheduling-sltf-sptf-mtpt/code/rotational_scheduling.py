"""회전 위치 최적화 검산 — SLTF·MTPT·SSTF·SPTF·WSTF.

시간 단위는 '회전 한 바퀴 = 1'(1부) 또는 '섹터 하나가 지나가는 시간 = 1'(2~4부)이다.
표준 라이브러리만 쓴다.
"""

import itertools
import random
import sys
from fractions import Fraction as Fr


# ── 1부. 고정 헤드 드럼: SLTF 와 MTPT ─────────────────────────────
# 레코드는 (시작 각도, 끝 각도). 각도는 둘레를 1 로 둔 [0, 1) 위치다.
# 헤드는 시각 0 에 각도 0 에 있고, 드럼은 한 방향으로 돈다.

def run_order(records, order):
    """주어진 순서로 처리할 때 마지막 레코드가 끝나는 시각."""
    clock = Fr(0)
    for idx in order:
        start, end = records[idx]
        angle = clock % 1
        clock += (start - angle) % 1          # 회전 지연: 시작 각도가 올 때까지
        clock += (end - start) % 1            # 전송: 끝 각도까지 읽는다
    return clock


def sltf_order(records):
    """매번 지금 각도에서 가장 먼저 시작 각도가 오는 레코드를 고른다."""
    clock, left, order = Fr(0), set(range(len(records))), []
    while left:
        angle = clock % 1
        nxt = min(sorted(left), key=lambda i: (records[i][0] - angle) % 1)
        order.append(nxt)
        left.remove(nxt)
        start, end = records[nxt]
        clock += (start - angle) % 1 + (end - start) % 1
    return order


def mtpt_brute(records):
    """정의대로: 모든 순서 가운데 총처리시간이 가장 짧은 것.

    Fuller 의 MTPT0 는 O(N log N) 알고리즘이지만 여기서는 구현하지 않고
    정의를 그대로 대입해 최소값을 찾는다. 레코드가 적을 때만 쓸 수 있다.
    """
    return min(itertools.permutations(range(len(records))),
               key=lambda o: (run_order(records, o), o))


def find_widest_gap(size=3, grid=8):
    """1/grid 격자 위 레코드 size 개 가운데 SLTF 와 MTPT 의 차이가 가장 큰 묶음.

    손으로 골라 '그럴듯한' 예를 만들지 않으려고, 격자를 전부 훑어 찾는다.
    시작 각도가 겹치면 동률 처리 규칙이 결과를 정하므로 서로 다른 것만 본다.
    차이가 같으면 먼저 나온 묶음을 쓴다.
    """
    cells = [(Fr(s, grid), Fr((s + l) % grid, grid))
             for s in range(1, grid) for l in range(1, grid)]
    best, best_gap = None, Fr(-1)
    for combo in itertools.combinations(cells, size):
        if len({start for start, _ in combo}) < size:
            continue
        records = list(combo)
        gap = run_order(records, sltf_order(records)) - run_order(records, mtpt_brute(records))
        if gap > best_gap:
            best, best_gap = records, gap
    return best


def part1_hand_example():
    print("[1부] 고정 헤드 드럼 — 레코드 3개, 헤드는 각도 0")
    records = find_widest_gap()
    names = "ABC"
    for name, (s, e) in zip(names, records):
        print(f"  {name}: 시작 {s}  끝 {e}")
    for label, order in (("SLTF", sltf_order(records)), ("MTPT", mtpt_brute(records))):
        seq = " → ".join(names[i] for i in order)
        print(f"  {label}: {seq}  총처리시간 {run_order(records, order)} 바퀴")
    print()


def part1_random_batches(trials=2000, size=5, seed=7):
    """Fuller 요약본 §3 의 가정(시작 각도 균등, 길이 지수분포 평균 1/2)으로
    레코드를 만들되, 새 요청 도착 없이 한 묶음만 처리한다."""
    rng = random.Random(seed)
    worse, gaps = 0, []
    for _ in range(trials):
        records = []
        for _ in range(size):
            start = Fr(rng.randrange(64), 64)
            length = Fr(min(63, max(1, round(rng.expovariate(2) * 64))), 64)
            records.append((start, (start + length) % 1))
        sltf = run_order(records, sltf_order(records))
        best = run_order(records, mtpt_brute(records))
        if sltf > best:
            worse += 1
            gaps.append(sltf - best)
    print(f"[1부] 무작위 묶음 {trials}개 (레코드 {size}개, 도착 없음)")
    print(f"  SLTF 가 MTPT 보다 길었던 묶음: {worse}개 ({worse / trials:.1%})")
    print(f"  길었던 묶음의 평균 차이: {float(sum(gaps) / len(gaps)):.3f} 바퀴"
          f"  최대 차이: {float(max(gaps)):.3f} 바퀴")
    print()


# ── 2~4부. 이동 헤드 디스크: 탐색 + 회전 ─────────────────────────
SECTORS = 12                       # 트랙당 섹터 수. 섹터 하나 = 시간 1


def positioning(head_cyl, head_angle, cyl, sector, seek_per_cyl):
    """탐색 시간과, 탐색이 끝난 뒤 목표 섹터가 올 때까지의 회전 지연."""
    seek = abs(cyl - head_cyl) * seek_per_cyl
    angle_after = (head_angle + seek) % SECTORS
    rotate = (sector - angle_after) % SECTORS
    return seek, rotate


def part2_sstf_vs_sptf():
    print("[2부] SSTF 와 SPTF — 헤드: 실린더 0, 섹터 6 시작 위치")
    reqs = {"X": (1, 5), "Y": (2, 9)}
    for name, (c, s) in reqs.items():
        print(f"  요청 {name}: 실린더 {c} 섹터 {s}")
    print("  1칸 탐색 | X 탐색+회전 | Y 탐색+회전 | SSTF | SPTF")
    for seek_per_cyl in (0.5, 1, 2, 3, 4, 6):
        cost = {}
        cells = []
        for name, (c, s) in reqs.items():
            seek, rot = positioning(0, 6, c, s, seek_per_cyl)
            cost[name] = seek + rot
            cells.append(f"{seek:>4} + {rot:>4} = {seek + rot:>4}")
        sptf = min(cost, key=cost.get)
        print(f"  {seek_per_cyl:>8} | {cells[0]} | {cells[1]} |  X   |  {sptf}")
    print()


def part3_wstf_weight():
    print("[3부] WSTF 가중 시간 TW = Treal × (M − E) / M,  M = 30초")
    M = 30.0
    rows = [("가까운 새 요청", 2.0, 0.0), ("먼 오래된 요청", 12.0, 20.0),
            ("먼 오래된 요청", 12.0, 28.0)]
    for label, treal, elapsed in rows:
        tw = treal * (M - elapsed) / M
        print(f"  {label}: Treal {treal:>4}ms  E {elapsed:>4}초  →  TW {tw:.2f}")
    print()


def simulate(policy, steps=20000, queue=20, cyls=100, seed=11):
    """닫힌 계: 요청 하나를 처리하면 무작위 위치에 새 요청 하나가 들어온다."""
    rng = random.Random(seed)
    seek_per_cyl = 0.1
    seek_base = 1.0

    def cost(head_c, head_a, c, s):
        seek = 0.0 if c == head_c else seek_base + abs(c - head_c) * seek_per_cyl
        rot = (s - (head_a + seek)) % SECTORS
        return seek, rot

    clock, head_c, head_a = 0.0, 0, 0.0
    pending = [(rng.randrange(cyls), rng.randrange(SECTORS), 0.0) for _ in range(queue)]
    waits, busy = [], 0.0
    max_age = 3000.0                                  # WSTF 의 M
    for _ in range(steps):
        def key(req):
            c, s, born = req
            seek, rot = cost(head_c, head_a, c, s)
            if policy == "SSTF":
                return (abs(c - head_c), seek + rot)
            if policy == "SPTF":
                return (seek + rot,)
            age = min(clock - born, max_age - 1e-9)   # WSTF
            return ((seek + rot) * (max_age - age) / max_age,)
        req = min(pending, key=key)
        pending.remove(req)
        c, s, born = req
        seek, rot = cost(head_c, head_a, c, s)
        service = seek + rot + 1                       # 1 섹터 전송
        clock += service
        busy += service
        head_c, head_a = c, (s + 1) % SECTORS
        waits.append(clock - born)
        pending.append((rng.randrange(cyls), rng.randrange(SECTORS), clock))
    waits.sort()
    return busy / steps, sum(waits) / steps, waits[int(steps * 0.99)], waits[-1]


def part4_simulation():
    print("[4부] 큐 20개 유지, 요청 20000개 처리 (실린더 100, 트랙당 12섹터)")
    print("  탐색 = 1 + 0.1×거리, 회전 한 바퀴 = 12, WSTF 의 M = 3000")
    print("  정책 | 요청당 처리 시간 | 평균 응답 | 99% 응답 | 최대 응답")
    for policy in ("SSTF", "SPTF", "WSTF"):
        per, mean, p99, worst = simulate(policy)
        print(f"  {policy} | {per:>16.2f} | {mean:>9.1f} | {p99:>8.1f} | {worst:>9.1f}")
    print()


if __name__ == "__main__":
    print(f"Python {sys.version.split()[0]}")
    print()
    part1_hand_example()
    part1_random_batches()
    part2_sstf_vs_sptf()
    part3_wstf_weight()
    part4_simulation()
