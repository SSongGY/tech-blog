"""ON CONFLICT 다섯 가지가 어디까지 되돌리는지 직접 확인한다.

핵심은 '어디까지 되돌아가는가'다. 되돌리는 범위가 좁은 것부터 넓은 것까지
FAIL < ABORT < ROLLBACK 순이고, IGNORE 는 되돌리는 대신 그 행만 건너뛰며,
REPLACE 는 되돌리는 대신 걸리적거리는 기존 행을 지운다.
"""

from __future__ import annotations

import sqlite3

from dbshow import print_dataset, print_environment

RULE = "=" * 64

SCHEMA = """
CREATE TABLE inventory (
    sku  TEXT    PRIMARY KEY,
    qty  INTEGER NOT NULL,
    note TEXT    DEFAULT '정상'
);
INSERT INTO inventory (sku, qty, note) VALUES
    ('A-100', 10, '정상'),
    ('A-200', 20, '재고조사 대상');
"""

# 세 번째 행 A-100 이 PRIMARY KEY 를 어긴다. 앞 두 행과 뒤 한 행의 운명이
# 해결 방식마다 갈리는 것이 이 예제의 전부다.
BATCH = """
INSERT {clause} INTO inventory (sku, qty, note) VALUES
    ('B-010', 1, '신규'),
    ('B-020', 2, '신규'),
    ('A-100', 99, '중복'),
    ('B-030', 3, '신규')
"""


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.isolation_level = None  # BEGIN/COMMIT 을 직접 적어야 경계가 보인다
    conn.executescript(SCHEMA)
    return conn


def snapshot(conn: sqlite3.Connection) -> list[str]:
    return [sku for (sku,) in conn.execute("SELECT sku FROM inventory ORDER BY sku")]


def run_batch(clause: str) -> None:
    """트랜잭션을 열고, 안전한 행 하나를 넣은 뒤, 충돌이 든 4행을 넣는다."""
    conn = build_database()
    conn.execute("BEGIN")
    conn.execute("INSERT INTO inventory (sku, qty) VALUES ('T-001', 7)")

    label = clause or "(생략 = OR ABORT)"
    try:
        conn.execute(BATCH.format(clause=clause))
        outcome = "에러 없음"
    except sqlite3.IntegrityError as exc:
        outcome = f"{type(exc).__name__}: {exc}"

    in_tx = conn.in_transaction
    rows = snapshot(conn)
    existing = conn.execute("SELECT qty FROM inventory WHERE sku = 'A-100'").fetchone()
    if in_tx:
        conn.execute("COMMIT")

    print(f"[{label}]")
    print(f"  결과        {outcome}")
    print(f"  트랜잭션    {'열려 있음' if in_tx else '끝났음 (되감김)'}")
    print(f"  남은 sku    {rows}")
    print(f"  기존 A-100  qty={existing[0]}  (원래 10, 배치가 넣으려던 값은 99)")
    print(f"  선행 T-001  {'남음' if 'T-001' in rows else '사라짐'}")
    print(f"  앞선 B-010  {'남음' if 'B-010' in rows else '사라짐'}")
    print(f"  뒤따른 B-030 {'남음' if 'B-030' in rows else '사라짐'}")
    print()
    conn.close()


def show_replace_side_effects() -> None:
    """REPLACE 는 되돌리지 않는다. 기존 행을 지우고 그 자리에 새 행을 넣는다."""
    conn = build_database()
    before = conn.execute(
        "SELECT rowid, sku, qty, note FROM inventory WHERE sku = 'A-200'"
    ).fetchone()
    # note 를 빼고 넣으면 기존 값이 이어지는 게 아니라 DEFAULT 가 들어간다
    conn.execute("INSERT OR REPLACE INTO inventory (sku, qty) VALUES ('A-200', 55)")
    after = conn.execute(
        "SELECT rowid, sku, qty, note FROM inventory WHERE sku = 'A-200'"
    ).fetchone()

    print(f"[REPLACE 전]  rowid={before[0]}  qty={before[2]}  note={before[3]!r}")
    print(f"[REPLACE 후]  rowid={after[0]}  qty={after[2]}  note={after[3]!r}")
    print()
    conn.close()


def show_not_null_handling() -> None:
    """REPLACE 가 NOT NULL 을 만나면 DEFAULT 유무로 갈린다."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE with_default (
            id   INTEGER PRIMARY KEY,
            name TEXT NOT NULL DEFAULT '이름없음'
        );
        CREATE TABLE no_default (
            id   INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );
        """
    )
    conn.execute("INSERT OR REPLACE INTO with_default (id, name) VALUES (1, NULL)")
    filled = conn.execute("SELECT name FROM with_default WHERE id = 1").fetchone()[0]
    print(f"[NOT NULL + DEFAULT]  REPLACE 로 NULL 을 넣으면 → {filled!r}")

    try:
        conn.execute("INSERT OR REPLACE INTO no_default (id, name) VALUES (1, NULL)")
        print("[NOT NULL, DEFAULT 없음]  통과함")
    except sqlite3.IntegrityError as exc:
        print(f"[NOT NULL, DEFAULT 없음]  {type(exc).__name__}: {exc}")
    print()
    conn.close()


def show_clause_precedence() -> None:
    """표 정의에 적은 ON CONFLICT 와 문장에 적은 OR 중 무엇이 이기는지."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE tagged (
            code TEXT PRIMARY KEY ON CONFLICT IGNORE,
            memo TEXT
        );
        INSERT INTO tagged VALUES ('X', '처음');
        """
    )
    conn.execute("INSERT INTO tagged VALUES ('X', '표 정의가 정한 IGNORE')")
    kept = conn.execute("SELECT memo FROM tagged WHERE code = 'X'").fetchone()[0]
    print(f"[표 정의 IGNORE, 문장은 그냥 INSERT]  남은 memo → {kept!r}")

    conn.execute("INSERT OR REPLACE INTO tagged VALUES ('X', '문장의 OR REPLACE')")
    kept = conn.execute("SELECT memo FROM tagged WHERE code = 'X'").fetchone()[0]
    print(f"[문장에 OR REPLACE 를 적으면]        남은 memo → {kept!r}")
    print()
    conn.close()


def show_ignore_covers_not_null() -> None:
    """IGNORE 는 UNIQUE 뿐 아니라 NOT NULL·CHECK 위반 행도 건너뛴다."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE score (
            id    INTEGER PRIMARY KEY,
            point INTEGER NOT NULL CHECK (point >= 0)
        );
        """
    )
    conn.execute(
        "INSERT OR IGNORE INTO score (id, point) VALUES (1, 10), (2, NULL), "
        "(3, -5), (4, 40)"
    )
    rows = conn.execute("SELECT id, point FROM score ORDER BY id").fetchall()
    print(f"[OR IGNORE 로 4행 투입 — NULL 1행, CHECK 위반 1행 포함]  남은 행 → {rows}")
    print()
    conn.close()


def main() -> None:
    print_environment()
    print_dataset(build_database())

    print(RULE)
    print("1. 같은 배치를 다섯 가지 해결 방식으로 — 무엇이 남는가")
    print(RULE)
    for clause in ("", "OR ROLLBACK", "OR ABORT", "OR FAIL", "OR IGNORE", "OR REPLACE"):
        run_batch(clause)

    print(RULE)
    print("2. REPLACE 는 고치는 것이 아니라 지우고 다시 넣는다")
    print(RULE)
    show_replace_side_effects()

    print(RULE)
    print("3. REPLACE 와 NOT NULL")
    print(RULE)
    show_not_null_handling()

    print(RULE)
    print("4. 표 정의의 ON CONFLICT 와 문장의 OR — 누가 이기는가")
    print(RULE)
    show_clause_precedence()

    print(RULE)
    print("5. IGNORE 가 건너뛰는 범위")
    print(RULE)
    show_ignore_covers_not_null()


if __name__ == "__main__":
    main()
