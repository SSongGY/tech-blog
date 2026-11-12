"""rsync 기술 보고서(Tridgell·Mackerras)의 약한 롤링 체크섬과 2단 검사를 구현해 본다.

β(받는 쪽)는 옛 파일 B 를, α(보내는 쪽)는 새 파일 A 를 갖고 있다.
1) 롤링 점화식이 직접 계산과 같은 값을 내는지 확인
2) 앞쪽에 5바이트를 끼워 넣은 A — 고정 위치 비교와 롤링 비교가 보내는 바이트 수
3) 받은 지시로 B 에서 A 를 다시 만들어 해시가 같은지 확인
4) 블록 크기별 손익 — 서명 크기와 리터럴 크기
5) 약한 체크섬만 맞고 강한 해시가 틀린 횟수(false alarm)
"""
import hashlib
import random

MOD = 1 << 16          # 보고서가 쓰는 M = 2^16
SIGNATURE_BYTES = 20   # 블록 하나당 약한 4바이트 + 강한 16바이트 (보고서 Results 절)
TOKEN_BYTES = 4        # 일치 블록 번호를 보내는 비용 — 이 예제의 가정


def weak_parts(data, start, end):
    """a(k,l), b(k,l) 를 정의식 그대로 계산한다. 점화식 검산용."""
    a = sum(data[start:end]) % MOD
    b = sum((end - i) * data[i] for i in range(start, end)) % MOD
    return a, b


def strong_hash(chunk):
    return hashlib.md5(chunk).digest()


def make_signature(old, block_size):
    """β 쪽 일: B 를 겹치지 않는 블록으로 나눠 (약한, 강한) 체크섬을 만든다."""
    table = {}
    count = len(old) // block_size
    for index in range(count):
        chunk = old[index * block_size:(index + 1) * block_size]
        a, b = weak_parts(chunk, 0, block_size)
        table.setdefault(a + (b << 16), []).append((strong_hash(chunk), index))
    return table, count


def rolling_delta(new, table, block_size):
    """α 쪽 일: A 의 모든 위치에서 창을 한 바이트씩 밀며 B 의 블록을 찾는다."""
    ops, literal = [], bytearray()
    false_alarms = weak_hits = 0
    k = 0
    a = b = None
    while k + block_size <= len(new):
        if a is None:
            a, b = weak_parts(new, k, k + block_size)
        found = None
        candidates = table.get(a + (b << 16))
        if candidates:
            weak_hits += 1
            digest = strong_hash(new[k:k + block_size])
            found = next((idx for s, idx in candidates if s == digest), None)
            if found is None:
                false_alarms += 1
        if found is not None:
            if literal:
                ops.append(("literal", bytes(literal)))
                literal = bytearray()
            ops.append(("block", found))
            k += block_size
            a = None    # 일치 블록 끝에서 창을 새로 잡는다
            continue
        # 점화식: a(k+1,l+1) = a - X_k + X_{l+1},  b(k+1,l+1) = b - (l-k+1) X_k + a(k+1,l+1)
        out_byte = new[k]
        literal.append(out_byte)
        if k + block_size < len(new):
            a = (a - out_byte + new[k + block_size]) % MOD
            b = (b - block_size * out_byte + a) % MOD
        k += 1
    literal.extend(new[k:])
    if literal:
        ops.append(("literal", bytes(literal)))
    return ops, weak_hits, false_alarms


def fixed_delta(new, old, block_size):
    """비교 대상: 같은 번호의 블록끼리만 비교한다. 위치가 밀리면 못 찾는다."""
    ops = []
    for index in range(0, len(new), block_size):
        chunk = new[index:index + block_size]
        same = old[index:index + block_size]
        if len(chunk) == block_size and strong_hash(chunk) == strong_hash(same):
            ops.append(("block", index // block_size))
        else:
            ops.append(("literal", chunk))
    return ops


def rebuild(old, ops, block_size):
    out = bytearray()
    for kind, value in ops:
        if kind == "block":
            out += old[value * block_size:(value + 1) * block_size]
        else:
            out += value
    return bytes(out)


def wire_cost(ops, block_count):
    literal = sum(len(v) for k, v in ops if k == "literal")
    matched = sum(1 for k, _ in ops if k == "block")
    total = block_count * SIGNATURE_BYTES + literal + matched * TOKEN_BYTES
    return literal, matched, total


def make_files():
    rng = random.Random(20261112)
    words = ["select", "index", "page", "commit", "rollback", "log", "lock",
             "buffer", "query", "table", "row", "column", "join", "plan"]
    old = " ".join(rng.choice(words) for _ in range(40000)).encode()
    new = bytearray(old)
    new[150000:150050] = b""                                  # 50바이트 삭제
    new[100000:100300] = bytes(rng.randrange(256) for _ in range(300))  # 300바이트 교체
    new[1000:1000] = b"[NEW]"                                 # 앞쪽에 5바이트 삽입
    new += b" appended tail" * 10                             # 끝에 140바이트 추가
    return old, bytes(new)


def main():
    old, new = make_files()
    print(f"B(옛 파일) {len(old):,}바이트 · A(새 파일) {len(new):,}바이트")
    print(f"변경: 1,000번째에 5바이트 삽입, 100,000번째 300바이트 교체,"
          f" 150,000번째 50바이트 삭제, 끝에 140바이트 추가")
    print()

    print("[1] 롤링 점화식 검산 — 블록 700, 첫 5,000개 위치")
    size = 700
    a, b = weak_parts(new, 0, size)
    mismatches = 0
    for k in range(5000):
        if (a, b) != weak_parts(new, k, k + size):
            mismatches += 1
        out_byte = new[k]
        a = (a - out_byte + new[k + size]) % MOD
        b = (b - size * out_byte + a) % MOD
    print(f"  직접 계산과 다른 위치 {mismatches}개")
    print()

    print("[2] 블록 700바이트 — 무엇을 보내는가")
    table, count = make_signature(old, size)
    fixed_ops = fixed_delta(new, old, size)
    roll_ops, weak_hits, false_alarms = rolling_delta(new, table, size)
    print(f"  서명: 블록 {count}개 × {SIGNATURE_BYTES}바이트 = {count * SIGNATURE_BYTES:,}바이트")
    print("  방식        | 리터럴 바이트 | 일치 블록 | 보내는 총량 | A 대비")
    for name, ops in (("고정 위치", fixed_ops), ("롤링", roll_ops)):
        literal, matched, total = wire_cost(ops, count)
        print(f"  {name:<10}| {literal:>12,} | {matched:>8} | {total:>10,} | {total / len(new):6.1%}")
    print(f"  파일 전체   | {len(new):>12,} | {0:>8} | {len(new):>10,} | {1:6.1%}")
    print()

    print("[3] B 와 지시로 A 를 다시 만든다")
    rebuilt = rebuild(old, roll_ops, size)
    same = hashlib.sha256(rebuilt).hexdigest() == hashlib.sha256(new).hexdigest()
    print(f"  롤링 지시로 만든 파일 {len(rebuilt):,}바이트 · SHA-256 일치 {same}")
    print(f"  리터럴 덩어리 {sum(1 for k, _ in roll_ops if k == 'literal')}개:"
          + "".join(f" {len(v)}" for k, v in roll_ops if k == "literal"))
    print()

    print("[4] 블록 크기별 — 롤링 방식")
    print("  블록 | 서명 바이트 | 리터럴 바이트 | 일치 블록 | 총량 | A 대비 | 약한 일치 | false alarm")
    for size in (64, 128, 256, 512, 700, 1024, 2048, 4096, 8192):
        table, count = make_signature(old, size)
        ops, weak_hits, false_alarms = rolling_delta(new, table, size)
        assert rebuild(old, ops, size) == new
        literal, matched, total = wire_cost(ops, count)
        print(f"  {size:>4} | {count * SIGNATURE_BYTES:>10,} | {literal:>12,} | {matched:>8} |"
              f" {total:>6,} | {total / len(new):6.1%} | {weak_hits:>8,} | {false_alarms:>4}")
    print()

    print("[5] B 의 모든 창 위치에서 약한 체크섬이 겹치는가")
    print("  블록 | 창 수 | 서로 다른 내용 | 서로 다른 약한 값 | 내용은 다른데 약한 값이 같은 쌍의 창")
    for size in (64, 700):
        weak_to_digest = {}
        contents = set()
        clashes = 0
        a, b = weak_parts(old, 0, size)
        windows = len(old) - size + 1
        for k in range(windows):
            chunk = old[k:k + size]
            digest = strong_hash(chunk)
            contents.add(digest)
            key = a + (b << 16)
            first = weak_to_digest.setdefault(key, digest)
            if first != digest:
                clashes += 1
            if k + size < len(old):
                out_byte = old[k]
                a = (a - out_byte + old[k + size]) % MOD
                b = (b - size * out_byte + a) % MOD
        print(f"  {size:>4} | {windows:,} | {len(contents):,} | {len(weak_to_digest):,} | {clashes:,}")
    low, high = min(old), max(old)
    print(f"  B 의 바이트 값 범위 {low}~{high} (서로 다른 값 {len(set(old))}개)")
    print()

    print("[참고] hashlib 에서 MD4 를 쓸 수 있는가")
    try:
        hashlib.new("md4")
        print("  가능")
    except ValueError as error:
        print(f"  불가 — {error}")


if __name__ == "__main__":
    main()
