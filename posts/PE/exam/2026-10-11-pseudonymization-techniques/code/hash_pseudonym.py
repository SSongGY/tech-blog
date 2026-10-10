"""가명처리 기법 중 '대체' 계열 4가지가 무엇을 막고 무엇을 못 막는지 확인한다.

[1] 키 없는 해시 — 식별자 값의 범위가 좁으면 전부 해시해 보고 되돌릴 수 있다
[2] 키 있는 해시(HMAC) — 키 없이 같은 열거를 하면 하나도 못 되돌린다
[3] 제공처별 키 — 같은 키를 쓰면 두 가명정보가 가명만으로 결합된다
[4] 토큰화 — 매핑표(추가정보) 없이는 토큰과 원래 값이 연결되지 않는다

전화번호는 전부 가상이다. 재현을 위해 키와 난수 시드를 고정했다.
실제 처리에서는 키를 secrets 로 만들고 가명정보와 분리해 보관한다.
"""
import hashlib
import hmac
import platform
import random
import time

# 공격자가 "010-00xx-xxxx 대역"이라는 것만 안다고 가정한다. 후보 10^6개.
PREFIX = "010-00"
CANDIDATE_COUNT = 1_000_000
FULL_SPACE = 100_000_000  # 010-xxxx-xxxx 전체

SUBJECTS = [
    ("가상1", "010-0012-3456"),
    ("가상2", "010-0047-0001"),
    ("가상3", "010-0063-9182"),
    ("가상4", "010-0080-5500"),
    ("가상5", "010-0099-2718"),
]


def candidate(i):
    digits = f"{i:06d}"
    return f"{PREFIX}{digits[:2]}-{digits[2:]}"


def sha256_hex(value):
    return hashlib.sha256(value.encode()).hexdigest()


def hmac_hex(key, value):
    return hmac.new(key, value.encode(), hashlib.sha256).hexdigest()


def enumerate_attack(pseudonyms, pseudonymize):
    """후보를 전부 가명처리해 보고 일치하는 것을 되찾는다."""
    targets = set(pseudonyms)
    recovered = {}
    started = time.perf_counter()
    for i in range(CANDIDATE_COUNT):
        phone = candidate(i)
        p = pseudonymize(phone)
        if p in targets:
            recovered[p] = phone
    elapsed = time.perf_counter() - started
    return recovered, elapsed


def main():
    print(f"Python {platform.python_version()}")
    print(f"가상 대상자 {len(SUBJECTS)}명, 공격자 후보 {CANDIDATE_COUNT:,}개 ({PREFIX}xx-xxxx)")
    print()

    print("[1] 키 없는 해시(SHA-256)")
    released = [sha256_hex(phone) for _, phone in SUBJECTS]
    for (name, _), p in zip(SUBJECTS, released):
        print(f"  {name}  {p[:16]}...")
    recovered, elapsed = enumerate_attack(released, sha256_hex)
    print(f"  되찾은 수: {len(recovered)}/{len(SUBJECTS)}  소요 {elapsed:.2f}초")
    for p in released:
        print(f"    {p[:16]}... -> {recovered.get(p, '못 찾음')}")
    rate = CANDIDATE_COUNT / elapsed
    print(f"  측정 속도 {rate:,.0f}건/초 -> 010 전체 {FULL_SPACE:,}개 환산 {FULL_SPACE / rate / 60:.1f}분 (단일 스레드)")
    print()

    print("[2] 키 있는 해시(HMAC-SHA256), 공격자는 키를 모른다")
    secret_key = b"fixed-key-for-reproducibility-01"
    released = [hmac_hex(secret_key, phone) for _, phone in SUBJECTS]
    attacker_key = b"attacker-guess-key"
    recovered, elapsed = enumerate_attack(released, lambda v: hmac_hex(attacker_key, v))
    print(f"  되찾은 수: {len(recovered)}/{len(SUBJECTS)}  소요 {elapsed:.2f}초")
    recovered, _ = enumerate_attack(released, lambda v: hmac_hex(secret_key, v))
    print(f"  (키가 새면) 되찾은 수: {len(recovered)}/{len(SUBJECTS)}")
    print()

    print("[3] 두 제공처 A·B 가 각자 받은 가명정보를 가명으로 결합해 본다")
    in_a = SUBJECTS[:4]
    in_b = SUBJECTS[1:]
    key_a = b"recipient-A-key-0000000000000000"
    key_b = b"recipient-B-key-0000000000000000"
    for label, ka, kb in (("같은 키", secret_key, secret_key), ("제공처별 키", key_a, key_b)):
        set_a = {hmac_hex(ka, phone) for _, phone in in_a}
        set_b = {hmac_hex(kb, phone) for _, phone in in_b}
        print(f"  {label:6}  A {len(set_a)}명, B {len(set_b)}명 -> 가명 일치 {len(set_a & set_b)}명")
    print()

    print("[4] 토큰화 — 난수 토큰과 매핑표")
    rng = random.Random(20261011)
    mapping = {}
    for name, phone in SUBJECTS:
        mapping[phone] = f"T{rng.randrange(10**8):08d}"
    for name, phone in SUBJECTS:
        print(f"  {name}  {mapping[phone]}")
    # 토큰은 원래 값의 함수가 아니다. 같은 번호도 발급을 다시 하면 다른 토큰이 나온다
    rng_again = random.Random(20261012)
    again = f"T{rng_again.randrange(10**8):08d}"
    print(f"  가상1 을 다시 발급하면 {again} (처음 {mapping[SUBJECTS[0][1]]})")
    reverse = {token: phone for phone, token in mapping.items()}
    token = mapping[SUBJECTS[2][1]]
    print(f"  매핑표가 있으면 {token} -> {reverse[token]}")


if __name__ == "__main__":
    main()
