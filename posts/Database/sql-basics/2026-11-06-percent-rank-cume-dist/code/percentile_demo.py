"""PERCENT_RANK 와 CUME_DIST 가 동점·NULL·한 행 파티션에서 어떤 값을 내는지 확인한다.

python percentile_demo.py
"""

import sqlite3

from dbshow import _render, print_dataset, print_environment


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript("""
    CREATE TABLE exam (
        student TEXT    NOT NULL,
        class   TEXT    NOT NULL,
        score   INTEGER
    );
    INSERT INTO exam (student, class, score) VALUES
      ('가온', 'A반', 95),
      ('나래', 'A반', 88),
      ('다온', 'A반', 88),
      ('라온', 'A반', 88),
      ('마루', 'A반', 76),
      ('바름', 'B반', 91),
      ('사름', 'B반', 70),
      ('아름', 'B반', 64),
      ('자람', 'B반', 52),
      ('차오', 'C반', 80);
    """)
    return conn


def show(conn, title, sql):
    print(f"\n### {title}")
    print(sql.strip())
    cur = conn.execute(sql)
    names = [d[0] for d in cur.description]
    rows = cur.fetchall()
    # 숫자 칸만 오른쪽으로 붙여야 자릿수가 눈으로 비교된다
    aligns = [
        all(isinstance(r[i], (int, float)) or r[i] is None for r in rows)
        for i in range(len(names))
    ]
    for line in _render(names, rows, aligns):
        print(line)


def print_plan(conn, sql):
    """sqlite3 CLI 와 같은 모양으로 그린다 — id·parent 컬럼으로 중첩을 복원한다."""
    children = {}
    for node_id, parent, _, detail in conn.execute("EXPLAIN QUERY PLAN " + sql):
        children.setdefault(parent, []).append((node_id, detail))

    def walk(parent, prefix):
        rows = children.get(parent, [])
        for i, (node_id, detail) in enumerate(rows):
            last = i == len(rows) - 1
            print(prefix + ("`--" if last else "|--") + detail)
            walk(node_id, prefix + ("   " if last else "|  "))

    print("QUERY PLAN")
    walk(0, "")


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)

    show(conn, "1. 전체 10명 — 네 함수를 나란히", """
SELECT student, score,
       RANK()         OVER w AS rnk,
       ROW_NUMBER()   OVER w AS rn,
       PERCENT_RANK() OVER w AS pct_rank,
       CUME_DIST()    OVER w AS cume
FROM exam
WHERE score IS NOT NULL
WINDOW w AS (ORDER BY score)
ORDER BY score, student
""")

    print("\n### 2. 공식으로 손 계산한 값과 맞춰 보기 (n = 10)")
    rows = conn.execute("""
SELECT student, score,
       RANK() OVER (ORDER BY score)         AS rnk,
       COUNT(*) OVER (ORDER BY score)       AS peers_upto,
       PERCENT_RANK() OVER (ORDER BY score) AS pct_rank,
       CUME_DIST() OVER (ORDER BY score)    AS cume
FROM exam ORDER BY score, student
""").fetchall()
    n = len(rows)
    for student, score, rnk, peers_upto, pct_rank, cume in rows:
        # COUNT(*) OVER (ORDER BY ...) 는 기본 프레임이 RANGE 라 동점 끝까지 센다
        by_hand_pct = (rnk - 1) / (n - 1)
        by_hand_cume = peers_upto / n
        print(f"  {student} {score:3d}  ({rnk}-1)/({n}-1)={by_hand_pct:.4f} vs {pct_rank:.4f}"
              f"   {peers_upto}/{n}={by_hand_cume:.4f} vs {cume:.4f}"
              f"   일치={by_hand_pct == pct_rank and by_hand_cume == cume}")

    show(conn, "3. 반별로 — 한 명뿐인 C반은 어떻게 되나", """
SELECT class, student, score,
       PERCENT_RANK() OVER (PARTITION BY class ORDER BY score) AS pct_rank,
       CUME_DIST()    OVER (PARTITION BY class ORDER BY score) AS cume
FROM exam
ORDER BY class, score
""")

    show(conn, "4. '상위 몇 %' — 내림차순으로 다시 매기기", """
SELECT student, score,
       CUME_DIST() OVER (ORDER BY score DESC)       AS top_share,
       1 - CUME_DIST() OVER (ORDER BY score)        AS one_minus_asc
FROM exam
ORDER BY score DESC, student
""")

    print("\n### 5. 손으로 (rank-1)/(n-1) 을 쓰면 — 정수 나눗셈")
    for label, expr in [
        ("정수끼리 나눔", "(RANK() OVER (ORDER BY score) - 1) / (COUNT(*) OVER () - 1)"),
        ("한쪽을 실수로", "(RANK() OVER (ORDER BY score) - 1) * 1.0 / (COUNT(*) OVER () - 1)"),
    ]:
        values = [r[0] for r in conn.execute(f"SELECT {expr} FROM exam ORDER BY score")]
        print(f"  {label}: {values}")

    conn.execute("INSERT INTO exam (student, class, score) VALUES ('카람', 'B반', NULL)")
    show(conn, "6. 점수가 NULL 인 학생이 끼면 (11명)", """
SELECT student, score,
       PERCENT_RANK() OVER (ORDER BY score) AS pct_rank,
       CUME_DIST()    OVER (ORDER BY score) AS cume
FROM exam
ORDER BY score, student
""")

    show(conn, "7. NULL 을 거르고 매기기 — WHERE 가 먼저다", """
SELECT student, score,
       PERCENT_RANK() OVER (ORDER BY score) AS pct_rank
FROM exam
WHERE score IS NOT NULL
ORDER BY score, student
LIMIT 3
""")

    print("\n### 8. ORDER BY 를 빼면")
    rows = conn.execute(
        "SELECT PERCENT_RANK() OVER (), CUME_DIST() OVER () FROM exam"
    ).fetchall()
    print(f"  PERCENT_RANK 값 종류: {sorted(set(r[0] for r in rows))}")
    print(f"  CUME_DIST 값 종류:    {sorted(set(r[1] for r in rows))}")

    print("\n### 9. 백분위 '값'을 돌려주는 함수가 있나")
    for fn in ("median(score)", "percentile(score, 50)", "percentile_cont(score, 0.5)"):
        try:
            value = conn.execute(f"SELECT {fn} FROM exam").fetchone()[0]
            print(f"  {fn} -> {value}")
        except sqlite3.Error as exc:
            print(f"  {fn} -> {type(exc).__name__}: {exc}")

    print("\n### 10. 실행계획")
    print_plan(conn, "SELECT student, CUME_DIST() OVER (ORDER BY score) FROM exam")


if __name__ == "__main__":
    main()
