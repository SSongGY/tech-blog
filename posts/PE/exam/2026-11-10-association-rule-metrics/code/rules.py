"""연관 규칙 지표 답안 검산.

가상 카페의 거래 10건으로 지지도·신뢰도·향상도·레버리지·확신도를 계산하고,
지지도·신뢰도 기준만 통과시키면 향상도 1 미만 규칙이 섞여 들어오는 것을 확인한다.
지표 정의는 Hahsler 의 arules 지표 목록(원 출처 Agrawal 1993, Brin 1997,
Piatetsky-Shapiro 1991)을 그대로 따른다.
"""
from itertools import combinations

TRANSACTIONS = [
    {"커피", "빵", "우유"},
    {"커피", "빵", "우유"},
    {"커피", "빵", "우유"},
    {"빵", "우유"},
    {"커피", "빵"},
    {"커피", "케이크"},
    {"커피", "케이크"},
    {"커피", "케이크"},
    {"케이크"},
    {"커피"},
]
MIN_SUPPORT = 0.3
MIN_CONFIDENCE = 0.6


def support(itemset):
    hits = sum(1 for t in TRANSACTIONS if itemset <= t)
    return hits / len(TRANSACTIONS)


def measures(antecedent, consequent):
    supp_x = support(antecedent)
    supp_y = support(consequent)
    supp_xy = support(antecedent | consequent)
    conf = supp_xy / supp_x
    lift = conf / supp_y
    leverage = supp_xy - supp_x * supp_y
    # 신뢰도가 1이면 반례가 0건이라 확신도의 분모가 0이 된다 — 정의상 무한대
    conviction = float("inf") if conf == 1 else (1 - supp_y) / (1 - conf)
    return supp_xy, conf, lift, leverage, conviction


def label(itemset):
    return "{" + ",".join(sorted(itemset)) + "}"


def main():
    items = sorted(set().union(*TRANSACTIONS))
    print(f"거래 {len(TRANSACTIONS)}건")
    for i, t in enumerate(TRANSACTIONS, 1):
        print(f"  T{i:<2} {label(t)}")
    print("\n품목별 지지도:", ", ".join(f"{i} {support({i}):.1f}" for i in items))

    frequent = [frozenset(c) for k in (2, 3) for c in combinations(items, k)
                if support(set(c)) >= MIN_SUPPORT]
    print(f"\n빈발 항목집합(지지도 ≥ {MIN_SUPPORT}):",
          ", ".join(f"{label(f)} {support(f):.1f}" for f in frequent))

    print(f"\n규칙 전체 (신뢰도 ≥ {MIN_CONFIDENCE} 이면 '채택')")
    header = f"{'규칙':<18}{'지지도':>6}{'신뢰도':>7}{'향상도':>7}{'레버리지':>8}{'확신도':>7}  판정"
    print(header)
    for itemset in frequent:
        for k in range(1, len(itemset)):
            for lhs in combinations(sorted(itemset), k):
                x = frozenset(lhs)
                y = itemset - x
                s, c, l, lev, conv = measures(x, y)
                verdict = "채택" if c >= MIN_CONFIDENCE else "-"
                if verdict == "채택" and l < 1:
                    verdict += " (향상도 < 1: 음의 연관)"
                rule = f"{label(x)}→{label(y)}"
                print(f"{rule:<18}{s:>7.2f}{c:>8.2f}{l:>8.3f}{lev:>9.2f}{conv:>8.2f}  {verdict}")


if __name__ == "__main__":
    main()
