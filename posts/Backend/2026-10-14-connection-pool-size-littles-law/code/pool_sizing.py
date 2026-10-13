"""커넥션 풀 크기를 바꿔 가며 처리량과 응답시간을 재고, 리틀의 법칙으로 검산한다.

구조는 닫힌 계(closed system)다. 풀 크기만큼의 워커가 쉬지 않고 요청을 던지므로
계 안에 머무는 요청 수 L 은 항상 풀 크기와 같다. 그러면 리틀의 법칙 L = λW 로
처리량 λ 와 평균 응답시간 W 를 서로 검산할 수 있다.

백엔드는 동시에 CAPACITY 건까지만 실제로 처리한다. 그 이상은 자리가 날 때까지
기다린다. DB 서버의 CPU·디스크처럼 늘릴 수 없는 자원을 흉내 낸 것이다.

자리를 기다리는 방식은 두 가지를 둔다. 깨우는 순서를 보장하지 않는 세마포어와,
먼저 온 쪽이 먼저 들어가는 FIFO 대기열이다. 둘의 평균은 같고 분포는 다르다.
"""

import statistics
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor

CAPACITY = 4              # 백엔드가 실제로 동시에 처리할 수 있는 건수
SERVICE_TIME = 0.015      # 한 건을 처리하는 데 드는 시간(초)
JOBS_PER_RUN = 300        # 한 번의 측정에서 처리하는 요청 수
POOL_SIZES = [1, 2, 4, 8, 16, 32, 64]

RULE = "=" * 84


class SemaphoreGate:
    """자리 수만 세는 문. 기다리던 것 중 누구를 깨울지는 정해 두지 않는다."""

    name = "세마포어"

    def __init__(self, capacity):
        self._slots = threading.Semaphore(capacity)

    def __enter__(self):
        self._slots.acquire()

    def __exit__(self, *exc):
        self._slots.release()


class FifoGate:
    """먼저 기다리기 시작한 쪽이 먼저 들어가도록 줄을 세우는 문."""

    name = "FIFO 대기열"

    def __init__(self, capacity):
        self._capacity = capacity
        self._busy = 0
        self._waiting = deque()
        self._lock = threading.Lock()

    def __enter__(self):
        with self._lock:
            if self._busy < self._capacity:
                self._busy += 1
                return
            ticket = threading.Event()
            self._waiting.append(ticket)
        ticket.wait()

    def __exit__(self, *exc):
        with self._lock:
            if self._waiting:
                self._waiting.popleft().set()   # 자리를 그대로 넘겨준다
            else:
                self._busy -= 1


def measure(gate_class, pool_size):
    """풀 크기 하나에 대해 처리량과 응답시간 분포를 잰다."""
    gate = gate_class(CAPACITY)
    latencies = []
    latencies_lock = threading.Lock()

    def one_request(_index):
        started = time.perf_counter()
        with gate:
            time.sleep(SERVICE_TIME)
        elapsed = time.perf_counter() - started
        with latencies_lock:
            latencies.append(elapsed)

    run_started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=pool_size) as pool:
        list(pool.map(one_request, range(JOBS_PER_RUN)))
    wall_clock = time.perf_counter() - run_started

    ordered = sorted(latencies)
    throughput = JOBS_PER_RUN / wall_clock          # λ (건/초)
    mean_latency = statistics.fmean(ordered)        # W (초)
    return {
        "pool_size": pool_size,
        "throughput": throughput,
        "mean": mean_latency,
        "median": statistics.median(ordered),
        "p95": ordered[int(len(ordered) * 0.95) - 1],
        "max": ordered[-1],
        "little_l": throughput * mean_latency,      # L = λW
    }


def print_rows(rows):
    print("  풀 크기 | 처리량(건/초) | 평균(ms) | 중앙값(ms) | p95(ms) | 최대(ms)")
    print("  " + "-" * 68)
    for row in rows:
        print(
            f"  {row['pool_size']:>7} | {row['throughput']:>13.1f} | "
            f"{row['mean'] * 1000:>8.1f} | {row['median'] * 1000:>10.1f} | "
            f"{row['p95'] * 1000:>7.1f} | {row['max'] * 1000:>8.1f}"
        )


def main():
    print(RULE)
    print("조건")
    print(RULE)
    print(f"  백엔드 동시 처리 한도  {CAPACITY}건")
    print(f"  한 건 처리 시간        {SERVICE_TIME * 1000:.0f}ms")
    print(f"  측정당 요청 수         {JOBS_PER_RUN}건")
    print(f"  이론상 최대 처리량     {CAPACITY / SERVICE_TIME:.0f}건/초")
    print()

    print(RULE)
    print("① 풀 크기별 측정 — 자리를 세마포어로 기다릴 때")
    print(RULE)
    semaphore_rows = [measure(SemaphoreGate, size) for size in POOL_SIZES]
    print_rows(semaphore_rows)
    print()

    print(RULE)
    print("② 리틀의 법칙으로 검산 — 닫힌 계이므로 L 은 풀 크기와 같아야 한다")
    print(RULE)
    print("  풀 크기 | L = λ × W | 풀 크기 대비 오차")
    print("  " + "-" * 44)
    for row in semaphore_rows:
        error = (row["little_l"] - row["pool_size"]) / row["pool_size"] * 100
        print(f"  {row['pool_size']:>7} | {row['little_l']:>9.2f} | {error:>+16.1f}%")
    print()

    print(RULE)
    print("③ 같은 조건에서 대기 순서만 FIFO 로 바꾸면")
    print(RULE)
    fifo_rows = [measure(FifoGate, size) for size in POOL_SIZES]
    print_rows(fifo_rows)
    print()

    print(RULE)
    print("④ 두 방식 비교 — 평균은 같은가, 분포는 같은가")
    print(RULE)
    print("  풀 크기 | 평균 차이(ms) | 세마포어 중앙값 | FIFO 중앙값 | 세마포어 최대 | FIFO 최대")
    print("  " + "-" * 88)
    for left, right in zip(semaphore_rows, fifo_rows):
        print(
            f"  {left['pool_size']:>7} | "
            f"{(left['mean'] - right['mean']) * 1000:>+13.1f} | "
            f"{left['median'] * 1000:>15.1f} | {right['median'] * 1000:>11.1f} | "
            f"{left['max'] * 1000:>13.1f} | {right['max'] * 1000:>9.1f}"
        )
    print()

    best = max(semaphore_rows, key=lambda r: r["throughput"])
    saturating = next(
        r for r in semaphore_rows if r["throughput"] >= best["throughput"] * 0.95
    )
    largest = semaphore_rows[-1]
    print(RULE)
    print("⑤ 풀을 키워서 얻은 것과 잃은 것")
    print(RULE)
    print(f"  최대 처리량의 95%에 닿은 가장 작은 풀   {saturating['pool_size']}")
    print(f"  풀을 {saturating['pool_size']} -> {largest['pool_size']} 로 키웠을 때")
    print(
        f"    처리량    {saturating['throughput']:.1f} -> {largest['throughput']:.1f} 건/초 "
        f"({largest['throughput'] / saturating['throughput']:.2f}배)"
    )
    print(
        f"    평균 응답 {saturating['mean'] * 1000:.1f} -> {largest['mean'] * 1000:.1f} ms "
        f"({largest['mean'] / saturating['mean']:.1f}배)"
    )


if __name__ == "__main__":
    main()
