"""COALESCE와 NULLIF — NULL이 연산·비교·집계에서 어떻게 움직이는지 본다.

주문 표에 할인액이 비어 있는 행(NULL)과 전화번호가 빈 문자열('')인 행이 섞여 있다.
결제액을 계산하고, 할인 조건으로 거르고, 평균을 내면서 NULL이 어디서 결과를
바꾸는지 확인한 뒤 COALESCE와 NULLIF로 고친다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

ORDERS = [
    # (id, 고객, 정가, 할인액, 수량, 휴대폰, 집전화)
    (1, "김도윤", 30000, 3000, 1, "010-1111-2222", None),
    (2, "이서준", 45000, None, 2, "", "02-333-4444"),
    (3, "박하은", 12000, 0, 0, "010-5555-6666", "031-777-8888"),
    (4, "최유나", 28000, None, 1, None, None),
    (5, "정민호", 50000, 5000, 3, "", None),
]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE customer_order (
            id          INTEGER PRIMARY KEY,
            customer    TEXT    NOT NULL,
            list_price  INTEGER NOT NULL,
            discount    INTEGER,
            quantity    INTEGER NOT NULL,
            mobile      TEXT,
            home_phone  TEXT
        )
        """
    )
    conn.executemany(
        "INSERT INTO customer_order VALUES (?, ?, ?, ?, ?, ?, ?)", ORDERS
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
        print(f"  {row}")
    print(f"  -> {len(rows)}행")


def section_arithmetic(conn: sqlite3.Connection) -> None:
    print("\n== 1. 연산 — NULL이 하나라도 끼면 결과가 NULL ==")
    show(conn, "1-A 정가 - 할인액", """
        SELECT id, list_price, discount, list_price - discount AS pay
        FROM customer_order ORDER BY id""")
    show(conn, "1-B COALESCE(할인액, 0)으로 바꿔 빼면", """
        SELECT id, list_price - COALESCE(discount, 0) AS pay
        FROM customer_order ORDER BY id""")
    show(conn, "1-C 문자열 잇기도 같다", """
        SELECT id, customer || ' / ' || home_phone AS label
        FROM customer_order ORDER BY id""")


def section_comparison(conn: sqlite3.Connection) -> None:
    print("\n== 2. 비교 — NULL과의 비교는 참도 거짓도 아니다 ==")
    show(conn, "2-A discount = NULL", """
        SELECT id FROM customer_order WHERE discount = NULL""")
    show(conn, "2-B discount IS NULL", """
        SELECT id FROM customer_order WHERE discount IS NULL""")
    show(conn, "2-C discount <> 3000 (할인 3000원이 아닌 주문)", """
        SELECT id FROM customer_order WHERE discount <> 3000 ORDER BY id""")
    show(conn, "2-D 비교식 자체의 값", """
        SELECT NULL = NULL, NULL <> 1, NULL IS NULL, 1 IS NOT NULL""")


def section_aggregate(conn: sqlite3.Connection) -> None:
    print("\n== 3. 집계 — 집계 함수는 NULL 행을 건너뛴다 ==")
    show(conn, "3-A COUNT(*) 와 COUNT(discount)", """
        SELECT COUNT(*), COUNT(discount) FROM customer_order""")
    show(conn, "3-B SUM·AVG 할인액", """
        SELECT SUM(discount), AVG(discount) FROM customer_order""")
    show(conn, "3-C NULL을 0으로 치고 평균", """
        SELECT AVG(COALESCE(discount, 0)) FROM customer_order""")
    show(conn, "3-D 조건에 맞는 행이 없을 때 SUM", """
        SELECT SUM(discount), COALESCE(SUM(discount), 0)
        FROM customer_order WHERE list_price > 100000""")


def section_coalesce(conn: sqlite3.Connection) -> None:
    print("\n== 4. COALESCE — 인자 여럿 중 첫 번째 NULL 아닌 값 ==")
    show(conn, "4-A 휴대폰, 없으면 집전화, 둘 다 없으면 '연락처 없음'", """
        SELECT id, COALESCE(mobile, home_phone, '연락처 없음') AS contact
        FROM customer_order ORDER BY id""")


def section_nullif(conn: sqlite3.Connection) -> None:
    print("\n== 5. NULLIF — 두 값이 같으면 NULL ==")
    show(conn, "5-A NULLIF 의 값", """
        SELECT NULLIF(3, 3), NULLIF(3, 4), NULLIF('', ''), NULLIF(NULL, 1)""")
    show(conn, "5-B 빈 문자열을 NULL로 바꾼 뒤 COALESCE", """
        SELECT id,
               COALESCE(NULLIF(mobile, ''), home_phone, '연락처 없음') AS contact
        FROM customer_order ORDER BY id""")
    show(conn, "5-C 수량 0으로 나누기", """
        SELECT id, list_price / quantity AS unit_price
        FROM customer_order ORDER BY id""")
    show(conn, "5-D NULLIF로 0을 NULL로 바꾼 뒤 나누기", """
        SELECT id, list_price / NULLIF(quantity, 0) AS unit_price
        FROM customer_order ORDER BY id""")
    show(conn, "5-E 빈 문자열 휴대폰은 IS NULL에 걸리는가", """
        SELECT id FROM customer_order WHERE mobile IS NULL ORDER BY id""")


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)
    section_arithmetic(conn)
    section_comparison(conn)
    section_aggregate(conn)
    section_coalesce(conn)
    section_nullif(conn)


if __name__ == "__main__":
    main()
