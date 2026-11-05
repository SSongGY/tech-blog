"""상위 k개를 뽑을 때 sorted 와 heapq.nsmallest 의 시간이 k 에 따라 어떻게 갈리는지 잰다."""

import heapq
import random
import sys
import timeit

SEED = 20261105
REPEAT = 5


def best_ms(func) -> float:
    """5번 재서 가장 빠른 값을 쓴다. 느린 쪽으로 튀는 값은 다른 프로세스의 영향이다."""
    return min(timeit.repeat(func, number=1, repeat=REPEAT)) * 1000


def compare(size: int, ks: list[int], *, with_key: bool) -> None:
    rng = random.Random(SEED)
    data = [rng.randrange(10**9) for _ in range(size)]
    key = (lambda x: -x) if with_key else None
    kwargs = {"key": key} if with_key else {}

    print(f"\n정렬 대상 {size:,}개, key={'있음' if with_key else '없음'}")
    print(f"  {'k':>8} | {'k/n':>7} | {'sorted':>9} | {'nsmallest':>9} | 빠른 쪽")
    print(f"  {'-' * 8}-+-{'-' * 7}-+-{'-' * 9}-+-{'-' * 9}-+--------")
    for k in ks:
        t_sorted = best_ms(lambda: sorted(data, **kwargs)[:k])
        t_heap = best_ms(lambda: heapq.nsmallest(k, data, **kwargs))
        assert sorted(data, **kwargs)[:k] == heapq.nsmallest(k, data, **kwargs)
        winner = "nsmallest" if t_heap < t_sorted else "sorted"
        print(f"  {k:>8,} | {k / size:>6.2%} | {t_sorted:>7.1f}ms | {t_heap:>7.1f}ms | {winner}")


def main() -> None:
    print(f"Python {sys.version.split()[0]}")
    ks = [1, 10, 100, 1_000, 10_000, 15_000, 20_000, 25_000, 30_000, 100_000, 199_999, 200_000]
    compare(200_000, ks, with_key=False)
    compare(200_000, ks, with_key=True)

    # n 이 같아도 k 가 전체와 같거나 크면 nsmallest 가 sorted 로 넘어가는 분기가 있다
    rng = random.Random(SEED)
    data = [rng.randrange(10**9) for _ in range(200_000)]
    t_all = best_ms(lambda: heapq.nsmallest(200_000, data))
    t_sorted = best_ms(lambda: sorted(data))
    print(f"\nk = n 일 때: nsmallest {t_all:.1f}ms / sorted {t_sorted:.1f}ms")

    # 제너레이터는 len 이 없어서 위 분기를 못 탄다
    t_gen = best_ms(lambda: heapq.nsmallest(200_000, iter(data)))
    print(f"k = n 인데 이터레이터를 넘기면: nsmallest {t_gen:.1f}ms")


if __name__ == "__main__":
    main()
