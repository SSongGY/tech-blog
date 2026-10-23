"""MC/DC 의 독립 영향 쌍과 최소 케이스 수를 전수 계산으로 확인한다.

NASA/TM-2001-210876 이 부록 B 표 1 에 실은 Z = (A or B) and (C or D) 의
독립 영향 쌍, 본문 2.3.5 절의 "입력 n 개면 최소 n+1 개", 부록 B 의
논리 연산자별 최소 테스트 집합을 각각 계산해 문서의 값과 맞춰 본다.
"""

import itertools
import platform

CONDITIONS = "ABCD"

# 식을 트리로 둔다. ('var', 이름) / ('and'|'or'|'xor', 왼쪽, 오른쪽) / ('not', 자식)
EXPR = ("and", ("or", ("var", "A"), ("var", "B")),
               ("or", ("var", "C"), ("var", "D")))


def evaluate(node, env):
    kind = node[0]
    if kind == "var":
        return env[node[1]]
    if kind == "not":
        return not evaluate(node[1], env)
    left, right = evaluate(node[1], env), evaluate(node[2], env)
    if kind == "and":
        return left and right
    if kind == "or":
        return left or right
    return left != right  # xor


def leaves(node):
    if node[0] == "var":
        return {node[1]}
    return set().union(*(leaves(child) for child in node[1:]))


def propagates(node, env, target):
    """target 조건의 값이 node 의 출력까지 전달되는가 (마스킹되지 않았는가).

    and 게이트는 나머지 입력이 전부 참일 때만, or 게이트는 나머지 입력이
    전부 거짓일 때만 한 입력의 변화가 출력에 나타난다. xor 는 언제나 나타난다.
    """
    if node[0] == "var":
        return node[1] == target
    if node[0] == "not":
        return propagates(node[1], env, target)
    for i, other in ((1, 2), (2, 1)):
        if target in leaves(node[i]):
            if not propagates(node[i], env, target):
                return False
            if node[0] == "and":
                return evaluate(node[other], env)
            if node[0] == "or":
                return not evaluate(node[other], env)
            return True  # xor
    return False


def truth_table(names, node):
    """1번부터 번호를 매긴 진리표. F=0, T=1 로 세는 순서라 문서의 표와 같다."""
    rows = []
    for i, combo in enumerate(itertools.product([False, True], repeat=len(names)), 1):
        env = dict(zip(names, combo))
        rows.append((i, env, evaluate(node, env)))
    return rows


def unique_cause_pairs(rows, names, target):
    """해당 조건만 다르고 결과도 다른 두 케이스. DO-178B 용어집의 정의 그대로."""
    pairs = []
    for (i, e1, z1), (j, e2, z2) in itertools.combinations(rows, 2):
        if z1 == z2 or e1[target] == e2[target]:
            continue
        if all(e1[n] == e2[n] for n in names if n != target):
            pairs.append((i, j))
    return pairs


def masking_pairs(rows, node, target):
    """양쪽 모두에서 그 조건이 마스킹되지 않고 결과가 갈리는 두 케이스."""
    pairs = []
    for (i, e1, z1), (j, e2, z2) in itertools.combinations(rows, 2):
        if z1 == z2 or e1[target] == e2[target]:
            continue
        if propagates(node, e1, target) and propagates(node, e2, target):
            pairs.append((i, j))
    return pairs


def smallest_covering_set(rows, names, pairs_by_condition):
    """모든 조건의 독립 영향 쌍을 하나씩 품는 가장 작은 케이스 집합."""
    numbers = [i for i, _env, _z in rows]
    for size in range(2, len(numbers) + 1):
        for subset in itertools.combinations(numbers, size):
            chosen = set(subset)
            if all(any(a in chosen and b in chosen for a, b in pairs_by_condition[n])
                   for n in names):
                return subset
    return None


def operator_minimum_sets(kind):
    """2입력 연산자에서 두 입력 모두의 독립 영향을 보이는 최소 집합을 전부 찾는다."""
    node = (kind, ("var", "A"), ("var", "B"))
    rows = truth_table("AB", node)
    found = []
    for subset in itertools.combinations(rows, 3):
        picked = [(i, env, z) for i, env, z in subset]
        ok = all(unique_cause_pairs(picked, "AB", n) for n in "AB")
        if ok:
            found.append(tuple("".join("T" if env[n] else "F" for n in "AB")
                               for _i, env, _z in picked))
    return found


def main():
    print(f"Python {platform.python_version()}")
    print()

    rows = truth_table(CONDITIONS, EXPR)
    print("[1] Z = (A or B) and (C or D) 의 진리표")
    print("  번호   A B C D   Z")
    for i, env, z in rows:
        values = " ".join("T" if env[n] else "F" for n in CONDITIONS)
        print(f"  {i:>4}   {values}   {'T' if z else 'F'}")
    print()

    unique = {n: unique_cause_pairs(rows, CONDITIONS, n) for n in CONDITIONS}
    masking = {n: masking_pairs(rows, EXPR, n) for n in CONDITIONS}
    print("[2] 조건별 독립 영향 쌍")
    for n in CONDITIONS:
        extra = sorted(set(masking[n]) - set(unique[n]))
        print(f"  {n}: 유일 원인 {unique[n]}")
        print(f"     마스킹에서만 추가로 성립 {extra if extra else '없음'}")
    print()

    smallest_unique = smallest_covering_set(rows, CONDITIONS, unique)
    smallest_masking = smallest_covering_set(rows, CONDITIONS, masking)
    print("[3] 최소 케이스 수 — 입력 4개")
    print(f"  유일 원인 MC/DC 최소 집합 {smallest_unique} → {len(smallest_unique)}개")
    print(f"  마스킹 MC/DC 최소 집합  {smallest_masking} → {len(smallest_masking)}개")
    print(f"  n+1 = {len(CONDITIONS) + 1}, 다중 조건 커버리지 2^n = {2 ** len(CONDITIONS)}")
    print()

    print("[4] 2입력 연산자별 최소 테스트 집합 (Chilenski·Miller)")
    for kind in ("and", "or", "xor"):
        sets = operator_minimum_sets(kind)
        shown = "; ".join("(" + ", ".join(s) + ")" for s in sets)
        print(f"  {kind:<4} {len(sets)}가지 — {shown}")
    print()

    print("[5] 조건 수에 따른 케이스 수")
    print("   n   MC/DC 최소(n+1)   다중 조건 커버리지(2^n)")
    for n in (2, 4, 8, 16, 36):
        print(f"  {n:>2}   {n + 1:>13,}   {2 ** n:>22,}")


if __name__ == "__main__":
    main()
