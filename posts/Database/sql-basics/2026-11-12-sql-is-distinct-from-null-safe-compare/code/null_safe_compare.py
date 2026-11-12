"""어제와 오늘 스냅숏을 비교해 바뀐 행을 찾는다 — NULL 이 섞이면 <> 가 놓치는 행.

1) 비교 연산자 진리표 — =, <>, IS, IS NOT, IS DISTINCT FROM
2) 한 컬럼 비교 — <> 와 IS NOT 이 찾는 행
3) COALESCE 우회가 놓치는 행
4) 여러 컬럼 — OR 로 잇기, 행 값 IS NOT, EXCEPT
5) 조인 키에 NULL 이 있을 때 — = 와 IS
6) 실행계획 — IS 도 인덱스를 탄다
"""
import sqlite3

from dbshow import print_dataset, print_environment


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE customer_yesterday (
            customer_id INTEGER PRIMARY KEY,
            email       TEXT,
            phone       TEXT
        );
        CREATE TABLE customer_today (
            customer_id INTEGER PRIMARY KEY,
            email       TEXT,
            phone       TEXT
        );
        -- 1 그대로 / 2 이메일 변경 / 3 전화 새로 등록 / 4 전화 삭제
        -- 5 둘 다 NULL 그대로 / 6 전화 변경 / 7 빈 문자열을 지워 NULL 로
        INSERT INTO customer_yesterday VALUES
            (1, 'a@x.kr', '010-1000'),
            (2, 'b@x.kr', NULL),
            (3, 'c@x.kr', NULL),
            (4, 'd@x.kr', '010-4000'),
            (5, NULL,     NULL),
            (6, 'f@x.kr', '010-6000'),
            (7, 'g@x.kr', '');
        INSERT INTO customer_today VALUES
            (1, 'a@x.kr', '010-1000'),
            (2, 'b2@x.kr', NULL),
            (3, 'c@x.kr', '010-3000'),
            (4, 'd@x.kr', NULL),
            (5, NULL,     NULL),
            (6, 'f@x.kr', '010-6001'),
            (7, 'g@x.kr', NULL);
        """
    )
    return conn


def show(conn, sql):
    print("  sql> " + " ".join(sql.split()))
    cursor = conn.execute(sql)
    headers = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    print("  " + " | ".join(headers))
    for row in rows:
        print("  " + " | ".join("NULL" if v is None else repr(v) for v in row))
    print(f"  ({len(rows)}행)")
    print()


def show_plan(conn, sql):
    print("  sql> " + " ".join(sql.split()))
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    # sqlite3 CLI 와 같은 모양으로 그린다: 부모 id 로 깊이를, 형제 중 마지막인지로 가지 모양을 정한다
    depth = {0: -1}
    last_child = {parent_id: node_id for node_id, parent_id, _, _ in rows}
    print("  QUERY PLAN")
    for node_id, parent_id, _, detail in rows:
        depth[node_id] = depth.get(parent_id, -1) + 1
        branch = "`--" if last_child[parent_id] == node_id else "|--"
        print("  " + "   " * depth[node_id] + branch + detail)
    print()


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("[1] 비교 연산자 진리표")
    show(
        conn,
        """
        SELECT a, b,
               a = b                     AS eq,
               a <> b                    AS ne,
               NOT (a = b)               AS not_eq,
               a IS b                    AS is_,
               a IS NOT b                AS is_not,
               a IS DISTINCT FROM b      AS distinct_from,
               a IS NOT DISTINCT FROM b  AS not_distinct_from
        FROM (SELECT 1 AS a, 1 AS b
              UNION ALL SELECT 1, 2
              UNION ALL SELECT 1, NULL
              UNION ALL SELECT NULL, NULL)
        """,
    )

    print("[2] 전화번호가 바뀐 고객 — <> 로 찾기")
    show(
        conn,
        """
        SELECT y.customer_id, y.phone AS before, t.phone AS after
        FROM customer_yesterday AS y
        JOIN customer_today AS t USING (customer_id)
        WHERE y.phone <> t.phone
        """,
    )
    print("[2] 같은 질문 — IS NOT 으로 찾기")
    show(
        conn,
        """
        SELECT y.customer_id, y.phone AS before, t.phone AS after
        FROM customer_yesterday AS y
        JOIN customer_today AS t USING (customer_id)
        WHERE y.phone IS NOT t.phone
        """,
    )
    print("[2] 같은 질문 — IS DISTINCT FROM 으로 찾기")
    show(
        conn,
        """
        SELECT y.customer_id
        FROM customer_yesterday AS y
        JOIN customer_today AS t USING (customer_id)
        WHERE y.phone IS DISTINCT FROM t.phone
        """,
    )

    print("[3] COALESCE 로 NULL 을 빈 문자열로 바꿔 비교")
    show(
        conn,
        """
        SELECT y.customer_id, y.phone AS before, t.phone AS after
        FROM customer_yesterday AS y
        JOIN customer_today AS t USING (customer_id)
        WHERE COALESCE(y.phone, '') <> COALESCE(t.phone, '')
        """,
    )

    print("[4] 이메일이나 전화가 바뀐 고객 — 컬럼마다 IS NOT 을 OR 로")
    show(
        conn,
        """
        SELECT y.customer_id
        FROM customer_yesterday AS y
        JOIN customer_today AS t USING (customer_id)
        WHERE y.email IS NOT t.email OR y.phone IS NOT t.phone
        """,
    )
    print("[4] 같은 질문 — 행 값 (email, phone) IS NOT (...)")
    show(
        conn,
        """
        SELECT y.customer_id
        FROM customer_yesterday AS y
        JOIN customer_today AS t USING (customer_id)
        WHERE (y.email, y.phone) IS NOT (t.email, t.phone)
        """,
    )
    print("[4] 같은 질문 — 컬럼마다 <> 를 OR 로")
    show(
        conn,
        """
        SELECT y.customer_id
        FROM customer_yesterday AS y
        JOIN customer_today AS t USING (customer_id)
        WHERE y.email <> t.email OR y.phone <> t.phone
        """,
    )
    print("[4] 같은 질문 — 오늘 EXCEPT 어제 (집합 연산은 NULL 을 같은 값으로 본다)")
    show(
        conn,
        """
        SELECT customer_id, email, phone FROM customer_today
        EXCEPT
        SELECT customer_id, email, phone FROM customer_yesterday
        """,
    )

    print("[5] 전화번호로 두 스냅숏 잇기 — = 와 IS")
    show(
        conn,
        """
        SELECT COUNT(*) AS matched_by_eq
        FROM customer_yesterday AS y JOIN customer_today AS t ON y.phone = t.phone
        """,
    )
    show(
        conn,
        """
        SELECT COUNT(*) AS matched_by_is
        FROM customer_yesterday AS y JOIN customer_today AS t ON y.phone IS t.phone
        """,
    )
    show(
        conn,
        """
        SELECT y.customer_id AS y_id, t.customer_id AS t_id, y.phone
        FROM customer_yesterday AS y JOIN customer_today AS t ON y.phone IS t.phone
        WHERE y.phone IS NULL
        ORDER BY y_id, t_id
        """,
    )

    print("[6] 실행계획 — phone 에 인덱스를 만든 뒤")
    conn.execute("CREATE INDEX ix_customer_today_phone ON customer_today (phone)")
    show_plan(conn, "SELECT customer_id FROM customer_today WHERE phone = '010-3000'")
    show_plan(conn, "SELECT customer_id FROM customer_today WHERE phone IS '010-3000'")
    show_plan(conn, "SELECT customer_id FROM customer_today WHERE phone IS NULL")
    show_plan(
        conn,
        "SELECT customer_id FROM customer_today "
        "WHERE phone IS NOT DISTINCT FROM '010-3000'",
    )
    show_plan(conn, "SELECT customer_id FROM customer_today WHERE phone IS NOT NULL")


if __name__ == "__main__":
    main()
