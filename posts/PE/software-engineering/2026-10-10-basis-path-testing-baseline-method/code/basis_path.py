"""기본 경로 테스트(구조적 테스트)의 4단계를 NIST SP 500-235 의 예제 모듈로 따라간다.

1) 제어 흐름 그래프 작성 2) V(G) 계산 3) 기준 경로 방법으로 기본 경로 선택
4) 경로마다 입력과 기대 출력을 정해 실행. 분기 커버리지 100% 인 테스트 집합이
기본 경로 집합보다 약하다는 것과, 실행 불가능한 경로가 있으면 랭크가 V(G) 에
못 미친다는 것도 함께 계산한다. 외부 의존성 없이 표준 라이브러리만 쓴다.
"""

import itertools
import platform
import sys
from fractions import Fraction


def branch(trace, name, outcome):
    # 판단을 지날 때마다 (판단 이름, 결과)를 남긴다. 경로는 이 기록으로 복원한다.
    trace.append((name, bool(outcome)))
    return outcome


# ---------------------------------------------------------------- 대상 모듈

def count(text, trace):
    """NIST 문서 5.4절의 C 모듈 count 를 파이썬으로 옮긴 것.

    명세: 문자열이 'A' 로 시작하면 'C' 의 개수를, 아니면 -1 을 돌려준다.
    결함: 'B' 와 'C' 를 알아보는 두 분기의 본문이 뒤바뀌어 'B' 를 센다.
    """
    chars = text + "\0"
    index = 0
    counted = other = 0
    if branch(trace, "=A", chars[index] == "A"):
        while True:
            index += 1
            if branch(trace, "=B", chars[index] == "B"):
                counted += 1
                continue
            if branch(trace, "=C", chars[index] == "C"):
                other += 1
                continue
            if branch(trace, "!=NUL", chars[index] != "\0"):
                continue
            return counted
    return -1


def count_spec(text):
    return text.count("C") if text.startswith("A") else -1


# 노드 -> 다음 노드. 판단 노드는 (판단 이름, 참일 때, 거짓일 때)
COUNT_CFG = {
    "entry": "dA",
    "dA": ("=A", "inc", "ret_neg"),
    "inc": "dB",
    "dB": ("=B", "b_body", "dC"),
    "b_body": "inc",
    "dC": ("=C", "c_body", "dNul"),
    "c_body": "inc",
    "dNul": ("!=NUL", "inc", "ret_cnt"),
    "ret_cnt": "exit",
    "ret_neg": "exit",
    "exit": None,
}


def classify(n, trace):
    # 세 판단이 같은 값을 다른 각도로 묻는다. 어느 입력이든 참은 정확히 하나다.
    kind = None
    if branch(trace, "n<0", n < 0):
        kind = "음수"
    if branch(trace, "n==0", n == 0):
        kind = "영"
    if branch(trace, "n>0", n > 0):
        kind = "양수"
    return kind


CLASSIFY_CFG = {
    "entry": "d1",
    "d1": ("n<0", "s1", "d2"),
    "s1": "d2",
    "d2": ("n==0", "s2", "d3"),
    "s2": "d3",
    "d3": ("n>0", "s3", "ret"),
    "s3": "ret",
    "ret": "exit",
    "exit": None,
}


def classify2(n, trace):
    if branch(trace, "n<0", n < 0):
        return "음수"
    if branch(trace, "n==0", n == 0):
        return "영"
    return "양수"


CLASSIFY2_CFG = {
    "entry": "d1",
    "d1": ("n<0", "s1", "d2"),
    "s1": "ret",
    "d2": ("n==0", "s2", "s3"),
    "s2": "ret",
    "s3": "ret",
    "ret": "exit",
    "exit": None,
}


# ---------------------------------------------------------------- 그래프 계산

def edges_of(cfg):
    result = []
    for node, nxt in cfg.items():
        if nxt is None:
            continue
        if isinstance(nxt, tuple):
            result.append((node, nxt[1]))
            result.append((node, nxt[2]))
        else:
            result.append((node, nxt))
    return result


def decision_nodes(cfg):
    return [node for node, nxt in cfg.items() if isinstance(nxt, tuple)]


def walk(cfg, trace):
    """판단 기록을 따라 그래프를 걸어 지나간 간선 목록을 만든다."""
    node, outcomes, path = "entry", iter(trace), []
    while cfg[node] is not None:
        nxt = cfg[node]
        if isinstance(nxt, tuple):
            name, outcome = next(outcomes)
            assert name == nxt[0], (name, nxt[0])
            target = nxt[1] if outcome else nxt[2]
        else:
            target = nxt
        path.append((node, target))
        node = target
    return path


def edge_vector(cfg, trace):
    # NIST 2.3절: 경로마다 간선 수만큼의 원소를 두고, 각 원소는 그 간선을 지난 횟수다.
    order = edges_of(cfg)
    path = walk(cfg, trace)
    return [path.count(edge) for edge in order]


def rank(vectors):
    rows = [[Fraction(v) for v in vec] for vec in vectors]
    result, col = 0, 0
    width = len(rows[0]) if rows else 0
    while result < len(rows) and col < width:
        pivot = next((r for r in range(result, len(rows)) if rows[r][col] != 0), None)
        if pivot is None:
            col += 1
            continue
        rows[result], rows[pivot] = rows[pivot], rows[result]
        for r in range(len(rows)):
            if r != result and rows[r][col] != 0:
                factor = rows[r][col] / rows[result][col]
                rows[r] = [a - factor * b for a, b in zip(rows[r], rows[result])]
        result += 1
        col += 1
    return result


def trace_of(module, value):
    trace = []
    module(value, trace)
    return trace


def show_trace(trace):
    return " ".join(f"{name}{'T' if outcome else 'F'}" for name, outcome in trace)


# ---------------------------------------------------------------- 기준 경로 방법

def is_suffix(tail, whole):
    return len(tail) <= len(whole) and whole[len(whole) - len(tail):] == tail


def baseline_method(module, cfg, baseline_input, candidates):
    """NIST 6.3절의 기준 경로 방법.

    기준 경로의 판단을 앞에서부터 하나씩 뒤집는다. 뒤집은 판단 앞은 기준 경로를 그대로
    따르고, 뒤집은 뒤에는 기준 경로에 다시 합류해 끝까지 따른다. 기준 경로의 판단을
    다 뒤집으면 새로 생긴 경로에서 아직 안 뒤집은 판단을 같은 방식으로 뒤집는다.
    """
    traces = {value: trace_of(module, value) for value in candidates}
    chosen = [(baseline_input, traces[baseline_input], "기준 경로")]
    flipped = set()
    cursor = 0
    while cursor < len(chosen):
        _, parent, _ = chosen[cursor]
        for position, (name, outcome) in enumerate(parent):
            if name in flipped:
                continue
            # 반복 때문에 같은 판단을 다시 만나면 첫 번째 만남만 뒤집는다 (NIST 6.4절)
            if any(prev == name for prev, _ in parent[:position]):
                continue
            flipped.add(name)
            prefix = parent[:position] + [(name, not outcome)]
            rejoin = [v for v, t in traces.items()
                      if t[:len(prefix)] == prefix and is_suffix(t[len(prefix):], parent)]
            if not rejoin:
                continue
            value = min(rejoin, key=lambda v: (len(v), v))
            chosen.append((value, traces[value], f"{name} 를 {'F' if outcome else 'T'} 로 뒤집음"))
        cursor += 1
    return chosen


# ---------------------------------------------------------------- 실행

def coverage(cfg, traces):
    outcomes = {(n, o) for t in traces for n, o in t}
    total_outcomes = 2 * len(decision_nodes(cfg))
    nodes = {node for t in traces for edge in walk(cfg, t) for node in edge}
    return len(outcomes), total_outcomes, len(nodes), len(cfg)


def main():
    print(f"Python {platform.python_version()} / {platform.system()}")
    candidates = ["".join(p) for size in range(5) for p in itertools.product("ABCX", repeat=size)]
    print(f"후보 입력: 'A','B','C','X' 로 만든 길이 0~4 문자열 {len(candidates)}개")

    print("\n[1] 1단계 — 제어 흐름 그래프 (count)")
    for node, nxt in COUNT_CFG.items():
        if isinstance(nxt, tuple):
            print(f"  {node:<8} 판단 {nxt[0]:<6} T→{nxt[1]:<8} F→{nxt[2]}")
        elif nxt is not None:
            print(f"  {node:<8} → {nxt}")

    print("\n[2] 2단계 — V(G) 계산")
    edge_total, node_total = len(edges_of(COUNT_CFG)), len(COUNT_CFG)
    predicates = len(decision_nodes(COUNT_CFG))
    print(f"  E − N + 2 = {edge_total} − {node_total} + 2 = {edge_total - node_total + 2}")
    print(f"  판단 수 + 1 = {predicates} + 1 = {predicates + 1}")
    everything = [edge_vector(COUNT_CFG, trace_of(count, v)) for v in candidates]
    distinct = {tuple(v) for v in everything}
    print(f"  후보 {len(candidates)}개가 만든 서로 다른 경로 {len(distinct)}개, 그 경로 행렬의 랭크 {rank(list(distinct))}")

    print("\n[3] 3단계 — 기준 경로 방법 (기준 입력 'AB')")
    basis = baseline_method(count, COUNT_CFG, "AB", candidates)
    for i, (value, trace, note) in enumerate(basis, 1):
        print(f"  경로 {i}: 입력 {value!r:<7} {note:<18} {show_trace(trace)}")
    vectors = [edge_vector(COUNT_CFG, t) for _, t, _ in basis]
    print(f"  경로 {len(basis)}개의 랭크 {rank(vectors)}  (V(G) 와 같으면 기본 경로 집합)")

    print("\n[4] 4단계 — 입력·기대 출력을 정해 실행")
    print(f"  {'입력':<8}{'기대':>5}{'실제':>5}  판정")
    for value, _, _ in basis:
        actual, expected = count(value, []), count_spec(value)
        print(f"  {value!r:<8}{expected:>5}{actual:>5}  {'통과' if actual == expected else '결함 발견'}")

    print("\n[5] 비교 — 분기 커버리지를 채우는 테스트 2개 (NIST 그림 5-4 의 입력)")
    branch_set = ["X", "ABCX"]
    traces = [trace_of(count, v) for v in branch_set]
    done_out, total_out, done_nodes, total_nodes = coverage(COUNT_CFG, traces)
    print(f"  판단 결과 {done_out}/{total_out} · 노드 {done_nodes}/{total_nodes} 를 지난다")
    for value in branch_set:
        print(f"  {value!r:<8} 기대 {count_spec(value):>3}  실제 {count(value, []):>3}")
    current = [edge_vector(COUNT_CFG, t) for t in traces]
    print(f"  경로 랭크 {rank(current)} — 기본 경로 기준까지 {5 - rank(current)}개 모자란다")

    print("\n[6] 기능 테스트를 기본 경로로 채우기 (NIST 6.5절)")
    added = []
    for value, trace, _ in basis:
        vec = edge_vector(COUNT_CFG, trace)
        if rank(current + [vec]) > rank(current):
            current.append(vec)
            added.append(value)
    print(f"  추가한 입력 {added} → 랭크 {rank(current)}")
    found = [v for v in added if count(v, []) != count_spec(v)]
    print(f"  추가분 중 결함을 드러낸 입력: {found}")

    print("\n[7] 분기 커버리지 100% 인 2개짜리 집합 중 결함을 놓치는 것")
    # 길이 4 까지는 판단 결과 8개를 다 지나는 문자열이 B·C 를 하나씩만 가지므로 길이 5 까지 본다
    longer = ["".join(p) for size in range(6) for p in itertools.product("ABCX", repeat=size)]
    outcome_sets = {v: frozenset(trace_of(count, v)) for v in longer}
    correct = {v: count(v, []) == count_spec(v) for v in longer}
    full_cover = miss = 0
    for a, b in itertools.combinations(longer, 2):
        if len(outcome_sets[a] | outcome_sets[b]) == 8:
            full_cover += 1
            if correct[a] and correct[b]:
                miss += 1
    print(f"  길이 0~5 입력 {len(longer)}개로 만든 쌍 중 분기 커버리지 100% 쌍 {full_cover}개, "
          f"그중 결함을 놓치는 쌍 {miss}개 ({miss / full_cover:.1%})")
    # 경로가 같으면 판단 결과의 순서가 같고, count 에서는 그것이 B·C 개수까지 정하므로
    # 경로마다 가장 짧은 입력 하나만 대표로 둔다.
    short = [v for v in candidates if len(v) <= 3]
    representative = {}
    for value in short:
        key = tuple(edge_vector(COUNT_CFG, trace_of(count, value)))
        representative.setdefault(key, value)
    basis_sets = miss_basis = 0
    for combo in itertools.combinations(list(representative.items()), 5):
        if rank([list(key) for key, _ in combo]) == 5:
            basis_sets += 1
            if all(count(v, []) == count_spec(v) for _, v in combo):
                miss_basis += 1
    print(f"  길이 0~3 입력의 서로 다른 경로 {len(representative)}개로 만들 수 있는 기본 경로 집합 "
          f"{basis_sets}개 중 결함을 놓치는 집합 {miss_basis}개")

    print("\n[8] 실행 불가능한 경로 — 같은 값을 세 번 묻는 classify")
    for name, module, cfg in (("classify ", classify, CLASSIFY_CFG), ("classify2", classify2, CLASSIFY2_CFG)):
        vg = len(edges_of(cfg)) - len(cfg) + 2
        vecs = {tuple(edge_vector(cfg, trace_of(module, n))) for n in range(-5, 6)}
        print(f"  {name}  V(G)={vg}  입력 -5~5 의 서로 다른 경로 {len(vecs)}개  실현 가능한 랭크 {rank(list(vecs))}")
    for n in (-1, 0, 1):
        print(f"    classify({n:>2}): {show_trace(trace_of(classify, n))}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
