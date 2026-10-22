"""자기참조 외래키 — 한 표 안에서 부모를 가리킬 때 실제로 무슨 일이 일어나는가.

표준 SQL 과 SQLite 3.49.1 로 돌아간다. 외래키 검사는 SQLite 에서 기본이 꺼져
있으므로(PRAGMA foreign_keys) 연결마다 켜 준다.
"""

from __future__ import annotations

import sqlite3

from dbshow import print_dataset, print_environment

SCHEMA = """
CREATE TABLE department (
    department_id   INTEGER PRIMARY KEY,
    department_name TEXT    NOT NULL,
    parent_id       INTEGER REFERENCES department(department_id) ON DELETE CASCADE
);
"""

# (id, 이름, 부모) — 부모가 먼저 들어가도록 순서를 맞춰 둔 행들이다.
SEED_ROWS = [
    (1, "본사", None),
    (2, "기술본부", 1),
    (3, "경영지원본부", 1),
    (4, "플랫폼개발팀", 2),
    (5, "데이터플랫폼팀", 2),
    (6, "인사팀", 3),
    (7, "쿼리엔진파트", 4),
    (8, "스토리지파트", 4),
]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO department VALUES (?, ?, ?)", SEED_ROWS)
    conn.commit()
    return conn


def show_direct_children(conn: sqlite3.Connection) -> None:
    print("1. 한 단계 아래만 — 자기 자신과 조인한다")
    rows = conn.execute(
        """
        SELECT parent.department_name, child.department_name
          FROM department AS parent
          JOIN department AS child ON child.parent_id = parent.department_id
         WHERE parent.department_name = '기술본부'
         ORDER BY child.department_id
        """
    ).fetchall()
    for parent_name, child_name in rows:
        print(f"  {parent_name} -> {child_name}")
    print()


def show_recursive_path(conn: sqlite3.Connection) -> None:
    print("2. 끝까지 내려가기 — 재귀 CTE 가 같은 표를 반복해서 다시 읽는다")
    rows = conn.execute(
        """
        WITH RECURSIVE subtree(department_id, department_name, depth, path) AS (
            SELECT department_id, department_name, 0, department_name
              FROM department
             WHERE parent_id IS NULL
            UNION ALL
            SELECT d.department_id, d.department_name, s.depth + 1,
                   s.path || ' > ' || d.department_name
              FROM department AS d
              JOIN subtree AS s ON d.parent_id = s.department_id
        )
        SELECT depth, path FROM subtree ORDER BY path
        """
    ).fetchall()
    for depth, path in rows:
        print(f"  depth={depth}  {path}")
    print()


def show_insert_order(conn: sqlite3.Connection) -> None:
    print("3. 부모보다 자식을 먼저 넣으면")
    try:
        conn.execute("INSERT INTO department VALUES (11, '신설파트', 10)")
    except sqlite3.IntegrityError as exc:
        print(f"  IntegrityError: {exc}")
    conn.rollback()

    print("  같은 두 줄을 순서만 바꿔 넣으면")
    conn.execute("INSERT INTO department VALUES (10, '신설팀', 2)")
    conn.execute("INSERT INTO department VALUES (11, '신설파트', 10)")
    conn.commit()
    row = conn.execute(
        "SELECT department_id, department_name, parent_id FROM department"
        " WHERE department_id IN (10, 11) ORDER BY department_id"
    ).fetchall()
    print(f"  들어간 행: {row}")
    print()


def show_cascade(conn: sqlite3.Connection) -> None:
    print("4. 부모 한 행을 지우면 — ON DELETE CASCADE 는 손자까지 따라 내려간다")
    before = conn.execute("SELECT count(*) FROM department").fetchone()[0]
    cur = conn.execute("DELETE FROM department WHERE department_name = '플랫폼개발팀'")
    conn.commit()
    after = conn.execute("SELECT count(*) FROM department").fetchone()[0]
    remaining = conn.execute(
        "SELECT department_name FROM department ORDER BY department_id"
    ).fetchall()
    # rowcount 는 DELETE 문이 직접 고른 행만 센다. 연쇄로 지워진 행은 안 센다.
    print(f"  DELETE 가 직접 지목한 행: {cur.rowcount}")
    print(f"  전체 행 수: {before} -> {after} ({before - after}행 사라짐)")
    print(f"  남은 부서: {[name for (name,) in remaining]}")
    print()


def show_cycle(conn: sqlite3.Connection) -> None:
    print("5. 외래키는 순환을 막지 못한다")
    conn.execute(
        "UPDATE department SET parent_id = 5 WHERE department_name = '기술본부'"
    )
    conn.commit()
    pairs = conn.execute(
        "SELECT department_id, parent_id FROM department"
        " WHERE department_id IN (2, 5) ORDER BY department_id"
    ).fetchall()
    print(f"  (department_id, parent_id) = {pairs}  <- 2 -> 5 -> 2 로 닫힌다")
    print("  외래키 제약은 통과한다. 가리키는 행이 실제로 있기 때문이다.")

    # 깊이 제한이 없으면 재귀 CTE 가 끝나지 않는다. LIMIT 으로 잘라서 보여 준다.
    rows = conn.execute(
        """
        WITH RECURSIVE walk(department_id, depth) AS (
            SELECT department_id, 0 FROM department WHERE department_id = 2
            UNION ALL
            SELECT d.department_id, w.depth + 1
              FROM department AS d JOIN walk AS w ON d.parent_id = w.department_id
        )
        SELECT department_id, depth FROM walk LIMIT 8
        """
    ).fetchall()
    print(f"  같은 재귀 CTE 를 돌리면: {rows} ... (LIMIT 8 로 잘랐다)")

    rows = conn.execute(
        """
        WITH RECURSIVE walk(department_id, depth, seen) AS (
            SELECT department_id, 0, ',' || department_id || ','
              FROM department WHERE department_id = 2
            UNION ALL
            SELECT d.department_id, w.depth + 1, w.seen || d.department_id || ','
              FROM department AS d JOIN walk AS w ON d.parent_id = w.department_id
             WHERE w.seen NOT LIKE '%,' || d.department_id || ',%'
        )
        SELECT department_id, depth FROM walk
        """
    ).fetchall()
    print(f"  지나온 id 를 들고 다니며 거르면: {rows}")
    print()


def show_plan(conn: sqlite3.Connection) -> None:
    print("6. 자식을 찾는 질의의 실행계획 — parent_id 에는 색인이 자동으로 생기지 않는다")
    query = "SELECT department_id FROM department WHERE parent_id = 2"
    for line in conn.execute("EXPLAIN QUERY PLAN " + query):
        print(f"  {line[3]}")
    conn.execute("CREATE INDEX ix_department_parent_id ON department(parent_id)")
    print("  CREATE INDEX ix_department_parent_id ON department(parent_id) 뒤")
    for line in conn.execute("EXPLAIN QUERY PLAN " + query):
        print(f"  {line[3]}")
    print()


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)
    show_direct_children(conn)
    show_recursive_path(conn)
    show_insert_order(conn)
    show_cascade(conn)
    show_cycle(conn)
    show_plan(conn)
    conn.close()


if __name__ == "__main__":
    main()
