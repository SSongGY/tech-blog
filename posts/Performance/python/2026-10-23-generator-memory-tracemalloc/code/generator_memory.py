"""같은 처리를 리스트로 담을 때와 제너레이터로 흘릴 때의 최대 메모리를 잰다.

tracemalloc 은 파이썬이 잡은 메모리만 센다. 그래서 '이 코드가 무엇을 들고
있는가'를 보기에는 맞고, 프로세스 전체의 RSS 와는 다른 값이다.
한 번만 훑는 작업과 두 번 훑어야 하는 작업을 각각 재서, 제너레이터가
이득을 보는 자리와 손해를 보는 자리를 가른다.
"""

from __future__ import annotations

import itertools
import platform
import sys
import time
import tracemalloc

RULE = "=" * 70
RECORD_COUNT = 200_000


def make_records(count: int):
    """로그 한 줄을 흉내 낸 dict 를 count 개 만들어 흘린다."""
    for i in range(count):
        yield {"id": i, "level": "ERROR" if i % 7 == 0 else "INFO", "bytes": i % 997}


def measure(label: str, func) -> tuple[object, int, int, float]:
    """func 을 돌리며 현재/최대 메모리와 소요 시간을 잰다."""
    tracemalloc.start()
    tracemalloc.reset_peak()
    started = time.perf_counter()
    result = func()
    elapsed = time.perf_counter() - started
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"  {label:38s} 최대 {peak / 1024:10,.1f} KiB   {elapsed * 1000:7.1f} ms")
    return result, current, peak, elapsed


def section(title: str) -> None:
    print(RULE)
    print(title)
    print(RULE)


def one_pass() -> None:
    section("1. 한 번만 훑는 작업 — 오류 줄의 바이트 합계")

    def with_list() -> int:
        records = [r for r in make_records(RECORD_COUNT)]
        errors = [r for r in records if r["level"] == "ERROR"]
        return sum(r["bytes"] for r in errors)

    def with_generator() -> int:
        records = make_records(RECORD_COUNT)
        errors = (r for r in records if r["level"] == "ERROR")
        return sum(r["bytes"] for r in errors)

    total_list, _, peak_list, _ = measure("리스트로 전부 담고 처리", with_list)
    total_gen, _, peak_gen, _ = measure("제너레이터로 흘리며 처리", with_generator)
    print(f"  두 방식의 결과가 같은가: {total_list == total_gen}  (합계 {total_list:,})")
    print(f"  최대 메모리 비율: {peak_list / peak_gen:,.1f}배")
    print()


def two_passes() -> None:
    section("2. 두 번 훑어야 하는 작업 — 합계를 구한 뒤 평균 초과분을 센다")

    def with_list() -> tuple[int, int]:
        records = [r for r in make_records(RECORD_COUNT)]
        total = sum(r["bytes"] for r in records)
        average = total / len(records)
        above = sum(1 for r in records if r["bytes"] > average)
        return total, above

    def with_regenerate() -> tuple[int, int]:
        # 제너레이터는 한 번 소진되면 다시 못 쓴다. 두 번째 훑기를 위해 새로 만든다.
        total = sum(r["bytes"] for r in make_records(RECORD_COUNT))
        average = total / RECORD_COUNT
        above = sum(1 for r in make_records(RECORD_COUNT) if r["bytes"] > average)
        return total, above

    def with_tee() -> tuple[int, int]:
        first, second = itertools.tee(make_records(RECORD_COUNT), 2)
        total = sum(r["bytes"] for r in first)
        average = total / RECORD_COUNT
        above = sum(1 for r in second if r["bytes"] > average)
        return total, above

    a, _, _, t_list = measure("리스트로 담고 두 번 훑기", with_list)
    b, _, _, t_regen = measure("제너레이터를 두 번 만들기", with_regenerate)
    c, _, _, t_tee = measure("itertools.tee 로 갈라 쓰기", with_tee)
    print(f"  세 방식의 결과가 같은가: {a == b == c}  {a}")
    print(f"  리스트 대비 소요 시간 — 재생성 {t_regen / t_list:,.2f}배 · tee {t_tee / t_list:,.2f}배")
    print()


def costly_source() -> None:
    section("2-b. 원천이 비쌀 때 — 레코드 하나를 만드는 데 계산이 붙으면")

    def make_costly(count: int):
        for i in range(count):
            # 원천이 비싼 상황을 흉내 낸다. 파싱·복호화·원격 호출 자리라고 보면 된다.
            digest = sum(ord(ch) * (k + 1) for k, ch in enumerate(f"record-{i}"))
            yield {"id": i, "level": "ERROR" if i % 7 == 0 else "INFO", "bytes": digest % 997}

    count = 50_000

    def with_list() -> tuple[int, int]:
        records = [r for r in make_costly(count)]
        total = sum(r["bytes"] for r in records)
        above = sum(1 for r in records if r["bytes"] > total / len(records))
        return total, above

    def with_regenerate() -> tuple[int, int]:
        total = sum(r["bytes"] for r in make_costly(count))
        above = sum(1 for r in make_costly(count) if r["bytes"] > total / count)
        return total, above

    a, _, peak_list, t_list = measure("리스트로 담고 두 번 훑기", with_list)
    b, _, peak_gen, t_regen = measure("제너레이터를 두 번 만들기", with_regenerate)
    print(f"  두 방식의 결과가 같은가: {a == b}  {a}")
    print(f"  리스트 대비 소요 시간 — 재생성 {t_regen / t_list:,.2f}배")
    print(f"  리스트 대비 최대 메모리 — 재생성 {peak_gen / peak_list:,.5f}배")
    print()


def what_is_counted() -> None:
    section("3. 제너레이터 객체 자체는 얼마나 되는가")
    gen = make_records(RECORD_COUNT)
    sample = next(gen)
    print(f"  제너레이터 객체     sys.getsizeof = {sys.getsizeof(gen):,} 바이트")
    print(f"  dict 한 개          sys.getsizeof = {sys.getsizeof(sample):,} 바이트")
    empty = []
    print(f"  빈 리스트           sys.getsizeof = {sys.getsizeof(empty):,} 바이트")
    full = [None] * RECORD_COUNT
    print(f"  {RECORD_COUNT:,}칸 리스트  sys.getsizeof = {sys.getsizeof(full):,} 바이트"
          "  (칸만 센 값. 안에 든 dict 는 따로다)")
    gen.close()
    print()


def leading_pattern() -> None:
    section("4. 앞부분만 필요할 때")

    def with_list() -> list:
        records = [r for r in make_records(RECORD_COUNT)]
        errors = [r for r in records if r["level"] == "ERROR"]
        return errors[:5]

    def with_generator() -> list:
        errors = (r for r in make_records(RECORD_COUNT) if r["level"] == "ERROR")
        return list(itertools.islice(errors, 5))

    head_list, _, _, _ = measure("리스트로 전부 담고 앞 5개", with_list)
    head_gen, _, _, _ = measure("제너레이터에서 앞 5개만", with_generator)
    print(f"  두 결과가 같은가: {head_list == head_gen}")
    print(f"  첫 행: {head_gen[0]}")
    print()


def main() -> None:
    print(RULE)
    print("환경")
    print(RULE)
    print(f"  Python  {platform.python_version()}  ({platform.python_implementation()})")
    print(f"  OS      {platform.system()} {platform.release()}")
    print(f"  레코드  {RECORD_COUNT:,}개 · 각 dict 는 키 3개")
    print()

    one_pass()
    two_passes()
    costly_source()
    what_is_counted()
    leading_pattern()


if __name__ == "__main__":
    main()
