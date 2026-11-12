"""분류 트리의 잎 클래스로 조합표를 만들고 커버리지 기준별 케이스 수를 센다.

예제 명세: 결제 요청 기능
  - 결제 수단: 카드(신용 / 체크) / 계좌이체 / 간편결제   ← 카드 아래 하위 분류
  - 금액: 최소 미만 / 정상 / 한도 초과
  - 할부: 일시불 / 할부
  - 회원 등급: 일반 / 우수
  제약: 할부는 신용카드에서만 된다

1) 전체 조합과 양립 불가 조합 제외
2) 최소 클래스 커버리지 — 잎 클래스마다 한 번 이상
3) pairwise 커버리지 — 서로 다른 두 분류의 클래스 쌍마다 한 번 이상
4) 트리 세분이 없을 때(카드를 한 클래스로 둘 때)와 비교
"""
from itertools import combinations, product

TREE = {
    "결제 수단": ["신용카드", "체크카드", "계좌이체", "간편결제"],
    "금액": ["최소 미만", "정상", "한도 초과"],
    "할부": ["일시불", "할부"],
    "회원 등급": ["일반", "우수"],
}


def is_feasible(case):
    # 의존 규칙: "할부 = 할부 이면 결제 수단 = 신용카드"
    return not (case["할부"] == "할부" and case["결제 수단"] != "신용카드")


def all_cases(tree):
    names = list(tree)
    for values in product(*(tree[n] for n in names)):
        yield dict(zip(names, values))


def feasible_pairs(tree, cases):
    """실현 가능한 조합 안에 실제로 나타나는 (분류, 클래스) 쌍만 커버리지 대상으로 삼는다."""
    pairs = set()
    for case in cases:
        for a, b in combinations(tree, 2):
            pairs.add(((a, case[a]), (b, case[b])))
    return pairs


def pairs_of(tree, case):
    return {((a, case[a]), (b, case[b])) for a, b in combinations(tree, 2)}


def greedy_pairwise(tree, cases):
    """남은 쌍을 가장 많이 덮는 조합을 하나씩 고른다. 같으면 앞선 조합을 고른다."""
    remaining = feasible_pairs(tree, cases)
    chosen = []
    while remaining:
        best = max(cases, key=lambda c: len(pairs_of(tree, c) & remaining))
        chosen.append(best)
        remaining -= pairs_of(tree, best)
    return chosen


def greedy_min_class(tree, cases):
    """아직 안 나온 잎 클래스를 가장 많이 덮는 조합을 하나씩 고른다."""
    remaining = {(n, v) for n in tree for v in tree[n]}
    chosen = []
    while remaining:
        best = max(cases, key=lambda c: len({(n, c[n]) for n in tree} & remaining))
        chosen.append(best)
        remaining -= {(n, best[n]) for n in tree}
    return chosen


def smallest_min_class(tree, cases, start):
    """하한부터 크기를 늘려 가며 잎 클래스를 전부 덮는 첫 조합 묶음을 찾는다."""
    every_class = {(n, v) for n in tree for v in tree[n]}
    for size in range(start, len(cases) + 1):
        for group in combinations(cases, size):
            if {(n, c[n]) for c in group for n in tree} == every_class:
                return list(group)
    return []


def print_cases(tree, cases):
    names = list(tree)
    print("  TC  | " + " | ".join(names))
    for i, case in enumerate(cases, 1):
        print(f"  {i:>3} | " + " | ".join(case[n] for n in names))


def report(title, tree):
    print("=" * 64)
    print(title)
    print("=" * 64)
    sizes = {n: len(v) for n, v in tree.items()}
    print("  잎 클래스 수: " + ", ".join(f"{n} {s}" for n, s in sizes.items()))

    every = list(all_cases(tree))
    feasible = [c for c in every if is_feasible(c)]
    print(f"  전체 조합 {len(every)} · 양립 불가 {len(every) - len(feasible)}"
          f" · 실현 가능 {len(feasible)}")

    min_cases = greedy_min_class(tree, feasible)
    print(f"\n[최소 클래스 커버리지] 하한 {max(sizes.values())}건"
          f" (가장 큰 분류의 클래스 수) · 탐욕 선택 {len(min_cases)}건")
    print_cases(tree, min_cases)
    exact = smallest_min_class(tree, feasible, max(sizes.values()))
    print(f"\n  전수 탐색으로 찾은 최소 {len(exact)}건")
    print_cases(tree, exact)

    pairs = feasible_pairs(tree, feasible)
    names = list(tree)
    largest = max(sizes[a] * sizes[b] for a, b in combinations(names, 2))
    pw_cases = greedy_pairwise(tree, feasible)
    covered = set().union(*(pairs_of(tree, c) for c in pw_cases))
    print(f"\n[pairwise 커버리지] 덮어야 할 쌍 {len(pairs)}개 · 하한 {largest}건"
          f" (두 분류 클래스 수 곱의 최댓값) · 탐욕 선택 {len(pw_cases)}건"
          f" · 덮은 쌍 {len(covered & pairs)}/{len(pairs)}")
    print_cases(tree, pw_cases)

    all_feasible = all(is_feasible(c) for c in min_cases + pw_cases)
    print(f"\n  고른 케이스가 모두 의존 규칙을 지키는가: {all_feasible}")
    print()
    return pw_cases


def main():
    report("1) 카드를 신용/체크로 세분한 트리", TREE)

    flat_tree = dict(TREE)
    flat_tree["결제 수단"] = ["카드", "계좌이체", "간편결제"]
    print("=" * 64)
    print("2) 세분하지 않은 트리 — 카드를 한 클래스로 두면")
    print("=" * 64)
    flat_every = list(all_cases(flat_tree))
    # 세분이 없으면 '카드' 안에 신용·체크가 섞여 있어 할부 제약을 클래스 수준에서 적을 수 없다
    print(f"  전체 조합 {len(flat_every)} · 제외 규칙을 적을 수 없어 전부 후보로 남는다")
    card_installment = [c for c in flat_every
                        if c["결제 수단"] == "카드" and c["할부"] == "할부"]
    print(f"  '카드 + 할부' 조합 {len(card_installment)}건 — 체크카드로 실행하면 실패,"
          " 신용카드로 실행하면 성공. 기대 결과를 하나로 정할 수 없다")


if __name__ == "__main__":
    main()
