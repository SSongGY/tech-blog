"""재귀 CTE 로 조직도를 펴 본다.

한 표 안에서 행이 다른 행을 가리키는 구조(manager_id -> id)를 한 질의로 훑는다.
아래로 내려가기, 위로 올라가기, 경로 문자열 만들기, 순서 바꾸기(너비 우선·깊이 우선),
그리고 종료 조건을 빠뜨리거나 데이터에 순환이 있을 때 무슨 일이 나는지까지 본다.

끝나지 않는 질의는 그대로 두면 영원히 돈다. 그래서 VDBE 명령 수를 세다가
한도를 넘으면 중단시키는 장치(set_progress_handler)를 걸어 둔다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

SCHEMA = """
CREATE TABLE employee (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    title       TEXT NOT NULL,
    manager_id  INTEGER REFERENCES employee(id)
);
"""

# (id, 이름, 직책, 상사 id). 사장 아래 본부장 2명, 그 아래 팀장과 팀원.
EMPLOYEES = [
    (1, "김대표", "사장", None),
    (2, "이본부", "개발본부장", 1),
    (3, "박본부", "영업본부장", 1),
    (4, "최팀장", "플랫폼팀장", 2),
    (5, "정팀장", "데이터팀장", 2),
    (6, "한사원", "플랫폼팀", 4),
    (7, "오사원", "플랫폼팀", 4),
    (8, "서사원", "데이터팀", 5),
    (9, "윤사원", "영업1팀", 3),
]

STEP_LIMIT = 200_000  # 이만큼 VDBE 명령을 돌려도 안 끝나면 끊는다


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO employee VALUES (?, ?, ?, ?)", EMPLOYEES)
    conn.commit()
    return conn


def query(conn: sqlite3.Connection, label: str, sql: str) -> None:
    """결과를 찍는다. 에러도 결과다."""
    print(f"\n[{label}]")
    try:
        cur = conn.execute(sql)
        print(f"  {tuple(col[0] for col in cur.description)}")
        for row in cur.fetchall():
            print(f"  {row}")
    except sqlite3.Error as exc:
        print(f"  -> {type(exc).__name__}: {exc}")


def query_with_guard(conn: sqlite3.Connection, label: str, sql: str) -> None:
    """끝나지 않을 수 있는 질의. 명령 수가 한도를 넘으면 SQLite 가 중단한다."""
    steps = 0

    def tick() -> int:
        nonlocal steps
        steps += 1
        return 1 if steps >= STEP_LIMIT else 0  # 0 이 아니면 중단

    print(f"\n[{label}]")
    conn.set_progress_handler(tick, 1)
    try:
        rows = conn.execute(sql).fetchall()
        print(f"  행 {len(rows)}개, VDBE 명령 {steps:,}개 만에 끝남")
    except sqlite3.Error as exc:
        print(f"  -> {type(exc).__name__}: {exc}  (VDBE 명령 {steps:,}개에서 끊음)")
    finally:
        conn.set_progress_handler(None, 1)


def plan_tree(conn: sqlite3.Connection, sql: str) -> str:
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
    return "\n".join("  " + line for line in lines)


DOWN_FROM_DEV = """
WITH RECURSIVE subordinate(id, name, title, level) AS (
    SELECT id, name, title, 1 FROM employee WHERE id = 2
    UNION ALL
    SELECT e.id, e.name, e.title, s.level + 1
    FROM employee AS e
    JOIN subordinate AS s ON e.manager_id = s.id
)
SELECT level, id, name, title FROM subordinate
"""


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("== 1. 자기 조인으로는 한 단계씩만 내려간다 ==")
    query(conn, "1-A 개발본부장(2)의 직속 부하", """
        SELECT e.id, e.name, e.title
        FROM employee AS e
        WHERE e.manager_id = 2
        ORDER BY e.id""")
    query(conn, "1-B 두 단계 아래까지 — 조인을 한 번 더 적어야 한다", """
        SELECT e2.id, e2.name, e2.title
        FROM employee AS e1
        JOIN employee AS e2 ON e2.manager_id = e1.id
        WHERE e1.manager_id = 2
        ORDER BY e2.id""")

    print("\n== 2. 재귀 CTE — 깊이에 상관없이 전부 내려간다 ==")
    query(conn, "2-A 개발본부장(2) 아래 전원, level 은 2 를 1 로 둔 깊이", DOWN_FROM_DEV)

    print("\n== 3. 위로 올라가기 — 한사원(6)의 보고 라인 ==")
    query(conn, "3-A 상사 체인", """
        WITH RECURSIVE chain(id, name, title, manager_id, hop) AS (
            SELECT id, name, title, manager_id, 0 FROM employee WHERE id = 6
            UNION ALL
            SELECT e.id, e.name, e.title, e.manager_id, c.hop + 1
            FROM employee AS e
            JOIN chain AS c ON e.id = c.manager_id
        )
        SELECT hop, id, name, title FROM chain""")

    print("\n== 4. 경로 문자열 — 재귀 단계마다 이어 붙인다 ==")
    query(conn, "4-A 사장부터 각 직원까지의 경로", """
        WITH RECURSIVE org(id, name, level, path) AS (
            SELECT id, name, 1, name FROM employee WHERE manager_id IS NULL
            UNION ALL
            SELECT e.id, e.name, o.level + 1, o.path || ' > ' || e.name
            FROM employee AS e
            JOIN org AS o ON e.manager_id = o.id
        )
        SELECT level, path FROM org ORDER BY path""")

    print("\n== 5. 꺼내는 순서 — 재귀 SELECT 의 ORDER BY 가 정한다 ==")
    base = """
        WITH RECURSIVE org(id, name, level) AS (
            SELECT id, name, 1 FROM employee WHERE manager_id IS NULL
            UNION ALL
            SELECT e.id, e.name, o.level + 1
            FROM employee AS e
            JOIN org AS o ON e.manager_id = o.id
            {order_by}
        )
        SELECT level, name FROM org"""
    query(conn, "5-A ORDER BY 없음 (현재 구현은 FIFO — 문서가 순서를 보장하지 않는다)",
          base.format(order_by=""))
    query(conn, "5-B ORDER BY o.level + 1 — 너비 우선", base.format(order_by="ORDER BY 3"))
    query(conn, "5-C ORDER BY o.level + 1 DESC — 깊이 우선", base.format(order_by="ORDER BY 3 DESC"))

    print("\n== 6. 실행계획 ==")
    print(plan_tree(conn, DOWN_FROM_DEV))

    print("\n== 7. 재귀 SELECT 에 쓸 수 없는 것 ==")
    query(conn, "7-A 집계 함수", """
        WITH RECURSIVE t(id, n) AS (
            SELECT id, 1 FROM employee WHERE id = 1
            UNION ALL
            SELECT e.id, COUNT(*) FROM employee AS e JOIN t ON e.manager_id = t.id
        )
        SELECT * FROM t""")
    query(conn, "7-B 재귀 표를 두 번 참조", """
        WITH RECURSIVE t(id) AS (
            SELECT 1
            UNION ALL
            SELECT a.id + 1 FROM t AS a JOIN t AS b ON a.id = b.id WHERE a.id < 3
        )
        SELECT * FROM t""")

    print("\n== 8. 종료 조건을 빠뜨리면 ==")
    query_with_guard(conn, "8-A WHERE 없는 숫자 생성 — 끝나지 않아서 끊었다", """
        WITH RECURSIVE cnt(x) AS (
            SELECT 1
            UNION ALL
            SELECT x + 1 FROM cnt
        )
        SELECT x FROM cnt""")
    query_with_guard(conn, "8-B 같은 질의에 LIMIT 10 — 재귀가 멈춘다", """
        WITH RECURSIVE cnt(x) AS (
            SELECT 1
            UNION ALL
            SELECT x + 1 FROM cnt LIMIT 10
        )
        SELECT x FROM cnt""")

    print("\n== 9. 데이터에 순환이 생기면 — 사장(1)의 상사를 한사원(6)으로 ==")
    conn.execute("UPDATE employee SET manager_id = 6 WHERE id = 1")
    cycle_sql = """
        WITH RECURSIVE chain(id, name, manager_id{extra_col}) AS (
            SELECT id, name, manager_id{extra_init} FROM employee WHERE id = 6
            {op}
            SELECT e.id, e.name, e.manager_id{extra_step}
            FROM employee AS e
            JOIN chain AS c ON e.id = c.manager_id
            LIMIT 12
        )
        SELECT * FROM chain"""
    query(conn, "9-A UNION ALL — 같은 행이 계속 나와 LIMIT 에 걸린다",
          cycle_sql.format(op="UNION ALL", extra_col="", extra_init="", extra_step=""))
    query(conn, "9-B UNION — 똑같은 행은 큐에 다시 넣지 않아 스스로 멈춘다",
          cycle_sql.format(op="UNION", extra_col="", extra_init="", extra_step=""))
    query(conn, "9-C UNION 인데 hop 컬럼이 있으면 — 행이 매번 달라 멈추지 않는다",
          cycle_sql.format(op="UNION", extra_col=", hop", extra_init=", 0",
                           extra_step=", c.hop + 1"))
    conn.close()


if __name__ == "__main__":
    main()
