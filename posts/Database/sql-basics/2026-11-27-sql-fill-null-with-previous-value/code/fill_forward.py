"""값이 빠진(NULL) 행을 바로 앞의 값으로 채운다.

1) 흔한 시도 — COALESCE(temp, LAG(temp)) 는 빈 칸이 둘 이상 이어지면 못 채운다
2) IGNORE NULLS 는 SQLite 에 없다
3) 방법 A: 상관 부질의 (앞쪽에서 NULL 아닌 마지막 값)
4) 방법 B: COUNT(temp) 누적으로 묶음 번호를 만들고 묶음 안에서 MAX 로 편다
5) 방법 C: 재귀 CTE 로 한 행씩 내려가며 값을 넘긴다
6) 같은 시각이 두 번 찍힌 행 — 기본 프레임(RANGE)과 ROWS 가 갈린다
7) 실행계획
8) 행 수를 늘려 VDBE 명령 수를 센다
"""
import random
import sqlite3

from dbshow import print_dataset, print_environment


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE reading (
            sensor_id TEXT    NOT NULL,
            ts        TEXT    NOT NULL,   -- 측정 시각
            temp      REAL,               -- 측정 실패면 NULL
            PRIMARY KEY (sensor_id, ts)
        );
        INSERT INTO reading VALUES
            ('S1', '09:00', NULL),        -- 첫 값부터 빠졌다
            ('S1', '09:10', 21.5),
            ('S1', '09:20', NULL),
            ('S1', '09:30', NULL),        -- 빈 칸 두 개가 이어진다
            ('S1', '09:40', 22.0),
            ('S1', '09:50', NULL),
            ('S2', '09:00', 30.1),
            ('S2', '09:10', NULL),
            ('S2', '09:20', NULL),
            ('S2', '09:30', NULL),
            ('S2', '09:40', 29.8);
        """
    )
    return conn


def show_rows(conn, sql, params=()):
    print("  sql> " + " ".join(sql.split())[:150] + " ...")
    cursor = conn.execute(sql, params)
    print("   ", tuple(d[0] for d in cursor.description))
    for row in cursor:
        print("   ", row)


def show_plan(conn, sql):
    """sqlite3 CLI 가 그리는 것과 같은 모양의 트리로 EXPLAIN QUERY PLAN 을 찍는다."""
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    children = {}
    for node_id, parent, _, detail in rows:
        children.setdefault(parent, []).append((node_id, detail))

    def walk(parent, prefix):
        nodes = children.get(parent, [])
        for i, (node_id, detail) in enumerate(nodes):
            last = i == len(nodes) - 1
            print("    " + prefix + ("`--" if last else "|--") + detail)
            walk(node_id, prefix + ("   " if last else "|  "))

    print("    QUERY PLAN")
    walk(0, "")


SQL_LAG = """
    SELECT sensor_id, ts, temp,
           COALESCE(temp, LAG(temp) OVER (PARTITION BY sensor_id ORDER BY ts)) AS filled
    FROM reading ORDER BY sensor_id, ts
"""

SQL_IGNORE_NULLS = """
    SELECT sensor_id, ts,
           LAST_VALUE(temp IGNORE NULLS) OVER (PARTITION BY sensor_id ORDER BY ts) AS filled
    FROM reading
"""

SQL_SUBQUERY = """
    SELECT r.sensor_id, r.ts, r.temp,
           (SELECT p.temp FROM reading p
             WHERE p.sensor_id = r.sensor_id
               AND p.ts <= r.ts
               AND p.temp IS NOT NULL
             ORDER BY p.ts DESC LIMIT 1) AS filled
    FROM reading r ORDER BY r.sensor_id, r.ts
"""

SQL_GROUPS = """
    WITH grouped AS (
        SELECT sensor_id, ts, temp,
               COUNT(temp) OVER (PARTITION BY sensor_id ORDER BY ts
                                 ROWS UNBOUNDED PRECEDING) AS grp
        FROM reading
    )
    SELECT sensor_id, ts, temp, grp,
           MAX(temp) OVER (PARTITION BY sensor_id, grp) AS filled
    FROM grouped ORDER BY sensor_id, ts
"""

SQL_RECURSIVE = """
    WITH RECURSIVE numbered AS (
        SELECT sensor_id, ts, temp,
               ROW_NUMBER() OVER (PARTITION BY sensor_id ORDER BY ts) AS rn
        FROM reading
    ),
    walk(sensor_id, ts, temp, rn, filled) AS (
        SELECT sensor_id, ts, temp, rn, temp FROM numbered WHERE rn = 1
        UNION ALL
        SELECT n.sensor_id, n.ts, n.temp, n.rn, COALESCE(n.temp, w.filled)
        FROM walk w JOIN numbered n
          ON n.sensor_id = w.sensor_id AND n.rn = w.rn + 1
    )
    SELECT sensor_id, ts, temp, filled FROM walk ORDER BY sensor_id, ts
"""


def fill_only(sql):
    """결과 비교용 — (sensor_id, ts, filled) 만 남긴다."""
    return f"SELECT sensor_id, ts, filled FROM ({sql})"


def count_vdbe(conn, sql):
    steps = 0

    def tick():
        nonlocal steps
        steps += 1
        return 0

    conn.set_progress_handler(tick, 1)
    rows = conn.execute(sql).fetchall()
    conn.set_progress_handler(None, 1)
    return steps, rows


def build_large(sensor_count, rows_per_sensor, null_ratio, with_key=True):
    rng = random.Random(20261127)
    conn = sqlite3.connect(":memory:")
    key = ", PRIMARY KEY (sensor_id, ts)" if with_key else ""
    conn.execute(
        "CREATE TABLE reading (sensor_id TEXT NOT NULL, ts TEXT NOT NULL,"
        f" temp REAL{key})"
    )
    data = []
    for s in range(sensor_count):
        for i in range(rows_per_sensor):
            value = None if rng.random() < null_ratio else round(rng.uniform(15, 35), 1)
            data.append((f"S{s:03d}", f"{i:06d}", value))
    conn.executemany("INSERT INTO reading VALUES (?, ?, ?)", data)
    return conn


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("\n[1] COALESCE(temp, LAG(temp)) — 빈 칸이 이어지면 둘째 칸부터 못 채운다")
    show_rows(conn, SQL_LAG)

    print("\n[2] LAST_VALUE(temp IGNORE NULLS)")
    try:
        conn.execute(SQL_IGNORE_NULLS)
    except sqlite3.OperationalError as error:
        print("  sqlite3.OperationalError:", error)

    print("\n[3] 방법 A — 상관 부질의")
    show_rows(conn, SQL_SUBQUERY)

    print("\n[4] 방법 B — COUNT(temp) 누적으로 묶음 번호(grp)를 만들고 묶음 안에서 MAX")
    show_rows(conn, SQL_GROUPS)

    print("\n[5] 방법 C — 재귀 CTE")
    show_rows(conn, SQL_RECURSIVE)

    a = conn.execute(fill_only(SQL_SUBQUERY)).fetchall()
    b = conn.execute(fill_only(SQL_GROUPS)).fetchall()
    c = conn.execute(fill_only(SQL_RECURSIVE)).fetchall()
    print("\n  세 방법의 결과가 같은가:", a == b == c)

    print("\n[6] 같은 시각이 두 번 찍힌 행 — 키를 (sensor_id, ts, seq) 로 바꾼 표")
    conn.executescript(
        """
        CREATE TABLE reading_dup (
            sensor_id TEXT NOT NULL, ts TEXT NOT NULL, seq INTEGER NOT NULL,
            temp REAL, PRIMARY KEY (sensor_id, ts, seq)
        );
        INSERT INTO reading_dup VALUES
            ('S1', '09:00', 1, 20.0),
            ('S1', '09:10', 1, NULL),
            ('S1', '09:10', 2, 25.0),     -- 같은 시각에 값이 하나 더 들어왔다
            ('S1', '09:20', 1, NULL);
        """
    )
    print("  (6-1) 프레임을 적지 않음 — 기본 RANGE 는 같은 ts 를 한 덩어리로 센다")
    show_rows(conn, """
        SELECT ts, seq, temp,
               COUNT(temp) OVER (ORDER BY ts) AS grp
        FROM reading_dup ORDER BY ts, seq
    """)
    print("  (6-2) ROWS UNBOUNDED PRECEDING, 정렬 키에 seq 까지")
    show_rows(conn, """
        SELECT ts, seq, temp,
               COUNT(temp) OVER (ORDER BY ts, seq ROWS UNBOUNDED PRECEDING) AS grp
        FROM reading_dup ORDER BY ts, seq
    """)

    print("\n[7] 실행계획")
    for label, sql in (("A 상관 부질의", SQL_SUBQUERY), ("B COUNT 묶음", SQL_GROUPS),
                       ("C 재귀 CTE", SQL_RECURSIVE)):
        print(f"  [{label}]")
        show_plan(conn, sql)

    print("\n[8] 센서 20개 x 행 수, 빈 칸 비율 30% — VDBE 명령 수")
    print(f"  {'행 수':>8} {'A 상관 부질의':>14} {'B COUNT 묶음':>14} {'C 재귀 CTE':>14}  결과 일치")
    for rows_per_sensor in (50, 200, 800):
        big = build_large(20, rows_per_sensor, 0.3)
        sa, ra = count_vdbe(big, fill_only(SQL_SUBQUERY))
        sb, rb = count_vdbe(big, fill_only(SQL_GROUPS))
        sc, rc = count_vdbe(big, fill_only(SQL_RECURSIVE))
        total = 20 * rows_per_sensor
        print(f"  {total:>8,} {sa:>14,} {sb:>14,} {sc:>14,}  {ra == rb == rc}")
        big.close()

    print("\n[9] 빈 칸이 길게 이어질 때 — 빈 칸 비율 90%, 16,000행")
    big = build_large(20, 800, 0.9)
    sa, _ = count_vdbe(big, fill_only(SQL_SUBQUERY))
    sb, _ = count_vdbe(big, fill_only(SQL_GROUPS))
    print(f"  A 상관 부질의 {sa:,}   B COUNT 묶음 {sb:,}")
    big.close()

    print("\n[10] (sensor_id, ts) 인덱스가 없는 표 — 빈 칸 비율 30%")
    for rows_per_sensor in (50, 200):
        big = build_large(20, rows_per_sensor, 0.3, with_key=False)
        sa, _ = count_vdbe(big, fill_only(SQL_SUBQUERY))
        sb, _ = count_vdbe(big, fill_only(SQL_GROUPS))
        print(f"  {20 * rows_per_sensor:>6,}행  A 상관 부질의 {sa:>12,}   B COUNT 묶음 {sb:>10,}")
        if rows_per_sensor == 200:
            print("  [A 상관 부질의, 인덱스 없음]")
            show_plan(big, SQL_SUBQUERY)
        big.close()
    conn.close()


if __name__ == "__main__":
    main()
