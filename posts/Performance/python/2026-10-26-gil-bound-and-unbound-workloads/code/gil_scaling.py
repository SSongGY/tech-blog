"""GIL 이 걸리는 작업과 안 걸리는 작업을 실측으로 가른다.

세 가지 작업(순수 계산 · 파일 입출력 · sleep)을 스레드와 프로세스로 각각
1·2·4 개씩 돌려 벽시계 시간을 재고, 마지막으로 작업 크기를 키워 가며
프로세스로 바꾸는 비용이 언제 회수되는지를 찾는다.
"""

import os
import platform
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

RULE = "=" * 70

CPU_LOOPS = 4_000_000      # 한 번에 0.2초 안팎이 되도록 고른 값
IO_BYTES = 4 * 1024 * 1024  # 4MiB 를 쓰고 다시 읽는다
IO_ROUNDS = 6
SLEEP_SEC = 0.25
REPEATS = 3                 # 흔들림을 줄이려고 세 번 재고 가장 빠른 값을 쓴다


def cpu_task(loops):
    """순수 계산. 바이트코드만 돌기 때문에 GIL 을 놓을 자리가 없다."""
    total = 0
    for i in range(loops):
        total += i * i
    return total


def io_task(args):
    """파일에 쓰고 다시 읽는다. 쓰기·읽기 동안 GIL 이 풀린다."""
    rounds, nbytes = args
    chunk = b"x" * nbytes
    read = 0
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "payload.bin")
        for _ in range(rounds):
            with open(path, "wb") as fp:
                fp.write(chunk)
                fp.flush()
                os.fsync(fp.fileno())
            with open(path, "rb") as fp:
                read += len(fp.read())
    return read


def sleep_task(seconds):
    """time.sleep 은 자는 동안 GIL 을 내놓는다."""
    time.sleep(seconds)
    return seconds


WORKLOADS = {
    "순수 계산": (cpu_task, CPU_LOOPS),
    "파일 입출력": (io_task, (IO_ROUNDS, IO_BYTES)),
    "sleep": (sleep_task, SLEEP_SEC),
}


def measure_serial(func, arg, count):
    """같은 작업을 한 스레드에서 연달아 count 번 한다 — 배속의 기준선."""
    times = []
    for _ in range(REPEATS):
        start = time.perf_counter()
        for _ in range(count):
            func(arg)
        times.append(time.perf_counter() - start)
    return min(times)


def measure(pool_cls, func, arg, workers, tasks=None):
    """같은 작업 tasks 개를 워커 workers 개에 던지고 전부 끝날 때까지를 잰다.

    풀 생성을 시간 안에 넣는다. 프로세스로 바꾸는 비용에는 기동 시간이
    포함되고, 그것을 빼고 재면 바꿀지 말지를 판단할 수 없기 때문이다.
    """
    tasks = workers if tasks is None else tasks
    times = []
    for _ in range(REPEATS):
        start = time.perf_counter()
        with pool_cls(max_workers=workers) as pool:
            list(pool.map(func, [arg] * tasks))
        times.append(time.perf_counter() - start)
    return min(times)


def print_environment():
    print(RULE)
    print("환경")
    print(RULE)
    print(f"  Python     {platform.python_version()} ({platform.python_implementation()})")
    print(f"  OS         {platform.system()} {platform.release()}")
    print(f"  CPU 코어   {os.cpu_count()}개 (논리)")
    gil = getattr(sys, "_is_gil_enabled", None)
    print(f"  GIL        {'켜짐' if gil is None or gil() else '꺼짐'}")
    print(f"  기동 방식  {__import__('multiprocessing').get_start_method()}")
    print()


def pad_to(name, width):
    """한글은 두 칸을 차지하므로 len 으로 맞추면 표가 어긋난다."""
    used = sum(2 if ord(ch) > 0x2000 else 1 for ch in name)
    return name + " " * max(0, width - used)


def print_serial_baseline():
    print(RULE)
    print("기준선 — 같은 작업을 한 스레드에서 4번 연달아 (초, 3회 중 최소)")
    print(RULE)
    base = {}
    for name, (func, arg) in WORKLOADS.items():
        base[name] = measure_serial(func, arg, 4)
        print(f"  {pad_to(name, 12)} {base[name]:7.3f}")
    print()
    return base


def print_scaling(pool_cls, label, base):
    print(RULE)
    print(f"{label} — 4개 작업을 워커 n 개로 (초, 3회 중 최소)")
    print(RULE)
    print(f"  {'작업':12s} | {'1개':>7s} | {'2개':>7s} | {'4개':>7s} | {'4개 배속':>9s}")
    print(f"  {'-' * 12}-+-{'-' * 7}-+-{'-' * 7}-+-{'-' * 7}-+-{'-' * 9}")
    rows = {}
    for name, (func, arg) in WORKLOADS.items():
        got = [measure(pool_cls, func, arg, w, tasks=4) for w in (1, 2, 4)]
        rows[name] = got
        print(
            f"  {pad_to(name, 12)} | {got[0]:7.3f} | {got[1]:7.3f} | {got[2]:7.3f} "
            f"| {base[name] / got[2]:8.2f}배"
        )
    print()
    return rows


def crossover():
    """프로세스로 바꾸는 비용이 언제 회수되는지 — 작업 크기를 키워 가며 본다."""
    print(RULE)
    print("작업 크기별 — 단일 / 스레드 4 / 프로세스 4 (초, 3회 중 최소)")
    print(RULE)
    print(f"  {'루프 수':>10s} | {'직렬':>7s} | {'스레드4':>8s} | {'프로세스4':>10s} | 더 빠른 쪽")
    print(f"  {'-' * 10}-+-{'-' * 7}-+-{'-' * 8}-+-{'-' * 10}-+-----------")
    for loops in (10_000, 100_000, 1_000_000, 4_000_000, 16_000_000):
        single = measure_serial(cpu_task, loops, 4)
        threaded = measure(ThreadPoolExecutor, cpu_task, loops, 4, tasks=4)
        processed = measure(ProcessPoolExecutor, cpu_task, loops, 4, tasks=4)
        winner = "프로세스4" if processed < threaded else "스레드4"
        print(
            f"  {loops:10,d} | {single:7.3f} | {threaded:8.3f} | {processed:10.3f} "
            f"| {winner}"
        )
    print()


def main():
    print_environment()
    base = print_serial_baseline()
    thread_rows = print_scaling(ThreadPoolExecutor, "스레드", base)
    process_rows = print_scaling(ProcessPoolExecutor, "프로세스", base)

    print(RULE)
    print("워커 4개일 때 스레드와 프로세스 중 어느 쪽이 빨랐나")
    print(RULE)
    for name in WORKLOADS:
        t, p = thread_rows[name][2], process_rows[name][2]
        faster = "스레드" if t < p else "프로세스"
        print(
            f"  {pad_to(name, 12)} 스레드 {t:6.3f}초 · 프로세스 {p:6.3f}초 "
            f"→ {faster}가 {max(t, p) / min(t, p):.2f}배 빠름"
        )
    print()

    crossover()


if __name__ == "__main__":
    main()
