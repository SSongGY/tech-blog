"""RFC 8017 의 RSA 기본 연산을 작은 수와 2048비트 수로 직접 계산해 검산한다.

학습용이다. 난수는 재현을 위해 시드를 고정한 random.Random 을 쓰므로 실제 키 생성에 쓰면 안 된다.

1) 작은 소수로 키 생성 — φ(n) 으로 구한 d 와 λ(n) 으로 구한 d
2) RSAEP·RSADP — 두 d 가 모두 복호하는가
3) CRT 복호 — RFC 8017 §5.1.2 단계 2b 를 그대로
4) 서명 RSASP1·검증 RSAVP1
5) 범위 검사가 없으면 — m 과 m + n 이 같은 암호문
6) 교과서 RSA 의 성질 — 결정적, 곱셈 동형
7) 2048비트 키 — CRT 로 빨라지는 정도, e=3 에서 패딩 없는 짧은 메시지
"""
import math
import random
import time

SEED = 20261115


def modinv(a, m):
    return pow(a, -1, m)


def is_probable_prime(n, rng, rounds=40):
    if n < 2:
        return False
    for small in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % small == 0:
            return n == small
    d, s = n - 1, 0
    while d % 2 == 0:
        d, s = d // 2, s + 1
    for _ in range(rounds):
        a = rng.randrange(2, n - 1)
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def random_prime(bits, rng, e):
    while True:
        # 최상위 두 비트를 세워 p*q 가 정확히 2*bits 비트가 되게 한다
        candidate = rng.getrandbits(bits) | (0b11 << (bits - 2)) | 1
        if math.gcd(candidate - 1, e) == 1 and is_probable_prime(candidate, rng):
            return candidate


def crt_decrypt(c, p, q, d_p, d_q, q_inv):
    m_1 = pow(c, d_p, p)
    m_2 = pow(c, d_q, q)
    h = (m_1 - m_2) * q_inv % p
    return m_2 + q * h, (m_1, m_2, h)


def integer_cube_root(x):
    lo, hi = 0, 1 << (x.bit_length() // 3 + 2)
    while lo < hi:
        mid = (lo + hi) // 2
        if mid ** 3 < x:
            lo = mid + 1
        else:
            hi = mid
    return lo


def small_example():
    p, q, e = 61, 53, 17
    n = p * q
    phi = (p - 1) * (q - 1)
    lam = math.lcm(p - 1, q - 1)
    d_phi = modinv(e, phi)
    d_lam = modinv(e, lam)
    print("[1] 키 생성 p=61, q=53, e=17")
    print(f"  n = {n}, φ(n) = {phi}, λ(n) = lcm({p - 1}, {q - 1}) = {lam}")
    print(f"  gcd(e, λ(n)) = {math.gcd(e, lam)}")
    print(f"  d (φ 기준) = {d_phi}   e*d mod φ = {e * d_phi % phi}")
    print(f"  d (λ 기준) = {d_lam}    e*d mod λ = {e * d_lam % lam}")
    print(f"  d_φ - d_λ = {d_phi - d_lam} = {(d_phi - d_lam) // lam} × λ(n)")
    print()

    m = 65
    c = pow(m, e, n)
    print(f"[2] RSAEP m={m} -> c = m^e mod n = {c}")
    print(f"  RSADP d_φ: c^{d_phi} mod n = {pow(c, d_phi, n)}")
    print(f"  RSADP d_λ: c^{d_lam} mod n = {pow(c, d_lam, n)}")
    every_m_ok = all(pow(pow(x, e, n), d_lam, n) == x for x in range(n))
    print(f"  0..n-1 전부 d_λ 로 복호되는가: {every_m_ok}")
    print()

    d_p, d_q, q_inv = d_lam % (p - 1), d_lam % (q - 1), modinv(q, p)
    recovered, (m_1, m_2, h) = crt_decrypt(c, p, q, d_p, d_q, q_inv)
    print("[3] CRT 복호 (RFC 8017 §5.1.2 단계 2b)")
    print(f"  dP = d mod (p-1) = {d_p}, dQ = d mod (q-1) = {d_q}, qInv = q^-1 mod p = {q_inv}")
    print(f"  m_1 = c^dP mod p = {m_1}, m_2 = c^dQ mod q = {m_2}")
    print(f"  h = (m_1 - m_2) * qInv mod p = {h}")
    print(f"  m = m_2 + q*h = {recovered}")
    print()

    digest = 123
    s = pow(digest, d_lam, n)
    print(f"[4] 서명 RSASP1 s = {digest}^d mod n = {s}")
    print(f"  검증 RSAVP1 s^e mod n = {pow(s, e, n)}  (위조 s+1 -> {pow(s + 1, e, n)})")
    print()

    big = m + n
    print("[5] 범위 검사가 없으면")
    print(f"  m={m} 의 암호문 {pow(m, e, n)}, m+n={big} 의 암호문 {pow(big, e, n)}")
    print(f"  {big} 을 복호하면 {pow(pow(big, e, n), d_lam, n)}")
    print()

    print("[6] 교과서 RSA 의 성질")
    print(f"  같은 m=65 를 두 번 암호화: {pow(65, e, n)}, {pow(65, e, n)}")
    answers = {pow(x, e, n): x for x in (0, 1)}  # 예/아니오를 0/1 로 보냈다면
    intercepted = pow(1, e, n)
    print(f"  0 과 1 의 암호문: {pow(0, e, n)}, {pow(1, e, n)} -> 가로챈 {intercepted} 는 {answers[intercepted]}")
    m_a, m_b = 7, 9
    product_cipher = pow(m_a, e, n) * pow(m_b, e, n) % n
    print(f"  E({m_a})*E({m_b}) mod n = {product_cipher}, E({m_a * m_b}) = {pow(m_a * m_b, e, n)}")
    print(f"  개인키 없이 만든 그 암호문을 복호하면 {pow(product_cipher, d_lam, n)}")
    print()


def large_example():
    rng = random.Random(SEED)
    e = 65537
    p = random_prime(1024, rng, e)
    q = random_prime(1024, rng, e)
    n = p * q
    lam = math.lcm(p - 1, q - 1)
    d = modinv(e, lam)
    d_p, d_q, q_inv = d % (p - 1), d % (q - 1), modinv(q, p)
    print("[7-A] 2048비트 키 (e=65537, 시드 고정 의사난수 — 학습용)")
    print(f"  n 비트 수 = {n.bit_length()}, d 비트 수 = {d.bit_length()}")
    print(f"  p 비트 수 = {p.bit_length()}, q 비트 수 = {q.bit_length()}")

    m = rng.randrange(2, n - 1)
    c = pow(m, e, n)
    repeat = 30
    start = time.perf_counter()
    for _ in range(repeat):
        plain = pow(c, d, n)
    full_ms = (time.perf_counter() - start) / repeat * 1000
    start = time.perf_counter()
    for _ in range(repeat):
        plain_crt, _ = crt_decrypt(c, p, q, d_p, d_q, q_inv)
    crt_ms = (time.perf_counter() - start) / repeat * 1000
    start = time.perf_counter()
    for _ in range(repeat):
        pow(m, e, n)
    enc_ms = (time.perf_counter() - start) / repeat * 1000
    print(f"  복호 결과 일치: c^d={plain == m}, CRT={plain_crt == m}")
    print(f"  {repeat}회 평균  암호화(e=65537) {enc_ms:.3f} ms · 복호 c^d {full_ms:.2f} ms · CRT {crt_ms:.2f} ms")
    print(f"  CRT 대비 배율 {full_ms / crt_ms:.1f}배, 복호/암호화 {full_ms / enc_ms:.0f}배")
    print()

    # e=3 이고 패딩이 없으면, 짧은 메시지는 m^3 < n 이라 mod 가 일어나지 않는다
    e_small = 3
    p3 = random_prime(1024, rng, e_small)
    q3 = random_prime(1024, rng, e_small)
    n3 = p3 * q3
    secret_key = rng.getrandbits(128)  # AES-128 키를 그대로 m 으로 보냈다고 하자
    c3 = pow(secret_key, e_small, n3)
    root = integer_cube_root(c3)
    print("[7-B] e=3, 패딩 없이 128비트 키를 보내면")
    print(f"  m^3 비트 수 = {(secret_key ** 3).bit_length()} < n 비트 수 {n3.bit_length()}")
    print(f"  c 의 정수 세제곱근 == m : {root == secret_key}")
    print(f"  개인키 없이 되찾은 m 의 앞 16자리: {str(root)[:16]}…")


if __name__ == "__main__":
    small_example()
    large_example()
