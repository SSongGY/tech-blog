"""LSM 트리의 두 압축 방식을 같은 쓰기 흐름에 돌려 세 가지 증폭을 센다.

- 레벨 압축(leveled): L0 파일이 4개가 되면 L1 과 합치고, Ln 이 목표 크기를 넘으면
  파일 하나를 골라 Ln+1 의 겹치는 파일과 합친다. 목표 크기는 레벨마다 10배.
- 크기 계층 압축(tiered): 같은 계층에 정렬 run 이 4개 모이면 하나로 합쳐 다음 계층에 둔다.

크기는 바이트 대신 "항목(키-값 한 쌍) 수"로 센다. 블룸 필터·블록 캐시는 없다.
RocksDB 의 실제 파일 선택 규칙과는 다르고, 증폭이 어디서 생기는지를 보이려는 단순 모형이다.
"""
import random
from bisect import bisect_left

SEED = 20261108
MEMTABLE_ENTRIES = 1_000
FILE_ENTRIES = 1_000
L0_TRIGGER = 4
LEVEL_BASE = 4_000
LEVEL_MULTIPLIER = 10
TIER_TRIGGER = 4
# 처음 몇 번의 압축은 데이터가 작아 비율이 크게 튄다. 살아 있는 키가 이만큼 쌓인 뒤부터 잰다
PEAK_WARMUP_KEYS = 20_000


def merge_runs(runs):
    """runs 는 오래된 것부터. 같은 키는 새 값이 이긴다."""
    merged = {}
    for run in runs:
        for key, value in run:
            merged[key] = value
    return sorted(merged.items())


class Stats:
    def __init__(self):
        self.user_writes = 0
        self.disk_writes = 0
        self.compactions = 0
        self.peak_space_ratio = 0.0
        self.seen = set()           # 삭제가 없으므로 한 번이라도 쓴 키 = 살아 있는 키

    def note_peak(self, entries_on_disk):
        live = len(self.seen)
        if live >= PEAK_WARMUP_KEYS:
            self.peak_space_ratio = max(self.peak_space_ratio, entries_on_disk / live)


class LeveledLsm:
    def __init__(self):
        self.memtable = {}
        self.l0 = []                # 겹치는 run 목록, 오래된 것부터
        self.levels = [[]]          # levels[0] = L1, 각 레벨은 겹치지 않는 파일 목록
        self.cursor = []            # 레벨별 라운드 로빈 위치
        self.stats = Stats()

    def put(self, key, value):
        self.stats.user_writes += 1
        self.stats.seen.add(key)
        self.memtable[key] = value
        if len(self.memtable) >= MEMTABLE_ENTRIES:
            self.flush()

    def flush(self):
        run = sorted(self.memtable.items())
        self.memtable = {}
        self.l0.append(run)
        self.stats.disk_writes += len(run)
        if len(self.l0) >= L0_TRIGGER:
            self.compact_l0()
        level = 0
        while level < len(self.levels):
            if self.level_size(level) > self.target(level):
                self.compact_level(level)
            else:
                level += 1

    def target(self, level):
        return LEVEL_BASE * LEVEL_MULTIPLIER**level

    def level_size(self, level):
        return sum(len(f) for f in self.levels[level])

    def disk_entries(self):
        return sum(len(r) for r in self.l0) + sum(self.level_size(i) for i in range(len(self.levels)))

    def overlapping(self, level, low, high):
        files = self.levels[level]
        hit = [i for i, f in enumerate(files) if not (f[-1][0] < low or f[0][0] > high)]
        return hit

    def write_level(self, level, keep, new_entries, before):
        chunks = [new_entries[i:i + FILE_ENTRIES] for i in range(0, len(new_entries), FILE_ENTRIES)]
        self.stats.disk_writes += len(new_entries)
        self.stats.compactions += 1
        # 출력 파일을 다 쓴 뒤에 입력 파일을 지우므로 그 순간 디스크에 둘 다 있다
        self.stats.note_peak(before + len(new_entries))
        files = keep + chunks
        files.sort(key=lambda f: f[0][0])
        self.levels[level] = files

    def compact_l0(self):
        low = min(r[0][0] for r in self.l0)
        high = max(r[-1][0] for r in self.l0)
        hit = self.overlapping(0, low, high)
        older = [self.levels[0][i] for i in hit]
        keep = [f for i, f in enumerate(self.levels[0]) if i not in hit]
        before = self.disk_entries()
        merged = merge_runs(older + self.l0)
        self.write_level(0, keep, merged, before)
        self.l0 = []

    def compact_level(self, level):
        if level + 1 == len(self.levels):
            self.levels.append([])
        while len(self.cursor) <= level:
            self.cursor.append(-1)
        before = self.disk_entries()
        files = self.levels[level]
        starts = [f[0][0] for f in files]
        pick = bisect_left(starts, self.cursor[level] + 1)
        if pick >= len(files):
            pick = 0
        chosen = files.pop(pick)
        self.cursor[level] = chosen[-1][0]
        hit = self.overlapping(level + 1, chosen[0][0], chosen[-1][0])
        older = [self.levels[level + 1][i] for i in hit]
        keep = [f for i, f in enumerate(self.levels[level + 1]) if i not in hit]
        merged = merge_runs(older + [chosen])
        self.write_level(level + 1, keep, merged, before)

    def live_count(self):
        return len(self.stats.seen)

    def sorted_runs(self):
        return len(self.l0) + sum(1 for lv in self.levels if lv)

    def probes(self, key):
        """메모리 밖에서 몇 개의 run(파일)을 열어 봐야 키를 찾는가."""
        count = 0
        for run in reversed(self.l0):
            count += 1
            if run_contains(run, key):
                return count
        for lv in self.levels:
            if not lv:
                continue
            count += 1
            starts = [f[0][0] for f in lv]
            i = bisect_left(starts, key + 1) - 1
            if i >= 0 and run_contains(lv[i], key):
                return count
        return count


class TieredLsm:
    def __init__(self):
        self.memtable = {}
        self.tiers = [[]]           # tiers[i] = 그 계층의 run 목록, 오래된 것부터
        self.stats = Stats()

    def put(self, key, value):
        self.stats.user_writes += 1
        self.stats.seen.add(key)
        self.memtable[key] = value
        if len(self.memtable) >= MEMTABLE_ENTRIES:
            self.flush()

    def flush(self):
        run = sorted(self.memtable.items())
        self.memtable = {}
        self.tiers[0].append(run)
        self.stats.disk_writes += len(run)
        tier = 0
        while tier < len(self.tiers):
            if len(self.tiers[tier]) >= TIER_TRIGGER:
                self.compact_tier(tier)
            tier += 1

    def compact_tier(self, tier):
        if tier + 1 == len(self.tiers):
            self.tiers.append([])
        before = self.disk_entries()
        merged = merge_runs(self.tiers[tier])
        self.stats.disk_writes += len(merged)
        self.stats.compactions += 1
        self.stats.note_peak(before + len(merged))
        self.tiers[tier] = []
        self.tiers[tier + 1].append(merged)

    def disk_entries(self):
        return sum(len(r) for t in self.tiers for r in t)

    def live_count(self):
        return len(self.stats.seen)

    def sorted_runs(self):
        return sum(len(t) for t in self.tiers)

    def probes(self, key):
        count = 0
        for t in self.tiers:              # 낮은 계층일수록 새 데이터
            for run in reversed(t):
                count += 1
                if run_contains(run, key):
                    return count
        return count


def run_contains(run, key):
    i = bisect_left(run, (key,))
    return i < len(run) and run[i][0] == key


def drive(lsm, key_space, total_writes, seed):
    rng = random.Random(seed)
    for seq in range(total_writes):
        lsm.put(rng.randrange(key_space), seq)
    if lsm.memtable:
        lsm.flush()
    return lsm


def report(name, lsm, seed):
    s = lsm.stats
    live = lsm.live_count()
    disk = lsm.disk_entries()
    rng = random.Random(seed + 1)
    keys = sorted(collect_keys(lsm))
    sample = [rng.choice(keys) for _ in range(2_000)]
    avg_probe = sum(lsm.probes(k) for k in sample) / len(sample)
    print(f"  {name:<10}| {s.disk_writes / s.user_writes:6.2f} | {disk / live:8.2f} | "
          f"{s.peak_space_ratio:8.2f} | {lsm.sorted_runs():5d} | {avg_probe:9.2f} | {s.compactions:6d}")


def collect_keys(lsm):
    keys = set()
    if isinstance(lsm, LeveledLsm):
        for r in lsm.l0:
            keys.update(k for k, _ in r)
        for lv in lsm.levels:
            for f in lv:
                keys.update(k for k, _ in f)
    else:
        for t in lsm.tiers:
            for r in t:
                keys.update(k for k, _ in r)
    return keys


def experiment(title, key_space, total_writes):
    print(f"== {title}: 쓰기 {total_writes:,}건, 키 공간 {key_space:,} ==")
    print("  방식      | 쓰기증폭 | 공간(끝) | 공간(최대) | run 수 | 평균 탐색 run | 압축 횟수")
    for name, cls in (("레벨", LeveledLsm), ("크기 계층", TieredLsm)):
        lsm = drive(cls(), key_space, total_writes, SEED)
        report(name, lsm, SEED)
    print()


def show_levels():
    print("== 레벨 압축이 끝난 뒤 레벨별 크기 (갱신 위주 흐름) ==")
    lsm = drive(LeveledLsm(), 50_000, 400_000, SEED)
    print(f"  L0 run {len(lsm.l0)}개, {sum(len(r) for r in lsm.l0):,} 항목")
    for i, lv in enumerate(lsm.levels, start=1):
        print(f"  L{i} 파일 {len(lv):3d}개, {sum(len(f) for f in lv):7,} 항목 (목표 {lsm.target(i - 1):,})")
    print()
    print("== 크기 계층 압축이 끝난 뒤 계층별 run 크기 (갱신 위주 흐름) ==")
    lsm = drive(TieredLsm(), 50_000, 400_000, SEED)
    for i, t in enumerate(lsm.tiers):
        print(f"  계층 {i}: run {len(t)}개 {[len(r) for r in t]}")
    print()


def main():
    print(f"random seed = {SEED}")
    print(f"memtable {MEMTABLE_ENTRIES:,} 항목 · 파일 {FILE_ENTRIES:,} 항목 · L0 트리거 {L0_TRIGGER} · "
          f"L1 목표 {LEVEL_BASE:,} · 배수 {LEVEL_MULTIPLIER} · 계층 트리거 {TIER_TRIGGER}")
    print()
    experiment("갱신 위주(같은 키를 여러 번 쓴다)", 50_000, 400_000)
    experiment("삽입 위주(대부분 새 키)", 10_000_000, 400_000)
    show_levels()


if __name__ == "__main__":
    main()
