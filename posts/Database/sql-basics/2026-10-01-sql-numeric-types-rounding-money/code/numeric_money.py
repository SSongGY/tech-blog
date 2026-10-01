"""숫자 타입과 반올림 — 돈을 다룰 때.

같은 금액을 REAL·DECIMAL(10,2)·INTEGER(센트) 세 컬럼에 나란히 넣고,
더하기·비교·나누기·반올림·형 변환에서 어느 컬럼이 어떻게 틀어지는지 본다.
SQLite 에서 DECIMAL 로 선언한 컬럼도 십진수로 저장되지 않는다는 것을 먼저 확인한다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

PRICES = [
    # (id, 상품, 가격 문자열 — 화면에서 받은 그대로)
    (1, "아메리카노", "0.10"),
    (2, "시럽 추가", "0.20"),
    (3, "머그컵", "19.99"),
    (4, "원두 1kg", "20.00"),
]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE price (
            id           INTEGER PRIMARY KEY,
            item         TEXT NOT NULL,
            amount_real  REAL,
            amount_dec   DECIMAL(10, 2),
            amount_cents INTEGER
        )
        """
    )
    # 세 컬럼에 같은 문자열을 넣는다. 저장 형태는 컬럼 선언(친화성)이 정한다
    conn.executemany(
        "INSERT INTO price VALUES (?, ?, ?, ?, ?)",
        [(i, name, text, text, round(float(text) * 100)) for i, name, text in PRICES],
    )
    conn.commit()
    return conn


def show(conn: sqlite3.Connection, label: str, sql: str) -> None:
    print(f"\n[{label}]")
    print(f"  {' '.join(sql.split())}")
    try:
        rows = conn.execute(sql).fetchall()
    except sqlite3.Error as exc:
        print(f"  에러: {type(exc).__name__}: {exc}")
        return
    for row in rows:
        print(f"  {row!r}")


def section_storage(conn: sqlite3.Connection) -> None:
    print("\n== 1. 선언한 타입과 실제로 저장된 형태 ==")
    show(conn, "1-A typeof — 저장 부류", """
        SELECT id, typeof(amount_real), typeof(amount_dec), typeof(amount_cents)
        FROM price ORDER BY id
    """)
    # printf 는 기본으로 유효숫자 16자리까지만 찍는다. '!' 를 붙여야 26자리까지 보인다
    show(conn, "1-B 0.1 은 실제로 어떤 값인가", """
        SELECT printf('%.20f', amount_real), printf('%!.20f', amount_real)
        FROM price WHERE id = 1
    """)


def section_sum(conn: sqlite3.Connection) -> None:
    print("\n== 2. 더하고 비교하기 ==")
    show(conn, "2-A 아메리카노 + 시럽", """
        SELECT SUM(amount_real), SUM(amount_dec), SUM(amount_cents)
        FROM price WHERE id IN (1, 2)
    """)
    show(conn, "2-B 합계가 0.30 과 같은가", """
        SELECT SUM(amount_real) = 0.3, SUM(amount_dec) = 0.3, SUM(amount_cents) = 30
        FROM price WHERE id IN (1, 2)
    """)
    show(conn, "2-C 0.1 을 열 번 더하면", """
        WITH RECURSIVE n(i) AS (SELECT 1 UNION ALL SELECT i + 1 FROM n WHERE i < 10)
        SELECT SUM(0.1), SUM(0.1) = 1.0, SUM(10) FROM n
    """)
    show(conn, "2-D 같은 열 번을 + 로 이어 쓰면", """
        SELECT 0.1+0.1+0.1+0.1+0.1+0.1+0.1+0.1+0.1+0.1
    """)
    print("\n[2-E 파이썬에서 같은 일을 하면]")
    print(f"  sum([0.1] * 10) = {sum([0.1] * 10)!r}")
    show(conn, "2-F decimal 확장이 들어 있는가", """
        SELECT decimal_sum(amount_real) FROM price
    """)


def section_division(conn: sqlite3.Connection) -> None:
    print("\n== 3. 나누기 — 정수끼리 나누면 몫만 남는다 ==")
    show(conn, "3-A 1000원을 세 명이 나누기", """
        SELECT 1000 / 3, 1000 % 3, 1000 / 3.0, 1000 / 3 * 3
    """)
    show(conn, "3-B 비율 계산에서", """
        SELECT 1 / 4 * 100, 1 * 100 / 4, 1.0 / 4 * 100
    """)


def section_round(conn: sqlite3.Connection) -> None:
    print("\n== 4. round — 0.5 는 어디로 가는가 ==")
    show(conn, "4-A 정확히 반인 값", """
        SELECT round(0.5), round(1.5), round(2.5), round(-2.5)
    """)
    show(conn, "4-B 소수 둘째 자리로", """
        SELECT round(0.125, 2), round(1.005, 2), round(2.675, 2)
    """)
    show(conn, "4-C 그 값들이 실제로 저장된 모양", """
        SELECT printf('%!.20f', 0.125), printf('%!.20f', 1.005), printf('%!.20f', 2.675)
    """)
    print("\n[4-D 같은 값을 파이썬 round 에 넣으면]")
    print(f"  {(round(0.5), round(1.5), round(2.5), round(-2.5))!r}")
    print(f"  {(round(0.125, 2), round(1.005, 2), round(2.675, 2))!r}")


def section_cast(conn: sqlite3.Connection) -> None:
    print("\n== 5. 달러를 센트로 바꾸기 ==")
    show(conn, "5-A 곱한 결과", """
        SELECT amount_real * 100, printf('%.2f', amount_real * 100),
               printf('%!.20f', amount_real * 100)
        FROM price WHERE id = 3
    """)
    show(conn, "5-B CAST 는 버린다", """
        SELECT CAST(amount_real * 100 AS INTEGER),
               CAST(round(amount_real * 100) AS INTEGER),
               CAST(-19.99 AS INTEGER)
        FROM price WHERE id = 3
    """)


def section_overflow(conn: sqlite3.Connection) -> None:
    print("\n== 6. 정수의 끝 ==")
    conn.execute("CREATE TABLE big (v INTEGER)")
    conn.executemany("INSERT INTO big VALUES (?)", [(9223372036854775807,), (1,)])
    show(conn, "6-A SUM 이 64비트를 넘으면", "SELECT SUM(v) FROM big")
    show(conn, "6-B total 은 실수로 더한다", "SELECT total(v), typeof(total(v)) FROM big")
    show(conn, "6-C 범위를 넘는 정수 리터럴", """
        SELECT 9223372036854775807 + 0, typeof(9223372036854775808)
    """)


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)
    section_storage(conn)
    section_sum(conn)
    section_division(conn)
    section_round(conn)
    section_cast(conn)
    section_overflow(conn)


if __name__ == "__main__":
    main()
