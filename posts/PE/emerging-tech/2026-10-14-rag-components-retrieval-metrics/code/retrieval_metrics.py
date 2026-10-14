"""RAG 검색 단계의 품질 지표를 손으로 검산할 수 있게 계산한다.

재는 것은 네 가지다.

- Recall@k   : 정답 문서 중 상위 k 안에 들어온 비율
- Precision@k: 상위 k 중 정답인 비율
- MRR        : 첫 정답이 나온 순위의 역수를 질의마다 평균
- nDCG@k     : 등급을 매긴 적합도를 순위로 할인해 더하고 이상적 순서로 나눈 값

nDCG 는 Jarvelin & Kekalainen (2002) 의 정의를 따른다. 이득은 널리 쓰이는
지수형 2^rel - 1 을 쓰고, 할인은 log2(i+1) 이다.

지표 구현이 맞는지는 손으로 계산한 값과 맞춰 본다 (아래 EXPECTED).
"""

from __future__ import annotations

import math

# 질의마다 (문서 id -> 적합도 등급). 0 은 무관, 3 이 가장 적합하다.
# 등급제는 nDCG 가 전제하는 형태다. 이진 지표는 등급 > 0 을 정답으로 본다.
RELEVANCE: dict[str, dict[str, int]] = {
    "Q1 연차 이월 규정": {"d1": 3, "d2": 2, "d3": 1},
    "Q2 출장비 정산 기한": {"d11": 3, "d12": 1},
    "Q3 재택근무 승인 절차": {"d21": 2, "d22": 2, "d23": 1},
}

# 두 검색기가 돌려준 상위 8건. 같은 질의, 같은 문서 모음이다.
RANKINGS: dict[str, dict[str, list[str]]] = {
    "검색기 A": {
        "Q1 연차 이월 규정": ["d1", "d4", "d2", "d5", "d3", "d6", "d7", "d8"],
        "Q2 출장비 정산 기한": ["d11", "d13", "d12", "d14", "d15", "d16", "d17", "d18"],
        "Q3 재택근무 승인 절차": ["d24", "d21", "d22", "d25", "d23", "d26", "d27", "d28"],
    },
    "검색기 B": {
        "Q1 연차 이월 규정": ["d4", "d5", "d1", "d2", "d3", "d6", "d7", "d8"],
        "Q2 출장비 정산 기한": ["d13", "d14", "d15", "d11", "d12", "d16", "d17", "d18"],
        "Q3 재택근무 승인 절차": ["d24", "d25", "d21", "d26", "d22", "d23", "d27", "d28"],
    },
}

# 손으로 계산해 둔 값. 구현이 이 값과 어긋나면 구현이 틀린 것이다.
EXPECTED = {
    ("검색기 A", "nDCG@5", "Q1 연차 이월 규정"): 0.9461,
    ("검색기 B", "nDCG@5", "Q1 연차 이월 규정"): 0.5514,
}

RULE = "=" * 72


def recall_at_k(ranked: list[str], gold: dict[str, int], k: int) -> float:
    """상위 k 안에 들어온 정답 문서의 비율."""
    relevant = {doc for doc, grade in gold.items() if grade > 0}
    if not relevant:
        return 0.0
    return len(relevant & set(ranked[:k])) / len(relevant)


def precision_at_k(ranked: list[str], gold: dict[str, int], k: int) -> float:
    """상위 k 중 정답인 비율. 분모가 k 로 고정이라 k 를 키우면 보통 떨어진다."""
    relevant = {doc for doc, grade in gold.items() if grade > 0}
    return len(relevant & set(ranked[:k])) / k


def reciprocal_rank(ranked: list[str], gold: dict[str, int]) -> float:
    """첫 정답이 나온 순위의 역수. 하나도 없으면 0."""
    for position, doc in enumerate(ranked, start=1):
        if gold.get(doc, 0) > 0:
            return 1 / position
    return 0.0


def dcg_at_k(grades: list[int], k: int) -> float:
    """지수형 이득 (2^rel - 1) 을 log2(i+1) 로 할인해 더한다."""
    return sum(
        (2 ** grade - 1) / math.log2(position + 1)
        for position, grade in enumerate(grades[:k], start=1)
    )


def ndcg_at_k(ranked: list[str], gold: dict[str, int], k: int) -> float:
    """실제 순서의 DCG 를 이상적 순서의 DCG 로 나눈다. 0~1 로 떨어진다."""
    actual = [gold.get(doc, 0) for doc in ranked]
    ideal = sorted(gold.values(), reverse=True)
    best = dcg_at_k(ideal, k)
    return dcg_at_k(actual, k) / best if best else 0.0


def show_worked_example() -> None:
    """Q1 하나를 항마다 펼쳐 찍는다. 손 계산과 맞춰 보기 위한 것이다."""
    print(RULE)
    print("손 계산 대조 — Q1 의 nDCG@5 를 항마다 펼친다")
    print(RULE)
    query = "Q1 연차 이월 규정"
    gold = RELEVANCE[query]
    print(f"정답 등급: {gold}")
    ideal = sorted(gold.values(), reverse=True)
    print(f"이상적 순서의 등급: {ideal} → IDCG@5 = {dcg_at_k(ideal, 5):.4f}\n")

    for name in RANKINGS:
        ranked = RANKINGS[name][query]
        grades = [gold.get(doc, 0) for doc in ranked[:5]]
        print(f"{name}  상위 5건 {ranked[:5]}")
        print(f"  등급      {grades}")
        terms = [
            f"(2^{g}-1)/log2({i}+1) = {(2 ** g - 1) / math.log2(i + 1):.4f}"
            for i, g in enumerate(grades, start=1)
            if g > 0
        ]
        for term in terms:
            print(f"    {term}")
        dcg = dcg_at_k(grades, 5)
        print(f"  DCG@5   = {dcg:.4f}")
        print(f"  nDCG@5  = {dcg:.4f} / {dcg_at_k(ideal, 5):.4f} = "
              f"{ndcg_at_k(ranked, gold, 5):.4f}\n")

    print("손으로 계산해 둔 값과 맞는가")
    for (name, metric, q), expected in EXPECTED.items():
        got = round(ndcg_at_k(RANKINGS[name][q], RELEVANCE[q], 5), 4)
        print(f"  {name} {metric} {q}: 계산 {got} · 기대 {expected} · "
              f"{'일치' if got == expected else '불일치'}")
    print()


def show_table() -> None:
    print(RULE)
    print("질의 3건 평균 — 두 검색기 비교")
    print(RULE)
    header = (
        f"{'검색기':<8} {'Recall@3':>9} {'Recall@5':>9} {'P@3':>7}"
        f" {'P@5':>7} {'MRR':>7} {'nDCG@5':>8}"
    )
    print(header)
    print("-" * len(header))
    for name, per_query in RANKINGS.items():
        queries = list(per_query)
        values = {
            "Recall@3": [recall_at_k(per_query[q], RELEVANCE[q], 3) for q in queries],
            "Recall@5": [recall_at_k(per_query[q], RELEVANCE[q], 5) for q in queries],
            "P@3": [precision_at_k(per_query[q], RELEVANCE[q], 3) for q in queries],
            "P@5": [precision_at_k(per_query[q], RELEVANCE[q], 5) for q in queries],
            "MRR": [reciprocal_rank(per_query[q], RELEVANCE[q]) for q in queries],
            "nDCG@5": [ndcg_at_k(per_query[q], RELEVANCE[q], 5) for q in queries],
        }
        means = {key: sum(v) / len(v) for key, v in values.items()}
        print(
            f"{name:<8} {means['Recall@3']:9.3f} {means['Recall@5']:9.3f}"
            f" {means['P@3']:7.3f} {means['P@5']:7.3f}"
            f" {means['MRR']:7.3f} {means['nDCG@5']:8.3f}"
        )
    print()


def show_context_budget() -> None:
    """생성기에 상위 몇 건을 넣느냐에 따라 같은 검색 결과가 다르게 쓰인다."""
    print(RULE)
    print("생성기에 넣는 문서 수(k)에 따라 들어가는 정답 건수")
    print(RULE)
    print(f"{'k':>3} | {'검색기 A':>12} | {'검색기 B':>12}")
    print("-" * 36)
    for k in (1, 2, 3, 5, 8):
        row = []
        for name, per_query in RANKINGS.items():
            total = sum(
                len({d for d, g in RELEVANCE[q].items() if g > 0} & set(per_query[q][:k]))
                for q in per_query
            )
            row.append(total)
        print(f"{k:>3} | {row[0]:>12} | {row[1]:>12}")
    print("\n세 질의의 정답 문서는 모두 8건이다.\n")


def main() -> None:
    print(f"정답 집합이 있는 질의 {len(RELEVANCE)}건, 검색기 {len(RANKINGS)}개\n")
    show_worked_example()
    show_table()
    show_context_budget()


if __name__ == "__main__":
    main()
