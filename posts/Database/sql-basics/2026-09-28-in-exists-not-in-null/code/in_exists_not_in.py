"""IN, EXISTS, NOT IN — 서브쿼리 쪽에 NULL 이 한 칸 섞이면 결과가 어떻게 갈리는지 본다.

메모리 SQLite에 고객 5명과 구매 6건을 넣는다. 구매 한 건은 비회원 결제라
customer_id 가 NULL 이다. 같은 질문("한 번도 안 산 고객")을 NOT IN, NOT EXISTS,
LEFT JOIN 으로 각각 풀어 결과를 나란히 찍는다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

CUSTOMERS = [
    (1, "한지우"),
    (2, "오민재"),
    (3, "윤서아"),
    (4, "장하준"),
    (5, "임채원"),
]

# customer_id 가 NULL 인 행은 비회원 결제다. 회원 번호가 없으니 비워 둔다
PURCHASES = [
    (101, 1, 12000),
    (102, 1, 8000),
    (103, 2, 30000),
    (104, 3, 5000),
    (105, None, 7000),
    (106, 3, 9000),
]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE customer (
            id   INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );
        CREATE TABLE purchase (
            id          INTEGER PRIMARY KEY,
            customer_id INTEGER REFERENCES customer(id),
            amount      INTEGER NOT NULL
        );
        """
    )
    conn.executemany("INSERT INTO customer VALUES (?, ?)", CUSTOMERS)
    conn.executemany("INSERT INTO purchase VALUES (?, ?, ?)", PURCHASES)
    conn.commit()
    return conn


def show(conn: sqlite3.Connection, label: str, sql: str) -> None:
    print(f"\n[{label}]")
    print(f"  {' '.join(sql.split())}")
    rows = conn.execute(sql).fetchall()
    for row in rows:
        print(f"  {row}")
    print(f"  -> {len(rows)}행")


def show_plan(conn: sqlite3.Connection, label: str, sql: str) -> None:
    # sqlite3 CLI 가 그리는 트리 모양을 그대로 흉내 낸다 (id·parent 로 깊이를 잡는다)
    print(f"\n[{label}]")
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    # 조상이 뒤에 형제를 더 가지면 "|  ", 아니면 "   " 을 앞에 쌓는다
    prefix = {0: ""}
    print("  QUERY PLAN")
    for i, (node_id, parent, _, detail) in enumerate(rows):
        is_last = all(r[1] != parent for r in rows[i + 1 :])
        branch = "`--" if is_last else "|--"
        lead = prefix.get(parent, "")
        print(f"  {lead}{branch}{detail}")
        prefix[node_id] = lead + ("   " if is_last else "|  ")


def section_truth_values(conn: sqlite3.Connection) -> None:
    print("\n== 1. 목록에 NULL 이 있을 때 IN / NOT IN 이 돌려주는 값 ==")
    # 1 = 참, 0 = 거짓, None = 알 수 없음(NULL)
    show(conn, "1-A 목록에 있는 값",
         "SELECT 1 IN (1, 2, NULL), 1 NOT IN (1, 2, NULL)")
    show(conn, "1-B 목록에 없는 값",
         "SELECT 3 IN (1, 2, NULL), 3 NOT IN (1, 2, NULL)")
    show(conn, "1-C NULL 이 없는 목록",
         "SELECT 3 IN (1, 2), 3 NOT IN (1, 2)")
    show(conn, "1-D 왼쪽이 NULL",
         "SELECT NULL IN (1, 2), NULL NOT IN (1, 2)")
    show(conn, "1-E 풀어 쓴 NOT IN",
         "SELECT 3 <> 1 AND 3 <> 2 AND 3 <> NULL")


def section_positive(conn: sqlite3.Connection) -> None:
    print("\n== 2. 산 적이 있는 고객 — IN, EXISTS, JOIN ==")
    show(conn, "2-A IN", """
        SELECT c.id, c.name FROM customer AS c
        WHERE c.id IN (SELECT p.customer_id FROM purchase AS p)
        ORDER BY c.id""")
    show(conn, "2-B EXISTS", """
        SELECT c.id, c.name FROM customer AS c
        WHERE EXISTS (SELECT 1 FROM purchase AS p WHERE p.customer_id = c.id)
        ORDER BY c.id""")
    show(conn, "2-C INNER JOIN", """
        SELECT c.id, c.name FROM customer AS c
        INNER JOIN purchase AS p ON p.customer_id = c.id
        ORDER BY c.id""")


def section_negative(conn: sqlite3.Connection) -> None:
    print("\n== 3. 한 번도 안 산 고객 — NOT IN, NOT EXISTS, LEFT JOIN ==")
    show(conn, "3-A NOT IN", """
        SELECT c.id, c.name FROM customer AS c
        WHERE c.id NOT IN (SELECT p.customer_id FROM purchase AS p)
        ORDER BY c.id""")
    show(conn, "3-B NOT EXISTS", """
        SELECT c.id, c.name FROM customer AS c
        WHERE NOT EXISTS (SELECT 1 FROM purchase AS p WHERE p.customer_id = c.id)
        ORDER BY c.id""")
    show(conn, "3-C LEFT JOIN ... IS NULL", """
        SELECT c.id, c.name FROM customer AS c
        LEFT JOIN purchase AS p ON p.customer_id = c.id
        WHERE p.id IS NULL
        ORDER BY c.id""")
    show(conn, "3-D NOT IN + IS NOT NULL", """
        SELECT c.id, c.name FROM customer AS c
        WHERE c.id NOT IN (SELECT p.customer_id FROM purchase AS p
                           WHERE p.customer_id IS NOT NULL)
        ORDER BY c.id""")


def section_without_null(conn: sqlite3.Connection) -> None:
    print("\n== 4. 비회원 결제를 지우면 ==")
    conn.execute("DELETE FROM purchase WHERE customer_id IS NULL")
    show(conn, "4-A NOT IN (NULL 행 삭제 후)", """
        SELECT c.id, c.name FROM customer AS c
        WHERE c.id NOT IN (SELECT p.customer_id FROM purchase AS p)
        ORDER BY c.id""")
    conn.rollback()


def section_plans(conn: sqlite3.Connection) -> None:
    print("\n== 5. 실행계획 ==")
    show_plan(conn, "5-A IN", """
        SELECT c.id FROM customer AS c
        WHERE c.id IN (SELECT p.customer_id FROM purchase AS p)""")
    show_plan(conn, "5-B EXISTS", """
        SELECT c.id FROM customer AS c
        WHERE EXISTS (SELECT 1 FROM purchase AS p WHERE p.customer_id = c.id)""")
    show_plan(conn, "5-C NOT IN", """
        SELECT c.id FROM customer AS c
        WHERE c.id NOT IN (SELECT p.customer_id FROM purchase AS p)""")
    show_plan(conn, "5-D NOT EXISTS", """
        SELECT c.id FROM customer AS c
        WHERE NOT EXISTS (SELECT 1 FROM purchase AS p WHERE p.customer_id = c.id)""")


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)
    section_truth_values(conn)
    section_positive(conn)
    section_negative(conn)
    section_without_null(conn)
    section_plans(conn)


if __name__ == "__main__":
    main()
