"""타원곡선 암호를 작은 소수체에서 손으로 계산해 검산한다.

학습용이다. 곡선이 19개 점뿐이라 전수 조사로 바로 깨진다.
실제 키는 검증된 암호 라이브러리로 만든다.
"""

import hashlib
import platform
import sys

# 무한원점(항등원)을 None 으로 둔다. 좌표로 표현할 수 없는 점이기 때문이다.
INFINITY = None


def show(point):
    return "O(무한원점)" if point is INFINITY else str(point)


class Curve:
    """짧은 바이어슈트라스 형 y^2 = x^3 + ax + b (mod p)."""

    def __init__(self, p, a, b):
        if (4 * a**3 + 27 * b**2) % p == 0:
            raise ValueError("4a^3 + 27b^2 = 0 이면 특이 곡선이라 군이 되지 않는다")
        self.p, self.a, self.b = p, a, b

    def contains(self, point):
        if point is INFINITY:
            return True
        x, y = point
        return (y * y - (x**3 + self.a * x + self.b)) % self.p == 0

    def negate(self, point):
        if point is INFINITY:
            return INFINITY
        x, y = point
        return (x, (-y) % self.p)

    def add(self, p1, p2, trace=False):
        if p1 is INFINITY:
            return p2
        if p2 is INFINITY:
            return p1
        x1, y1 = p1
        x2, y2 = p2
        if x1 == x2 and (y1 + y2) % self.p == 0:
            # P + (-P): 세로 직선이 셋째 점을 만나지 않으므로 무한원점이 된다
            return INFINITY
        if p1 == p2:
            slope = (3 * x1 * x1 + self.a) * pow(2 * y1, -1, self.p) % self.p
            kind = "접선"
        else:
            slope = (y2 - y1) * pow(x2 - x1, -1, self.p) % self.p
            kind = "현"
        x3 = (slope * slope - x1 - x2) % self.p
        y3 = (slope * (x1 - x3) - y1) % self.p
        if trace:
            print(f"    {p1} + {p2}: {kind} 기울기 λ={slope}, x3={x3}, y3={y3}")
        return (x3, y3)

    def multiply(self, k, point, trace=False):
        """왼쪽 비트부터 보는 double-and-add."""
        bits = bin(k)[2:]
        # 맨 앞 비트는 항상 1 이므로 G 에서 출발한다. 0 을 두 배 하는 헛연산을 세지 않기 위해서다
        result, doubles, adds = point, 0, 0
        if trace:
            print(f"    비트 1 → 시작 G = {show(result)}")
        for bit in bits[1:]:
            result = self.add(result, result)
            doubles += 1
            step = "배가"
            if bit == "1":
                result = self.add(result, point)
                adds += 1
                step = "배가 후 +G"
            if trace:
                print(f"    비트 {bit} → {step:<8} {show(result)}")
        if trace:
            print(f"    연산 횟수: 배가 {doubles}번 + 더하기 {adds}번 = {doubles + adds}번 (G 를 반복해 더하면 {k - 1}번)")
        return result

    def points(self):
        found = [INFINITY]
        for x in range(self.p):
            for y in range(self.p):
                if self.contains((x, y)):
                    found.append((x, y))
        return found


def point_order(curve, point):
    order, current = 1, point
    while current is not INFINITY:
        current = curve.add(current, point)
        order += 1
    return order


def hash_to_int(message, n):
    # FIPS 186-5 §6.4.1: 해시의 왼쪽 min(N, hashlen) 비트를 정수로 쓴다
    digest = int.from_bytes(hashlib.sha256(message).digest(), "big")
    return digest >> (256 - n.bit_length())


def ecdsa_sign(curve, g, n, d, message, k):
    e = hash_to_int(message, n)
    r = curve.multiply(k, g)[0] % n
    s = pow(k, -1, n) * (e + r * d) % n
    if r == 0 or s == 0:
        raise ValueError("r 또는 s 가 0 이면 k 를 새로 고른다")
    return e, r, s


def ecdsa_verify(curve, g, n, q, message, r, s):
    if not (1 <= r < n and 1 <= s < n):
        return False
    e = hash_to_int(message, n)
    w = pow(s, -1, n)
    u1, u2 = e * w % n, r * w % n
    point = curve.add(curve.multiply(u1, g), curve.multiply(u2, q))
    return point is not INFINITY and point[0] % n == r


def main():
    print(f"[환경] Python {platform.python_version()} ({sys.platform})")

    print("\n[1] 곡선 E: y^2 = x^3 + 2x + 2 (mod 17)")
    curve = Curve(17, 2, 2)
    every_point = curve.points()
    print(f"    판별식 4a^3+27b^2 mod p = {(4 * 8 + 27 * 4) % 17} (0 이 아니다)")
    print(f"    점 개수 #E = {len(every_point)} (무한원점 포함)")
    trace_t = 17 + 1 - len(every_point)
    print(f"    t = p+1-#E = {trace_t}, |t| <= 2*sqrt(p) = {2 * 17**0.5:.2f} → {abs(trace_t) <= 2 * 17**0.5}")

    g = (5, 1)
    n = point_order(curve, g)
    print(f"    기점 G = {g}, 위수 n = {n}, 보조인수 h = #E/n = {len(every_point) // n}")

    print("\n[2] 점 덧셈 — 현과 접선")
    two_g = curve.add(g, g, trace=True)
    three_g = curve.add(two_g, g, trace=True)
    print(f"    2G = {two_g}, 3G = {three_g}, 둘 다 곡선 위: {curve.contains(two_g) and curve.contains(three_g)}")
    print(f"    G + (-G) = {show(curve.add(g, curve.negate(g)))}  (-G = {curve.negate(g)})")

    print("\n[3] G 의 배수 1G..19G")
    multiples = [curve.multiply(i, g) for i in range(1, n + 1)]
    for i in range(0, n, 5):
        print("    " + "  ".join(f"{j + 1}G={show(multiples[j])}" for j in range(i, min(i + 5, n))))

    print("\n[4] 스칼라 곱 13G 를 double-and-add 로 (13 = 0b1101)")
    curve.multiply(13, g, trace=True)

    print("\n[5] ECDH 키 합의")
    d_a, d_b = 3, 7
    q_a, q_b = curve.multiply(d_a, g), curve.multiply(d_b, g)
    z_a, z_b = curve.multiply(d_a, q_b), curve.multiply(d_b, q_a)
    print(f"    A: d_A={d_a}, Q_A={q_a}  /  B: d_B={d_b}, Q_B={q_b}")
    print(f"    A 가 계산 d_A*Q_B = {z_a},  B 가 계산 d_B*Q_A = {z_b}")
    print(f"    공유 비밀 Z (x 좌표) = {z_a[0]}, 일치: {z_a == z_b}, 21G = {curve.multiply(21 % n, g)}")

    print("\n[6] ECDSA 서명과 검증")
    d = 7
    q = curve.multiply(d, g)
    message = b"transfer 100"
    e, r, s = ecdsa_sign(curve, g, n, d, message, k=10)
    print(f"    개인키 d={d}, 공개키 Q={q}, k=10, kG={curve.multiply(10, g)}")
    print(f"    e = SHA-256 왼쪽 {n.bit_length()}비트 = {e} (n 보다 클 수 있다. 식 안에서 mod n 으로 줄어든다)")
    print(f"    서명 (r, s) = ({r}, {s})")
    print(f"    검증: {ecdsa_verify(curve, g, n, q, message, r, s)}")
    print(f"    메시지 변조(b'transfer 900') 검증: {ecdsa_verify(curve, g, n, q, b'transfer 900', r, s)}")
    print(f"    s 변조(s+1) 검증: {ecdsa_verify(curve, g, n, q, message, r, (s + 1) % n)}")

    print("\n[7] 같은 k 를 두 번 쓰면 개인키가 풀린다")
    m1, m2 = b"transfer 100", b"hello"
    e1, r1, s1 = ecdsa_sign(curve, g, n, d, m1, k=10)
    e2, r2, s2 = ecdsa_sign(curve, g, n, d, m2, k=10)
    print(f"    서명1 (e={e1}, r={r1}, s={s1}),  서명2 (e={e2}, r={r2}, s={s2})  → r 이 같다")
    k_found = (e1 - e2) * pow(s1 - s2, -1, n) % n
    d_found = (s1 * k_found - e1) * pow(r1, -1, n) % n
    print(f"    k = (e1-e2)/(s1-s2) mod n = {k_found}")
    print(f"    d = (s1*k - e1)/r mod n = {d_found}, 실제 d 와 같음: {d_found == d}")

    print("\n[8] 작은 곡선은 전수 조사로 깨진다 — Q 만 보고 d 찾기")
    tries = next(i for i in range(1, n) if curve.multiply(i, g) == q)
    print(f"    Q={q} → d={tries}, 시도 {tries}번 (최대 n-1={n - 1}번)")

    print("\n[9] P-256 (SP 800-186 도메인 파라미터)로 같은 연산 검산")
    p256 = Curve(
        2**256 - 2**224 + 2**192 + 2**96 - 1,
        -3,
        0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B,
    )
    g256 = (
        0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296,
        0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5,
    )
    n256 = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551
    print(f"    G 가 곡선 위: {p256.contains(g256)}")
    print(f"    p 비트 수 = {p256.p.bit_length()}, n 비트 수 = {n256.bit_length()}")
    print(f"    n*G = 무한원점: {p256.multiply(n256, g256) is INFINITY}")
    d_a, d_b = 0x1234567890ABCDEF, 0xFEDCBA0987654321
    z1 = p256.multiply(d_a, p256.multiply(d_b, g256))
    z2 = p256.multiply(d_b, p256.multiply(d_a, g256))
    print(f"    ECDH 공유 비밀 일치: {z1 == z2}")
    e, r, s = ecdsa_sign(p256, g256, n256, d_a, b"transfer 100", k=0x0BADC0FFEE)
    print(f"    ECDSA 서명 검증: {ecdsa_verify(p256, g256, n256, p256.multiply(d_a, g256), b'transfer 100', r, s)}")
    print(f"    서명 길이: r {r.bit_length()}비트 + s {s.bit_length()}비트 (각 최대 256비트)")


if __name__ == "__main__":
    main()
