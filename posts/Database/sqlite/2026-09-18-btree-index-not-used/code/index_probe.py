"""B-Tree 인덱스가 사용되는 조건과 사용되지 않는 조건을 SQLite로 재현한다.

같은 테이블·같은 인덱스에 대해 WHERE 절 표현만 바꿔가며
EXPLAIN QUERY PLAN 결과(SEARCH vs SCAN)와 실행 시간을 나란히 측정한다.

실행:
    python index_probe.py
"""

from __future__ import annotations

import random
import sqlite3
import sys
import time
from dataclasses import dataclass, field

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROW_COUNT = 200_000
RANDOM_SEED = 20260918
REPEAT_COUNT = 5  # 측정 편차를 줄이기 위해 여러 번 돌리고 최솟값을 쓴다

# status는 일부러 편향시킨다. 선택도가 인덱스 사용 여부를 가르는 걸 보이기 위함이다.
STATUS_WEIGHTS = {"active": 0.70, "dormant": 0.25, "locked": 0.05}
REGION_POOL = ("KR", "US", "JP", "DE", "SG")
BASE_EPOCH = 1_700_000_000

SCHEMA_SQL = """
CREATE TABLE app_user (
    user_id     INTEGER PRIMARY KEY,
    email       TEXT    NOT NULL,
    login_name  TEXT    NOT NULL,
    status      TEXT    NOT NULL,
    region_code TEXT    NOT NULL,
    created_at  INTEGER NOT NULL
);
CREATE INDEX ix_app_user_email             ON app_user(email);
CREATE INDEX ix_app_user_status_created_at ON app_user(status, created_at);
CREATE INDEX ix_app_user_region_code       ON app_user(region_code);
"""


@dataclass(frozen=True)
class ProbeCase:
    """WHERE 절 하나를 측정하기 위한 단위."""

    label: str
    where_clause: str
    params: tuple = ()
    pragmas: tuple[str, ...] = field(default=())


@dataclass
class ProbeResult:
    label: str
    where_clause: str
    plan: str
    matched_rows: int
    elapsed_ms: float

    @property
    def uses_index(self) -> bool:
        return "SEARCH" in self.plan


def build_database() -> sqlite3.Connection:
    """200,000행 테이블과 인덱스 3개를 만들고 통계를 수집한다."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA_SQL)

    rng = random.Random(RANDOM_SEED)
    statuses = list(STATUS_WEIGHTS)
    weights = list(STATUS_WEIGHTS.values())

    rows = [
        (
            user_id,
            f"user{user_id:06d}@example.com",
            f"login_{user_id:06d}",
            rng.choices(statuses, weights)[0],
            rng.choice(REGION_POOL),
            BASE_EPOCH + rng.randrange(365 * 24 * 3600),
        )
        for user_id in range(ROW_COUNT)
    ]
    conn.executemany("INSERT INTO app_user VALUES (?, ?, ?, ?, ?, ?)", rows)
    conn.execute("ANALYZE")  # 통계가 없으면 옵티마이저는 선택도를 추정할 수 없다
    conn.commit()
    return conn


def explain(conn: sqlite3.Connection, sql: str, params: tuple) -> str:
    plan_rows = conn.execute(f"EXPLAIN QUERY PLAN {sql}", params).fetchall()
    return " / ".join(row[3] for row in plan_rows)


def run_case(
    conn: sqlite3.Connection, case: ProbeCase, select_list: str = "user_id"
) -> ProbeResult:
    """select_list에 따라 커버링 인덱스 여부가 달라지므로 투영 목록도 인자로 받는다."""
    for pragma in case.pragmas:
        conn.execute(pragma)

    sql = f"SELECT {select_list} FROM app_user WHERE {case.where_clause}"
    plan = explain(conn, sql, case.params)

    best_ms = float("inf")
    matched_rows = 0
    for _ in range(REPEAT_COUNT):
        started = time.perf_counter()
        matched_rows = len(conn.execute(sql, case.params).fetchall())
        best_ms = min(best_ms, (time.perf_counter() - started) * 1000)

    for pragma in case.pragmas:  # 다음 케이스에 영향이 남지 않게 되돌린다
        conn.execute(pragma.replace("ON", "OFF"))

    return ProbeResult(case.label, case.where_clause, plan, matched_rows, best_ms)


def build_cases() -> list[ProbeCase]:
    target_email = "user123456@example.com"
    cutoff_epoch = BASE_EPOCH + 300 * 24 * 3600

    return [
        ProbeCase("① 단일 컬럼 등치", "email = ?", (target_email,)),
        ProbeCase("② 컬럼에 함수 적용", "lower(email) = ?", (target_email,)),
        ProbeCase("③ 컬럼에 연산 적용", "created_at + 0 > ?", (cutoff_epoch,)),
        ProbeCase("④ 접두 LIKE (기본)", "email LIKE 'user12345%'"),
        ProbeCase(
            "⑤ 접두 LIKE (case_sensitive_like=ON)",
            "email LIKE 'user12345%'",
            pragmas=("PRAGMA case_sensitive_like = ON",),
        ),
        ProbeCase("⑥ 선행 와일드카드 LIKE", "email LIKE '%12345@example.com'"),
        ProbeCase(
            "⑦ 복합 인덱스 선행 컬럼 사용",
            "status = ? AND created_at >= ?",
            ("locked", cutoff_epoch),
        ),
        ProbeCase("⑧ 복합 인덱스 선행 컬럼 생략", "created_at >= ?", (cutoff_epoch,)),
        ProbeCase("⑨ 선택도가 낮은 등치", "status = ?", ("active",)),
        ProbeCase("⑩ 부정 조건", "email <> ?", (target_email,)),
        ProbeCase(
            "⑪ OR 로 묶인 서로 다른 인덱스",
            "email = ? OR region_code = ?",
            (target_email, "SG"),
        ),
    ]


def print_report(results: list[ProbeResult]) -> None:
    print(f"{'케이스':<36} {'인덱스':<7} {'결과행':>8} {'시간(ms)':>10}  실행계획")
    print("-" * 118)
    for result in results:
        mark = "사용" if result.uses_index else "미사용"
        print(
            f"{result.label:<36} {mark:<7} {result.matched_rows:>8,} "
            f"{result.elapsed_ms:>10.2f}  {result.plan}"
        )


def main() -> None:
    print(f"SQLite {sqlite3.sqlite_version} · {ROW_COUNT:,}행 · 최소 {REPEAT_COUNT}회 측정\n")
    conn = build_database()
    cases = build_cases()

    print("[A] SELECT user_id — 인덱스만 읽어도 답이 나오는 커버링 상황")
    print_report([run_case(conn, case, "user_id") for case in cases])

    print("\n[B] SELECT login_name — 인덱스에 없는 컬럼이라 테이블을 다시 읽어야 하는 상황")
    print_report([run_case(conn, case, "login_name") for case in cases])

    print("\n[추가] lower(email)에 표현식 인덱스를 만들면 ②는 어떻게 되는가")
    conn.execute("CREATE INDEX ix_app_user_email_lower ON app_user(lower(email))")
    conn.execute("ANALYZE")
    after = run_case(
        conn,
        ProbeCase("② 재측정 (표현식 인덱스 추가 후)", "lower(email) = ?",
                  ("user123456@example.com",)),
    )
    print_report([after])
    conn.close()


if __name__ == "__main__":
    main()
