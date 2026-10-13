"""CHECK 제약이 무엇을 막고 무엇을 못 막는지 SQLite 로 확인한다.

의존성 없음. `python check_constraint.py` 로 그대로 돌아간다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

SCHEMA = """
CREATE TABLE product (
    id        INTEGER PRIMARY KEY,
    name      TEXT    NOT NULL,
    price     INTEGER NOT NULL CHECK (price >= 0),
    discount  INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT discount_within_price CHECK (discount BETWEEN 0 AND price)
);

INSERT INTO product (id, name, price, discount) VALUES
    (1, '기계식 키보드', 89000, 9000),
    (2, '무선 마우스',   32000,    0),
    (3, '모니터 암',    145000, 20000);
"""


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    return conn


def attempt(conn: sqlite3.Connection, label: str, sql: str, *params) -> None:
    """한 문장을 돌려 보고 통과했는지 막혔는지만 한 줄로 찍는다."""
    try:
        conn.execute(sql, params)
        print(f"  [통과] {label}")
    except sqlite3.Error as exc:
        print(f"  [거부] {label}\n         {type(exc).__name__}: {exc}")


def section(title: str) -> None:
    print(f"\n{'=' * 64}\n{title}\n{'=' * 64}")


def demo_basic(conn: sqlite3.Connection) -> None:
    section("1. 범위를 벗어난 값은 INSERT 도 UPDATE 도 막힌다")
    attempt(conn, "정상 삽입", "INSERT INTO product VALUES (4, 'USB 허브', 24000, 2000)")
    attempt(conn, "가격이 음수", "INSERT INTO product VALUES (5, '케이블', -1000, 0)")
    attempt(conn, "할인이 가격보다 큼",
            "INSERT INTO product VALUES (6, '독', 99000, 120000)")
    attempt(conn, "UPDATE 로 음수를 만들기",
            "UPDATE product SET price = -1 WHERE id = 1")

    section("2. NULL 은 위반이 아니다")
    conn.executescript("CREATE TABLE memo (score INTEGER CHECK (score BETWEEN 0 AND 100));")
    attempt(conn, "NULL 삽입", "INSERT INTO memo VALUES (NULL)")
    attempt(conn, "101 삽입", "INSERT INTO memo VALUES (101)")
    print("  memo 에 남은 행:", conn.execute("SELECT score FROM memo").fetchall())


def demo_text_leak(conn: sqlite3.Connection) -> None:
    section("3. 한쪽만 막은 CHECK 는 문자열을 통과시킨다")
    conn.executescript("""
    CREATE TABLE one_sided (v INTEGER CHECK (v >= 0));
    CREATE TABLE two_sided (v INTEGER CHECK (v BETWEEN 0 AND 100));
    """)
    attempt(conn, "one_sided 에 'abc'", "INSERT INTO one_sided VALUES (?)", "abc")
    attempt(conn, "two_sided 에 'abc'", "INSERT INTO two_sided VALUES (?)", "abc")
    print("  one_sided 에 저장된 것:",
          conn.execute("SELECT v, typeof(v) FROM one_sided").fetchall())

    print("\n  왜 통과하나 — 비교 결과를 직접 본다")
    for expr in ("'abc' >= 0", "'abc' <= 100", "'abc' BETWEEN 0 AND 100"):
        print(f"    {expr:24} -> {conn.execute('SELECT ' + expr).fetchone()[0]}")

    print("\n  숫자로 읽히는 문자열은 컬럼 친화성이 먼저 바꿔 놓는다")
    conn.executescript("CREATE TABLE affinity_demo (v INTEGER);")
    for raw in ("50", "7.5", "1e3", "abc"):
        conn.execute("INSERT INTO affinity_demo VALUES (?)", (raw,))
    print("   ", conn.execute("SELECT v, typeof(v) FROM affinity_demo").fetchall())


def demo_tighten(conn: sqlite3.Connection) -> None:
    section("4. 타입까지 막는 두 가지 방법")
    conn.executescript("""
    CREATE TABLE typed_check (
        v INTEGER CHECK (typeof(v) = 'integer' AND v BETWEEN 0 AND 100)
    );
    CREATE TABLE strict_table (v INTEGER CHECK (v BETWEEN 0 AND 100)) STRICT;
    """)
    for label, table in (("typeof() 를 넣은 CHECK", "typed_check"),
                         ("STRICT 표", "strict_table")):
        print(f"  {label}")
        attempt(conn, "  50", f"INSERT INTO {table} VALUES (?)", 50)
        attempt(conn, "  'abc'", f"INSERT INTO {table} VALUES (?)", "abc")
        attempt(conn, "  NULL", f"INSERT INTO {table} VALUES (?)", None)


def demo_silent_skip(conn: sqlite3.Connection) -> None:
    section("5. OR IGNORE 와 PRAGMA 는 CHECK 를 조용히 건너뛴다")
    conn.executescript("CREATE TABLE batch (v INTEGER CHECK (v > 0));")
    attempt(conn, "3행 중 2번째가 위반 (그냥 INSERT)",
            "INSERT INTO batch VALUES (1), (-1), (3)")
    print("  batch 내용:", conn.execute("SELECT v FROM batch").fetchall())
    attempt(conn, "같은 3행을 INSERT OR IGNORE 로",
            "INSERT OR IGNORE INTO batch VALUES (1), (-1), (3)")
    print("  batch 내용:", conn.execute("SELECT v FROM batch").fetchall())

    conn.execute("PRAGMA ignore_check_constraints = ON")
    attempt(conn, "PRAGMA 를 켠 채 -99 삽입", "INSERT INTO batch VALUES (-99)")
    conn.execute("PRAGMA ignore_check_constraints = OFF")
    print("  PRAGMA 를 끈 뒤 batch 내용:",
          conn.execute("SELECT v FROM batch").fetchall())

    print("\n  표 수준 CHECK 에 붙인 ON CONFLICT 는 받아들여지지만 효과가 없다")
    attempt(conn, "CREATE (표 수준 + ON CONFLICT IGNORE)",
            "CREATE TABLE legacy (v INTEGER, CHECK (v > 0) ON CONFLICT IGNORE)")
    attempt(conn, "legacy 에 -1 삽입", "INSERT INTO legacy VALUES (-1)")
    attempt(conn, "CREATE (컬럼 수준 + ON CONFLICT IGNORE)",
            "CREATE TABLE legacy2 (v INTEGER CHECK (v > 0) ON CONFLICT IGNORE)")


def demo_existing_violations(conn: sqlite3.Connection) -> None:
    section("6. 이미 제약을 어긴 데이터가 있는 표")
    conn.executescript("""
    CREATE TABLE score (id INTEGER PRIMARY KEY, name TEXT, v INTEGER);
    INSERT INTO score VALUES
        (1, '김', 80), (2, '이', 150), (3, '박', -3), (4, '최', NULL);
    """)
    attempt(conn, "ALTER TABLE ... ADD CONSTRAINT",
            "ALTER TABLE score ADD CONSTRAINT c CHECK (v BETWEEN 0 AND 100)")

    print("\n  붙이기 전에 어긴 행부터 센다")
    print("    NOT (v BETWEEN 0 AND 100) 만:",
          conn.execute("SELECT id FROM score "
                       "WHERE NOT (v BETWEEN 0 AND 100)").fetchall())
    print("    IS NULL 을 더하면:",
          conn.execute("SELECT id FROM score WHERE v IS NULL "
                       "OR NOT (v BETWEEN 0 AND 100)").fetchall())

    print("\n  표를 새로 만들어 옮기면 한 행만 어겨도 문장 전체가 멈춘다")
    conn.executescript("""
    CREATE TABLE score_new (
        id INTEGER PRIMARY KEY, name TEXT,
        v  INTEGER NOT NULL CHECK (v BETWEEN 0 AND 100)
    );
    """)
    attempt(conn, "통째로 INSERT SELECT",
            "INSERT INTO score_new SELECT id, name, v FROM score")
    print("  score_new 행수:",
          conn.execute("SELECT count(*) FROM score_new").fetchone()[0])

    print("\n  값을 먼저 고친 뒤 옮긴다")
    attempt(conn, "범위로 자르고 NULL 은 0 으로",
            "INSERT INTO score_new "
            "SELECT id, name, max(0, min(100, coalesce(v, 0))) FROM score")
    print("  score_new 내용:",
          conn.execute("SELECT id, name, v FROM score_new").fetchall())


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)
    demo_basic(conn)
    demo_text_leak(conn)
    demo_tighten(conn)
    demo_silent_skip(conn)
    demo_existing_violations(conn)


if __name__ == "__main__":
    main()
