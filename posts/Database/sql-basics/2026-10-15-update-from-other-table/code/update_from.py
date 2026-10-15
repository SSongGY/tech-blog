"""다른 표의 값으로 갱신하는 세 가지 방법을 나란히 돌려 비교한다.

상관 서브쿼리 / 상관 서브쿼리 + WHERE EXISTS / UPDATE … FROM 이 각각
매칭되지 않은 행을 어떻게 다루는지, 조인에 여러 행이 걸릴 때 어느 값이
들어가는지를 실제 출력으로 확인한다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

RULE = "=" * 64

SCHEMA = """
-- unit_price 에 NOT NULL 을 걸지 않았다. 걸었을 때 무슨 일이 생기는지는
-- ①-B 에서 따로 본다.
CREATE TABLE product (
    product_id   INTEGER PRIMARY KEY,
    product_name TEXT    NOT NULL,
    unit_price   INTEGER
);

CREATE TABLE supplier_price (
    supplier_name TEXT    NOT NULL,
    product_id    INTEGER NOT NULL,
    unit_price    INTEGER NOT NULL
);

INSERT INTO product (product_id, product_name, unit_price) VALUES
    (1, '키보드',   38000),
    (2, '마우스',   19000),
    (3, '모니터',  210000),
    (4, '웹캠',     55000);

-- 3번 모니터는 공급사가 둘이다. 조인이 두 행에 걸린다.
-- 4번 웹캠은 단가표에 없다. 조인이 한 행에도 안 걸린다.
INSERT INTO supplier_price (supplier_name, product_id, unit_price) VALUES
    ('가나상사', 1,  36500),
    ('가나상사', 2,  17800),
    ('가나상사', 3, 198000),
    ('다라유통', 3, 203000);
"""


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    return conn


def show_product(conn: sqlite3.Connection, caption: str, table: str = "product") -> None:
    print(f"-- {caption}")
    for row in conn.execute(f"SELECT * FROM {table} ORDER BY product_id"):
        print("  ", tuple("NULL" if v is None else v for v in row))
    print()


def format_plan(conn: sqlite3.Connection, sql: str) -> str:
    """EXPLAIN QUERY PLAN 결과를 sqlite3 CLI 가 보여주는 모양 그대로 만든다.

    detail 문자열만 라벨 붙여 찍으면 사람이 정리한 표처럼 보인다. CLI 와 같은
    모양이면 도구가 돌려준 값이라는 것이 글에서 바로 드러난다.
    """
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    children: dict[int, list[tuple[int, str]]] = {}
    for node_id, parent_id, _, detail in rows:
        children.setdefault(parent_id, []).append((node_id, detail))

    lines = ["QUERY PLAN"]

    def walk(parent_id: int, prefix: str) -> None:
        items = children.get(parent_id, [])
        for index, (node_id, detail) in enumerate(items):
            last = index == len(items) - 1
            lines.append(prefix + ("`--" if last else "|--") + detail)
            walk(node_id, prefix + ("   " if last else "|  "))

    walk(0, "")
    return "\n".join(lines)


def section(title: str) -> None:
    print(RULE)
    print(title)
    print(RULE)


def run_case(title: str, statement: str) -> None:
    """매번 같은 초기 상태에서 시작해야 세 방법을 공평하게 비교할 수 있다."""
    conn = build_database()
    section(title)
    print(statement.strip())
    print()
    cur = conn.execute(statement)
    print(f"  갱신된 행 수: {cur.rowcount}")
    print()
    show_product(conn, "갱신 후 product")
    conn.close()


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)
    conn.close()

    run_case(
        "① 상관 서브쿼리 — WHERE 없이",
        """
UPDATE product
   SET unit_price = (SELECT sp.unit_price
                       FROM supplier_price sp
                      WHERE sp.product_id = product.product_id
                        AND sp.supplier_name = '가나상사');
""",
    )

    section("①-B 같은 문장을 unit_price NOT NULL 인 표에 돌리면")
    conn = build_database()
    conn.executescript(
        "CREATE TABLE product_strict ("
        " product_id INTEGER PRIMARY KEY,"
        " product_name TEXT NOT NULL,"
        " unit_price INTEGER NOT NULL);"
        "INSERT INTO product_strict SELECT * FROM product;"
    )
    try:
        conn.execute(
            "UPDATE product_strict SET unit_price = ("
            "SELECT sp.unit_price FROM supplier_price sp "
            "WHERE sp.product_id = product_strict.product_id "
            "AND sp.supplier_name = '가나상사')"
        )
    except sqlite3.IntegrityError as exc:
        print(f"  sqlite3.IntegrityError: {exc}")
    print()
    show_product(conn, "갱신 후 product_strict — 문장 전체가 되돌려졌다", "product_strict")
    conn.close()

    run_case(
        "② 상관 서브쿼리 — WHERE EXISTS 로 막기",
        """
UPDATE product
   SET unit_price = (SELECT sp.unit_price
                       FROM supplier_price sp
                      WHERE sp.product_id = product.product_id
                        AND sp.supplier_name = '가나상사')
 WHERE EXISTS (SELECT 1
                 FROM supplier_price sp
                WHERE sp.product_id = product.product_id
                  AND sp.supplier_name = '가나상사');
""",
    )

    run_case(
        "③ UPDATE … FROM — 조인으로 갱신",
        """
UPDATE product
   SET unit_price = sp.unit_price
  FROM supplier_price sp
 WHERE sp.product_id = product.product_id
   AND sp.supplier_name = '가나상사';
""",
    )

    run_case(
        "④ 조인이 두 행에 걸릴 때 — 공급사를 안 좁히면",
        """
UPDATE product
   SET unit_price = sp.unit_price
  FROM supplier_price sp
 WHERE sp.product_id = product.product_id;
""",
    )

    run_case(
        "⑤ FROM 절에 대상 표를 다시 적으면",
        """
UPDATE product
   SET unit_price = sp.unit_price
  FROM product p
       JOIN supplier_price sp ON sp.product_id = p.product_id
 WHERE p.product_id = 1;
""",
    )

    section("⑥ 같은 문장을 다섯 번 돌려 ④의 결과가 흔들리는지 본다")
    for attempt in range(1, 6):
        conn = build_database()
        conn.execute(
            "UPDATE product SET unit_price = sp.unit_price "
            "FROM supplier_price sp WHERE sp.product_id = product.product_id"
        )
        picked = conn.execute(
            "SELECT unit_price FROM product WHERE product_id = 3"
        ).fetchone()[0]
        print(f"  {attempt}회차 — 3번 모니터에 들어간 값: {picked}")
        conn.close()
    print()

    section("⑦ 실행계획 — ② 와 ③ 이 같은 일을 하는지")
    conn = build_database()
    for label, statement in (
        (
            "② 상관 서브쿼리 + WHERE EXISTS",
            "UPDATE product SET unit_price = (SELECT sp.unit_price FROM supplier_price sp "
            "WHERE sp.product_id = product.product_id AND sp.supplier_name = '가나상사') "
            "WHERE EXISTS (SELECT 1 FROM supplier_price sp "
            "WHERE sp.product_id = product.product_id AND sp.supplier_name = '가나상사')",
        ),
        (
            "③ UPDATE … FROM",
            "UPDATE product SET unit_price = sp.unit_price FROM supplier_price sp "
            "WHERE sp.product_id = product.product_id AND sp.supplier_name = '가나상사'",
        ),
    ):
        print(f"-- {label}")
        print(format_plan(conn, statement))
        print()
    conn.close()


if __name__ == "__main__":
    main()
