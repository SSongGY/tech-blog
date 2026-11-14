"""SQLite 에 없는 < ALL · > ANY 를 다른 형태로 바꿔 쓰고, 빈 집합과 NULL 에서 결과를 비교한다.

질문: 같은 분류의 경쟁사 가격 '모두'보다 싼 우리 상품은?

1) SQLite 는 ALL·ANY 구문을 받지 않는다
2) 분류별 경쟁사 가격 — 값이 있음 / NULL 이 섞임 / 한 건도 없음
3) < ALL 을 바꿔 쓴 세 형태 — MIN 비교, NOT EXISTS, NULL 까지 따지는 NOT EXISTS
4) > ANY 를 바꿔 쓴 두 형태 — WHERE 에서는 같고, NOT 을 씌우면 갈린다
5) 상품마다 세 형태의 판정값을 나란히
"""
import sqlite3

from dbshow import print_dataset, print_environment


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE product (
            product_id INTEGER PRIMARY KEY,
            category   TEXT    NOT NULL,
            price      INTEGER NOT NULL
        );
        CREATE TABLE rival_offer (
            offer_id INTEGER PRIMARY KEY,
            category TEXT NOT NULL,
            price    INTEGER          -- 가격 미공개 행은 NULL
        );
        INSERT INTO product VALUES
            (1, 'pen',  1000),
            (2, 'pen',  1300),
            (3, 'note', 2500),
            (4, 'ink',  5000);
        -- pen 은 값이 다 있고, note 는 NULL 이 섞이고, ink 는 경쟁사 행이 없다
        INSERT INTO rival_offer VALUES
            (1, 'pen',  1200),
            (2, 'pen',  1500),
            (3, 'note', 3000),
            (4, 'note', NULL);
        """
    )
    return conn


def show(conn, sql):
    print("  sql> " + " ".join(sql.split()))
    try:
        cursor = conn.execute(sql)
    except sqlite3.Error as error:
        print(f"  {type(error).__name__}: {error}")
        print()
        return
    headers = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    print("  " + " | ".join(headers))
    for row in rows:
        print("  " + " | ".join("NULL" if v is None else str(v) for v in row))
    print(f"  ({len(rows)}행)")
    print()


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("[1] ALL·ANY 구문을 그대로 쓰면")
    show(
        conn,
        """
        SELECT product_id FROM product AS p
        WHERE p.price < ALL (SELECT r.price FROM rival_offer AS r
                             WHERE r.category = p.category)
        """,
    )
    show(
        conn,
        """
        SELECT product_id FROM product AS p
        WHERE p.price > ANY (SELECT r.price FROM rival_offer AS r
                             WHERE r.category = p.category)
        """,
    )

    print("[1] 오류 위치가 다른 이유 — ALL 은 키워드, ANY 는 이름으로 읽힌다")
    show(conn, "SELECT 1 AS any")
    show(conn, "SELECT 1 AS all")
    show(conn, "SELECT any(1)")

    print("[2] 분류별 경쟁사 가격 — MIN 은 NULL 을 건너뛰고, 행이 없으면 NULL")
    show(
        conn,
        """
        SELECT p.category,
               (SELECT COUNT(*) FROM rival_offer r WHERE r.category = p.category)
                   AS offer_rows,
               (SELECT COUNT(r.price) FROM rival_offer r WHERE r.category = p.category)
                   AS priced_rows,
               (SELECT MIN(r.price) FROM rival_offer r WHERE r.category = p.category)
                   AS min_price
        FROM (SELECT DISTINCT category FROM product) AS p
        ORDER BY p.category
        """,
    )

    print("[3-A] < ALL 을 MIN 비교로")
    show(
        conn,
        """
        SELECT product_id, category, price FROM product AS p
        WHERE p.price < (SELECT MIN(r.price) FROM rival_offer AS r
                         WHERE r.category = p.category)
        ORDER BY product_id
        """,
    )
    print("[3-B] < ALL 을 NOT EXISTS 로 — '나보다 싸거나 같은 경쟁 가격이 없다'")
    show(
        conn,
        """
        SELECT product_id, category, price FROM product AS p
        WHERE NOT EXISTS (SELECT 1 FROM rival_offer AS r
                          WHERE r.category = p.category
                            AND r.price <= p.price)
        ORDER BY product_id
        """,
    )
    print("[3-C] < ALL 을 표준 의미 그대로 — 참이 아닌 비교(거짓·NULL)가 하나도 없다")
    show(
        conn,
        """
        SELECT product_id, category, price FROM product AS p
        WHERE NOT EXISTS (SELECT 1 FROM rival_offer AS r
                          WHERE r.category = p.category
                            AND (p.price < r.price) IS NOT 1)
        ORDER BY product_id
        """,
    )

    print("[4-A] > ANY 를 MIN 비교로 — 어느 한 경쟁 가격보다라도 비싼 상품")
    show(
        conn,
        """
        SELECT product_id FROM product AS p
        WHERE p.price > (SELECT MIN(r.price) FROM rival_offer AS r
                         WHERE r.category = p.category)
        ORDER BY product_id
        """,
    )
    print("[4-B] > ANY 를 EXISTS 로")
    show(
        conn,
        """
        SELECT product_id FROM product AS p
        WHERE EXISTS (SELECT 1 FROM rival_offer AS r
                      WHERE r.category = p.category AND p.price > r.price)
        ORDER BY product_id
        """,
    )
    print("[4-C] 두 형태에 NOT 을 씌우면 — NOT (> MIN)")
    show(
        conn,
        """
        SELECT product_id FROM product AS p
        WHERE NOT (p.price > (SELECT MIN(r.price) FROM rival_offer AS r
                              WHERE r.category = p.category))
        ORDER BY product_id
        """,
    )
    print("[4-D] NOT EXISTS")
    show(
        conn,
        """
        SELECT product_id FROM product AS p
        WHERE NOT EXISTS (SELECT 1 FROM rival_offer AS r
                          WHERE r.category = p.category AND p.price > r.price)
        ORDER BY product_id
        """,
    )

    print("[5] 상품마다 판정값 — 1 참, 0 거짓, NULL 모름")
    show(
        conn,
        """
        SELECT p.product_id, p.category, p.price,
               p.price < (SELECT MIN(r.price) FROM rival_offer r
                          WHERE r.category = p.category)            AS by_min,
               NOT EXISTS (SELECT 1 FROM rival_offer r
                           WHERE r.category = p.category
                             AND r.price <= p.price)                AS by_not_exists,
               NOT EXISTS (SELECT 1 FROM rival_offer r
                           WHERE r.category = p.category
                             AND (p.price < r.price) IS NOT 1)      AS by_strict
        FROM product AS p
        ORDER BY p.product_id
        """,
    )


if __name__ == "__main__":
    main()
