"""선언한 타입과 실제로 저장되는 값이 어떻게 갈리는지 typeof() 로 확인한다.

1) 선언 타입 문자열이 어느 친화성으로 접히는지 (규칙은 위에서 아래로 첫 일치)
2) 같은 값 '42' 를 친화성이 다른 컬럼에 넣으면 무엇으로 저장되는지
3) 변환이 안 되는 값은 그대로 저장되는지
4) CAST 는 친화성과 달리 값을 강제로 바꾸는지
5) 비교할 때 친화성이 한쪽 값을 바꾸는지
"""
import sqlite3

from dbshow import print_dataset, print_environment

DECLARED_TYPES = [
    "INT", "BIGINT", "VARCHAR(20)", "TEXT", "DECIMAL(10,2)", "FLOAT",
    "DOUBLE", "BOOLEAN", "DATE", "FLOATING POINT", "STRING", "BLOB", "",
]


def affinity_of(declared: str) -> str:
    """SQLite 가 문서에 적은 순서 그대로 선언 문자열을 친화성으로 접는다."""
    upper = declared.upper()
    if "INT" in upper:
        return "INTEGER"
    if "CHAR" in upper or "CLOB" in upper or "TEXT" in upper:
        return "TEXT"
    if "BLOB" in upper or upper == "":
        return "BLOB"
    if "REAL" in upper or "FLOA" in upper or "DOUB" in upper:
        return "REAL"
    return "NUMERIC"


def show(title: str, conn: sqlite3.Connection, sql: str) -> None:
    print()
    print(f"-- {title}")
    print(f"   {sql}")
    for row in conn.execute(sql):
        print("  ", row)


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE sample (
            id        INTEGER PRIMARY KEY,
            as_int    INT,
            as_text   VARCHAR(20),
            as_num    DECIMAL(10,2),
            as_real   DOUBLE,
            as_none   BLOB
        );
        """
    )
    # 같은 문자열을 여섯 컬럼에 그대로 넣는다. 바인딩 값은 전부 TEXT 다.
    for value in ("42", "42.0", "3.14", "007", "abc", " 12 "):
        conn.execute(
            "INSERT INTO sample (as_int, as_text, as_num, as_real, as_none) "
            "VALUES (?, ?, ?, ?, ?)",
            (value,) * 5,
        )
    conn.execute(
        "INSERT INTO sample (as_int, as_text, as_num, as_real, as_none) "
        "VALUES (42, 42, 42, 42, 42)"
    )
    conn.execute(
        "INSERT INTO sample (as_int, as_text, as_num, as_real, as_none) "
        "VALUES (3.0, 3.0, 3.0, 3.0, 3.0)"
    )
    conn.commit()
    return conn


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print()
    print("=" * 64)
    print("1) 선언 타입 문자열 -> 친화성 (문서의 다섯 규칙을 위에서 아래로)")
    print("=" * 64)
    for declared in DECLARED_TYPES:
        label = declared if declared else "(선언 없음)"
        print(f"  {label:<16} -> {affinity_of(declared)}")

    print()
    print("=" * 64)
    print("2) 컬럼별 저장 결과 — 값, typeof")
    print("=" * 64)
    for column in ("as_int", "as_text", "as_num", "as_real", "as_none"):
        show(
            f"{column}",
            conn,
            f"SELECT id, {column}, typeof({column}) FROM sample ORDER BY id",
        )

    print()
    print("=" * 64)
    print("3) CAST 는 친화성과 다르다")
    print("=" * 64)
    show(
        "CAST 는 값을 강제로 바꾼다. 'abc' 도 0 이 된다",
        conn,
        "SELECT CAST('abc' AS INTEGER), CAST('12abc' AS INTEGER), "
        "CAST(' 12 ' AS INTEGER), CAST('3.9' AS INTEGER), CAST(42 AS TEXT)",
    )
    show(
        "CAST 결과의 typeof",
        conn,
        "SELECT typeof(CAST('42' AS INTEGER)), typeof(CAST(42 AS TEXT)), "
        "typeof(CAST('42' AS NUMERIC)), typeof(CAST('4.5' AS NUMERIC))",
    )

    print()
    print("=" * 64)
    print("4) 비교에서의 친화성 — 컬럼과 리터럴을 비교할 때")
    print("=" * 64)
    show(
        "as_int(INTEGER 친화성) = '42' : 리터럴이 숫자로 바뀌어 비교된다",
        conn,
        "SELECT id FROM sample WHERE as_int = '42' ORDER BY id",
    )
    show(
        "as_none(BLOB 친화성) = '42' : 변환이 없어 TEXT 와 INTEGER 는 다른 값이다",
        conn,
        "SELECT id, typeof(as_none) FROM sample WHERE as_none = '42' ORDER BY id",
    )
    show(
        "친화성이 없는 표현식끼리: 42 = '42'",
        conn,
        "SELECT 42 = '42', CAST(42 AS TEXT) = '42'",
    )
    show(
        "as_text(TEXT 친화성) = 42 : 숫자 쪽이 TEXT 로 바뀌어 비교된다",
        conn,
        "SELECT id, as_text, typeof(as_text) FROM sample WHERE as_text = 42 ORDER BY id",
    )

    conn.close()


if __name__ == "__main__":
    main()
