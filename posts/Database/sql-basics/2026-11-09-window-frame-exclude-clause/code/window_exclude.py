"""윈도우 프레임 EXCLUDE 절 네 가지가 프레임에서 무엇을 빼는지 확인한다.

python window_exclude.py
"""

import sqlite3
import time

from dbshow import _render, print_dataset, print_environment


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript("""
    CREATE TABLE employee (
        emp_name  TEXT    NOT NULL,
        dept_name TEXT    NOT NULL,
        salary    INTEGER NOT NULL
    );
    INSERT INTO employee (emp_name, dept_name, salary) VALUES
      ('가온', '개발', 300),
      ('나래', '개발', 400),
      ('다온', '개발', 400),
      ('라온', '개발', 500),
      ('마루', '영업', 350),
      ('바름', '영업', 450),
      ('사름', '인사', 380);
    """)
    return conn


def show(conn, title, sql):
    print(f"\n### {title}")
    print(sql.strip())
    cur = conn.execute(sql)
    names = [d[0] for d in cur.description]
    rows = cur.fetchall()
    # 숫자 칸만 오른쪽으로 붙여야 자릿수가 눈으로 비교된다
    aligns = [
        all(isinstance(r[i], (int, float)) or r[i] is None for r in rows)
        for i in range(len(names))
    ]
    for line in _render(names, rows, aligns):
        print(line)


def print_plan(conn, sql):
    """sqlite3 CLI 와 같은 모양으로 그린다 — id·parent 컬럼으로 중첩을 복원한다."""
    children = {}
    for node_id, parent, _, detail in conn.execute("EXPLAIN QUERY PLAN " + sql):
        children.setdefault(parent, []).append((node_id, detail))

    def walk(parent, prefix):
        rows = children.get(parent, [])
        for i, (node_id, detail) in enumerate(rows):
            last = i == len(rows) - 1
            print(prefix + ("`--" if last else "|--") + detail)
            walk(node_id, prefix + ("   " if last else "|  "))

    print("QUERY PLAN")
    walk(0, "")


def count_vm_steps(conn, sql):
    """VDBE 명령 수를 센다 — 시간과 달리 실행할 때마다 같은 값이 나온다."""
    steps = 0

    def tick():
        nonlocal steps
        steps += 1
        return 0

    conn.set_progress_handler(tick, 1)
    try:
        conn.execute(sql).fetchall()
    finally:
        conn.set_progress_handler(None, 0)
    return steps


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)

    whole = "ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING"
    show(conn, "1. 개발 부서 4명 — 네 가지 EXCLUDE 가 프레임에 남기는 사람", f"""
SELECT emp_name, salary,
  group_concat(emp_name, ',') OVER (ORDER BY salary {whole}
                                    EXCLUDE NO OTHERS)  AS no_others,
  group_concat(emp_name, ',') OVER (ORDER BY salary {whole}
                                    EXCLUDE CURRENT ROW) AS current_row,
  group_concat(emp_name, ',') OVER (ORDER BY salary {whole}
                                    EXCLUDE GROUP)       AS grp,
  group_concat(emp_name, ',') OVER (ORDER BY salary {whole}
                                    EXCLUDE TIES)        AS ties
FROM employee
WHERE dept_name = '개발'
ORDER BY salary, emp_name
""")

    show(conn, "2. 나를 뺀 부서 평균 — EXCLUDE CURRENT ROW 와 (합-나)/(수-1)", f"""
SELECT dept_name, emp_name, salary,
  AVG(salary) OVER (PARTITION BY dept_name {whole}
                    EXCLUDE CURRENT ROW)                AS others_avg,
  (SUM(salary) OVER (PARTITION BY dept_name) - salary)
    / (COUNT(*) OVER (PARTITION BY dept_name) - 1)      AS by_formula,
  (SUM(salary) OVER (PARTITION BY dept_name) - salary) * 1.0
    / (COUNT(*) OVER (PARTITION BY dept_name) - 1)      AS by_formula_real
FROM employee
ORDER BY dept_name, salary, emp_name
""")

    show(conn, "3. 기본 프레임(RANGE) 그대로 — EXCLUDE CURRENT ROW 가 동점을 남긴다", """
SELECT emp_name, salary,
  SUM(salary) OVER (ORDER BY salary)                         AS running,
  SUM(salary) OVER (ORDER BY salary
                    RANGE UNBOUNDED PRECEDING
                    EXCLUDE CURRENT ROW)                     AS range_excl,
  SUM(salary) OVER (ORDER BY salary
                    ROWS UNBOUNDED PRECEDING
                    EXCLUDE CURRENT ROW)                     AS rows_excl,
  COUNT(*)    OVER (ORDER BY salary
                    RANGE UNBOUNDED PRECEDING
                    EXCLUDE CURRENT ROW)                     AS range_cnt,
  COUNT(*)    OVER (ORDER BY salary
                    ROWS UNBOUNDED PRECEDING
                    EXCLUDE CURRENT ROW)                     AS rows_cnt
FROM employee
WHERE dept_name = '개발'
ORDER BY salary, emp_name
""")

    show(conn, "4. ORDER BY 가 없으면 — 파티션 전체가 동점 묶음이다", f"""
SELECT dept_name, emp_name,
  COUNT(*) OVER (PARTITION BY dept_name {whole} EXCLUDE CURRENT ROW) AS excl_cur,
  COUNT(*) OVER (PARTITION BY dept_name {whole} EXCLUDE GROUP)       AS excl_grp,
  COUNT(*) OVER (PARTITION BY dept_name {whole} EXCLUDE TIES)        AS excl_ties
FROM employee
ORDER BY dept_name, emp_name
""")

    show(conn, "5. 앞뒤 한 명씩만 — 이웃 평균과 내 값 비교", """
SELECT emp_name, salary,
  AVG(salary) OVER (ORDER BY salary, emp_name
                    ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING
                    EXCLUDE CURRENT ROW)                    AS neighbor_avg,
  group_concat(emp_name, ',') OVER (ORDER BY salary, emp_name
                    ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING
                    EXCLUDE CURRENT ROW)                    AS neighbors
FROM employee
ORDER BY salary, emp_name
""")

    show(conn, "6. 프레임을 쓰지 않는 함수에 EXCLUDE 를 붙이면", f"""
SELECT emp_name, salary,
  ROW_NUMBER()     OVER (ORDER BY salary {whole} EXCLUDE CURRENT ROW) AS rn,
  RANK()           OVER (ORDER BY salary {whole} EXCLUDE CURRENT ROW) AS rnk,
  FIRST_VALUE(emp_name)
                   OVER (ORDER BY salary {whole} EXCLUDE CURRENT ROW) AS first_other
FROM employee
WHERE dept_name = '개발'
ORDER BY salary, emp_name
""")

    print("\n### 7. 문법 — EXCLUDE 는 프레임 경계 뒤에만 온다")
    for label, clause in [
        ("ORDER BY 뒤에 바로", "ORDER BY salary EXCLUDE TIES"),
        ("경계 앞에", "ORDER BY salary EXCLUDE TIES ROWS UNBOUNDED PRECEDING"),
        ("경계 뒤에", "ORDER BY salary ROWS UNBOUNDED PRECEDING EXCLUDE TIES"),
    ]:
        try:
            conn.execute(f"SELECT COUNT(*) OVER ({clause}) FROM employee").fetchall()
            print(f"  {label:16s} OK     — {clause}")
        except sqlite3.Error as exc:
            print(f"  {label:16s} 실패   — {clause}\n{'':20s}{type(exc).__name__}: {exc}")

    print("\n### 8. 실행계획 — EXCLUDE 유무")
    for label, sql in [
        ("EXCLUDE 없음", f"SELECT AVG(salary) OVER (PARTITION BY dept_name {whole}) "
                         "FROM employee"),
        ("EXCLUDE CURRENT ROW", f"SELECT AVG(salary) OVER (PARTITION BY dept_name {whole} "
                                "EXCLUDE CURRENT ROW) FROM employee"),
    ]:
        print(f"-- {label}")
        print_plan(conn, sql)

    print("\n### 9. 행이 늘어날 때 일의 양 — VDBE 명령 수와 시간")
    print("  한 부서에 n 명. 나를 뺀 평균을 두 방법으로 구한다.")
    big = sqlite3.connect(":memory:")
    big.execute("CREATE TABLE employee (emp_name TEXT, dept_name TEXT, salary INTEGER)")
    queries = {
        "EXCLUDE": f"SELECT AVG(salary) OVER (PARTITION BY dept_name {whole} "
                   "EXCLUDE CURRENT ROW) FROM employee",
        "공식": "SELECT (SUM(salary) OVER w - salary) * 1.0 / (COUNT(*) OVER w - 1) "
                "FROM employee WINDOW w AS (PARTITION BY dept_name)",
    }
    header = ["n", "EXCLUDE 명령 수", "공식 명령 수", "EXCLUDE ms", "공식 ms"]
    rows = []
    for n in (500, 1000, 2000, 4000):
        big.execute("DELETE FROM employee")
        # 급여는 n 에 따라 정해지는 값이라 다시 돌려도 같은 표가 나온다
        big.executemany(
            "INSERT INTO employee VALUES (?, '개발', ?)",
            [(f"e{i}", 300 + (i * 37) % 500) for i in range(n)],
        )
        steps = {k: count_vm_steps(big, q) for k, q in queries.items()}
        elapsed = {}
        for k, q in queries.items():
            start = time.perf_counter()
            big.execute(q).fetchall()
            elapsed[k] = (time.perf_counter() - start) * 1000
        rows.append([n, steps["EXCLUDE"], steps["공식"],
                     f"{elapsed['EXCLUDE']:.1f}", f"{elapsed['공식']:.1f}"])
    for line in _render(header, rows, [True] * 5):
        print(line)
    big.close()
    conn.close()


if __name__ == "__main__":
    main()
