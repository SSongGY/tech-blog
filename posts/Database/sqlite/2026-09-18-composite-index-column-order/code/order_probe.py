"""복합 인덱스의 컬럼 순서가 스캔 범위를 얼마나 바꾸는지 측정한다.

같은 두 컬럼으로 순서만 바꾼 인덱스 두 개를 만들고, INDEXED BY로 사용할 인덱스를
고정한 뒤 같은 질의를 돌린다. 실행계획에 찍힌 seek 조건을 그대로 COUNT(*)로 세어
"인덱스가 실제로 훑어야 하는 범위"를 행 수로 확인한다.

표준 라이브러리만 쓴다.  실행: python order_probe.py
"""

from __future__ import annotations

import random
import sqlite3
import time
from dataclasses import dataclass

ROW_COUNT = 300_000
REPEAT_COUNT = 5
RANDOM_SEED = 20260918  # 측정값을 재현하려면 시드를 고정해야 한다

# status는 일부러 치우치게 넣는다. 선행 컬럼의 선택도가 결과를 가르는지 보기 위해서다.
STATUS_WEIGHTS = [("active", 70), ("dormant", 25), ("locked", 5)]
CHANNEL_NAMES = [f"ch{i:02d}" for i in range(12)]

DAY_SECONDS = 86_400
BASE_EPOCH = 1_735_689_600  # 2025-01-01 00:00:00 UTC
SPAN_DAYS = 180
CUTOFF_DAY = 150  # created_at 범위 조건의 기준점


@dataclass(frozen=True)
class Timing:
    label: str
    plan: str
    result_rows: int
    best_ms: float


def build_database(use_analyze: bool = True) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE app_event (
            event_id   INTEGER PRIMARY KEY,
            status     TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            channel    TEXT NOT NULL,
            amount     INTEGER NOT NULL
        )
        """
    )

    rng = random.Random(RANDOM_SEED)
    statuses = [name for name, weight in STATUS_WEIGHTS for _ in range(weight)]
    rows = []
    for event_id in range(1, ROW_COUNT + 1):
        offset_day = rng.randrange(SPAN_DAYS)
        rows.append(
            (
                event_id,
                rng.choice(statuses),
                BASE_EPOCH + offset_day * DAY_SECONDS + rng.randrange(DAY_SECONDS),
                rng.choice(CHANNEL_NAMES),
                rng.randrange(1_000, 500_000),
            )
        )
    conn.executemany("INSERT INTO app_event VALUES (?, ?, ?, ?, ?)", rows)

    # 같은 두 컬럼, 순서만 다른 인덱스. 이 글의 비교 대상이다.
    conn.execute("CREATE INDEX ix_event_status_created ON app_event(status, created_at)")
    conn.execute("CREATE INDEX ix_event_created_status ON app_event(created_at, status)")
    conn.execute("CREATE INDEX ix_event_channel_status ON app_event(channel, status)")
    # 두 번째 컬럼만 다른 한 쌍. 정렬을 없앨 수 있는지가 여기서 갈린다.
    conn.execute("CREATE INDEX ix_event_status_amount ON app_event(status, amount)")
    if use_analyze:
        conn.execute("ANALYZE")
    return conn


def plan_of(conn: sqlite3.Connection, sql: str, params: tuple) -> str:
    rows = conn.execute(f"EXPLAIN QUERY PLAN {sql}", params).fetchall()
    return " / ".join(row[3] for row in rows)


def measure(conn: sqlite3.Connection, label: str, sql: str, params: tuple) -> Timing:
    plan = plan_of(conn, sql, params)
    best_ms = float("inf")
    fetched = 0
    for _ in range(REPEAT_COUNT):
        started = time.perf_counter()
        fetched = len(conn.execute(sql, params).fetchall())
        best_ms = min(best_ms, (time.perf_counter() - started) * 1000)
    return Timing(label, plan, fetched, best_ms)


def scan_width(conn: sqlite3.Connection, where_clause: str, params: tuple) -> int:
    """실행계획이 seek 조건으로 쓴 술어만 남겨 세면 훑는 범위가 나온다."""
    sql = f"SELECT COUNT(*) FROM app_event WHERE {where_clause}"
    return conn.execute(sql, params).fetchone()[0]


def print_table(title: str, timings: list[Timing]) -> None:
    print(f"\n### {title}")
    for t in timings:
        print(f"  [{t.label}] {t.best_ms:8.2f}ms  결과 {t.result_rows:,}행")
        print(f"      {t.plan}")


def case_equality_plus_range(conn: sqlite3.Connection) -> None:
    """등치 + 범위 조건: 여기서 컬럼 순서가 갈린다."""
    cutoff = BASE_EPOCH + CUTOFF_DAY * DAY_SECONDS
    params = ("locked", cutoff)
    where = "status = ? AND created_at >= ?"

    timings = []
    for index_name in ("ix_event_status_created", "ix_event_created_status"):
        sql = (
            f"SELECT event_id FROM app_event INDEXED BY {index_name} "
            f"WHERE {where}"
        )
        timings.append(measure(conn, index_name, sql, params))
    print_table("등치 + 범위 — WHERE status = 'locked' AND created_at >= cutoff", timings)

    narrow = scan_width(conn, "status = ? AND created_at >= ?", params)
    wide = scan_width(conn, "created_at >= ?", (cutoff,))
    print(f"  훑는 범위: (status, created_at) = {narrow:,}행"
          f"  /  (created_at, status) = {wide:,}행  → {wide / narrow:.1f}배")


def case_both_equality(conn: sqlite3.Connection) -> None:
    """양쪽 모두 등치면 WHERE 절에 쓴 순서와 무관하게 같은 집합으로 좁혀진다."""
    timings = []
    for where, bind in (
        ("channel = ? AND status = ?", ("ch03", "locked")),
        ("status = ? AND channel = ?", ("locked", "ch03")),
    ):
        sql = (
            "SELECT event_id FROM app_event INDEXED BY ix_event_channel_status "
            f"WHERE {where}"
        )
        timings.append(measure(conn, where, sql, bind))
    print_table("등치 + 등치 — WHERE 절에 쓴 순서를 바꿔도 같은가", timings)

    both = scan_width(conn, "channel = ? AND status = ?", ("ch03", "locked"))
    leading_only = scan_width(conn, "channel = ?", ("ch03",))
    print(f"  훑는 범위: 두 컬럼 모두 seek = {both:,}행"
          f"  /  선행 컬럼만 seek = {leading_only:,}행")


def case_prefix_only(conn: sqlite3.Connection) -> None:
    """후행 컬럼만 조건에 쓰면 인덱스의 선행 컬럼을 건너뛸 수 있는가."""
    timings = []
    sql_second = (
        "SELECT event_id FROM app_event INDEXED BY ix_event_channel_status "
        "WHERE status = ?"
    )
    timings.append(measure(conn, "후행 컬럼만 (status)", sql_second, ("locked",)))
    sql_first = (
        "SELECT event_id FROM app_event INDEXED BY ix_event_channel_status "
        "WHERE channel = ?"
    )
    timings.append(measure(conn, "선행 컬럼만 (channel)", sql_first, ("ch03",)))
    print_table("선행 컬럼을 생략했을 때 — ix_event_channel_status(channel, status)", timings)


def case_order_by(conn: sqlite3.Connection) -> None:
    """정렬 제거: 두 번째 컬럼이 ORDER BY 컬럼이면 정렬 단계가 사라진다."""
    timings = []
    for index_name in ("ix_event_status_created", "ix_event_status_amount"):
        sql = (
            f"SELECT event_id, created_at FROM app_event INDEXED BY {index_name} "
            f"WHERE status = ? ORDER BY created_at LIMIT 20"
        )
        timings.append(measure(conn, index_name, sql, ("locked",)))
    print_table(
        "WHERE status = 'locked' ORDER BY created_at LIMIT 20 — 정렬이 남는가", timings
    )


def case_statistics_dependency() -> None:
    """스킵 스캔은 통계에 의존한다. ANALYZE 유무만 바꿔 계획을 비교한다."""
    sql = (
        "SELECT event_id FROM app_event INDEXED BY ix_event_channel_status "
        "WHERE status = ?"
    )
    print("\n### 같은 질의, ANALYZE 유무만 다를 때")
    for use_analyze in (True, False):
        conn = build_database(use_analyze=use_analyze)
        print(f"  ANALYZE={use_analyze!s:5s} -> {plan_of(conn, sql, ('locked',))}")
        conn.close()


def main() -> None:
    print(f"SQLite {sqlite3.sqlite_version} · 행 {ROW_COUNT:,} · 각 케이스 {REPEAT_COUNT}회 중 최솟값")
    conn = build_database()

    distribution = conn.execute(
        "SELECT status, COUNT(*) FROM app_event GROUP BY status ORDER BY 2 DESC"
    ).fetchall()
    print("status 분포:", ", ".join(f"{s}={c:,}" for s, c in distribution))
    channel_count = conn.execute(
        "SELECT COUNT(DISTINCT channel) FROM app_event"
    ).fetchone()[0]
    print(f"channel 서로 다른 값: {channel_count}개")

    case_equality_plus_range(conn)
    case_both_equality(conn)
    case_prefix_only(conn)
    case_order_by(conn)
    conn.close()
    case_statistics_dependency()


if __name__ == "__main__":
    main()
