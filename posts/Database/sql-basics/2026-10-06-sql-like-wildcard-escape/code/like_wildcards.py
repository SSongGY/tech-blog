"""LIKE 의 와일드카드 % 와 _ 가 실제로 무엇과 맞는지 하나씩 확인한다.

글자 그대로의 % 나 _ 를 찾을 때 ESCAPE 가 왜 필요한지, 대소문자·한글·NULL·숫자
컬럼에서 LIKE 가 어떻게 움직이는지, 앞자리에 와일드카드를 두면 실행계획이
어떻게 바뀌는지를 같은 표 하나로 본다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

# 이름에 일부러 % 와 _ 를 글자로 넣은 행, 대소문자만 다른 행, 비 ASCII 대소문자 행,
# 이름이 NULL 인 행을 섞었다
PRODUCTS = [
    (1, "Apple", "1001"),
    (2, "apple pie", "1002"),
    (3, "ABC 노트", "1003"),
    (4, "ab", "2001"),
    (5, "A_B 케이블", "2002"),
    (6, "사과", "2003"),
    (7, "사과즙 1L", "3001"),
    (8, "100% 면 티셔츠", "3002"),
    (9, "1000원 균일", "3003"),
    (10, "50_off 쿠폰", "4001"),
    (11, "coffee 원두", "4002"),
    (12, "AxB 어댑터", "4003"),
    (13, "Æble 잼", "5001"),
    (14, None, "5002"),
]


def build_database() -> sqlite3.Connection:
    # 문장 캐시가 지운 인덱스를 계획에 남기는 일이 있어 캐시를 끈다
    conn = sqlite3.connect(":memory:", cached_statements=0)
    conn.execute("""
CREATE TABLE product (
    product_id   INTEGER PRIMARY KEY,
    product_name TEXT,
    sku          INTEGER NOT NULL
)""")
    conn.executemany("INSERT INTO product VALUES (?, ?, ?)", PRODUCTS)
    conn.execute("CREATE INDEX ix_product_name ON product (product_name)")
    return conn


def run(conn: sqlite3.Connection, title: str, sql: str) -> None:
    print(f"\n-- {title}")
    print(f"   {sql.strip()}")
    try:
        rows = conn.execute(sql).fetchall()
    except sqlite3.Error as exc:
        print(f"   에러: {exc}")
        return
    for row in rows:
        print("      " + " | ".join(repr(v) if v is None else str(v) for v in row))
    print(f"   ({len(rows)}행)")


def show_plan(conn: sqlite3.Connection, title: str, sql: str) -> None:
    # sqlite3 CLI 가 그리는 트리 모양을 그대로 흉내 낸다 (id·parent 로 깊이를 잡는다)
    print(f"\n-- {title}")
    print(f"   {sql.strip()}")
    plan = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    prefix = {0: ""}
    print("   QUERY PLAN")
    for i, (node_id, parent, _, detail) in enumerate(plan):
        is_last = all(r[1] != parent for r in plan[i + 1 :])
        lead = prefix.get(parent, "")
        print(f"   {lead}{'`--' if is_last else '|--'}{detail}")
        prefix[node_id] = lead + ("   " if is_last else "|  ")


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)

    base = "SELECT product_id, product_name FROM product WHERE product_name"

    print("\n==== 1부. % 와 _ 의 뜻 ====")
    run(conn, "1. 'a%' — a 로 시작", f"{base} LIKE 'a%'")
    run(conn, "2. '%pie' — pie 로 끝남", f"{base} LIKE '%pie'")
    run(conn, "3. '%과%' — 과 가 어디든 들어 있음", f"{base} LIKE '%과%'")
    run(conn, "4. 'ab' — 와일드카드 없음 = 같은 글자인지 비교", f"{base} LIKE 'ab'")
    run(conn, "5. 'a_' — a 다음에 정확히 한 글자", f"{base} LIKE 'a_'")
    run(conn, "6. '사_' — 한글도 한 글자로 센다", f"{base} LIKE '사_'")
    run(conn, "7. '사__' — 밑줄 둘은 정확히 두 글자", f"{base} LIKE '사__'")

    print("\n==== 2부. 글자 그대로의 % 와 _ ====")
    run(conn, "8. '100%' 를 찾으려고 '%100%%'", f"{base} LIKE '%100%%'")
    run(conn, "9. ESCAPE '!' 로 % 를 글자로", f"{base} LIKE '%100!%%' ESCAPE '!'")
    run(conn, "10. '_off' 를 찾으려고 '%_off%'", f"{base} LIKE '%_off%'")
    run(conn, "10-1. ESCAPE 로 _ 를 글자로", f"{base} LIKE '%!_off%' ESCAPE '!'")
    run(conn, "11. 'A_B' 를 찾으려고 'a_b%' (밑줄이 아무 글자와 맞는지)",
        f"{base} LIKE 'a_b%'")
    run(conn, "12. ESCAPE 로 _ 를 글자로", f"{base} LIKE 'a!_b%' ESCAPE '!'")
    run(conn, "13. ESCAPE 문자를 두 글자로 주면", f"{base} LIKE 'a!_b%' ESCAPE '!!'")

    print("\n==== 3부. 대소문자·NULL·숫자 ====")
    run(conn, "14. 대소문자 — ASCII 와 비 ASCII",
        "SELECT 'a' LIKE 'A', 'Æ' LIKE 'æ', '가' LIKE '가'")
    run(conn, "15. 'æ%' 로 Æble 을 찾으면", f"{base} LIKE 'æ%'")
    run(conn, "16. NULL 과 빈 문자열에 '%'",
        "SELECT NULL LIKE '%', '' LIKE '%', 'x' LIKE NULL")
    run(conn, "17. '%' 는 모든 행인가 — 14행 중 몇 행?",
        "SELECT COUNT(*) FROM product WHERE product_name LIKE '%'")
    run(conn, "18. 뒤 공백은 그대로 비교된다",
        "SELECT 'Apple ' LIKE 'Apple', 'Apple ' LIKE 'Apple%'")
    run(conn, "19. INTEGER 컬럼 sku 에 LIKE '100%'",
        "SELECT product_id, sku, typeof(sku) FROM product WHERE sku LIKE '100%'")
    run(conn, "20. NOT LIKE 와 NULL 행",
        "SELECT COUNT(*) FROM product WHERE product_name NOT LIKE 'a%'")

    print("\n==== 4부. 와일드카드 위치와 실행계획 ====")
    show_plan(conn, "21. LIKE 'a%' (기본 설정)", f"{base} LIKE 'a%'")
    show_plan(conn, "22. GLOB 'A*' — 대소문자를 가리는 앞자리 고정",
              f"{base} GLOB 'A*'")
    show_plan(conn, "23. GLOB '*e' — 앞자리가 와일드카드", f"{base} GLOB '*e'")
    run(conn, "24. GLOB 'A*' 결과 — 대소문자를 가린다", f"{base} GLOB 'A*'")


if __name__ == "__main__":
    main()
