"""행 값(row value) — 여러 컬럼을 괄호로 묶어 한 번에 다룬다.

1) 묶음 비교는 왼쪽 컬럼부터 차례로 본다 — NULL 이 끼면 어떻게 되는가
2) 연·월이 따로 저장된 표에서 기간 거르기 — 컬럼별 조건과 묶음 비교
3) 두 컬럼을 함께 IN — 부질의, VALUES, 괄호 목록
4) NOT IN 과 행 값 안의 NULL
5) UPDATE SET (a, b) = (SELECT ...) — 부질의가 0행이면
6) 쓸 수 없는 자리 — 크기가 다르거나 결과 컬럼에 쓸 때
7) 실행계획 — 묶음 비교가 (year, month) 인덱스를 타는가
"""
import sqlite3

from dbshow import print_dataset, print_environment


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE monthly_sales (
            year    INTEGER NOT NULL,
            month   INTEGER NOT NULL,
            region  TEXT    NOT NULL,
            amount  INTEGER NOT NULL
        );
        INSERT INTO monthly_sales VALUES
            (2025, 10, 'north', 120), (2025, 11, 'north', 130),
            (2025, 12, 'north', 150), (2026,  1, 'north', 110),
            (2026,  2, 'north', 140), (2026,  3, 'north', 160),
            (2025, 11, 'south',  90), (2026,  1, 'south', 100),
            (2026,  4, 'south',  95), (2025,  1, 'south',  80);

        CREATE TABLE closed_month (
            year   INTEGER,
            month  INTEGER
        );
        INSERT INTO closed_month VALUES (2025, 11), (2026, 1);

        CREATE TABLE employee (
            emp_id  INTEGER PRIMARY KEY,
            name    TEXT NOT NULL,
            dept    TEXT,
            grade   INTEGER
        );
        INSERT INTO employee(name, dept, grade) VALUES
            ('kim', 'sales', 3), ('lee', 'dev', 2), ('park', 'ops', 1);

        CREATE TABLE promotion (
            emp_id    INTEGER PRIMARY KEY,
            new_dept  TEXT,
            new_grade INTEGER
        );
        INSERT INTO promotion VALUES (1, 'sales', 4), (2, 'platform', 3);
        """
    )
    return conn


def show(conn, sql):
    print("  sql> " + " ".join(sql.split()))
    try:
        cursor = conn.execute(sql)
    except sqlite3.Error as exc:
        print(f"  {type(exc).__name__}: {exc}")
        print()
        return
    headers = [d[0] for d in cursor.description]
    print("  " + " | ".join(headers))
    for row in cursor.fetchall():
        print("  " + " | ".join("NULL" if v is None else repr(v) for v in row))
    print()


def show_plan(conn, sql):
    """EXPLAIN QUERY PLAN 의 (id, parent) 로 sqlite3 CLI 와 같은 트리를 그린다."""
    print("  sql> " + " ".join(sql.split()))
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    children = {}
    for node_id, parent, _, detail in rows:
        children.setdefault(parent, []).append((node_id, detail))

    def draw(parent, prefix):
        kids = children.get(parent, [])
        for i, (node_id, detail) in enumerate(kids):
            last = i == len(kids) - 1
            print("  " + prefix + ("`--" if last else "|--") + detail)
            draw(node_id, prefix + ("   " if last else "|  "))

    print("  QUERY PLAN")
    draw(0, "")
    print()


def section_compare(conn):
    print("== 1) 묶음 비교는 왼쪽 컬럼부터 — NULL 이 끼면 ==")
    show(conn, "SELECT (2025, 12) < (2026, 1) AS a, (2026, 3) < (2026, 10) AS b, (2026, 3) = (2026, 3) AS c")
    show(conn, "SELECT (2026, NULL) = (2026, 3) AS eq_null, (2025, NULL) = (2026, 3) AS eq_false")
    show(conn, "SELECT (2025, NULL) < (2026, 3) AS lt_decided, (2026, NULL) < (2026, 3) AS lt_unknown")
    show(conn, "SELECT (2026, NULL) IS (2026, NULL) AS is_same")


def section_range(conn):
    print("== 2) 2025년 11월부터 2026년 2월까지 — 컬럼별 조건과 묶음 비교 ==")
    show(conn, """
        SELECT year, month, region, amount FROM monthly_sales
        WHERE year >= 2025 AND month >= 11 AND year <= 2026 AND month <= 2
        ORDER BY year, month, region
    """)
    show(conn, """
        SELECT year, month, region, amount FROM monthly_sales
        WHERE (year, month) >= (2025, 11) AND (year, month) <= (2026, 2)
        ORDER BY year, month, region
    """)
    show(conn, """
        SELECT year, month, region, amount FROM monthly_sales
        WHERE (year, month) BETWEEN (2025, 11) AND (2026, 2)
        ORDER BY year, month, region
    """)


def section_in(conn):
    print("== 3) 두 컬럼을 함께 IN ==")
    show(conn, """
        SELECT year, month, region, amount FROM monthly_sales
        WHERE (year, month) IN (SELECT year, month FROM closed_month)
        ORDER BY year, month, region
    """)
    show(conn, """
        SELECT year, month, region, amount FROM monthly_sales
        WHERE (year, month) IN (VALUES (2025, 12), (2026, 3))
        ORDER BY year, month, region
    """)
    show(conn, """
        SELECT year, month, region FROM monthly_sales
        WHERE (year, month) IN ((2025, 12), (2026, 3))
    """)
    print("  -- 컬럼마다 따로 IN 을 걸면 짝이 풀린다")
    show(conn, """
        SELECT year, month, region, amount FROM monthly_sales
        WHERE year IN (SELECT year FROM closed_month)
          AND month IN (SELECT month FROM closed_month)
        ORDER BY year, month, region
    """)


def section_not_in(conn):
    print("== 4) NOT IN 과 행 값 안의 NULL ==")
    show(conn, """
        SELECT count(*) AS open_rows FROM monthly_sales
        WHERE (year, month) NOT IN (SELECT year, month FROM closed_month)
    """)
    conn.execute("INSERT INTO closed_month VALUES (2026, NULL)")
    print("  -- closed_month 에 (2026, NULL) 을 넣은 뒤")
    show(conn, """
        SELECT year, month, region FROM monthly_sales
        WHERE (year, month) NOT IN (SELECT year, month FROM closed_month)
        ORDER BY year, month, region
    """)
    show(conn, """
        SELECT year, month, region FROM monthly_sales AS s
        WHERE NOT EXISTS (SELECT 1 FROM closed_month AS c
                          WHERE c.year = s.year AND c.month = s.month)
        ORDER BY year, month, region
    """)
    conn.execute("DELETE FROM closed_month WHERE month IS NULL")


def section_update(conn):
    print("== 5) UPDATE SET (dept, grade) = (SELECT ...) ==")
    conn.execute("""
        UPDATE employee
        SET (dept, grade) = (SELECT new_dept, new_grade FROM promotion
                             WHERE promotion.emp_id = employee.emp_id)
        WHERE emp_id IN (SELECT emp_id FROM promotion)
    """)
    show(conn, "SELECT emp_id, name, dept, grade FROM employee ORDER BY emp_id")
    print("  -- WHERE 없이 같은 UPDATE 를 한 번 더 — park 은 promotion 에 없다")
    cursor = conn.execute("""
        UPDATE employee
        SET (dept, grade) = (SELECT new_dept, new_grade FROM promotion
                             WHERE promotion.emp_id = employee.emp_id)
    """)
    print(f"  바뀐 행 수: {cursor.rowcount}")
    show(conn, "SELECT emp_id, name, dept, grade FROM employee ORDER BY emp_id")
    print("  -- 두 컬럼 맞바꾸기도 묶음으로 쓸 수 있다")
    conn.execute("UPDATE closed_month SET (year, month) = (month, year)")
    show(conn, "SELECT year, month FROM closed_month ORDER BY rowid")
    conn.execute("UPDATE closed_month SET (year, month) = (month, year)")


def section_errors(conn):
    print("== 6) 쓸 수 없는 자리 ==")
    show(conn, "SELECT (1, 2) = (1, 2, 3)")
    show(conn, "SELECT (year, month) FROM monthly_sales LIMIT 1")
    show(conn, "SELECT year FROM monthly_sales WHERE (year, month) = (SELECT year FROM closed_month)")


def section_plan(conn):
    print("== 7) 실행계획 — (year, month) 인덱스 ==")
    conn.execute("CREATE INDEX idx_sales_ym ON monthly_sales(year, month)")
    show_plan(conn, """
        SELECT * FROM monthly_sales
        WHERE (year, month) >= (2025, 11) AND (year, month) <= (2026, 2)
    """)
    show_plan(conn, """
        SELECT * FROM monthly_sales
        WHERE year >= 2025 AND month >= 11 AND year <= 2026 AND month <= 2
    """)
    show_plan(conn, """
        SELECT * FROM monthly_sales
        WHERE (year, month) IN (SELECT year, month FROM closed_month)
    """)


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)
    section_compare(conn)
    section_range(conn)
    section_in(conn)
    section_not_in(conn)
    section_update(conn)
    section_errors(conn)
    section_plan(conn)
    conn.close()


if __name__ == "__main__":
    main()
