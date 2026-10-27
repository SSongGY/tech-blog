"""VLSM 배치를 두 순서로 계산해 정렬 제약이 만드는 차이를 보인다.

주소 블록을 쪼갤 때 각 서브넷은 자기 크기의 배수 주소에서만 시작할 수 있다.
이 제약 때문에 배치 순서가 결과를 바꾼다 — 같은 요구, 같은 블록인데 한 순서는
들어가고 다른 순서는 못 들어간다.
"""

import ipaddress
import sys

# RFC 5737 이 문서용으로 예약한 TEST-NET-3 의 앞쪽 절반
BLOCK = ipaddress.ip_network("203.0.113.0/25")

# (세그먼트 이름, 필요한 호스트 수) — 설계서에 적힌 순서 그대로
REQUIREMENTS = [
    ("영업망", 50),
    ("본사-지사 링크", 2),
    ("운영망", 25),
    ("본사-DR 링크", 2),
    ("백업망", 10),
]


def prefix_for(hosts):
    """호스트 n 대를 수용하는 가장 긴(=가장 작은) 접두사 길이.

    네트워크 주소와 브로드캐스트 주소가 호스트로 못 쓰이므로 n+2 를 담아야 한다.
    """
    length = 32
    while (1 << (32 - length)) - 2 < hosts:
        length -= 1
    return length


def align_up(value, size):
    """value 이상인 size 의 배수. 서브넷은 자기 크기의 배수에서만 시작한다."""
    return -(-value // size) * size


def place(order, label):
    """커서를 앞으로만 옮기며 배치한다. 한 번 건너뛴 자리는 다시 쓰지 않는다."""
    print(f"[{label}]")
    base = int(BLOCK.network_address)
    cursor = base
    limit = base + BLOCK.num_addresses
    skipped = 0
    for name, hosts in order:
        length = prefix_for(hosts)
        size = 1 << (32 - length)
        start = align_up(cursor, size)
        gap = start - cursor
        if start + size > limit:
            print(f"  {name:<14} /{length} ({size:>3}개) 필요 -> "
                  f"{ipaddress.ip_address(start)} 부터 놓아야 하는데 블록 밖이다. 배치 실패")
            print(f"  -> 건너뛴 주소 {skipped}개가 남아 있지만 커서가 지나쳐 쓸 수 없다\n")
            return None
        if gap:
            print(f"  (건너뜀 {ipaddress.ip_address(cursor)} ~ "
                  f"{ipaddress.ip_address(start - 1)} : {gap}개)")
            skipped += gap
        net = ipaddress.ip_network((start, length))
        print(f"  {name:<14} {str(net):<18} 호스트 {size - 2:>3}대 "
              f"({net[0]} ~ {net[-1]})")
        cursor = start + size
    used = cursor - base
    print(f"  -> 사용 {used}개 / 건너뜀 {skipped}개 / 남음 {limit - cursor}개\n")
    return used


def fixed_length():
    """고정 길이 서브넷 — 모든 세그먼트가 가장 큰 세그먼트의 마스크를 쓴다."""
    longest = min(prefix_for(h) for _, h in REQUIREMENTS)
    size = 1 << (32 - longest)
    total = size * len(REQUIREMENTS)
    # 총량을 담는 블록도 자기 크기의 배수에서 시작하므로 2의 거듭제곱으로 올림한다
    length = 32
    while (1 << (32 - length)) < total:
        length -= 1
    print("[고정 길이 — 전부 가장 큰 세그먼트에 맞춘다]")
    print(f"  가장 큰 요구는 {max(h for _, h in REQUIREMENTS)}대 -> 모든 서브넷이 /{longest} ({size}개)")
    print(f"  {len(REQUIREMENTS)}개 세그먼트 x {size} = {total}개 -> 최소 /{length} ({1 << (32 - length)}개) 블록이 필요하다")
    return 1 << (32 - length)


def main():
    print(f"파이썬 {sys.version.split()[0]} / ipaddress (표준 라이브러리)")
    print(f"할당받은 블록 {BLOCK} — 주소 {BLOCK.num_addresses}개\n")

    print("[요구조건]")
    for name, hosts in REQUIREMENTS:
        length = prefix_for(hosts)
        size = 1 << (32 - length)
        print(f"  {name:<14} 호스트 {hosts:>2}대 -> /{length} (주소 {size:>3}개, 호스트 {size - 2:>3}대)")
    demand = sum(1 << (32 - prefix_for(h)) for _, h in REQUIREMENTS)
    print(f"  합계 {demand}개 <= 블록 {BLOCK.num_addresses}개\n")

    place(REQUIREMENTS, "요구 순서 그대로 배치")
    vlsm = place(sorted(REQUIREMENTS, key=lambda r: -r[1]), "큰 것부터 배치")

    fixed = fixed_length()
    print(f"\n[대비] VLSM {BLOCK.num_addresses}개(/{BLOCK.prefixlen}) vs "
          f"고정 길이 {fixed}개 -> {fixed // BLOCK.num_addresses}배")
    print(f"  VLSM 은 같은 요구를 {vlsm}개로 덮고 {BLOCK.num_addresses - vlsm}개를 남겼다")


if __name__ == "__main__":
    main()
