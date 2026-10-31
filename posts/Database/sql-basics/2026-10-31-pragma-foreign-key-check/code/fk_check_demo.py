"""외래키를 끈 채 쌓인 데이터에 제약을 걸기 전, PRAGMA foreign_key_check 로
깨진 참조를 먼저 찾아낸다.

SQLite 는 외래키 강제가 기본으로 꺼져 있다(PRAGMA foreign_keys = OFF).
그래서 스키마에 REFERENCES 를 적어 두고도 부모 없는 자식 행이 쌓일 수 있다.
나중에 PRAGMA foreign_keys = ON 으로 켜도 이미 들어 있는 행은 검사되지 않는다.
켜기 전에 무엇이 깨져 있는지 세는 것이 foreign_key_check 다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

SCHEMA = """
CREATE TABLE team (
    team_id   INTEGER PRIMARY KEY,
    team_name TEXT NOT NULL
);

CREATE TABLE employee (
    emp_id    INTEGER PRIMARY KEY,
    emp_name  TEXT NOT NULL,
    team_id   INTEGER REFERENCES team(team_id),
    mentor_id INTEGER REFERENCES employee(emp_id)
);

CREATE TABLE badge (
    badge_code TEXT PRIMARY KEY,
    emp_id     INTEGER REFERENCES employee(emp_id)
) WITHOUT ROWID;
"""

SEED = """
INSERT INTO team VALUES (10, '플랫폼'), (20, '데이터');

INSERT INTO employee VALUES
    (1, '김하늘', 10, NULL),
    (2, '박도윤', 20, 1),
    (3, '이서아', 30, 1),      -- team 30 은 없다
    (4, '최민준', 10, 99),     -- employee 99 는 없다
    (5, '정예준', NULL, NULL); -- NULL 은 위반이 아니다

INSERT INTO badge VALUES
    ('B-001', 1),
    ('B-002', 77);             -- employee 77 은 없다
"""


def build_database() -> sqlite3.Connection:
    """외래키 강제를 끈 채로 데이터를 넣는다 — 운영에서 흔히 이 상태가 된다."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.executescript(SCHEMA)
    conn.executescript(SEED)
    return conn


def show(conn: sqlite3.Connection, label: str, sql: str) -> None:
    print(f"\n-- {label}")
    print(f"   {sql}")
    rows = conn.execute(sql).fetchall()
    if not rows:
        print("   (0행)")
        return
    for row in rows:
        print(f"   {row}")


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("\n" + "=" * 64)
    print("1. 제약을 켜기만 하면 기존 행이 검사되는가")
    print("=" * 64)
    conn.execute("PRAGMA foreign_keys = ON")
    show(conn, "강제 설정 상태", "PRAGMA foreign_keys")
    show(conn, "깨진 행이 그대로 남아 있다",
         "SELECT emp_id, emp_name, team_id FROM employee WHERE team_id = 30")

    print("\n" + "=" * 64)
    print("2. PRAGMA foreign_key_check 가 돌려주는 네 칸")
    print("=" * 64)
    cur = conn.execute("PRAGMA foreign_key_check")
    print("   컬럼:", [d[0] for d in cur.description])
    for row in cur.fetchall():
        print("   ", row)

    show(conn, "표 하나만 검사한다", "PRAGMA foreign_key_check(employee)")

    print("\n" + "=" * 64)
    print("3. 네 번째 칸(fkid)은 foreign_key_list 의 id 와 같다")
    print("=" * 64)
    cur = conn.execute("PRAGMA foreign_key_list(employee)")
    print("   컬럼:", [d[0] for d in cur.description])
    for row in cur.fetchall():
        print("   ", row)

    print("\n" + "=" * 64)
    print("4. rowid 로 깨진 행을 집어 낸다")
    print("=" * 64)
    show(conn, "fkid 1 번(team_id) 을 위반한 행",
         "SELECT e.emp_id, e.emp_name, e.team_id "
         "FROM pragma_foreign_key_check('employee') AS c "
         "JOIN employee AS e ON e.rowid = c.rowid "
         "WHERE c.fkid = 1")
    show(conn, "fkid 0 번(mentor_id) 을 위반한 행",
         "SELECT e.emp_id, e.emp_name, e.mentor_id "
         "FROM pragma_foreign_key_check('employee') AS c "
         "JOIN employee AS e ON e.rowid = c.rowid "
         "WHERE c.fkid = 0")

    print("\n" + "=" * 64)
    print("5. WITHOUT ROWID 표는 두 번째 칸이 NULL 이다")
    print("=" * 64)
    cur = conn.execute("PRAGMA foreign_key_check(badge)")
    for row in cur.fetchall():
        print("   ", row)

    print("\n" + "=" * 64)
    print("6. 고치고 다시 센다")
    print("=" * 64)
    conn.execute("INSERT INTO team VALUES (30, '보안')")
    conn.execute("UPDATE employee SET mentor_id = NULL WHERE emp_id = 4")
    conn.execute("DELETE FROM badge WHERE badge_code = 'B-002'")
    show(conn, "남은 위반", "PRAGMA foreign_key_check")

    print("\n" + "=" * 64)
    print("7. 이제 새 위반은 들어오지 못한다")
    print("=" * 64)
    try:
        conn.execute("INSERT INTO employee VALUES (6, '한지우', 40, NULL)")
    except sqlite3.IntegrityError as exc:
        print(f"   sqlite3.IntegrityError: {exc}")

    print("\n" + "=" * 64)
    print("8. 트랜잭션 안에서는 강제를 끄지 못한다")
    print("=" * 64)
    print(f"   conn.in_transaction = {conn.in_transaction}")
    conn.execute("PRAGMA foreign_keys = OFF")
    show(conn, "OFF 를 넣었는데 값이 그대로다", "PRAGMA foreign_keys")
    try:
        conn.execute("INSERT INTO employee VALUES (7, '오시윤', 50, NULL)")
    except sqlite3.IntegrityError as exc:
        print(f"   sqlite3.IntegrityError: {exc}")

    print("\n" + "=" * 64)
    print("9. 커밋해서 트랜잭션을 닫은 뒤에야 꺼진다")
    print("=" * 64)
    conn.commit()
    print(f"   conn.in_transaction = {conn.in_transaction}")
    conn.execute("PRAGMA foreign_keys = OFF")
    show(conn, "이번에는 꺼졌다", "PRAGMA foreign_keys")
    conn.execute("INSERT INTO employee VALUES (7, '오시윤', 50, NULL)")
    show(conn, "그리고 깨진 행이 다시 쌓인다",
         "PRAGMA foreign_key_check(employee)")

    conn.close()


if __name__ == "__main__":
    main()
