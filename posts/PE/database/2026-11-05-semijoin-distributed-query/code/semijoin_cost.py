"""분산 조인 R(사이트 1) ⋈ S(사이트 2) 의 전송량을 세 방식으로 센다.

방식 A: R 전체를 사이트 2 로 보낸다 (ship-whole)
방식 B: S 의 조인 속성 π(S)를 사이트 1 로 보내고, R ⋉ S 만 사이트 2 로 보낸다 (반결합)
방식 C: π(S) 대신 비트 배열을 보낸다 (해시 버킷 수 N)
전송량은 바이트로 센다. 계산 비용·지연은 세지 않는다.
"""
import random
import zlib

SEED = 20261105
R_ROWS = 10_000      # R 의 행 수
R_ROW_BYTES = 100    # R 한 행의 바이트
KEY_BYTES = 4        # 조인 속성 한 값의 바이트
KEY_SPACE = 50_000   # 조인 속성이 가질 수 있는 값의 수
BUCKETS = 8192       # 비트 배열 크기(비트)


def bucket(value):
    # 파이썬 내장 hash 는 실행마다 달라지는 값이 있어 결정적인 해시를 쓴다
    return zlib.crc32(value.to_bytes(4, "big")) % BUCKETS


def scenario(name, s_distinct):
    rng = random.Random(SEED)
    r_keys = [rng.randrange(KEY_SPACE) for _ in range(R_ROWS)]
    s_keys = set(rng.sample(range(KEY_SPACE), s_distinct))

    ship_whole = R_ROWS * R_ROW_BYTES
    projection = len(s_keys) * KEY_BYTES
    reduced = sum(1 for k in r_keys if k in s_keys)
    semijoin_total = projection + reduced * R_ROW_BYTES

    bits = [False] * BUCKETS
    for k in s_keys:
        bits[bucket(k)] = True
    approx = sum(1 for k in r_keys if bits[bucket(k)])
    bitarray_total = BUCKETS // 8 + approx * R_ROW_BYTES

    print("\n-- %s: S 의 서로 다른 조인 값 %d개" % (name, len(s_keys)))
    print("  R 의 행 중 S 와 짝이 있는 행: %d / %d" % (reduced, R_ROWS))
    print("  %-28s %9s" % ("방식", "전송(B)"))
    print("  %-28s %9d" % ("A 전체 전송", ship_whole))
    print("  %-28s %9d  (π(S) %d + R⋉S %d)" % ("B 반결합", semijoin_total, projection, reduced * R_ROW_BYTES))
    print("  %-28s %9d  (비트 %d + R' %d행, 거짓 양성 %d행)"
          % ("C 비트 배열", bitarray_total, BUCKETS // 8, approx, approx - reduced))
    print("  반결합이 이득인가: %s" % (semijoin_total < ship_whole))


if __name__ == "__main__":
    print("R %d행 x %dB = %dB, 조인 값 %dB, 값의 범위 %d" % (R_ROWS, R_ROW_BYTES, R_ROWS * R_ROW_BYTES, KEY_BYTES, KEY_SPACE))
    scenario("S 가 작다", 200)
    scenario("S 가 보통", 5_000)
    scenario("S 가 크다", 48_000)
