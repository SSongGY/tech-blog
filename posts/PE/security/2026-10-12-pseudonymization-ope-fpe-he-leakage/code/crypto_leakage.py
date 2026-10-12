"""가명처리용 암호 기법 3종이 분석에 남기는 것과 새는 것을 확인한다.

외부 의존성 없이 표준 라이브러리만 쓴다. 키·난수 시드를 고정해 매번 같은 결과가 나온다.
여기 있는 구현은 전부 성질을 보이기 위한 학습용이다. 실제 가명처리에는 검증된 구현을 쓴다.
환자·카드번호·급여 데이터는 전부 지어낸 것이다.
"""

import hashlib
import hmac
import math
import random
import statistics
import sys

AGE_DOMAIN = list(range(100))  # 평문 공간: 나이 0~99
CIPHER_SPACE = 2 ** 16         # 암호문 공간: 0~65535


# ---------------------------------------------------------------------------
# 순서보존 암호 (OPE)
# Boldyreva 등(2009)의 이상적 OPE는 평문 공간에서 암호문 공간으로 가는
# "무작위 순서보존 함수"다. 암호문 공간에서 평문 개수만큼 무작위로 뽑아 정렬하면 그것이 된다.
# ---------------------------------------------------------------------------
def make_ope_table(key):
    rng = random.Random(key)
    points = sorted(rng.sample(range(CIPHER_SPACE), len(AGE_DOMAIN)))
    return dict(zip(AGE_DOMAIN, points))


def sorting_attack(ciphertexts):
    """Naveed 등(2015) 6.1절. 보조 정보 없이 정렬 순위만으로 평문을 대응시킨다."""
    ranked = sorted(set(ciphertexts))
    return {c: AGE_DOMAIN[i] for i, c in enumerate(ranked)}


def section_ope():
    print("[1] 순서보존 암호 — 비교는 되지만 순서가 그대로 새어 나간다")
    table = make_ope_table(key="ope-key-A")
    print(f"    평문 공간 {len(AGE_DOMAIN)}개(나이 0~99) -> 암호문 공간 {CIPHER_SPACE}개")
    print("    앞 5개 대응:", ", ".join(f"{a}->{table[a]}" for a in AGE_DOMAIN[:5]))

    rng = random.Random(7)
    # 조밀한 열: 나이 0~99가 한 번 이상씩 모두 나온다 (병원 환자 1,000명)
    dense_ages = AGE_DOMAIN + [rng.randint(0, 99) for _ in range(900)]
    rng.shuffle(dense_ages)
    dense_cipher = [table[a] for a in dense_ages]

    over_60 = sum(1 for c in dense_cipher if c >= table[60])
    print(f"    서버가 키 없이 '나이 >= 60' 범위 질의 수행: {over_60}건 "
          f"(평문으로 센 값 {sum(1 for a in dense_ages if a >= 60)}건)")

    guess = sorting_attack(dense_cipher)
    hit = sum(1 for a, c in zip(dense_ages, dense_cipher) if guess[c] == a)
    print(f"    조밀한 열(1,000행, 서로 다른 값 {len(set(dense_ages))}개) 정렬 공격: "
          f"{hit}/{len(dense_ages)}행 복원")

    # 희소한 열: 30명만 있어 나이 공간의 일부만 나온다
    sparse_ages = [rng.randint(20, 60) for _ in range(30)]
    sparse_cipher = [table[a] for a in sparse_ages]
    guess = sorting_attack(sparse_cipher)
    hit = sum(1 for a, c in zip(sparse_ages, sparse_cipher) if guess[c] == a)
    print(f"    희소한 열(30행, 서로 다른 값 {len(set(sparse_ages))}개) 정렬 공격: "
          f"{hit}/{len(sparse_ages)}행 복원")

    # 희소해도 암호문 값의 위치가 평문의 대략적 위치를 드러낸다
    errors = []
    for a, c in zip(sparse_ages, sparse_cipher):
        estimate = round(c / CIPHER_SPACE * len(AGE_DOMAIN))
        errors.append(abs(estimate - a))
    within = sum(1 for e in errors if e <= math.isqrt(len(AGE_DOMAIN)))
    print(f"    같은 30행을 '암호문/65536*100'으로 어림: 평균 오차 "
          f"{statistics.mean(errors):.1f}세, 최대 {max(errors)}세, "
          f"오차 {math.isqrt(len(AGE_DOMAIN))}세 이내 {within}/30행")

    other = make_ope_table(key="ope-key-B")
    print(f"    키를 바꾸면 나이 40의 암호문: {table[40]} -> {other[40]} "
          "(값은 달라도 순서는 같다)")
    print()


# ---------------------------------------------------------------------------
# 형태보존 암호 (FPE)
# NIST SP 800-38G FF1의 뼈대(숫자열을 반으로 나눠 라운드마다 한쪽에 의사난수를 더함)만
# 흉내 낸 학습용 Feistel이다. 라운드 함수에 AES 대신 HMAC-SHA256을 썼다. 표준 FF1이 아니다.
# ---------------------------------------------------------------------------
ROUNDS = 10


def _round_value(key, round_no, half, width):
    digest = hmac.new(key, f"{round_no}|{half}".encode(), hashlib.sha256).digest()
    return int.from_bytes(digest, "big") % (10 ** width)


def fpe_encrypt(key, digits):
    u = len(digits) // 2
    a, b = digits[:u], digits[u:]
    for i in range(ROUNDS):
        width = len(a)
        c = (int(a) + _round_value(key, i, b, width)) % (10 ** width)
        a, b = b, str(c).zfill(width)
    return a + b


def fpe_decrypt(key, digits):
    u = len(digits) // 2
    # 마지막 라운드 뒤 두 반쪽의 길이: ROUNDS가 짝수면 처음과 같다
    a, b = digits[:u], digits[u:]
    for i in reversed(range(ROUNDS)):
        width = len(b)
        c = (int(b) - _round_value(key, i, a, width)) % (10 ** width)
        a, b = str(c).zfill(width), a
    return a + b


def section_fpe():
    print("[2] 형태보존 암호 — 자리 수와 문자 종류가 그대로라 스키마를 안 바꾼다")
    key = b"fpe-key-A"
    cards = ["9410123412341234", "9410987698769876", "9410123412341234"]
    for card in cards:
        enc = fpe_encrypt(key, card)
        dec = fpe_decrypt(key, enc)
        print(f"    {card} -> {enc}  (길이 {len(enc)}, 숫자만: {enc.isdigit()}, "
              f"복호 일치: {dec == card})")
    same = fpe_encrypt(key, cards[0]) == fpe_encrypt(key, cards[2])
    print(f"    같은 카드번호의 암호문이 같은가: {same} -> 같은 값끼리 묶이고 빈도가 보인다")
    print(f"    VARCHAR(16) 컬럼에 그대로 들어가는가: {len(fpe_encrypt(key, cards[0])) <= 16}")

    small = sorted({fpe_encrypt(key, f"{n:02d}") for n in range(100)})
    print(f"    두 자리 값(00~99)을 전부 암호화한 서로 다른 암호문 수: {len(small)}개 "
          "-> 정의역이 작으면 100개 대응표로 전부 풀린다")
    print()


# ---------------------------------------------------------------------------
# 동형 암호 (Paillier, ISO/IEC 18033-6이 정한 두 방식 중 하나)
# 덧셈 동형: E(a)·E(b) mod n² 을 복호하면 a+b
# 소수는 학습용으로 작게 잡았다(메르센 소수 2^61-1, 2^31-1).
# ---------------------------------------------------------------------------
P, Q = 2 ** 61 - 1, 2 ** 31 - 1
N = P * Q
N2 = N * N
G = N + 1
LAM = math.lcm(P - 1, Q - 1)
MU = pow((pow(G, LAM, N2) - 1) // N, -1, N)


def he_encrypt(m, rng):
    while True:
        r = rng.randrange(1, N)
        if math.gcd(r, N) == 1:
            break
    return (pow(G, m, N2) * pow(r, N, N2)) % N2


def he_decrypt(c):
    return ((pow(c, LAM, N2) - 1) // N * MU) % N


def section_he():
    print("[3] 동형 암호(Paillier) — 암호문 상태로 더하지만 비교·정렬은 못 한다")
    rng = random.Random(11)
    salaries = {"가": 320, "나": 410, "다": 290, "라": 505, "마": 380}  # 단위: 만원
    enc = {k: he_encrypt(v, rng) for k, v in salaries.items()}

    total_cipher = 1
    for c in enc.values():
        total_cipher = (total_cipher * c) % N2
    print(f"    급여 5건을 암호문끼리 곱함 -> 복호: {he_decrypt(total_cipher)}"
          f" (평문 합계 {sum(salaries.values())})")
    print(f"    '가'의 암호문을 3제곱 -> 복호: {he_decrypt(pow(enc['가'], 3, N2))}"
          f" (320 x 3 = {320 * 3})")

    c1, c2 = he_encrypt(320, rng), he_encrypt(320, rng)
    print(f"    같은 320을 두 번 암호화한 암호문이 같은가: {c1 == c2} "
          "-> 같은 값끼리 묶이지 않는다")
    bigger = enc["라"] > enc["가"]
    print(f"    암호문 크기 비교 E(505) > E(320): {bigger} "
          "-> 암호문의 대소는 평문의 대소와 무관하다")
    print(f"    평문 {salaries['가'].bit_length()}비트 -> 암호문 약 {enc['가'].bit_length()}비트"
          f" (n² = {N2.bit_length()}비트)")
    print()


def main():
    print(f"Python {sys.version.split()[0]}")
    print()
    section_ope()
    section_fpe()
    section_he()


if __name__ == "__main__":
    main()
