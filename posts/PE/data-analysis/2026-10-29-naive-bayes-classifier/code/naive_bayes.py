"""다항 나이브 베이즈 분류기를 손으로 짜서 계산 과정을 전부 찍는다.

McCallum & Nigam (1998) 의 다항 사건 모델(식 5·6)과 다변량 베르누이 모델
(식 2·3)을 그대로 옮겼다. 스무딩은 두 모델 모두 라플라스 사전분포를 쓴다.
"""

import math
import sys
from collections import Counter

# 가상의 사내 메일 학습 집합. 공백으로 끊어 토큰으로 쓴다.
TRAIN = [
    ("스팸", "무료 쿠폰 지금 신청"),
    ("스팸", "지금 신청 무료 대출"),
    ("스팸", "대출 한도 상향 무료 무료"),
    ("정상", "회의 자료 공유 부탁"),
    ("정상", "내일 회의 일정 공유"),
    ("정상", "프로젝트 자료 정리 부탁"),
    ("정상", "일정 변경 공유 부탁"),
]

TEST = "무료 자료 공유"
UNSEEN = "무료 쿠폰 할인"  # '할인' 은 학습에 없던 단어다


def banner(title):
    print()
    print("=" * 66)
    print(title)
    print("=" * 66)


def tokenize(text):
    return text.split()


def build_vocabulary(train):
    vocab = set()
    for _, text in train:
        vocab.update(tokenize(text))
    return sorted(vocab)


def class_counts(train):
    """클래스별 문서 수와 단어 빈도를 센다."""
    docs = Counter()
    words = {}
    for label, text in train:
        docs[label] += 1
        words.setdefault(label, Counter()).update(tokenize(text))
    return docs, words


def multinomial_params(train, vocab, alpha=1.0):
    """다항 모델의 조건부 확률. 분모에 alpha*|V| 를 더하는 것이 라플라스 스무딩이다."""
    docs, words = class_counts(train)
    total_docs = sum(docs.values())
    priors = {c: n / total_docs for c, n in docs.items()}
    likelihood = {}
    totals = {}
    for c in docs:
        total = sum(words[c].values())
        totals[c] = total
        likelihood[c] = {
            w: (words[c][w] + alpha) / (total + alpha * len(vocab)) for w in vocab
        }
    return priors, likelihood, words, totals


def classify(priors, likelihood, vocab, text, verbose=False):
    """로그 확률의 합으로 점수를 낸다. 곱으로 하면 토큰이 늘수록 0 으로 가라앉는다."""
    tokens = [t for t in tokenize(text) if t in vocab]
    dropped = [t for t in tokenize(text) if t not in vocab]
    scores = {}
    for c, prior in priors.items():
        score = math.log(prior)
        parts = [f"log P({c})={math.log(prior):+.4f}"]
        for t in tokens:
            term = math.log(likelihood[c][t])
            score += term
            parts.append(f"log P({t}|{c})={term:+.4f}")
        scores[c] = score
        if verbose:
            print(f"  {c}: " + " ".join(parts))
            print(f"       합계 = {score:+.4f}")
    return scores, tokens, dropped


def softmax(scores):
    """로그 점수를 사후확률로 되돌린다. 최대값을 빼고 지수를 취해 오버플로를 피한다."""
    top = max(scores.values())
    exps = {c: math.exp(s - top) for c, s in scores.items()}
    z = sum(exps.values())
    return {c: v / z for c, v in exps.items()}


def report_training(train, vocab):
    banner("1. 학습 집합과 어휘")
    for label, text in train:
        print(f"  [{label}] {text}")
    print()
    print(f"어휘 크기 |V| = {len(vocab)}")
    print("  " + " ".join(vocab))


def report_params(priors, likelihood, words, totals, vocab):
    banner("2. 추정한 모수 — 사전확률과 조건부확률 (라플라스 alpha=1)")
    for c in sorted(priors):
        print(f"  P({c}) = {priors[c]:.4f}   클래스 내 총 단어 수 = {totals[c]}")
    print()
    header = f"{'단어':<8}" + "".join(f"{c + ' 빈도':>10}{c + ' 확률':>12}" for c in sorted(priors))
    print(header)
    print("-" * len(header))
    for w in vocab:
        row = f"{w:<8}"
        for c in sorted(priors):
            row += f"{words[c][w]:>10}{likelihood[c][w]:>12.4f}"
        print(row)
    print()
    for c in sorted(priors):
        total = sum(likelihood[c].values())
        print(f"  sum_w P(w|{c}) = {total:.6f}   (어휘 전체에 대해 1 이 되어야 한다)")


def report_classification(priors, likelihood, vocab, text):
    banner(f"3. 분류 — \"{text}\"")
    scores, tokens, dropped = classify(priors, likelihood, vocab, text, verbose=True)
    if dropped:
        print(f"  어휘에 없어 버린 토큰: {dropped}")
    print()
    posterior = softmax(scores)
    for c in sorted(scores, key=lambda k: -scores[k]):
        print(f"  {c}: 로그점수 {scores[c]:+.4f}  사후확률 {posterior[c]:.4f}")
    winner = max(scores, key=scores.get)
    print(f"  -> 판정: {winner}")
    return winner


def report_smoothing_effect(train, vocab):
    banner("4. 스무딩을 빼면 무슨 일이 생기는가")
    _, words = class_counts(train)
    print("  '할인' 은 학습 집합에 없다. alpha=0 이면 두 클래스 모두 확률이 0 이 된다.")
    print(f"    스팸에서의 빈도 = {words['스팸']['할인']}, 정상에서의 빈도 = {words['정상']['할인']}")
    print()
    print("  어휘에 '할인' 을 넣고 alpha 를 바꿔 가며 P('할인'|스팸) 을 본다.")
    vocab_plus = sorted(set(vocab) | {"할인"})
    print(f"  {'alpha':>8}{'P(할인|스팸)':>16}{'P(무료|스팸)':>16}")
    for alpha in (0.0, 0.01, 0.1, 1.0):
        if alpha == 0.0:
            _, words_only = class_counts(train)
            total = sum(words_only["스팸"].values())
            p_unseen = words_only["스팸"]["할인"] / total
            p_free = words_only["스팸"]["무료"] / total
        else:
            _, lk, _, _ = multinomial_params(train, vocab_plus, alpha=alpha)
            p_unseen = lk["스팸"]["할인"]
            p_free = lk["스팸"]["무료"]
        print(f"  {alpha:>8.2f}{p_unseen:>16.6f}{p_free:>16.6f}")
    print()
    print("  alpha 를 키우면 못 본 단어에 확률이 생기는 대신 본 단어의 확률이 깎인다.")


def report_underflow():
    banner("5. 로그를 쓰는 이유 — 곱으로 계산할 때의 하한")
    p = 0.01
    print(f"  단어 하나의 확률을 {p} 로 두고 토큰 수를 늘려 가며 곱해 본다.")
    print(f"  {'토큰 수':>8}{'곱':>24}{'로그 합':>14}")
    for n in (10, 50, 100, 150, 160, 200, 400):
        product = p ** n
        log_sum = n * math.log(p)
        print(f"  {n:>8}{product:>24.6e}{log_sum:>14.2f}")
    print()
    print(f"  float 의 최소 정규값 = {sys.float_info.min:.6e}")
    print(f"  0.01 ** 200 == 0.0 ? {0.01 ** 200 == 0.0}")
    print("  로그 합은 같은 지점에서도 유한한 값으로 남는다.")


def bernoulli_compare(train, vocab, text):
    """다변량 베르누이 모델. 문서에 없는 단어의 '미출현 확률'까지 곱한다."""
    banner(f"6. 다변량 베르누이 모델과의 비교 — \"{text}\"")
    docs, _ = class_counts(train)
    total_docs = sum(docs.values())
    present = {}
    for label, body in train:
        for w in set(tokenize(body)):
            present.setdefault(label, Counter())[w] += 1
    priors = {c: n / total_docs for c, n in docs.items()}

    tokens = set(t for t in tokenize(text) if t in vocab)
    scores = {}
    for c in sorted(priors):
        # 식 3: 분자에 1, 분모에 2 를 더하는 라플라스 사전분포
        score = math.log(priors[c])
        for w in vocab:
            p_w = (present.get(c, Counter())[w] + 1) / (docs[c] + 2)
            score += math.log(p_w if w in tokens else 1 - p_w)
        scores[c] = score
    posterior = softmax(scores)
    for c in sorted(scores, key=lambda k: -scores[k]):
        print(f"  {c}: 로그점수 {scores[c]:+.4f}  사후확률 {posterior[c]:.4f}")
    print(f"  -> 판정: {max(scores, key=scores.get)}")
    print()
    print("  베르누이는 어휘 전체를 훑으며 '나오지 않은 단어'의 확률까지 곱한다.")
    print(f"  이 문서의 토큰은 {len(tokens)}개지만 곱한 항은 {len(vocab)}개다.")
    return max(scores, key=scores.get)


def main():
    print(f"Python {sys.version.split()[0]}")
    print("가상의 사내 메일 7통으로 학습한다. 실재하는 데이터가 아니다.")
    vocab = build_vocabulary(TRAIN)
    report_training(TRAIN, vocab)
    priors, likelihood, words, totals = multinomial_params(TRAIN, vocab)
    report_params(priors, likelihood, words, totals, vocab)
    report_classification(priors, likelihood, vocab, TEST)
    report_classification(priors, likelihood, vocab, UNSEEN)
    report_smoothing_effect(TRAIN, vocab)
    report_underflow()
    bernoulli_compare(TRAIN, vocab, TEST)


if __name__ == "__main__":
    main()
