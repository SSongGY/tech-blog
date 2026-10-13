"""인덱스가 여럿일 때 SQLite 가 무엇을 고르는지, ANALYZE 가 그 선택을 어떻게 바꾸는지.

같은 2,000행·같은 두 인덱스를 담은 DB 를 두 판 만든다. 둘의 차이는
인덱스를 만든 순서 하나뿐이다. 통계가 없으면 두 판의 실행계획이 갈리고,
ANALYZE 한 뒤에는 선택도가 높은 쪽으로 둘 다 모인다.
"""

import sqlite3

from dbshow import RULE, print_dataset, print_environment

ROW_COUNT = 2000
TARGET_EMP_NO = "E01234"

# 두 판의 차이는 이 순서뿐이다. 컬럼도 데이터도 질의도 같다.
BUILD_ORDERS = {
    "A": ["emp_no", "status"],
    "B": ["status", "emp_no"],
}

QUERY = "SELECT name FROM employee WHERE status = '재직' AND emp_no = ?"

SCHEMA = """
CREATE TABLE employee (
    id     INTEGER PRIMARY KEY,
    emp_no TEXT NOT NULL,
    status TEXT NOT NULL,
    name   TEXT NOT NULL
);
"""


def build_database(order_key="A"):
    """같은 2,000행을 담되 인덱스를 order_key 가 정한 순서로 만든다."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.executemany(
        "INSERT INTO employee VALUES (?, ?, ?, ?)",
        [
            (
                i,
                f"E{i:05d}",                        # 2,000개가 전부 다른 값
                "휴직" if i % 100 == 0 else "재직",  # 값은 두 가지뿐
                f"사원{i:04d}",
            )
            for i in range(1, ROW_COUNT + 1)
        ],
    )
    for column in BUILD_ORDERS[order_key]:
        conn.execute(f"CREATE INDEX idx_emp_{column} ON employee({column})")
    return conn


def print_plan(conn, sql, params):
    """EXPLAIN QUERY PLAN 이 그리는 트리를 손대지 않고 그대로 찍는다."""
    print("  QUERY PLAN")
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql, params).fetchall()
    for position, row in enumerate(rows):
        branch = "`--" if position == len(rows) - 1 else "|--"
        print(f"  {branch}{row[3]}")


def print_selectivity(conn):
    """두 조건이 각각 몇 행으로 좁혀 주는지 실제로 세어 본다."""
    matched_status = conn.execute(
        "SELECT count(*) FROM employee WHERE status = '재직'"
    ).fetchone()[0]
    matched_emp_no = conn.execute(
        "SELECT count(*) FROM employee WHERE emp_no = ?", (TARGET_EMP_NO,)
    ).fetchone()[0]
    print(f"    status = '재직'          -> {matched_status:4d}행으로 좁혀진다")
    print(f"    emp_no = '{TARGET_EMP_NO}'      -> {matched_emp_no:4d}행으로 좁혀진다")


def main():
    print_environment()
    print_dataset(build_database())

    print(RULE)
    print("각 조건이 실제로 몇 행을 남기는가")
    print(RULE)
    print_selectivity(build_database())
    print()

    for stage, run_analyze in (("통계 없음", False), ("ANALYZE 실행 후", True)):
        print(RULE)
        print(f"{stage} — 같은 질의, 같은 데이터, 같은 두 인덱스")
        print(RULE)
        for order_key in ("A", "B"):
            conn = build_database(order_key)
            if run_analyze:
                conn.execute("ANALYZE")
            print(f"  [{order_key}판] 인덱스 만든 순서: "
                  + " -> ".join(BUILD_ORDERS[order_key]))
            print_plan(conn, QUERY, (TARGET_EMP_NO,))
            print(f"  결과: {conn.execute(QUERY, (TARGET_EMP_NO,)).fetchall()}")
            if run_analyze:
                print("  sqlite_stat1:")
                for idx, stat in conn.execute(
                    "SELECT idx, stat FROM sqlite_stat1 ORDER BY idx"
                ):
                    print(f"    {idx:16s} {stat}")
            print()


if __name__ == "__main__":
    main()
