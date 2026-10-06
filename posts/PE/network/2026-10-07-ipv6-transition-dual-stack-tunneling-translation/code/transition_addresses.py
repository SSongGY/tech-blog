"""IPv6 전환 기술이 쓰는 주소를 RFC 에 적힌 규칙대로 계산하고, RFC 의 예시와 맞는지 검산한다.

- 변환(NAT64/DNS64): RFC 6052 의 IPv4 내장 IPv6 주소. 프리픽스 길이 6가지와 u 옥텟(비트 64~71) 규칙
- 터널링(6to4): RFC 3056 의 2002:V4ADDR::/48
- 터널링(구성 터널): RFC 4213 의 동적 터널 MTU = IPv4 경로 MTU - IPv4 헤더
"""

import ipaddress
import platform
import sys

# RFC 6052 §2.4 의 표를 그대로 옮겼다. 계산 결과를 이 값과 비교한다
RFC6052_EXAMPLES = [
    ("2001:db8::/32", "2001:db8:c000:221::"),
    ("2001:db8:100::/40", "2001:db8:1c0:2:21::"),
    ("2001:db8:122::/48", "2001:db8:122:c000:2:2100::"),
    ("2001:db8:122:300::/56", "2001:db8:122:3c0:0:221::"),
    ("2001:db8:122:344::/64", "2001:db8:122:344:c0:2:2100::"),
    ("2001:db8:122:344::/96", "2001:db8:122:344::192.0.2.33"),
]
EXAMPLE_IPV4 = "192.0.2.33"
WELL_KNOWN_PREFIX = ipaddress.IPv6Network("64:ff9b::/96")
IPV4_HEADER_BYTES = 20


def embed_ipv4(prefix: ipaddress.IPv6Network, ipv4: ipaddress.IPv4Address) -> ipaddress.IPv6Address:
    """RFC 6052 §2.2: 프리픽스 뒤에 IPv4 32비트를 넣되 비트 64~71(u 옥텟)은 건너뛰고 0으로 둔다."""
    if prefix.prefixlen not in (32, 40, 48, 56, 64, 96):
        raise ValueError(f"RFC 6052 가 허용하지 않는 길이: /{prefix.prefixlen}")
    octets = list(prefix.network_address.packed)
    v4 = list(ipv4.packed)
    position = prefix.prefixlen // 8
    for byte in v4:
        if position == 8:  # u 옥텟 자리는 0으로 남기고 건너뛴다
            position += 1
        octets[position] = byte
        position += 1
    return ipaddress.IPv6Address(bytes(octets))


def extract_ipv4(prefix_len: int, address: ipaddress.IPv6Address) -> ipaddress.IPv4Address:
    """embed_ipv4 의 역. NAT64 가 목적지 IPv6 주소에서 IPv4 서버 주소를 꺼내는 계산이다."""
    octets = address.packed
    picked = []
    position = prefix_len // 8
    while len(picked) < 4:
        if position != 8:
            picked.append(octets[position])
        position += 1
    return ipaddress.IPv4Address(bytes(picked))


def dns64_synthesize(ipv4_text: str) -> str:
    """잘 알려진 프리픽스(64:ff9b::/96)로 AAAA 를 합성한다. RFC 6052 §3.1 의 제한을 지킨다."""
    ipv4 = ipaddress.IPv4Address(ipv4_text)
    if not ipv4.is_global:
        return f"{ipv4} -> 합성하지 않음 (전역 주소가 아니다, RFC 6052 §3.1)"
    return f"{ipv4} -> {embed_ipv4(WELL_KNOWN_PREFIX, ipv4)}"


def sixtofour_prefix(ipv4_text: str) -> ipaddress.IPv6Network:
    """RFC 3056 §2: 2002::/16 뒤에 IPv4 32비트를 붙여 /48 사이트 프리픽스를 만든다."""
    v4 = ipaddress.IPv4Address(ipv4_text).packed
    return ipaddress.IPv6Network((b"\x20\x02" + v4 + bytes(10), 48))


def main() -> None:
    print(f"Python {platform.python_version()} / {platform.system()} {platform.release()}")
    print(f"ipaddress 모듈 (표준 라이브러리, {sys.version.split()[0]})")

    print("\n== 1. RFC 6052 §2.4 표 검산 — IPv4 192.0.2.33 을 프리픽스 길이별로 넣는다")
    ipv4 = ipaddress.IPv4Address(EXAMPLE_IPV4)
    for prefix_text, expected_text in RFC6052_EXAMPLES:
        prefix = ipaddress.IPv6Network(prefix_text)
        got = embed_ipv4(prefix, ipv4)
        expected = ipaddress.IPv6Address(expected_text)
        back = extract_ipv4(prefix.prefixlen, got)
        verdict = "일치" if got == expected else "불일치"
        print(f"  /{prefix.prefixlen:<3} {str(got):<32} RFC {verdict} · 역변환 {back}")

    print("\n== 2. u 옥텟(비트 64~71)이 실제로 0인가 — 9번째 바이트")
    for prefix_text, _ in RFC6052_EXAMPLES:
        prefix = ipaddress.IPv6Network(prefix_text)
        got = embed_ipv4(prefix, ipv4)
        print(f"  /{prefix.prefixlen:<3} 9번째 바이트 = 0x{got.packed[8]:02x}")

    print("\n== 3. 허용되지 않는 길이")
    try:
        embed_ipv4(ipaddress.IPv6Network("2001:db8::/44"), ipv4)
    except ValueError as exc:
        print(f"  {exc}")

    print("\n== 4. DNS64 합성 — 잘 알려진 프리픽스 64:ff9b::/96")
    for text in ("192.0.2.33", "8.8.8.8", "10.1.2.3", "192.168.0.10"):
        print(f"  {dns64_synthesize(text)}")

    print("\n== 5. 6to4 사이트 프리픽스 — 2002:V4ADDR::/48")
    for text in ("8.8.8.8", "1.1.1.1"):
        net = sixtofour_prefix(text)
        host = net.network_address + 1
        print(f"  {text:<14} -> {net}  (첫 주소 {host}, 표준 라이브러리 sixtofour = {host.sixtofour})")

    print("\n== 6. 구성 터널 MTU — RFC 4213 §3.2")
    for path_mtu in (1500, 1492, 1400):
        dynamic = path_mtu - IPV4_HEADER_BYTES
        print(f"  IPv4 경로 MTU {path_mtu} -> 동적 터널 MTU {dynamic}")
    print("  정적 터널 MTU 허용 범위 1280~1480, 권고값 1280")


if __name__ == "__main__":
    main()
