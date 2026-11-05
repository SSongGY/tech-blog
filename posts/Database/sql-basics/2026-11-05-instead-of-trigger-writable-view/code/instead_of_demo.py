"""조인 뷰에 쓰기를 거는 INSTEAD OF 트리거를 단계별로 확인한다."""

import sqlite3

from dbshow import print_dataset, print_environment

SCHEMA = """
CREATE TABLE member (
    member_id INTEGER PRIMARY KEY,
    name      TEXT NOT NULL
);
CREATE TABLE wallet (
    member_id INTEGER PRIMARY KEY REFERENCES member(member_id),
    balance   INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE audit_log (
    seq    INTEGER PRIMARY KEY,
    action TEXT NOT NULL
);
CREATE VIEW member_wallet AS
SELECT m.member_id, m.name, w.balance
FROM member AS m JOIN wallet AS w USING (member_id);
"""

INSTEAD_OF_TRIGGERS = """
CREATE TRIGGER member_wallet_ins INSTEAD OF INSERT ON member_wallet
BEGIN
    INSERT INTO member(member_id, name) VALUES (NEW.member_id, NEW.name);
    INSERT INTO wallet(member_id, balance) VALUES (NEW.member_id, COALESCE(NEW.balance, 0));
    INSERT INTO audit_log(action) VALUES ('insert ' || NEW.member_id);
END;
CREATE TRIGGER member_wallet_upd INSTEAD OF UPDATE ON member_wallet
BEGIN
    UPDATE member SET name = NEW.name WHERE member_id = OLD.member_id;
    UPDATE wallet SET balance = NEW.balance WHERE member_id = OLD.member_id;
    INSERT INTO audit_log(action) VALUES ('update ' || OLD.member_id);
END;
CREATE TRIGGER member_wallet_del INSTEAD OF DELETE ON member_wallet
BEGIN
    DELETE FROM wallet WHERE member_id = OLD.member_id;
    DELETE FROM member WHERE member_id = OLD.member_id;
    INSERT INTO audit_log(action) VALUES ('delete ' || OLD.member_id);
END;
"""


def try_sql(conn, label, sql, params=()):
    """에러도 결과의 일부이므로 잡아서 메시지를 그대로 찍는다."""
    try:
        cur = conn.execute(sql, params)
        print(f"{label}: 성공, rowcount={cur.rowcount}")
        return cur
    except sqlite3.Error as err:
        print(f"{label}: {type(err).__name__}: {err}")
        return None


def show(conn, sql):
    for row in conn.execute(sql):
        print("  ", row)


def main():
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.execute("INSERT INTO member VALUES (1, '가영'), (2, '나래')")
    conn.execute("INSERT INTO wallet VALUES (1, 500), (2, 800)")
    print_environment()
    print_dataset(conn)

    print("\n[1] 트리거가 없을 때 뷰에 쓰기")
    try_sql(conn, "INSERT", "INSERT INTO member_wallet VALUES (3, '다은', 100)")
    try_sql(conn, "UPDATE", "UPDATE member_wallet SET balance = 0 WHERE member_id = 1")
    try_sql(conn, "DELETE", "DELETE FROM member_wallet WHERE member_id = 1")

    print("\n[2] 뷰에는 BEFORE/AFTER 트리거를 만들 수 없다")
    try_sql(conn, "BEFORE", "CREATE TRIGGER t1 BEFORE INSERT ON member_wallet BEGIN SELECT 1; END")
    try_sql(conn, "AFTER", "CREATE TRIGGER t2 AFTER INSERT ON member_wallet BEGIN SELECT 1; END")

    conn.executescript(INSTEAD_OF_TRIGGERS)

    print("\n[3] INSTEAD OF INSERT 한 줄이 두 표에 나뉘어 들어간다")
    try_sql(conn, "INSERT", "INSERT INTO member_wallet VALUES (3, '다은', 100)")
    print("  member:")
    show(conn, "SELECT * FROM member ORDER BY member_id")
    print("  wallet:")
    show(conn, "SELECT * FROM wallet ORDER BY member_id")

    print("\n[4] 뷰에 UPDATE — 여러 행이면 트리거가 행마다 돈다")
    try_sql(conn, "UPDATE", "UPDATE member_wallet SET balance = balance + 50 WHERE balance < 600")
    show(conn, "SELECT * FROM member_wallet ORDER BY member_id")
    print("  audit_log:")
    show(conn, "SELECT * FROM audit_log ORDER BY seq")

    print("\n[5] 조건에 맞는 행이 없으면 트리거는 돌지 않는다")
    before = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    try_sql(conn, "UPDATE", "UPDATE member_wallet SET balance = 0 WHERE member_id = 99")
    after = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    print(f"  audit_log 행 수: {before} -> {after}")

    print("\n[6] 뷰에 쓴 건수는 rowcount 에 잡히지 않는다")
    before = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    try_sql(conn, "뷰 UPDATE", "UPDATE member_wallet SET balance = balance + 1")
    after = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    print(f"  트리거가 남긴 audit_log: {after - before}행 늘어남")
    try_sql(conn, "표 UPDATE", "UPDATE wallet SET balance = balance + 1")

    print("\n[7] RETURNING 은 뷰에서 쓸 수 있는가")
    cur = try_sql(conn, "INSERT RETURNING",
                  "INSERT INTO member_wallet VALUES (4, '라온', 10) RETURNING member_id")
    if cur is not None:
        print("  돌려받은 행:", cur.fetchall())

    print("\n[8] 뷰의 WHERE 에 걸리지 않는 행을 INSERT 하면")
    conn.execute(
        "CREATE VIEW rich AS SELECT member_id, name, balance FROM member_wallet WHERE balance >= 1000"
    )
    conn.execute(
        "CREATE TRIGGER rich_ins INSTEAD OF INSERT ON rich BEGIN "
        "INSERT INTO member_wallet VALUES (NEW.member_id, NEW.name, NEW.balance); END"
    )
    try_sql(conn, "INSERT INTO rich (잔액 10)", "INSERT INTO rich VALUES (5, '마루', 10)")
    print("  rich 뷰에서 보이는 행:", conn.execute("SELECT COUNT(*) FROM rich WHERE member_id = 5").fetchone()[0])
    print("  member_wallet 에서 보이는 행:",
          conn.execute("SELECT COUNT(*) FROM member_wallet WHERE member_id = 5").fetchone()[0])


if __name__ == "__main__":
    main()
