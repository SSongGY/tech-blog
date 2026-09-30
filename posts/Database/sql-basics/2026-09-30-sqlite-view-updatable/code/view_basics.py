"""SQLite 의 VIEW 를 만들고 쓰는 법, 그리고 뷰를 통해 데이터를 바꾸려 할 때 일어나는 일을 확인한다.

SQLite 의 뷰는 읽기 전용이다. INSERT·UPDATE·DELETE 를 받으려면 INSTEAD OF 트리거를 달아야 한다.
뷰가 데이터를 따로 갖지 않는다는 것, 원본 표가 바뀌면 뷰가 어떻게 되는지도 본다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

SCHEMA = """
CREATE TABLE member (
    member_id  INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    phone      TEXT,
    active     INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE orders (
    order_id   INTEGER PRIMARY KEY,
    member_id  INTEGER NOT NULL REFERENCES member (member_id),
    amount     INTEGER NOT NULL
);
INSERT INTO member VALUES
    (1, '김하나', '010-1111', 1),
    (2, '이두리', NULL,       0),
    (3, '박세찬', '010-3333', 1);
INSERT INTO orders VALUES (10, 1, 5000), (11, 3, 7000), (12, 1, 2000);
"""


def build_database():
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.executescript(SCHEMA)
    return conn


def attempt(conn, sql):
    """실패해도 멈추지 않고 SQLite 가 돌려준 오류 문구를 그대로 찍는다."""
    try:
        cur = conn.execute(sql)
        print(f"   [성공] {sql}")
        print(f"          → rowcount = {cur.rowcount}")
    except sqlite3.Error as exc:
        print(f"   [실패] {sql}")
        print(f"          → {type(exc).__name__}: {exc}")


def show(conn, sql):
    print(f"   {sql}")
    cur = conn.execute(sql)
    print("   " + " | ".join(d[0] for d in cur.description))
    for row in cur.fetchall():
        print("   " + " | ".join("NULL" if v is None else str(v) for v in row))
    print()


def plan_tree(conn, sql):
    """EXPLAIN QUERY PLAN 결과를 sqlite3 CLI 가 그리는 트리 모양 그대로 만든다."""
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
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
    return "\n".join("   " + line for line in lines)


def main():
    print_environment()
    conn = build_database()
    print_dataset(conn)

    print("-- 1. 뷰를 만들고 표처럼 조회한다")
    conn.execute("""
        CREATE VIEW v_active_member (member_id, member_name, phone) AS
            SELECT member_id, name, phone FROM member WHERE active = 1""")
    conn.execute("""
        CREATE VIEW v_member_total AS
            SELECT m.member_id, m.name, COUNT(o.order_id) AS order_count,
                   COALESCE(SUM(o.amount), 0) AS total_amount
            FROM member m LEFT JOIN orders o ON o.member_id = m.member_id
            GROUP BY m.member_id, m.name""")
    show(conn, "SELECT * FROM v_active_member")
    show(conn, "SELECT * FROM v_member_total")

    print("-- 2. 뷰는 데이터를 따로 갖지 않는다 — sqlite_schema 에 남는 것은 SELECT 문뿐")
    show(conn, "SELECT type, name, rootpage FROM sqlite_schema ORDER BY type, name")
    conn.execute("UPDATE member SET active = 1 WHERE member_id = 2")
    print("   원본 표에서 member 2 를 active = 1 로 바꾼 뒤")
    show(conn, "SELECT * FROM v_active_member")

    print("-- 3. 뷰에 직접 INSERT·UPDATE·DELETE")
    attempt(conn, "UPDATE v_active_member SET phone = '010-2222' WHERE member_id = 2")
    attempt(conn, "INSERT INTO v_active_member VALUES (4, '최네모', NULL)")
    attempt(conn, "DELETE FROM v_active_member WHERE member_id = 3")
    print()

    print("-- 4. INSTEAD OF 트리거를 달면 받는다")
    conn.execute("""
        CREATE TRIGGER tr_active_member_update
        INSTEAD OF UPDATE OF phone ON v_active_member
        BEGIN
            UPDATE member SET phone = NEW.phone WHERE member_id = OLD.member_id;
        END""")
    conn.execute("""
        CREATE TRIGGER tr_active_member_insert
        INSTEAD OF INSERT ON v_active_member
        BEGIN
            INSERT INTO member (member_id, name, phone, active)
            VALUES (NEW.member_id, NEW.member_name, NEW.phone, 0);
        END""")
    attempt(conn, "UPDATE v_active_member SET phone = '010-2222' WHERE member_id = 2")
    attempt(conn, "UPDATE v_active_member SET member_name = '이둘' WHERE member_id = 2")
    show(conn, "SELECT member_id, name, phone FROM member WHERE member_id = 2")

    print("-- 5. 트리거가 넣은 행이 뷰 조건에 안 맞으면 — 넣었는데 뷰에 안 보인다")
    attempt(conn, "INSERT INTO v_active_member VALUES (4, '최네모', NULL)")
    show(conn, "SELECT * FROM v_active_member")
    show(conn, "SELECT member_id, name, active FROM member WHERE member_id = 4")
    attempt(conn, """CREATE VIEW v_checked AS SELECT * FROM member WHERE active = 1
                     WITH CHECK OPTION""")
    print()

    print("-- 6. 뷰를 조회해도 원본 표의 인덱스를 쓴다")
    print(plan_tree(conn, "SELECT * FROM v_active_member WHERE member_id = 3"))
    print()
    print(plan_tree(conn, "SELECT * FROM v_member_total WHERE member_id = 3"))
    print()

    print("-- 7. SELECT * 로 만든 뷰와 원본 표의 컬럼 추가")
    conn.execute("CREATE VIEW v_member_all AS SELECT * FROM member")
    conn.execute("ALTER TABLE member ADD COLUMN email TEXT")
    show(conn, "SELECT * FROM v_member_all WHERE member_id = 1")
    show(conn, "SELECT * FROM v_active_member WHERE member_id = 1")

    print("-- 8. 원본 표를 지우면 뷰는 남고, 조회할 때 실패한다")
    attempt(conn, "DROP TABLE orders")
    show(conn, "SELECT name FROM sqlite_schema WHERE type = 'view' ORDER BY name")
    attempt(conn, "SELECT * FROM v_member_total")
    conn.close()


if __name__ == "__main__":
    main()
