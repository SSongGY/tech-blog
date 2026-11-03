"""INDEXED BY 와 NOT INDEXED 가 질의 계획과 실제 수행량을 어떻게 바꾸는지 본다.

SQLite 3.49.1 / Python 3.13.5 에서 돌렸다. 외부 의존성은 없다.
"""

import random
import sqlite3

from dbshow import print_dataset, print_environment

DEPARTMENTS = ["영업", "개발", "인사", "재무"]
ROW_COUNT = 20000
SEED = 42


def build_database() -> sqlite3.Connection:
    """부서는 4가지로 고르게, 급여는 3000~8999 로 흩어 놓는다."""
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE employee (
            emp_id   INTEGER PRIMARY KEY,
            dept     TEXT    NOT NULL,
            salary   INTEGER NOT NULL,
            hired_on TEXT    NOT NULL
        )
        """
    )
    rng = random.Random(SEED)
    rows = [
        (
            emp_id,
            rng.choice(DEPARTMENTS),
            rng.randrange(3000, 9000),
            f"20{rng.randrange(10, 26):02d}-{rng.randrange(1, 13):02d}-01",
        )
        for emp_id in range(1, ROW_COUNT + 1)
    ]
    conn.executemany("INSERT INTO employee VALUES (?, ?, ?, ?)", rows)
    conn.execute("CREATE INDEX idx_emp_dept ON employee(dept)")
    conn.execute("CREATE INDEX idx_emp_salary ON employee(salary)")
    conn.commit()
    return conn


def show_plan(conn: sqlite3.Connection, sql: str) -> None:
    for _, _, _, detail in conn.execute("EXPLAIN QUERY PLAN " + sql):
        print(f"    {detail}")


def count_steps(conn: sqlite3.Connection, sql: str) -> tuple[int, list]:
    """진행 콜백을 1 스텝마다 걸어 가상머신 명령 수를 센다.

    경과 시간과 달리 기계 상태에 흔들리지 않아 같은 입력이면 같은 값이 나온다.
    """
    counter = [0]

    def tick() -> int:
        counter[0] += 1
        return 0

    conn.set_progress_handler(tick, 1)
    rows = conn.execute(sql).fetchall()
    conn.set_progress_handler(None, 1)
    return counter[0], rows


QUERIES = {
    "지정 없음": "SELECT COUNT(*) FROM employee WHERE dept = '영업' AND salary > 8000",
    "NOT INDEXED": "SELECT COUNT(*) FROM employee NOT INDEXED WHERE dept = '영업' AND salary > 8000",
    "INDEXED BY idx_emp_dept": "SELECT COUNT(*) FROM employee INDEXED BY idx_emp_dept WHERE dept = '영업' AND salary > 8000",
    "INDEXED BY idx_emp_salary": "SELECT COUNT(*) FROM employee INDEXED BY idx_emp_salary WHERE dept = '영업' AND salary > 8000",
}


def compare(conn: sqlite3.Connection, title: str) -> None:
    print(f"\n[{title}]")
    for label, sql in QUERIES.items():
        steps, rows = count_steps(conn, sql)
        print(f"  {label}  (결과 {rows[0][0]}행, {steps} 스텝)")
        show_plan(conn, sql)


def try_sql(conn: sqlite3.Connection, label: str, sql: str) -> None:
    print(f"\n  {label}")
    print(f"    {sql}")
    try:
        conn.execute(sql).fetchall()
    except sqlite3.OperationalError as exc:
        print(f"    OperationalError: {exc}")
    else:
        show_plan(conn, sql)


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("\n[두 조건이 각각 몇 행을 남기는가]")
    for label, where in [("dept = '영업'", "dept = '영업'"),
                         ("salary > 8000", "salary > 8000"),
                         ("둘 다", "dept = '영업' AND salary > 8000")]:
        n = conn.execute(f"SELECT COUNT(*) FROM employee WHERE {where}").fetchone()[0]
        print(f"  {label:<16} {n}행")

    compare(conn, "통계 없음 — 방금 만든 상태")
    conn.execute("ANALYZE")
    compare(conn, "ANALYZE 로 통계를 만든 뒤")

    print("\n[지정한 인덱스를 쓸 수 없을 때]")
    try_sql(conn, "조건과 무관한 인덱스를 지정",
            "SELECT emp_id FROM employee INDEXED BY idx_emp_salary WHERE dept = '영업'")
    try_sql(conn, "이름이 없는 인덱스를 지정",
            "SELECT emp_id FROM employee INDEXED BY idx_emp_none WHERE dept = '영업'")

    print("\n[NOT INDEXED 는 rowid 까지 막지는 않는다]")
    try_sql(conn, "기본키 조건",
            "SELECT dept FROM employee NOT INDEXED WHERE emp_id = 7")

    print("\n[부분 인덱스는 조건이 겹쳐도 못 쓸 수 있다]")
    conn.execute("CREATE INDEX idx_emp_high ON employee(salary) WHERE salary > 7000")
    try_sql(conn, "인덱스 조건과 글자까지 같은 범위",
            "SELECT emp_id FROM employee WHERE salary > 7000")
    try_sql(conn, "더 좁은 범위인데 글자가 다름",
            "SELECT emp_id FROM employee WHERE salary > 8000")
    try_sql(conn, "더 좁은 범위를 지정까지 해 봄",
            "SELECT emp_id FROM employee INDEXED BY idx_emp_high WHERE salary > 8000")

    print("\n[인덱스가 사라진 뒤]")
    conn.execute("DROP INDEX idx_emp_dept")
    try_sql(conn, "지정 없음 — 조용히 전체 훑기로 내려앉는다",
            "SELECT COUNT(*) FROM employee WHERE dept = '영업'")
    try_sql(conn, "지정 있음 — 준비 단계에서 끊긴다",
            "SELECT COUNT(*) FROM employee INDEXED BY idx_emp_dept WHERE dept = '영업'")

    conn.close()


if __name__ == "__main__":
    main()
