"""딕셔너리가 커지는 지점과, 해시가 겹쳤을 때 조회 비용이 변하는 모습을 잰다.

세 가지를 찍는다.
  1. 항목을 하나씩 넣으며 sys.getsizeof 가 계단처럼 뛰는 지점
  2. 같은 항목 수라도 만드는 방법에 따라 크기가 달라지는 것
  3. 해시가 전부 같은 키를 넣었을 때 조회 시간이 어떻게 변하는지
"""

import platform
import sys
import timeit

RULE = "=" * 64
STEP_LIMIT = 200          # 1번에서 이 개수까지 넣어 본다
TRIAL_SIZES = (10, 50, 100, 200, 400)   # 3번에서 재는 키 개수


class ConstantHash:
    """해시가 전부 같은 키. 사전은 해시가 같아도 같은 키로 보지 않는다."""

    __slots__ = ("value",)

    def __init__(self, value: int) -> None:
        self.value = value

    def __hash__(self) -> int:
        return 0

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ConstantHash) and self.value == other.value


class UniqueHash(ConstantHash):
    """같은 클래스에 해시만 서로 다르게. 비교 비용을 맞추려고 상속한다."""

    def __hash__(self) -> int:
        return self.value


def print_environment() -> None:
    print(RULE)
    print("환경")
    print(RULE)
    print(f"  Python     {platform.python_version()} ({platform.python_implementation()})")
    print(f"  OS         {platform.system()} {platform.release()}")
    print(f"  포인터     {sys.maxsize.bit_length() + 1}비트")
    print()


def growth_steps() -> None:
    """빈 사전에 항목을 하나씩 넣으며 크기가 바뀌는 순간만 찍는다."""
    print(RULE)
    print(f"1. 항목을 1개씩 {STEP_LIMIT}개까지 넣으며 sys.getsizeof 가 바뀐 지점")
    print(RULE)
    print("  항목 수 | 바이트 | 직전 대비")

    table = {}
    previous = sys.getsizeof(table)
    print(f"  {0:7d} | {previous:6d} | (빈 사전)")
    for i in range(STEP_LIMIT):
        table[i] = i
        current = sys.getsizeof(table)
        if current != previous:
            print(f"  {len(table):7d} | {current:6d} | +{current - previous}")
            previous = current
    print()


def construction_shapes() -> None:
    """만드는 방법이 크기를 가르는지 확인한다."""
    print(RULE)
    print("2. 같은 항목을 어떻게 만들든 크기는 같은가")
    print(RULE)
    print("  항목 수 | 하나씩 삽입 | dict(제너레이터) | fromkeys | 리터럴/복사")

    for count in (5, 8, 10, 100, 1000):
        incremental = {}
        for i in range(count):
            incremental[i] = i
        at_once = dict((i, i) for i in range(count))
        prefilled = dict.fromkeys(range(count), 0)
        copied = dict(incremental)
        print(
            f"  {count:7d} | {sys.getsizeof(incremental):11d} |"
            f" {sys.getsizeof(at_once):16d} | {sys.getsizeof(prefilled):8d} |"
            f" {sys.getsizeof(copied):11d}"
        )
    print()


def deleted_entries() -> None:
    """크기를 정하는 것이 현재 항목 수가 아님을 보인다."""
    print(RULE)
    print("3. 크기를 정하는 것은 지금 든 개수가 아니라 거쳐 간 최대 개수다")
    print(RULE)

    table = {i: i for i in range(1000)}
    print(f"  1000개 보유        : {sys.getsizeof(table):6d}바이트")
    for i in range(999):
        del table[i]
    print(f"  999개 삭제 후 1개  : {sys.getsizeof(table):6d}바이트")
    print(f"  항목 수            : {len(table)}개")
    rebuilt = dict(table)
    print(f"  dict() 로 다시 만듦: {sys.getsizeof(rebuilt):6d}바이트")
    print()


def integer_key_spacing() -> None:
    """정수 키의 간격이 2의 거듭제곱일 때 느려지는지 잰다.

    정수의 해시는 자기 자신이고 슬롯 번호는 해시의 하위 비트다. 간격이
    2의 거듭제곱이면 하위 비트가 전부 같아 첫 슬롯이 겹친다.
    """
    print(RULE)
    print("6. 정수 키의 간격 — 연속 vs 2의 거듭제곱 간격 (4096개 전체 조회)")
    print(RULE)
    print("  간격   | 조회 1회(µs) | 사전 크기(바이트)")

    count = 4096
    for stride in (1, 3, 1024, 4096, 65536):
        keys = [i * stride for i in range(count)]
        table = dict.fromkeys(keys, 0)
        repeat = 20
        total = timeit.timeit(
            lambda: [table[k] for k in keys], number=repeat
        ) / (repeat * count)
        print(f"  {stride:6d} | {total * 1e6:12.4f} | {sys.getsizeof(table):17d}")
    print()


def lookup_cost() -> None:
    """해시가 전부 같을 때와 다를 때의 조회 시간을 나란히 잰다."""
    print(RULE)
    print("4. 해시가 전부 같은 키 vs 서로 다른 키 — 마지막 키 1회 조회")
    print(RULE)
    print("  키 개수 | 해시 동일(µs) | 해시 상이(µs) | 배수")

    for count in TRIAL_SIZES:
        same = {ConstantHash(i): i for i in range(count)}
        diff = {UniqueHash(i): i for i in range(count)}
        probe_same = ConstantHash(count - 1)
        probe_diff = UniqueHash(count - 1)

        # 반복 횟수를 키 개수에 반비례시키면 전체 수행 시간이 비슷해진다
        repeat = max(2000, 200000 // count)
        same_sec = timeit.timeit(lambda: same[probe_same], number=repeat) / repeat
        diff_sec = timeit.timeit(lambda: diff[probe_diff], number=repeat) / repeat
        print(
            f"  {count:7d} | {same_sec * 1e6:13.3f} | {diff_sec * 1e6:13.3f} |"
            f" {same_sec / diff_sec:5.1f}배"
        )
    print()


def hash_identity() -> None:
    """정수 키의 해시가 무엇인지 확인한다."""
    print(RULE)
    print("5. 정수 키의 해시는 자기 자신이다")
    print(RULE)
    for value in (0, 1, 7, 8, 1000, -1, -2):
        print(f"  hash({value:5d}) = {hash(value)}")
    print(f"  hash(2**61 - 1) = {hash(2 ** 61 - 1)}")
    print(f"  hash(2**61)     = {hash(2 ** 61)}")
    print()


def predicted_size(table_size: int) -> int:
    """문서에 적힌 구조대로 바이트 수를 계산한다.

    dictobject.c 가 밝힌 것:
      - 슬롯 하나는 테이블 크기가 128 이하면 1바이트, 2**15 이하면 2바이트
      - 쓸 수 있는 칸 수 USABLE_FRACTION(n) = (n * 2) / 3
      - 항목 한 칸은 hash·key·value 세 포인터 = 24바이트 (64비트)
    앞의 두 상수 48 은 이 빌드에서 잰 값이다 — 사전 객체와 키 테이블 머리.
    """
    index_bytes = 1 if table_size <= 128 else 2 if table_size <= 2 ** 15 else 4
    usable = (table_size * 2) // 3
    return 48 + 48 + table_size * index_bytes + usable * 24


def size_reconciliation() -> None:
    """리사이즈가 일어나는 지점과 그때의 크기를 계산값과 맞춰 본다."""
    print(RULE)
    print("7. 리사이즈 지점과 크기를 문서의 규칙으로 계산해 실측과 대조")
    print(RULE)
    print("  테이블 | 쓸 수 있는 칸 | 리사이즈 시작 | 계산 바이트 | 실측 바이트 | 일치")

    table_size = 8
    while table_size <= 2048:
        usable = (table_size * 2) // 3
        measured = {}
        for i in range(usable):
            measured[i] = i
        actual = sys.getsizeof(measured)
        expected = predicted_size(table_size)
        print(
            f"  {table_size:6d} | {usable:13d} | {usable + 1:13d}번째 |"
            f" {expected:11d} | {actual:11d} | {'예' if expected == actual else '아니오'}"
        )
        table_size *= 2
    print()


def main() -> None:
    print_environment()
    growth_steps()
    construction_shapes()
    deleted_entries()
    lookup_cost()
    hash_identity()
    integer_key_spacing()
    size_reconciliation()


if __name__ == "__main__":
    main()
