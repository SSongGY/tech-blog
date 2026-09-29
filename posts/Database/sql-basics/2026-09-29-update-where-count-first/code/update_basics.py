"""UPDATE 에서 WHERE 를 빠뜨렸을 때와, 그것을 막는 절차를 확인한다.

절차는 네 단계다. 같은 조건으로 먼저 센다 → 트랜잭션 안에서 UPDATE 한다 →
바뀐 행 수가 센 값과 같은지 본다 → 같으면 COMMIT, 다르면 ROLLBACK.
"""

import sqlite3

from dbshow import print_dataset, print_environment

SCHEMA = """
CREATE TABLE member (
    member_id  INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    grade      TEXT NOT NULL,
    point      INTEGER NOT NULL
);
INSERT INTO member (member_id, name, grade, point) VALUES
    (1, '김하나', 'basic', 1200),
    (2, '이두리', 'gold',  5400),
    (3, '박세찬', 'basic',  300),
    (4, '정가람', 'basic', 2500),
    (5, '한별',   'gold',  8100);
"""


def show(conn, sql):
    print(f"   {sql}")
    for row in conn.execute(sql).fetchall():
        print("   " + " | ".join(str(v) for v in row))
    print()


def safe_update(conn, count_where, update_sql):
    """센 값과 바뀐 행 수가 다르면 되돌린다.

    센 조건과 UPDATE 를 따로 받는 것은, 옮겨 적다 어긋나는 경우를 3장에서 보이려는 것이다.
    """
    count_sql = f"SELECT COUNT(*) FROM member WHERE {count_where}"
    expected = conn.execute(count_sql).fetchone()[0]
    print(f"   {count_sql}  → {expected}")
    conn.execute("BEGIN")
    changed = conn.execute(update_sql).rowcount
    print(f"   {update_sql}  → 바뀐 행 {changed}")
    if changed == expected:
        conn.execute("COMMIT")
        print("   같으므로 COMMIT")
    else:
        conn.execute("ROLLBACK")
        print("   다르므로 ROLLBACK")
    print()


def main():
    print_environment()
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.executescript(SCHEMA)
    print_dataset(conn)

    print("-- 1. WHERE 를 빠뜨리면 — 트랜잭션 안에서 돌리고 되돌린다")
    conn.execute("BEGIN")
    changed = conn.execute("UPDATE member SET grade = 'gold'").rowcount
    print(f"   UPDATE member SET grade = 'gold'  → 바뀐 행 {changed}")
    show(conn, "SELECT grade, COUNT(*) FROM member GROUP BY grade")
    conn.execute("ROLLBACK")
    print("   ROLLBACK 뒤")
    show(conn, "SELECT grade, COUNT(*) FROM member GROUP BY grade")

    print("-- 2. 절차대로 — 포인트 2000 이상인 basic 회원을 gold 로")
    safe_update(
        conn,
        "grade = 'basic' AND point >= 2000",
        "UPDATE member SET grade = 'gold' WHERE grade = 'basic' AND point >= 2000",
    )
    show(conn, "SELECT member_id, name, grade, point FROM member ORDER BY member_id")

    print("-- 3. 센 조건을 UPDATE 로 옮기다 AND 를 OR 로 적었다")
    safe_update(
        conn,
        "grade = 'basic' AND point < 500",
        "UPDATE member SET point = point + 100 WHERE grade = 'basic' OR point < 500",
    )
    show(conn, "SELECT member_id, name, grade, point FROM member ORDER BY member_id")

    print("-- 4. 값이 그대로여도 바뀐 행으로 센다")
    changed = conn.execute(
        "UPDATE member SET grade = 'gold' WHERE grade = 'gold'"
    ).rowcount
    print(f"   UPDATE member SET grade = 'gold' WHERE grade = 'gold'  → 바뀐 행 {changed}")
    print()

    print("-- 5. SET 의 오른쪽은 바뀌기 전 값을 읽는다 — 두 컬럼 맞바꾸기")
    conn.execute("CREATE TABLE pair (a INTEGER, b INTEGER)")
    conn.execute("INSERT INTO pair VALUES (1, 2)")
    conn.execute("UPDATE pair SET a = b, b = a")
    show(conn, "SELECT a, b FROM pair")

    print("-- 6. RETURNING — 바뀐 행을 그 자리에서 돌려받는다")
    sql = ("UPDATE member SET point = point - 300 WHERE member_id = 3 "
           "RETURNING member_id, name, point")
    show(conn, sql)

    conn.close()


if __name__ == "__main__":
    main()
