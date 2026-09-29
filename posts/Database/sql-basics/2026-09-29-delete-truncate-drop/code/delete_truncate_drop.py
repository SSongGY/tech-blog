"""DELETE 와 DROP 이 무엇을 지우고, 트랜잭션 안에서 되돌릴 수 있는지, 파일 크기가 줄어드는지 본다.

SQLite 에는 TRUNCATE 문이 없다. 대신 WHERE 없는 DELETE 에 truncate optimization 이 걸린다.
파일 크기를 재려면 메모리 DB 가 아니라 실제 파일이어야 하므로 임시 폴더에 DB 를 만든다.
"""

import os
import sqlite3
import tempfile

from dbshow import print_dataset, print_environment

SCHEMA = """
CREATE TABLE product (
    product_id  INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    price       INTEGER NOT NULL
);
INSERT INTO product (product_id, name, price) VALUES
    (1, '연필', 500),
    (2, '공책', 1500),
    (3, '지우개', 300),
    (4, '볼펜', 1000);
"""

BULK_ROWS = 20000


def show(conn, sql):
    print(f"   {sql}")
    for row in conn.execute(sql).fetchall():
        print("   " + " | ".join(str(v) for v in row))
    print()


def table_names(conn):
    rows = conn.execute(
        "SELECT name FROM sqlite_schema WHERE type = 'table' ORDER BY name"
    ).fetchall()
    return [name for (name,) in rows]


def storage(conn, path, label):
    page_count = conn.execute("PRAGMA page_count").fetchone()[0]
    freelist = conn.execute("PRAGMA freelist_count").fetchone()[0]
    size_kb = os.path.getsize(path) // 1024
    # 한글 라벨은 폭이 두 칸이라 앞에 두면 줄이 어긋난다. 숫자를 앞에 맞춰 두고 라벨을 뒤에 붙인다
    print(f"   파일 {size_kb:>5} KB · 전체 페이지 {page_count:>4} · 빈 페이지 {freelist:>4}  ← {label}")


def fill_bulk(conn):
    conn.execute("CREATE TABLE access_log (log_id INTEGER PRIMARY KEY, body TEXT NOT NULL)")
    # 자동 커밋 상태라 BEGIN 없이 넣으면 행마다 커밋해 수십 초가 걸린다
    conn.execute("BEGIN")
    # body 를 200자로 채워 페이지 수가 눈에 띄게 늘게 한다
    conn.executemany(
        "INSERT INTO access_log (body) VALUES (?)",
        ((f"{i:06d}" + "x" * 194,) for i in range(BULK_ROWS)),
    )
    conn.execute("COMMIT")


def main():
    print_environment()
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.executescript(SCHEMA)
    print_dataset(conn)

    print("-- 1. DELETE ... WHERE — 고른 행만 지우고, ROLLBACK 으로 되돌린다")
    conn.execute("BEGIN")
    changed = conn.execute("DELETE FROM product WHERE price < 1000").rowcount
    print(f"   DELETE FROM product WHERE price < 1000  → 지운 행 {changed}")
    show(conn, "SELECT product_id, name FROM product ORDER BY product_id")
    conn.execute("ROLLBACK")
    print("   ROLLBACK 뒤")
    show(conn, "SELECT COUNT(*) FROM product")

    print("-- 2. WHERE 없는 DELETE — 행은 전부 사라지고 표는 남는다")
    conn.execute("BEGIN")
    changed = conn.execute("DELETE FROM product").rowcount
    print(f"   DELETE FROM product  → 지운 행 {changed}")
    print(f"   남은 표: {table_names(conn)}")
    show(conn, "SELECT COUNT(*) FROM product")
    conn.execute("ROLLBACK")
    print("   ROLLBACK 뒤")
    show(conn, "SELECT COUNT(*) FROM product")

    print("-- 3. DROP TABLE — 표 정의까지 사라진다. SQLite 에서는 이것도 ROLLBACK 된다")
    conn.execute("BEGIN")
    conn.execute("DROP TABLE product")
    print("   DROP TABLE product")
    print(f"   남은 표: {table_names(conn)}")
    try:
        conn.execute("SELECT COUNT(*) FROM product")
    except sqlite3.OperationalError as exc:
        print(f"   SELECT COUNT(*) FROM product  → 에러: {exc}")
    conn.execute("ROLLBACK")
    print("   ROLLBACK 뒤")
    print(f"   남은 표: {table_names(conn)}")
    show(conn, "SELECT COUNT(*) FROM product")

    print("-- 4. TRUNCATE — SQLite 에는 이 문장이 없다")
    try:
        conn.execute("TRUNCATE TABLE product")
    except sqlite3.OperationalError as exc:
        print(f"   TRUNCATE TABLE product  → 에러: {exc}")
    print()
    conn.close()

    with tempfile.TemporaryDirectory() as work_dir:
        print("-- 5. 지워도 파일은 줄지 않는다 — 빈 페이지로 남고 VACUUM 이 돌려준다")
        path = os.path.join(work_dir, "shop.db")
        conn = sqlite3.connect(path, isolation_level=None)
        fill_bulk(conn)
        storage(conn, path, f"{BULK_ROWS}행 넣은 뒤")
        conn.execute("DELETE FROM access_log")
        storage(conn, path, "DELETE (WHERE 없음) 뒤")
        conn.execute("DROP TABLE access_log")
        storage(conn, path, "DROP TABLE 뒤")
        conn.execute("BEGIN")
        try:
            conn.execute("VACUUM")
        except sqlite3.OperationalError as exc:
            print(f"   BEGIN 안에서 VACUUM  → 에러: {exc}")
        conn.execute("ROLLBACK")
        conn.execute("VACUUM")
        storage(conn, path, "VACUUM 뒤")
        conn.close()
        print()

        print("-- 6. auto_vacuum = FULL 이면 커밋 시점에 파일이 줄어든다")
        path = os.path.join(work_dir, "shop_auto.db")
        conn = sqlite3.connect(path, isolation_level=None)
        # auto_vacuum 은 표를 만들기 전에 정해야 한다
        conn.execute("PRAGMA auto_vacuum = FULL")
        fill_bulk(conn)
        storage(conn, path, f"{BULK_ROWS}행 넣은 뒤")
        conn.execute("DELETE FROM access_log")
        storage(conn, path, "DELETE (WHERE 없음) 뒤")
        conn.close()


if __name__ == "__main__":
    main()
