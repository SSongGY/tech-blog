"""ORDER BY의 다중 정렬 키와 NULL이 놓이는 자리를 SQLite로 확인한다."""

import sqlite3

TIE_QUERY = "SELECT name FROM employee WHERE bonus = 300 ORDER BY bonus DESC"


def build_sample(conn):
    conn.executescript(
        """
        CREATE TABLE employee (
            name     TEXT NOT NULL,
            team     TEXT NOT NULL,
            bonus    INTEGER,          -- 아직 정해지지 않은 사람은 NULL
            hired_on TEXT NOT NULL
        );
        INSERT INTO employee VALUES
            ('강민수', '개발', 300, '2021-03-02'),
            ('김서연', '개발', NULL, '2019-07-15'),
            ('박지훈', '개발', 300, '2023-01-09'),
            ('이하늘', '영업', 500, '2020-11-23'),
            ('정우성', '영업', NULL, '2022-05-30'),
            ('최유진', '영업', 150, '2018-02-14');
        """
    )


def show(conn, label, order_clause):
    sql = f"SELECT name, team, bonus FROM employee ORDER BY {order_clause}"
    print(f"\n-- {label}")
    print(f"   ORDER BY {order_clause}")
    for name, team, bonus in conn.execute(sql):
        print(f"   {name}  {team}  {'NULL' if bonus is None else bonus:>5}")


def report_tie_order(conn, label):
    """같은 질의를 접근 경로만 바꿔 돌려 본다. ORDER BY 절은 손대지 않는다."""
    names = [row[0] for row in conn.execute(TIE_QUERY)]
    plan = [row[3] for row in conn.execute("EXPLAIN QUERY PLAN " + TIE_QUERY)]
    print(f"   {label:14} 결과: {names}")
    print(f"   {'':14} 계획: {plan[0]}")


def main():
    print(f"SQLite {sqlite3.sqlite_version}")
    conn = sqlite3.connect(":memory:")
    build_sample(conn)

    show(conn, "1. 오름차순 기본값 — NULL은 어디로 가는가", "bonus ASC")
    show(conn, "2. 내림차순 기본값", "bonus DESC")
    show(conn, "3. 오름차순인데 NULL을 뒤로", "bonus ASC NULLS LAST")
    show(conn, "4. 내림차순인데 NULL을 앞으로", "bonus DESC NULLS FIRST")
    show(conn, "5. 정렬 키 두 개 — 1순위 team, 2순위 bonus", "team ASC, bonus DESC")
    show(conn, "6. 키마다 방향을 따로 준다", "team DESC, bonus ASC NULLS LAST")
    show(conn, "7. 동점(bonus 300)을 가르는 3순위 키", "bonus DESC NULLS LAST, hired_on ASC")

    print("\n-- 8. 동점 행의 순서는 왜 믿으면 안 되는가")
    report_tie_order(conn, "인덱스 없음")
    conn.execute("CREATE INDEX idx_bonus_name ON employee(bonus, name DESC)")
    report_tie_order(conn, "인덱스 생성 후")

    conn.close()


if __name__ == "__main__":
    main()
