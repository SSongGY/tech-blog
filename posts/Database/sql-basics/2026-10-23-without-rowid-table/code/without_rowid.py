"""WITHOUT ROWID 테이블 — 기본키로 바로 저장하면 무엇이 달라지는가.

표준 라이브러리 sqlite3 만 쓴다. 같은 데이터를 일반 표와 WITHOUT ROWID 표에
넣고 크기·실행계획·제약 차이를 나란히 찍는다. 크기는 메모리 DB 의
page_count * page_size 로 잰다.
"""

from __future__ import annotations

import random
import sqlite3

from dbshow import print_dataset, print_environment

WORD_COUNT = 20_000
SEED = 42


def make_words(count: int) -> list[str]:
    # 시드를 고정해 몇 번 돌려도 같은 단어 목록이 나오게 한다.
    rng = random.Random(SEED)
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    words = set()
    while len(words) < count:
        words.add("".join(rng.choice(alphabet) for _ in range(rng.randint(6, 12))))
    # set 의 순회 순서는 실행마다 바뀌므로 먼저 정렬한 뒤 섞는다.
    ordered = sorted(words)
    rng.shuffle(ordered)
    return ordered


def db_bytes(conn: sqlite3.Connection) -> int:
    page_count = conn.execute("PRAGMA page_count").fetchone()[0]
    page_size = conn.execute("PRAGMA page_size").fetchone()[0]
    return page_count * page_size


def build_pair(ddl_suffix: str, words: list[str], payload: bytes | None) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    if payload is None:
        conn.execute(f"CREATE TABLE wordcount (word TEXT PRIMARY KEY, cnt INTEGER){ddl_suffix}")
        conn.executemany(
            "INSERT INTO wordcount VALUES (?, ?)",
            [(word, i % 97) for i, word in enumerate(words)],
        )
    else:
        conn.execute(
            f"CREATE TABLE wordcount (word TEXT PRIMARY KEY, cnt INTEGER, memo BLOB){ddl_suffix}"
        )
        conn.executemany(
            "INSERT INTO wordcount VALUES (?, ?, ?)",
            [(word, i % 97, payload) for i, word in enumerate(words)],
        )
    conn.commit()
    return conn


def plan(conn: sqlite3.Connection, sql: str) -> list[str]:
    return [row[3] for row in conn.execute("EXPLAIN QUERY PLAN " + sql, ("abc",))]


def section(title: str) -> None:
    print()
    print(title)


def show_small_dataset() -> None:
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE wordcount_rowid (word TEXT PRIMARY KEY, cnt INTEGER);
        CREATE TABLE wordcount_norowid (word TEXT PRIMARY KEY, cnt INTEGER) WITHOUT ROWID;
        """
    )
    rows = [("sqlite", 3), ("btree", 5), ("page", 2), ("index", 7), ("rowid", 1)]
    conn.executemany("INSERT INTO wordcount_rowid VALUES (?, ?)", rows)
    conn.executemany("INSERT INTO wordcount_norowid VALUES (?, ?)", rows)
    print_dataset(conn)

    section("1. 같은 다섯 행, 같은 SELECT * — ORDER BY 없이 읽은 순서")
    print("  일반 표        :", [r[0] for r in conn.execute("SELECT * FROM wordcount_rowid")])
    print("  WITHOUT ROWID :", [r[0] for r in conn.execute("SELECT * FROM wordcount_norowid")])
    print("  일반 표의 숨은 rowid:",
          conn.execute("SELECT rowid, word FROM wordcount_rowid").fetchall())
    try:
        conn.execute("SELECT rowid FROM wordcount_norowid")
    except sqlite3.OperationalError as exc:
        print("  WITHOUT ROWID 에서 rowid 를 읽으면:", f"OperationalError: {exc}")

    section("2. 스키마에 생긴 객체 — sqlite_schema")
    for row in conn.execute("SELECT type, name, tbl_name FROM sqlite_schema ORDER BY name"):
        print("  ", row)

    section("3. PRAGMA index_info — 일반 표는 비고, WITHOUT ROWID 는 기본키 컬럼이 나온다")
    print("  wordcount_rowid  :", conn.execute("PRAGMA index_info(wordcount_rowid)").fetchall())
    print("  wordcount_norowid:", conn.execute("PRAGMA index_info(wordcount_norowid)").fetchall())


def show_lookup_plans(words: list[str]) -> None:
    section("4. 단어 하나를 찾는 실행계획 (detail 원문)")
    sql = "SELECT cnt FROM wordcount WHERE word = ?"
    for label, suffix in (("일반 표", ""), ("WITHOUT ROWID", " WITHOUT ROWID")):
        conn = build_pair(suffix, words[:10], None)
        print(f"  {label:<13}:", plan(conn, sql))


def show_sizes(words: list[str]) -> None:
    section(f"5. 크기 — 행 {WORD_COUNT:,}개, 페이지 4096 바이트")
    cases = (
        ("짧은 행 (단어 + 정수)", None),
        ("200바이트 BLOB 추가", b"x" * 200),
        ("2000바이트 BLOB 추가", b"x" * 2000),
    )
    for label, payload in cases:
        sizes = []
        for suffix in ("", " WITHOUT ROWID"):
            conn = build_pair(suffix, words, payload)
            sizes.append(db_bytes(conn))
        ratio = sizes[1] / sizes[0]
        print(f"  {label:<22} 일반 {sizes[0]:>11,}  WITHOUT {sizes[1]:>11,}  비율 {ratio:.2f}")


def show_overflow_rule() -> None:
    # 파일 포맷 문서 §1.6 의 식을 그대로 옮겼다. U 는 예약 영역이 0 이므로 페이지 크기와 같다.
    section("7. 한 페이지에 직접 담을 수 있는 최대 크기 X — 파일 포맷 문서의 식으로 계산")
    usable = 4096
    table_leaf_x = usable - 35
    index_x = (usable - 12) * 64 // 255 - 23
    min_local = (usable - 12) * 32 // 255 - 23
    print(f"  U={usable}  표 B-트리 잎 X={table_leaf_x}  인덱스 B-트리 X={index_x}  M={min_local}")
    for payload_size in (220, 2000, 2030):
        k = min_local + (payload_size - min_local) % (usable - 4)
        for label, x in (("일반 표", table_leaf_x), ("WITHOUT ROWID", index_x)):
            if payload_size <= x:
                local = payload_size
            else:
                local = k if k <= x else min_local
            print(f"  P={payload_size:>4}  {label:<13} 페이지에 {local:>4}  넘침 {payload_size - local:>4}")


def show_constraints() -> None:
    section("6. 일반 표와 다르게 동작하는 제약")
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE loose (code TEXT PRIMARY KEY, name TEXT)")
    conn.execute("CREATE TABLE strict_pk (code TEXT PRIMARY KEY, name TEXT) WITHOUT ROWID")

    conn.execute("INSERT INTO loose VALUES (NULL, 'a')")
    conn.execute("INSERT INTO loose VALUES (NULL, 'b')")
    print("  일반 표 기본키에 NULL 두 번:", conn.execute("SELECT * FROM loose").fetchall())
    try:
        conn.execute("INSERT INTO strict_pk VALUES (NULL, 'a')")
    except sqlite3.IntegrityError as exc:
        print("  WITHOUT ROWID 기본키에 NULL:", f"IntegrityError: {exc}")

    try:
        conn.execute(
            "CREATE TABLE seq (seq_id INTEGER PRIMARY KEY AUTOINCREMENT, v TEXT) WITHOUT ROWID"
        )
    except sqlite3.OperationalError as exc:
        print("  AUTOINCREMENT 를 붙이면     :", f"OperationalError: {exc}")

    conn.execute("CREATE TABLE ipk_rowid (item_id INTEGER PRIMARY KEY, v TEXT)")
    conn.execute("CREATE TABLE ipk_norowid (item_id INTEGER PRIMARY KEY, v TEXT) WITHOUT ROWID")
    conn.execute("INSERT INTO ipk_rowid (v) VALUES ('자동 번호')")
    print("  일반 표 INTEGER PRIMARY KEY 생략:", conn.execute("SELECT * FROM ipk_rowid").fetchall())
    try:
        conn.execute("INSERT INTO ipk_norowid (v) VALUES ('자동 번호')")
    except sqlite3.IntegrityError as exc:
        print("  WITHOUT ROWID 에서 생략      :", f"IntegrityError: {exc}")


def main() -> None:
    print_environment()
    show_small_dataset()
    words = make_words(WORD_COUNT)
    show_lookup_plans(words)
    show_sizes(words)
    show_constraints()
    show_overflow_rule()


if __name__ == "__main__":
    main()
