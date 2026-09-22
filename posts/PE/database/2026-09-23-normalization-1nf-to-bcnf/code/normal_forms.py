"""정규화 1NF~BCNF — 함수 종속으로 정규형을 판정하고 이상현상을 실제로 재현한다.

앞부분은 함수 종속 집합에서 속성 폐포·후보키를 계산해 2NF/3NF/BCNF 위반을 찾는다.
분해한 릴레이션은 그 릴레이션의 속성으로 투영한 FD 로 다시 판정한다.
뒷부분은 같은 릴레이션을 SQLite 에 만들어 갱신·삭제·삽입 이상을 행 수로 확인한다.
"""

import sqlite3
from itertools import combinations

# 속성 기호 — S 학번, C 과목코드, N 학생이름, D 학과, O 학과사무실, P 담당교수, G 성적
ENROLL_ATTRS = frozenset("SCNDOPG")
ENROLL_FDS = [
    (frozenset("S"), frozenset("N")),
    (frozenset("S"), frozenset("D")),
    (frozenset("D"), frozenset("O")),
    (frozenset("C"), frozenset("P")),
    (frozenset("SC"), frozenset("G")),
]

# BCNF 만 위반하는 고전 예 — 학생 S, 과목 C, 교수 P. 교수 한 명은 과목 하나만 맡는다.
TEACH_ATTRS = frozenset("SCP")
TEACH_FDS = [
    (frozenset("SC"), frozenset("P")),
    (frozenset("P"), frozenset("C")),
]


def closure(attrs: frozenset, fds: list) -> frozenset:
    """속성 집합의 폐포. 더 이상 늘지 않을 때까지 적용 가능한 FD 를 붙인다."""
    result = set(attrs)
    changed = True
    while changed:
        changed = False
        for left, right in fds:
            if left <= result and not right <= result:
                result |= right
                changed = True
    return frozenset(result)


def minimal_cover(fds: list) -> list:
    """최소 커버 — 우변을 단일 속성으로 쪼개고, 불필요한 좌변 속성과 FD 를 걷어낸다.

    정규형 판정은 커버 하나만 봐도 된다. 커버의 모든 FD 가 조건을 만족하면
    그 커버가 함의하는 FD 도 전부 만족하기 때문이다.
    """
    single = []
    for left, right in fds:
        for attr in right - left:
            single.append((left, frozenset(attr)))

    trimmed = []
    for left, right in single:
        reduced = left
        for attr in sorted(left):
            shrunk = reduced - {attr}
            if shrunk and right <= closure(shrunk, single):
                reduced = shrunk
        trimmed.append((reduced, right))

    result = list(dict.fromkeys(trimmed))
    for fd in list(result):
        rest = [other for other in result if other != fd]
        if fd[1] <= closure(fd[0], rest):
            result = rest
    return sorted(result, key=lambda fd: (len(fd[0]), fmt(fd[0])))


def project_fds(attrs: frozenset, fds: list) -> list:
    """FD 집합을 부분 릴레이션의 속성으로 투영한 뒤 최소 커버로 줄인다.

    부분집합마다 원래 FD 로 폐포를 구하고, 그중 이 릴레이션에 있는 속성만 남긴다.
    """
    projected = []
    for size in range(1, len(attrs)):
        for combo in combinations(sorted(attrs), size):
            left = frozenset(combo)
            right = closure(left, fds) & attrs - left
            if right:
                projected.append((left, right))
    return minimal_cover(projected)


def candidate_keys(attrs: frozenset, fds: list) -> list:
    """폐포가 전체 속성이 되는 최소 부분집합을 전부 찾는다."""
    keys = []
    for size in range(1, len(attrs) + 1):
        for combo in combinations(sorted(attrs), size):
            candidate = frozenset(combo)
            if closure(candidate, fds) != attrs:
                continue
            if any(key < candidate for key in keys):
                continue  # 이미 찾은 키를 포함하면 최소가 아니다
            keys.append(candidate)
    return keys


def fmt(attrs) -> str:
    return "".join(sorted(attrs)) or "(없음)"


def check_forms(label: str, attrs: frozenset, base_fds: list, show_fds: bool = True) -> None:
    fds = project_fds(attrs, base_fds)
    keys = candidate_keys(attrs, fds)
    prime = frozenset().union(*keys) if keys else frozenset()
    print(f"\n--- {label} ({fmt(attrs)}) ---")
    if show_fds:
        for left, right in fds:
            print(f"  FD  {fmt(left)} -> {fmt(right)}")
    print(f"  후보키   {[fmt(k) for k in keys]}")
    print(f"  기본속성 {fmt(prime)} · 비기본속성 {fmt(attrs - prime)}")

    partial, transitive, bcnf_bad = [], [], []
    for left, right in fds:
        is_super = closure(left, fds) == attrs
        for attr in right - left:
            if not is_super and f"{fmt(left)} -> {attr}" not in bcnf_bad:
                bcnf_bad.append(f"{fmt(left)} -> {attr}")
            if attr in prime:
                continue  # 2NF·3NF 는 비기본속성만 따진다
            if any(left < key for key in keys):
                partial.append(f"{fmt(left)} -> {attr}")
            elif not is_super:
                transitive.append(f"{fmt(left)} -> {attr}")

    print(f"  2NF 위반(부분 함수 종속)      {partial or '없음'}")
    print(f"  3NF 위반(이행 함수 종속)      {transitive or '없음'}")
    print(f"  BCNF 위반(결정자가 비 슈퍼키) {bcnf_bad or '없음'}")


def check_lossless(parts: list, base_fds: list) -> None:
    """Heath 의 정리 — 공통 속성이 어느 한쪽을 결정하면 두 조각 분해는 무손실이다."""
    left, right = parts
    shared = left & right
    ok = left <= closure(shared, base_fds) or right <= closure(shared, base_fds)
    print(
        f"  {fmt(left)} / {fmt(right)}  공통 {fmt(shared)} -> "
        f"폐포 {fmt(closure(shared, base_fds))}  [{'무손실' if ok else '손실 가능'}]"
    )


def check_preserving(parts: list, base_fds: list) -> None:
    """분해 뒤에도 원래 FD 를 릴레이션 하나 안에서 확인할 수 있는가."""
    union = []
    for part in parts:
        union.extend(project_fds(part, base_fds))
    lost = [
        f"{fmt(left)} -> {fmt(right)}"
        for left, right in base_fds
        if not right <= closure(left, union)
    ]
    print(f"  종속성 보존: {'모두 보존' if not lost else '깨진 FD ' + str(lost)}")


def anomaly_demo() -> None:
    """정규화 전 표에서 갱신·삭제·삽입 이상이 실제로 일어나는지 센다."""
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE enrollment (
            student_id   TEXT NOT NULL,
            course_id    TEXT NOT NULL,
            student_name TEXT NOT NULL,
            dept         TEXT NOT NULL,
            dept_office  TEXT NOT NULL,
            professor    TEXT NOT NULL,
            grade        TEXT,
            PRIMARY KEY (student_id, course_id)
        )
        """
    )
    rows = [
        ("S1", "C1", "김서준", "컴퓨터", "3층 301호", "박교수", "A"),
        ("S1", "C2", "김서준", "컴퓨터", "3층 301호", "최교수", "B"),
        ("S1", "C3", "김서준", "컴퓨터", "3층 301호", "정교수", "A"),
        ("S2", "C1", "이하윤", "컴퓨터", "3층 301호", "박교수", "B"),
        ("S3", "C4", "박도윤", "전자", "2층 210호", "한교수", "C"),
    ]
    conn.executemany("INSERT INTO enrollment VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
    conn.commit()

    print("\n--- 이상현상 (수강 5행) ---")
    same = conn.execute(
        "SELECT COUNT(*) FROM enrollment WHERE dept = '컴퓨터'"
    ).fetchone()[0]
    print(f"  갱신 이상: 컴퓨터학과 사무실 한 곳을 옮기면 고쳐야 할 행 {same}개")
    cur = conn.execute(
        "UPDATE enrollment SET dept_office = '5층 501호' "
        "WHERE student_id = 'S1' AND course_id = 'C1'"
    )
    conn.commit()
    offices = conn.execute(
        "SELECT DISTINCT dept_office FROM enrollment WHERE dept = '컴퓨터' "
        "ORDER BY dept_office"
    ).fetchall()
    print(f"    {cur.rowcount}행만 고치자 컴퓨터학과 사무실이 둘로 갈렸다: {offices}")

    conn.execute("DELETE FROM enrollment WHERE student_id = 'S3'")
    conn.commit()
    left_dept = conn.execute(
        "SELECT COUNT(*) FROM enrollment WHERE dept = '전자'"
    ).fetchone()[0]
    print(f"  삭제 이상: 박도윤의 수강 1건을 지우자 전자학과가 남은 행 {left_dept}개")

    try:
        conn.execute(
            "INSERT INTO enrollment (student_id, student_name, dept, dept_office) "
            "VALUES ('S4', '최시우', '전자', '2층 210호')"
        )
        conn.commit()
        print("    [실패] 수강 없는 학생이 등록됐다")
    except sqlite3.Error as exc:
        print(f"  삽입 이상: 수강 과목 없는 학생 등록 -> {type(exc).__name__}: {exc}")

    conn.close()


def main() -> None:
    print(f"SQLite {sqlite3.sqlite_version}")

    check_forms("정규화 전 수강", ENROLL_ATTRS, ENROLL_FDS)

    print("\n=== 2NF 분해 — 부분 함수 종속 제거 ===")
    two_nf = [frozenset("SNDO"), frozenset("CP"), frozenset("SCG")]
    check_lossless([frozenset("SNDO"), frozenset("SCPG")], ENROLL_FDS)
    check_lossless([frozenset("CP"), frozenset("SCG")], ENROLL_FDS)
    check_preserving(two_nf, ENROLL_FDS)
    for name, attrs in zip(["학생", "과목", "수강"], two_nf):
        check_forms(name, attrs, ENROLL_FDS, show_fds=False)

    print("\n=== 3NF 분해 — 이행 함수 종속 제거 ===")
    three_nf = [frozenset("SND"), frozenset("DO"), frozenset("CP"), frozenset("SCG")]
    check_lossless([frozenset("SND"), frozenset("DO")], ENROLL_FDS)
    check_preserving(three_nf, ENROLL_FDS)
    for name, attrs in zip(["학생", "학과", "과목", "수강"], three_nf):
        check_forms(name, attrs, ENROLL_FDS, show_fds=False)

    print("\n=== 3NF 는 만족하지만 BCNF 는 아닌 경우 ===")
    check_forms("강의", TEACH_ATTRS, TEACH_FDS)

    print("\n=== BCNF 분해 ===")
    bcnf = [frozenset("PC"), frozenset("SP")]
    check_lossless(bcnf, TEACH_FDS)
    check_preserving(bcnf, TEACH_FDS)
    for name, attrs in zip(["교수-과목", "학생-교수"], bcnf):
        check_forms(name, attrs, TEACH_FDS)

    anomaly_demo()


if __name__ == "__main__":
    main()
