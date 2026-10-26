"""ATTACH 로 여러 데이터베이스 파일을 한 연결에 붙여 본다.

출력 맨 앞에 두 파일의 표 정의와 데이터를 먼저 찍는다. 그래야 그 아래
조인 결과가 왜 그 행인지 따라 읽힌다.
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path

from dbshow import RULE, print_environment, print_table

SALES_SCHEMA = """
CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    amount      INTEGER NOT NULL,
    ordered_on  TEXT    NOT NULL
);
INSERT INTO orders VALUES
    (101, 1, 48000, '2026-10-02'),
    (102, 2, 15000, '2026-10-11'),
    (103, 1,  9000, '2026-10-20');
"""

ARCHIVE_SCHEMA = """
CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    amount      INTEGER NOT NULL,
    ordered_on  TEXT    NOT NULL
);
INSERT INTO orders VALUES
    (7,  1, 32000, '2024-03-15'),
    (8,  3,  5000, '2024-07-01');

CREATE TABLE customer (
    customer_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL
);
INSERT INTO customer VALUES (1, '김하늘'), (2, '박도윤'), (3, '이서준');
"""


def build_file(path: Path, schema: str) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(schema)
    conn.commit()
    conn.close()


def show_file(path: Path, tables: list[str]) -> None:
    conn = sqlite3.connect(path)
    print(f"--- 파일 {path.name} ---")
    for table in tables:
        print_table(conn, table)
    conn.close()


def section(title: str) -> None:
    print(RULE)
    print(title)
    print(RULE)


def run_rows(conn: sqlite3.Connection, sql: str) -> None:
    print(f"sql> {' '.join(sql.split())}")
    for row in conn.execute(sql):
        print(f"     {row}")
    print()


def main() -> None:
    print_environment()

    with tempfile.TemporaryDirectory() as workdir:
        work = Path(workdir)
        sales_path = work / "sales.db"
        archive_path = work / "archive.db"
        build_file(sales_path, SALES_SCHEMA)
        build_file(archive_path, ARCHIVE_SCHEMA)

        section("스키마와 데이터 — 아래 질의는 전부 이 두 파일을 대상으로 한다")
        show_file(sales_path, ["orders"])
        show_file(archive_path, ["orders", "customer"])

        conn = sqlite3.connect(sales_path)
        conn.isolation_level = None  # BEGIN/COMMIT 을 SQL 로 직접 적는다
        try:
            demo(conn, archive_path, work)
        finally:
            # 닫지 않으면 임시 폴더를 지울 때 Windows 에서 파일이 잠겨 있다
            conn.close()


def demo(conn: sqlite3.Connection, archive_path: Path, work: Path) -> None:
        section("1. ATTACH — 붙이고 나면 database_list 에 한 줄이 는다")
        conn.execute("ATTACH DATABASE ? AS archive", (str(archive_path),))
        for seq, name, _file in conn.execute("PRAGMA database_list"):
            print(f"  seq={seq}  schema={name}")
        print()

        section("2. 파일을 건너뛰는 조인과 UNION")
        run_rows(
            conn,
            """
            SELECT o.order_id, c.name, o.amount
              FROM main.orders AS o
              JOIN archive.customer AS c USING (customer_id)
             ORDER BY o.order_id
            """,
        )
        run_rows(
            conn,
            """
            SELECT customer_id, SUM(amount) AS total
              FROM (SELECT customer_id, amount FROM main.orders
                    UNION ALL
                    SELECT customer_id, amount FROM archive.orders)
             GROUP BY customer_id
             ORDER BY customer_id
            """,
        )

        section("3. 같은 이름의 표가 양쪽에 있을 때 — 접두사를 빼면 어디로 가나")
        run_rows(conn, "SELECT COUNT(*) FROM orders")
        run_rows(conn, "SELECT COUNT(*) FROM main.orders")
        run_rows(conn, "SELECT COUNT(*) FROM archive.orders")

        section("4. 트랜잭션은 두 파일에 걸친다 — ROLLBACK 이 양쪽을 되돌린다")
        conn.execute("BEGIN")
        conn.execute("INSERT INTO main.orders VALUES (104, 2, 1, '2026-10-26')")
        conn.execute("INSERT INTO archive.orders VALUES (9, 3, 1, '2024-01-01')")
        print("  BEGIN 뒤 INSERT 2건 (파일 하나씩)")
        run_rows(conn, "SELECT (SELECT COUNT(*) FROM main.orders), "
                       "(SELECT COUNT(*) FROM archive.orders)")
        conn.execute("ROLLBACK")
        print("  ROLLBACK 수행")
        run_rows(conn, "SELECT (SELECT COUNT(*) FROM main.orders), "
                       "(SELECT COUNT(*) FROM archive.orders)")

        section("5. 트랜잭션 안에서 DETACH 를 하면 ROLLBACK 이 되돌려 주는가")
        conn.execute("BEGIN")
        try:
            conn.execute("DETACH DATABASE archive")
            print("  BEGIN 안에서 DETACH 수행 — 에러 없음")
        except sqlite3.OperationalError as exc:
            print(f"  OperationalError: {exc}")
        conn.execute("ROLLBACK")
        names = [name for _s, name, _f in conn.execute("PRAGMA database_list")]
        print(f"  ROLLBACK 뒤 database_list = {names}")
        conn.execute("ATTACH DATABASE ? AS archive", (str(archive_path),))
        names = [name for _s, name, _f in conn.execute("PRAGMA database_list")]
        print(f"  다시 ATTACH 한 뒤      = {names}")
        print()

        section("6. 저널 모드별 다중 파일 원자성 — 값만 찍는다")
        for schema in ("main", "archive"):
            mode = conn.execute(f"PRAGMA {schema}.journal_mode").fetchone()[0]
            print(f"  {schema:8s} journal_mode = {mode}")
        conn.execute("PRAGMA main.journal_mode = WAL")
        mode = conn.execute("PRAGMA main.journal_mode").fetchone()[0]
        print(f"  main 을 WAL 로 바꾼 뒤 = {mode}")
        print()

        section("7. 몇 개까지 붙일 수 있나 — 에러가 날 때까지 붙여 본다")
        attached = 1  # archive
        try:
            for i in range(200):
                conn.execute(f"ATTACH DATABASE ':memory:' AS mem{i}")
                attached += 1
        except sqlite3.OperationalError as exc:
            print(f"  {attached}개까지 붙은 뒤 OperationalError: {exc}")
        print(f"  database_list 행 수 = "
              f"{len(conn.execute('PRAGMA database_list').fetchall())}")
        try:
            conn.execute("VACUUM main INTO ?", (str(work / "full.db"),))
        except sqlite3.OperationalError as exc:
            print(f"  이 상태에서 VACUUM INTO → OperationalError: {exc}")
        for i in range(attached - 1):
            conn.execute(f"DETACH DATABASE mem{i}")
        print(f"  mem* 를 전부 DETACH 한 뒤 행 수 = "
              f"{len(conn.execute('PRAGMA database_list').fetchall())}")
        print()

        section("8. VACUUM INTO — 붙이지 않고 파일 하나를 통째로 복제한다")
        backup_path = work / "backup.db"
        conn.execute("VACUUM main INTO ?", (str(backup_path),))
        print(f"  {backup_path.name} 생성, {os.path.getsize(backup_path)} 바이트")
        copy = sqlite3.connect(backup_path)
        print(f"  복제본 orders 행 수 = "
              f"{copy.execute('SELECT COUNT(*) FROM orders').fetchone()[0]}")
        copy.close()


if __name__ == "__main__":
    main()
