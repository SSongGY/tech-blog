"""낙관적 잠금과 비관적 잠금의 비용이 어디서 갈리는지 재 본다.

DB 벤치마크가 아니다. 두 방식의 **비용 구조**만 떼어 내 같은 작업량으로
재는 모형이다. 저장소는 프로세스 안의 배열이고, 행 단위 원자적 갱신은
행마다 둔 자물쇠로 흉내 낸다. 읽고 쓰는 사이의 `sleep` 이 DB 왕복과
애플리케이션 처리에 해당한다.

의존성 없음. `python locking_crossover.py` 로 그대로 돌아간다.
"""

import platform
import random
import statistics
import sys
import threading
import time

ROWS = 64                 # 전체 행 수
THREADS = 16              # 동시에 도는 작업자
OPS_PER_THREAD = 40       # 작업자 한 명이 성공시켜야 하는 갱신 횟수
WORK_SECONDS = 0.002      # 읽고 쓰는 사이에 걸리는 시간
REPEATS = 3               # 같은 조건을 몇 번 돌려 중앙값을 쓸지
SEED = 20261013

TOTAL_UPDATES = THREADS * OPS_PER_THREAD


class Store:
    """행마다 값과 버전을 들고 있는 저장소.

    `compare_and_set` 이 DB 의 `UPDATE ... WHERE id=? AND version=?` 에
    해당한다. 버전이 어긋나면 아무 행도 안 고치고 거짓을 돌려준다.
    """

    def __init__(self, rows: int) -> None:
        self.values = [0] * rows
        self.versions = [0] * rows
        self._cell = [threading.Lock() for _ in range(rows)]
        self.row_locks = [threading.Lock() for _ in range(rows)]

    def read(self, row: int) -> tuple[int, int]:
        with self._cell[row]:
            return self.values[row], self.versions[row]

    def compare_and_set(self, row: int, value: int, version: int) -> bool:
        with self._cell[row]:
            if self.versions[row] != version:
                return False
            self.values[row] = value
            self.versions[row] += 1
            return True

    def write(self, row: int, value: int) -> None:
        with self._cell[row]:
            self.values[row] = value
            self.versions[row] += 1


def make_workload(hot_ratio: float, seed: int = SEED) -> list[list[int]]:
    """두 방식이 **똑같은** 순서로 같은 행을 건드리도록 미리 만들어 둔다."""
    rng = random.Random(seed)
    return [
        [0 if rng.random() < hot_ratio else rng.randrange(ROWS)
         for _ in range(OPS_PER_THREAD)]
        for _ in range(THREADS)
    ]


def _run_threads(workload: list[list[int]], worker) -> float:
    threads = [threading.Thread(target=worker, args=(t,)) for t in workload]
    start = time.perf_counter()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return time.perf_counter() - start


def run_optimistic(workload, pool_size: int):
    """읽을 때 잠그지 않고, 쓸 때 버전이 그대로인지 확인한다."""
    store = Store(ROWS)
    pool = threading.Semaphore(pool_size)
    tries_per_op: list[int] = []
    guard = threading.Lock()

    def worker(targets):
        local = []
        for row in targets:
            count = 0
            while True:
                count += 1
                with pool:
                    value, version = store.read(row)
                    time.sleep(WORK_SECONDS)
                    succeeded = store.compare_and_set(row, value + 1, version)
                if succeeded:
                    break
            local.append(count)
        with guard:
            tries_per_op.extend(local)

    elapsed = _run_threads(workload, worker)
    return elapsed, tries_per_op, store


def run_pessimistic(workload, pool_size: int):
    """읽기 전에 그 행을 잠그고, 다 쓸 때까지 쥐고 있는다."""
    store = Store(ROWS)
    pool = threading.Semaphore(pool_size)
    waits: list[float] = []
    guard = threading.Lock()

    def worker(targets):
        local = []
        for row in targets:
            with pool:
                start = time.perf_counter()
                with store.row_locks[row]:
                    local.append(time.perf_counter() - start)
                    value, _ = store.read(row)
                    time.sleep(WORK_SECONDS)
                    store.write(row, value + 1)
        with guard:
            waits.extend(local)

    elapsed = _run_threads(workload, worker)
    return elapsed, waits, store


def run_no_locking(workload):
    """아무것도 안 하면 무엇을 잃는지 보려고 같은 작업을 맨몸으로 돌린다."""
    store = Store(ROWS)

    def worker(targets):
        for row in targets:
            value, _ = store.read(row)
            time.sleep(WORK_SECONDS)
            store.write(row, value + 1)

    _run_threads(workload, worker)
    return store


def section(title: str) -> None:
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


def print_environment() -> None:
    section("환경과 조건")
    print(f"  Python   {platform.python_version()}")
    print(f"  OS       {platform.system()} {platform.release()}")
    print(f"  행 수            {ROWS}")
    print(f"  작업자(스레드)   {THREADS}")
    print(f"  작업자당 갱신    {OPS_PER_THREAD}회  (전체 {TOTAL_UPDATES}회)")
    print(f"  읽고 쓰는 사이   {WORK_SECONDS * 1000:.0f}ms")
    print(f"  같은 조건 반복   {REPEATS}회, 중앙값을 싣는다")
    print("\n  '핫 로우 비율' 은 전체 갱신 중 몇 %가 0번 행 하나로 몰리는지다.")
    print("  나머지는 64개 행에 고루 흩어진다. 두 방식은 같은 난수열로")
    print("  만든 똑같은 작업 목록을 받는다.")


def demo_lost_update() -> None:
    section("1. 아무것도 안 하면 갱신이 사라진다")
    work = make_workload(1.0)
    store = run_no_locking(work)
    print(f"  모든 작업자가 0번 행만 {TOTAL_UPDATES}회 올리도록 시켰다.")
    print(f"  기대한 값 : {TOTAL_UPDATES}")
    print(f"  실제 값   : {store.values[0]}")
    print(f"  사라진 갱신: {TOTAL_UPDATES - store.values[0]}회")
    print("\n  읽은 값을 들고 있는 사이 남이 먼저 고쳐 놓으면, 내가 쓰는 순간")
    print("  그 변경이 덮인다. 두 방식 모두 이것을 막으려고 있다.")


def _measure(ratio: float, pool_size: int):
    optimistic, pessimistic, tries, waits = [], [], [], []
    for repeat in range(REPEATS):
        work = make_workload(ratio, SEED + repeat)
        o_time, o_tries, o_store = run_optimistic(work, pool_size)
        p_time, p_waits, p_store = run_pessimistic(work, pool_size)
        # 둘 다 갱신을 하나도 잃지 않아야 한다. 아니면 측정이 무의미하다.
        assert sum(o_store.values) == TOTAL_UPDATES, "낙관 쪽 갱신 유실"
        assert sum(p_store.values) == TOTAL_UPDATES, "비관 쪽 갱신 유실"
        optimistic.append(o_time)
        pessimistic.append(p_time)
        tries.append(o_tries)
        waits.append(p_waits)
    flat_tries = tries[len(tries) // 2]
    flat_waits = waits[len(waits) // 2]
    return (statistics.median(optimistic), statistics.median(pessimistic),
            flat_tries, flat_waits)


RATIOS = (0.0, 0.10, 0.25, 0.50, 0.75, 1.0)


def demo_wall_clock() -> None:
    section(f"2. 커넥션이 넉넉할 때 (풀 {THREADS} = 스레드 수)")
    print(f"  {'핫 로우':>7} | {'낙관 초':>8} {'비관 초':>8} | "
          f"{'총 시도':>8} {'헛시도':>8} | {'한 건 최대':>10}")
    print("  " + "-" * 62)
    for ratio in RATIOS:
        o_time, p_time, tries, _ = _measure(ratio, THREADS)
        total = sum(tries)
        print(f"  {ratio * 100:6.0f}% | {o_time:8.2f} {p_time:8.2f} | "
              f"{total:8d} {total - TOTAL_UPDATES:8d} | {max(tries):10d}")
    print(f"\n  '총 시도' 는 낙관적 쪽이 읽고-일하고-쓰기를 몇 번 했는지다.")
    print(f"  성공해야 하는 갱신은 어느 줄에서나 {TOTAL_UPDATES}회로 같다.")


def demo_bounded_pool(pool_size: int = 4) -> None:
    section(f"3. 커넥션이 좁을 때 (풀 {pool_size}, 스레드 {THREADS})")
    print(f"  {'핫 로우':>7} | {'낙관 초':>8} {'비관 초':>8} | {'빠른 쪽':>8} | "
          f"{'총 시도':>8}")
    print("  " + "-" * 56)
    for ratio in RATIOS:
        o_time, p_time, tries, _ = _measure(ratio, pool_size)
        faster = "낙관" if o_time < p_time else "비관"
        gap = abs(o_time - p_time) / max(o_time, p_time) * 100
        label = f"{faster} {gap:.0f}%" if gap >= 3 else "비슷"
        print(f"  {ratio * 100:6.0f}% | {o_time:8.2f} {p_time:8.2f} | "
              f"{label:>8} | {sum(tries):8d}")


def demo_tail() -> None:
    section("4. 한 건이 겪는 재시도 횟수의 분포")
    print(f"  {'핫 로우':>7} | {'중앙값':>7} {'p95':>7} {'최대':>7} | "
          f"{'비관 대기 중앙값':>16} {'비관 대기 최대':>14}")
    print("  " + "-" * 68)
    for ratio in RATIOS:
        _, _, tries, waits = _measure(ratio, THREADS)
        ordered = sorted(tries)
        p95 = ordered[int(len(ordered) * 0.95)]
        print(f"  {ratio * 100:6.0f}% | {statistics.median(tries):7.0f} "
              f"{p95:7d} {max(tries):7d} | "
              f"{statistics.median(waits) * 1000:14.1f}ms "
              f"{max(waits) * 1000:12.1f}ms")


def main() -> None:
    print_environment()
    demo_lost_update()
    demo_wall_clock()
    demo_bounded_pool()
    demo_tail()


if __name__ == "__main__":
    sys.exit(main())
