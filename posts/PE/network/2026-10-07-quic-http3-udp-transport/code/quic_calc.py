"""RFC 9000(QUIC)의 규칙 몇 가지를 계산으로 검산한다. 패킷을 실제로 주고받는 실험이 아니다.

1. 가변 길이 정수 인코딩(RFC 9000 §16) — 부록 A.1 의 예시 4개를 디코딩·재인코딩한다
2. 스트림 ID 의 하위 2비트(§2.1) — ID 0~11 이 어느 종류인지 표로 만든다
3. 머리 막힘(HOL blocking) 모형 — RFC 9114 §1 의 문장을 그대로 규칙으로 옮겨,
   패킷 하나가 사라졌을 때 TCP 위의 HTTP/2 와 QUIC 위의 HTTP/3 가 각각 몇 스트림을
   멈추는지 센다
4. 연결 수립에 드는 왕복 수 — RFC 9293(TCP)·RFC 8446(TLS 1.3)·RFC 9001(QUIC) 이 적은
   왕복 수를 RTT 에 곱한다
"""

# RFC 9000 Appendix A.1 에 적힌 예시 (16진 바이트열, 10진 값)
RFC_SAMPLES = [
    ("c2197c5eff14e88c", 151_288_809_941_952_652),
    ("9d7f3e7d", 494_878_333),
    ("7bbd", 15_293),
    ("25", 37),
]

# RFC 9000 §16 Table 4
VARINT_TABLE = [
    ("00", 1, 6, 2**6 - 1),
    ("01", 2, 14, 2**14 - 1),
    ("10", 4, 30, 2**30 - 1),
    ("11", 8, 62, 2**62 - 1),
]

STREAM_TYPES = {
    0x00: "클라이언트 시작 · 양방향",
    0x01: "서버 시작 · 양방향",
    0x02: "클라이언트 시작 · 단방향",
    0x03: "서버 시작 · 단방향",
}


def decode_varint(data: bytes) -> tuple[int, int]:
    """첫 바이트의 상위 2비트로 길이를 정하고, 그 2비트를 뺀 나머지를 빅엔디안으로 읽는다."""
    prefix = data[0] >> 6
    length = 1 << prefix
    value = data[0] & 0x3F
    for byte in data[1:length]:
        value = (value << 8) | byte
    return value, length


def encode_varint(value: int) -> bytes:
    for prefix, length, usable_bits, _max in VARINT_TABLE:
        if value < (1 << usable_bits):
            raw = value | (int(prefix, 2) << (8 * length - 2))
            return raw.to_bytes(length, "big")
    raise ValueError("2^62 이상은 인코딩할 수 없다")


def stream_type(stream_id: int) -> str:
    return STREAM_TYPES[stream_id & 0x03]


def hol_blocking(packets: list[tuple[int, str]], lost: int) -> dict[str, list[str]]:
    """패킷 번호 순으로 (번호, 스트림) 이 전송됐고 `lost` 번이 사라졌다.

    TCP: 바이트열 하나. 사라진 패킷 뒤의 바이트는 재전송이 올 때까지 응용에 못 올라간다.
         (RFC 9114 §1 — 손실 패킷과 무관한 트랜잭션까지 전부 멈춘다)
    QUIC: 스트림마다 순서를 지킨다. 사라진 패킷이 실은 스트림만 그 자리에서 기다린다.
    """
    tcp_blocked = {stream for number, stream in packets if number > lost}
    quic_blocked = {stream for number, stream in packets if number == lost}
    return {"tcp": sorted(tcp_blocked), "quic": sorted(quic_blocked)}


def main() -> None:
    print("== 1. 가변 길이 정수 — RFC 9000 부록 A.1 예시 검산")
    print("   2MSB | 길이 | 쓰는 비트 | 최대값")
    for prefix, length, usable_bits, max_value in VARINT_TABLE:
        print(f"   {prefix}   | {length}    | {usable_bits:>2}        | {max_value:,}")
    print()
    for hex_text, expected in RFC_SAMPLES:
        data = bytes.fromhex(hex_text)
        value, length = decode_varint(data)
        again = encode_varint(value).hex()
        verdict = "RFC 일치" if value == expected else f"RFC 불일치 (RFC: {expected:,})"
        roundtrip = "재인코딩 일치" if again == hex_text else f"재인코딩 다름 ({again})"
        print(f"   {hex_text:<18} -> {length}바이트, 값 {value:,}  {verdict} · {roundtrip}")
    print()
    print("   같은 값 300 을 더 긴 형식으로도 적을 수 있다 — 디코더는 어느 쪽이든 300 으로 읽는다")
    for length in (2, 4, 8):
        prefix = {2: 0b01, 4: 0b10, 8: 0b11}[length]
        raw = (300 | (prefix << (8 * length - 2))).to_bytes(length, "big")
        print(f"   {raw.hex():<18} -> {decode_varint(raw)[0]}")
    print()

    print("== 2. 스트림 ID 하위 2비트 — RFC 9000 §2.1 Table 1")
    for stream_id in range(12):
        print(f"   ID {stream_id:>2} (하위 2비트 {stream_id & 3:#04x}) : {stream_type(stream_id)}")
    print("   HTTP/3 요청 스트림(클라이언트 양방향)은 0, 4, 8, … / 제어 스트림은 단방향 2, 3, 6, 7, … 중 하나")
    print()

    print("== 3. 머리 막힘 모형 — 스트림 A·B·C 가 패킷 6개에 번갈아 실렸고 2번이 사라졌다")
    packets = [(1, "A"), (2, "B"), (3, "C"), (4, "A"), (5, "B"), (6, "C")]
    blocked = hol_blocking(packets, lost=2)
    print(f"   전송 순서: {' '.join(f'{n}:{s}' for n, s in packets)}")
    print(f"   TCP 위 HTTP/2 — 재전송을 기다리는 스트림: {blocked['tcp']}  ({len(blocked['tcp'])}개)")
    print(f"   QUIC 위 HTTP/3 — 재전송을 기다리는 스트림: {blocked['quic']}  ({len(blocked['quic'])}개)")
    print()

    print("== 4. 첫 요청을 보내기까지의 왕복 수 × RTT")
    print("   TCP 3-way 1 RTT(RFC 9293 §3.5) + TLS 1.3 1 RTT(RFC 8446 §2) = 2 RTT")
    print("   QUIC 1 RTT(RFC 9001 §4.1 — TLS 1.3 핸드셰이크를 전송 핸드셰이크와 합침), 재개 시 0-RTT")
    print("   RTT(ms) | TCP+TLS 1.3 | QUIC 첫 연결 | QUIC 0-RTT 재개")
    for rtt in (20, 50, 100, 200):
        print(f"   {rtt:>7} | {2 * rtt:>11} | {1 * rtt:>12} | {0 * rtt:>15}")


if __name__ == "__main__":
    main()
