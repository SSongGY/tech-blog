"""CREATE TABLE 의 타입과 네 가지 제약이 언제, 무엇을 검사하는지 하나씩 부딪혀 본다.

문장마다 성공/에러를 찍고, 바뀐 뒤의 표를 다시 찍는다.
에러 메시지는 SQLite 가 돌려준 문구 그대로다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

SCHEMA = """
CREATE TABLE product (
  product_id INTEGER PRIMARY KEY,
  sku        TEXT    NOT NULL UNIQUE,
  name       TEXT    NOT NULL,
  price      INTEGER CHECK (price > 0),
  barcode    TEXT    UNIQUE,
  status     TEXT    NOT NULL DEFAULT 'draft'
);
INSERT INTO product (product_id, sku, name, price, barcode)
VALUES (1, 'A-100', '연필', 500, '880001'),
       (2, 'A-200', '지우개', 300, NULL);
"""


def run(conn: sqlite3.Connection, sql: str) -> None:
    print(f"   {sql}")
    try:
        cur = conn.execute(sql)
        print(f"   성공 · 바뀐 행 {cur.rowcount}")
    except sqlite3.Error as exc:
        print(f"   에러: {exc}")


def show(conn: sqlite3.Connection, sql: str) -> None:
    print(f"   {sql}")
    rows = conn.execute(sql).fetchall()
    for row in rows:
        print("   " + " | ".join("NULL" if v is None else str(v) for v in row))
    if not rows:
        print("   (행 없음)")


def section(title: str) -> None:
    print(f"\n-- {title}")


def main() -> None:
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.executescript(SCHEMA)
    print_environment()
    print_dataset(conn)
    # 위 표의 '제약' 칸은 PK·NOT NULL·DEFAULT 만 보여 준다. UNIQUE·CHECK 는 정의문에 있다
    print("[product 정의문]")
    print(conn.execute("SELECT sql FROM sqlite_master WHERE name = 'product'").fetchone()[0])

    section("1. DEFAULT — 컬럼을 빼면 채운다")
    run(conn, "INSERT INTO product (product_id, sku, name, price) "
              "VALUES (3, 'A-300', '자', 1200)")
    show(conn, "SELECT product_id, status FROM product WHERE product_id = 3")

    section("2. DEFAULT — NULL 을 직접 적으면 채우지 않는다")
    run(conn, "INSERT INTO product (product_id, sku, name, price, status) "
              "VALUES (4, 'A-400', '풀', 800, NULL)")

    section("3. NOT NULL — 빈 문자열은 NULL 이 아니다")
    run(conn, "INSERT INTO product (product_id, sku, name, price) "
              "VALUES (5, 'A-500', NULL, 700)")
    run(conn, "INSERT INTO product (product_id, sku, name, price) "
              "VALUES (5, 'A-500', '', 700)")

    section("4. CHECK — 거짓이면 막고, NULL 이면 통과시킨다")
    run(conn, "INSERT INTO product (product_id, sku, name, price) "
              "VALUES (6, 'A-600', '가위', 0)")
    run(conn, "INSERT INTO product (product_id, sku, name, price) "
              "VALUES (6, 'A-600', '가위', NULL)")
    run(conn, "UPDATE product SET price = -100 WHERE product_id = 1")

    section("5. UNIQUE — 같은 값은 막고, NULL 끼리는 겹쳐도 된다")
    run(conn, "INSERT INTO product (product_id, sku, name, price, barcode) "
              "VALUES (7, 'A-700', '자석', 900, '880001')")
    run(conn, "INSERT INTO product (product_id, sku, name, price, barcode) "
              "VALUES (7, 'A-700', '자석', 900, NULL)")
    show(conn, "SELECT COUNT(*) FROM product WHERE barcode IS NULL")

    section("6. 타입 — 선언한 타입과 다른 값")
    run(conn, "INSERT INTO product (product_id, sku, name, price) "
              "VALUES (8, 'A-800', '클립', '1500')")
    run(conn, "INSERT INTO product (product_id, sku, name, price) "
              "VALUES (9, 'A-900', '핀', '천원')")
    show(conn, "SELECT product_id, price, typeof(price) FROM product "
               "WHERE product_id IN (8, 9)")

    section("7. 타입 — STRICT 표에서는 막는다")
    conn.execute("CREATE TABLE product_strict (product_id INTEGER PRIMARY KEY, "
                 "price INTEGER) STRICT")
    run(conn, "INSERT INTO product_strict VALUES (1, '1500')")
    run(conn, "INSERT INTO product_strict VALUES (2, '천원')")
    show(conn, "SELECT product_id, price, typeof(price) FROM product_strict")

    section("8. 검사 시점 — 두 행의 sku 를 한 문장으로 맞바꾼다")
    show(conn, "SELECT product_id, sku FROM product WHERE product_id IN (2, 3)")
    run(conn, "UPDATE product SET sku = CASE product_id WHEN 2 THEN 'A-300' "
              "WHEN 3 THEN 'A-200' END WHERE product_id IN (2, 3)")
    show(conn, "SELECT product_id, sku FROM product WHERE product_id IN (2, 3)")
    print("   -- 임시 값을 거쳐 세 문장으로 나누면")
    run(conn, "UPDATE product SET sku = 'TMP' WHERE product_id = 2")
    run(conn, "UPDATE product SET sku = 'A-200' WHERE product_id = 3")
    run(conn, "UPDATE product SET sku = 'A-300' WHERE product_id = 2")
    show(conn, "SELECT product_id, sku FROM product WHERE product_id IN (2, 3)")

    section("최종 표")
    show(conn, "SELECT * FROM product ORDER BY product_id")


if __name__ == "__main__":
    main()
