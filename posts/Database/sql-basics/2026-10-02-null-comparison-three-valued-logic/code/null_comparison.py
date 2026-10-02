"""`= NULL`이 왜 아무 행도 돌려주지 않는지, 삼값 논리를 실제 질의 결과로 확인한다.

회원 표에는 추천인(referrer_id)이 비어 있는 회원이 섞여 있다. 진리표를 SQLite가 직접
계산하게 한 뒤, WHERE·CHECK·UNIQUE·CASE가 '알 수 없음(NULL)'을 각각 어떻게 다루는지 본다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

MEMBERS = [
    # (id, 이름, 추천인 id, 등급)
    (1, "김도윤", None, "gold"),
    (2, "이서준", 1, "silver"),
    (3, "박하은", 1, None),
    (4, "최유나", None, "silver"),
    (5, "정민호", 3, "gold"),
]

def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE member (
            id           INTEGER PRIMARY KEY,
            name         TEXT NOT NULL,
            referrer_id  INTEGER,
            grade        TEXT
        );
        """
    )
    conn.executemany("INSERT INTO member VALUES (?, ?, ?, ?)", MEMBERS)
    conn.commit()
    return conn


def show(conn: sqlite3.Connection, label: str, sql: str) -> None:
    print(f"\n[{label}]")
    print(f"  {' '.join(sql.split())}")
    try:
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
    except sqlite3.Error as exc:
        print(f"  에러: {type(exc).__name__}: {exc}")
        return
    print(f"  {tuple(col[0] for col in cursor.description)}")
    for row in rows:
        print(f"  {row}")


def section_truth_table(conn: sqlite3.Connection) -> None:
    print("\n== 1. 진리표를 SQLite가 직접 계산한다 ==")
    # 1=참, 0=거짓, NULL=알 수 없음. 세 값의 모든 조합을 만든다
    show(conn, "1-A AND · OR", """
        WITH v(x) AS (VALUES (1), (0), (NULL))
        SELECT a.x AS p, b.x AS q, a.x AND b.x AS p_and_q, a.x OR b.x AS p_or_q
        FROM v a, v b""")
    show(conn, "1-B NOT", """
        WITH v(x) AS (VALUES (1), (0), (NULL))
        SELECT x AS p, NOT x AS not_p FROM v""")
    show(conn, "1-C NULL과의 비교는 전부 NULL", """
        SELECT NULL = NULL, NULL <> NULL, NULL = 1, NULL > 1, 1 IN (NULL), 1 IN (1, NULL)""")


def section_where(conn: sqlite3.Connection) -> None:
    print("\n== 2. WHERE 는 참인 행만 남긴다 ==")
    show(conn, "2-A = NULL", "SELECT id, name FROM member WHERE referrer_id = NULL")
    show(conn, "2-B IS NULL", "SELECT id, name FROM member WHERE referrer_id IS NULL")
    show(conn, "2-C <> 1 은 NULL 행을 빼고 돌려준다", """
        SELECT id, name, referrer_id FROM member WHERE referrer_id <> 1""")
    show(conn, "2-D NOT (referrer_id = 1) 도 마찬가지다", """
        SELECT id, name FROM member WHERE NOT (referrer_id = 1)""")
    show(conn, "2-E IS NOT 1 은 NULL 행을 포함한다", """
        SELECT id, name, referrer_id FROM member WHERE referrer_id IS NOT 1""")
    show(conn, "2-F IS DISTINCT FROM", """
        SELECT id, name FROM member WHERE grade IS DISTINCT FROM 'gold'""")
    # 화면에서 넘어온 값이 None일 수 있는 바인딩 변수 — 같은 질의문으로 두 경우를 다 처리하는가
    print("\n[2-G 바인딩 변수에 None 을 넘기면]")
    for operator in ("=", "IS"):
        for referrer in (None, 1):
            sql = f"SELECT id FROM member WHERE referrer_id {operator} ?"
            ids = [row[0] for row in conn.execute(sql, (referrer,))]
            print(f"  {sql:<45} 값={referrer!r:<5} -> {ids}")


def section_check_unique(conn: sqlite3.Connection) -> None:
    print("\n== 3. CHECK 와 UNIQUE 는 NULL 을 통과시킨다 ==")
    conn.execute(
        "CREATE TABLE coupon (code TEXT UNIQUE, rate INTEGER CHECK (rate BETWEEN 1 AND 50))"
    )
    for code, rate in [("A10", 10), ("B99", 99), (None, None), (None, 30)]:
        try:
            conn.execute("INSERT INTO coupon VALUES (?, ?)", (code, rate))
            print(f"  INSERT ({code!r}, {rate!r}) -> 성공")
        except sqlite3.IntegrityError as exc:
            print(f"  INSERT ({code!r}, {rate!r}) -> 에러: {exc}")
    show(conn, "3-A 들어간 행", "SELECT code, rate FROM coupon")
    show(conn, "3-B WHERE 로 같은 조건을 걸면", """
        SELECT code, rate FROM coupon WHERE rate BETWEEN 1 AND 50""")


def section_case(conn: sqlite3.Connection) -> None:
    print("\n== 4. CASE 안의 비교 ==")
    show(conn, "4-A CASE x WHEN NULL 은 NULL 을 못 잡는다", """
        SELECT id, grade,
               CASE grade WHEN NULL THEN '미지정' ELSE '지정' END AS by_value,
               CASE WHEN grade IS NULL THEN '미지정' ELSE '지정' END AS by_is_null
        FROM member""")


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)
    section_truth_table(conn)
    section_where(conn)
    section_check_unique(conn)
    section_case(conn)


if __name__ == "__main__":
    main()
