"""VALUES 절을 표처럼 써서 임시 데이터를 조인에 끼워 넣는다.

SQLite 3.49.1 / Python 3.13.5 에서 돌렸다. 외부 의존성은 없다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

CHANNEL_CODES = [("ON", "온라인"), ("OF", "오프라인"), ("MO", "모바일")]
BIG_ROW_COUNT = 50000


def build_database() -> sqlite3.Connection:
    """매출 4건. 코드 XX 는 일부러 코드표에 없는 값으로 넣는다."""
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE sale (
            sale_id INTEGER PRIMARY KEY,
            ch      TEXT    NOT NULL,
            amount  INTEGER NOT NULL
        )
        """
    )
    conn.executemany(
        "INSERT INTO sale VALUES (?, ?, ?)",
        [(1, "ON", 100), (2, "OF", 200), (3, "ON", 50), (4, "XX", 10)],
    )
    conn.commit()
    return conn


def show_plan(conn: sqlite3.Connection, sql: str) -> None:
    """sqlite3 CLI 가 그리는 트리와 같은 모양으로 detail 을 찍는다."""
    rows = list(conn.execute("EXPLAIN QUERY PLAN " + sql))
    children: dict[int, list[tuple[int, str]]] = {}
    for node_id, parent_id, _, detail in rows:
        children.setdefault(parent_id, []).append((node_id, detail))

    def walk(parent_id: int, prefix: str) -> None:
        kids = children.get(parent_id, [])
        for index, (node_id, detail) in enumerate(kids):
            last = index == len(kids) - 1
            print(f"{prefix}{'`--' if last else '|--'}{detail}")
            walk(node_id, prefix + ("   " if last else "|  "))

    print("QUERY PLAN")
    walk(0, "")


def section(title: str) -> None:
    print()
    print("=" * 62)
    print(title)
    print("=" * 62)


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)

    section("1. 단독 VALUES 는 그 자체로 결과 집합이다")
    cur = conn.execute("VALUES ('ON', '온라인'), ('OF', '오프라인')")
    print("컬럼 이름:", [desc[0] for desc in cur.description])
    print("행       :", cur.fetchall())

    section("2. CTE 로 이름을 붙이면 표가 된다")
    sql = """
        WITH channel(code, label) AS (
            VALUES ('ON','온라인'), ('OF','오프라인'), ('MO','모바일')
        )
        SELECT channel.label, COALESCE(SUM(sale.amount), 0) AS total
        FROM channel LEFT JOIN sale ON sale.ch = channel.code
        GROUP BY channel.code, channel.label
        ORDER BY channel.code
    """
    cur = conn.execute(sql)
    print("컬럼 이름:", [desc[0] for desc in cur.description])
    for label, total in cur.fetchall():
        print(f"  {label:<6} {total:>5}")

    section("3. 같은 일을 CASE 로 하면 두 가지가 빠진다")
    case_sql = """
        SELECT CASE ch WHEN 'ON' THEN '온라인'
                       WHEN 'OF' THEN '오프라인'
                       WHEN 'MO' THEN '모바일' END AS label,
               SUM(amount) AS total
        FROM sale GROUP BY 1 ORDER BY 1
    """
    for label, total in conn.execute(case_sql).fetchall():
        print(f"  {str(label):<6} {total:>5}")
    print("  → 매출이 0인 '모바일' 행이 없고, 코드표에 없는 'XX' 가 NULL 로 섞였다")

    section("4. 코드표에 없는 값만 뽑아낸다")
    unknown_sql = """
        WITH channel(code, label) AS (
            VALUES ('ON','온라인'), ('OF','오프라인'), ('MO','모바일')
        )
        SELECT DISTINCT sale.ch
        FROM sale LEFT JOIN channel ON sale.ch = channel.code
        WHERE channel.code IS NULL
    """
    print("  코드표에 없는 값:", [row[0] for row in conn.execute(unknown_sql)])

    section("5. 질의 계획 — VALUES 목록에는 인덱스가 없다")
    conn.execute("CREATE TABLE big (big_id INTEGER PRIMARY KEY, ch TEXT NOT NULL)")
    conn.executemany(
        "INSERT INTO big VALUES (?, ?)",
        [(i, CHANNEL_CODES[i % 3][0]) for i in range(1, BIG_ROW_COUNT + 1)],
    )
    join_sql = """
        WITH channel(code, label) AS (
            VALUES ('ON','온라인'), ('OF','오프라인'), ('MO','모바일')
        )
        SELECT channel.label, COUNT(*) FROM channel JOIN big ON big.ch = channel.code
        GROUP BY channel.code, channel.label
    """
    print("-- big.ch 에 인덱스가 없을 때")
    show_plan(conn, join_sql)
    conn.execute("CREATE INDEX ix_big_ch ON big(ch)")
    conn.execute("ANALYZE")
    print("-- big.ch 에 인덱스를 만든 뒤")
    show_plan(conn, join_sql)

    section("6. VALUES 리터럴에는 타입 친화성이 없다")
    conn.execute("CREATE TABLE num_key (k INTEGER PRIMARY KEY, v TEXT NOT NULL)")
    conn.execute("INSERT INTO num_key VALUES (1, '일')")
    pairs = [
        (
            "INTEGER 컬럼 = VALUES 의 문자 '1'",
            "WITH m(k) AS (VALUES ('1')) "
            "SELECT COUNT(*) FROM num_key JOIN m ON num_key.k = m.k",
        ),
        (
            "VALUES 의 숫자 1 = VALUES 의 문자 '1'",
            "WITH a(x) AS (VALUES (1)), b(x) AS (VALUES ('1')) "
            "SELECT COUNT(*) FROM a JOIN b ON a.x = b.x",
        ),
    ]
    for label, probe_sql in pairs:
        print(f"  {label:<34} 매칭 {conn.execute(probe_sql).fetchone()[0]}건")

    section("7. 컬럼 이름은 CTE 에서만 붙는다")
    forms = [
        "SELECT * FROM (VALUES (1,'x')) AS n(a, b)",
        "SELECT * FROM (VALUES (1,'x')) AS n",
        "WITH n(a, b) AS (VALUES (1,'x')) SELECT * FROM n",
    ]
    for form in forms:
        try:
            cur = conn.execute(form)
            names = [desc[0] for desc in cur.description]
            print(f"  OK   {form:<48} {names}")
        except sqlite3.OperationalError as exc:
            print(f"  에러 {form:<48} {exc}")

    section("8. MATERIALIZED 힌트를 붙이면 계획이 바뀐다")
    for hint in ("", "MATERIALIZED "):
        hinted = f"""
            WITH channel(code, label) AS {hint}(
                VALUES ('ON','온라인'), ('OF','오프라인'), ('MO','모바일')
            )
            SELECT channel.label FROM channel JOIN big ON big.ch = channel.code LIMIT 3
        """
        first = next(iter(conn.execute("EXPLAIN QUERY PLAN " + hinted)))[3]
        print(f"  {hint or '(힌트 없음)':<16} 첫 줄: {first}")

    section("9. 리터럴로 적는 행 수와 바인딩 파라미터 수는 상한이 다르다")
    for count in (10000, 100000):
        body = ",".join(f"({i})" for i in range(count))
        total = conn.execute(
            f"WITH m(a) AS (VALUES {body}) SELECT COUNT(*) FROM m"
        ).fetchone()[0]
        print(f"  OK   리터럴 {count}행 — COUNT(*) = {total}")
    for count in (32766, 32767):
        body = ",".join("(?)" for _ in range(count))
        try:
            conn.execute(
                f"WITH m(a) AS (VALUES {body}) SELECT COUNT(*) FROM m",
                list(range(count)),
            )
            print(f"  OK   파라미터 {count}개")
        except sqlite3.OperationalError as exc:
            print(f"  에러 파라미터 {count}개 — {exc}")

    conn.close()


if __name__ == "__main__":
    main()
