"""RFC 4648 의 Base64 규칙을 직접 구현하고, 표준 라이브러리와 맞춰 본 뒤 틀리기 쉬운 자리를 재현한다.

1) 직접 만든 인코더 — RFC 4648 §10 시험 벡터와 무작위 입력 3,000개로 base64.b64encode 와 비교
2) 입력 길이별 출력 길이와 '=' 개수, Base32·Base16 과 크기 비교, MIME 줄바꿈이 더하는 크기
3) URL 안전 알파벳 — '+' '/' 가 '-' '_' 로 바뀌는 바이트, 서로 다른 디코더에 넣으면
4) 패딩을 뺀 문자열 — 디코딩 실패와 복원
5) 알파벳 밖 글자 — 기본 디코더는 버리고, validate=True 는 거부한다
6) 정규 인코딩 — 패드 비트가 0 이 아닌 'Zh==' 도 b'f' 로 읽힌다
"""
import base64
import binascii
import random

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
PAD = "="
RANDOM_SEED = 20261120
RANDOM_CASES = 3000


def encode(data: bytes) -> str:
    """RFC 4648 §4: 3바이트(24비트)를 6비트 4개로 나눠 알파벳 글자로 바꾼다."""
    out = []
    for start in range(0, len(data), 3):
        chunk = data[start:start + 3]
        # 모자란 바이트는 오른쪽에 0 비트를 채워 24비트를 만든다
        group = int.from_bytes(chunk + b"\x00" * (3 - len(chunk)), "big")
        sextets = [(group >> shift) & 0x3F for shift in (18, 12, 6, 0)]
        # 1바이트면 글자 2개 + '==', 2바이트면 글자 3개 + '='
        used = len(chunk) + 1
        out.extend(ALPHABET[s] for s in sextets[:used])
        out.append(PAD * (4 - used))
    return "".join(out)


def try_decode(label, func, text):
    try:
        result = func(text)
        print(f"  {label:<40} {text!r:<14} → {result!r}")
    except (binascii.Error, ValueError) as error:
        print(f"  {label:<40} {text!r:<14} → {type(error).__name__}: {error}")


def section_compare():
    print("[1] 직접 만든 인코더 vs base64.b64encode")
    for word in ("", "f", "fo", "foo", "foob", "fooba", "foobar"):
        mine = encode(word.encode())
        std = base64.b64encode(word.encode()).decode()
        print(f"  {word!r:<10} 직접 {mine!r:<12} 표준 {std!r:<12} 같음 {mine == std}")
    rng = random.Random(RANDOM_SEED)
    mismatch = 0
    for _ in range(RANDOM_CASES):
        data = bytes(rng.randrange(256) for _ in range(rng.randrange(0, 301)))
        mismatch += encode(data) != base64.b64encode(data).decode()
    print(f"  무작위 입력 {RANDOM_CASES}개(0~300바이트) · 불일치 {mismatch}개")


def section_lengths():
    print("\n[2-1] 입력 길이별 출력 길이")
    print("  입력 | Base64 | '=' | Base32 | '=' | Base16")
    for n in range(0, 11):
        data = bytes(range(n))
        b64 = base64.b64encode(data).decode()
        b32 = base64.b32encode(data).decode()
        b16 = base64.b16encode(data).decode()
        print(f"  {n:>4} | {len(b64):>6} | {b64.count('='):>3} | {len(b32):>6} | {b32.count('='):>3} | {len(b16):>6}")

    print("\n[2-2] 3,000바이트를 인코딩한 크기")
    data = bytes(random.Random(RANDOM_SEED).randrange(256) for _ in range(3000))
    rows = [
        ("Base16 (b16encode)", base64.b16encode(data)),
        ("Base32 (b32encode)", base64.b32encode(data)),
        ("Base64 (b64encode)", base64.b64encode(data)),
        ("Base64 + 76자 줄바꿈 (encodebytes)", base64.encodebytes(data)),
    ]
    for label, encoded in rows:
        print(f"  {label:<36} {len(encoded):>5}바이트 · 원본의 {len(encoded) / len(data):.4f}배")
    lines = base64.encodebytes(data).split(b"\n")
    print(f"  encodebytes 줄 수 {len(lines) - 1} · 첫 줄 길이 {len(lines[0])} · 줄 끝 바이트 {base64.encodebytes(data)[76:77]!r}")


def section_urlsafe():
    print("\n[3] URL 안전 알파벳 (RFC 4648 §5)")
    data = bytes([0xFB, 0xFF, 0xBF])
    std = base64.b64encode(data).decode()
    url = base64.urlsafe_b64encode(data).decode()
    print(f"  바이트 {data.hex(' ')}  표준 {std!r}  URL 안전 {url!r}")
    try_decode("b64decode (표준 디코더)", base64.b64decode, url)
    try_decode("b64decode(validate=True)", lambda t: base64.b64decode(t, validate=True), url)
    try_decode("urlsafe_b64decode (URL 안전 디코더)", base64.urlsafe_b64decode, url)
    try_decode("urlsafe_b64decode 에 표준 문자열", base64.urlsafe_b64decode, std)


def section_padding():
    print("\n[4] 패딩을 뺀 문자열 (RFC 4648 §3.2)")
    for text in ("Zm9vYg", "Zm9vYmE", "Zm9vYmFy"):
        try_decode("b64decode", base64.b64decode, text)
    for text in ("Zm9vYg", "Zm9vYmE"):
        restored = text + PAD * (-len(text) % 4)
        try_decode("'=' 를 (-길이 % 4)개 붙여서", base64.b64decode, restored)
    try_decode("길이 % 4 == 1 은 복원 불가", base64.b64decode, "Zm9vY" + "===")


def section_non_alphabet():
    print("\n[5] 알파벳 밖 글자 (RFC 4648 §3.3)")
    for text in ("Zm9v\nYmFy", "Zm9v YmFy", "Zm9v*YmFy", "Zm=9vYmFy"):
        try_decode("b64decode", base64.b64decode, text)
        try_decode("b64decode(validate=True)", lambda t: base64.b64decode(t, validate=True), text)


def section_canonical():
    print("\n[6] 정규 인코딩 — 패드 비트 (RFC 4648 §3.5)")
    print("  (두 번째 글자 6비트 중 위 2비트가 데이터, 아래 4비트가 패드)")
    for text in ("Zg==", "Zh==", "Zi==", "Zv=="):
        sextet = ALPHABET.index(text[1])
        try_decode(f"두 번째 글자 {text[1]!r} = {sextet:06b}", base64.b64decode, text)


def main():
    section_compare()
    section_lengths()
    section_urlsafe()
    section_padding()
    section_non_alphabet()
    section_canonical()


if __name__ == "__main__":
    main()
