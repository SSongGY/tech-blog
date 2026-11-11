"""다른 표를 기준으로 행을 지우는 방법들.

1) DELETE ... JOIN, DELETE ... USING, DELETE ... LIMIT 가 SQLite 에서 되는가
2) 단일 키 — IN 과 EXISTS 가 같은 행을 지운다
3) 복합 키 — 컬럼마다 IN 을 따로 걸면 엉뚱한 행까지 지운다
4) 같은 표를 부질의에서 다시 읽을 때 — 지우기 전 값으로 평가되는가
5) 지우기 전에 같은 조건으로 센다
6) 실행계획
"""
import sqlite3

from dbshow import print_dataset, print_environment


def build_database():
    # isolation_level=None 이면 파이썬이 BEGIN 을 몰래 넣지 않는다. BEGIN/ROLLBACK 을 직접 쓴다
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.executescript(
        """
        CREATE TABLE cart_item (
            member_id  INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            qty        INTEGER NOT NULL,
            PRIMARY KEY (member_id, product_id)
        );
        CREATE TABLE discontinued (
            product_id INTEGER PRIMARY KEY
        );
        CREATE TABLE removed_pair (
            member_id  INTEGER NOT NULL,
            product_id INTEGER NOT NULL
        );
        INSERT INTO cart_item VALUES
            (1, 10, 2), (1, 20, 1), (1, 30, 5),
            (2, 10, 1), (2, 30, 3),
            (3, 20, 4);
        INSERT INTO discontinued VALUES (20), (40);
        -- 회원 1 은 상품 30 을, 회원 2 는 상품 10 을 직접 뺐다
        INSERT INTO removed_pair VALUES (1, 30), (2, 10);
        """
    )
    return conn


def show(conn, sql):
    print("  sql> " + " ".join(sql.split()))
    cursor = conn.execute(sql)
    headers = [d[0] for d in cursor.description]
    print("  " + " | ".join(headers))
    for row in cursor.fetchall():
        print("  " + " | ".join("NULL" if v is None else str(v) for v in row))
    print()


def try_sql(conn, sql):
    print("  sql> " + " ".join(sql.split()))
    try:
        conn.execute(sql)
        print("  -> 성공")
    except sqlite3.Error as error:
        print(f"  -> {type(error).__name__}: {error}")
    print()


def delete_and_show(conn, sql):
    """BEGIN 안에서 지우고 남은 행을 보인 뒤 ROLLBACK 해서 다음 실험이 같은 상태에서 시작하게 한다."""
    conn.execute("BEGIN")
    print("  sql> " + " ".join(sql.split()))
    cursor = conn.execute(sql)
    print(f"  지운 행 {cursor.rowcount}")
    remaining = conn.execute(
        "SELECT member_id, product_id FROM cart_item ORDER BY 1, 2"
    ).fetchall()
    print("  남은 행 " + " ".join(f"({m},{p})" for m, p in remaining))
    conn.execute("ROLLBACK")
    print()


def show_plan(conn, sql):
    """EXPLAIN QUERY PLAN 의 (id, parent) 로 sqlite3 CLI 와 같은 트리를 그린다."""
    print("  sql> " + " ".join(sql.split()))
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    children = {}
    for node_id, parent, _, detail in rows:
        children.setdefault(parent, []).append((node_id, detail))

    def draw(parent, prefix):
        kids = children.get(parent, [])
        for i, (node_id, detail) in enumerate(kids):
            last = i == len(kids) - 1
            print("  " + prefix + ("`--" if last else "|--") + detail)
            draw(node_id, prefix + ("   " if last else "|  "))

    print("  QUERY PLAN")
    draw(0, "")
    print()


DELETE_IN = """
    DELETE FROM cart_item
    WHERE product_id IN (SELECT product_id FROM discontinued)
"""

DELETE_EXISTS = """
    DELETE FROM cart_item
    WHERE EXISTS (SELECT 1 FROM discontinued d
                  WHERE d.product_id = cart_item.product_id)
"""


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("== 1) 다른 DB 의 문법을 그대로 쓰면 ==")
    try_sql(conn, """
        DELETE c FROM cart_item c
        JOIN discontinued d ON d.product_id = c.product_id
    """)
    try_sql(conn, """
        DELETE FROM cart_item USING discontinued d
        WHERE d.product_id = cart_item.product_id
    """)
    try_sql(conn, "DELETE FROM cart_item WHERE qty > 1 LIMIT 1")
    show(conn, "SELECT COUNT(*) AS limit_option FROM pragma_compile_options "
               "WHERE compile_options = 'ENABLE_UPDATE_DELETE_LIMIT'")

    print("== 2) 단일 키 — 단종 상품을 담은 장바구니 행 지우기 ==")
    delete_and_show(conn, DELETE_IN)
    delete_and_show(conn, DELETE_EXISTS)

    print("== 3) 복합 키 — (회원, 상품) 짝으로 지우기 ==")
    delete_and_show(conn, """
        DELETE FROM cart_item
        WHERE member_id  IN (SELECT member_id  FROM removed_pair)
          AND product_id IN (SELECT product_id FROM removed_pair)
    """)
    delete_and_show(conn, """
        DELETE FROM cart_item
        WHERE EXISTS (SELECT 1 FROM removed_pair r
                      WHERE r.member_id  = cart_item.member_id
                        AND r.product_id = cart_item.product_id)
    """)
    delete_and_show(conn, """
        DELETE FROM cart_item
        WHERE (member_id, product_id) IN
              (SELECT member_id, product_id FROM removed_pair)
    """)

    print("== 4) 같은 표를 부질의에서 다시 읽기 ==")
    print("  상품을 두 개 이상 담은 회원의 행을 지운다. 지우는 도중에 다시 세면 마지막 행은 1이 되어 남는다")
    delete_and_show(conn, """
        DELETE FROM cart_item
        WHERE (SELECT COUNT(*) FROM cart_item AS c2
               WHERE c2.member_id = cart_item.member_id) >= 2
    """)
    print("  평균보다 적게 담은 행을 지운다. 지우는 도중에 평균을 다시 내면 기준이 올라간다")
    show(conn, "SELECT AVG(qty) AS avg_qty FROM cart_item")
    delete_and_show(conn, """
        DELETE FROM cart_item
        WHERE qty < (SELECT AVG(qty) FROM cart_item)
    """)

    print("== 5) 지우기 전에 같은 조건으로 센다 ==")
    show(conn, """
        SELECT COUNT(*) AS will_delete FROM cart_item
        WHERE product_id IN (SELECT product_id FROM discontinued)
    """)
    delete_and_show(conn, DELETE_IN)

    print("== 6) 실행계획 ==")
    show_plan(conn, DELETE_IN)
    show_plan(conn, DELETE_EXISTS)
    show_plan(conn, """
        DELETE FROM cart_item
        WHERE (SELECT COUNT(*) FROM cart_item AS c2
               WHERE c2.member_id = cart_item.member_id) >= 2
    """)
    conn.close()


if __name__ == "__main__":
    main()
