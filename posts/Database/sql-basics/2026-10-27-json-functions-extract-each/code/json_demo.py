"""SQLite JSON 함수 — 값 꺼내기, 배열 펴기, 그리고 인덱스를 태우는 지점.

표준 라이브러리만 쓴다. 메모리 DB 에 주문 표를 만들고 JSON 컬럼 하나에
옵션과 태그를 넣은 뒤, 꺼내 쓰는 방법을 차례로 찍는다.
"""

import json
import sqlite3

from dbshow import print_dataset, print_environment

SCHEMA = """
CREATE TABLE orders (
    order_id  INTEGER PRIMARY KEY,
    customer  TEXT NOT NULL,
    payload   TEXT NOT NULL      -- JSON 문서를 그대로 담는다
);
"""

ORDERS = [
    (1, "김하늘", {"status": "paid", "amount": 48000,
                   "tags": ["express", "gift"],
                   "ship": {"city": "서울", "zip": "04524"}}),
    (2, "박도윤", {"status": "pending", "amount": 12500,
                   "tags": ["express"],
                   "ship": {"city": "부산", "zip": "48058"}}),
    (3, "이서연", {"status": "paid", "amount": 230000,
                   "tags": [],
                   "ship": {"city": "서울", "zip": "06236"}}),
    (4, "최민재", {"status": "canceled", "amount": 7900,
                   "tags": ["coupon", "gift", "first"],
                   "ship": {"city": "대전"}}),
]


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.executemany(
        "INSERT INTO orders VALUES (?, ?, ?)",
        [(oid, name, json.dumps(doc, ensure_ascii=False)) for oid, name, doc in ORDERS],
    )
    conn.commit()
    return conn


def section(title):
    print("=" * 64)
    print(title)
    print("=" * 64)


def show(conn, sql, params=()):
    """질의문과 결과를 같이 찍는다. 무엇이 무엇의 출력인지 보이게."""
    print(f"  SQL> {' '.join(sql.split())}")
    for row in conn.execute(sql, params):
        print(f"       {row}")
    print()


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)

    section("1. json_extract — 경로로 값 하나 꺼내기")
    show(conn, """
        SELECT order_id,
               json_extract(payload, '$.status')    AS status,
               json_extract(payload, '$.amount')    AS amount,
               json_extract(payload, '$.ship.city') AS city
        FROM orders ORDER BY order_id
    """)
    show(conn, "SELECT json_extract(payload, '$.ship.zip') FROM orders WHERE order_id = 4")

    section("2. -> 와 ->> 는 무엇이 다른가")
    show(conn, """
        SELECT payload -> '$.status'  AS arrow,
               payload ->> '$.status' AS arrow2,
               typeof(payload -> '$.status')  AS t1,
               typeof(payload ->> '$.status') AS t2
        FROM orders WHERE order_id = 1
    """)

    section("3. json_type · json_valid · json_array_length")
    show(conn, """
        SELECT order_id,
               json_type(payload, '$.amount')   AS amount_type,
               json_type(payload, '$.tags')     AS tags_type,
               json_type(payload, '$.ship.zip') AS zip_type,
               json_array_length(payload, '$.tags') AS tag_count
        FROM orders ORDER BY order_id
    """)
    show(conn, "SELECT json_valid('{\"a\":1}'), json_valid('{a:1}'), json_valid('[1,2,')")

    section("4. json_each — 배열을 행으로 편다")
    show(conn, """
        SELECT o.order_id, o.customer, t.key, t.value
        FROM orders AS o, json_each(o.payload, '$.tags') AS t
        ORDER BY o.order_id, t.key
    """)
    show(conn, """
        SELECT t.value AS tag, COUNT(*) AS n
        FROM orders AS o, json_each(o.payload, '$.tags') AS t
        GROUP BY t.value ORDER BY n DESC, tag
    """)

    section("5. json_each 는 객체도 편다 / json_tree 는 끝까지 내려간다")
    show(conn, """
        SELECT key, value, type
        FROM json_each((SELECT payload FROM orders WHERE order_id = 2))
    """)
    show(conn, """
        SELECT fullkey, type, atom
        FROM json_tree((SELECT payload FROM orders WHERE order_id = 2))
        WHERE atom IS NOT NULL
    """)

    section("6. 다시 묶기 — json_object · json_group_array")
    show(conn, """
        SELECT json_object(
                   'city',  json_extract(payload, '$.ship.city'),
                   'total', SUM(json_extract(payload, '$.amount')),
                   'ids',   json_group_array(order_id)
               ) AS summary
        FROM orders
        WHERE json_extract(payload, '$.status') <> 'canceled'
        GROUP BY json_extract(payload, '$.ship.city')
        ORDER BY 1
    """)

    section("7. 인덱스 — JSON 그대로는 안 타고, 꺼내 둬야 탄다")
    print("  (가) 식에 바로 인덱스를 거는 경우")
    conn.execute(
        "CREATE INDEX idx_status ON orders(json_extract(payload, '$.status'))"
    )
    show(conn, """
        EXPLAIN QUERY PLAN
        SELECT order_id FROM orders WHERE json_extract(payload, '$.status') = 'paid'
    """)
    print("  (나) 같은 뜻을 ->> 로 적으면")
    show(conn, """
        EXPLAIN QUERY PLAN
        SELECT order_id FROM orders WHERE payload ->> '$.status' = 'paid'
    """)
    print("  (나-2) ->> 쪽에도 같은 모양으로 인덱스를 하나 더 걸면")
    conn.execute("CREATE INDEX idx_status_arrow ON orders(payload ->> '$.status')")
    show(conn, """
        EXPLAIN QUERY PLAN
        SELECT order_id FROM orders WHERE payload ->> '$.status' = 'paid'
    """)
    print("  (다) 생성 컬럼으로 빼고 거는 경우")
    conn.execute(
        "ALTER TABLE orders ADD COLUMN amount INTEGER "
        "GENERATED ALWAYS AS (json_extract(payload, '$.amount')) VIRTUAL"
    )
    conn.execute("CREATE INDEX idx_amount ON orders(amount)")
    show(conn, """
        EXPLAIN QUERY PLAN
        SELECT order_id FROM orders WHERE amount > 20000
    """)
    print("  (라) 배열 안을 조건으로 쓰면")
    show(conn, """
        EXPLAIN QUERY PLAN
        SELECT o.order_id FROM orders AS o, json_each(o.payload, '$.tags') AS t
        WHERE t.value = 'gift'
    """)

    section("8. 없는 경로와 NULL — 어느 쪽이 NULL 인지 구분되지 않는다")
    show(conn, """
        SELECT order_id,
               json_extract(payload, '$.ship.zip') AS zip,
               json_type(payload, '$.ship.zip')    AS zip_type
        FROM orders WHERE order_id IN (3, 4)
    """)
    show(conn, """
        SELECT json_extract('{"a":null}', '$.a')    AS stored_null,
               json_type('{"a":null}', '$.a')       AS stored_type,
               json_extract('{"a":null}', '$.b')    AS missing,
               json_type('{"a":null}', '$.b')       AS missing_type
    """)

    section("9. JSONB — 저장 형식을 바꾸면 크기가 달라진다")
    # length() 는 TEXT 에 글자 수를, BLOB 에 바이트 수를 돌려준다. 그대로 나란히
    # 놓으면 한글 한 글자(UTF-8 3바이트) 때문에 비교가 성립하지 않는다.
    show(conn, """
        SELECT length(payload)              AS text_chars,
               octet_length(payload)        AS text_bytes,
               octet_length(jsonb(payload)) AS jsonb_bytes
        FROM orders ORDER BY order_id
    """)
    show(conn, """
        SELECT jsonb_extract(jsonb(payload), '$.ship.city') AS city,
               typeof(jsonb(payload))                       AS stored_as
        FROM orders WHERE order_id = 1
    """)

    conn.close()


if __name__ == "__main__":
    main()
