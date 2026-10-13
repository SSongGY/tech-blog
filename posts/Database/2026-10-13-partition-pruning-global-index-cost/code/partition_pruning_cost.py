"""파티셔닝이 항상 빨라지지 않는 이유 — 조각 수가 늘면 같이 늘어나는 비용.

SQLite 에는 네이티브 파티션이 없다. 대신 파티션 테이블의 원형인 **UNION ALL 파티션 뷰**를
세워 같은 구조를 만든다. 같은 30,000행을 통짜 표 하나, 연 단위 3조각, 월 단위 36조각으로
각각 넣고 같은 질의를 돌려 일의 양을 비교한다. 조각마다 같은 모양의 로컬 인덱스를 둔다.

일의 양은 시간이 아니라 **VDBE(SQLite 가상 머신) 명령 실행 횟수**로 잰다.
sqlite3.Connection.set_progress_handler(handler, 1) 은 명령 하나마다 handler 를
부르므로, 같은 입력이면 몇 번을 돌려도 같은 수가 나온다. 벽시계 시간과 달리
다른 프로세스에 흔들리지 않는다.
"""

from __future__ import annotations

import random
import sqlite3

from dbshow import print_environment

YEARS = (2024, 2025, 2026)
ROWS_PER_YEAR = 10_000
CUSTOMER_COUNT = 500
RANDOM_SEED = 42
PROBE_CUSTOMER = 137

FLAT_SCHEMA = """
CREATE TABLE order_flat (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    ordered_on  TEXT    NOT NULL,
    amount      INTEGER NOT NULL
);
"""

PART_SCHEMA = """
CREATE TABLE {name} (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    ordered_on  TEXT    NOT NULL,
    amount      INTEGER NOT NULL,
    CHECK (ordered_on >= '{low}' AND ordered_on < '{high}')
);
"""


def make_rows() -> list[tuple[int, int, str, int]]:
    """세 해에 걸쳐 같은 수의 주문을 만든다. 시드를 고정해 매번 같은 데이터가 나온다."""
    rng = random.Random(RANDOM_SEED)
    rows = []
    order_id = 1
    for year in YEARS:
        for _ in range(ROWS_PER_YEAR):
            month = rng.randint(1, 12)
            day = rng.randint(1, 28)
            rows.append((
                order_id,
                rng.randint(1, CUSTOMER_COUNT),
                f"{year}-{month:02d}-{day:02d}",
                rng.randrange(1_000, 500_000, 100),
            ))
            order_id += 1
    return rows


def year_buckets() -> list[tuple[str, str, str]]:
    """(표 이름, 하한, 상한) — 연 단위 3조각."""
    return [(f"order_y{y}", f"{y}-01-01", f"{y + 1}-01-01") for y in YEARS]


def month_buckets() -> list[tuple[str, str, str]]:
    """(표 이름, 하한, 상한) — 월 단위 36조각."""
    out = []
    for year in YEARS:
        for month in range(1, 13):
            high_y, high_m = (year + 1, 1) if month == 12 else (year, month + 1)
            out.append((
                f"order_m{year}{month:02d}",
                f"{year}-{month:02d}-01",
                f"{high_y}-{high_m:02d}-01",
            ))
    return out


def build_partitions(
    conn: sqlite3.Connection,
    view_name: str,
    buckets: list[tuple[str, str, str]],
    rows: list[tuple[int, int, str, int]],
) -> None:
    for name, low, high in buckets:
        conn.executescript(PART_SCHEMA.format(name=name, low=low, high=high))
        conn.executemany(
            f"INSERT INTO {name} VALUES (?, ?, ?, ?)",
            [r for r in rows if low <= r[2] < high],
        )
        conn.execute(f"CREATE INDEX ix_{name}_ordered_on ON {name}(ordered_on)")
        conn.execute(f"CREATE INDEX ix_{name}_customer_id ON {name}(customer_id)")
    union = "\n    UNION ALL\n".join(f"    SELECT * FROM {n}" for n, _, _ in buckets)
    conn.executescript(f"CREATE VIEW {view_name} AS\n{union};")


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(FLAT_SCHEMA)
    rows = make_rows()
    conn.executemany("INSERT INTO order_flat VALUES (?, ?, ?, ?)", rows)
    conn.execute("CREATE INDEX ix_order_flat_ordered_on ON order_flat(ordered_on)")
    conn.execute("CREATE INDEX ix_order_flat_customer_id ON order_flat(customer_id)")

    build_partitions(conn, "order_y", year_buckets(), rows)
    build_partitions(conn, "order_m", month_buckets(), rows)

    conn.execute("ANALYZE")
    conn.commit()
    return conn


def count_steps(conn: sqlite3.Connection, sql: str) -> tuple[int, list[tuple]]:
    """질의 하나를 끝까지 돌리며 VDBE 명령 실행 횟수를 센다."""
    steps = 0

    def tick() -> int:
        nonlocal steps
        steps += 1
        return 0  # 0 이 아니면 질의가 중단된다

    conn.set_progress_handler(tick, 1)
    try:
        rows = conn.execute(sql).fetchall()
    finally:
        conn.set_progress_handler(None, 0)
    return steps, rows


def plan_counts(conn: sqlite3.Connection, sql: str) -> tuple[int, int]:
    """실행계획에서 SEARCH 줄과 SCAN 줄이 각각 몇 개인지 센다."""
    search = scan = 0
    for row in conn.execute("EXPLAIN QUERY PLAN " + sql):
        detail = row[3]
        if detail.startswith("SEARCH "):
            search += 1
        elif detail.startswith("SCAN ") and not detail.startswith("SCAN (subquery"):
            scan += 1
    return search, scan


def compare(conn: sqlite3.Connection, label: str, template: str,
            show_flat_plan: bool = False) -> None:
    """같은 질의를 통짜·3조각·36조각에 돌려 나란히 찍는다."""
    print(f"-- {label}")
    print("   " + " ".join(template.format(t="<표>").split()))
    base = None
    for title, table in (("통짜  1조각", "order_flat"), ("연  단위 3조각", "order_y"),
                         ("월 단위 36조각", "order_m")):
        sql = template.format(t=table)
        steps, rows = count_steps(conn, sql)
        search, scan = plan_counts(conn, sql)
        base = base or steps
        print(f"   [{title}] 결과 {rows[0]} · VDBE {steps:>9,}회 "
              f"· 통짜의 {steps / base:>7.2f}배 · 계획 SEARCH {search} / SCAN {scan}")
        if show_flat_plan and table == "order_flat":
            for row in conn.execute("EXPLAIN QUERY PLAN " + sql):
                print(f"       통짜 계획: {row[3]}")
    print()


def main() -> None:
    conn = build_database()
    print_environment()

    total = conn.execute("SELECT COUNT(*) FROM order_flat").fetchone()[0]
    print("=" * 64)
    print("데이터 — 같은 행을 세 가지 모양으로 넣었다")
    print("=" * 64)
    print(f"  order_flat   {total:,}행 · 표 1개 · 인덱스 ordered_on, customer_id")
    print(f"  order_y      {total:,}행 · 표 3개를 UNION ALL 로 묶은 뷰 · 표마다 같은 인덱스 2개")
    print(f"  order_m      {total:,}행 · 표 36개를 UNION ALL 로 묶은 뷰 · 표마다 같은 인덱스 2개")
    print(f"  고객 수 {CUSTOMER_COUNT}명 · 난수 시드 {RANDOM_SEED}\n")

    print("### 1. CHECK 제약으로 조각을 걸러 주는가")
    print("   order_y 의 각 표에는 연도를 못 박는 CHECK 가 걸려 있다.")
    print("   2026년만 묻는 질의의 실행계획에 order_y2024 가 나오는지 본다.")
    for row in conn.execute(
        "EXPLAIN QUERY PLAN SELECT COUNT(*) FROM order_y "
        "WHERE ordered_on >= '2026-01-01' AND ordered_on < '2027-01-01'"
    ):
        print(f"   {row[3]}")
    print()

    print("### 2. 파티션 키로 범위 조회")
    compare(conn, "2. 2025년 주문 건수",
            "SELECT COUNT(*) FROM {t} "
            "WHERE ordered_on >= '2025-01-01' AND ordered_on < '2026-01-01'")
    compare(conn, "3. 2025년 3월 한 달 — 조각 하나에만 들어 있다",
            "SELECT COUNT(*) FROM {t} "
            "WHERE ordered_on >= '2025-03-01' AND ordered_on < '2025-04-01'")
    compare(conn, "4. 같은 3월을 substr() 로 — 키를 함수로 감쌌다",
            "SELECT COUNT(*) FROM {t} WHERE substr(ordered_on, 1, 7) = '2025-03'")

    print("### 3. 파티션 키가 없는 조회 — 전역 인덱스 대 로컬 인덱스")
    compare(conn, f"5. 고객 {PROBE_CUSTOMER}번의 주문 건수 (연도 조건 없음)",
            f"SELECT COUNT(*) FROM {{t}} WHERE customer_id = {PROBE_CUSTOMER}")
    compare(conn, f"6. 고객 {PROBE_CUSTOMER}번 + 2025년 3월로 좁히면",
            f"SELECT COUNT(*) FROM {{t}} WHERE customer_id = {PROBE_CUSTOMER} "
            "AND ordered_on >= '2025-03-01' AND ordered_on < '2025-04-01'")

    print("### 4. 전 구간 집계와 정렬")
    compare(conn, "7. 전체 주문 금액 합계", "SELECT SUM(amount) FROM {t}")
    compare(conn, "8. 가장 최근 주문 1건",
            "SELECT order_id FROM {t} ORDER BY ordered_on DESC, order_id DESC LIMIT 1",
            show_flat_plan=True)

    conn.close()


if __name__ == "__main__":
    main()
