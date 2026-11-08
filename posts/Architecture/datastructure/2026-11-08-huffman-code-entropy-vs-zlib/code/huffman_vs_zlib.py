"""허프만 부호를 표준 라이브러리로 만들고, 엔트로피 하한·zlib(DEFLATE)과 맞대 본다.

1) 섀넌 1948 예제(1/2, 1/4, 1/8, 1/8) — 허프만 평균 길이가 엔트로피와 같아지는가
2) 치우친 이진 원천(p=0.95) — 기호당 1비트 아래로 못 내려가는 자리, 기호 묶기(K=1..4)
3) RFC 1951 정규 허프만 — 길이만으로 부호를 다시 만든다
4) 실제 텍스트 — 0차 엔트로피, 허프만, zlib 을 비교한다 (한 번, 20번 반복)
"""
import codecs
import contextlib
import heapq
import io
import math
import random
import zlib

with contextlib.redirect_stdout(io.StringIO()):
    import this  # 'The Zen of Python' 을 rot13 으로 담고 있다. import 할 때 원문을 찍으므로 삼킨다
from collections import Counter
from itertools import product


def entropy(probs):
    return -sum(p * math.log2(p) for p in probs.values() if p > 0)


def huffman_lengths(probs):
    """두 개의 가장 작은 확률을 합치는 일을 하나가 남을 때까지 되풀이한다.

    동점이면 먼저 넣은 쪽이 먼저 나오도록 순번을 붙인다 — 결과를 매번 같게 하려는 것이다.
    """
    if len(probs) == 1:
        return {sym: 1 for sym in probs}
    heap = [(p, order, [sym]) for order, (sym, p) in enumerate(sorted(probs.items()))]
    heapq.heapify(heap)
    lengths = {sym: 0 for sym in probs}
    order = len(heap)
    while len(heap) > 1:
        p1, _, syms1 = heapq.heappop(heap)
        p2, _, syms2 = heapq.heappop(heap)
        for sym in syms1 + syms2:
            lengths[sym] += 1  # 합쳐질 때마다 그 아래 잎은 한 단계 깊어진다
        heapq.heappush(heap, (p1 + p2, order, syms1 + syms2))
        order += 1
    return lengths


def canonical_codes(lengths):
    """RFC 1951 §3.2.2 의 세 단계: bl_count → next_code → 기호 순서대로 배정."""
    max_bits = max(lengths.values())
    bl_count = Counter(lengths.values())
    next_code = {}
    code = 0
    for bits in range(1, max_bits + 1):
        code = (code + bl_count.get(bits - 1, 0)) << 1
        next_code[bits] = code
    codes = {}
    for sym in sorted(lengths):
        n = lengths[sym]
        codes[sym] = format(next_code[n], f"0{n}b")
        next_code[n] += 1
    return codes


def expected_length(probs, lengths):
    return sum(probs[s] * lengths[s] for s in probs)


def section_shannon():
    print("== 1) 섀넌 1948 예제 — 확률이 전부 2의 거듭제곱 ==")
    probs = {"A": 1 / 2, "B": 1 / 4, "C": 1 / 8, "D": 1 / 8}
    lengths = huffman_lengths(probs)
    codes = canonical_codes(lengths)
    for sym in probs:
        print(f"  {sym} p={probs[sym]:<6} 길이 {lengths[sym]}  부호 {codes[sym]}")
    print(f"  엔트로피 H = {entropy(probs):.4f}  평균 길이 L = {expected_length(probs, lengths):.4f}")
    print()


def section_skewed():
    print("== 2) 치우친 이진 원천 p(a)=0.95 — K 개씩 묶어 부호화 ==")
    base = {"a": 0.95, "b": 0.05}
    h = entropy(base)
    print(f"  기호당 엔트로피 H = {h:.4f} 비트")
    print("  K | 잎 수 | 기호당 L | L - H  | 한계 H + 1/K")
    for k in range(1, 5):
        block = {"".join(t): math.prod(base[c] for c in t) for t in product(base, repeat=k)}
        per_symbol = expected_length(block, huffman_lengths(block)) / k
        print(f"  {k} | {len(block):>5} | {per_symbol:.4f}   | {per_symbol - h:.4f} | {h + 1 / k:.4f}")
    print()


def section_rfc_example():
    print("== 3) RFC 1951 예제 — 길이 (3,3,3,3,3,2,4,4) 로 부호 만들기 ==")
    lengths = dict(zip("ABCDEFGH", (3, 3, 3, 3, 3, 2, 4, 4)))
    codes = canonical_codes(lengths)
    print("  " + "  ".join(f"{s}={codes[s]}" for s in "ABCDEFGH"))
    print()


def raw_deflate_size(data, strategy=zlib.Z_DEFAULT_STRATEGY):
    # wbits=-15 는 zlib 머리(2바이트)와 adler32(4바이트) 없이 DEFLATE 블록만 낸다
    # Z_HUFFMAN_ONLY 는 LZ77 반복 찾기를 끄고 허프만 부호화만 한다
    comp = zlib.compressobj(9, zlib.DEFLATED, -15, 8, strategy)
    return len(comp.compress(data) + comp.flush())


def section_text():
    print("== 4) 실제 텍스트 — The Zen of Python ==")
    zen = codecs.decode(this.s, "rot13").encode("ascii")
    rng = random.Random(20261108)
    shuffled = bytes(rng.sample(list(zen), len(zen)))
    cases = [
        ("원문 1회", zen),
        ("원문 20회 반복", zen * 20),
        ("같은 글자를 섞은 것", shuffled),
    ]
    print("  입력 | 바이트 | 기호 종류 | H(0차) | 허프만 비트/기호 | DEFLATE 비트/기호 | DEFLATE 허프만만 비트/기호")
    for name, data in cases:
        counts = Counter(data)
        probs = {b: c / len(data) for b, c in counts.items()}
        lengths = huffman_lengths(probs)
        codes = canonical_codes(lengths)
        bits = "".join(codes[b] for b in data)
        decoded = decode(bits, codes)
        assert decoded == data, "복호 실패"
        deflate_bits = raw_deflate_size(data) * 8
        huffman_only_bits = raw_deflate_size(data, zlib.Z_HUFFMAN_ONLY) * 8
        print(f"  {name} | {len(data)} | {len(counts)} | {entropy(probs):.4f} | "
              f"{len(bits) / len(data):.4f} | {deflate_bits / len(data):.4f} | "
              f"{huffman_only_bits / len(data):.4f}")
    print("  (허프만 비트에는 부호표를 넣지 않았다. DEFLATE 는 부호표와 블록 머리를 포함한다)")
    print("  복호 결과가 세 입력 모두 원문과 같았다")


def decode(bits, codes):
    reverse = {code: sym for sym, code in codes.items()}
    out = bytearray()
    buf = ""
    for bit in bits:
        buf += bit
        if buf in reverse:  # 접두어 없는 부호라 처음 맞는 자리에서 끊어도 된다
            out.append(reverse[buf])
            buf = ""
    return bytes(out)


def main():
    print(f"Python zlib 모듈 {zlib.ZLIB_RUNTIME_VERSION} (런타임 라이브러리)")
    print()
    section_shannon()
    section_skewed()
    section_rfc_example()
    section_text()


if __name__ == "__main__":
    main()
