"""TLB 와 유효 메모리 접근 시간(EAT)을 계산하고, 접근 기록으로 TLB 를 흉내 내 검산한다.

1) EAT 공식 — 페이지 테이블 단계 수 k 와 TLB 적중률 a 로 계산
2) 목표 지연 이내로 두려면 적중률이 얼마여야 하는가 — 공식을 a 에 대해 푼다
3) OSTEP 19장 배열 예제를 그대로 돌려 적중률 70% 를 재현
4) 접근 패턴별 적중률 측정 — 순차·페이지 간격·무작위
5) 문맥 교환 때 TLB 를 비우는 경우와 ASID 로 구분하는 경우
6) 측정한 적중률을 공식에 넣어 시뮬레이션의 평균 시간과 맞는지 확인
"""
import random
from collections import OrderedDict

MEMORY_NS = 100  # 주기억장치 1회 접근 — 시험 문제에 흔히 주어지는 가정값
TLB_NS = 20      # TLB 1회 조회 — 같은 가정값
SEED = 7


def eat(hit_ratio, levels, tlb_ns=TLB_NS, memory_ns=MEMORY_NS):
    """적중이면 TLB + 데이터 1회, 실패면 TLB + 페이지 테이블 k회 + 데이터 1회."""
    hit_cost = tlb_ns + memory_ns
    miss_cost = tlb_ns + (levels + 1) * memory_ns
    return hit_ratio * hit_cost + (1 - hit_ratio) * miss_cost


def required_hit_ratio(target_ns, levels, tlb_ns=TLB_NS, memory_ns=MEMORY_NS):
    # EAT = (tlb + m) + (1 - a) * k * m  을 a 에 대해 푼다
    hit_cost = tlb_ns + memory_ns
    return 1 - (target_ns - hit_cost) / (levels * memory_ns)


class Tlb:
    """완전 연관 TLB. 교체는 LRU. ASID 를 쓰면 (asid, vpn) 을 키로 둔다."""

    def __init__(self, entry_count):
        self.entry_count = entry_count
        self.entries = OrderedDict()
        self.hits = 0
        self.misses = 0

    def lookup(self, vpn, asid=0):
        key = (asid, vpn)
        if key in self.entries:
            self.entries.move_to_end(key)
            self.hits += 1
            return True
        self.misses += 1
        if len(self.entries) >= self.entry_count:
            self.entries.popitem(last=False)
        self.entries[key] = True
        return False

    def flush(self):
        self.entries.clear()

    @property
    def hit_ratio(self):
        return self.hits / (self.hits + self.misses)


def section_formula():
    print("== 1) EAT 공식 (TLB %dns, 메모리 %dns) ==" % (TLB_NS, MEMORY_NS))
    print("  적중률 | 1단계 | 2단계 | 4단계 | 5단계")
    for hit_ratio in (0.80, 0.90, 0.98, 0.99):
        cells = ["%5.1f" % eat(hit_ratio, k) for k in (1, 2, 4, 5)]
        print("  %5.0f%% | %s" % (hit_ratio * 100, " | ".join(cells)))
    print("  (TLB 가 없을 때 4단계: %dns)" % ((4 + 1) * MEMORY_NS))
    print()
    print("  TLB 시간을 0 으로 두는 교재식 (1단계, 적중률 80%%): %.1f ns"
          % eat(0.80, 1, tlb_ns=0))
    print()


def section_required():
    print("== 2) 목표 EAT 를 지키는 최소 적중률 ==")
    for target in (130, 125):
        cells = []
        for k in (1, 2, 4, 5):
            cells.append("%d단계 %.4f" % (k, required_hit_ratio(target, k)))
        print("  목표 %dns: %s" % (target, " · ".join(cells)))
    print()


def section_ostep_array():
    print("== 3) OSTEP 19.2 배열 예제 재현 ==")
    # 4바이트 정수 10개가 가상 주소 100 부터 놓이고, 페이지는 16바이트다
    page_size = 16
    tlb = Tlb(entry_count=16)
    marks = []
    for i in range(10):
        address = 100 + 4 * i
        marks.append("hit" if tlb.lookup(address // page_size) else "miss")
    print("  " + ", ".join(marks))
    print("  적중률 %.0f%%" % (tlb.hit_ratio * 100))
    print()


def run_pattern(addresses, entry_count, page_size=4096):
    tlb = Tlb(entry_count)
    for address in addresses:
        tlb.lookup(address // page_size)
    return tlb.hit_ratio


def section_patterns():
    print("== 4) 접근 패턴별 적중률 (페이지 4KB, TLB 64항목, 접근 20만 회) ==")
    rng = random.Random(SEED)
    count = 200_000
    patterns = {
        "순차 4바이트 간격": [4 * i for i in range(count)],
        "4KB 간격(매번 다른 페이지)": [4096 * i for i in range(count)],
        "64개 페이지 안 무작위": [rng.randrange(64 * 4096) for _ in range(count)],
        "65개 페이지 순환": [4096 * (i % 65) for i in range(count)],
        "1024개 페이지 안 무작위": [rng.randrange(1024 * 4096) for _ in range(count)],
    }
    for name, addresses in patterns.items():
        ratio = run_pattern(addresses, entry_count=64)
        print("  %-24s 적중률 %7.3f%%  EAT(4단계) %6.1f ns"
              % (name, ratio * 100, eat(ratio, 4)))
    print()
    return patterns


def section_context_switch():
    print("== 5) 문맥 교환: TLB 비우기 vs ASID (프로세스 2개, 1000회마다 교대) ==")
    rng = random.Random(SEED)
    working_pages = 32
    slice_length = 1000
    for use_asid in (False, True):
        tlb = Tlb(entry_count=64)
        for turn in range(200):
            asid = turn % 2
            if not use_asid:
                tlb.flush()
            for _ in range(slice_length):
                tlb.lookup(rng.randrange(working_pages), asid=asid if use_asid else 0)
        label = "ASID 로 구분" if use_asid else "교환마다 비움"
        print("  %-14s 적중률 %.3f%%  미스 %d회" % (label, tlb.hit_ratio * 100, tlb.misses))
    print()


def section_crosscheck():
    print("== 6) 측정 적중률을 공식에 넣은 값 vs 접근마다 시간을 더한 평균 ==")
    rng = random.Random(SEED)
    addresses = [rng.randrange(256 * 4096) for _ in range(100_000)]
    levels = 4
    tlb = Tlb(entry_count=64)
    total_ns = 0
    for address in addresses:
        if tlb.lookup(address // 4096):
            total_ns += TLB_NS + MEMORY_NS
        else:
            total_ns += TLB_NS + (levels + 1) * MEMORY_NS
    print("  측정 적중률 %.4f" % tlb.hit_ratio)
    print("  공식 EAT    %.3f ns" % eat(tlb.hit_ratio, levels))
    print("  누적 평균   %.3f ns" % (total_ns / len(addresses)))
    print()


def main():
    section_formula()
    section_required()
    section_ostep_array()
    section_patterns()
    section_context_switch()
    section_crosscheck()


if __name__ == "__main__":
    main()
