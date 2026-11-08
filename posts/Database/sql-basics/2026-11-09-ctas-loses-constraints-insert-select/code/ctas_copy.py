"""CREATE TABLE ... AS SELECT(CTAS)로 복사한 표가 원본과 무엇이 다른가.

1) 두 표의 정의를 sqlite_schema 에서 나란히 본다
2) 컬럼 정보(PRAGMA table_info)와 인덱스 목록을 비교한다
3) 원본이 막던 값을 복사본에 넣어 본다 — 중복 id, NULL, 음수, 기본값
4) 대소문자 무시 정렬(COLLATE NOCASE)이 사라지면 검색 결과가 바뀐다
5) 계산식 컬럼은 어떤 타입 이름을 받는가
6) 인덱스가 없으니 실행계획이 바뀐다
7) 뼈대를 먼저 만들고 INSERT INTO ... SELECT 로 채운다
8) INSERT INTO ... SELECT 도중 제약 위반이 나면 몇 행이 들어가는가
"""
import sqlite3

from dbshow import print_dataset, print_environment


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE product (
            product_id  INTEGER PRIMARY KEY,
            name        TEXT    NOT NULL COLLATE NOCASE,
            price       INTEGER NOT NULL DEFAULT 0 CHECK (price >= 0),
            sku         TEXT    UNIQUE
        );
        CREATE INDEX ix_product_price ON product(price);
        INSERT INTO product(name, price, sku) VALUES
            ('Apple',  1200, 'A-01'),
            ('banana',  800, 'B-01'),
            ('Cherry', 3000, 'C-01'),
            ('melon',  5000, 'M-01');
        """
    )
    return conn


def show(conn, sql):
    print("  sql> " + " ".join(sql.split()))
    try:
        cursor = conn.execute(sql)
    except sqlite3.Error as exc:
        print(f"  {type(exc).__name__}: {exc}")
        print()
        return
    if cursor.description is None:
        print(f"  (바뀐 행 수: {cursor.rowcount})")
        print()
        return
    headers = [d[0] for d in cursor.description]
    print("  " + " | ".join(headers))
    for row in cursor.fetchall():
        print("  " + " | ".join("NULL" if v is None else repr(v) for v in row))
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


def section_schema(conn):
    print("== 1) 정의 비교 — sqlite_schema ==")
    conn.execute("CREATE TABLE product_copy AS SELECT * FROM product")
    for (sql,) in conn.execute(
        "SELECT sql FROM sqlite_schema WHERE name IN ('product', 'product_copy')"
        " ORDER BY name"
    ):
        print("  " + "\n  ".join(line.rstrip() for line in sql.splitlines()))
        print()


def section_columns(conn):
    print("== 2) 컬럼 정보와 인덱스 ==")
    for table in ("product", "product_copy"):
        show(conn, f"SELECT name, type, \"notnull\", dflt_value, pk"
                   f" FROM pragma_table_info('{table}')")
        show(conn, f"SELECT name, \"unique\", origin FROM pragma_index_list('{table}')")
    show(conn, "SELECT count(*) AS copied_rows FROM product_copy")


def section_violations(conn):
    print("== 3) 원본이 막던 값을 넣어 본다 ==")
    statements = [
        "INSERT INTO {t}(product_id, name, price, sku) VALUES (1, 'dup', 10, 'D-01')",
        "INSERT INTO {t}(product_id, name, price, sku) VALUES (10, NULL, 10, 'N-01')",
        "INSERT INTO {t}(product_id, name, price, sku) VALUES (11, 'minus', -5, 'X-01')",
        "INSERT INTO {t}(product_id, name, price, sku) VALUES (12, 'same sku', 10, 'A-01')",
    ]
    for table in ("product", "product_copy"):
        print(f"  -- 대상: {table}")
        for template in statements:
            show(conn, template.format(t=table))
    print("  -- price 를 빼고 넣으면 기본값이 들어가는가")
    show(conn, "INSERT INTO product(name, sku) VALUES ('kiwi', 'K-01')")
    show(conn, "INSERT INTO product_copy(name, sku) VALUES ('kiwi', 'K-01')")
    show(conn, "SELECT product_id, name, price FROM product WHERE name = 'kiwi'")
    show(conn, "SELECT product_id, name, price FROM product_copy WHERE name = 'kiwi'")


def section_collation(conn):
    print("== 4) COLLATE NOCASE 가 사라지면 ==")
    show(conn, "SELECT product_id, name FROM product WHERE name = 'APPLE'")
    show(conn, "SELECT product_id, name FROM product_copy WHERE name = 'APPLE'")
    show(conn, "SELECT name FROM product WHERE product_id <= 4 ORDER BY name")
    show(conn, "SELECT name FROM product_copy WHERE product_id <= 4 ORDER BY name")


def section_expression_types(conn):
    print("== 5) 계산식 컬럼이 받는 타입 이름 ==")
    conn.execute(
        """
        CREATE TABLE price_report AS
        SELECT product_id,
               name,
               price * 1.1               AS price_vat,
               CAST(price AS REAL)       AS price_real,
               CAST(price AS NUMERIC)    AS price_num,
               upper(name)               AS name_upper,
               count(*) OVER ()          AS total_rows,
               NULL                      AS memo
        FROM product WHERE product_id <= 4
        """
    )
    (sql,) = conn.execute(
        "SELECT sql FROM sqlite_schema WHERE name = 'price_report'"
    ).fetchone()
    print("  " + sql)
    print()
    show(conn, "SELECT name, type FROM pragma_table_info('price_report')")
    show(conn, "SELECT typeof(price_vat), typeof(name_upper), typeof(total_rows)"
               " FROM price_report LIMIT 1")


def section_plan(conn):
    print("== 6) 인덱스가 없으니 실행계획이 바뀐다 ==")
    show_plan(conn, "SELECT name FROM product WHERE price > 2500")
    show_plan(conn, "SELECT name FROM product_copy WHERE price > 2500")
    show_plan(conn, "SELECT name FROM product WHERE product_id = 3")
    show_plan(conn, "SELECT name FROM product_copy WHERE product_id = 3")


def section_insert_select(conn):
    print("== 7) 뼈대를 먼저 만들고 INSERT INTO ... SELECT ==")
    (src_sql,) = conn.execute(
        "SELECT sql FROM sqlite_schema WHERE name = 'product'"
    ).fetchone()
    # 원본 정의 문장을 그대로 재사용하면 제약을 손으로 옮겨 적다 빠뜨리는 일이 없다
    conn.execute(src_sql.replace("CREATE TABLE product", "CREATE TABLE product_backup", 1))
    for (idx_sql,) in conn.execute(
        "SELECT sql FROM sqlite_schema WHERE type = 'index'"
        " AND tbl_name = 'product' AND sql IS NOT NULL"
    ).fetchall():
        conn.execute(idx_sql.replace("ix_product_", "ix_product_backup_", 1)
                            .replace("ON product(", "ON product_backup(", 1))
    show(conn, "INSERT INTO product_backup SELECT * FROM product")
    show(conn, "SELECT name, type, \"notnull\", dflt_value, pk"
               " FROM pragma_table_info('product_backup')")
    show(conn, "SELECT name, \"unique\", origin FROM pragma_index_list('product_backup')")
    show(conn, "INSERT INTO product_backup(product_id, name, price) VALUES (20, NULL, 1)")
    show(conn, "SELECT product_id, name FROM product_backup WHERE name = 'APPLE'")


def section_partial_failure(conn):
    print("== 8) INSERT INTO ... SELECT 도중 제약 위반이 나면 ==")
    conn.execute("CREATE TABLE incoming (name TEXT, price INTEGER, sku TEXT)")
    conn.execute(
        "INSERT INTO incoming VALUES ('grape', 2000, 'G-01'),"
        " ('lemon', -100, 'L-01'), ('peach', 2500, 'P-01')"
    )
    show(conn, "SELECT count(*) AS before_rows FROM product")
    show(conn, "INSERT INTO product(name, price, sku) SELECT name, price, sku FROM incoming")
    show(conn, "SELECT count(*) AS after_rows FROM product")
    show(conn, "INSERT OR IGNORE INTO product(name, price, sku)"
               " SELECT name, price, sku FROM incoming")
    show(conn, "SELECT product_id, name, price FROM product WHERE product_id > 4")


def main():
    conn = build_database()
    conn.isolation_level = None  # 문장마다 자동 커밋해야 실패한 문장의 효과가 따로 보인다
    print_environment()
    print_dataset(conn)
    section_schema(conn)
    section_columns(conn)
    section_violations(conn)
    section_collation(conn)
    section_expression_types(conn)
    section_plan(conn)
    section_insert_select(conn)
    section_partial_failure(conn)
    conn.close()


if __name__ == "__main__":
    main()
