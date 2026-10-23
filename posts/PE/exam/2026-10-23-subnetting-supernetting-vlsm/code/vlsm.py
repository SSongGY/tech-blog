"""192.168.0.0/22 를 네 팀에 VLSM 으로 나누고 검산한다.

표준 라이브러리 ipaddress 만 쓴다. 손으로 센 비트 수가 맞는지 확인하는 것이
목적이므로, 분할 규칙(필요 호스트 수 -> 접두어 길이)도 직접 계산한다.
"""

import ipaddress

BASE = ipaddress.IPv4Network("192.168.0.0/22")

# 문항이 준 소요 인원. 큰 쪽부터 배치해야 빈틈이 생기지 않는다.
DEMANDS = [
    ("개발팀", 500),
    ("영업팀", 250),
    ("인사팀", 125),
    ("보안팀", 125),
]


def required_prefix(hosts):
    """호스트 n 대를 수용하는 가장 작은 접두어 길이.

    네트워크 주소와 브로드캐스트 주소가 각각 한 자리씩 빠지므로 n + 2 를 담아야 한다.
    """
    size = 1
    bits = 0
    while size < hosts + 2:
        size *= 2
        bits += 1
    return 32 - bits


def allocate(base, demands):
    """큰 블록부터 차례로 떼어 준다. cursor 는 다음에 쓸 첫 주소."""
    cursor = int(base.network_address)
    result = []
    for name, hosts in sorted(demands, key=lambda d: -d[1]):
        prefix = required_prefix(hosts)
        block = ipaddress.IPv4Network((cursor, prefix))
        result.append((name, hosts, block))
        cursor += block.num_addresses
    return result


def print_allocation(rows):
    head = f"{'팀':<6} {'인원':>5} {'네트워크':<18} {'서브넷 마스크':<17} {'호스트 대역':<31} {'브로드캐스트':<15} {'수용':>6}"
    print(head)
    print("-" * len(head))
    for name, hosts, block in rows:
        first = block.network_address + 1
        last = block.broadcast_address - 1
        print(
            f"{name:<6} {hosts:>5} {str(block):<18} {str(block.netmask):<17} "
            f"{str(first) + ' ~ ' + str(last):<31} {str(block.broadcast_address):<15} "
            f"{block.num_addresses - 2:>6}"
        )


def check(rows):
    """빈틈·겹침·범위 이탈이 없는지 본다. 하나라도 어긋나면 분할이 틀린 것이다."""
    used = 0
    prev_end = int(BASE.network_address) - 1
    for name, hosts, block in rows:
        assert block.subnet_of(BASE), f"{name} 블록이 {BASE} 밖으로 나갔다"
        assert block.num_addresses - 2 >= hosts, f"{name} 수용량 부족"
        assert int(block.network_address) == prev_end + 1, f"{name} 앞에 빈틈이 있다"
        prev_end = int(block.broadcast_address)
        used += block.num_addresses
    print(f"할당 합계    {used} / {BASE.num_addresses} 주소")
    print(f"남는 주소    {BASE.num_addresses - used}")
    print(f"마지막 주소  {ipaddress.IPv4Address(prev_end)} (기준 대역 끝 {BASE.broadcast_address})")


def show_mask_and(a, b, prefix):
    """RFC 950 이 정한 판정: 두 주소를 마스크와 AND 해 같으면 같은 서브넷이다."""
    mask = int(ipaddress.IPv4Network((0, prefix)).netmask)
    na = ipaddress.IPv4Address(int(ipaddress.IPv4Address(a)) & mask)
    nb = ipaddress.IPv4Address(int(ipaddress.IPv4Address(b)) & mask)
    verdict = "같은 서브넷" if na == nb else "다른 서브넷 -> 게이트웨이로"
    print(f"/{prefix:<2} {a:<13} -> {str(na):<13} | {b:<13} -> {str(nb):<13} | {verdict}")


def supernet_demo():
    """반대 방향. 연속된 /24 네 개는 /22 하나로 묶인다."""
    quads = [ipaddress.IPv4Network(f"192.168.{i}.0/24") for i in range(4)]
    merged = list(ipaddress.collapse_addresses(quads))
    print("묶기 전 ", ", ".join(str(q) for q in quads))
    print("묶은 뒤 ", ", ".join(str(m) for m in merged))

    broken = [ipaddress.IPv4Network(f"192.168.{i}.0/24") for i in (0, 1, 2, 5)]
    print("경계가 어긋나면", ", ".join(str(m) for m in ipaddress.collapse_addresses(broken)))


if __name__ == "__main__":
    print(f"기준 대역    {BASE}  마스크 {BASE.netmask}  주소 {BASE.num_addresses}개")
    print(f"사용 범위    {BASE.network_address} ~ {BASE.broadcast_address}")
    print()

    print("[소요 인원 -> 접두어 길이]")
    for name, hosts in DEMANDS:
        p = required_prefix(hosts)
        n = ipaddress.IPv4Network((0, p))
        print(f"  {name} {hosts:>3}명 -> 필요 주소 {hosts + 2:>3}개 -> /{p} ({n.num_addresses}개, 호스트 {n.num_addresses - 2}개)")
    print()

    rows = allocate(BASE, DEMANDS)
    print("[VLSM 분할 결과]")
    print_allocation(rows)
    print()

    print("[검산]")
    check(rows)
    print()

    print("[마스크 AND 판정]")
    show_mask_and("192.168.0.5", "192.168.1.200", 23)
    show_mask_and("192.168.0.5", "192.168.1.200", 24)
    print()

    print("[슈퍼네팅 — 묶는 방향]")
    supernet_demo()
