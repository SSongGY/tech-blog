"""상품 매출로 ABC 등급을 매긴다 (A: 누적 80%까지, B: 95%까지, C: 나머지).

1) 정수끼리 나누면 비율이 0 이 된다
2) 누적 매출과 누적 비율 — ORDER BY 만 준 기본 프레임
3) 기본 프레임(RANGE)은 동점 행에 같은 누적값을 준다 — ROWS 와 나란히
4) 경계 행을 어디에 넣는가 — '누적 ≤ 80%' 와 '누적 전 < 80%'
5) 기본 프레임으로 '누적 전'을 구하면 동점 둘이 함께 밀려난다
6) 정렬 키를 하나 더 둔 최종 질의
7) 등급별 상품 수와 매출 비중
8) 분류별로 따로 매기기 — PARTITION BY
"""
import sqlite3

from dbshow import print_dataset, print_environment


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE product_sales (
            product_id TEXT    PRIMARY KEY,
            category   TEXT    NOT NULL,
            sales      INTEGER NOT NULL      -- 한 달 매출(만 원)
        );
        INSERT INTO product_sales VALUES
            ('P01', '식품', 400), ('P02', '생활', 200), ('P03', '식품', 150),
            ('P04', '생활',  80), ('P05', '식품',  80), ('P06', '생활',  40),
            ('P07', '식품',  20), ('P08', '생활',  15), ('P09', '식품',  10),
            ('P10', '생활',   5);
        """
    )
    return conn


def show_rows(conn, sql):
    print("  sql> " + " ".join(sql.split())[:160] + " ...")
    cursor = conn.execute(sql)
    print("   ", tuple(d[0] for d in cursor.description))
    for row in cursor:
        print("   ", row)


# 누적 비율은 정수 비교로 등급을 가른다: cum * 100 <= 80 * total.
# 0.8 같은 실수 비교를 피하면 경계가 정확히 80% 일 때도 흔들리지 않는다.
ROWS_CUM = """SUM(sales) OVER (ORDER BY sales DESC, product_id
                               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)"""
TOTAL = "SUM(sales) OVER ()"

FINAL_SQL = f"""
    SELECT product_id, sales, cum, prev_cum, total,
           CASE WHEN prev_cum * 100 < 80 * total THEN 'A'
                WHEN prev_cum * 100 < 95 * total THEN 'B'
                ELSE 'C' END AS grade
    FROM (SELECT product_id, sales,
                 {ROWS_CUM} AS cum,
                 {ROWS_CUM} - sales AS prev_cum,
                 {TOTAL} AS total
          FROM product_sales)
    ORDER BY cum"""


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("\n[1] 정수 / 정수 — 비율이 전부 0 이 된다")
    show_rows(conn, f"""
        SELECT product_id, sales, sales / {TOTAL} AS int_div,
               sales * 1.0 / {TOTAL} AS real_div
        FROM product_sales ORDER BY sales DESC, product_id LIMIT 3""")

    print("\n[2] ORDER BY 만 준 누적 합 — 프레임을 적지 않았다")
    show_rows(conn, f"""
        SELECT product_id, sales,
               SUM(sales) OVER (ORDER BY sales DESC) AS cum_default,
               ROUND(SUM(sales) OVER (ORDER BY sales DESC) * 100.0 / {TOTAL}, 1) AS cum_pct
        FROM product_sales ORDER BY sales DESC, product_id""")

    print("\n[3] 기본 프레임(RANGE) 과 ROWS 를 나란히 — 동점 P04·P05 를 본다")
    show_rows(conn, """
        SELECT product_id, sales,
               SUM(sales) OVER (ORDER BY sales DESC
                   RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cum_range,
               SUM(sales) OVER (ORDER BY sales DESC
                   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cum_rows,
               SUM(sales) OVER (ORDER BY sales DESC
                   GROUPS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cum_groups
        FROM product_sales ORDER BY sales DESC, product_id""")

    print("\n[4-1] A = 누적 ≤ 80% — 80% 를 넘기는 P04 는 B 로 간다")
    show_rows(conn, f"""
        SELECT product_id, sales, cum,
               CASE WHEN cum * 100 <= 80 * total THEN 'A' ELSE '-' END AS grade
        FROM (SELECT product_id, sales, {ROWS_CUM} AS cum, {TOTAL} AS total
              FROM product_sales)
        ORDER BY cum LIMIT 5""")
    print("[4-2] A = 누적 전 < 80% — 80% 선에 걸친 P04 까지 A")
    show_rows(conn, f"""
        SELECT product_id, sales, cum - sales AS prev_cum, cum,
               CASE WHEN (cum - sales) * 100 < 80 * total THEN 'A' ELSE '-' END AS grade
        FROM (SELECT product_id, sales, {ROWS_CUM} AS cum, {TOTAL} AS total
              FROM product_sales)
        ORDER BY cum LIMIT 5""")

    print("\n[5] 기본 프레임으로 '누적 전' 을 구하면 — P04·P05 가 함께 밀려난다")
    show_rows(conn, f"""
        SELECT product_id, sales, cum - sales AS prev_cum, cum,
               CASE WHEN (cum - sales) * 100 < 80 * total THEN 'A' ELSE '-' END AS grade
        FROM (SELECT product_id, sales,
                     SUM(sales) OVER (ORDER BY sales DESC) AS cum, {TOTAL} AS total
              FROM product_sales)
        ORDER BY sales DESC, product_id LIMIT 5""")

    print("\n[6] 최종 질의 — ROWS + 정렬 키 product_id, 누적 전 비율로 판정")
    show_rows(conn, FINAL_SQL)

    print("\n[6-1] 정렬 키 없이 ROWS 만 — 같은 데이터를 거꾸로 넣은 표에서 다시 돌린다")
    conn.executescript("""
        CREATE TABLE product_sales_rev (
            product_id TEXT PRIMARY KEY, category TEXT NOT NULL, sales INTEGER NOT NULL);
        INSERT INTO product_sales_rev
            SELECT * FROM product_sales ORDER BY product_id DESC;
    """)
    no_tiebreak = """
        SELECT product_id, sales,
               SUM(sales) OVER (ORDER BY sales DESC
                   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cum
        FROM {table} ORDER BY cum LIMIT 5"""
    show_rows(conn, no_tiebreak.format(table="product_sales"))
    show_rows(conn, no_tiebreak.format(table="product_sales_rev"))

    print("\n[7] 등급별 상품 수와 매출 비중")
    show_rows(conn, f"""
        SELECT grade, COUNT(*) AS items, SUM(sales) AS sales,
               ROUND(SUM(sales) * 100.0 / MAX(total), 1) AS pct
        FROM ({FINAL_SQL})
        GROUP BY grade ORDER BY grade""")

    print("\n[8] 분류별로 따로 — PARTITION BY category")
    show_rows(conn, """
        SELECT category, product_id, sales, prev_cum, total,
               CASE WHEN prev_cum * 100 < 80 * total THEN 'A'
                    WHEN prev_cum * 100 < 95 * total THEN 'B'
                    ELSE 'C' END AS grade
        FROM (SELECT category, product_id, sales,
                     SUM(sales) OVER w - sales AS prev_cum,
                     SUM(sales) OVER (PARTITION BY category) AS total
              FROM product_sales
              WINDOW w AS (PARTITION BY category ORDER BY sales DESC, product_id
                           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW))
        ORDER BY category, sales DESC, product_id""")
    conn.close()


if __name__ == "__main__":
    main()
