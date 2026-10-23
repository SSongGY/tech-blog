"""rowid 와 AUTOINCREMENT 가 다음 번호를 고르는 방식을 나란히 돌려 본다.

표 둘을 같은 데이터로 채운 뒤 똑같은 조작을 가하고, 그때마다 다음 번호가
무엇이 되는지와 sqlite_sequence 가 어떻게 바뀌는지를 찍는다.
"""

from __future__ import annotations

import sqlite3

from dbshow import print_dataset, print_environment

RULE = "=" * 64

SCHEMA = """
CREATE TABLE plain (
    id    INTEGER PRIMARY KEY,
    title TEXT NOT NULL
);

CREATE TABLE strict_seq (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL
);
"""

SEED = ["첫 글", "둘째 글", "셋째 글", "넷째 글"]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    for title in SEED:
        conn.execute("INSERT INTO plain (title) VALUES (?)", (title,))
        conn.execute("INSERT INTO strict_seq (title) VALUES (?)", (title,))
    conn.commit()
    return conn


def section(title: str) -> None:
    print(RULE)
    print(title)
    print(RULE)


def ids(conn: sqlite3.Connection, table: str) -> list[int]:
    return [row[0] for row in conn.execute(f"SELECT id FROM {table} ORDER BY id")]


def show_sequence(conn: sqlite3.Connection) -> None:
    rows = conn.execute("SELECT name, seq FROM sqlite_sequence ORDER BY name").fetchall()
    if not rows:
        print("  sqlite_sequence: (행 없음)")
        return
    for name, seq in rows:
        print(f"  sqlite_sequence: name={name!r}  seq={seq}")


def insert_both(conn: sqlite3.Connection, title: str) -> tuple[int, int]:
    cur = conn.execute("INSERT INTO plain (title) VALUES (?)", (title,))
    plain_id = cur.lastrowid
    cur = conn.execute("INSERT INTO strict_seq (title) VALUES (?)", (title,))
    strict_id = cur.lastrowid
    conn.commit()
    return plain_id, strict_id


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)

    section("0. 두 표가 sqlite_master 에 어떻게 적혀 있는가")
    for (sql,) in conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' ORDER BY name"
    ):
        print("  " + " ".join(sql.split()))
    print()
    show_sequence(conn)
    print()

    section("1. 마지막 행을 지우고 다시 넣는다")
    conn.execute("DELETE FROM plain WHERE id = 4")
    conn.execute("DELETE FROM strict_seq WHERE id = 4")
    conn.commit()
    print(f"  삭제 후  plain={ids(conn, 'plain')}  strict_seq={ids(conn, 'strict_seq')}")
    show_sequence(conn)
    plain_id, strict_id = insert_both(conn, "다섯째 글")
    print(f"  재삽입   plain 이 받은 번호={plain_id}  strict_seq 가 받은 번호={strict_id}")
    print(f"  현재     plain={ids(conn, 'plain')}  strict_seq={ids(conn, 'strict_seq')}")
    show_sequence(conn)
    print()

    section("2. 중간 행을 지우고 다시 넣는다")
    conn.execute("DELETE FROM plain WHERE id = 2")
    conn.execute("DELETE FROM strict_seq WHERE id = 2")
    conn.commit()
    print(f"  삭제 후  plain={ids(conn, 'plain')}  strict_seq={ids(conn, 'strict_seq')}")
    plain_id, strict_id = insert_both(conn, "여섯째 글")
    print(f"  재삽입   plain 이 받은 번호={plain_id}  strict_seq 가 받은 번호={strict_id}")
    print()

    section("3. 전체를 지우고 다시 넣는다")
    conn.execute("DELETE FROM plain")
    conn.execute("DELETE FROM strict_seq")
    conn.commit()
    print(f"  비운 뒤  plain={ids(conn, 'plain')}  strict_seq={ids(conn, 'strict_seq')}")
    show_sequence(conn)
    plain_id, strict_id = insert_both(conn, "비운 뒤 첫 글")
    print(f"  재삽입   plain 이 받은 번호={plain_id}  strict_seq 가 받은 번호={strict_id}")
    show_sequence(conn)
    print()

    section("4. 번호를 직접 지정해 넣으면 다음 번호가 어디서부터인가")
    conn.execute("INSERT INTO plain (id, title) VALUES (1000, '직접 지정')")
    conn.execute("INSERT INTO strict_seq (id, title) VALUES (1000, '직접 지정')")
    conn.commit()
    show_sequence(conn)
    plain_id, strict_id = insert_both(conn, "그다음 글")
    print(f"  자동 부여 plain={plain_id}  strict_seq={strict_id}")
    conn.execute("DELETE FROM plain WHERE id = 1000")
    conn.execute("DELETE FROM strict_seq WHERE id = 1000")
    conn.commit()
    print(f"  1000번 삭제 후 plain={ids(conn, 'plain')}  strict_seq={ids(conn, 'strict_seq')}")
    show_sequence(conn)
    plain_id, strict_id = insert_both(conn, "1000번 삭제 뒤 글")
    print(f"  자동 부여 plain={plain_id}  strict_seq={strict_id}")
    print()

    section("5. 상한에 닿으면 무엇이 일어나는가")
    limit = 9223372036854775807  # 64비트 부호 있는 정수의 최댓값
    probe = sqlite3.connect(":memory:")
    probe.executescript(SCHEMA)
    probe.execute("INSERT INTO plain (id, title) VALUES (?, '상한')", (limit,))
    probe.execute("INSERT INTO strict_seq (id, title) VALUES (?, '상한')", (limit,))
    probe.commit()
    for table in ("plain", "strict_seq"):
        try:
            cur = probe.execute(f"INSERT INTO {table} (title) VALUES ('한 칸 더')")
            print(f"  {table:11s} 성공 — 받은 번호={cur.lastrowid}")
        except sqlite3.Error as exc:
            print(f"  {table:11s} 실패 — {type(exc).__name__}: {exc}")
    probe.close()
    print()

    section("6. 번호 재사용이 바깥 참조를 어긋나게 하는 장면")
    conn.execute("DELETE FROM plain")
    conn.executescript(
        "INSERT INTO plain (title) VALUES ('운영 매뉴얼');"
        "INSERT INTO plain (title) VALUES ('장애 보고서');"
    )
    conn.commit()
    bookmark = conn.execute(
        "SELECT id FROM plain WHERE title = '장애 보고서'"
    ).fetchone()[0]
    print(f"  바깥 시스템이 적어 둔 번호: {bookmark}  ('장애 보고서')")
    conn.execute("DELETE FROM plain WHERE id = ?", (bookmark,))
    conn.execute("INSERT INTO plain (title) VALUES ('점심 메뉴')")
    conn.commit()
    now = conn.execute("SELECT title FROM plain WHERE id = ?", (bookmark,)).fetchone()
    print(f"  같은 번호로 다시 찾으면: {now[0]!r}")
    print()

    conn.close()

    section("7. 롤백된 트랜잭션이 가져간 번호는 돌아오는가")
    tx = sqlite3.connect(":memory:", isolation_level=None)
    tx.executescript(SCHEMA)
    tx.execute("INSERT INTO strict_seq (title) VALUES ('첫 글')")
    tx.execute("BEGIN")
    tx.execute("INSERT INTO strict_seq (title) VALUES ('롤백될 글')")
    before = tx.execute("SELECT seq FROM sqlite_sequence").fetchone()[0]
    print(f"  롤백 전 seq={before}")
    tx.execute("ROLLBACK")
    after = tx.execute("SELECT seq FROM sqlite_sequence").fetchone()[0]
    print(f"  롤백 후 seq={after}")
    cur = tx.execute("INSERT INTO strict_seq (title) VALUES ('다음 글')")
    print(f"  다음 삽입이 받은 번호={cur.lastrowid}")
    print(f"  남은 행={tx.execute('SELECT id, title FROM strict_seq').fetchall()}")
    tx.close()
    print()

    section("8. 기본키 타입을 INT 로 적으면")
    alt = sqlite3.connect(":memory:")
    alt.execute("CREATE TABLE loose (id INT PRIMARY KEY, title TEXT)")
    alt.execute("INSERT INTO loose (title) VALUES ('a')")
    alt.execute("INSERT INTO loose (title) VALUES ('b')")
    print("  id, typeof(id), rowid, title")
    for row in alt.execute("SELECT id, typeof(id), rowid, title FROM loose"):
        print(f"    {row}")
    try:
        alt.execute("CREATE TABLE u (id INT PRIMARY KEY AUTOINCREMENT, title TEXT)")
        print("  INT PRIMARY KEY AUTOINCREMENT — 생성됨")
    except sqlite3.Error as exc:
        print(f"  INT PRIMARY KEY AUTOINCREMENT — {type(exc).__name__}: {exc}")
    alt.close()
    print()


if __name__ == "__main__":
    main()
