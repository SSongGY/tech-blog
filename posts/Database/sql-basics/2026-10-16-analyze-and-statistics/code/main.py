"""ANALYZE 가 쌓는 통계가 실행계획을 어떻게 바꾸는지 확인한다.

복합 인덱스 (grade, phone) 를 걸어 두고 선두 컬럼 없이 phone 만 조건으로 준다.
이 질의는 통계가 있을 때와 없을 때 계획이 갈린다.
"""

from __future__ import annotations

import sqlite3

from dbshow import print_dataset, print_environment

RULE = "=" * 64

SCHEMA = """
CREATE TABLE people (
    grade TEXT NOT NULL,
    phone TEXT NOT NULL,
    name  TEXT NOT NULL
);
CREATE INDEX idx_people ON people(grade, phone);
"""

QUERY = "SELECT name FROM people WHERE phone = ?"
PARAMS = ("010-0000123",)

GRADES = ("vip", "gold", "basic")


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.executemany(
        "INSERT INTO people VALUES (?, ?, ?)",
        # 등급은 세 종류뿐이고 전화번호는 전부 다르다.
        # 선두 컬럼의 값이 적다는 것이 뒤에서 계획을 가르는 조건이 된다.
        [(GRADES[i % 3], f"010-{i:07d}", f"회원{i:05d}") for i in range(30000)],
    )
    conn.commit()
    return conn


def show_plan(conn: sqlite3.Connection, label: str) -> None:
    print(f"-- {label}")
    print("QUERY PLAN")
    for _sel, _ord, _from, detail in conn.execute("EXPLAIN QUERY PLAN " + QUERY, PARAMS):
        print(f"`--{detail}")
    print()


def show_stat1(conn: sqlite3.Connection) -> None:
    rows = conn.execute("SELECT tbl, idx, stat FROM sqlite_stat1").fetchall()
    if not rows:
        print("  sqlite_stat1 에 행이 없다\n")
        return
    print("  tbl    | idx        | stat")
    print("  -------+------------+-------------")
    for tbl, idx, stat in rows:
        print(f"  {tbl:6s} | {str(idx):10s} | {stat}")
    print()


def show_grade_counts(conn: sqlite3.Connection) -> None:
    total, distinct = conn.execute(
        "SELECT COUNT(*), COUNT(DISTINCT grade) FROM people"
    ).fetchone()
    print(f"  전체 {total}행 · grade 값 {distinct}종 · 값 하나당 평균 {total // distinct}행")
    for grade, cnt in conn.execute(
        "SELECT grade, COUNT(*) FROM people GROUP BY grade ORDER BY COUNT(*) DESC LIMIT 4"
    ):
        print(f"    {grade:8s} {cnt:6d}행")
    print()


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print(RULE)
    print("1. 이 빌드가 쌓을 수 있는 통계 — stat4 는 컴파일 옵션이다")
    print(RULE)
    opts = [o for o in (r[0] for r in conn.execute("PRAGMA compile_options")) if "STAT" in o]
    print(f"  STAT 관련 컴파일 옵션: {opts or '없음'}")
    print("  → ENABLE_STAT4 가 없으므로 ANALYZE 는 sqlite_stat1 만 만든다\n")

    print(RULE)
    print("2. ANALYZE 전 — 통계 표 자체가 없다")
    print(RULE)
    has_stat1 = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE name = 'sqlite_stat1'"
    ).fetchone()[0]
    print(f"  sqlite_stat1 존재: {bool(has_stat1)}\n")
    show_plan(conn, "ANALYZE 전")

    print(RULE)
    print("3. ANALYZE 실행 — sqlite_stat1 에 무엇이 쌓이는가")
    print(RULE)
    conn.execute("ANALYZE")
    show_stat1(conn)
    show_plan(conn, "ANALYZE 후")

    print(RULE)
    print("4. stat 문자열의 숫자 읽기 — 지금은 평균이 실제와 맞는다")
    print(RULE)
    show_grade_counts(conn)

    print(RULE)
    print("5. 통계는 스냅샷이다 — 데이터를 바꿔도 따라오지 않는다")
    print(RULE)
    conn.executemany(
        "INSERT INTO people VALUES (?, ?, ?)",
        # 등급을 1인 1종으로 쪼개 선두 컬럼의 값 가짓수를 확 올린다
        [(f"vip-{i:05d}", f"011-{i:07d}", f"신규{i:05d}") for i in range(30000)],
    )
    conn.commit()
    print("  grade 가 전부 다른 행 30,000개를 더 넣었다")
    show_grade_counts(conn)
    print("  그런데 sqlite_stat1 은 그대로다:")
    show_stat1(conn)
    show_plan(conn, "데이터만 바뀐 뒤")

    print(RULE)
    print("6. 다시 ANALYZE — 통계가 계획을 되돌린다")
    print(RULE)
    conn.execute("ANALYZE")
    show_stat1(conn)
    show_plan(conn, "재-ANALYZE 후")
    print("  평균 2행은 어느 등급도 설명하지 못한다 — vip·gold·basic 은 각각 10,000행이다.")
    print("  sqlite_stat1 은 값별 분포를 담지 않으므로 이 치우침이 보이지 않는다.\n")
    conn.close()

    print(RULE)
    print("7. 경계는 어디인가 — 선두 컬럼의 중복 개수를 1씩 올려 본다")
    print(RULE)
    print("  중복 | stat             | 계획")
    print("  -----+------------------+----------------------------------------------")
    for dup in (10, 15, 17, 18, 19, 25):
        stat, detail = threshold_case(dup)
        print(f"  {dup:4d} | {stat:16s} | {detail}")
    print()


def threshold_case(dup: int, total: int = 36000) -> tuple[str, str]:
    """선두 컬럼 값 하나당 중복이 dup 개가 되도록 만들고 계획을 돌려본다."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.executemany(
        "INSERT INTO people VALUES (?, ?, ?)",
        [(f"g{i // dup}", f"010-{i:07d}", f"회원{i:05d}") for i in range(total)],
    )
    conn.execute("ANALYZE")
    stat = conn.execute("SELECT stat FROM sqlite_stat1").fetchone()[0]
    detail = " / ".join(
        d for _a, _b, _c, d in conn.execute("EXPLAIN QUERY PLAN " + QUERY, PARAMS)
    )
    conn.close()
    return stat, detail


if __name__ == "__main__":
    main()
