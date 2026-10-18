"""KV 캐시가 차지하는 바이트 수를 구성 요소별로 계산한다.

캐시 크기는 모델 가중치를 받지 않아도 구조 상수만으로 정해진다.
따라서 이 스크립트는 GPU 없이 어디서나 같은 값을 낸다.

    bytes = 2 * L * H_kv * d_h * S * B * e
      2    키와 값 두 벌
      L    디코더 레이어 수
      H_kv 레이어당 키·값 헤드 수
      d_h  헤드 하나의 차원
      S    문맥 길이(토큰)
      B    동시에 처리하는 배치 크기
      e    원소 하나의 바이트 수
"""

import platform
import sys

# 가정한 구성. 특정 제품의 값이 아니라 70B 급 디코더의 형태를 본뜬 숫자다.
LAYERS = 80
QUERY_HEADS = 64
HEAD_DIM = 128

# 원소 하나의 바이트 수. INT4 는 반 바이트라 0.5 로 둔다.
ELEMENT_BYTES = {"FP16": 2.0, "FP8": 1.0, "INT4": 0.5}

# 어텐션 변형별 키·값 헤드 수. GQA 는 질의 헤드를 8 그룹으로 묶은 경우다.
KV_HEADS = {
    "MHA": QUERY_HEADS,
    "GQA(8group)": 8,
    "MQA": 1,
}

GIB = 1024 ** 3


def kv_cache_bytes(layers, kv_heads, head_dim, seq_len, batch, element_bytes):
    """키·값 두 벌을 모두 더한 캐시 크기를 바이트로 돌려준다."""
    return 2 * layers * kv_heads * head_dim * seq_len * batch * element_bytes


def print_environment():
    print("[환경]")
    print(f"  파이썬  {platform.python_version()}")
    print(f"  플랫폼  {platform.system()} {platform.release()}")
    print(f"  실행    {sys.argv[0]}")
    print()


def print_assumptions():
    print("[가정한 구성]")
    print(f"  decoder layers L   = {LAYERS}")
    print(f"  query heads        = {QUERY_HEADS}")
    print(f"  head dim d_h       = {HEAD_DIM}")
    print(f"  hidden dim         = {QUERY_HEADS * HEAD_DIM}")
    print()


VARIANTS = ("MHA", "GQA(8group)", "MQA")


def row(label, sizes):
    cells = " | ".join(f"{size / GIB:10.2f} GiB" for size in sizes)
    print(f"  {label:>10} | {cells}")


def table_by_context():
    print("[1] context length vs cache size (batch 1, FP16)")
    print(f"  {'tokens':>10} | {'MHA':>14} | {'GQA(8group)':>14} | {'MQA':>14}")
    print("  " + "-" * 62)
    for seq_len in (1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072):
        sizes = [
            kv_cache_bytes(
                LAYERS, KV_HEADS[name], HEAD_DIM, seq_len, 1, ELEMENT_BYTES["FP16"]
            )
            for name in VARIANTS
        ]
        row(f"{seq_len:,}", sizes)
    print("  문맥을 2배로 늘릴 때마다 세 열 모두 정확히 2배가 된다.")
    print()


def table_by_batch():
    print("[2] batch size vs cache size (16,384 tokens, FP16)")
    print(f"  {'batch':>10} | {'MHA':>14} | {'GQA(8group)':>14} | {'MQA':>14}")
    print("  " + "-" * 62)
    for batch in (1, 8, 32, 128):
        sizes = [
            kv_cache_bytes(
                LAYERS, KV_HEADS[name], HEAD_DIM, 16384, batch, ELEMENT_BYTES["FP16"]
            )
            for name in VARIANTS
        ]
        row(f"{batch:,}", sizes)
    print()


def table_by_precision():
    print("[3] element precision vs cache size (GQA 8group, 16,384 tokens, batch 32)")
    print(f"  {'precision':>10} | {'bytes/elem':>10} | {'cache':>14} | {'vs FP16':>8}")
    print("  " + "-" * 54)
    base = None
    for name, element_bytes in ELEMENT_BYTES.items():
        size = kv_cache_bytes(
            LAYERS, KV_HEADS["GQA(8group)"], HEAD_DIM, 16384, 32, element_bytes
        )
        if base is None:
            base = size
        print(
            f"  {name:>10} | {element_bytes:>10} | {size / GIB:10.2f} GiB"
            f" | {base / size:7.1f}x"
        )
    print()


def check_head_ratio():
    """캐시가 줄어드는 비율이 질의 헤드 수 / 키·값 헤드 수와 같은지 확인한다."""
    print("[4] reduction factor vs head-count ratio")
    mha = kv_cache_bytes(LAYERS, KV_HEADS["MHA"], HEAD_DIM, 8192, 4, 2.0)
    for name in ("GQA(8group)", "MQA"):
        size = kv_cache_bytes(LAYERS, KV_HEADS[name], HEAD_DIM, 8192, 4, 2.0)
        measured = mha / size
        expected = QUERY_HEADS / KV_HEADS[name]
        mark = "match" if abs(measured - expected) < 1e-9 else "MISMATCH"
        print(
            f"  {name:>12}: computed {measured:5.1f}x,"
            f" head ratio {expected:5.1f}x -> {mark}"
        )
    print()


def main():
    print_environment()
    print_assumptions()
    table_by_context()
    table_by_batch()
    table_by_precision()
    check_head_ratio()


if __name__ == "__main__":
    main()
