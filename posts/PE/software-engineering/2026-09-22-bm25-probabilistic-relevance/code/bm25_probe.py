"""BM25 항 가중치의 세 가지 성질을 직접 계산해 확인한다.

식은 Robertson & Zaragoza, "The Probabilistic Relevance Framework: BM25 and Beyond",
Foundations and Trends in Information Retrieval 3(4), 2009 의 식 (3.3)·(3.12)·(3.15)를
그대로 옮긴 것이다.

  w_IDF(i)  = log( (N - n_i + 0.5) / (n_i + 0.5) )                     … (3.3)
  B         = (1 - b) + b * dl / avdl                                   … (3.12)
  w_BM25(i) = tf / (k1 * B + tf) * w_IDF(i)                             … (3.15)

확인하는 것은 셋이다.
  ① tf 가 커져도 항 가중치가 w_IDF 를 넘지 못한다 (포화)
  ② k1 이 포화가 시작되는 속도를 정한다
  ③ b 가 문서 길이를 얼마나 반영할지 정한다. b = 0 이면 길이를 무시한다
"""

import math

# 말뭉치 크기와 문서 빈도. 값 자체에는 의미가 없고, 희소한 항과 흔한 항을
# 나란히 놓아 IDF 차이가 포화 한계에 어떻게 반영되는지 보려고 고른 값이다.
COLLECTION_SIZE = 1_000_000
AVG_DOC_LENGTH = 300

TERMS = [
    ("희소어", 1_000),
    ("보통어", 50_000),
    ("흔한어", 400_000),
]

K1_DEFAULT = 1.2
B_DEFAULT = 0.75


def idf_weight(collection_size, doc_freq):
    """관련성 정보가 없을 때 RSJ 가중치가 환원되는 형태 (식 3.3)."""
    return math.log((collection_size - doc_freq + 0.5) / (doc_freq + 0.5))


def length_norm(doc_length, avg_doc_length, b):
    """소프트 길이 정규화 성분 B (식 3.12)."""
    return (1.0 - b) + b * doc_length / avg_doc_length


def bm25_term_weight(tf, doc_freq, doc_length, k1=K1_DEFAULT, b=B_DEFAULT,
                     collection_size=COLLECTION_SIZE,
                     avg_doc_length=AVG_DOC_LENGTH):
    """BM25 항 가중치 (식 3.15)."""
    norm = length_norm(doc_length, avg_doc_length, b)
    return tf / (k1 * norm + tf) * idf_weight(collection_size, doc_freq)


def section(title):
    print()
    print("=" * 66)
    print(title)
    print("=" * 66)


def probe_saturation():
    section("[1] tf 가 커져도 w_IDF 를 넘지 못한다 — 포화")
    print(f"k1 = {K1_DEFAULT}, b = {B_DEFAULT}, dl = avdl = {AVG_DOC_LENGTH}")
    print()
    header = f"{'tf':>5}"
    for name, _ in TERMS:
        header += f"{name:>12}"
    header += f"{'선형 tf*idf':>14}"
    print(header)

    linear_reference = idf_weight(COLLECTION_SIZE, TERMS[1][1])
    for tf in (1, 2, 3, 5, 10, 20, 50, 200, 10_000):
        row = f"{tf:>5}"
        for _, doc_freq in TERMS:
            weight = bm25_term_weight(tf, doc_freq, AVG_DOC_LENGTH)
            row += f"{weight:>12.4f}"
        row += f"{tf * linear_reference:>14.1f}"
        print(row)

    print()
    print("포화 한계 w_IDF (tf → ∞ 일 때의 극한):")
    for name, doc_freq in TERMS:
        print(f"  {name}(n_i={doc_freq:>7,})  {idf_weight(COLLECTION_SIZE, doc_freq):.4f}")


def probe_k1():
    section("[2] k1 이 포화 속도를 정한다")
    print(f"'보통어'(n_i = {TERMS[1][1]:,}), b = {B_DEFAULT}, dl = avdl")
    print("괄호 안은 포화 한계 대비 비율")
    print()
    doc_freq = TERMS[1][1]
    limit = idf_weight(COLLECTION_SIZE, doc_freq)

    header = f"{'tf':>5}"
    for k1 in (0.0, 0.5, 1.2, 2.0, 10.0):
        header += f"{'k1=' + str(k1):>18}"
    print(header)

    for tf in (1, 2, 5, 10, 30):
        row = f"{tf:>5}"
        for k1 in (0.0, 0.5, 1.2, 2.0, 10.0):
            weight = bm25_term_weight(tf, doc_freq, AVG_DOC_LENGTH, k1=k1)
            row += f"{weight:>10.4f}({weight / limit * 100:>4.0f}%)"
        print(row)


def probe_b():
    section("[3] b 가 문서 길이 반영 정도를 정한다")
    print(f"'보통어'(n_i = {TERMS[1][1]:,}), tf = 5, k1 = {K1_DEFAULT}, avdl = {AVG_DOC_LENGTH}")
    print()
    doc_freq = TERMS[1][1]

    header = f"{'dl':>7}{'dl/avdl':>10}"
    for b in (0.0, 0.3, 0.75, 1.0):
        header += f"{'b=' + str(b):>12}"
    print(header)

    for doc_length in (30, 150, 300, 900, 3000):
        row = f"{doc_length:>7}{doc_length / AVG_DOC_LENGTH:>10.2f}"
        for b in (0.0, 0.3, 0.75, 1.0):
            weight = bm25_term_weight(5, doc_freq, doc_length, b=b)
            row += f"{weight:>12.4f}"
        print(row)

    print()
    print("같은 tf=5 라도 b>0 이면 긴 문서의 가중치가 깎인다.")
    print("b=0 열은 길이에 상관없이 값이 같다 — 정규화가 꺼진 상태다.")


def probe_negative_idf():
    section("[4] n_i 가 절반을 넘으면 IDF 가 음수가 된다")
    print(f"N = {COLLECTION_SIZE:,}")
    print()
    print(f"{'n_i':>10}{'n_i/N':>10}{'w_IDF':>12}")
    for doc_freq in (1_000, 100_000, 400_000, 490_000, 500_000, 510_000, 800_000):
        weight = idf_weight(COLLECTION_SIZE, doc_freq)
        print(f"{doc_freq:>10,}{doc_freq / COLLECTION_SIZE:>10.3f}{weight:>12.4f}")
    print()
    print("n_i 가 N/2 를 넘는 순간 부호가 뒤집힌다. 그 항을 가진 문서가")
    print("오히려 점수를 잃는다는 뜻이라, 구현마다 여기를 따로 막는다.")


if __name__ == "__main__":
    probe_saturation()
    probe_k1()
    probe_b()
    probe_negative_idf()
