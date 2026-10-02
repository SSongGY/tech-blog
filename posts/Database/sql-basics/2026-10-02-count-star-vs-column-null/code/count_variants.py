"""COUNT(*)·COUNT(컬럼)·COUNT(DISTINCT 컬럼)이 같은 표에서 서로 다른 값을 내는 것을 본다.

회원 표에는 휴대폰이 비어 있는(NULL) 회원, 빈 문자열('')로 들어간 회원, 지역이 겹치는 회원이
섞여 있다. 주문 표에는 주문이 하나도 없는 회원이 있다. 세 가지 COUNT를 나란히 찍고,
LEFT JOIN 뒤에 무엇을 세느냐에 따라 "주문 0건"이 1건으로 둔갑하는 것을 확인한다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

MEMBERS = [
    # (id, 이름, 휴대폰, 지역)
    (1, "김도윤", "010-1111-2222", "서울"),
    (2, "이서준", None, "부산"),
    (3, "박하은", "010-3333-4444", "서울"),
    (4, "최유나", "", None),
    (5, "정민호", None, "서울"),
]

ORDERS = [
    # (id, 회원 id, 금액)
    (101, 1, 30000),
    (102, 1, 12000),
    (103, 3, 45000),
    (104, 5, 8000),
    (105, 3, 15000),
]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE member (
            id      INTEGER PRIMARY KEY,
            name    TEXT NOT NULL,
            mobile  TEXT,
            city    TEXT
        );
        CREATE TABLE shop_order (
            id         INTEGER PRIMARY KEY,
            member_id  INTEGER NOT NULL REFERENCES member(id),
            amount     INTEGER NOT NULL
        );
        """
    )
    conn.executemany("INSERT INTO member VALUES (?, ?, ?, ?)", MEMBERS)
    conn.executemany("INSERT INTO shop_order VALUES (?, ?, ?)", ORDERS)
    conn.commit()
    return conn


def show(conn: sqlite3.Connection, label: str, sql: str) -> None:
    print(f"\n[{label}]")
    print(f"  {' '.join(sql.split())}")
    try:
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
    except sqlite3.Error as exc:
        print(f"  에러: {type(exc).__name__}: {exc}")
        return
    print(f"  {tuple(col[0] for col in cursor.description)}")
    for row in rows:
        print(f"  {row}")


def section_three_counts(conn: sqlite3.Connection) -> None:
    print("\n== 1. 같은 표, 세 가지 COUNT ==")
    show(conn, "1-A 행 수 / 휴대폰 수 / 지역 수 / 서로 다른 지역 수", """
        SELECT COUNT(*), COUNT(mobile), COUNT(city), COUNT(DISTINCT city)
        FROM member""")
    show(conn, "1-B 빈 문자열은 NULL이 아니므로 센다", """
        SELECT COUNT(mobile), COUNT(NULLIF(mobile, '')) FROM member""")
    show(conn, "1-C 괄호 안에 상수를 넣으면", """
        SELECT COUNT(1), COUNT('x'), COUNT(NULL) FROM member""")
    show(conn, "1-D SELECT DISTINCT 로 뽑은 지역을 세면", """
        SELECT COUNT(*) FROM (SELECT DISTINCT city FROM member)""")


def section_empty_input(conn: sqlite3.Connection) -> None:
    print("\n== 2. 세는 대상이 하나도 없을 때 ==")
    show(conn, "2-A 조건에 맞는 행이 없으면 COUNT는 0, SUM은 NULL", """
        SELECT COUNT(*), COUNT(mobile), SUM(id)
        FROM member WHERE city = '제주'""")


def section_group_by(conn: sqlite3.Connection) -> None:
    print("\n== 3. GROUP BY 와 함께 ==")
    show(conn, "3-A 지역별 회원 수와 휴대폰 등록 수", """
        SELECT city, COUNT(*) AS member_cnt, COUNT(mobile) AS mobile_cnt
        FROM member GROUP BY city ORDER BY city""")


def section_left_join(conn: sqlite3.Connection) -> None:
    print("\n== 4. LEFT JOIN 뒤에 무엇을 세는가 ==")
    show(conn, "4-A 회원별 주문 수를 COUNT(*)로", """
        SELECT m.id, m.name, COUNT(*) AS order_cnt
        FROM member m LEFT JOIN shop_order o ON o.member_id = m.id
        GROUP BY m.id ORDER BY m.id""")
    show(conn, "4-B 회원별 주문 수를 COUNT(o.id)로", """
        SELECT m.id, m.name, COUNT(o.id) AS order_cnt
        FROM member m LEFT JOIN shop_order o ON o.member_id = m.id
        GROUP BY m.id ORDER BY m.id""")
    show(conn, "4-C 조인 직후의 행 — 주문 없는 회원도 한 줄은 남는다", """
        SELECT m.id, o.id AS order_id
        FROM member m LEFT JOIN shop_order o ON o.member_id = m.id
        WHERE m.id IN (2, 4) ORDER BY m.id""")


def section_conditional(conn: sqlite3.Connection) -> None:
    print("\n== 5. 조건부로 세기 ==")
    show(conn, "5-A CASE 로 조건에 맞을 때만 값을 준다", """
        SELECT COUNT(CASE WHEN city = '서울' THEN 1 END) AS seoul_cnt,
               COUNT(CASE WHEN city = '서울' THEN 1 ELSE 0 END) AS wrong_cnt
        FROM member""")
    show(conn, "5-B FILTER 절", """
        SELECT COUNT(*) FILTER (WHERE city = '서울') AS seoul_cnt
        FROM member""")
    show(conn, "5-C DISTINCT 에 컬럼 두 개", """
        SELECT COUNT(DISTINCT city, mobile) FROM member""")


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)
    section_three_counts(conn)
    section_empty_input(conn)
    section_group_by(conn)
    section_left_join(conn)
    section_conditional(conn)


if __name__ == "__main__":
    main()
