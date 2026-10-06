"""동점이 있는 점수표에 ROW_NUMBER·RANK·DENSE_RANK 를 나란히 붙여 비교한다.

세 함수는 동점이 없으면 같은 값을 내고, 동점이 생기는 순간부터 갈린다.
그래서 동점을 일부러 여러 군데(2명 동점, 3명 동점, NULL 2개) 넣어 둔다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

# 88점 2명, 75점 3명이 동점이다. 결시자 2명은 점수가 NULL 이다
SCORES = [
    (1, "김하늘", "1반", 95),
    (2, "이도윤", "1반", 88),
    (3, "박서준", "1반", 88),
    (4, "최유나", "1반", 80),
    (5, "정민호", "1반", 75),
    (6, "한지우", "2반", 75),
    (7, "윤채원", "2반", 75),
    (8, "장태오", "2반", 70),
    (9, "오세린", "2반", None),
    (10, "서지안", "2반", None),
]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("""
CREATE TABLE exam_score (
    student_id INTEGER PRIMARY KEY,
    name       TEXT    NOT NULL,
    class_name TEXT    NOT NULL,
    score      INTEGER
)
""")
    conn.executemany("INSERT INTO exam_score VALUES (?, ?, ?, ?)", SCORES)
    return conn


def run(conn: sqlite3.Connection, title: str, sql: str) -> None:
    print(f"\n-- {title}")
    for line in sql.strip().splitlines():
        print(f"   {line}")
    try:
        cursor = conn.execute(sql)
    except sqlite3.Error as exc:
        print(f"   에러: {exc}")
        return
    header = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    print("   => " + " | ".join(header))
    for row in rows:
        print("      " + " | ".join(str(v) for v in row))
    print(f"   ({len(rows)}행)")


def main() -> None:
    conn = build_database()
    try:
        print_environment()
        print_dataset(conn)

        run(conn, "1. 세 함수를 한 결과에 나란히 (전체, 점수 내림차순)", """
SELECT name, score,
       ROW_NUMBER() OVER (ORDER BY score DESC) AS row_num,
       RANK()       OVER (ORDER BY score DESC) AS rnk,
       DENSE_RANK() OVER (ORDER BY score DESC) AS dense_rnk
FROM exam_score
ORDER BY score DESC, student_id
""")

        # "상위 3등까지" 를 어느 함수로 거르느냐에 따라 몇 명이 나오는지
        for func in ("ROW_NUMBER", "RANK", "DENSE_RANK"):
            run(conn, f"2. 상위 3등까지 — {func}() <= 3", f"""
SELECT name, score, pos
FROM (SELECT name, score,
             {func}() OVER (ORDER BY score DESC) AS pos
      FROM exam_score)
WHERE pos <= 3
""")

        run(conn, "3. 반별로 따로 매기기 — PARTITION BY class_name", """
SELECT class_name, name, score,
       RANK()       OVER (PARTITION BY class_name ORDER BY score DESC) AS rnk,
       DENSE_RANK() OVER (PARTITION BY class_name ORDER BY score DESC) AS dense_rnk
FROM exam_score
ORDER BY class_name, score DESC, student_id
""")

        # 마지막 등수가 무엇과 같은지 — RANK 는 "나보다 높은 사람 수 + 1", DENSE_RANK 는 "고유 점수 개수"
        run(conn, "4. 마지막 등수와 개수 비교 (NULL 제외)", """
SELECT MAX(rnk)               AS max_rank,
       MAX(dense_rnk)         AS max_dense_rank,
       COUNT(*)               AS students,
       COUNT(DISTINCT score)  AS distinct_scores
FROM (SELECT score,
             RANK()       OVER (ORDER BY score DESC) AS rnk,
             DENSE_RANK() OVER (ORDER BY score DESC) AS dense_rnk
      FROM exam_score
      WHERE score IS NOT NULL)
""")

        run(conn, "5. 오름차순이면 NULL 은 어디로 가는가", """
SELECT name, score,
       RANK() OVER (ORDER BY score) AS rnk
FROM exam_score
ORDER BY score, student_id
""")

        run(conn, "6. NULLS LAST 로 결시자를 맨 뒤로", """
SELECT name, score,
       RANK() OVER (ORDER BY score DESC NULLS LAST) AS rnk
FROM exam_score
WHERE class_name = '2반'
ORDER BY score DESC NULLS LAST, student_id
""")

        run(conn, "7. OVER 안에 ORDER BY 가 없으면", """
SELECT name, score,
       RANK()       OVER () AS rnk,
       DENSE_RANK() OVER () AS dense_rnk
FROM exam_score
WHERE class_name = '1반'
""")

        run(conn, "8. 동점 처리 기준을 하나 더 주면 — ORDER BY score DESC, name", """
SELECT name, score,
       RANK()       OVER (ORDER BY score DESC, name) AS rnk,
       DENSE_RANK() OVER (ORDER BY score DESC, name) AS dense_rnk
FROM exam_score
WHERE score IN (88, 75)
ORDER BY score DESC, name
""")

        run(conn, "9. 괄호 안에 인자를 주면", """
SELECT name, RANK(score) OVER (ORDER BY score DESC) AS rnk
FROM exam_score
""")

        run(conn, "10. 같은 창을 WINDOW 절로 한 번만 정의", """
SELECT name, score,
       RANK()       OVER w AS rnk,
       DENSE_RANK() OVER w AS dense_rnk
FROM exam_score
WHERE score IS NOT NULL
WINDOW w AS (ORDER BY score DESC)
ORDER BY score DESC, student_id
""")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
