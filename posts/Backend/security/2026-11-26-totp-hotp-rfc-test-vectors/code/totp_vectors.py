"""HOTP(RFC 4226)와 TOTP(RFC 6238)를 표준 라이브러리로 구현해 RFC 시험 벡터와 대조한다.

1) RFC 4226 5.4 절의 예시 HMAC 값으로 동적 절단을 한 단계씩 따라간다
2) RFC 4226 부록 D 시험 벡터 10건
3) RFC 6238 부록 B 시험 벡터 18건 — 해시별 비밀 값 길이가 다르다
4) 부록 B 본문에 적힌 20바이트 비밀 값만 쓰면 SHA-256·SHA-512 가 어긋난다
5) 31비트를 10^6 으로 나눈 나머지의 치우침을 정확히 센다
6) 허용 창을 넓히면 한 시점에 통과하는 코드가 몇 개가 되는가
7) 추측 공격 모의 실험 — 4자리 코드로 줄여 식과 맞춰 본다
8) 시계가 늦은 기기와 같은 코드의 재사용
"""
import hashlib
import hmac
import random
import struct

RFC4226_SECRET = b"12345678901234567890"
RFC4226_VECTORS = [
    (0, "4c93cf18", 1284755224, "755224"), (1, "41397eea", 1094287082, "287082"),
    (2, "082fef30", 137359152, "359152"), (3, "66ef7655", 1726969429, "969429"),
    (4, "61c5938a", 1640338314, "338314"), (5, "33c083d4", 868254676, "254676"),
    (6, "7256c032", 1918287922, "287922"), (7, "04e5b397", 82162583, "162583"),
    (8, "2823443f", 673399871, "399871"), (9, "2679dc69", 645520489, "520489"),
]

# RFC 6238 부록 A 참조 코드가 쓰는 비밀 값: "1234567890" 을 반복해 20·32·64바이트로 자른 것
RFC6238_SEEDS = {
    "sha1": (b"1234567890" * 2)[:20],
    "sha256": (b"1234567890" * 4)[:32],
    "sha512": (b"1234567890" * 7)[:64],
}
RFC6238_VECTORS = [
    (59, "94287082", "46119246", "90693936"),
    (1111111109, "07081804", "68084774", "25091201"),
    (1111111111, "14050471", "67062674", "99943326"),
    (1234567890, "89005924", "91819424", "93441116"),
    (2000000000, "69279037", "90698825", "38618901"),
    (20000000000, "65353130", "77737706", "47863826"),
]


def dynamic_truncate(mac):
    """RFC 4226 5.3: 마지막 바이트의 아래 4비트를 오프셋으로 4바이트를 꺼내 최상위 비트를 지운다."""
    offset = mac[-1] & 0x0F
    return struct.unpack(">I", mac[offset:offset + 4])[0] & 0x7FFFFFFF


def hotp(secret, counter, digits=6, algorithm="sha1"):
    mac = hmac.new(secret, struct.pack(">Q", counter), algorithm).digest()
    return str(dynamic_truncate(mac) % 10 ** digits).zfill(digits)


def totp(secret, unix_time, digits=6, algorithm="sha1", step=30, t0=0):
    return hotp(secret, (unix_time - t0) // step, digits, algorithm)


def verify(secret, code, unix_time, window, last_used_step=None, step=30):
    """현재 스텝 기준 앞뒤 window 스텝을 본다. 맞은 스텝 번호를 돌려주고, 없으면 None.

    last_used_step 이하의 스텝은 받지 않는다 (RFC 6238 5.2: 같은 OTP 의 두 번째 시도 거부).
    """
    current = unix_time // step
    for delta in sorted(range(-window, window + 1), key=abs):
        candidate = current + delta
        if last_used_step is not None and candidate <= last_used_step:
            continue
        if hmac.compare_digest(hotp(secret, candidate), code):
            return candidate
    return None


def main():
    print("[1] RFC 4226 5.4 절 예시 — 동적 절단")
    example = bytes.fromhex("1f8698690e02ca16618550ef7f19da8e945b555a")
    offset = example[-1] & 0x0F
    chunk = example[offset:offset + 4]
    value = dynamic_truncate(example)
    print(f"    HMAC 20바이트      {example.hex()}")
    print(f"    마지막 바이트      0x{example[-1]:02x} -> 아래 4비트 = 오프셋 {offset}")
    print(f"    바이트 {offset}~{offset + 3}      0x{chunk.hex()}")
    print(f"    최상위 비트 제거   {value}")
    print(f"    mod 10^6           {value % 10 ** 6:06d}   (RFC: 872921)")

    print("\n[2] RFC 4226 부록 D — 비밀 값 '12345678901234567890', 6자리")
    print("    ", ("count", "truncated_hex", "truncated_dec", "hotp", "rfc", "match"))
    matched = 0
    for counter, rfc_hex, rfc_dec, rfc_code in RFC4226_VECTORS:
        mac = hmac.new(RFC4226_SECRET, struct.pack(">Q", counter), "sha1").digest()
        truncated = dynamic_truncate(mac)
        code = hotp(RFC4226_SECRET, counter)
        ok = (f"{truncated:08x}", truncated, code) == (rfc_hex, rfc_dec, rfc_code)
        matched += ok
        print("    ", (counter, f"{truncated:08x}", truncated, code, rfc_code, ok))
    print(f"     일치 {matched}/{len(RFC4226_VECTORS)}")

    print("\n[3] RFC 6238 부록 B — 8자리, 스텝 30초, T0 = 0")
    print("    ", ("unix_time", "T_hex", "mode", "totp", "rfc", "match"))
    matched = 0
    for unix_time, *expected in RFC6238_VECTORS:
        for algorithm, rfc_code in zip(("sha1", "sha256", "sha512"), expected):
            code = totp(RFC6238_SEEDS[algorithm], unix_time, 8, algorithm)
            matched += code == rfc_code
            print("    ", (unix_time, f"{unix_time // 30:016X}", algorithm, code, rfc_code,
                           code == rfc_code))
    print(f"     일치 {matched}/{len(RFC6238_VECTORS) * 3}")

    print("\n[4] 본문에 적힌 20바이트 비밀 값을 세 해시에 그대로 쓰면")
    print("    ", ("mode", "match_with_20_byte_secret"))
    for index, algorithm in enumerate(("sha1", "sha256", "sha512")):
        hits = sum(totp(RFC4226_SECRET, row[0], 8, algorithm) == row[1 + index]
                   for row in RFC6238_VECTORS)
        print("    ", (algorithm, f"{hits}/{len(RFC6238_VECTORS)}"))

    print("\n[5] 31비트 값을 10^6 으로 나눈 나머지 — 코드마다 원상이 몇 개인가")
    quotient, remainder = divmod(2 ** 31, 10 ** 6)
    print(f"     2^31 = {2 ** 31} = {quotient} x 10^6 + {remainder}")
    print(f"     코드 000000~{remainder - 1:06d}: {quotient + 1}개,  "
          f"코드 {remainder:06d}~999999: {quotient}개")
    print(f"     확률 비  {(quotient + 1) / quotient:.6f}")
    print(f"     가장 흔한 코드의 확률 x 10^6 = {(quotient + 1) / 2 ** 31 * 10 ** 6:.8f}")

    print("\n[6] 허용 창 ±w 스텝 — 한 시점에 통과하는 서로 다른 6자리 코드 수")
    rng = random.Random(20261126)
    secrets = [rng.randbytes(20) for _ in range(2000)]
    now_step = 1795687200 // 30
    print("    ", ("window", "codes_checked", "mean_distinct", "guess_prob_x_1e6",
                   "valid_seconds"))
    for window in (0, 1, 2, 5, 10):
        distinct = [len({hotp(secret, now_step + d) for d in range(-window, window + 1)})
                    for secret in secrets]
        mean = sum(distinct) / len(distinct)
        print("    ", (window, 2 * window + 1, round(mean, 4), round(mean, 4),
                       30 * (2 * window + 1)))

    print("\n[7] 추측 공격 모의 실험 — 4자리 코드, 시도 5회 뒤 잠금, 계정 40,000개")
    print("    ", ("window", "accepted", "simulated", "formula_1-(1-a/10^4)^5", "sv/10^Digit"))
    trials, attempts, digits = 40000, 5, 4
    for window in (0, 1, 2, 5):
        accepted = 2 * window + 1
        broken = 0
        for _ in range(trials):
            secret = rng.randbytes(20)
            valid = {hotp(secret, now_step + d, digits) for d in range(-window, window + 1)}
            guesses = rng.sample(range(10 ** digits), attempts)
            broken += any(f"{guess:0{digits}d}" in valid for guess in guesses)
        formula = 1 - (1 - accepted / 10 ** digits) ** attempts
        print("    ", (window, accepted, round(broken / trials, 5), round(formula, 5),
                       round(accepted * attempts / 10 ** digits, 5)))

    print("\n[8] 시계가 40초 늦은 기기와 재사용")
    secret = RFC4226_SECRET
    server_time = 1795687215
    device_code = totp(secret, server_time - 40)
    server_step = server_time // 30
    for window in (0, 1):
        step = verify(secret, device_code, server_time, window)
        offset = None if step is None else step - server_step
        print(f"     창 ±{window}: 맞은 스텝 = {step}, 서버 스텝과의 차 = {offset}")
    first = verify(secret, device_code, server_time, 1)
    again = verify(secret, device_code, server_time + 5, 1)
    guarded = verify(secret, device_code, server_time + 5, 1, last_used_step=first)
    print(f"     같은 코드를 5초 뒤 다시 제출 — 기록 없음: {again}, 마지막 스텝 기록: {guarded}")


if __name__ == "__main__":
    main()
