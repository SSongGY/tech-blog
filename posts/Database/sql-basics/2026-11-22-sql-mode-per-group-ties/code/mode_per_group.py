"""그룹(매장)마다 가장 많이 팔린 메뉴, 즉 최빈값을 구한다.

1) 매장·메뉴별 판매 건수부터 센다
2) 맨 컬럼(MAX 와 함께 쓴 menu)과 LIMIT 1 — 동점이면 하나만 남는다
3) GROUP BY 두 번 — 최대 건수를 구해 다시 붙인다
4) 상관 부질의 HAVING — 그 매장의 최대 건수와 같은 메뉴만
5) RANK 창 함수 — 순위 1 을 전부 남긴다 (ROW_NUMBER 와 비교)
6) NULL 이 최빈값이 되는 자리 — COUNT(*) 와 COUNT(menu)
7) 동점을 한 줄로 묶거나, 규칙을 정해 하나만 고른다
"""
import sqlite3

from dbshow import print_dataset, print_environment

MENU_COUNT = """
    SELECT store, menu, COUNT(*) AS sold
    FROM sale
    GROUP BY store, menu"""


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE sale (
            sale_id INTEGER PRIMARY KEY,
            store   TEXT NOT NULL,
            menu    TEXT              -- 주문서에서 메뉴가 빠진 건은 NULL 로 들어왔다
        );
        INSERT INTO sale (store, menu) VALUES
            ('gangnam', 'latte'), ('gangnam', 'latte'), ('gangnam', 'latte'),
            ('gangnam', 'mocha'), ('gangnam', 'americano'),
            ('hongdae', 'americano'), ('hongdae', 'latte'), ('hongdae', 'americano'),
            ('hongdae', 'latte'), ('hongdae', 'mocha'),
            ('jamsil', 'latte'), ('jamsil', 'mocha'), ('jamsil', 'americano'),
            ('sinchon', 'mocha'), ('sinchon', NULL), ('sinchon', NULL),
            ('sinchon', NULL), ('sinchon', 'mocha');
        """
    )
    return conn


def show_rows(conn, sql):
    print("  sql> " + " ".join(sql.split())[:150] + " ...")
    cursor = conn.execute(sql)
    print("   ", tuple(d[0] for d in cursor.description))
    for row in cursor:
        print("   ", row)


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("\n[1] 매장·메뉴별 판매 건수")
    show_rows(conn, MENU_COUNT + " ORDER BY store, sold DESC, menu")

    print("\n[2-1] 맨 컬럼 — MAX(sold) 와 함께 menu 를 그냥 고른다")
    show_rows(conn, f"""
        SELECT store, menu, MAX(sold) AS sold
        FROM ({MENU_COUNT})
        GROUP BY store ORDER BY store""")
    print("[2-2] 상관 부질의 + LIMIT 1")
    show_rows(conn, """
        SELECT s.store,
               (SELECT menu FROM sale AS x WHERE x.store = s.store
                GROUP BY menu ORDER BY COUNT(*) DESC LIMIT 1) AS menu
        FROM (SELECT DISTINCT store FROM sale) AS s ORDER BY s.store""")

    print("\n[3] GROUP BY 두 번 — 매장별 최대 건수를 구해 다시 붙인다")
    show_rows(conn, f"""
        WITH menu_count AS ({MENU_COUNT}),
             top_count AS (SELECT store, MAX(sold) AS max_sold
                           FROM menu_count GROUP BY store)
        SELECT c.store, c.menu, c.sold
        FROM menu_count AS c
        JOIN top_count AS t ON t.store = c.store AND t.max_sold = c.sold
        ORDER BY c.store, c.menu""")

    print("\n[4] 상관 부질의 HAVING — 그 매장의 최대 건수와 같은 메뉴만")
    show_rows(conn, """
        SELECT s.store, s.menu, COUNT(*) AS sold
        FROM sale AS s
        GROUP BY s.store, s.menu
        HAVING COUNT(*) = (SELECT MAX(cnt) FROM
                             (SELECT COUNT(*) AS cnt FROM sale AS x
                              WHERE x.store = s.store GROUP BY x.menu))
        ORDER BY s.store, s.menu""")

    print("\n[5-1] RANK 창 함수 — 집계 결과 위에 순위를 매긴다")
    show_rows(conn, """
        SELECT store, menu, COUNT(*) AS sold,
               RANK()       OVER (PARTITION BY store ORDER BY COUNT(*) DESC) AS rnk,
               ROW_NUMBER() OVER (PARTITION BY store ORDER BY COUNT(*) DESC) AS rn
        FROM sale GROUP BY store, menu
        ORDER BY store, rnk, menu""")
    print("[5-2] rnk = 1 만 남긴다")
    show_rows(conn, """
        SELECT store, menu, sold FROM (
            SELECT store, menu, COUNT(*) AS sold,
                   RANK() OVER (PARTITION BY store ORDER BY COUNT(*) DESC) AS rnk
            FROM sale GROUP BY store, menu)
        WHERE rnk = 1 ORDER BY store, menu""")

    print("\n[6-1] sinchon 의 NULL — GROUP BY 는 NULL 을 한 묶음으로 센다")
    show_rows(conn, """
        SELECT menu, COUNT(*) AS count_star, COUNT(menu) AS count_menu
        FROM sale WHERE store = 'sinchon' GROUP BY menu ORDER BY menu""")
    print("[6-2] 메뉴가 빠진 건을 먼저 걸러 낸 최빈값")
    show_rows(conn, """
        SELECT store, menu, sold FROM (
            SELECT store, menu, COUNT(*) AS sold,
                   RANK() OVER (PARTITION BY store ORDER BY COUNT(*) DESC) AS rnk
            FROM sale WHERE menu IS NOT NULL GROUP BY store, menu)
        WHERE rnk = 1 ORDER BY store, menu""")

    print("\n[7-1] 동점을 한 줄로 — group_concat 으로 묶고 몇 개인지 함께")
    show_rows(conn, """
        SELECT store, MAX(sold) AS sold, COUNT(*) AS tied,
               group_concat(menu, ',' ORDER BY menu) AS modes
        FROM (
            SELECT store, menu, COUNT(*) AS sold,
                   RANK() OVER (PARTITION BY store ORDER BY COUNT(*) DESC) AS rnk
            FROM sale WHERE menu IS NOT NULL GROUP BY store, menu)
        WHERE rnk = 1 GROUP BY store ORDER BY store""")
    print("[7-2] 규칙을 정해 하나만 — 동점이면 메뉴 이름순 첫 번째")
    show_rows(conn, """
        SELECT store, menu, sold FROM (
            SELECT store, menu, COUNT(*) AS sold,
                   ROW_NUMBER() OVER (PARTITION BY store
                                      ORDER BY COUNT(*) DESC, menu) AS rn
            FROM sale WHERE menu IS NOT NULL GROUP BY store, menu)
        WHERE rn = 1 ORDER BY store""")
    conn.close()


if __name__ == "__main__":
    main()
