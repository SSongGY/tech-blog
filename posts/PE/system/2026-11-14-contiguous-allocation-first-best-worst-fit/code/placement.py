"""연속 메모리 할당의 배치 기법 4가지 — 최초·다음·최적·최악 적합을 직접 계산해 검산한다.

1) OSTEP 17.3 예제(빈 블록 10·30·20, 요청 15)를 재현해 구현을 검산
2) 빈 블록 5개에 요청 4개를 넣는 계산 문제 — 기법마다 어디에 들어가고 무엇이 남는가
3) 들어가지 못한 요청 — 남은 빈 공간 합계와 가장 큰 빈 블록(외부 단편화)
4) 압축 후 다시 넣기
5) 무작위 할당·해제를 오래 돌려 빈 블록 수 / 할당 블록 수 비율을 잰다(50% 규칙 확인)
"""
import random

POLICIES = ("first", "next", "best", "worst")


class Allocator:
    """빈 블록 목록을 주소 순서로 들고 있는 가변 분할 할당기."""

    def __init__(self, holes, policy):
        # holes: [(시작 주소, 크기), ...] 주소 오름차순
        self.holes = [list(h) for h in holes]
        self.policy = policy
        self.next_index = 0          # 다음 적합이 이어서 찾을 위치
        self.examined = 0            # 살펴본 빈 블록 수 (탐색 비용)

    def _choose(self, size):
        count = len(self.holes)
        if self.policy == "next":
            order = [(self.next_index + k) % count for k in range(count)] if count else []
        else:
            order = range(count)
        chosen = None
        for i in order:
            self.examined += 1
            hole_size = self.holes[i][1]
            if hole_size < size:
                continue
            if self.policy in ("first", "next"):
                return i  # 처음 맞는 것에서 멈춘다 — 나머지는 보지 않는다
            if chosen is None:
                chosen = i
            elif self.policy == "best" and hole_size < self.holes[chosen][1]:
                chosen = i
            elif self.policy == "worst" and hole_size > self.holes[chosen][1]:
                chosen = i
        return chosen

    def allocate(self, size):
        i = self._choose(size)
        if i is None:
            return None
        start, hole_size = self.holes[i]
        if hole_size == size:
            del self.holes[i]
            self.next_index = i if i < len(self.holes) else 0
        else:
            self.holes[i] = [start + size, hole_size - size]
            self.next_index = i
        return start

    def free(self, start, size):
        # 주소 순서로 끼워 넣고 이웃한 빈 블록과 합친다(병합)
        self.holes.append([start, size])
        self.holes.sort()
        merged = []
        for hole in self.holes:
            if merged and merged[-1][0] + merged[-1][1] == hole[0]:
                merged[-1][1] += hole[1]
            else:
                merged.append(hole)
        self.holes = merged
        self.next_index = min(self.next_index, max(len(self.holes) - 1, 0))

    def sizes(self):
        return [h[1] for h in self.holes]


def layout(sizes, gap=0):
    """크기 목록을 주소 순서로 이어 붙인 빈 블록 목록으로 만든다."""
    holes, address = [], 0
    for s in sizes:
        holes.append((address, s))
        address += s + gap
    return holes


def part1():
    print("[1] OSTEP 17.3 예제 — 빈 블록 10, 30, 20 에 요청 15")
    for policy in POLICIES:
        alloc = Allocator(layout([10, 30, 20], gap=1), policy)
        alloc.allocate(15)
        print(f"  {policy:<6} -> 남은 빈 블록 {alloc.sizes()}")
    print()


def part2_3_4():
    holes_kb = [100, 500, 200, 300, 600]
    requests_kb = [212, 417, 112, 426]
    print(f"[2] 빈 블록 {holes_kb} KB 에 요청 {requests_kb} KB 를 차례로")
    # 빈 블록 사이에는 사용 중인 영역이 있다고 보고 1KB 간격을 둔다 — 병합되지 않게
    for policy in POLICIES:
        alloc = Allocator(layout(holes_kb, gap=1), policy)
        placements = []
        for req in requests_kb:
            before = {h[0]: h[1] for h in alloc.holes}
            start = alloc.allocate(req)
            if start is None:
                placements.append(f"{req}->대기")
            else:
                placements.append(f"{req}->{before[start]}")
        free_total = sum(alloc.sizes())
        largest = max(alloc.sizes())
        print(f"  {policy:<6} 배치 {', '.join(placements)}")
        print(f"         남은 빈 블록 {alloc.sizes()} · 합계 {free_total} · 최대 {largest}"
              f" · 살펴본 빈 블록 {alloc.examined}개")
        if any("대기" in p for p in placements):
            print(f"         [3] 426 KB 를 못 넣었다 — 빈 공간 합계 {free_total} KB >= 426 이지만 "
                  f"가장 큰 빈 블록이 {largest} KB (외부 단편화)")
            print(f"         [4] 압축하면 빈 블록 [{free_total}] 하나 -> 426 KB 배치 가능: "
                  f"{free_total >= 426}")
    print()


def part5(seed=20261114, memory=100_000, steps=200_000, warmup=20_000, free_probability=0.3):
    print("[5] 무작위 할당·해제 — 빈 블록 수 / 할당 블록 수 (50% 규칙)")
    print(f"  메모리 {memory}, 요청 크기 1~1000 균등, 단계 {steps} (앞 {warmup} 단계 버림), 시드 {seed}")
    # 해제보다 할당이 잦게 두어 메모리가 늘 꽉 찬 상태(실패 -> 해제)에서 잰다
    print(f"  한 단계에서 해제할 확률 {free_probability}, 나머지는 할당")
    print("  기법   | 빈/할당 비율 | 빈 공간 비율 | 할당 1회당 살펴본 빈 블록 | 첫 시도 실패")
    for policy in POLICIES:
        rng = random.Random(seed)
        alloc = Allocator([(0, memory)], policy)
        live = []  # [(시작, 크기)]
        ratio_sum = free_sum = 0.0
        samples = allocations = failures = 0
        alloc.examined = 0
        for step in range(steps):
            if live and rng.random() < free_probability:
                start, size = live.pop(rng.randrange(len(live)))
                alloc.free(start, size)
            else:
                size = rng.randint(1, 1000)
                start = alloc.allocate(size)
                # 들어갈 자리가 없으면 무작위 블록을 풀어 가며 다시 시도한다
                if start is None and step >= warmup:
                    failures += 1
                while start is None:
                    victim = live.pop(rng.randrange(len(live)))
                    alloc.free(*victim)
                    start = alloc.allocate(size)
                live.append((start, size))
                allocations += 1
            if step >= warmup and live:
                ratio_sum += len(alloc.holes) / len(live)
                free_sum += sum(alloc.sizes()) / memory
                samples += 1
        print(f"  {policy:<6} | {ratio_sum / samples:12.3f} | {free_sum / samples:12.3f} | "
              f"{alloc.examined / allocations:24.1f} | {failures:6d}")
    print()


if __name__ == "__main__":
    part1()
    part2_3_4()
    part5()
