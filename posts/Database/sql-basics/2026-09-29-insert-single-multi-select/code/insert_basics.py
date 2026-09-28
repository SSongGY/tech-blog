"""INSERT 의 세 가지 모양(단건·다건·SELECT)과, INSERT SELECT 에서 컬럼 순서가
어긋났을 때 무슨 일이 일어나는지 확인한다.

INSERT SELECT 는 이름이 아니라 **자리 순서**로 값을 맞춘다. 타입이 같은 컬럼끼리
순서가 바뀌면 에러 없이 틀린 값이 들어간다. 그것을 적재 뒤에 잡아내는 질의까지 돌린다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

SCHEMA = """
CREATE TABLE member (
    member_id  INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    email      TEXT NOT NULL,
    grade      TEXT NOT NULL DEFAULT 'basic'
);
CREATE TABLE signup_staging (
    email      TEXT NOT NULL,
    name       TEXT NOT NULL
);
INSERT INTO signup_staging (email, name) VALUES
    ('kim@example.com',  '김하나'),
    ('lee@example.com',  '이두리'),
    ('park@example.com', '박세찬');
"""


def run(conn, label, sql):
    print(f"-- {label}")
    print(f"   {sql}")
    try:
        cursor = conn.execute(sql)
        print(f"   성공 · 바뀐 행 {cursor.rowcount}")
    except sqlite3.Error as exc:
        print(f"   에러: {exc}")
    print()


def show(conn, sql):
    print(f"   {sql}")
    rows = conn.execute(sql).fetchall()
    if not rows:
        print("   (행 없음)")
    for row in rows:
        print("   " + " | ".join("NULL" if v is None else str(v) for v in row))
    print()


def main():
    print_environment()
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.executescript(SCHEMA)
    print_dataset(conn)

    run(
        conn,
        "1. 단건 — 컬럼 이름을 적는다. 빠진 grade 는 DEFAULT 로 채워진다",
        "INSERT INTO member (member_id, name, email) "
        "VALUES (1, '최고참', 'choi@example.com')",
    )
    run(
        conn,
        "2. 다건 — VALUES 뒤에 괄호 묶음을 쉼표로 잇는다",
        "INSERT INTO member (member_id, name, email, grade) VALUES "
        "(2, '정가람', 'jung@example.com', 'gold'), "
        "(3, '한별', 'han@example.com', 'basic')",
    )
    run(
        conn,
        "3. 다건 중 한 행이 실패하면 — 3번 id 가 이미 있다",
        "INSERT INTO member (member_id, name, email) VALUES "
        "(4, '오늘', 'oh@example.com'), (3, '중복', 'dup@example.com')",
    )
    show(conn, "SELECT * FROM member ORDER BY member_id")

    run(
        conn,
        "4. 값 개수가 컬럼 개수와 다르면",
        "INSERT INTO member (member_id, name, email) VALUES (5, '개수부족')",
    )
    run(
        conn,
        "5. 컬럼 이름 없이 넣으면 표의 컬럼 수를 전부 채워야 한다",
        "INSERT INTO member VALUES (5, '생략', 'skip@example.com')",
    )

    print("== INSERT SELECT — 스테이징 표에서 옮겨 담는다")
    print("   스테이징 표의 컬럼 순서는 (email, name), 대상 표는 (name, email) 이다")
    print()
    conn.execute("BEGIN")
    run(
        conn,
        "6. SELECT * 로 옮긴다 — 순서가 뒤집혀 있다",
        "INSERT INTO member (name, email) SELECT * FROM signup_staging",
    )
    show(conn, "SELECT member_id, name, email FROM member WHERE member_id > 3")

    print("-- 7. 적재 뒤 검사 — 원본에 있는데 대상에 없는 (이름, 이메일) 쌍")
    check_sql = (
        "SELECT name, email FROM signup_staging "
        "EXCEPT SELECT name, email FROM member"
    )
    show(conn, check_sql)
    conn.execute("ROLLBACK")

    run(
        conn,
        "8. 양쪽에 컬럼 이름을 적어 옮긴다",
        "INSERT INTO member (name, email) SELECT name, email FROM signup_staging",
    )
    show(conn, "SELECT member_id, name, email, grade FROM member WHERE member_id > 3")
    print("-- 9. 같은 검사를 다시 돌린다")
    show(conn, check_sql)

    conn.close()


if __name__ == "__main__":
    main()
