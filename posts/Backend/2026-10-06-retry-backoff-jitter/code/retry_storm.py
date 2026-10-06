"""장애 직후 클라이언트 100개가 한꺼번에 재시도할 때 백오프 방식별로 무엇이 달라지는지 센다.

서버는 10ms 칸마다 요청 5개까지만 처리하고 나머지는 즉시 거절한다(과부하 응답).
거절된 클라이언트는 각자의 백오프 규칙대로 기다렸다가 다시 보낸다.
같은 시드로 돌리므로 매번 같은 결과가 나온다.
"""

import heapq
import random
from collections import Counter
from typing import Callable

CLIENT_COUNT = 100
SLOT_MS = 10
CAPACITY_PER_SLOT = 5      # 최소 100 / 5 = 20칸 = 200ms 는 걸린다
BASE_MS = 10
CAP_MS = 2000
MAX_ATTEMPTS = 50
SEED = 20261006

# (attempt, 직전 대기, 난수) -> 이번 대기(ms). attempt 는 실패한 횟수(1부터)
Backoff = Callable[[int, float, random.Random], float]


def no_backoff(attempt: int, prev: float, rng: random.Random) -> float:
    return BASE_MS


def exponential(attempt: int, prev: float, rng: random.Random) -> float:
    return min(CAP_MS, BASE_MS * 2 ** attempt)


def exponential_grpc_jitter(attempt: int, prev: float, rng: random.Random) -> float:
    # gRPC 연결 백오프처럼 계산값의 ±20% 만 흔든다
    backoff = min(CAP_MS, BASE_MS * 2 ** attempt)
    return backoff + rng.uniform(-0.2 * backoff, 0.2 * backoff)


def full_jitter(attempt: int, prev: float, rng: random.Random) -> float:
    return rng.uniform(0, min(CAP_MS, BASE_MS * 2 ** attempt))


def equal_jitter(attempt: int, prev: float, rng: random.Random) -> float:
    temp = min(CAP_MS, BASE_MS * 2 ** attempt)
    return temp / 2 + rng.uniform(0, temp / 2)


def decorrelated_jitter(attempt: int, prev: float, rng: random.Random) -> float:
    return min(CAP_MS, rng.uniform(BASE_MS, prev * 3))


STRATEGIES: list[tuple[str, Backoff]] = [
    ("고정 10ms", no_backoff),
    ("지수", exponential),
    ("지수 + ±20%", exponential_grpc_jitter),
    ("지수 + 전체 지터", full_jitter),
    ("지수 + 절반 지터", equal_jitter),
    ("비상관 지터", decorrelated_jitter),
]


def simulate(backoff: Backoff, seed: int = SEED) -> dict:
    rng = random.Random(seed)
    # (보낸 시각 ms, 클라이언트 번호, 시도 횟수, 직전 대기)
    queue = [(0.0, cid, 1, float(BASE_MS)) for cid in range(CLIENT_COUNT)]
    heapq.heapify(queue)
    slot_load: Counter = Counter()
    accepted_in_slot: Counter = Counter()
    total_calls = 0
    finished_at = 0.0
    gave_up = 0
    while queue:
        sent_at, cid, attempt, prev = heapq.heappop(queue)
        slot = int(sent_at // SLOT_MS)
        total_calls += 1
        slot_load[slot] += 1
        if accepted_in_slot[slot] < CAPACITY_PER_SLOT:
            accepted_in_slot[slot] += 1
            finished_at = max(finished_at, sent_at)
            continue
        if attempt >= MAX_ATTEMPTS:
            gave_up += 1
            continue
        wait = backoff(attempt, prev, rng)
        heapq.heappush(queue, (sent_at + wait, cid, attempt + 1, wait))
    busy_slots = [n for n in slot_load.values()]
    return {
        "calls": total_calls,
        "finished_ms": finished_at,
        "peak": max(busy_slots),
        "gave_up": gave_up,
        "slot_load": slot_load,
    }


def print_timeline(name: str, slot_load: Counter, upto_ms: int) -> None:
    """앞쪽 구간의 칸별 요청 수. 5 를 넘는 칸은 그만큼 거절된 것이다."""
    print(f"\n  [{name}] 0~{upto_ms}ms 칸별 요청 수 (10ms 칸, 처리 한도 {CAPACITY_PER_SLOT})")
    cells = [slot_load.get(s, 0) for s in range(upto_ms // SLOT_MS)]
    for start in range(0, len(cells), 20):
        row = cells[start:start + 20]
        print(f"   {start*SLOT_MS:5d}ms: " + " ".join(f"{n:3d}" for n in row))


def main() -> None:
    print(f"클라이언트 {CLIENT_COUNT}, 처리 한도 {CAPACITY_PER_SLOT}건/{SLOT_MS}ms, "
          f"base {BASE_MS}ms, cap {CAP_MS}ms, 최대 {MAX_ATTEMPTS}회, 시드 {SEED}")
    print(f"이론 하한: 호출 {CLIENT_COUNT}회, 완료 {CLIENT_COUNT // CAPACITY_PER_SLOT * SLOT_MS - SLOT_MS}ms 칸")

    print("\n== 1. 방식별 총 호출 수 · 완료 시각 · 최대 칸 부하 ==")
    print("  방식              | 총 호출 | 완료(ms) | 최대 칸 | 포기")
    results = {}
    for name, backoff in STRATEGIES:
        r = simulate(backoff)
        results[name] = r
        print(f"  {name:<16} | {r['calls']:7d} | {r['finished_ms']:8.0f} | {r['peak']:7d} | {r['gave_up']:4d}")

    print("\n== 2. 지터가 없으면 재시도가 같은 칸에 몰린다 ==")
    print_timeline("지수", results["지수"]["slot_load"], 400)
    print_timeline("지수 + 전체 지터", results["지수 + 전체 지터"]["slot_load"], 400)

    print("\n== 3. 시드를 바꿔도 순위가 같은가 (전체 지터 vs 절반 지터 vs ±20%) ==")
    print("  시드     | 전체 지터 호출/완료 | 절반 지터 호출/완료 | ±20% 호출/완료")
    for seed in (1, 2, 3, 4, 5):
        full = simulate(full_jitter, seed)
        equal = simulate(equal_jitter, seed)
        grpc = simulate(exponential_grpc_jitter, seed)
        print(f"  {seed:8d} | {full['calls']:5d} / {full['finished_ms']:6.0f}ms "
              f"| {equal['calls']:5d} / {equal['finished_ms']:6.0f}ms "
              f"| {grpc['calls']:5d} / {grpc['finished_ms']:6.0f}ms")


if __name__ == "__main__":
    main()
