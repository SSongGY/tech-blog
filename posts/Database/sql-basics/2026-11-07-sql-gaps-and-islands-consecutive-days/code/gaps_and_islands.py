"""연속 구간 찾기 — 출석 기록에서 연속으로 나온 날을 한 묶음으로 센다.

1) 행 번호 차이 방식과 LAG 경계 방식이 같은 묶음을 내는지
2) 사용자별 가장 긴 연속 출석
3) 같은 날 기록이 두 번 들어가면 두 방식이 각각 어디서 어긋나는지, 고친 뒤
4) 날짜를 julianday 로 바꾸지 않고 빼면 생기는 일 (TEXT 산술, 월 경계)
5) 행 번호 차이 방식의 실행계획
"""
import sqlite3

from dbshow import _render, print_dataset, print_environment

# 연속된 날짜에서 1씩 늘어나는 행 번호를 빼면, 연속인 동안은 같은 값이 남는다
ROW_NUMBER_SQL = """
WITH numbered AS (
    SELECT user_id, attend_date,
           julianday(attend_date)
             - ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY attend_date) AS grp
    FROM attendance
)
SELECT user_id, MIN(attend_date) AS first_day, MAX(attend_date) AS last_day,
       COUNT(*) AS days
FROM numbered
GROUP BY user_id, grp
ORDER BY user_id, first_day
"""

# 앞 행과 하루 차이가 아니면 새 묶음의 시작(1)으로 표시하고, 표시를 누적해 묶음 번호로 쓴다
LAG_SQL = """
WITH marked AS (
    SELECT user_id, attend_date,
           CASE WHEN julianday(attend_date)
                     - julianday(LAG(attend_date) OVER w) = 1
                THEN 0 ELSE 1 END AS is_start
    FROM attendance
    WINDOW w AS (PARTITION BY user_id ORDER BY attend_date)
), grouped AS (
    SELECT user_id, attend_date,
           SUM(is_start) OVER (PARTITION BY user_id ORDER BY attend_date
                               ROWS UNBOUNDED PRECEDING) AS grp
    FROM marked
)
SELECT user_id, MIN(attend_date) AS first_day, MAX(attend_date) AS last_day,
       COUNT(*) AS days
FROM grouped
GROUP BY user_id, grp
ORDER BY user_id, first_day
"""

# 같은 날 중복을 먼저 걷어낸 행 번호 차이 방식
DISTINCT_FIRST_SQL = ROW_NUMBER_SQL.replace(
    "FROM attendance\n)",
    "FROM (SELECT DISTINCT user_id, attend_date FROM attendance)\n)")

# 차이가 0 (같은 날) 도 이어지는 것으로 보는 LAG 방식
LAG_ALLOW_SAME_DAY_SQL = LAG_SQL.replace("= 1\n", "<= 1\n")

LONGEST_SQL = """
WITH numbered AS (
    SELECT user_id, attend_date,
           julianday(attend_date)
             - ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY attend_date) AS grp
    FROM attendance
), islands AS (
    SELECT user_id, MIN(attend_date) AS first_day, COUNT(*) AS days
    FROM numbered
    GROUP BY user_id, grp
)
SELECT user_id, MAX(days) AS longest
FROM islands
GROUP BY user_id
ORDER BY user_id
"""


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE attendance (
            attendance_id INTEGER PRIMARY KEY,
            user_id       TEXT NOT NULL,
            attend_date   TEXT NOT NULL      -- 'YYYY-MM-DD'
        );
        INSERT INTO attendance(user_id, attend_date) VALUES
            ('kim', '2026-10-28'), ('kim', '2026-10-29'), ('kim', '2026-10-30'),
            ('kim', '2026-11-02'), ('kim', '2026-11-03'),
            ('kim', '2026-11-05'),
            ('lee', '2026-10-30'), ('lee', '2026-10-31'),
            ('lee', '2026-11-01'), ('lee', '2026-11-02');
        """
    )
    return conn


def show(conn, sql, aligns=None):
    cur = conn.execute(sql)
    headers = [d[0] for d in cur.description]
    rows = [tuple("NULL" if v is None else v for v in r) for r in cur.fetchall()]
    for line in _render(headers, rows, aligns or [False] * len(headers)):
        print("  " + line)


def section_two_ways(conn):
    print("== 1) 두 방식이 같은 묶음을 내는가 ==")
    print("  [중간값 — 행 번호 차이]")
    show(conn, """
        SELECT user_id, attend_date,
               ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY attend_date) AS rn,
               julianday(attend_date)
                 - ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY attend_date) AS grp
        FROM attendance ORDER BY user_id, attend_date
    """, [False, False, True, True])
    print("  [행 번호 차이 방식]")
    show(conn, ROW_NUMBER_SQL, [False, False, False, True])
    same = conn.execute(ROW_NUMBER_SQL).fetchall() == conn.execute(LAG_SQL).fetchall()
    print("  LAG 경계 방식과 결과가 같은가:", same)
    print()


def section_longest(conn):
    print("== 2) 사용자별 가장 긴 연속 출석 ==")
    show(conn, LONGEST_SQL, [False, True])
    print()


def section_duplicate(conn):
    print("== 3) kim 의 2026-10-29 기록이 한 번 더 들어가면 ==")
    conn.execute("SAVEPOINT dup")
    conn.execute(
        "INSERT INTO attendance(user_id, attend_date) VALUES ('kim', '2026-10-29')")
    print("  [행 번호 차이 방식 — kim]")
    show(conn, ROW_NUMBER_SQL.replace("ORDER BY user_id, first_day",
                                      "HAVING user_id = 'kim' ORDER BY first_day"),
         [False, False, False, True])
    print("  [LAG 경계 방식 — kim]")
    show(conn, LAG_SQL.replace("ORDER BY user_id, first_day",
                               "HAVING user_id = 'kim' ORDER BY first_day"),
         [False, False, False, True])
    print("  [DISTINCT 로 먼저 걷어낸 행 번호 차이 — kim]")
    show(conn, DISTINCT_FIRST_SQL.replace("ORDER BY user_id, first_day",
                                          "HAVING user_id = 'kim' ORDER BY first_day"),
         [False, False, False, True])
    print("  [LAG 차이 <= 1 로 고친 방식 — kim]")
    show(conn, LAG_ALLOW_SAME_DAY_SQL.replace("ORDER BY user_id, first_day",
                                              "HAVING user_id = 'kim' ORDER BY first_day"),
         [False, False, False, True])
    print("  [LAG 차이 <= 1, COUNT(DISTINCT attend_date) 로 센 방식 — kim]")
    show(conn, LAG_ALLOW_SAME_DAY_SQL
         .replace("COUNT(*) AS days", "COUNT(DISTINCT attend_date) AS days")
         .replace("ORDER BY user_id, first_day",
                  "HAVING user_id = 'kim' ORDER BY first_day"),
         [False, False, False, True])
    conn.execute("ROLLBACK TO dup")
    conn.execute("RELEASE dup")
    print()


def section_text_arithmetic(conn):
    print("== 4) julianday 없이 빼면 ==")
    print("  [TEXT 날짜에서 바로 행 번호를 빼면 — lee]")
    show(conn, """
        SELECT attend_date, attend_date + 0 AS as_number,
               attend_date - ROW_NUMBER() OVER (ORDER BY attend_date) AS grp
        FROM attendance WHERE user_id = 'lee' ORDER BY attend_date
    """, [False, True, True])
    print("  [일(日) 숫자만 꺼내 빼면 — lee]")
    show(conn, """
        SELECT attend_date,
               CAST(strftime('%d', attend_date) AS INTEGER)
                 - ROW_NUMBER() OVER (ORDER BY attend_date) AS grp
        FROM attendance WHERE user_id = 'lee' ORDER BY attend_date
    """, [False, True])
    print("  [julianday 로 빼면 — lee]")
    show(conn, """
        SELECT attend_date,
               julianday(attend_date)
                 - ROW_NUMBER() OVER (ORDER BY attend_date) AS grp
        FROM attendance WHERE user_id = 'lee' ORDER BY attend_date
    """, [False, True])
    print()


def print_plan(conn, sql):
    # sqlite3 CLI 와 같은 방식으로 (id, parent) 를 따라 트리를 그린다
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    children = {}
    for node_id, parent_id, _, detail in rows:
        children.setdefault(parent_id, []).append((node_id, detail))

    def draw(parent_id, prefix):
        items = children.get(parent_id, [])
        for i, (node_id, detail) in enumerate(items):
            last = i == len(items) - 1
            print(prefix + ("`--" if last else "|--") + detail)
            draw(node_id, prefix + ("   " if last else "|  "))

    print("  QUERY PLAN")
    draw(0, "  ")


def section_plan(conn):
    print("== 5) 행 번호 차이 방식의 실행계획 ==")
    print("  [인덱스 없음]")
    print_plan(conn, ROW_NUMBER_SQL)
    conn.execute(
        "CREATE INDEX ix_attendance_user_id_attend_date "
        "ON attendance(user_id, attend_date)")
    print("  [(user_id, attend_date) 인덱스 뒤]")
    print_plan(conn, ROW_NUMBER_SQL)
    print()


def main():
    conn = build_database()
    try:
        print_environment()
        print_dataset(conn)
        section_two_ways(conn)
        section_longest(conn)
        section_duplicate(conn)
        section_text_arithmetic(conn)
        section_plan(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
