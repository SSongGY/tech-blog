"""SQLite 컬럼에 선언한 타입과 실제로 저장되는 값의 종류가 어떻게 갈리는지 typeof()로 확인한다.

같은 값을 친화성이 다른 다섯 컬럼에 넣어 보고, 선언 이름이 어떤 친화성으로 읽히는지,
그 차이가 WHERE 비교와 ORDER BY에서 어떻게 드러나는지, STRICT 표는 무엇을 막는지 본다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

# 다른 DB에서 옮겨 오며 흔히 쓰는 선언을 그대로 둔다. 친화성은 이 이름에서 정해진다.
SCHEMA = """
CREATE TABLE customer (
    id        INTEGER PRIMARY KEY,
    name      VARCHAR(20),
    zip_code  STRING,
    phone     TEXT,
    point     INTEGER,
    memo
);
"""

SEED = [
    (1, "김도윤", "06236", "01012345678", "1500", "VIP"),
    (2, "이서준", "04524", "01098765432", "800", 10),
    (3, "박하은", "13529", "0215881234", "1,200", "10"),
]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO customer VALUES (?, ?, ?, ?, ?, ?)", SEED)
    conn.commit()
    return conn


def query(conn: sqlite3.Connection, label: str, sql: str) -> None:
    print(f"\n[{label}]")
    print(f"  {' '.join(sql.split())}")
    cur = conn.execute(sql)
    print(f"  {tuple(col[0] for col in cur.description)}")
    for row in cur.fetchall():
        print(f"  {row}")


def run(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> None:
    """막히는 문장도 결과로 찍는다. STRICT가 무엇을 거부하는지가 내용이다."""
    shown = " ".join(sql.split())
    if params:
        shown += f"   값={params!r}"
    try:
        conn.execute(sql, params)
        print(f"  성공  {shown}")
    except sqlite3.Error as exc:
        print(f"  에러  {shown}\n        -> {type(exc).__name__}: {exc}")


def show_affinity_by_value(conn: sqlite3.Connection) -> None:
    """같은 입력이 컬럼 친화성에 따라 다른 저장 부류로 바뀌는지 본다."""
    conn.execute(
        """CREATE TABLE probe_value (
               input   TEXT,
               t_col   TEXT,
               n_col   NUMERIC,
               i_col   INTEGER,
               r_col   REAL,
               b_col
           )"""
    )
    # 파이썬 값이 무엇으로 넘어가는지(문자열인지 정수인지)가 결과를 가르므로 repr로 남긴다
    inputs = ["42", "007", "3.0e+5", "4.50", "0x1F", "1,200", "abc", 12, 12.0, 4.5]
    for value in inputs:
        conn.execute(
            "INSERT INTO probe_value VALUES (?, ?, ?, ?, ?, ?)",
            (repr(value), value, value, value, value, value),
        )
    query(
        conn,
        "1-A 같은 값을 다섯 친화성 컬럼에 넣은 결과 — 값|typeof",
        """SELECT input,
                  quote(t_col) || '|' || typeof(t_col) AS "TEXT",
                  quote(n_col) || '|' || typeof(n_col) AS "NUMERIC",
                  quote(i_col) || '|' || typeof(i_col) AS "INTEGER",
                  quote(r_col) || '|' || typeof(r_col) AS "REAL",
                  quote(b_col) || '|' || typeof(b_col) AS "BLOB"
           FROM probe_value""",
    )


def show_affinity_by_name(conn: sqlite3.Connection) -> None:
    """선언 이름만 다르고 같은 글자 '0123'을 넣었을 때 무엇이 남는지 본다."""
    declared = [
        "VARCHAR(10)",
        "CHARINT",
        "STRING",
        "FLOATING POINT",
        "DOUBLE",
        "DATETIME",
        "BOOLEAN",
        "DECIMAL(10,2)",
        "BLOB",
        "",
    ]
    columns = ", ".join(f'"c{i}" {name}' for i, name in enumerate(declared))
    conn.execute(f"CREATE TABLE probe_name ({columns})")
    conn.execute(
        f"INSERT INTO probe_name VALUES ({', '.join('?' * len(declared))})",
        ["0123"] * len(declared),
    )
    row = conn.execute(
        "SELECT "
        + ", ".join(f'quote("c{i}"), typeof("c{i}")' for i in range(len(declared)))
        + " FROM probe_name"
    ).fetchone()
    print("\n[2-A 선언 이름별로 '0123'을 넣은 결과]")
    print(f"  {'선언':<16} {'저장된 값':<10} typeof")
    for i, name in enumerate(declared):
        print(f"  {name or '(없음)':<16} {row[i * 2]:<10} {row[i * 2 + 1]}")


def show_comparison(conn: sqlite3.Connection) -> None:
    query(
        conn,
        "3-A 우편번호를 숫자로 찾으면",
        "SELECT id, zip_code, typeof(zip_code) FROM customer WHERE zip_code = 6236",
    )
    query(
        conn,
        "3-B 글자로 찾으면",
        "SELECT id, zip_code FROM customer WHERE zip_code = '06236'",
    )
    query(
        conn,
        "3-C 친화성 없는 memo 컬럼은 10 과 '10' 을 다르게 본다",
        """SELECT id, quote(memo) AS memo, typeof(memo),
                  memo = 10 AS eq_int, memo = '10' AS eq_text
           FROM customer""",
    )
    query(
        conn,
        "3-D phone(TEXT)과 숫자를 비교하면 숫자 쪽이 글자로 바뀐다",
        "SELECT id, phone FROM customer WHERE phone = 01012345678",
    )
    query(
        conn,
        "3-D2 숫자로 적은 01012345678 은 이미 앞자리 0이 없다",
        "SELECT 01012345678 AS literal, typeof(01012345678), CAST(01012345678 AS TEXT)",
    )
    # 별칭을 컬럼 이름과 같게 두면 ORDER BY 가 quote() 결과(글자)를 정렬하므로 다른 이름을 쓴다
    query(
        conn,
        "3-E 정수와 글자가 섞인 point 를 큰 값부터 정렬하면",
        """SELECT id, quote(point) AS point_shown, typeof(point)
           FROM customer ORDER BY point DESC""",
    )
    query(
        conn,
        "3-F 합계에서 글자 '1,200'은 앞의 숫자 부분만 더해진다",
        """SELECT sum(point) AS total, typeof(sum(point)) AS total_type,
                  CAST('1,200' AS INTEGER) AS cast_int
           FROM customer""",
    )


def show_strict(conn: sqlite3.Connection) -> None:
    run(conn, "CREATE TABLE probe_strict_bad (zip_code VARCHAR(5)) STRICT")
    run(
        conn,
        """CREATE TABLE customer_strict (
               id        INTEGER PRIMARY KEY,
               zip_code  TEXT,
               point     INTEGER,
               memo      ANY
           ) STRICT""",
    )
    run(conn, "INSERT INTO customer_strict VALUES (1, '06236', '1500', '10')")
    run(conn, "INSERT INTO customer_strict VALUES (2, 6236, 800, 10)")
    run(conn, "INSERT INTO customer_strict VALUES (3, '13529', '1,200', 10)")
    run(conn, "INSERT INTO customer_strict VALUES (4, '04524', 3.5, 10)")
    query(
        conn,
        "4-A STRICT 표에 들어간 값",
        """SELECT id, quote(zip_code), typeof(zip_code), quote(point), typeof(point),
                  quote(memo), typeof(memo)
           FROM customer_strict""",
    )


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("\n== 0. customer 에 실제로 저장된 종류 ==")
    query(
        conn,
        "0-A typeof",
        """SELECT id, quote(zip_code), typeof(zip_code), quote(phone), typeof(phone),
                  quote(point), typeof(point), quote(memo), typeof(memo)
           FROM customer""",
    )

    print("\n== 1. 값은 컬럼 친화성에 따라 바뀐다 ==")
    show_affinity_by_value(conn)

    print("\n== 2. 친화성은 선언 이름의 글자로 정해진다 ==")
    show_affinity_by_name(conn)

    print("\n== 3. 비교와 정렬 ==")
    show_comparison(conn)

    print("\n== 4. STRICT 표 ==")
    show_strict(conn)


if __name__ == "__main__":
    main()
