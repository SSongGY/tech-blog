"""제약 위반을 만났을 때 ABORT·FAIL·IGNORE·REPLACE·ROLLBACK 이 어디까지 되돌리는지 확인한다."""

import sqlite3

from dbshow import print_environment, print_table

ALGORITHMS = ["ABORT", "FAIL", "IGNORE", "REPLACE", "ROLLBACK"]


def connect():
    # 트랜잭션 시작·종료를 직접 다루려고 자동 시작을 끈다
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def rows(conn, sql):
    return conn.execute(sql).fetchall()


def insert_case(algorithm):
    conn = connect()
    conn.executescript(
        """
        CREATE TABLE product (
            product_id INTEGER PRIMARY KEY,
            code       TEXT NOT NULL UNIQUE,
            qty        INTEGER NOT NULL
        );
        INSERT INTO product VALUES (1, 'A', 10), (2, 'B', 20);
        """
    )
    conn.execute("BEGIN")
    conn.execute("INSERT INTO product VALUES (3, 'C', 30)")  # 이 문장 이전에 이미 넣은 행
    sql = (
        f"INSERT OR {algorithm} INTO product (product_id, code, qty) "
        "VALUES (4, 'D', 40), (5, 'B', 50), (6, 'E', 60)"
    )
    try:
        conn.execute(sql)
        outcome = "오류 없음"
    except sqlite3.Error as exc:
        outcome = f"오류: {exc}"
    in_tx = conn.in_transaction
    print(f"\n  INSERT OR {algorithm:<8} {outcome}")
    print(f"    트랜잭션 안인가: {in_tx}")
    print("    남은 행:", rows(conn, "SELECT product_id, code, qty FROM product ORDER BY product_id"))


def update_case(algorithm):
    conn = connect()
    conn.executescript(
        """
        CREATE TABLE stock (
            item_id INTEGER PRIMARY KEY,
            qty     INTEGER NOT NULL CHECK (qty >= 0)
        );
        INSERT INTO stock VALUES (1, 5), (2, 5), (3, 0), (4, 5);
        """
    )
    try:
        conn.execute(f"UPDATE OR {algorithm} stock SET qty = qty - 1")
        outcome = "오류 없음"
    except sqlite3.Error as exc:
        outcome = f"오류: {exc}"
    print(f"\n  UPDATE OR {algorithm:<8} {outcome}")
    print("    남은 행:", rows(conn, "SELECT item_id, qty FROM stock ORDER BY item_id"))


def replace_kinds():
    conn = connect()
    conn.executescript(
        """
        CREATE TABLE member (
            member_id INTEGER PRIMARY KEY,
            email     TEXT NOT NULL UNIQUE,
            grade     TEXT NOT NULL DEFAULT 'basic',
            age       INTEGER CHECK (age >= 0)
        );
        INSERT INTO member VALUES (1, 'a@x.com', 'gold', 30);
        """
    )
    print("\n  REPLACE 가 위반 종류별로 하는 일")
    for label, sql in [
        ("UNIQUE 위반", "INSERT OR REPLACE INTO member (member_id, email, age) VALUES (2, 'a@x.com', 31)"),
        ("NOT NULL 위반", "INSERT OR REPLACE INTO member (member_id, email, grade, age) VALUES (3, 'b@x.com', NULL, 20)"),
        ("CHECK 위반", "INSERT OR REPLACE INTO member (member_id, email, age) VALUES (4, 'c@x.com', -1)"),
    ]:
        try:
            conn.execute(sql)
            outcome = "오류 없음"
        except sqlite3.Error as exc:
            outcome = f"오류: {exc}"
        print(f"    {label:<14} {outcome}")
    print("    남은 행:", rows(conn, "SELECT * FROM member ORDER BY member_id"))


def replace_side_effects():
    conn = connect()
    conn.executescript(
        """
        CREATE TABLE account (
            account_id INTEGER PRIMARY KEY,
            email      TEXT NOT NULL UNIQUE,
            nickname   TEXT
        );
        CREATE TABLE login_log (
            log_id     INTEGER PRIMARY KEY,
            account_id INTEGER NOT NULL REFERENCES account (account_id) ON DELETE CASCADE
        );
        CREATE TABLE delete_audit (account_id INTEGER);
        CREATE TRIGGER account_delete AFTER DELETE ON account
        BEGIN
            INSERT INTO delete_audit VALUES (old.account_id);
        END;
        INSERT INTO account VALUES (1, 'a@x.com', '민수');
        INSERT INTO login_log VALUES (1, 1), (2, 1), (3, 1);
        """
    )
    print_table(conn, "account")
    print_table(conn, "login_log")

    conn.execute("INSERT OR REPLACE INTO account (account_id, email) VALUES (1, 'a@x.com')")
    print("\n  INSERT OR REPLACE INTO account (account_id, email) VALUES (1, 'a@x.com')")
    print("    account    :", rows(conn, "SELECT * FROM account"))
    print("    login_log  :", rows(conn, "SELECT * FROM login_log"))
    print("    delete_audit (recursive_triggers 꺼짐):", rows(conn, "SELECT * FROM delete_audit"))

    conn.execute("PRAGMA recursive_triggers = ON")
    conn.execute("INSERT OR REPLACE INTO account (account_id, email) VALUES (1, 'a@x.com')")
    print("    delete_audit (recursive_triggers 켜짐 후 한 번 더):", rows(conn, "SELECT * FROM delete_audit"))


def upsert_contrast():
    conn = connect()
    conn.executescript(
        """
        CREATE TABLE account (
            account_id INTEGER PRIMARY KEY,
            email      TEXT NOT NULL UNIQUE,
            nickname   TEXT
        );
        INSERT INTO account VALUES (1, 'a@x.com', '민수');
        """
    )
    conn.execute(
        "INSERT INTO account (account_id, email) VALUES (1, 'a@x.com') "
        "ON CONFLICT (account_id) DO UPDATE SET email = excluded.email"
    )
    print("\n  같은 입력을 UPSERT(ON CONFLICT DO UPDATE)로 넣으면")
    print("    account    :", rows(conn, "SELECT * FROM account"))


def main():
    print_environment()

    print("\n== 1. 여러 행 INSERT 중 두 번째 행이 UNIQUE 를 어긴다")
    print("   (BEGIN 후 행 3 을 먼저 넣고, 그 뒤 행 4·5·6 을 한 문장으로 넣는다. 행 5 가 'B' 와 겹친다)")
    for algorithm in ALGORITHMS:
        insert_case(algorithm)

    print("\n== 2. 여러 행 UPDATE 중 세 번째 행이 CHECK 를 어긴다 (행 3 의 qty 는 0)")
    for algorithm in ALGORITHMS:
        update_case(algorithm)

    print("\n== 3. REPLACE 는 위반 종류에 따라 다르게 행동한다")
    replace_kinds()

    print("\n== 4. REPLACE 는 지우고 다시 넣는다")
    replace_side_effects()
    upsert_contrast()


if __name__ == "__main__":
    main()
