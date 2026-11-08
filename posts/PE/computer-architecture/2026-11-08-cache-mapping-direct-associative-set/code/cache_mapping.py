"""캐시 사상 방식 세 가지를 계산하고 시뮬레이션해 검산한다.

1) 주소 비트 분할 — 오프셋 O, 세트 인덱스 S, 태그 T
2) 블록 번호 접근열 하나를 직접·2-way·완전 연관으로 따라가며 적중/실패 표
3) 실패를 3C(최초·용량·충돌)로 나눠 센다
4) Drepper 6.2.1 의 4096 바이트 간격 실험을 32KB·8-way L1d 모형으로 재현
5) 캐시 크기만큼 떨어진 두 배열을 번갈아 읽을 때
"""
from collections import OrderedDict


def log2_exact(value):
    bits = value.bit_length() - 1
    if 1 << bits != value:
        raise ValueError(f"{value} 는 2의 거듭제곱이 아니다")
    return bits


def split_bits(cache_bytes, line_bytes, ways, address_bits=32):
    """캐시 크기 = 라인 크기 x 연관도 x 세트 수 (Drepper 3.3.1)."""
    num_lines = cache_bytes // line_bytes
    num_sets = num_lines // ways
    offset_bits = log2_exact(line_bytes)
    set_bits = log2_exact(num_sets)
    tag_bits = address_bits - set_bits - offset_bits
    return num_sets, offset_bits, set_bits, tag_bits


class Cache:
    """세트마다 LRU 로 교체하는 연관 캐시. ways=1 이면 직접 사상, ways=라인 수면 완전 연관."""

    def __init__(self, num_lines, ways, line_bytes=1):
        self.num_sets = num_lines // ways
        self.ways = ways
        self.line_bytes = line_bytes
        self.sets = [OrderedDict() for _ in range(self.num_sets)]

    def access(self, address):
        block = address // self.line_bytes
        index = block % self.num_sets
        tag = block // self.num_sets
        lines = self.sets[index]
        if tag in lines:
            lines.move_to_end(tag)
            return True, index
        if len(lines) >= self.ways:
            lines.popitem(last=False)
        lines[tag] = True
        return False, index


def run(cache, addresses):
    return [cache.access(a)[0] for a in addresses]


def section_bits():
    print("== 1) 주소 비트 분할 (32비트 주소) ==")
    print("  구성                         세트 수   O   S   T   태그 비교기")
    configs = [
        ("4MB / 64B / 직접 사상", 4 << 20, 64, 1),
        ("4MB / 64B / 8-way", 4 << 20, 64, 8),
        ("4MB / 64B / 완전 연관", 4 << 20, 64, (4 << 20) // 64),
        ("32KB / 64B / 8-way", 32 << 10, 64, 8),
    ]
    for label, size, line, ways in configs:
        sets, o, s, t = split_bits(size, line, ways)
        print(f"  {label:26} {sets:>7}  {o:>2}  {s:>2}  {t:>2}   {ways:>6}")
    address = 0x12345678
    sets, o, s, t = split_bits(32 << 10, 64, 8)
    offset = address & ((1 << o) - 1)
    index = (address >> o) & ((1 << s) - 1)
    tag = address >> (o + s)
    print(f"  주소 0x{address:08X} 를 32KB/64B/8-way 로 나누면 "
          f"tag=0x{tag:05X} set={index} offset={offset}")
    print()


TRACE = [0, 8, 0, 6, 8]


def section_trace():
    print("== 2) 블록 4개짜리 캐시, 접근열", TRACE, "==")
    for label, ways in (("직접 사상", 1), ("2-way", 2), ("완전 연관", 4)):
        cache = Cache(num_lines=4, ways=ways)
        cells = []
        for block in TRACE:
            hit, index = cache.access(block)
            cells.append(f"{block}->세트{index}:{'적중' if hit else '실패'}")
        misses = sum(1 for c in cells if c.endswith("실패"))
        print(f"  {label:6} 실패 {misses}회 | " + "  ".join(cells))
    print()


def classify_3c(addresses, num_lines, ways, line_bytes=1):
    """최초 = 처음 보는 블록, 용량 = 같은 크기 완전 연관 LRU 도 놓친 나머지, 충돌 = 그 밖."""
    target = run(Cache(num_lines, ways, line_bytes), addresses)
    full = run(Cache(num_lines, num_lines, line_bytes), addresses)
    seen = set()
    counts = {"최초": 0, "용량": 0, "충돌": 0}
    for address, hit, full_hit in zip(addresses, target, full):
        block = address // line_bytes
        first = block not in seen
        seen.add(block)
        if hit:
            continue
        if first:
            counts["최초"] += 1
        elif not full_hit:
            counts["용량"] += 1
        else:
            counts["충돌"] += 1
    return counts


def section_3c():
    print("== 3) 접근열", TRACE, "의 실패를 3C 로 ==")
    for label, ways in (("직접 사상", 1), ("2-way", 2), ("완전 연관", 4)):
        print(f"  {label:6} {classify_3c(TRACE, 4, ways)}")
    print()


def section_stride():
    print("== 4) 4096 바이트 간격 리스트를 100바퀴 (32KB, 64B 라인) ==")
    print("  원소 수 | 직접 사상 | 8-way    | 완전 연관 | 8-way 3C")
    for count in (8, 9, 16):
        addresses = [i * 4096 for i in range(count)] * 100
        rates = []
        for ways in (1, 8, 512):
            hits = run(Cache(num_lines=512, ways=ways, line_bytes=64), addresses)
            rates.append(sum(hits) / len(hits))
        c3 = classify_3c(addresses, 512, 8, 64)
        print(f"  {count:>6} | {rates[0]:8.1%} | {rates[1]:8.1%} | {rates[2]:8.1%} | {c3}")
    addresses = [i * (4096 + 64) for i in range(16)] * 100
    hits = run(Cache(num_lines=512, ways=8, line_bytes=64), addresses)
    print(f"  간격을 4096+64 로 바꾸고 16개, 8-way: 적중률 {sum(hits) / len(hits):.1%}")
    print()


def section_two_arrays():
    print("== 5) 8바이트 원소 2048개 배열 a, b 를 a[i], b[i] 순으로 읽기 (32KB, 64B) ==")
    for gap_label, base_b in (("b 시작 = 32KB (캐시 크기)", 32 << 10), ("b 시작 = 32KB + 64B", (32 << 10) + 64)):
        addresses = []
        for i in range(2048):
            addresses.append(i * 8)
            addresses.append(base_b + i * 8)
        row = []
        for label, ways in (("직접", 1), ("2-way", 2), ("8-way", 8)):
            hits = run(Cache(num_lines=512, ways=ways, line_bytes=64), addresses)
            row.append(f"{label} {sum(hits) / len(hits):6.2%}")
        print(f"  {gap_label:26} | " + " | ".join(row))
    print()


def main():
    section_bits()
    section_trace()
    section_3c()
    section_stride()
    section_two_arrays()


if __name__ == "__main__":
    main()
