"""k-익명성·ℓ-다양성·t-근접성을 가상 데이터로 직접 계산한다.

각 모델이 막는 공격과 막지 못하는 공격을 숫자로 보이려는 것이다. 데이터는 전부
지어낸 것이고 실제 인물·기관과 관계없다. 외부 의존성 없이 표준 라이브러리만 쓴다.
"""

from collections import Counter, defaultdict
from fractions import Fraction

# 데이터 1 — 의료 기록 12건. 이름은 이미 지웠고 준식별자(우편번호·나이·성별)가 남아 있다
MEDICAL = [
    # (record_id, zip_code, age, sex, disease)
    (1, "30121", 24, "남", "전립선비대증"),
    (2, "30125", 27, "여", "고혈압"),
    (3, "30128", 22, "남", "전립선비대증"),
    (4, "30121", 28, "남", "고혈압"),
    (5, "30521", 45, "여", "당뇨"),
    (6, "30524", 52, "남", "독감"),
    (7, "30527", 48, "여", "기관지염"),
    (8, "30521", 57, "남", "갑상선염"),
    (9, "30125", 33, "남", "위암"),
    (10, "30128", 36, "여", "위암"),
    (11, "30121", 31, "남", "위암"),
    (12, "30125", 38, "여", "위암"),
]

# 공격자가 따로 구할 수 있는 공개 명부 — 이름과 준식별자만 있다
PUBLIC_ROSTER = [
    ("가람", "30121", 24, "남"), ("나래", "30125", 27, "여"), ("다솜", "30128", 22, "남"),
    ("라온", "30121", 28, "남"), ("마루", "30521", 45, "여"), ("바다", "30524", 52, "남"),
    ("사랑", "30527", 48, "여"), ("아라", "30521", 57, "남"), ("자람", "30125", 33, "남"),
    ("차오", "30128", 36, "여"), ("하늘", "30121", 31, "남"), ("한결", "30125", 38, "여"),
]

# 데이터 2 — 급여(백만 원)와 질병 9건. ℓ-다양성의 한계와 t-근접성을 본다
SALARY = [
    # (record_id, zip_code, age, salary, disease)
    (1, "47671", 29, 30, "위궤양"),
    (2, "47602", 22, 40, "역류성식도염"),
    (3, "47673", 27, 50, "위염"),
    (4, "47905", 43, 60, "위염"),
    (5, "47909", 52, 110, "독감"),
    (6, "47906", 47, 80, "기관지염"),
    (7, "47605", 30, 70, "기관지염"),
    (8, "47675", 36, 90, "폐렴"),
    (9, "47607", 32, 100, "위염"),
]


def decade(age: int) -> str:
    return "40~59" if age >= 40 else f"{age // 10 * 10}대"


def group_by(rows, key_func) -> dict:
    classes = defaultdict(list)
    for row in rows:
        classes[key_func(row)].append(row)
    return dict(classes)


def k_value(classes: dict) -> int:
    return min(len(members) for members in classes.values())


def distinct_l(members, sensitive_index: int) -> int:
    return len({row[sensitive_index] for row in members})


def ordered_emd(class_values, all_values) -> Fraction:
    """Li 외(2007) 5.1절의 ordered distance EMD. 값 사이 거리를 순위 차/(m-1)로 둔다."""
    domain = sorted(set(all_values))
    m = len(domain)
    p = Counter(class_values)
    q = Counter(all_values)
    running = Fraction(0)
    total = Fraction(0)
    for value in domain[:-1]:
        running += Fraction(p[value], len(class_values)) - Fraction(q[value], len(all_values))
        total += abs(running)
    return total / (m - 1)


def equal_emd(class_values, all_values) -> Fraction:
    """5.2절의 equal distance EMD. 범주끼리 거리를 모두 1로 보면 변동 거리의 절반이 된다."""
    p = Counter(class_values)
    q = Counter(all_values)
    return sum(
        abs(Fraction(p[v], len(class_values)) - Fraction(q[v], len(all_values)))
        for v in set(all_values)
    ) / 2


def show_classes(title: str, classes: dict, sensitive_index: int) -> None:
    print(f"\n-- {title}")
    for key, members in classes.items():
        ids = ",".join(str(row[0]) for row in members)
        values = [row[sensitive_index] for row in members]
        print(f"   {key}  행 {ids:<10} 크기 {len(members)}  ℓ={distinct_l(members, sensitive_index)}  민감정보 {values}")
    print(f"   => k = {k_value(classes)}")


def main() -> None:
    print("== 1. 이름을 지워도 준식별자로 다시 붙는다 (연결 공격) ==")
    qi_counts = Counter((row[1], row[2], row[3]) for row in MEDICAL)
    unique = sum(1 for count in qi_counts.values() if count == 1)
    print(f"   (우편번호, 나이, 성별) 조합이 유일한 행: {unique} / {len(MEDICAL)}")
    linked = 0
    for name, zip_code, age, sex in PUBLIC_ROSTER:
        hits = [row for row in MEDICAL if (row[1], row[2], row[3]) == (zip_code, age, sex)]
        if len(hits) == 1:
            linked += 1
            if name in ("나래", "자람"):
                print(f"   명부의 {name}({zip_code}, {age}, {sex}) -> 기록 {hits[0][0]}번 -> {hits[0][4]}")
    print(f"   명부 이름과 1:1로 이어진 기록: {linked} / {len(MEDICAL)}")

    print("\n== 2. 일반화 A — 우편번호 앞 3자리, 나이 구간, 성별 삭제 ==")
    release_a = group_by(MEDICAL, lambda r: (r[1][:3] + "**", decade(r[2])))
    show_classes("동질 집합", release_a, 4)
    print("   공개 명부로 다시 붙이면 각 이름이 4행 중 하나로만 좁혀진다 (재식별 확률 1/4)")

    print("\n== 3. k=4 인데도 드러나는 것 ==")
    target = ("301**", "30대")
    print(f"   동질성 공격: 자람(30125, 33, 남)은 {target} 집합 -> 질병 {sorted({r[4] for r in release_a[target]})}")
    target = ("301**", "20대")
    diseases = sorted({r[4] for r in release_a[target]})
    print(f"   배경지식 공격: 나래(30125, 27, 여)는 {target} 집합 -> 후보 {diseases}")
    print("                  '전립선비대증은 여성에게 없다'를 알면 -> 고혈압")

    print("\n== 4. 두 번 공개하면 (합성 공격) ==")
    release_b = group_by(MEDICAL, lambda r: (r[3], "20~39" if r[2] < 40 else "40~59"))
    show_classes("일반화 B — 성별 유지, 나이 20년 구간, 우편번호 삭제", release_b, 4)
    revealed = []
    for row in MEDICAL:
        set_a = {r[4] for r in release_a[(row[1][:3] + "**", decade(row[2]))]}
        set_b = {r[4] for r in release_b[(row[3], "20~39" if row[2] < 40 else "40~59")]}
        both = set_a & set_b
        if len(both) == 1:
            revealed.append((row[0], next(iter(both))))
    print(f"   A 와 B 의 후보 질병 교집합이 1개로 좁혀지는 사람: {len(revealed)} / {len(MEDICAL)}")
    print(f"   {revealed}")

    print("\n== 5. ℓ-다양성을 채워도 남는 것 (유사성·쏠림) ==")
    salaries = [row[3] for row in SALARY]
    diseases_all = [row[4] for row in SALARY]
    release_c = group_by(SALARY, lambda r: (r[1][:3] + "**", "40~59" if r[2] >= 40 else f"{r[2] // 10 * 10}대"))
    show_classes("일반화 C — 우편번호 앞 3자리, 나이 구간", release_c, 4)
    for key, members in release_c.items():
        t_salary = ordered_emd([r[3] for r in members], salaries)
        t_disease = equal_emd([r[4] for r in members], diseases_all)
        print(f"   {key}  급여 {sorted(r[3] for r in members)}  "
              f"t(급여)={float(t_salary):.3f}  t(질병, 동일거리)={float(t_disease):.3f}")

    print("\n== 6. t-근접성을 맞추도록 다시 묶는다 ==")
    release_d = group_by(SALARY, lambda r: (r[1][:4] + "*", "≤40" if r[2] <= 40 else ">40"))
    show_classes("일반화 D — 우편번호 앞 4자리, 나이 40 기준", release_d, 4)
    worst = Fraction(0)
    for key, members in release_d.items():
        t_salary = ordered_emd([r[3] for r in members], salaries)
        t_disease = equal_emd([r[4] for r in members], diseases_all)
        worst = max(worst, t_salary)
        print(f"   {key}  급여 {sorted(r[3] for r in members)}  "
              f"t(급여)={float(t_salary):.3f}  t(질병, 동일거리)={float(t_disease):.3f}")
    print(f"   => 급여 기준 최대 t = {float(worst):.3f} ({worst})")

    print("\n== 7. 검산 — 두 동질 집합을 합치면 t 는 커지지 않는다 (Li 외 2007, Fact 2) ==")
    group_c = release_c[("476**", "20대")]
    group_d = release_c[("476**", "30대")]
    merged = group_c + group_d
    t_1 = ordered_emd([r[3] for r in group_c], salaries)
    t_2 = ordered_emd([r[3] for r in group_d], salaries)
    t_m = ordered_emd([r[3] for r in merged], salaries)
    print(f"   t1={float(t_1):.3f}  t2={float(t_2):.3f}  합친 집합 t={float(t_m):.3f}  "
          f"<= max(t1, t2): {t_m <= max(t_1, t_2)}")


if __name__ == "__main__":
    main()
