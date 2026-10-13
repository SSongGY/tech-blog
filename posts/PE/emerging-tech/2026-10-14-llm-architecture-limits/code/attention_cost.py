"""트랜스포머 구조에서 비용이 어디서 나오는지 직접 계산한다.

쓰는 상수는 전부 Vaswani et al.(2017) "Attention Is All You Need" 의
base 모델 값이다. 측정이 아니라 구조에서 바로 따라 나오는 산술이다.

  §3.1  인코더·디코더 스택  N = 6,  d_model = 512
  §3.2.2 멀티헤드          h = 8,  d_k = d_v = d_model / h = 64
  Table 1 self-attention 의 레이어당 복잡도  O(n^2 · d)
"""

NUM_LAYERS = 6        # N  — 디코더 스택의 층 수
D_MODEL = 512         # d_model
NUM_HEADS = 8         # h
BYTES_PER_VALUE = 2   # 가중치를 16비트로 둘 때. 32비트면 두 배가 된다

SEQUENCE_LENGTHS = [128, 256, 512, 1024, 2048, 4096]

RULE = "=" * 68


def attention_scores(seq_len):
    """한 번의 순전파에서 만들어지는 어텐션 점수 칸의 총 개수.

    헤드 하나가 n x n 점수 행렬을 만들고, 그것이 헤드 수와 층 수만큼 생긴다.
    """
    return seq_len * seq_len * NUM_HEADS * NUM_LAYERS


def kv_cache_bytes(seq_len):
    """디코더가 이미 만든 토큰의 K, V 를 들고 있을 때 차지하는 바이트.

    층마다 K 한 벌과 V 한 벌이고, 각 벌은 토큰당 d_model 개의 값이다.
    """
    return 2 * NUM_LAYERS * seq_len * D_MODEL * BYTES_PER_VALUE


def main():
    print(RULE)
    print("기준 모델 — Vaswani et al.(2017) base")
    print(RULE)
    print(f"  층 수 N        {NUM_LAYERS}")
    print(f"  d_model        {D_MODEL}")
    print(f"  헤드 수 h      {NUM_HEADS}  (d_k = d_v = {D_MODEL // NUM_HEADS})")
    print(f"  값 하나의 크기 {BYTES_PER_VALUE}바이트 (16비트로 둘 때)")
    print()

    print(RULE)
    print("입력 길이가 2배가 될 때 무엇이 몇 배가 되는가")
    print(RULE)
    # 한글은 터미널에서 두 칸을 차지하므로 폭을 손으로 맞춘다
    header = "    길이 n |      어텐션 점수 칸 | 직전 대비 |     KV 캐시 | 직전 대비"
    print(header)
    print("  " + "-" * 70)

    previous_scores = None
    previous_cache = None
    for seq_len in SEQUENCE_LENGTHS:
        scores = attention_scores(seq_len)
        cache = kv_cache_bytes(seq_len)
        scores_ratio = "-" if previous_scores is None else f"{scores / previous_scores:.1f}배"
        cache_ratio = "-" if previous_cache is None else f"{cache / previous_cache:.1f}배"
        print(
            f"  {seq_len:>8,} | {scores:>18,} | {scores_ratio:>7} | "
            f"{cache / 1024 / 1024:>7.2f} MiB | {cache_ratio:>7}"
        )
        previous_scores, previous_cache = scores, cache
    print()

    print(RULE)
    print("검산 — 정의대로 다시 세어 본다")
    print(RULE)
    seq_len = 512
    by_definition = 0
    for _layer in range(NUM_LAYERS):
        for _head in range(NUM_HEADS):
            by_definition += seq_len * seq_len      # n x n 점수 행렬 한 장
    print(f"  n = {seq_len} 일 때")
    print(f"    수식으로        {attention_scores(seq_len):,}")
    print(f"    하나씩 세어서   {by_definition:,}")
    print(f"    일치            {attention_scores(seq_len) == by_definition}")

    doubled = attention_scores(seq_len * 2) / attention_scores(seq_len)
    print(f"    길이를 2배로 하면 점수 칸은 {doubled:.0f}배 — n^2 이므로 4배여야 한다")
    print(f"    KV 캐시는 {kv_cache_bytes(seq_len * 2) / kv_cache_bytes(seq_len):.0f}배 — n 에 비례하므로 2배여야 한다")


if __name__ == "__main__":
    main()
