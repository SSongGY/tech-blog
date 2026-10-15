"""인덱스가 NULL 을 어떻게 다루는지 확인한다.

난수를 쓰지 않아 몇 번을 돌려도 같은 데이터·같은 결과가 나온다.
"""

from __future__ import annotations

import sqlite3

from dbshow import print_dataset, print_environment

RULE = "=" * 64
SCHEMA = """
CREATE TABLE employee (
    id         INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    manager_id INTEGER          -- 상급자가 없는 사원은 NULL
);
"""


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    # 5명 중 1명만 상급자가 있고 나머지 넷은 NULL 이다
    conn.executemany(
        "INSERT INTO employee VALUES (?, ?, ?)",
        [(i, f"사원{i:03d}", None if i % 5 else i // 5) for i in range(1, 101)],
    )
    conn.execute("CREATE INDEX idx_mgr ON employee(manager_id)")
    conn.commit()
    return conn


def plan_of(conn: sqlite3.Connection, sql: str) -> str:
    return " + ".join(r[3] for r in conn.execute("EXPLAIN QUERY PLAN " + sql))


def section(title: str) -> None:
    print(RULE)
    print(title)
    print(RULE)


def show_query(conn: sqlite3.Connection, sql: str) -> None:
    count = conn.execute(f"SELECT count(*) FROM ({sql})").fetchone()[0]
    print(f"  {sql}")
    print(f"    계획 : {plan_of(conn, sql)}")
    print(f"    건수 : {count}")


def experiment_is_null(conn: sqlite3.Connection) -> None:
    section("1. IS NULL 은 인덱스를 타는가 — 그리고 = NULL 과 무엇이 다른가")
    for sql in (
        "SELECT id FROM employee WHERE manager_id IS NULL",
        "SELECT id FROM employee WHERE manager_id = NULL",
        "SELECT id FROM employee WHERE manager_id IS NOT NULL",
        "SELECT id FROM employee WHERE manager_id <> 3",
        "SELECT id FROM employee WHERE manager_id IS NOT 3",
    ):
        show_query(conn, sql)
    print()


def experiment_order(conn: sqlite3.Connection) -> None:
    section("2. 정렬에서 NULL 이 놓이는 자리")
    for sql in (
        "SELECT manager_id FROM employee ORDER BY manager_id LIMIT 6",
        "SELECT manager_id FROM employee ORDER BY manager_id NULLS LAST LIMIT 6",
        "SELECT manager_id FROM employee ORDER BY manager_id DESC LIMIT 6",
        "SELECT manager_id FROM employee ORDER BY manager_id DESC NULLS FIRST LIMIT 6",
    ):
        values = [row[0] for row in conn.execute(sql)]
        print(f"  {sql}")
        print(f"    계획 : {plan_of(conn, sql)}")
        print(f"    결과 : {values}")
    print()


def experiment_unique() -> None:
    section("3. UNIQUE 와 PRIMARY KEY 는 NULL 을 받는가")
    conn = sqlite3.connect(":memory:")

    conn.execute("CREATE TABLE member (id INTEGER PRIMARY KEY, email TEXT UNIQUE)")
    for i in range(1, 4):
        conn.execute("INSERT INTO member VALUES (?, NULL)", (i,))
    print("  UNIQUE 컬럼에 NULL 세 번 삽입 :",
          conn.execute("SELECT count(*) FROM member").fetchone()[0], "행")
    try:
        conn.execute("INSERT INTO member VALUES (10, 'a@b.c')")
        conn.execute("INSERT INTO member VALUES (11, 'a@b.c')")
    except sqlite3.IntegrityError as exc:
        print("  같은 값 두 번 삽입              :", f"{type(exc).__name__}: {exc}")

    cases = [
        ("일반 rowid 표", "CREATE TABLE t1(code TEXT PRIMARY KEY, v TEXT)"),
        ("WITHOUT ROWID", "CREATE TABLE t2(code TEXT PRIMARY KEY, v TEXT) WITHOUT ROWID"),
        ("STRICT       ", "CREATE TABLE t3(code TEXT PRIMARY KEY, v TEXT) STRICT"),
        ("NOT NULL 명시", "CREATE TABLE t4(code TEXT PRIMARY KEY NOT NULL, v TEXT)"),
    ]
    print()
    for label, ddl in cases:
        conn.execute(ddl)
        table = ddl.split("(")[0].split()[-1]
        try:
            conn.execute(f"INSERT INTO {table} VALUES (NULL, 'x')")
            conn.execute(f"INSERT INTO {table} VALUES (NULL, 'y')")
            got = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            print(f"  PK 가 TEXT · {label} : NULL 두 번 통과 ({got}행)")
        except sqlite3.IntegrityError as exc:
            print(f"  PK 가 TEXT · {label} : {exc}")
    print()
    conn.close()


def experiment_not_in(conn: sqlite3.Connection) -> None:
    section("4. NOT IN 서브쿼리에 NULL 이 섞이면")
    both = (
        "SELECT count(*) FROM employee "
        "WHERE id NOT IN (SELECT manager_id FROM employee)",
        "SELECT count(*) FROM employee WHERE id NOT IN "
        "(SELECT manager_id FROM employee WHERE manager_id IS NOT NULL)",
    )
    for sql in both:
        print(f"  {sql}")
        print(f"    결과 : {conn.execute(sql).fetchone()[0]}건")
    print()


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)
    experiment_is_null(conn)
    experiment_order(conn)
    experiment_unique()
    experiment_not_in(conn)
    conn.close()


if __name__ == "__main__":
    main()
