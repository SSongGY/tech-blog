"""FIRST_VALUE 와 LAST_VALUE 가 기본 프레임에서 어떻게 갈리는지 확인한다.

같은 데이터에 프레임만 바꿔 가며 돌려서, LAST_VALUE 가 "구간의 끝"이 아니라
"지금까지 본 것 중 끝"을 돌려주는 자리를 눈으로 본다.
"""

import sqlite3
import unicodedata

from dbshow import print_dataset, print_environment

RULE = "=" * 64

SCHEMA = """
-- 개발 부서에 급여가 같은 행을 둘 넣었다. RANGE 와 ROWS 가 갈리는 자리를
-- 보려면 ORDER BY 키가 같은 행(동등 행)이 있어야 한다.
CREATE TABLE employee (
    emp_id    INTEGER PRIMARY KEY,
    emp_name  TEXT    NOT NULL,
    dept_name TEXT    NOT NULL,
    salary    INTEGER NOT NULL
);

INSERT INTO employee (emp_id, emp_name, dept_name, salary) VALUES
    (1, '김하나', '개발', 4200),
    (2, '이두리', '개발', 5100),
    (3, '박세진', '개발', 5100),
    (4, '최나래', '개발', 6300),
    (5, '정다윤', '영업', 3800),
    (6, '한소은', '영업', 4700),
    (7, '오미루', '영업', 5500);
"""


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    return conn


def section(title: str) -> None:
    print(RULE)
    print(title)
    print(RULE)


def _width(text: str) -> int:
    """한글은 터미널에서 두 칸을 차지한다. len 으로 재면 표가 어긋난다."""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def _pad(text: str, width: int) -> str:
    return text + " " * max(0, width - _width(text))


def run_query(conn: sqlite3.Connection, sql: str) -> None:
    print(sql.strip())
    print()
    cur = conn.execute(sql)
    headers = [d[0] for d in cur.description]
    cells = [[("NULL" if v is None else str(v)) for v in row] for row in cur.fetchall()]
    widths = [_width(h) for h in headers]
    for row in cells:
        widths = [max(w, _width(c)) for w, c in zip(widths, row)]
    print("  " + " | ".join(_pad(h, w) for h, w in zip(headers, widths)))
    print("  " + "-+-".join("-" * w for w in widths))
    for row in cells:
        print("  " + " | ".join(_pad(c, w) for c, w in zip(row, widths)).rstrip())
    print()


def format_plan(conn: sqlite3.Connection, sql: str) -> str:
    """EXPLAIN QUERY PLAN 결과를 sqlite3 CLI 가 그리는 트리 모양 그대로 만든다."""
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    children: dict[int, list[tuple[int, str]]] = {}
    for node_id, parent_id, _, detail in rows:
        children.setdefault(parent_id, []).append((node_id, detail))

    lines = ["QUERY PLAN"]

    def walk(parent_id: int, prefix: str) -> None:
        items = children.get(parent_id, [])
        for index, (node_id, detail) in enumerate(items):
            last = index == len(items) - 1
            lines.append(prefix + ("`--" if last else "|--") + detail)
            walk(node_id, prefix + ("   " if last else "|  "))

    walk(0, "")
    return "\n".join(lines)


def main() -> None:
    conn = build_database()

    print_environment()
    print_dataset(conn)

    section("① 프레임을 안 적고 그대로 — LAST_VALUE 가 자기 자신을 돌려준다")
    run_query(conn, """
SELECT emp_name, dept_name, salary,
       FIRST_VALUE(salary) OVER w AS first_value,
       LAST_VALUE(salary)  OVER w AS last_value
  FROM employee
WINDOW w AS (PARTITION BY dept_name ORDER BY salary)
""")

    section("② 프레임 끝을 파티션 끝까지 늘린다 — 의도한 값이 나온다")
    run_query(conn, """
SELECT emp_name, dept_name, salary,
       FIRST_VALUE(salary) OVER w AS first_value,
       LAST_VALUE(salary)  OVER w AS last_value
  FROM employee
WINDOW w AS (PARTITION BY dept_name ORDER BY salary
             ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
""")

    section("③ ORDER BY 를 뒤집어 FIRST_VALUE 로 받는다 — 프레임을 안 건드린다")
    run_query(conn, """
SELECT emp_name, dept_name, salary,
       FIRST_VALUE(salary) OVER (PARTITION BY dept_name
                                 ORDER BY salary)      AS lowest,
       FIRST_VALUE(salary) OVER (PARTITION BY dept_name
                                 ORDER BY salary DESC) AS highest
  FROM employee
""")

    section("④ 동등 행이 있을 때 RANGE 와 ROWS 가 갈린다 (개발 부서, 5100 이 둘)")
    run_query(conn, """
SELECT emp_name, salary,
       LAST_VALUE(emp_name) OVER (ORDER BY salary
           RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS by_range,
       LAST_VALUE(emp_name) OVER (ORDER BY salary
           ROWS  BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS by_rows
  FROM employee
 WHERE dept_name = '개발'
""")

    section("⑤ 프레임을 좁히면 '구간'이 움직인다 — 자기 포함 최근 3행")
    run_query(conn, """
SELECT emp_name, salary,
       FIRST_VALUE(salary) OVER w AS window_first,
       LAST_VALUE(salary)  OVER w AS window_last
  FROM employee
WINDOW w AS (ORDER BY salary ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
""")

    section("⑥ IGNORE NULLS 는 SQLite 가 받지 않는다")
    try:
        conn.execute(
            "SELECT LAST_VALUE(salary IGNORE NULLS) OVER (ORDER BY salary)"
            " FROM employee"
        )
    except sqlite3.Error as exc:
        print(f"  sqlite3.{type(exc).__name__}: {exc}")
    print()

    section("⑦ 실행계획 — 윈도우 함수는 정렬한 결과를 코루틴으로 한 번 훑는다")
    plan_sql = (
        "SELECT emp_name,"
        " LAST_VALUE(salary) OVER (PARTITION BY dept_name ORDER BY salary)"
        " FROM employee"
    )
    print(plan_sql)
    print()
    print(format_plan(conn, plan_sql))
    print()

    conn.close()


if __name__ == "__main__":
    main()
