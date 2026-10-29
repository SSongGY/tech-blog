"""DELETE 로 지운 공간이 어디로 가는지, VACUUM 이 그것을 어떻게 돌려주는지 본다.

실행:
    python vacuum_demo.py

파일 크기·페이지 수·freelist 길이를 단계마다 같이 찍는다. 세 숫자를 나란히
놓아야 "행은 줄었는데 파일은 그대로"가 어디서 생기는지가 보인다.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
from pathlib import Path

from dbshow import print_dataset, print_environment

WORK_DIR = Path(__file__).with_name("_work")
ROW_COUNT = 20_000
MEMO_PADDING = "x" * 200  # 한 행을 200바이트 넘게 만들어야 페이지가 눈에 띄게 늘어난다

SCHEMA = """
CREATE TABLE order_log (
    id        INTEGER PRIMARY KEY,
    placed_on TEXT    NOT NULL,
    status    TEXT    NOT NULL,
    memo      TEXT
);
CREATE INDEX idx_order_log_status ON order_log(status);
"""


def build_database(path: Path, *, auto_vacuum: int = 0) -> sqlite3.Connection:
    """빈 파일에 auto_vacuum 을 먼저 정하고 표를 만든다.

    auto_vacuum 은 표가 하나라도 생긴 뒤에는 PRAGMA 만으로 바뀌지 않는다.
    그래서 connect 직후, executescript 전에 건다.
    """
    conn = sqlite3.connect(path)
    conn.execute(f"PRAGMA auto_vacuum = {auto_vacuum}")
    conn.executescript(SCHEMA)
    conn.executemany(
        "INSERT INTO order_log (id, placed_on, status, memo) VALUES (?, ?, ?, ?)",
        [
            (i, f"2026-10-{i % 28 + 1:02d}", "paid" if i % 3 else "cancelled",
             f"{i}번 주문 {MEMO_PADDING}")
            for i in range(1, ROW_COUNT + 1)
        ],
    )
    conn.commit()
    return conn


def measure(conn: sqlite3.Connection, path: Path) -> dict[str, int]:
    def pragma(name: str) -> int:
        return conn.execute(f"PRAGMA {name}").fetchone()[0]

    return {
        "rows": conn.execute("SELECT COUNT(*) FROM order_log").fetchone()[0],
        "page_size": pragma("page_size"),
        "page_count": pragma("page_count"),
        "freelist_count": pragma("freelist_count"),
        "file_bytes": os.path.getsize(path),
    }


def report(label: str, stat: dict[str, int]) -> None:
    print(
        f"  {label:<26s}"
        f"행 {stat['rows']:>6,}"
        f" · 페이지 {stat['page_count']:>5,}"
        f" · freelist {stat['freelist_count']:>5,}"
        f" · 파일 {stat['file_bytes']:>9,} 바이트"
    )


def section(title: str) -> None:
    print()
    print("=" * 64)
    print(title)
    print("=" * 64)


def demo_default() -> None:
    """auto_vacuum 이 꺼진 기본 설정. 지워도 파일이 안 줄어든다."""
    section("1. auto_vacuum = NONE (기본값)")
    path = WORK_DIR / "shop.db"
    conn = build_database(path)

    print_dataset(conn)
    print(f"  PRAGMA auto_vacuum → {conn.execute('PRAGMA auto_vacuum').fetchone()[0]}")
    print()
    report("적재 직후", measure(conn, path))

    conn.execute("DELETE FROM order_log WHERE id % 10 != 0")
    conn.commit()
    report("90% 삭제 후", measure(conn, path))

    # 빈 페이지가 정말 재사용되는지 본다. 파일이 안 늘면 재사용된 것이다.
    conn.executemany(
        "INSERT INTO order_log (placed_on, status, memo) VALUES (?, ?, ?)",
        [(f"2026-11-{i % 28 + 1:02d}", "paid", f"재입력 {MEMO_PADDING}")
         for i in range(5_000)],
    )
    conn.commit()
    report("5,000행 다시 넣은 뒤", measure(conn, path))

    conn.execute("VACUUM")
    report("VACUUM 후", measure(conn, path))
    conn.close()


def demo_auto_full() -> None:
    section("2. auto_vacuum = FULL")
    path = WORK_DIR / "shop_full.db"
    conn = build_database(path, auto_vacuum=1)

    print(f"  PRAGMA auto_vacuum → {conn.execute('PRAGMA auto_vacuum').fetchone()[0]}")
    report("적재 직후", measure(conn, path))

    conn.execute("DELETE FROM order_log WHERE id % 10 != 0")
    conn.commit()
    report("90% 삭제 후", measure(conn, path))
    conn.close()


def demo_auto_incremental() -> None:
    section("3. auto_vacuum = INCREMENTAL")
    path = WORK_DIR / "shop_incr.db"
    conn = build_database(path, auto_vacuum=2)

    print(f"  PRAGMA auto_vacuum → {conn.execute('PRAGMA auto_vacuum').fetchone()[0]}")
    report("적재 직후", measure(conn, path))

    conn.execute("DELETE FROM order_log WHERE id % 10 != 0")
    conn.commit()
    report("90% 삭제 후", measure(conn, path))

    # PRAGMA incremental_vacuum 은 페이지를 하나 돌려줄 때마다 결과 행을 하나 낸다.
    # execute() 는 첫 행에서 멈추므로 여기서는 한 페이지만 준다.
    conn.execute("PRAGMA incremental_vacuum(100)")
    conn.commit()
    report("execute 만 (100 요청)", measure(conn, path))

    rows = conn.execute("PRAGMA incremental_vacuum(100)").fetchall()
    conn.commit()
    report("fetchall (100 요청)", measure(conn, path))
    print(f"      ↑ 받은 결과 행 {len(rows)}개 — 돌려준 페이지 수와 같다")

    rows = conn.execute("PRAGMA incremental_vacuum").fetchall()  # 인자 없으면 끝까지
    conn.commit()
    report("fetchall (전부)", measure(conn, path))
    print(f"      ↑ 받은 결과 행 {len(rows)}개")
    conn.close()


def demo_mode_switch() -> None:
    """표가 생긴 뒤에 auto_vacuum 을 바꾸려 하면 어떻게 되는지."""
    section("4. 이미 만든 DB 의 auto_vacuum 바꾸기")
    path = WORK_DIR / "shop_switch.db"
    conn = build_database(path)

    print(f"  바꾸기 전               → {conn.execute('PRAGMA auto_vacuum').fetchone()[0]}")
    conn.execute("PRAGMA auto_vacuum = FULL")
    print(f"  PRAGMA 만 건 직후        → {conn.execute('PRAGMA auto_vacuum').fetchone()[0]}")
    conn.execute("VACUUM")
    print(f"  그 상태로 VACUUM 한 뒤   → {conn.execute('PRAGMA auto_vacuum').fetchone()[0]}")
    conn.close()


def demo_vacuum_into() -> None:
    """원본을 건드리지 않고 정리된 사본을 만든다."""
    section("5. VACUUM INTO — 원본을 열어 둔 채 사본 만들기")
    path = WORK_DIR / "shop_into.db"
    copy_path = WORK_DIR / "shop_into_compact.db"
    conn = build_database(path)
    conn.execute("DELETE FROM order_log WHERE id % 10 != 0")
    conn.commit()
    report("원본 (90% 삭제 후)", measure(conn, path))

    conn.execute("VACUUM INTO ?", (str(copy_path),))
    report("원본 — VACUUM INTO 뒤", measure(conn, path))

    copy_conn = sqlite3.connect(copy_path)
    report("사본", measure(copy_conn, copy_path))
    copy_conn.close()
    conn.close()


def main() -> None:
    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)
    WORK_DIR.mkdir()

    print_environment()
    demo_default()
    demo_auto_full()
    demo_auto_incremental()
    demo_mode_switch()
    demo_vacuum_into()
    print()


if __name__ == "__main__":
    main()
