"""NTILE 이 행을 몇 개씩 나누는지, 나머지가 어디로 가는지 확인한다.

python ntile_demo.py
"""

import sqlite3

from dbshow import _render, print_dataset, print_environment


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript("""
    CREATE TABLE sales (
        customer TEXT    NOT NULL,
        region   TEXT    NOT NULL,
        amount   INTEGER NOT NULL
    );
    INSERT INTO sales (customer, region, amount) VALUES
      ('가온', '수도권', 980),
      ('나래', '수도권', 870),
      ('다온', '수도권', 760),
      ('라온', '수도권', 640),
      ('마루', '수도권', 520),
      ('바름', '수도권', 410),
      ('사름', '수도권', 300),
      ('아름', '영남',   950),
      ('자람', '영남',   720),
      ('차오', '영남',   610),
      ('카람', '영남',   480),
      ('타람', '영남',   350),
      ('파람', '영남',   210);
    """)
    return conn


def show(conn, title, sql):
    print(f"\n### {title}")
    print(sql.strip())
    cur = conn.execute(sql)
    names = [d[0] for d in cur.description]
    rows = cur.fetchall()
    # 숫자 칸만 오른쪽으로 붙여야 자릿수가 눈으로 비교된다
    aligns = [all(isinstance(r[i], int) for r in rows) for i in range(len(names))]
    for line in _render(names, rows, aligns):
        print(line)


def print_plan(conn, sql):
    """sqlite3 CLI 와 같은 모양으로 그린다 — id·parent 컬럼으로 중첩을 복원한다."""
    children = {}
    for node_id, parent, _, detail in conn.execute("EXPLAIN QUERY PLAN " + sql):
        children.setdefault(parent, []).append((node_id, detail))

    def walk(parent, prefix):
        rows = children.get(parent, [])
        for i, (node_id, detail) in enumerate(rows):
            last = i == len(rows) - 1
            print(prefix + ("`--" if last else "|--") + detail)
            walk(node_id, prefix + ("   " if last else "|  "))

    print("QUERY PLAN")
    walk(0, "")


def bucket_sizes(conn, row_count, tiles):
    """행 row_count 개를 NTILE(tiles) 로 나눴을 때 묶음별 행 수."""
    conn.execute("DROP TABLE IF EXISTS g")
    conn.execute("CREATE TABLE g (n INTEGER)")
    conn.executemany("INSERT INTO g VALUES (?)", [(i,) for i in range(row_count)])
    return conn.execute(
        "SELECT b, COUNT(*) FROM ("
        f"  SELECT NTILE({tiles}) OVER (ORDER BY n) AS b FROM g"
        ") GROUP BY b ORDER BY b"
    ).fetchall()


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)

    show(conn, "1. 전체를 4등분 — 13행은 딱 나뉘지 않는다", """
SELECT customer, amount,
       NTILE(4) OVER (ORDER BY amount DESC) AS quartile
FROM sales
ORDER BY amount DESC
""")

    show(conn, "2. 묶음마다 몇 행이 들어갔나", """
SELECT quartile, COUNT(*) AS rows_in_bucket,
       MAX(amount) AS top, MIN(amount) AS bottom
FROM (SELECT amount, NTILE(4) OVER (ORDER BY amount DESC) AS quartile FROM sales)
GROUP BY quartile
ORDER BY quartile
""")

    show(conn, "3. 지역별로 나누면 파티션마다 따로 센다", """
SELECT region, customer, amount,
       NTILE(3) OVER (PARTITION BY region ORDER BY amount DESC) AS tier
FROM sales
ORDER BY region, amount DESC
""")

    print("\n### 4. 행 수와 묶음 수를 바꿔 가며 — (묶음번호, 행수)")
    print("  몫 q = 행수 // n, 나머지 r = 행수 % n. 앞 r 개 묶음이 q+1 행을 갖는다.")
    for row_count, tiles in [(13, 4), (12, 4), (10, 4), (7, 3), (9, 2), (3, 5), (5, 1)]:
        q, r = divmod(row_count, tiles)
        sizes = bucket_sizes(conn, row_count, tiles)
        print(f"  {row_count:2d}행 / NTILE({tiles})  q={q} r={r}  ->  {sizes}")

    show(conn, "5. 동점은 묶음을 가른다 — RANK 와 다른 점", """
SELECT customer, amount,
       RANK()   OVER (ORDER BY amount DESC) AS rnk,
       NTILE(2) OVER (ORDER BY amount DESC) AS half
FROM (SELECT customer, 500 AS amount FROM sales WHERE region = '영남'
      UNION ALL SELECT customer, amount FROM sales WHERE region = '수도권')
ORDER BY amount DESC, customer
""")

    print("\n### 6. NTILE(0) 과 NTILE(-1)")
    for tiles in (0, -1):
        try:
            conn.execute(f"SELECT NTILE({tiles}) OVER (ORDER BY amount) FROM sales").fetchall()
            print(f"  NTILE({tiles}) -> 통과")
        except sqlite3.Error as exc:
            print(f"  NTILE({tiles}) -> {type(exc).__name__}: {exc}")

    print("\n### 7. 프레임을 적어도 NTILE 은 무시한다")
    plain = conn.execute(
        "SELECT NTILE(2) OVER (ORDER BY amount) FROM sales"
    ).fetchall()
    framed = conn.execute(
        "SELECT NTILE(2) OVER (ORDER BY amount "
        "ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) FROM sales"
    ).fetchall()
    print(f"  프레임 없음: {[r[0] for r in plain]}")
    print(f"  프레임 지정: {[r[0] for r in framed]}")
    print(f"  두 결과가 같은가: {plain == framed}")

    print("\n### 8. 실행계획")
    print_plan(conn, "SELECT customer, NTILE(4) OVER (ORDER BY amount DESC) FROM sales")


if __name__ == "__main__":
    main()
