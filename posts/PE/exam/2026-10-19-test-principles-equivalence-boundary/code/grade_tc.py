"""학점 처리 모듈 명세에 동등 분할·경계값 분석을 적용해 테스트 케이스를 도출하고 실행한다.

명세
    입력: 점수(score), 정수, 유효 범위 0~100
    출력: 90 이상 'A' / 80~89 'B' / 70~79 'C' / 60~69 'D' / 0~59 'F' / 범위 밖 'ERROR'

기대값은 명세에서 직접 계산하므로(expected_grade) 구현을 참조하지 않는다.
구현이 틀려도 기대값은 흔들리지 않아야 결함이 드러난다.
"""

import sys

VALID_MIN, VALID_MAX = 0, 100

# (이름, 하한, 상한, 기대 출력) — 하한·상한은 포함이고 None 은 끝이 없다는 뜻이다.
PARTITIONS = [
    ("P1 무효(하한 밖)", None, VALID_MIN - 1, "ERROR"),
    ("P2 F", 0, 59, "F"),
    ("P3 D", 60, 69, "D"),
    ("P4 C", 70, 79, "C"),
    ("P5 B", 80, 89, "B"),
    ("P6 A", 90, VALID_MAX, "A"),
    ("P7 무효(상한 밖)", VALID_MAX + 1, None, "ERROR"),
]

# 동등 분할에서 파티션마다 하나씩 고른 대표값. 경계를 피해 안쪽에서 고른다.
EP_REPRESENTATIVES = [-5, 30, 65, 75, 85, 95, 150]


def expected_grade(score: int) -> str:
    """명세가 정한 출력. 테스트 오라클 역할을 한다."""
    for _, low, high, want in PARTITIONS:
        if (low is None or score >= low) and (high is None or score <= high):
            return want
    raise AssertionError(f"파티션이 {score}를 덮지 않는다")


def grade(score: int) -> str:
    """명세대로 구현한 학점 처리 모듈."""
    if score < VALID_MIN or score > VALID_MAX:
        return "ERROR"
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def grade_shifted_boundary(score: int) -> str:
    """결함 D1 — A 의 하한을 >= 90 대신 > 90 으로 써서 경계가 한 칸 밀렸다."""
    if score < VALID_MIN or score > VALID_MAX:
        return "ERROR"
    if score > 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def grade_equality_guard(score: int) -> str:
    """결함 D2 — 상한 검사를 부등호 대신 등호로 써서 101 하나만 걸러낸다."""
    if score < VALID_MIN or score == VALID_MAX + 1:
        return "ERROR"
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def boundary_values() -> list[int]:
    """각 파티션의 최솟값·최댓값. 끝이 없는 쪽은 경계가 아니다."""
    values = set()
    for _, low, high, _want in PARTITIONS:
        values.update(bound for bound in (low, high) if bound is not None)
    return sorted(values)


def two_value_items() -> list[int]:
    """2-value BVA — 경계값과, 인접 파티션에 속하는 최근접 이웃."""
    items = set()
    for bound in boundary_values():
        items.add(bound)
        for neighbor in (bound - 1, bound + 1):
            if expected_grade(neighbor) != expected_grade(bound):
                items.add(neighbor)
    return sorted(items)


def three_value_items() -> list[int]:
    """3-value BVA — 경계값과 양쪽 이웃 모두. 같은 파티션 안쪽 값도 들어온다."""
    items = set()
    for bound in boundary_values():
        items.update({bound - 1, bound, bound + 1})
    return sorted(items)


def run(under_test, inputs: list[int]) -> list[tuple[int, str, str]]:
    """inputs 를 모두 실행하고 기대값과 어긋난 것만 돌려준다."""
    return [
        (value, expected_grade(value), under_test(value))
        for value in inputs
        if under_test(value) != expected_grade(value)
    ]


def main() -> int:
    print(f"Python {sys.version.split()[0]}")
    print()

    print("[동등 분할] 파티션과 대표값")
    print(f"  {'파티션':<18}{'범위':<12}{'기대 출력':<10}{'대표값'}")
    for (name, low, high, want), rep in zip(PARTITIONS, EP_REPRESENTATIVES):
        span = f"{'' if low is None else low}~{'' if high is None else high}"
        print(f"  {name:<18}{span:<12}{want:<10}{rep}")
    print(f"  파티션 {len(PARTITIONS)}개 → 테스트 케이스 {len(EP_REPRESENTATIVES)}건")
    print()

    suites = {
        "동등 분할": EP_REPRESENTATIVES,
        "2-value BVA": two_value_items(),
        "3-value BVA": three_value_items(),
    }
    print("[경계값 분석] 커버리지 아이템")
    print(f"  경계값      {len(boundary_values()):>2}개: {boundary_values()}")
    print(f"  2-value     {len(suites['2-value BVA']):>2}개: {suites['2-value BVA']}")
    print(f"  3-value     {len(suites['3-value BVA']):>2}개: {suites['3-value BVA']}")
    print()

    targets = {
        "정상 구현": grade,
        "D1 경계 밀림(> 90)": grade_shifted_boundary,
        "D2 등호 검사(== 101)": grade_equality_guard,
    }
    print("[실행] 기법별 결함 검출")
    print(f"  {'대상':<22}{'동등 분할':<12}{'2-value BVA':<14}{'3-value BVA'}")
    details = []
    for target_name, under_test in targets.items():
        cells = []
        for suite_name, inputs in suites.items():
            failures = run(under_test, inputs)
            cells.append("검출" if failures else "통과")
            for value, want, got in failures:
                details.append(f"{target_name} / {suite_name}: score={value} 기대 {want} 실제 {got}")
        print(f"  {target_name:<22}{cells[0]:<12}{cells[1]:<14}{cells[2]}")
    print()

    print("[실행] 어긋난 케이스")
    for line in details:
        print(f"  {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
