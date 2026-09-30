"""날짜와 시간 다루기 — 저장과 연산.

SQLite 에는 날짜 전용 타입이 없다. 같은 순간을 TEXT(ISO 8601)·REAL(율리우스 일)·
INTEGER(유닉스 시각) 중 하나로 저장하고, 날짜 함수가 그 값을 해석한다.
앞쪽에서는 형식이 제각각인 문자열이 정렬·비교에서 어떻게 틀리는지 보고,
뒤쪽에서는 날짜 함수와 수식어로 더하고 빼고 자른다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

ORDERS = [
    # (id, 고객, 주문 시각 — 사람이 손으로 넣은 형식 그대로)
    (1, "김도윤", "2026-09-05 09:30:00"),
    (2, "이서준", "2026-9-5 14:00:00"),
    (3, "박하은", "2026/09/28 18:10:00"),
    (4, "최유나", "2026-10-01 08:00:00"),
    (5, "정민재", "2026-09-30 23:59:59"),
    (6, "한지우", "2026-09-30"),
]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE orders (
            id          INTEGER PRIMARY KEY,
            customer    TEXT NOT NULL,
            ordered_at  TEXT NOT NULL
        )
        """
    )
    conn.executemany("INSERT INTO orders VALUES (?, ?, ?)", ORDERS)
    conn.commit()
    return conn


def show(conn: sqlite3.Connection, label: str, sql: str) -> None:
    print(f"\n[{label}]")
    print(f"  {' '.join(sql.split())}")
    rows = conn.execute(sql).fetchall()
    for row in rows:
        print(f"  {row!r}")
    print(f"  -> {len(rows)}행")


def section_text_order(conn: sqlite3.Connection) -> None:
    print("\n== 1. 문자열로 저장한 날짜의 정렬과 비교 ==")
    show(conn, "1-A ORDER BY ordered_at — 글자 순서로 정렬된다", """
        SELECT id, ordered_at FROM orders ORDER BY ordered_at
    """)
    show(conn, "1-B 9월 주문을 BETWEEN 으로 찾기", """
        SELECT id, ordered_at FROM orders
        WHERE ordered_at BETWEEN '2026-09-01' AND '2026-09-30'
    """)
    show(conn, "1-C 날짜 함수가 형식을 알아보는가", """
        SELECT id, ordered_at, date(ordered_at) FROM orders ORDER BY id
    """)
    show(conn, "1-D 형식 검사 — 알아보지 못한 행 찾기", """
        SELECT id, ordered_at FROM orders WHERE datetime(ordered_at) IS NULL
    """)


def section_fix(conn: sqlite3.Connection) -> None:
    print("\n== 2. ISO 8601 로 고친 뒤 ==")
    conn.execute("UPDATE orders SET ordered_at = '2026-09-05 14:00:00' WHERE id = 2")
    conn.execute("UPDATE orders SET ordered_at = '2026-09-28 18:10:00' WHERE id = 3")
    conn.execute("UPDATE orders SET ordered_at = '2026-09-30 00:00:00' WHERE id = 6")
    show(conn, "2-A 다시 정렬", """
        SELECT id, ordered_at FROM orders ORDER BY ordered_at
    """)
    show(conn, "2-B BETWEEN 끝값에 날짜만 쓰면", """
        SELECT id, ordered_at FROM orders
        WHERE ordered_at BETWEEN '2026-09-01' AND '2026-09-30'
    """)
    show(conn, "2-C 반열림 구간 — 이상 AND 미만", """
        SELECT id, ordered_at FROM orders
        WHERE ordered_at >= '2026-09-01' AND ordered_at < '2026-10-01'
    """)


def section_storage(conn: sqlite3.Connection) -> None:
    print("\n== 3. 같은 순간을 세 가지 형태로 ==")
    show(conn, "3-A TEXT · REAL · INTEGER", """
        SELECT '2026-10-01 08:00:00'              AS iso_text,
               julianday('2026-10-01 08:00:00')   AS julian_day,
               unixepoch('2026-10-01 08:00:00')   AS unix_time
    """)
    show(conn, "3-B 숫자에서 다시 글자로", """
        WITH t(jd, ux) AS (
            SELECT julianday('2026-10-01 08:00:00'), unixepoch('2026-10-01 08:00:00')
        )
        SELECT datetime(jd), datetime(ux, 'unixepoch'), datetime(ux),
               datetime(ux, 'auto')
        FROM t
    """)
    show(conn, "3-C typeof — 세 값의 저장 부류", """
        SELECT typeof('2026-10-01'), typeof(julianday('2026-10-01')),
               typeof(unixepoch('2026-10-01'))
    """)


def section_arithmetic(conn: sqlite3.Connection) -> None:
    print("\n== 4. 더하고 빼기 — 수식어 ==")
    show(conn, "4-A 일·시간·분 더하기", """
        SELECT datetime('2026-09-30 23:59:59', '+1 second'),
               date('2026-09-30', '+7 days'),
               datetime('2026-09-30 22:00:00', '+3 hours')
    """)
    show(conn, "4-B 월말에 한 달 더하기", """
        SELECT date('2026-01-31', '+1 month'),
               date('2026-01-31', 'start of month', '+1 month', '-1 day'),
               date('2026-01-31', '+1 month', 'floor')
    """)
    show(conn, "4-C 수식어는 왼쪽부터 차례로 적용된다", """
        SELECT date('2026-01-31', 'start of month', '+1 month'),
               date('2026-01-31', '+1 month', 'start of month')
    """)
    show(conn, "4-D 이번 달 첫날·말일, 다음 월요일", """
        SELECT date('2026-10-01 08:00:00', 'start of month'),
               date('2026-10-01 08:00:00', 'start of month', '+1 month', '-1 day'),
               date('2026-10-01', 'weekday 1')
    """)
    show(conn, "4-E 없는 날짜를 넣으면", """
        SELECT date('2026-02-30'), date('2026-02-31'), date('2026-02-32'),
               date('2026-13-01')
    """)


def section_diff(conn: sqlite3.Connection) -> None:
    print("\n== 5. 두 시각의 차이 ==")
    show(conn, "5-A 문자열끼리 빼면", """
        SELECT '2026-10-01' - '2026-09-05'
    """)
    show(conn, "5-B julianday 차이(일)와 unixepoch 차이(초)", """
        SELECT julianday('2026-10-01') - julianday('2026-09-05'),
               unixepoch('2026-10-01 08:00:00') - unixepoch('2026-09-30 23:59:59')
    """)
    show(conn, "5-C timediff — 년·월·일로 풀어 쓴 차이", """
        SELECT timediff('2026-10-01', '2026-09-05'),
               timediff('2026-03-01', '2026-01-31')
    """)
    show(conn, "5-D 주문마다 마감(10-01 08:00)까지 남은 시간", """
        SELECT id, ordered_at,
               ROUND((julianday('2026-10-01 08:00:00') - julianday(ordered_at)) * 24, 2)
                   AS hours_left
        FROM orders ORDER BY ordered_at
    """)


def section_format(conn: sqlite3.Connection) -> None:
    print("\n== 6. 잘라서 묶기 — strftime ==")
    show(conn, "6-A 형식 지정자", """
        SELECT strftime('%Y', '2026-10-01 08:05:09'),
               strftime('%m/%d %H:%M', '2026-10-01 08:05:09'),
               strftime('%w', '2026-10-01'),
               strftime('%j', '2026-10-01')
    """)
    show(conn, "6-B 날짜별 주문 수", """
        SELECT date(ordered_at) AS order_date, COUNT(*) AS order_count
        FROM orders GROUP BY date(ordered_at) ORDER BY order_date
    """)
    show(conn, "6-C strftime 결과의 타입", """
        SELECT strftime('%m', '2026-09-05') = 9,
               strftime('%m', '2026-09-05') = '09',
               CAST(strftime('%m', '2026-09-05') AS INTEGER) = 9
    """)


def section_timezone(conn: sqlite3.Connection) -> None:
    print("\n== 7. 시간대 ==")
    show(conn, "7-A 시간대 표기가 붙은 값은 UTC 로 바꿔 계산한다", """
        SELECT datetime('2026-10-01 08:00:00+09:00'),
               datetime('2026-10-01T08:00:00Z')
    """)
    show(conn, "7-B 같은 순간인데 글자는 다르다", """
        SELECT '2026-10-01 08:00:00+09:00' = '2026-09-30 23:00:00',
               datetime('2026-10-01 08:00:00+09:00') = '2026-09-30 23:00:00'
    """)


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)
    section_text_order(conn)
    section_fix(conn)
    section_storage(conn)
    section_arithmetic(conn)
    section_diff(conn)
    section_format(conn)
    section_timezone(conn)


if __name__ == "__main__":
    main()
