"""복합 자연키 스키마와 대리키 스키마를 같은 데이터로 만들어 비교한다.

재는 것은 넷이다.
  1. 저장 공간 — 자식 표마다 자연키 문자열이 통째로 복제된다
  2. 키 값이 바뀔 때 고쳐지는 행 수 — ON UPDATE CASCADE 가 어디까지 번지는가
  3. 조회 경로 — 자연키는 조인 없이 닿고, 대리키는 원래 값을 찾아 거슬러 올라가야 한다
  4. 자연키가 재사용될 때 무엇이 막히는가

파일 DB 를 쓰는 이유는 page_count 로 실제 크기를 재기 위해서다. 메모리 DB 로는
같은 PRAGMA 가 의미 있는 값을 주지 않는다.
"""

from __future__ import annotations

import os
import sqlite3
import time

from dbshow import print_dataset, print_environment

# 파일 이름을 probe 로 시작하면 저장소가 추적하지 않는다. 돌릴 때마다 새로 만든다.
NATURAL_DB = "probe_natural.db"
SURROGATE_DB = "probe_surrogate.db"

STUDENT_COUNT = 2_000
COURSE_COUNT = 300
ENROLLMENT_COUNT = 20_000
MEETINGS_PER_ENROLLMENT = 8

# --- 스키마 -----------------------------------------------------------------
#
# 두 스키마는 같은 사실을 담는다. 학생이 강좌를 듣고(enrollment), 그 수강마다
# 출석 기록이 회차별로 붙는다(attendance). 다른 것은 "무엇으로 행을 가리키는가"뿐이다.

NATURAL_SCHEMA = """
CREATE TABLE student (
    student_code TEXT PRIMARY KEY,
    name         TEXT NOT NULL
);
CREATE TABLE course (
    course_code  TEXT PRIMARY KEY,
    title        TEXT NOT NULL
);
CREATE TABLE enrollment (
    student_code TEXT NOT NULL REFERENCES student(student_code) ON UPDATE CASCADE,
    course_code  TEXT NOT NULL REFERENCES course(course_code)  ON UPDATE CASCADE,
    enrolled_on  TEXT NOT NULL,
    PRIMARY KEY (student_code, course_code)
);
CREATE TABLE attendance (
    student_code TEXT NOT NULL,
    course_code  TEXT NOT NULL,
    meeting_no   INTEGER NOT NULL,
    attended     INTEGER NOT NULL,
    PRIMARY KEY (student_code, course_code, meeting_no),
    FOREIGN KEY (student_code, course_code)
        REFERENCES enrollment(student_code, course_code) ON UPDATE CASCADE
);
"""

SURROGATE_SCHEMA = """
CREATE TABLE student (
    student_id   INTEGER PRIMARY KEY,
    student_code TEXT NOT NULL UNIQUE,
    name         TEXT NOT NULL
);
CREATE TABLE course (
    course_id    INTEGER PRIMARY KEY,
    course_code  TEXT NOT NULL UNIQUE,
    title        TEXT NOT NULL
);
CREATE TABLE enrollment (
    enrollment_id INTEGER PRIMARY KEY,
    student_id    INTEGER NOT NULL REFERENCES student(student_id),
    course_id     INTEGER NOT NULL REFERENCES course(course_id),
    enrolled_on   TEXT NOT NULL,
    UNIQUE (student_id, course_id)
);
CREATE TABLE attendance (
    attendance_id INTEGER PRIMARY KEY,
    enrollment_id INTEGER NOT NULL REFERENCES enrollment(enrollment_id),
    meeting_no    INTEGER NOT NULL,
    attended      INTEGER NOT NULL,
    UNIQUE (enrollment_id, meeting_no)
);
"""


def student_code(n: int) -> str:
    return f"S{n:06d}"


def course_code(n: int) -> str:
    """학과·학년도·일련번호가 들어간 흔한 모양의 자연키다."""
    return f"CS-2026-{n:04d}"


def enrollment_pairs() -> list[tuple[int, int]]:
    """학생·강좌 조합을 겹치지 않게 만든다. 난수를 안 쓰므로 매번 같은 집합이다."""
    pairs = []
    for i in range(ENROLLMENT_COUNT):
        pairs.append((i % STUDENT_COUNT, (i * 7 + i // STUDENT_COUNT) % COURSE_COUNT))
    # 같은 (학생, 강좌) 가 두 번 나오면 PK 에 걸린다. 중복을 걷어낸다.
    return sorted(set(pairs))


PAIRS = enrollment_pairs()


def build_natural(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(NATURAL_SCHEMA)
    conn.executemany(
        "INSERT INTO student VALUES (?, ?)",
        [(student_code(i), f"학생{i:04d}") for i in range(STUDENT_COUNT)],
    )
    conn.executemany(
        "INSERT INTO course VALUES (?, ?)",
        [(course_code(i), f"강좌{i:03d}") for i in range(COURSE_COUNT)],
    )
    conn.executemany(
        "INSERT INTO enrollment VALUES (?, ?, '2026-03-02')",
        [(student_code(s), course_code(c)) for s, c in PAIRS],
    )
    conn.executemany(
        "INSERT INTO attendance VALUES (?, ?, ?, ?)",
        [
            (student_code(s), course_code(c), m, (s + c + m) % 10 != 0)
            for s, c in PAIRS
            for m in range(1, MEETINGS_PER_ENROLLMENT + 1)
        ],
    )
    conn.commit()
    return conn


def build_surrogate(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SURROGATE_SCHEMA)
    conn.executemany(
        "INSERT INTO student VALUES (?, ?, ?)",
        [(i + 1, student_code(i), f"학생{i:04d}") for i in range(STUDENT_COUNT)],
    )
    conn.executemany(
        "INSERT INTO course VALUES (?, ?, ?)",
        [(i + 1, course_code(i), f"강좌{i:03d}") for i in range(COURSE_COUNT)],
    )
    conn.executemany(
        "INSERT INTO enrollment VALUES (?, ?, ?, '2026-03-02')",
        [(n + 1, s + 1, c + 1) for n, (s, c) in enumerate(PAIRS)],
    )
    conn.executemany(
        "INSERT INTO attendance VALUES (?, ?, ?, ?)",
        [
            (n * MEETINGS_PER_ENROLLMENT + m, n + 1, m, (s + c + m) % 10 != 0)
            for n, (s, c) in enumerate(PAIRS)
            for m in range(1, MEETINGS_PER_ENROLLMENT + 1)
        ],
    )
    conn.commit()
    return conn


def db_bytes(conn: sqlite3.Connection) -> int:
    page_count = conn.execute("PRAGMA page_count").fetchone()[0]
    page_size = conn.execute("PRAGMA page_size").fetchone()[0]
    return page_count * page_size


def show_plan(conn: sqlite3.Connection, title: str, sql: str, params=()) -> None:
    """EXPLAIN QUERY PLAN 의 id/parent 를 그대로 살려 트리로 찍는다."""
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql, params).fetchall()
    children: dict[int, list[tuple[int, str]]] = {}
    for node_id, parent, _unused, detail in rows:
        children.setdefault(parent, []).append((node_id, detail))

    print(f"\n-- {title}")
    print("  QUERY PLAN")

    def walk(parent: int, prefix: str) -> None:
        items = children.get(parent, [])
        for index, (node_id, detail) in enumerate(items):
            last = index == len(items) - 1
            print(f"  {prefix}{'`--' if last else '|--'} {detail}")
            walk(node_id, prefix + ("    " if last else "|   "))

    walk(0, "")


def timed(conn: sqlite3.Connection, sql: str, params_list: list[tuple]) -> float:
    started = time.perf_counter()
    for params in params_list:
        conn.execute(sql, params).fetchall()
    return time.perf_counter() - started


def main() -> None:
    for path in (NATURAL_DB, SURROGATE_DB):
        if os.path.exists(path):
            os.remove(path)

    natural = build_natural(NATURAL_DB)
    surrogate = build_surrogate(SURROGATE_DB)

    print_environment()
    print("자연키 스키마 — 아래 비교의 한쪽이다")
    print_dataset(natural, max_rows=5)

    print("=" * 64)
    print("1. 같은 사실을 담은 두 스키마의 크기")
    print("=" * 64)
    natural_bytes = db_bytes(natural)
    surrogate_bytes = db_bytes(surrogate)
    rows = natural.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
    print(f"  수강 {len(PAIRS):,}건 · 출석 {rows:,}행 · 두 DB 의 행 수는 같다")
    print(f"  자연키 스키마 : {natural_bytes:>10,} 바이트")
    print(f"  대리키 스키마 : {surrogate_bytes:>10,} 바이트")
    print(f"  차이          : {natural_bytes - surrogate_bytes:>10,} 바이트 "
          f"({natural_bytes / surrogate_bytes:.2f}배)")

    print("\n" + "=" * 64)
    print("2. 강좌 코드 하나가 바뀔 때 고쳐지는 행 수")
    print("=" * 64)
    old_code, new_code = course_code(7), "EE-2026-0007"
    affected = natural.execute(
        "SELECT COUNT(*) FROM attendance WHERE course_code = ?", (old_code,)
    ).fetchone()[0]
    print(f"  대상 강좌 {old_code} -> {new_code}")
    print(f"  이 강좌의 출석 행 수 : {affected:,}")

    before = natural.total_changes
    natural.execute("UPDATE course SET course_code = ? WHERE course_code = ?",
                    (new_code, old_code))
    natural.commit()
    print(f"  자연키 스키마에서 바뀐 행 : {natural.total_changes - before:,}")

    before = surrogate.total_changes
    surrogate.execute("UPDATE course SET course_code = ? WHERE course_code = ?",
                      (new_code, old_code))
    surrogate.commit()
    print(f"  대리키 스키마에서 바뀐 행 : {surrogate.total_changes - before:,}")

    left = natural.execute(
        "SELECT COUNT(*) FROM attendance WHERE course_code = ?", (old_code,)
    ).fetchone()[0]
    moved = natural.execute(
        "SELECT COUNT(*) FROM attendance WHERE course_code = ?", (new_code,)
    ).fetchone()[0]
    print(f"  자연키 스키마의 출석 행 : 옛 코드 {left}행 · 새 코드 {moved}행")

    print("\n" + "=" * 64)
    print("3. 한 학생의 한 강좌 출석을 꺼내는 경로")
    print("=" * 64)
    natural_sql = (
        "SELECT meeting_no, attended FROM attendance "
        "WHERE student_code = ? AND course_code = ? ORDER BY meeting_no"
    )
    surrogate_sql = (
        "SELECT a.meeting_no, a.attended FROM attendance a "
        "JOIN enrollment e ON a.enrollment_id = e.enrollment_id "
        "JOIN student s ON e.student_id = s.student_id "
        "JOIN course c ON e.course_id = c.course_id "
        "WHERE s.student_code = ? AND c.course_code = ? ORDER BY a.meeting_no"
    )
    probe = (student_code(PAIRS[0][0]), course_code(PAIRS[0][1]))
    print(f"  찾는 값: 학번 {probe[0]} · 강좌 {probe[1]}")
    print(f"  자연키 결과 {natural.execute(natural_sql, probe).fetchall()}")
    print(f"  대리키 결과 {surrogate.execute(surrogate_sql, probe).fetchall()}")
    show_plan(natural, "자연키 스키마", natural_sql, probe)
    show_plan(surrogate, "대리키 스키마", surrogate_sql, probe)

    repeats = [(student_code(s), course_code(c)) for s, c in PAIRS[:2000]]
    print(f"\n  한 건씩 꺼내는 조회 {len(repeats):,}회 (환경에 따라 흔들리는 값이다)")
    print(f"    자연키 : {timed(natural, natural_sql, repeats) * 1000:7.1f} ms")
    print(f"    대리키 : {timed(surrogate, surrogate_sql, repeats) * 1000:7.1f} ms")

    # 한 건 조회는 파이썬 호출 비용이 커서 조인 차이가 묻힌다. 전 범위를 훑는
    # 집계로 바꾸면 조인이 실제로 몇 번 일어나는지가 시간에 드러난다.
    natural_agg = ("SELECT course_code, AVG(attended) FROM attendance "
                   "GROUP BY course_code")
    surrogate_agg = ("SELECT c.course_code, AVG(a.attended) FROM attendance a "
                     "JOIN enrollment e ON a.enrollment_id = e.enrollment_id "
                     "JOIN course c ON e.course_id = c.course_id "
                     "GROUP BY c.course_code")
    natural_result = natural.execute(natural_agg).fetchall()
    surrogate_result = surrogate.execute(surrogate_agg).fetchall()
    print(f"\n  강좌별 출석률 집계 — 결과가 같은가: {natural_result == surrogate_result}"
          f" ({len(natural_result)}개 강좌)")
    print(f"    자연키 : {timed(natural, natural_agg, [()] * 3) * 1000 / 3:7.1f} ms (3회 평균)")
    print(f"    대리키 : {timed(surrogate, surrogate_agg, [()] * 3) * 1000 / 3:7.1f} ms (3회 평균)")
    show_plan(natural, "자연키 집계", natural_agg)
    show_plan(surrogate, "대리키 집계", surrogate_agg)

    print("\n" + "=" * 64)
    print("4. 대리키를 둬도 자연키 제약은 그대로 둬야 한다")
    print("=" * 64)
    # 폐강된 강좌의 코드를 다른 강좌가 물려받는 상황이다. 현실에서 드물지 않다.
    recycled = course_code(11)
    for label, conn, sql, params in (
        ("자연키", natural, "INSERT INTO course VALUES (?, ?)", (recycled, "새 강좌")),
        ("대리키", surrogate, "INSERT INTO course VALUES (?, ?, ?)",
         (COURSE_COUNT + 1, recycled, "새 강좌")),
    ):
        try:
            conn.execute(sql, params)
        except sqlite3.IntegrityError as error:
            print(f"  {label} 스키마: {type(error).__name__}: {error}")
        else:
            conn.rollback()
            print(f"  {label} 스키마: 들어갔다")

    # UNIQUE 를 빼면 어떻게 되는지. 대리키가 유일성을 대신해 준다는 오해를 확인한다.
    surrogate.executescript("""
        CREATE TABLE course_loose (
            course_id   INTEGER PRIMARY KEY,
            course_code TEXT NOT NULL,
            title       TEXT NOT NULL
        );
        INSERT INTO course_loose VALUES (1, 'CS-2026-0011', '예전 강좌');
        INSERT INTO course_loose VALUES (2, 'CS-2026-0011', '물려받은 강좌');
    """)
    loose = surrogate.execute(
        "SELECT course_id, title FROM course_loose WHERE course_code = ?",
        (recycled,),
    ).fetchall()
    print(f"\n  UNIQUE 를 뺀 표에 같은 코드를 두 번 넣으면: {loose}")
    print("  코드로 강좌를 찾는 질의가 두 행을 돌려준다 — 대리키가 유일성을 대신하지 않는다")

    natural.close()
    surrogate.close()


if __name__ == "__main__":
    main()
