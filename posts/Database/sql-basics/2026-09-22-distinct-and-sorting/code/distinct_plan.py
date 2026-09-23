"""DISTINCT가 실행계획에서 어떤 연산으로 바뀌는지 SQLite로 확인한다.

같은 SELECT DISTINCT 한 줄이 인덱스 유무에 따라 임시 B-Tree를 쓰기도 하고
쓰지 않기도 한다. 그 차이를 EXPLAIN QUERY PLAN으로 직접 뽑아 본다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

# 중복이 섞이도록 같은 (team, grade) 조합을 여러 번 넣는다.
EMPLOYEE_ROWS = [
    ("김서연", "개발", "선임"),
    ("박지훈", "개발", "선임"),
    ("강민수", "개발", "책임"),
    ("이하늘", "영업", "선임"),
    ("최유진", "영업", "선임"),
    ("정우성", "영업", "책임"),
    ("한지민", "지원", "책임"),
    ("오세훈", "지원", "책임"),
]


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE employee ("
        " id INTEGER PRIMARY KEY,"
        " name TEXT NOT NULL,"
        " team TEXT NOT NULL,"
        " grade TEXT NOT NULL)"
    )
    conn.executemany(
        "INSERT INTO employee (name, team, grade) VALUES (?, ?, ?)",
        EMPLOYEE_ROWS,
    )
    return conn


def show_rows(conn, label, sql):
    print(f"[{label}]")
    print(f"  SQL  : {sql}")
    for row in conn.execute(sql):
        print("  행   :", " | ".join("NULL" if v is None else str(v) for v in row))
    print()


def plan_tree(conn, sql, params=()):
    """EXPLAIN QUERY PLAN 결과를 sqlite3 CLI 가 보여주는 모양 그대로 만든다.

    detail 문자열만 라벨 붙여 찍으면 사람이 정리한 표처럼 보인다. CLI 와 같은 모양이면
    도구가 돌려준 값이라는 것이 글에서 바로 드러난다. 트리 구조는 각 행의
    (id, parent) 로 만든다 — 서브쿼리나 조인이 있으면 실제로 여러 단이 나온다.
    """
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql, params).fetchall()
    children = {}
    for node_id, parent_id, _, detail in rows:
        children.setdefault(parent_id, []).append((node_id, detail))

    lines = ["QUERY PLAN"]

    def walk(parent_id, prefix):
        items = children.get(parent_id, [])
        for index, (node_id, detail) in enumerate(items):
            last = index == len(items) - 1
            lines.append(prefix + ("`--" if last else "|--") + detail)
            walk(node_id, prefix + ("   " if last else "|  "))

    walk(0, "")
    return "\n".join(lines)


def indented_plan(conn, sql, params=(), indent="   "):
    """plan_tree 를 본문에 넣기 좋게 들여쓴다."""
    return "\n".join(indent + line for line in plan_tree(conn, sql, params).splitlines())


def show_plan(conn, label, sql):
    print(f"[{label}]")
    print(f"  SQL : {sql}")
    print(indented_plan(conn, sql, indent="  "))
    print()


def main():
    print_environment()
    print("=" * 62)

    conn = build_database()
    print_dataset(conn)

    print("## 1. DISTINCT는 무엇을 지우는가")
    show_rows(conn, "1-1 중복 포함", "SELECT team FROM employee")
    show_rows(conn, "1-2 중복 제거", "SELECT DISTINCT team FROM employee")
    # DISTINCT는 컬럼 하나가 아니라 SELECT 목록 전체를 한 줄로 보고 비교한다.
    show_rows(conn, "1-3 컬럼 두 개", "SELECT DISTINCT team, grade FROM employee")
    show_rows(conn, "1-4 name을 끼우면", "SELECT DISTINCT team, name FROM employee")

    print("## 2. 인덱스가 없을 때의 실행계획")
    show_plan(conn, "2-1 DISTINCT", "SELECT DISTINCT team FROM employee")
    show_plan(conn, "2-2 GROUP BY", "SELECT team FROM employee GROUP BY team")
    show_plan(conn, "2-3 그냥 SELECT", "SELECT team FROM employee")

    print("## 3. 인덱스를 만들면 달라지는가")
    conn.execute("CREATE INDEX ix_employee_team ON employee (team)")
    show_plan(conn, "3-1 DISTINCT", "SELECT DISTINCT team FROM employee")
    show_plan(conn, "3-2 DISTINCT 두 컬럼", "SELECT DISTINCT team, grade FROM employee")
    conn.execute("CREATE INDEX ix_employee_team_grade ON employee (team, grade)")
    show_plan(
        conn, "3-3 두 컬럼 인덱스 생성 후", "SELECT DISTINCT team, grade FROM employee"
    )

    print("## 4. 정렬은 덤이지 약속이 아니다")
    # 첫 컬럼이 grade인데 중복 제거에 쓰이는 인덱스는 (team, grade) 순이다.
    # 정렬된 것처럼 보이던 출력이 무엇을 기준으로 정렬된 것인지 드러난다.
    show_rows(conn, "4-1 grade만", "SELECT DISTINCT grade FROM employee")
    show_rows(conn, "4-2 grade, team", "SELECT DISTINCT grade, team FROM employee")
    show_plan(conn, "4-3 위 질의의 계획", "SELECT DISTINCT grade, team FROM employee")
    show_rows(
        conn,
        "4-4 순서를 요구하면",
        "SELECT DISTINCT grade, team FROM employee ORDER BY grade, team",
    )
    show_plan(
        conn,
        "4-5 그때의 계획",
        "SELECT DISTINCT grade, team FROM employee ORDER BY grade, team",
    )

    print("## 5. DISTINCT가 지워지는 경우")
    # 유니크 인덱스가 있으면 중복이 나올 수 없으므로 중복 제거 단계 자체가 필요 없다.
    show_plan(conn, "5-1 PK에 DISTINCT", "SELECT DISTINCT id FROM employee")
    show_plan(conn, "5-2 PK에 DISTINCT 없이", "SELECT id FROM employee")

    conn.close()


if __name__ == "__main__":
    main()
