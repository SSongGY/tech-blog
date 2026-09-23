"""GROUP BY 와 집계 함수가 NULL 을 다루는 방식을 SQLite 로 확인한다.

표준 라이브러리만 쓴다. 메모리 DB 에 9행짜리 employee 테이블을 만들고
COUNT(*) / COUNT(컬럼) / SUM / AVG 의 결과와 실행계획을 나란히 뽑는다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

# bonus 에 None 을 섞어 둔 것이 이 예제의 전부다. 지원팀은 세 명 모두 None 이다.
EMPLOYEE_ROWS = [
    (1, "김하나", "개발", 400),
    (2, "이두리", "개발", None),
    (3, "박세찬", "개발", 200),
    (4, "최나영", "영업", 300),
    (5, "정오름", "영업", 300),
    (6, "한여름", "지원", None),
    (7, "오가을", "지원", None),
    (8, "신겨울", "지원", None),
    (9, "윤바다", None, 100),
]


def open_db():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE employee (
            id     INTEGER PRIMARY KEY,
            name   TEXT NOT NULL,
            team   TEXT,
            bonus  INTEGER
        )
        """
    )
    conn.executemany("INSERT INTO employee VALUES (?, ?, ?, ?)", EMPLOYEE_ROWS)
    return conn


def show_rows(conn, sql, label):
    print(f"[{label}]")
    print(f"  SQL  : {sql}")
    rows = list(conn.execute(sql))
    if not rows:
        print("  행   : (없음)")
    for row in rows:
        cells = ["NULL" if v is None else str(v) for v in row]
        print("  행   : " + " | ".join(cells))
    print()


def show_plan(conn, sql, label):
    print(f"[{label}]")
    print(f"  SQL  : {sql}")
    print("  QUERY PLAN")
    # EXPLAIN QUERY PLAN 이 돌려주는 (id, parent, notused, detail) 을 그대로 쓴다.
    nodes = list(conn.execute("EXPLAIN QUERY PLAN " + sql))
    for i, (node_id, parent, _notused, detail) in enumerate(nodes):
        children = [n for n in nodes if n[1] == parent]
        last = children[-1][0] == node_id
        depth = 0
        cursor = parent
        while cursor != 0:
            depth += 1
            cursor = next(n[1] for n in nodes if n[0] == cursor)
        prefix = "   " * depth + ("`--" if last else "|--")
        print("  " + prefix + detail)
    print()


def section(title):
    print("=" * 62)
    print(f"## {title}")


def main():
    conn = open_db()
    print_dataset(conn)
    print_environment()

    section("1. 집계 함수는 NULL 을 세지 않는다")
    show_rows(
        conn,
        "SELECT COUNT(*), COUNT(bonus), SUM(bonus), AVG(bonus) FROM employee",
        "1-1 테이블 전체",
    )
    show_rows(
        conn,
        "SELECT team, COUNT(*), COUNT(bonus), SUM(bonus), AVG(bonus) "
        "FROM employee GROUP BY team",
        "1-2 팀별",
    )

    section("2. AVG 의 분모는 COUNT(*) 가 아니다")
    show_rows(
        conn,
        "SELECT team, AVG(bonus), SUM(bonus) * 1.0 / COUNT(*) FROM employee "
        "WHERE team = '개발' GROUP BY team",
        "2-1 개발팀의 AVG 와 손계산",
    )
    show_rows(
        conn,
        "SELECT AVG(COALESCE(bonus, 0)) FROM employee WHERE team = '개발'",
        "2-2 NULL 을 0 으로 채우면",
    )

    section("3. 전부 NULL 인 그룹")
    show_rows(
        conn,
        "SELECT team, COUNT(*), COUNT(bonus), SUM(bonus), AVG(bonus), "
        "MAX(bonus) FROM employee WHERE team = '지원' GROUP BY team",
        "3-1 지원팀은 bonus 가 전부 NULL",
    )
    show_rows(
        conn,
        "SELECT team, TOTAL(bonus) FROM employee WHERE team = '지원' GROUP BY team",
        "3-2 SQLite 의 TOTAL 은 0 을 돌려준다",
    )

    section("4. GROUP BY 는 NULL 을 한 그룹으로 묶는다")
    show_rows(
        conn,
        "SELECT team, COUNT(*) FROM employee GROUP BY team ORDER BY team",
        "4-1 team 이 NULL 인 행도 그룹이 된다",
    )
    show_rows(
        conn,
        "SELECT COUNT(*) FROM employee WHERE team = NULL",
        "4-2 같은 행을 WHERE team = NULL 로 찾으면",
    )
    show_rows(
        conn,
        "SELECT COUNT(*) FROM employee WHERE team IS NULL",
        "4-3 IS NULL 로 찾으면",
    )

    section("5. WHERE 와 HAVING")
    show_rows(
        conn,
        "SELECT team, COUNT(*) FROM employee GROUP BY team HAVING COUNT(*) >= 3",
        "5-1 HAVING 은 묶은 뒤에 걸린다",
    )
    show_rows(
        conn,
        "SELECT team, COUNT(*) FROM employee WHERE bonus IS NOT NULL "
        "GROUP BY team HAVING COUNT(*) >= 3",
        "5-2 WHERE 로 먼저 걸러 내면 그룹 자체가 달라진다",
    )

    section("6. SELECT 목록에 집계 대상이 아닌 컬럼을 두면")
    show_rows(
        conn,
        "SELECT team, name, MAX(bonus) FROM employee GROUP BY team",
        "6-1 MAX 와 같이 쓴 name",
    )
    show_rows(
        conn,
        "SELECT team, name, COUNT(*) FROM employee GROUP BY team",
        "6-2 COUNT 와 같이 쓴 name",
    )

    section("7. 실행계획")
    show_plan(conn, "SELECT team, COUNT(*) FROM employee GROUP BY team", "7-1 인덱스 없음")
    conn.execute("CREATE INDEX ix_employee_team ON employee (team)")
    show_plan(
        conn,
        "SELECT team, COUNT(*) FROM employee GROUP BY team",
        "7-2 ix_employee_team 생성 후",
    )
    show_plan(
        conn,
        "SELECT team, COUNT(bonus) FROM employee GROUP BY team",
        "7-3 인덱스에 없는 컬럼을 집계하면",
    )

    conn.close()


if __name__ == "__main__":
    main()
