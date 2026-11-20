"""다치 종속(MVD)과 조인 종속(JD)을 작은 릴레이션에서 직접 검산한다.

1) 4NF 예제 — 과목 →→ 강사 | 교재 를 정의(튜플 존재 조건)와 조인 두 방법으로 판정
2) 두 판정이 언제나 같은가 — 무작위 릴레이션 전부에서 비교 (Fagin 의 무손실 분해 정리)
3) MVD 추론 규칙 4개 + FD 와 섞일 때의 규칙 2개가 반례 없이 성립하는가
4) 성립하지 않는 규칙 — X →→ YZ 이어도 X →→ Y 는 아니다 (반례를 찾아 보인다)
5) 5NF 예제 — 공급자·부품·프로젝트. 어떤 둘로 나눠도 가짜 행이 생기고, 셋으로 나누면 정확히 돌아온다
6) 튜플 하나를 빼면 3-분해 조인 종속도 깨진다
"""
import itertools
import random

RANDOM_SEED = 20261120
RANDOM_TRIALS = 3000


# ── 릴레이션 연산 ──────────────────────────────────────────────
# 릴레이션은 (속성 튜플, 행 집합). 행은 속성 순서대로 값을 담은 튜플이다.

def project(attrs, rows, keep):
    index = [attrs.index(a) for a in keep]
    return tuple(keep), {tuple(row[i] for i in index) for row in rows}


def natural_join(left, right):
    left_attrs, left_rows = left
    right_attrs, right_rows = right
    common = [a for a in left_attrs if a in right_attrs]
    extra = [a for a in right_attrs if a not in left_attrs]
    out_attrs = tuple(left_attrs) + tuple(extra)
    out_rows = set()
    for l_row in left_rows:
        for r_row in right_rows:
            if all(l_row[left_attrs.index(a)] == r_row[right_attrs.index(a)] for a in common):
                out_rows.add(l_row + tuple(r_row[right_attrs.index(a)] for a in extra))
    return out_attrs, out_rows


def reorder(relation, attrs):
    rel_attrs, rows = relation
    return project(rel_attrs, rows, attrs)[1]


def join_of_projections(attrs, rows, components):
    joined = project(attrs, rows, components[0])
    for component in components[1:]:
        joined = natural_join(joined, project(attrs, rows, component))
    return reorder(joined, attrs)


# ── 종속 판정 ──────────────────────────────────────────────────

def jd_holds(attrs, rows, components):
    """*[R1, ..., Rn] — 프로젝션들의 조인이 원래 릴레이션과 같은가."""
    return join_of_projections(attrs, rows, components) == rows


def mvd_by_join(attrs, rows, x, y):
    """X →→ Y 를 *[XY, X(U−Y)] 로 판정한다."""
    xy = [a for a in attrs if a in x or a in y]
    x_rest = [a for a in attrs if a in x or a not in y]
    return jd_holds(attrs, rows, [xy, x_rest])


def mvd_by_definition(attrs, rows, x, y):
    """X →→ Y 를 튜플 존재 조건으로 판정한다.

    t1[X] = t2[X] 인 모든 쌍에 대해 t3[X] = t1[X], t3[Y] = t1[Y],
    t3[U−X−Y] = t2[U−X−Y] 인 t3 가 있어야 한다 (t4 는 t1·t2 를 바꾼 경우).
    """
    xi = [attrs.index(a) for a in attrs if a in x]
    yi = [attrs.index(a) for a in attrs if a in y and a not in x]
    zi = [attrs.index(a) for a in attrs if a not in x and a not in y]
    for t1, t2 in itertools.product(rows, repeat=2):
        if any(t1[i] != t2[i] for i in xi):
            continue
        t3 = [None] * len(attrs)
        for i in xi + yi:
            t3[i] = t1[i]
        for i in zi:
            t3[i] = t2[i]
        if tuple(t3) not in rows:
            return False
    return True


def fd_holds(attrs, rows, x, y):
    seen = {}
    xi = [attrs.index(a) for a in x]
    yi = [attrs.index(a) for a in y]
    for row in rows:
        key = tuple(row[i] for i in xi)
        value = tuple(row[i] for i in yi)
        if seen.setdefault(key, value) != value:
            return False
    return True


def subsets(attrs):
    for size in range(len(attrs) + 1):
        for combo in itertools.combinations(attrs, size):
            yield frozenset(combo)


def is_trivial_mvd(attrs, x, y):
    return y <= x or (x | y) == frozenset(attrs)


def nontrivial_mvds(attrs, rows):
    found = []
    for x in subsets(attrs):
        for y in subsets(attrs):
            if is_trivial_mvd(attrs, x, y) or (y & x):
                continue
            if mvd_by_join(attrs, rows, x, y):
                found.append((x, y))
    return found


def fmt(attr_set):
    return "".join(sorted(attr_set)) or "∅"


def show(title, attrs, rows):
    print(f"  {title}  {len(rows)}행")
    print("    " + " | ".join(attrs))
    for row in sorted(rows):
        print("    " + " | ".join(row))


def random_relation(rng, attrs, domain_size):
    universe = list(itertools.product(*[[f"{a.lower()}{v}" for v in range(domain_size)] for a in attrs]))
    return {row for row in universe if rng.random() < 0.5}


# ── 실행 ───────────────────────────────────────────────────────

def section_4nf():
    print("[1] 4NF 예제 — 강좌(과목 S, 강사 T, 교재 B)")
    attrs = ("S", "T", "B")
    rows = {
        ("db", "kim", "book1"), ("db", "kim", "book2"),
        ("db", "lee", "book1"), ("db", "lee", "book2"),
        ("os", "park", "book3"),
    }
    show("강좌", attrs, rows)
    x, y = frozenset("S"), frozenset("T")
    print(f"  S →→ T  정의로 판정: {mvd_by_definition(attrs, rows, x, y)}"
          f" · 조인으로 판정: {mvd_by_join(attrs, rows, x, y)}")
    print(f"  S →→ B  (상보 규칙)  : {mvd_by_join(attrs, rows, x, frozenset('B'))}")
    fds = [(fmt(l), fmt(r)) for l in subsets(attrs) for r in subsets(attrs)
           if r and not r <= l and fd_holds(attrs, rows, sorted(l), sorted(r - l))
           and len(l) < len(attrs) - 1]
    print(f"  이 인스턴스에서 성립하는 비자명 FD(결정자 1개 이하): {fds or '없음'}")
    print(f"  비자명 MVD 목록: {[(fmt(a), fmt(b)) for a, b in nontrivial_mvds(attrs, rows)]}")
    st = project(attrs, rows, ["S", "T"])
    sb = project(attrs, rows, ["S", "B"])
    show("분해 R1(S,T)", st[0], st[1])
    show("분해 R2(S,B)", sb[0], sb[1])
    back = reorder(natural_join(st, sb), attrs)
    print(f"  R1 ⋈ R2 = 원래 릴레이션? {back == rows}  ({len(back)}행)")

    print("\n[1-2] 강사-교재가 묶여 있으면 (kim 은 book1 만, lee 는 book2 만)")
    tied = {("db", "kim", "book1"), ("db", "lee", "book2"), ("os", "park", "book3")}
    show("강좌'", attrs, tied)
    print(f"  S →→ T  정의: {mvd_by_definition(attrs, tied, x, y)} · 조인: {mvd_by_join(attrs, tied, x, y)}")
    back = reorder(natural_join(project(attrs, tied, ["S", "T"]), project(attrs, tied, ["S", "B"])), attrs)
    print(f"  (S,T)⋈(S,B) = {len(back)}행, 가짜 행: {sorted(back - tied)}")


def section_equivalence(rng):
    print("\n[2] 정의 판정 = 조인 판정인가 — 무작위 릴레이션에서 비교")
    for attrs, domain_size in ((("A", "B", "C"), 2), (("A", "B", "C", "D"), 2)):
        checked = agree = held = 0
        for _ in range(RANDOM_TRIALS):
            rows = random_relation(rng, attrs, domain_size)
            for x in subsets(attrs):
                for y in subsets(attrs):
                    by_def = mvd_by_definition(attrs, rows, x, y)
                    by_join = mvd_by_join(attrs, rows, x, y)
                    checked += 1
                    agree += by_def == by_join
                    held += by_def
        print(f"  U={''.join(attrs)} 값 {domain_size}개씩 · 릴레이션 {RANDOM_TRIALS}개 · "
              f"(X,Y) 판정 {checked}회 · 일치 {agree}회 · MVD 성립 {held}회")


def section_rules(rng):
    print("\n[3] 추론 규칙 — 전제가 성립한 경우마다 결론도 성립하는가 (U=ABCD)")
    attrs = ("A", "B", "C", "D")
    universe = frozenset(attrs)
    every = list(subsets(attrs))
    stats = {name: [0, 0] for name in (
        "MVD0 상보", "MVD1 반사", "MVD2 증가", "MVD3 이행", "FMVD1 변환", "FMVD2 상호작용")}

    def record(name, premise, conclusion):
        if premise:
            stats[name][0] += 1
            stats[name][1] += not conclusion

    for _ in range(400):
        rows = random_relation(rng, attrs, 2)
        mvd = {(x, y): mvd_by_join(attrs, rows, x, y) for x in every for y in every}
        fd = {(x, y): fd_holds(attrs, rows, sorted(x), sorted(y)) for x in every for y in every}
        for x, y in itertools.product(every, repeat=2):
            record("MVD0 상보", mvd[x, y], mvd[x, universe - y])
            record("MVD1 반사", y <= x, mvd[x, y])
            record("FMVD1 변환", fd[x, y], mvd[x, y])
            for z in every:
                record("MVD2 증가", mvd[x, y], mvd[x | z, y | z])
                record("MVD3 이행", mvd[x, y] and mvd[y, z], mvd[x, z - y])
                record("FMVD2 상호작용", mvd[x, y] and fd[x | y, z], fd[x, z - y])
    for name, (premise, broken) in stats.items():
        print(f"  {name:<14} 전제 성립 {premise:>8}회 · 결론 깨짐 {broken}회")


def section_split_counterexample(rng):
    print("\n[4] X →→ YZ 이면 X →→ Y 인가 — 반례 찾기 (U=ABCD, X=A, Y=B, Z=C)")
    attrs = ("A", "B", "C", "D")
    x, y, yz = frozenset("A"), frozenset("B"), frozenset("BC")
    for trial in range(RANDOM_TRIALS):
        rows = random_relation(rng, attrs, 2)
        if mvd_by_join(attrs, rows, x, yz) and not mvd_by_join(attrs, rows, x, y):
            print(f"  {trial + 1}번째 무작위 릴레이션에서 찾음")
            show("반례", attrs, rows)
            print(f"  A →→ BC: {mvd_by_join(attrs, rows, x, yz)} · A →→ B: {mvd_by_join(attrs, rows, x, y)}")
            return
    print("  반례 없음")


def section_5nf():
    print("\n[5] 5NF 예제 — 공급(공급자 S, 부품 P, 프로젝트 J)")
    attrs = ("S", "P", "J")
    rows = {("s1", "p1", "j2"), ("s1", "p2", "j1"), ("s2", "p1", "j1"), ("s1", "p1", "j1")}
    show("공급", attrs, rows)
    print(f"  비자명 MVD 목록: {[(fmt(a), fmt(b)) for a, b in nontrivial_mvds(attrs, rows)] or '없음'}")
    pairs = [["S", "P"], ["P", "J"], ["J", "S"]]
    for a, b in itertools.combinations(pairs, 2):
        back = join_of_projections(attrs, rows, [a, b])
        print(f"  *[{''.join(a)}, {''.join(b)}]  조인 {len(back)}행 · 가짜 행 {sorted(back - rows)}")
    back = join_of_projections(attrs, rows, pairs)
    print(f"  *[SP, PJ, JS] 조인 {len(back)}행 · 가짜 행 {sorted(back - rows)} · 성립 {back == rows}")
    for pair in pairs:
        show(f"분해 {''.join(pair)}", tuple(pair), project(attrs, rows, pair)[1])

    print("\n[6] (s1, p1, j1) 을 빼면")
    smaller = rows - {("s1", "p1", "j1")}
    back = join_of_projections(attrs, smaller, pairs)
    print(f"  *[SP, PJ, JS] 조인 {len(back)}행 · 가짜 행 {sorted(back - smaller)} · 성립 {back == smaller}")


def main():
    rng = random.Random(RANDOM_SEED)
    section_4nf()
    section_equivalence(rng)
    section_rules(rng)
    section_split_counterexample(rng)
    section_5nf()


if __name__ == "__main__":
    main()
