"""짧은 메시지를 하나씩 압축할 때 zlib 에서 일어나는 일.

1) 한 건씩 압축하면 거의 줄지 않는다 (헤더 6바이트 + 반복을 찾을 앞부분이 없음)
2) 같은 메시지를 이어 붙여 한 번에 압축하면 크게 줄어든다
3) 사전(zdict)을 주면 한 건씩 압축해도 줄어든다
4) 사전이 다르면 풀 수 없다
"""
import json
import random
import zlib

MESSAGE_COUNT = 500
DICT_SAMPLE_COUNT = 30
LEVEL = 6
SEED = 20261105

ACTIONS = ["login", "logout", "view", "purchase", "search"]
PAGES = ["/home", "/cart", "/item/17", "/item/42", "/search", "/mypage"]


def make_message(rng, seq):
    return json.dumps(
        {
            "event": rng.choice(ACTIONS),
            "user_id": rng.randrange(1000, 9999),
            "page": rng.choice(PAGES),
            "status": "ok",
            "seq": seq,
        },
        separators=(",", ":"),
    ).encode()


def compress_one(data, zdict=None, wbits=zlib.MAX_WBITS):
    if zdict is None:
        comp = zlib.compressobj(LEVEL, zlib.DEFLATED, wbits)
    else:
        comp = zlib.compressobj(LEVEL, zlib.DEFLATED, wbits, zlib.DEF_MEM_LEVEL, zlib.Z_DEFAULT_STRATEGY, zdict)
    return comp.compress(data) + comp.flush()


def main():
    print("zlib 헤더 버전 %s / 실행 버전 %s" % (zlib.ZLIB_VERSION, zlib.ZLIB_RUNTIME_VERSION))
    rng = random.Random(SEED)
    messages = [make_message(rng, i) for i in range(MESSAGE_COUNT)]
    print("\n-- 입력 예시 (%d건 중 앞 3건)" % MESSAGE_COUNT)
    for m in messages[:3]:
        print("  %3d바이트  %s" % (len(m), m.decode()))
    raw_total = sum(len(m) for m in messages)
    print("  원본 합계 %d바이트, 평균 %.1f바이트" % (raw_total, raw_total / MESSAGE_COUNT))

    # 사전은 앞 메시지 몇 건에서 뽑는다. 압축 대상과 겹치지 않는 건을 쓰도록 별도 시드를 쓴다
    dict_rng = random.Random(SEED + 1)
    zdict = b"".join(make_message(dict_rng, i) for i in range(DICT_SAMPLE_COUNT))

    print("\n-- 압축 방식별 합계 (수준 %d)" % LEVEL)
    print("  %-34s %8s %8s" % ("방식", "합계(B)", "원본 대비"))

    def row(name, total):
        print("  %-34s %8d %7.1f%%" % (name, total, total / raw_total * 100))

    row("한 건씩, zlib 헤더 포함", sum(len(compress_one(m)) for m in messages))
    row("한 건씩, 헤더 없음(wbits=-15)", sum(len(compress_one(m, wbits=-zlib.MAX_WBITS)) for m in messages))
    row("한 건씩, 사전 %dB 사용" % len(zdict), sum(len(compress_one(m, zdict)) for m in messages))
    row("한 건씩, 사전 + 헤더 없음", sum(len(compress_one(m, zdict, -zlib.MAX_WBITS)) for m in messages))
    row("전부 이어 붙여 한 번에", len(zlib.compress(b"".join(messages), LEVEL)))

    one = messages[0]
    print("\n-- 첫 메시지(%d바이트) 한 건" % len(one))
    print("  사전 없음 %d바이트, 사전 사용 %d바이트" % (len(compress_one(one)), len(compress_one(one, zdict))))

    print("\n-- 풀기")
    packed = compress_one(one, zdict)
    d = zlib.decompressobj(zdict=zdict)
    print("  같은 사전으로 풀기:", d.decompress(packed) == one)
    try:
        zlib.decompress(packed)
    except zlib.error as exc:
        print("  사전 없이 풀기   :", exc)
    try:
        zlib.decompressobj(zdict=b"x" * len(zdict)).decompress(packed)
    except zlib.error as exc:
        print("  다른 사전으로 풀기:", exc)


if __name__ == "__main__":
    main()
