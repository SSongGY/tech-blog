"""max(a, b) 와 MAX(col) 을 나란히 돌려 NULL·타입·묶지 않은 컬럼의 차이를 본다.

1) 인자 개수가 함수의 종류를 정한다 — 하나면 집계, 둘 이상이면 스칼라
2) NULL — 스칼라는 하나라도 NULL 이면 NULL, 집계는 NULL 을 건너뛴다
3) 행마다 두 컬럼 중 큰 값 — NULL 이 섞인 행을 살리는 방법
4) 타입이 섞이면 — 문자열 '10' 이 정수 99 보다 크다
5) MAX 와 같이 쓴 묶지 않은 컬럼 — 최댓값을 가진 행의 값이 따라온다
"""
import sqlite3

from dbshow import print_dataset, print_environment


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE exam_score (
            student     TEXT PRIMARY KEY,
            mid_score   INTEGER,
            final_score INTEGER
        );
        INSERT INTO exam_score VALUES
            ('kim',  70,   85),
            ('lee',  90,   60),
            ('park', NULL, 75),
            ('choi', 80,   NULL),
            ('jung', NULL, NULL);

        CREATE TABLE product (
            id       INTEGER PRIMARY KEY,
            category TEXT NOT NULL,
            name     TEXT NOT NULL,
            price    INTEGER NOT NULL
        );
        INSERT INTO product(category, name, price) VALUES
            ('fruit', 'apple',  1200),
            ('fruit', 'mango',  3500),
            ('fruit', 'grape',  2800),
            ('drink', 'water',   900),
            ('drink', 'juice',  2100),
            ('drink', 'coffee', 2100);
        """
    )
    return conn


def show(conn, sql):
    cursor = conn.execute(sql)
    headers = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    print("  sql> " + " ".join(sql.split()))
    print("  " + " | ".join(headers))
    for row in rows:
        print("  " + " | ".join("NULL" if v is None else repr(v) for v in row))
    print()


def section_argument_count(conn):
    print("== 1) 인자 개수가 종류를 정한다 ==")
    show(conn, "SELECT max(final_score) FROM exam_score")
    show(conn, "SELECT student, max(mid_score, final_score) FROM exam_score")


def section_null(conn):
    print("== 2) NULL 을 다루는 방식이 반대다 ==")
    show(conn, "SELECT max(3, NULL, 7), min(3, NULL, 7)")
    show(conn, "SELECT max(mid_score), min(mid_score), count(mid_score) FROM exam_score")
    show(conn, "SELECT max(mid_score) FROM exam_score WHERE student = 'jung'")
    show(conn, "SELECT max(mid_score) FROM exam_score WHERE 0")


def section_row_best(conn):
    print("== 3) 행마다 두 점수 중 높은 것 ==")
    show(
        conn,
        """
        SELECT student,
               max(mid_score, final_score) AS naive,
               max(coalesce(mid_score, final_score),
                   coalesce(final_score, mid_score)) AS fixed
        FROM exam_score
        """,
    )


def section_mixed_type(conn):
    print("== 4) 타입이 섞이면 ==")
    show(conn, "SELECT max('10', 99), typeof(max('10', 99))")
    show(conn, "SELECT max(CAST('10' AS INTEGER), 99)")


def section_bare_column(conn):
    print("== 5) MAX 와 같이 쓴 묶지 않은 컬럼 ==")
    show(conn, "SELECT student, max(mid_score) FROM exam_score")
    show(conn, "SELECT name, max(price) FROM product")
    show(conn, "SELECT category, name, max(price) FROM product GROUP BY category")
    show(conn, "SELECT name, max(price), min(price) FROM product")
    show(conn, "SELECT name, avg(price) FROM product")


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)
    section_argument_count(conn)
    section_null(conn)
    section_row_best(conn)
    section_mixed_type(conn)
    section_bare_column(conn)


if __name__ == "__main__":
    main()
