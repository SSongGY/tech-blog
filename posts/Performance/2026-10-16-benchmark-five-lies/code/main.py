"""같은 코드로 다른 숫자를 만들어 내는 다섯 가지 방법.

측정 단계(준비 → 컴파일 → 측정 구간 → 반복 → 집계)마다 하나씩 짚는다.
난수는 전부 시드를 고정했으므로 몇 번을 돌려도 같은 데이터가 쓰인다.
절대 시간은 기계마다 다르지만 **배수와 대소 관계는 같아야 한다.**
"""

from __future__ import annotations

import dis
import gc
import platform
import random
import statistics
import sys
import time
import timeit

RULE = "=" * 64
REPEAT = 9


def section(title: str) -> None:
    print(RULE)
    print(title)
    print(RULE)


def median_ms(fn, rounds: int = REPEAT) -> float:
    out = []
    for _ in range(rounds):
        start = time.perf_counter()
        fn()
        out.append((time.perf_counter() - start) * 1000)
    return statistics.median(out)


def print_environment() -> None:
    section("환경")
    print(f"  Python   {platform.python_version()} ({sys.implementation.name})")
    print(f"  OS       {platform.system()} {platform.release()}")
    for name in ("perf_counter", "time"):
        info = time.get_clock_info(name)
        print(f"  {name:13s} {info.implementation}  해상도 {info.resolution}")
    print()


def lie1_unrepresentative_data() -> None:
    section("거짓말 1 — 준비: 데이터가 대표적이지 않다")
    rnd = random.Random(0)
    shuffled = [rnd.random() for _ in range(300_000)]
    ordered = sorted(shuffled)

    def sort_only(data: list[float]) -> float:
        """사본 만들기는 측정 구간 밖에 둔다. 그것까지 재면 정렬을 재는 게 아니다."""
        out = []
        for _ in range(REPEAT):
            copy = list(data)
            start = time.perf_counter()
            copy.sort()
            out.append((time.perf_counter() - start) * 1000)
        return statistics.median(out)

    a, b = sort_only(shuffled), sort_only(ordered)
    print(f"  30만 개 무작위 입력 정렬 : {a:8.3f} ms")
    print(f"  30만 개 정렬된 입력 정렬 : {b:8.3f} ms")
    print(f"  같은 list.sort() 인데 {a / b:.1f}배")
    print()


def lie2_constant_folding() -> None:
    section("거짓말 2 — 컴파일: 재려던 식이 이미 계산돼 있다")
    const = min(timeit.repeat("2 ** 20", number=1_000_000, repeat=REPEAT))
    var = min(timeit.repeat("x ** 20", setup="x = 2", number=1_000_000, repeat=REPEAT))
    print(f"  '2 ** 20'  (리터럴) : {const:8.4f} s / 100만회")
    print(f"  'x ** 20'  (변수)   : {var:8.4f} s / 100만회")
    print(f"  {var / const:.1f}배 차이")
    print()
    print("  바이트코드를 보면 이유가 보인다.")
    print("  --- compile('2 ** 20') ---")
    dis.dis(compile("2 ** 20", "<bench>", "eval"))
    print("  --- compile('x ** 20') ---")
    dis.dis(compile("x ** 20", "<bench>", "eval"))
    print()


def lie3_timer_cost() -> None:
    section("거짓말 3 — 측정 구간: 타이머 비용이 섞인다")
    reps = 200_000
    start = time.perf_counter()
    for _ in range(reps):
        time.perf_counter()
    timer_ns = (time.perf_counter() - start) / reps * 1e9

    x = 41
    one_shot = []
    for _ in range(2001):
        start = time.perf_counter()
        _ = x + 1
        one_shot.append(time.perf_counter() - start)
    single_ns = statistics.median(one_shot) * 1e9

    amortized_ns = min(
        timeit.repeat("x + 1", setup="x = 41", number=1_000_000, repeat=REPEAT)
    ) / 1_000_000 * 1e9

    print(f"  perf_counter 해상도            : "
          f"{time.get_clock_info('perf_counter').resolution * 1e9:8.1f} ns")
    print(f"  perf_counter() 호출 한 번      : {timer_ns:8.1f} ns")
    print(f"  'x + 1' 을 한 번만 재기        : {single_ns:8.1f} ns")
    print(f"  100만 번 돌려 나누기           : {amortized_ns:8.1f} ns")
    print(f"  한 번만 재면 {single_ns / amortized_ns:.1f}배로 부풀려진다")
    print()
    buckets: dict[int, int] = {}
    for value in one_shot:
        key = round(value * 1e9 / 100) * 100   # 100ns 눈금으로 묶는다
        buckets[key] = buckets.get(key, 0) + 1
    print("  한 번만 잰 2,001회가 어떤 값으로 나왔는가 (상위 5개)")
    for key, count in sorted(buckets.items(), key=lambda kv: -kv[1])[:5]:
        print(f"    {key:6d} ns : {count:5d}회")
    print()


def lie4_missing_warmup() -> list[float]:
    section("거짓말 4 — 반복: 웜업 회차가 그대로 섞인다")
    import re

    first, second = [], []
    pattern = r"(\d{4})-(\d{2})-(\d{2})"
    text = "주문일자 2026-10-16 확인"
    for _ in range(REPEAT):
        re.purge()                      # 정규식 캐시를 비워 '처음'을 다시 만든다
        start = time.perf_counter()
        re.search(pattern, text)
        first.append((time.perf_counter() - start) * 1e6)
        start = time.perf_counter()
        re.search(pattern, text)
        second.append((time.perf_counter() - start) * 1e6)
    f, s = statistics.median(first), statistics.median(second)
    print(f"  캐시를 비운 뒤 첫 re.search : {f:8.2f} us")
    print(f"  바로 다음 re.search        : {s:8.2f} us")
    print(f"  {f / s:.0f}배")
    print()


def lie5_summary_and_conditions() -> None:
    section("거짓말 5 — 집계: 대푯값과 측정 조건")

    def build():
        return len([{"id": i, "v": [i, i + 1]} for i in range(40_000)])

    runs = []
    for _ in range(60):
        start = time.perf_counter()
        build()
        runs.append((time.perf_counter() - start) * 1000)
    print("  40,000개 dict 생성 60회의 분포")
    print(f"    평균 {statistics.mean(runs):.3f} ms · 중앙값 {statistics.median(runs):.3f} ms"
          f" · 최소 {min(runs):.3f} ms · 최대 {max(runs):.3f} ms")
    print(f"    최대/최소 {max(runs) / min(runs):.2f}배 · "
          f"평균/중앙값 {statistics.mean(runs) / statistics.median(runs):.3f}배")
    print()

    def alloc():
        return [[i] for i in range(200_000)]

    def with_gc(enabled: bool) -> float:
        out = []
        for _ in range(REPEAT):
            gc.collect()
            gc.enable() if enabled else gc.disable()
            start = time.perf_counter()
            alloc()
            out.append((time.perf_counter() - start) * 1000)
            gc.enable()
        return statistics.median(out)

    on, off = with_gc(True), with_gc(False)
    print("  timeit 은 측정 중 GC 를 꺼 둔다 (공식 문서)")
    print(f"    GC 켜짐 : {on:8.3f} ms   ← 운영에서 도는 조건")
    print(f"    GC 꺼짐 : {off:8.3f} ms   ← timeit 기본 조건")
    print(f"    {on / off:.2f}배")
    print()


def main() -> None:
    print_environment()
    lie1_unrepresentative_data()
    lie2_constant_folding()
    lie3_timer_cost()
    lie4_missing_warmup()
    lie5_summary_and_conditions()


if __name__ == "__main__":
    main()
