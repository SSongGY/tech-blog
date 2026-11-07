"""스킵 리스트 — Pugh 1990 의 알고리즘을 그대로 옮겨 레벨 분포와 탐색 경로를 잰다.

1) 레벨 분포가 p^(k-1)(1-p) 를 따르는가, 노드당 포인터 수가 1/(1-p) 인가
2) 탐색 경로 길이가 논문의 상한 L(n)/p + 1/(1-p) 안에 드는가 (p 다섯 값)
3) n 을 키울 때 경로가 log n 으로 늘어나는가
4) 키를 정렬된 순서로 넣어도 같은 모양이 나오는가
5) 검산: 비교 횟수 = 경로 길이 + 1
"""
import math
import random
import statistics

SEED = 20261107


class Node:
    __slots__ = ("key", "forward")

    def __init__(self, key, level):
        self.key = key
        self.forward = [None] * level   # forward[0] 이 논문의 forward[1]


class SkipList:
    def __init__(self, p, max_level, rng):
        self.p = p
        self.max_level = max_level
        self.rng = rng
        self.level = 1
        # 논문은 NIL 을 "어떤 키보다 큰 원소"로 두므로 무한대를 키로 쓴다
        self.nil = Node(math.inf, 0)
        self.header = Node(-math.inf, max_level)
        self.header.forward = [self.nil] * max_level

    def random_level(self):
        level = 1
        while self.rng.random() < self.p and level < self.max_level:
            level += 1
        return level

    def insert(self, key):
        update = [None] * self.max_level
        x = self.header
        for i in range(self.level - 1, -1, -1):
            while x.forward[i].key < key:
                x = x.forward[i]
            update[i] = x
        x = x.forward[0]
        if x.key == key:
            return
        level = self.random_level()
        if level > self.level:
            for i in range(self.level, level):
                update[i] = self.header
            self.level = level
        node = Node(key, level)
        for i in range(level):
            node.forward[i] = update[i].forward[i]
            update[i].forward[i] = node

    def search(self, key):
        """(찾았는가, 수평 이동 수, 키 비교 횟수) 를 돌려준다."""
        x = self.header
        moves = 0
        comparisons = 0
        for i in range(self.level - 1, -1, -1):
            while True:
                comparisons += 1
                if x.forward[i].key < key:
                    x = x.forward[i]
                    moves += 1
                else:
                    break
        x = x.forward[0]
        return x.key == key, moves, comparisons

    def node_levels(self):
        levels = []
        x = self.header.forward[0]
        while x is not self.nil:
            levels.append(len(x.forward))
            x = x.forward[0]
        return levels


def build(n, p, seed, ordered=False, max_level=None):
    rng = random.Random(seed)
    if max_level is None:
        max_level = max(1, math.ceil(math.log(n, 1 / p)))   # 논문: MaxLevel = L(N)
    skip_list = SkipList(p, max_level, rng)
    keys = list(range(n))
    if not ordered:
        random.Random(seed + 1).shuffle(keys)
    for key in keys:
        skip_list.insert(key)
    return skip_list


def measure(skip_list, n):
    """모든 키를 한 번씩 찾아 경로 길이(수평 이동 + 내려간 단 수)를 모은다."""
    lengths = []
    check_ok = True
    for key in range(n):
        found, moves, comparisons = skip_list.search(key)
        length = moves + (skip_list.level - 1)
        if not found or comparisons != length + 1:
            check_ok = False
        lengths.append(length)
    return lengths, check_ok


def bound(n, p):
    return math.log(n, 1 / p) / p + 1 / (1 - p)


def section_levels():
    print("== 1) 레벨 분포 — p = 1/2, n = 65,536 ==")
    n, p = 65536, 0.5
    levels = build(n, p, SEED).node_levels()
    print("  레벨 | 노드 수 | 실측 비율 | 기대 비율 p^(k-1)(1-p)")
    for k in range(1, 9):
        count = levels.count(k)
        expected = p ** (k - 1) * (1 - p)
        print(f"  {k:>4} | {count:>7,} | {count / n:>9.4f} | {expected:>9.4f}")
    print(f"  9 이상 | {sum(1 for v in levels if v >= 9):>5,}")
    print()


def section_p_values():
    print("== 2) p 에 따른 공간과 탐색 경로 — n = 65,536, 키 무작위 순서 ==")
    n = 65536
    print("  p      | 포인터/노드 | 1/(1-p) | 최고 레벨 | 평균 경로 | 최장 경로 | 상한 L(n)/p+1/(1-p) | 검산")
    rows = []
    for label, p in [("1/2", 1 / 2), ("1/e", 1 / math.e), ("1/4", 1 / 4),
                     ("1/8", 1 / 8), ("1/16", 1 / 16)]:
        skip_list = build(n, p, SEED)
        levels = skip_list.node_levels()
        lengths, check_ok = measure(skip_list, n)
        rows.append((label, p, statistics.mean(lengths), max(lengths)))
        print(f"  {label:<6} | {sum(levels) / n:>11.3f} | {1 / (1 - p):>7.3f} |"
              f" {skip_list.level:>9} | {statistics.mean(lengths):>9.2f} |"
              f" {max(lengths):>9} | {bound(n, p):>19.2f} | {check_ok}")
    print()
    # 논문 Table 1 은 L(n)/p 를 p = 1/2 기준으로 나눈 값이다. 실측 평균도 같은 기준으로 나눠 본다
    print("  p      | 논문 Table 1 L(n)/p 비 | 실측 평균 경로 비 | 최장/평균")
    base_formula = (1 / 0.5) / math.log(2)
    base_mean = rows[0][2]
    for label, p, mean_length, max_length in rows:
        formula = (1 / p) / math.log(1 / p)
        print(f"  {label:<6} | {formula / base_formula:>22.2f} |"
              f" {mean_length / base_mean:>17.2f} | {max_length / mean_length:>9.2f}")
    print()


def section_growth():
    print("== 3) n 을 16배씩 키우면 — p = 1/4 ==")
    p = 1 / 4
    print("  n       | log4 n | 평균 경로 | 상한")
    for exponent in (8, 12, 16):
        n = 2 ** exponent
        lengths, _ = measure(build(n, p, SEED), n)
        print(f"  {n:>7,} | {math.log(n, 4):>6.0f} | {statistics.mean(lengths):>9.2f} |"
              f" {bound(n, p):>5.2f}")
    print()


def section_order():
    print("== 4) 넣는 순서를 바꾸면 — n = 65,536, p = 1/2 ==")
    n, p = 65536, 0.5
    print("  넣은 순서 | 최고 레벨 | 평균 경로 | 최장 경로")
    for label, ordered in [("무작위", False), ("오름차순", True)]:
        skip_list = build(n, p, SEED, ordered=ordered)
        lengths, _ = measure(skip_list, n)
        print(f"  {label:<8} | {skip_list.level:>9} | {statistics.mean(lengths):>9.2f} |"
              f" {max(lengths):>9}")
    print()


def section_cap():
    print("== 5) MaxLevel 을 L(n) 대신 32 로 두면 — n = 65,536 ==")
    n = 65536
    print("  p    | MaxLevel | 최고 레벨 | 평균 경로 | 최장 경로")
    for label, p in [("1/2", 1 / 2), ("1/4", 1 / 4)]:
        for max_level in (None, 32):
            skip_list = build(n, p, SEED, max_level=max_level)
            lengths, _ = measure(skip_list, n)
            shown = "L(n)" if max_level is None else str(max_level)
            print(f"  {label:<4} | {shown:>8} | {skip_list.level:>9} |"
                  f" {statistics.mean(lengths):>9.2f} | {max(lengths):>9}")
    print()


def main():
    print(f"난수 시드 {SEED}, MaxLevel = ceil(log_(1/p) n)")
    print()
    section_levels()
    section_p_values()
    section_growth()
    section_order()
    section_cap()


if __name__ == "__main__":
    main()
