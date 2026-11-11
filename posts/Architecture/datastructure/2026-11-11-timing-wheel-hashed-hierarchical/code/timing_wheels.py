"""힙·단순 휠·해시 휠·계층 휠로 같은 타이머 부하를 돌려 일의 양을 센다.

Varghese·Lauck(1987)의 분류를 따른다.
  Scheme 3  힙(트리 기반 우선순위 큐)
  Scheme 4  단순 타이밍 휠 — 슬롯 수 = MaxInterval
  Scheme 6  해시 휠 — 정렬하지 않은 목록, 남은 바퀴 수를 같이 저장
  Scheme 7  계층 휠 — 자릿수마다 휠 하나, 만료가 가까워지면 아래 휠로 옮긴다

"일" 은 타이머 항목을 한 번 건드린 횟수다. 힙은 비교 횟수, 휠은 슬롯에서 꺼내 본 항목 수
(만료·바퀴 수 감소·아래 휠로 이동)를 센다. 시간이 아니라 횟수를 세는 이유는 매번 같은 값이
나와야 글의 숫자와 output.txt 가 맞기 때문이다.
"""
import heapq
import random

TIMER_COUNT = 10_000
START_WINDOW = 2_000        # 처음 2,000 틱 동안 타이머를 고르게 건다
MAX_INTERVAL = 3_000        # 타이머 길이 상한(틱)
STOP_RATIO = 0.3            # 30% 는 만료 전에 멈춘다 — 응답이 와서 재전송 타이머를 끄는 경우
SEED = 20261111


class CountedEntry:
    """heapq 가 비교할 때마다 세려고 감싼다."""
    comparisons = 0
    __slots__ = ("expiry", "timer_id")

    def __init__(self, expiry, timer_id):
        self.expiry = expiry
        self.timer_id = timer_id

    def __lt__(self, other):
        CountedEntry.comparisons += 1
        return (self.expiry, self.timer_id) < (other.expiry, other.timer_id)


class HeapTimers:
    """Scheme 3. 멈춘 타이머는 표시만 해 두고 꺼낼 때 버린다(지연 삭제)."""
    name = "Scheme 3 힙"

    def __init__(self):
        self.heap = []
        self.stopped = set()
        self.now = 0
        self.tick_work = 0

    def start(self, timer_id, interval):
        before = CountedEntry.comparisons
        heapq.heappush(self.heap, CountedEntry(self.now + interval, timer_id))
        return CountedEntry.comparisons - before

    def stop(self, timer_id):
        self.stopped.add(timer_id)
        return 1

    def tick(self):
        self.now += 1
        expired = []
        before = CountedEntry.comparisons
        touched = 0
        while self.heap and self.heap[0].expiry <= self.now:
            entry = heapq.heappop(self.heap)
            touched += 1
            if entry.timer_id in self.stopped:
                self.stopped.discard(entry.timer_id)
                continue
            expired.append(entry.timer_id)
        self.tick_work = touched + (CountedEntry.comparisons - before)
        return expired

    def slots(self):
        return 0


class SimpleWheel:
    """Scheme 4. 슬롯이 MaxInterval 개라 한 바퀴 안의 타이머만 담을 수 있다."""
    name = "Scheme 4 단순 휠"

    def __init__(self, size):
        self.size = size
        self.buckets = [dict() for _ in range(size)]
        self.where = {}
        self.now = 0
        self.tick_work = 0

    def start(self, timer_id, interval):
        assert interval < self.size, "단순 휠은 MaxInterval 보다 긴 타이머를 담지 못한다"
        slot = (self.now + interval) % self.size
        self.buckets[slot][timer_id] = True
        self.where[timer_id] = slot
        return 1

    def stop(self, timer_id):
        # 슬롯 위치를 기억해 두었으므로 목록을 뒤지지 않고 바로 지운다
        del self.buckets[self.where.pop(timer_id)][timer_id]
        return 1

    def tick(self):
        self.now += 1
        bucket = self.buckets[self.now % self.size]
        expired = list(bucket)
        for timer_id in expired:
            del self.where[timer_id]
        bucket.clear()
        self.tick_work = len(expired)
        return expired

    def slots(self):
        return self.size


class HashedWheel:
    """Scheme 6. 슬롯 = (now + interval) mod size, 남은 바퀴 수 = (interval - 1) // size."""
    name = "Scheme 6 해시 휠"

    def __init__(self, size):
        self.size = size
        self.buckets = [dict() for _ in range(size)]
        self.where = {}
        self.now = 0
        self.tick_work = 0

    def start(self, timer_id, interval):
        slot = (self.now + interval) % self.size
        self.buckets[slot][timer_id] = (interval - 1) // self.size
        self.where[timer_id] = slot
        return 1

    def stop(self, timer_id):
        del self.buckets[self.where.pop(timer_id)][timer_id]
        return 1

    def tick(self):
        self.now += 1
        bucket = self.buckets[self.now % self.size]
        expired = []
        for timer_id, rounds in list(bucket.items()):
            if rounds == 0:
                expired.append(timer_id)
                del bucket[timer_id]
                del self.where[timer_id]
            else:
                bucket[timer_id] = rounds - 1
        self.tick_work = len(bucket) + len(expired)
        return expired


    def slots(self):
        return self.size


class HierarchicalWheel:
    """Scheme 7. 휠 3개 x 슬롯 16개. 만료 시각을 16진 세 자리로 보고 자릿수마다 휠 하나를 쓴다."""
    name = "Scheme 7 계층 휠"
    BITS = 4
    SIZE = 1 << BITS
    LEVELS = 3

    def __init__(self, trace_id=None):
        self.wheels = [[dict() for _ in range(self.SIZE)] for _ in range(self.LEVELS)]
        self.where = {}
        self.now = 0
        self.tick_work = 0
        self.trace_id = trace_id
        self.trace = []

    def place(self, timer_id, expiry):
        """지금 시각과 만료 시각이 처음 갈리는 자릿수의 휠에 넣는다."""
        for level in range(self.LEVELS - 1, 0, -1):
            shift = self.BITS * level
            if (expiry >> shift) != (self.now >> shift):
                break
        else:
            level = 0
        slot = (expiry >> (self.BITS * level)) & (self.SIZE - 1)
        self.wheels[level][slot][timer_id] = expiry
        self.where[timer_id] = (level, slot)
        if timer_id == self.trace_id:
            self.trace.append((self.now, level, slot))
        return level

    def start(self, timer_id, interval):
        assert interval < self.SIZE ** self.LEVELS - self.SIZE ** (self.LEVELS - 1)
        # 몇 번째 휠까지 내려가 보며 자리를 찾았는지가 START 의 비용이다 (논문의 O(m))
        level = self.place(timer_id, self.now + interval)
        return self.LEVELS - level

    def stop(self, timer_id):
        level, slot = self.where.pop(timer_id)
        del self.wheels[level][slot][timer_id]
        return 1

    def tick(self):
        self.now += 1
        moved = 0
        # 윗자리 휠부터 자리가 넘어간 슬롯을 비워 아래로 옮긴다
        for level in range(self.LEVELS - 1, 0, -1):
            if self.now & ((1 << (self.BITS * level)) - 1) == 0:
                slot = (self.now >> (self.BITS * level)) & (self.SIZE - 1)
                bucket = self.wheels[level][slot]
                for timer_id, expiry in list(bucket.items()):
                    del bucket[timer_id]
                    self.place(timer_id, expiry)
                    moved += 1
        bucket = self.wheels[0][self.now & (self.SIZE - 1)]
        expired = list(bucket)
        for timer_id in expired:
            del self.where[timer_id]
            if timer_id == self.trace_id:
                self.trace.append((self.now, "만료", None))
        bucket.clear()
        self.tick_work = moved + len(expired)
        return expired

    def slots(self):
        return self.SIZE * self.LEVELS


def make_workload():
    rng = random.Random(SEED)
    starts = {}
    stops = {}
    for timer_id in range(TIMER_COUNT):
        start_tick = rng.randrange(START_WINDOW)
        interval = rng.randint(1, MAX_INTERVAL)
        starts.setdefault(start_tick, []).append((timer_id, interval))
        if rng.random() < STOP_RATIO:
            stop_tick = start_tick + rng.randrange(interval)
            if stop_tick > start_tick:
                stops.setdefault(stop_tick, []).append(timer_id)
    return starts, stops


def run(timers, starts, stops):
    end_tick = START_WINDOW + MAX_INTERVAL + 1
    start_costs = []
    stop_costs = []
    tick_works = []
    log = []
    live_counts = []
    for tick in range(end_tick):
        if tick > 0:
            for timer_id in timers.tick():
                log.append((timers.now, timer_id))
            tick_works.append(timers.tick_work)
            if hasattr(timers, "where"):
                live_counts.append(len(timers.where))
        for timer_id in stops.get(tick, []):
            stop_costs.append(timers.stop(timer_id))
        for timer_id, interval in starts.get(tick, []):
            start_costs.append(timers.start(timer_id, interval))
    timers.live_counts = live_counts
    return start_costs, stop_costs, tick_works, log


def main():
    starts, stops = make_workload()
    print(f"타이머 {TIMER_COUNT:,}개 · 시작 구간 {START_WINDOW:,}틱 · 길이 1~{MAX_INTERVAL:,}틱 · "
          f"중간에 멈춤 {sum(len(v) for v in stops.values()):,}개 · seed {SEED}")
    print()

    schemes = [HeapTimers(), SimpleWheel(4096), HashedWheel(256), HierarchicalWheel(trace_id=0)]
    logs = []
    print(f"{'방식':<16} {'슬롯':>5} | {'START 평균':>10} {'최대':>4} | {'STOP':>4} | "
          f"{'틱당 일 평균':>11} {'최대':>5} | {'일 합계':>8}")
    for timers in schemes:
        start_costs, stop_costs, tick_works, log = run(timers, starts, stops)
        logs.append(sorted(log))
        print(f"{timers.name:<16} {timers.slots():>5} | "
              f"{sum(start_costs) / len(start_costs):>10.2f} {max(start_costs):>4} | "
              f"{max(stop_costs):>4} | "
              f"{sum(tick_works) / len(tick_works):>11.2f} {max(tick_works):>5} | "
              f"{sum(tick_works):>8,}")
    print()
    print("네 방식의 만료 기록(틱, 타이머)이 모두 같은가:", all(x == logs[0] for x in logs))
    print("만료된 타이머 수:", len(logs[0]))
    print()

    hierarchical = schemes[3]
    _, _, works, _ = run(HierarchicalWheel(), starts, stops)
    busiest = sorted(range(len(works)), key=lambda i: -works[i])[:4]
    print("계층 휠에서 일이 가장 많았던 틱 4개 (틱, 일, 16진 시각)")
    for i in sorted(busiest):
        print(f"  {i + 1:>5}틱  {works[i]:>4}  0x{i + 1:03x}")
    print()

    first =next((t, iv) for t, items in sorted(starts.items()) for tid, iv in items if tid == 0)
    print(f"계층 휠에서 타이머 0 의 이동 — 시작 {first[0]}틱, 길이 {first[1]}틱, "
          f"만료 예정 {first[0] + first[1]}틱")
    for now, level, slot in hierarchical.trace:
        if level == "만료":
            print(f"  {now:>5}틱  만료")
        else:
            print(f"  {now:>5}틱  휠 {level} 의 슬롯 {slot:>2} 에 들어감")
    print()

    print("해시 휠 슬롯 수를 바꾸면 — 논문 식 n/TableSize 와 비교")
    for size in (64, 256, 1024):
        wheel = HashedWheel(size)
        start_costs, stop_costs, tick_works, log = run(wheel, starts, stops)
        live_avg = sum(wheel.live_counts) / len(wheel.live_counts)
        print(f"  슬롯 {size:>5} | 틱당 일 평균 {sum(tick_works) / len(tick_works):>6.2f} "
              f"최대 {max(tick_works):>4} | 평균 대기 타이머 n {live_avg:>7.1f} "
              f"→ n/TableSize {live_avg / size:>6.2f}")


if __name__ == "__main__":
    main()
