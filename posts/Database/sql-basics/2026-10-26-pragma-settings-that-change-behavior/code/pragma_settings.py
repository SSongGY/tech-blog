"""PRAGMA 가 무엇을 바꾸고, 어디까지 남는지를 직접 확인한다.

세 갈래로 나뉜다.
  (1) 연결에만 사는 것   — foreign_keys, synchronous, cache_size
  (2) 파일에 남는 것     — journal_mode, user_version, page_size
  (3) 읽기 전용 조회용   — table_info, integrity_check, freelist_count
"""

from __future__ import annotations

import os
import sqlite3
import tempfile

from dbshow import print_dataset, print_environment

SCHEMA = """
CREATE TABLE author (
    author_id INTEGER PRIMARY KEY,
    name      TEXT NOT NULL
);
CREATE TABLE book (
    book_id   INTEGER PRIMARY KEY,
    title     TEXT NOT NULL,
    author_id INTEGER REFERENCES author(author_id)
);
INSERT INTO author VALUES (1, '김작가'), (2, '이작가');
INSERT INTO book VALUES (10, '첫 책', 1), (11, '두 번째 책', 2);
"""


def build_database(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def scalar(conn: sqlite3.Connection, sql: str):
    row = conn.execute(sql).fetchone()
    return None if row is None else row[0]


def section(title: str) -> None:
    print()
    print(title)


def main() -> None:
    workdir = tempfile.mkdtemp(prefix="pragma_demo_")
    db_path = os.path.join(workdir, "library.db")

    conn = build_database(db_path)
    print_environment()
    print_dataset(conn)

    section("1. PRAGMA 의 두 가지 꼴 — 묻기와 바꾸기")
    print(f"  PRAGMA foreign_keys;            -> {scalar(conn, 'PRAGMA foreign_keys')}")
    conn.execute("PRAGMA foreign_keys = ON")
    print(f"  PRAGMA foreign_keys = ON;  뒤   -> {scalar(conn, 'PRAGMA foreign_keys')}")
    # ON/OFF/1/0/true/false 전부 받는다. 값을 생략하면 묻는 꼴이 된다.
    conn.execute("PRAGMA foreign_keys = 0")
    print(f"  PRAGMA foreign_keys = 0;   뒤   -> {scalar(conn, 'PRAGMA foreign_keys')}")

    section("2. foreign_keys — 끄면 없는 저자를 가리켜도 들어간다")
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("INSERT INTO book VALUES (20, '유령 책', 999)")
    conn.commit()
    print(f"  OFF 에서 author_id=999 입력    -> 성공, 현재 book 행 수 {scalar(conn, 'SELECT count(*) FROM book')}")
    conn.execute("DELETE FROM book WHERE book_id = 20")
    conn.commit()

    conn.execute("PRAGMA foreign_keys = ON")
    try:
        conn.execute("INSERT INTO book VALUES (21, '유령 책', 999)")
    except sqlite3.IntegrityError as exc:
        print(f"  ON 에서 같은 입력              -> IntegrityError: {exc}")
    # 실패한 INSERT 도 파이썬이 연 암묵 트랜잭션은 그대로 둔다. 닫지 않으면
    # 바로 아래 PRAGMA 가 조용히 무시된다 (5절).
    conn.rollback()

    print("  이미 들어간 위반 행은 켜도 사라지지 않는다. 확인은 foreign_key_check 로 한다.")
    conn.execute("PRAGMA foreign_keys = OFF")
    print(f"  (rollback 뒤라 OFF 가 먹는다)  -> foreign_keys = {scalar(conn, 'PRAGMA foreign_keys')}")
    conn.execute("INSERT INTO book VALUES (22, '먼저 들어간 유령', 777)")
    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON")
    print(f"  PRAGMA foreign_key_check;      -> {conn.execute('PRAGMA foreign_key_check').fetchall()}")
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("DELETE FROM book WHERE book_id = 22")
    conn.commit()

    section("3. 어디까지 남는가 — 연결을 끊고 다시 붙여 본다")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA synchronous = OFF")
    conn.execute("PRAGMA cache_size = -8000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA user_version = 7")
    before = {
        "foreign_keys": scalar(conn, "PRAGMA foreign_keys"),
        "synchronous": scalar(conn, "PRAGMA synchronous"),
        "cache_size": scalar(conn, "PRAGMA cache_size"),
        "journal_mode": scalar(conn, "PRAGMA journal_mode"),
        "user_version": scalar(conn, "PRAGMA user_version"),
    }
    conn.close()

    conn = sqlite3.connect(db_path)
    after = {name: scalar(conn, f"PRAGMA {name}") for name in before}
    print(f"  {'PRAGMA':14} {'끊기 전':>10} {'다시 붙은 뒤':>14}   남는가")
    for name, old in before.items():
        kept = "파일에 남는다" if str(old) == str(after[name]) else "연결과 함께 사라진다"
        print(f"  {name:14} {str(old):>10} {str(after[name]):>14}   {kept}")

    section("4. cache_size 의 부호 — 양수는 페이지 수, 음수는 KiB")
    page_size = scalar(conn, "PRAGMA page_size")
    print(f"  page_size                      -> {page_size}")
    for value in (-2000, 2000, -8000):
        conn.execute(f"PRAGMA cache_size = {value}")
        got = scalar(conn, "PRAGMA cache_size")
        byte = -got * 1024 if got < 0 else got * page_size
        print(f"  cache_size = {value:<6}            -> {got:>6}  최대 {byte:>9,} 바이트")

    section("5. 트랜잭션 안에서는 안 먹는 PRAGMA 가 있다")
    conn.execute("PRAGMA journal_mode = DELETE")
    conn.execute("BEGIN")
    conn.execute("INSERT INTO author VALUES (3, '박작가')")
    in_tx = scalar(conn, "PRAGMA journal_mode = WAL")
    print(f"  트랜잭션 안에서 journal_mode=WAL -> {in_tx}  (바뀌지 않는다)")
    conn.execute("PRAGMA foreign_keys = ON")
    print(f"  트랜잭션 안에서 foreign_keys=ON  -> {scalar(conn, 'PRAGMA foreign_keys')}  (조용히 무시된다)")
    conn.rollback()
    conn.execute("PRAGMA foreign_keys = ON")
    print(f"  트랜잭션을 끝낸 뒤 다시 ON       -> {scalar(conn, 'PRAGMA foreign_keys')}")

    section("6. 알 수 없는 이름을 줘도 에러가 아니다")
    rows = conn.execute("PRAGMA fooreign_keys").fetchall()
    print(f"  PRAGMA fooreign_keys;          -> {rows}  (오타가 조용히 묻힌다)")
    conn.execute("PRAGMA foreign_keys = maybe")
    print(f"  PRAGMA foreign_keys = maybe;   -> {scalar(conn, 'PRAGMA foreign_keys')}  (해석 못 한 값은 0 으로)")

    section("7. 조회용 PRAGMA — 표처럼 읽는다")
    conn.execute("PRAGMA foreign_keys = ON")
    print("  PRAGMA table_info(book);")
    for row in conn.execute("PRAGMA table_info(book)"):
        print(f"    {row}")
    print(f"  PRAGMA integrity_check;        -> {scalar(conn, 'PRAGMA integrity_check')}")
    print("  PRAGMA foreign_key_list(book);")
    for row in conn.execute("PRAGMA foreign_key_list(book)"):
        print(f"    {row}")
    print("  같은 값을 SELECT 로도 읽는다 — pragma_ 접두 함수")
    try:
        conn.execute("SELECT name FROM pragma_table_info('book') WHERE notnull = 1")
    except sqlite3.OperationalError as exc:
        # notnull 은 SQLite 의 연산자(expr NOTNULL)라서 컬럼 이름으로 그냥 못 쓴다.
        print(f"    WHERE notnull = 1          -> OperationalError: {exc}")
    rows = conn.execute(
        'SELECT name, type FROM pragma_table_info(\'book\') WHERE "notnull" = 1'
    ).fetchall()
    print(f'    WHERE "notnull" = 1        -> {rows}')

    conn.close()
    print()
    print(f"작업 폴더: {workdir}")


if __name__ == "__main__":
    main()
