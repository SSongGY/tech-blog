"""CIDR 집약이 라우팅 항목 수를 어떻게 줄이고 어디서 깨지는지 계산한다.

주소는 RFC 5737 이 문서용으로 예약한 세 블록만 쓴다.
"""

import ipaddress
import sys

BLOCK = ipaddress.ip_network("203.0.113.0/24")          # TEST-NET-3
OTHERS = [ipaddress.ip_network("192.0.2.0/24"),         # TEST-NET-1
          ipaddress.ip_network("198.51.100.0/24")]      # TEST-NET-2


def common_prefix(networks):
    """여러 접두사를 한꺼번에 덮는 가장 긴(=가장 좁은) 접두사."""
    lo = min(int(n.network_address) for n in networks)
    hi = max(int(n.broadcast_address) for n in networks)
    length = 32
    while length and (lo >> (32 - length)) != (hi >> (32 - length)):
        length -= 1
    return ipaddress.ip_network((lo & ~((1 << (32 - length)) - 1), length))


def show(title, networks):
    print(f"[{title}]")
    for n in networks:
        print(f"  {n}")
    collapsed = list(ipaddress.collapse_addresses(networks))
    print(f"  -> 집약 결과 {len(networks)}개에서 {len(collapsed)}개로: "
          f"{', '.join(str(c) for c in collapsed)}\n")
    return collapsed


def main():
    print(f"파이썬 {sys.version.split()[0]} / ipaddress (표준 라이브러리)\n")

    # 1. 인접하고 정렬된 접두사는 하나로 묶인다
    customers = list(BLOCK.subnets(new_prefix=26))
    show("사업자가 203.0.113.0/24 를 고객 넷에게 /26 씩 위임", customers)

    # 2. 같은 산수를 할당 단위별로 — 집약하면 어느 경우든 항목 1개
    print("[쪼갠 단위에 따른 항목 수]")
    for block_len, unit in ((24, 26), (20, 24), (16, 24), (12, 24)):
        count = 1 << (unit - block_len)
        print(f"  /{block_len} 를 /{unit} 단위로 위임 -> 개별 광고 {count:>5}개 / 집약 광고 1개")
    print()

    # 3. 인접하지 않으면 묶이지 않는다
    scattered = [BLOCK] + OTHERS
    show("서로 떨어진 세 블록", scattered)
    cover = common_prefix(scattered)
    print(f"  억지로 하나로 덮으면 {cover} — 주소 {cover.num_addresses:,}개를 덮는다")
    print(f"  그 중 실제로 가진 것은 {sum(n.num_addresses for n in scattered):,}개뿐이다\n")

    # 4. 한 조각이 다른 사업자로 옮겨가면 구멍이 생긴다
    moved = ipaddress.ip_network("203.0.113.128/26")
    print("[고객 한 곳이 사업자를 옮겼을 때]")
    print(f"  원 사업자가 광고하는 집약  : {BLOCK}")
    print(f"  새 사업자가 광고하는 구체  : {moved}")
    print(f"  -> 전역 테이블 항목 1개에서 2개로 늘어난다")
    probe = ipaddress.ip_address("203.0.113.130")
    matches = [n for n in (BLOCK, moved) if probe in n]
    best = max(matches, key=lambda n: n.prefixlen)
    print(f"  {probe} 는 {len(matches)}개 경로에 맞고, 최장 일치는 {best} 이다\n")

    # 5. 집약에는 맞지만 더 구체적인 경로가 없는 구간
    assigned = [customers[0], customers[1], customers[3]]
    print("[집약을 광고하면서 아직 배정하지 않은 구간]")
    print(f"  광고하는 집약 : {BLOCK}")
    print(f"  배정한 구체   : {', '.join(str(n) for n in assigned)}")
    holes = [c for c in customers if c not in assigned]
    for h in holes:
        print(f"  -> {h} 로 온 패킷은 집약에만 맞는다. 이 패킷을 버리지 않으면 "
              f"전달 루프가 생길 수 있다 (RFC 4632 §5.1 규칙 2)")


if __name__ == "__main__":
    main()
