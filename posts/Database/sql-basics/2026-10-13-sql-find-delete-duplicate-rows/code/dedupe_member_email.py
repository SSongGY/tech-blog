"""회원 표에 같은 이메일이 두 번 들어간 행을 찾아 지우고, UNIQUE 인덱스로 재발을 막는다.

데이터를 일부러 비틀어 둔다.
- 가입 버튼을 두 번 눌러 같은 이메일이 두 번 들어간 회원이 둘 있다 (한 명은 세 번)
- 이메일을 비워 둔(NULL) 회원이 두 명 있다. 이 둘은 서로 다른 사람이다
- 대소문자만 다른 이메일이 있다 (Jia@Example.com / jia@example.com)
"""

import sqlite3

from dbshow import print_dataset, print_environment

MEMBERS = [
    ("sky@example.com", "김하늘", "2026-10-01 09:00"),
    ("doyun@example.com", "이도윤", "2026-10-01 09:05"),
    ("doyun@example.com", "이도윤", "2026-10-01 09:05"),
    ("jia@example.com", "최지아", "2026-10-02 10:00"),
    (None, "박서준", "2026-10-02 11:00"),
    ("minjae@example.com", "정민재", "2026-10-03 14:00"),
    ("minjae@example.com", "정민재", "2026-10-03 14:01"),
    ("minjae@example.com", "정민재", "2026-10-05 08:30"),
    (None, "한유나", "2026-10-04 16:00"),
    ("Jia@Example.com", "최지아", "2026-10-06 12:00"),
]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.executescript("""
CREATE TABLE member (
    email     TEXT,
    name      TEXT NOT NULL,
    joined_at TEXT NOT NULL
);
""")
    conn.executemany("INSERT INTO member VALUES (?, ?, ?)", MEMBERS)
    return conn


def run(conn: sqlite3.Connection, title: str, sql: str) -> list[tuple]:
    print(f"\n-- {title}")
    for line in sql.strip().splitlines():
        print(f"   {line}")
    try:
        cursor = conn.execute(sql)
    except sqlite3.Error as exc:
        print(f"   에러: {exc}")
        return []
    if cursor.description is None:
        print(f"   (바뀐 행 {cursor.rowcount})")
        return []
    header = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    print("   => " + " | ".join(header))
    for row in rows:
        print("      " + " | ".join(str(v) for v in row))
    print(f"   ({len(rows)}행)")
    return rows


def main() -> None:
    conn = build_database()
    try:
        print_environment()
        print_dataset(conn)

        run(conn, "1. 표에 보이지 않는 rowid", """
SELECT rowid, email, name FROM member
""")

        run(conn, "2. 같은 이메일이 두 번 이상인 것 — GROUP BY + HAVING", """
SELECT email, COUNT(*) AS dup_count
FROM member
GROUP BY email
HAVING COUNT(*) > 1
""")

        # NULL 은 서로 다른 사람인데 GROUP BY 가 한 묶음으로 센다
        run(conn, "3. NULL 을 빼고 다시 센다", """
SELECT email, COUNT(*) AS dup_count
FROM member
WHERE email IS NOT NULL
GROUP BY email
HAVING COUNT(*) > 1
""")

        run(conn, "4. 중복 묶음의 행을 전부 본다", """
SELECT rowid, email, name, joined_at
FROM member
WHERE email IN (
    SELECT email FROM member
    WHERE email IS NOT NULL
    GROUP BY email HAVING COUNT(*) > 1)
ORDER BY email, rowid
""")

        run(conn, "5. 묶음마다 남길 행 — MIN(rowid)", """
SELECT email, MIN(rowid) AS keep_rowid, COUNT(*) AS dup_count
FROM member
GROUP BY email
""")

        # 지우기 전에 지울 행을 SELECT 로 먼저 본다. NULL 조건을 빠뜨리면 어떻게 되는가
        run(conn, "6. 지울 행 미리 보기 — NULL 조건을 빠뜨린 판", """
SELECT rowid, email, name
FROM member
WHERE rowid NOT IN (SELECT MIN(rowid) FROM member GROUP BY email)
""")

        run(conn, "7. 지울 행 미리 보기 — NULL 은 대상에서 뺀 판", """
SELECT rowid, email, name
FROM member
WHERE email IS NOT NULL
  AND rowid NOT IN (SELECT MIN(rowid) FROM member GROUP BY email)
""")

        # 먼저 들어온 행이 아니라 가장 최근 가입 행을 남기고 싶을 때
        run(conn, "8. 다른 기준으로 남기기 — 최근 가입 행을 1번으로", """
SELECT rowid, email, joined_at,
       ROW_NUMBER() OVER (PARTITION BY email
                          ORDER BY joined_at DESC, rowid DESC) AS rn
FROM member
WHERE email IS NOT NULL
ORDER BY email, rn
""")

        run(conn, "9. 지우기 전에 UNIQUE 인덱스부터 만들면", """
CREATE UNIQUE INDEX ux_member_email ON member (email)
""")

        conn.execute("BEGIN")
        run(conn, "10. 트랜잭션 안에서 지운다 (7번 조건 그대로)", """
DELETE FROM member
WHERE email IS NOT NULL
  AND rowid NOT IN (SELECT MIN(rowid) FROM member GROUP BY email)
""")
        run(conn, "11. 지운 뒤 다시 센다", """
SELECT email, COUNT(*) AS dup_count
FROM member
WHERE email IS NOT NULL
GROUP BY email
HAVING COUNT(*) > 1
""")
        conn.execute("COMMIT")

        run(conn, "12. 이제 UNIQUE 인덱스가 만들어진다", """
CREATE UNIQUE INDEX ux_member_email ON member (email)
""")

        run(conn, "13. 같은 이메일을 다시 넣으면", """
INSERT INTO member VALUES ('sky@example.com', '김하늘', '2026-10-13 07:00')
""")

        # UNIQUE 인덱스는 NULL 을 서로 다른 값으로 본다 — GROUP BY 와 반대다
        run(conn, "14. NULL 이메일은 몇 개라도 들어간다", """
INSERT INTO member VALUES (NULL, '오세린', '2026-10-13 07:01')
""")

        run(conn, "15. 대소문자만 다른 이메일 — 아직 남아 있다", """
SELECT rowid, email, name FROM member
WHERE lower(email) = 'jia@example.com'
""")

        run(conn, "16. lower() 로 묶으면 중복이 보인다", """
SELECT lower(email) AS email_key, COUNT(*) AS dup_count
FROM member
WHERE email IS NOT NULL
GROUP BY lower(email)
HAVING COUNT(*) > 1
""")

        conn.execute("BEGIN")
        run(conn, "17. lower(email) 기준으로 한 번 더 지운다", """
DELETE FROM member
WHERE email IS NOT NULL
  AND rowid NOT IN (SELECT MIN(rowid) FROM member GROUP BY lower(email))
""")
        conn.execute("COMMIT")

        run(conn, "18. 표현식 UNIQUE 인덱스 — 대소문자 변형도 막는다", """
CREATE UNIQUE INDEX ux_member_email_lower ON member (lower(email))
""")

        run(conn, "19. 대문자로 다시 넣으면", """
INSERT INTO member VALUES ('SKY@example.com', '김하늘', '2026-10-13 07:02')
""")

        run(conn, "20. 정리 후 남은 행", """
SELECT rowid, email, name, joined_at FROM member ORDER BY rowid
""")

        # rowid 는 INTEGER PRIMARY KEY 가 없으면 VACUUM 에서 바뀔 수 있다고 문서가 적는다
        run(conn, "21. VACUUM", "VACUUM")
        run(conn, "22. VACUUM 뒤의 rowid", """
SELECT rowid, email, name FROM member ORDER BY rowid
""")

        conn.execute("""
CREATE TABLE member_code (
    email TEXT PRIMARY KEY,
    name  TEXT NOT NULL
) WITHOUT ROWID
""")
        run(conn, "23. WITHOUT ROWID 표에는 rowid 가 없다", """
SELECT rowid, email FROM member_code
""")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
