"""FODA 피처 모델의 규칙으로 유효한 제품 구성을 세고, 부분 선택을 전파한다.

규칙의 근거 (Kang 외, CMU/SEI-90-TR-21, 1990):
- 피처 종류 3가지: 필수(mandatory)·선택(optional)·대안(alternative) — 5.1.2
- 대안은 "둘 이상 고를 수 없다" — 5.1.2, 도구는 "적어도 하나"를 강제 — 7.3.2.6
- 조합 규칙 2가지: requires, mutex-with — 7.3.2.2

1) FODA 자동차 예(그림 5-1)의 유효 구성 수
2) 부분 선택(에어컨, 수동)에서 무엇이 함께 정해지는지 — 7.3.2.6 도구 규칙
3) 독립 선택 피처 10개에 조합 규칙을 하나씩 더할 때 구성 수
"""
from itertools import product

# 그림 5-1 의 Horsepower 는 값 피처라 조합 규칙 "Horsepower > 100" 을 세려면 값을 나눠야 한다.
# 여기서는 설명을 위해 '100 이하'·'100 초과' 두 대안으로 나눴다 (원 그림에는 없는 분할).
CAR_FEATURES = {
    # 이름: (부모, 종류)
    "transmission": ("car", "mandatory"),
    "horsepower": ("car", "mandatory"),
    "air_conditioning": ("car", "optional"),
    "manual": ("transmission", "alternative"),
    "automatic": ("transmission", "alternative"),
    "hp_100_or_less": ("horsepower", "alternative"),
    "hp_over_100": ("horsepower", "alternative"),
}
CAR_REQUIRES = [("air_conditioning", "hp_over_100")]
CAR_MUTEX = []


def violations(selected, features, requires, mutex, root="car"):
    """구성 하나가 어기는 규칙을 모두 돌려준다. 빈 목록이면 유효하다."""
    found = []
    if root not in selected:
        found.append("root")
    for name, (parent, kind) in features.items():
        if name in selected and parent not in selected:
            found.append(f"{name}: 부모 {parent} 없음")
        if kind == "mandatory" and parent in selected and name not in selected:
            found.append(f"{name}: 필수인데 빠짐")
    parents = {p for p, k in features.values() if k == "alternative"}
    for parent in parents:
        if parent not in selected:
            continue
        chosen = [n for n, (p, k) in features.items()
                  if p == parent and k == "alternative" and n in selected]
        if len(chosen) != 1:
            found.append(f"{parent}: 대안 {len(chosen)}개 선택")
    for a, b in requires:
        if a in selected and b not in selected:
            found.append(f"{a} requires {b}")
    for a, b in mutex:
        if a in selected and b in selected:
            found.append(f"{a} mutex-with {b}")
    return found


def enumerate_configs(features, requires, mutex, root="car"):
    names = list(features)
    valid, rejected = [], {}
    for bits in product((False, True), repeat=len(names)):
        selected = {root} | {n for n, on in zip(names, bits) if on}
        problems = violations(selected, features, requires, mutex, root)
        if problems:
            for p in problems:
                key = p.split(":")[0] if ":" in p else p
                rejected[key] = rejected.get(key, 0) + 1
        else:
            valid.append(sorted(selected - {root}))
    return valid, rejected


def propagate(marked, features, requires, mutex, root="car"):
    """7.3.2.6 의 도구처럼 표시한 피처에서 '유효'·'무효'를 퍼뜨린다."""
    valid = {root} | set(marked)
    changed = True
    while changed:
        changed = False
        for name, (parent, kind) in features.items():
            # 부모가 있어야 자식이 있다 / 유효한 부모의 필수 자식은 유효
            if name in valid and parent not in valid:
                valid.add(parent)
                changed = True
            if kind == "mandatory" and parent in valid and name not in valid:
                valid.add(name)
                changed = True
        for a, b in requires:
            if a in valid and b not in valid:
                valid.add(b)
                changed = True
    invalid = set()
    for a, b in mutex:
        if a in valid:
            invalid.add(b)
        if b in valid:
            invalid.add(a)
    for name, (parent, kind) in features.items():
        if kind == "alternative" and name in valid:
            # 대안은 둘 이상 고를 수 없으므로 형제 대안은 무효가 된다
            invalid |= {n for n, (p, k) in features.items()
                        if p == parent and k == "alternative" and n != name}
    return sorted(valid - {root}), sorted(invalid), sorted(valid & invalid)


def main():
    print("[1] FODA 자동차 예 — 원시 조합과 유효 구성")
    names = list(CAR_FEATURES)
    print(f"    비루트 피처 {len(names)}개 -> 원시 조합 {2 ** len(names)}개")
    valid, _ = enumerate_configs(CAR_FEATURES, [], CAR_MUTEX)
    print(f"    구조 규칙만 적용      -> 유효 {len(valid)}개")
    valid, rejected = enumerate_configs(CAR_FEATURES, CAR_REQUIRES, CAR_MUTEX)
    print(f"    + requires 1개 적용   -> 유효 {len(valid)}개")
    for config in valid:
        print("     ", config)

    print("\n[2] 부분 선택 전파 — 고객이 에어컨과 수동 변속기만 골랐다")
    chosen, blocked, conflict = propagate(
        {"air_conditioning", "manual"}, CAR_FEATURES, CAR_REQUIRES, CAR_MUTEX)
    print("    유효로 정해짐:", chosen)
    print("    무효로 정해짐:", blocked)
    print("    충돌:", conflict or "없음")
    print("  같은 고객이 '100 이하' 엔진까지 고르면")
    chosen, blocked, conflict = propagate(
        {"air_conditioning", "manual", "hp_100_or_less"},
        CAR_FEATURES, CAR_REQUIRES, CAR_MUTEX)
    print("    충돌:", conflict or "없음")

    print("\n[3] 독립 선택 피처 10개 (f0..f9) 에 조합 규칙을 더할 때")
    features = {f"f{i}": ("root", "optional") for i in range(10)}
    cases = [
        ("규칙 없음", [], []),
        ("f0 requires f1", [("f0", "f1")], []),
        ("f2 mutex-with f3", [], [("f2", "f3")]),
        ("둘 다", [("f0", "f1")], [("f2", "f3")]),
        ("f0 requires f1, f1 requires f2", [("f0", "f1"), ("f1", "f2")], []),
    ]
    for label, requires, mutex in cases:
        valid, _ = enumerate_configs(features, requires, mutex, root="root")
        print(f"    {label:<32} 유효 {len(valid):>5}개")


if __name__ == "__main__":
    main()
