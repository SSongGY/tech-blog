"""LIKE 검색과 FTS5 전문검색을 같은 데이터로 대조한다.

SQLite 3.49.1 / Python 3.13.5 에서 돌린다. 추가 설치가 필요 없다.
"""

from __future__ import annotations

import sqlite3
import sys
import time

from dbshow import print_dataset, print_environment

sys.stdout.reconfigure(encoding="utf-8")

RULE = "=" * 64

NOTES = [
    ("백업 실패", "야간 백업이 디스크 공간 부족으로 중단되었다"),
    ("공간 정리", "오래된 로그를 지워 디스크 공간을 확보했다"),
    ("스위치 교체", "네트워크 지연이 사라졌다"),
    ("인덱스 재생성", "조회가 느려 인덱스를 다시 만들었다"),
    ("백업 재시도", "백업 작업을 새벽으로 옮겨 다시 돌렸다"),
]


def build() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE note(
            id    INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            body  TEXT NOT NULL
        );
        """
    )
    conn.executemany("INSERT INTO note(title, body) VALUES (?, ?)", NOTES)
    return conn


def plan(conn: sqlite3.Connection, sql: str) -> str:
    """EXPLAIN QUERY PLAN 의 detail 원문을 그대로 돌려준다."""
    return " / ".join(row[3] for row in conn.execute("EXPLAIN QUERY PLAN " + sql))


def section(title: str) -> None:
    print(RULE)
    print(title)
    print(RULE)


def show_like(conn: sqlite3.Connection) -> None:
    section("1. LIKE 로 본문을 찾는다")
    rows = conn.execute(
        "SELECT id, title FROM note WHERE body LIKE '%디스크%'"
    ).fetchall()
    print("  LIKE '%디스크%'  ->", rows)
    print("  실행계획(detail 원문):", plan(conn, "SELECT id FROM note WHERE body LIKE '%디스크%'"))
    print()

    conn.execute("CREATE INDEX idx_note_body ON note(body)")
    print("  인덱스를 만든 뒤에도")
    for sql in (
        "SELECT id FROM note WHERE body LIKE '%디스크%'",
        "SELECT id FROM note WHERE body LIKE '야간%'",
        "SELECT id FROM note WHERE body = '네트워크 지연이 사라졌다'",
    ):
        print(f"    {sql.split('WHERE ')[1]:45s} {plan(conn, sql)}")
    print()


def show_like_prefix_rule() -> None:
    section("2. 접두 LIKE 가 인덱스를 타는 조건")
    for label, decl, index_sql, pragma in (
        ("기본", "TEXT", "CREATE INDEX i ON t(v)", None),
        ("case_sensitive_like=ON", "TEXT", "CREATE INDEX i ON t(v)", "PRAGMA case_sensitive_like = ON"),
        ("COLLATE NOCASE 인덱스", "TEXT COLLATE NOCASE", "CREATE INDEX i ON t(v COLLATE NOCASE)", None),
    ):
        c = sqlite3.connect(":memory:")
        c.executescript(f"CREATE TABLE t(v {decl}); INSERT INTO t VALUES ('야간 백업이 밀렸다');")
        c.execute(index_sql)
        if pragma:
            c.execute(pragma)
        detail = plan(c, "SELECT v FROM t WHERE v LIKE '야간%'")
        print(f"  {label:24s} LIKE '야간%'  -> {detail}")
        c.close()
    print()


def show_fts(conn: sqlite3.Connection) -> None:
    section("3. FTS5 가상 테이블을 붙인다")
    conn.executescript(
        """
        CREATE VIRTUAL TABLE note_fts USING fts5(
            title, body,
            content = 'note',
            content_rowid = 'id'
        );
        INSERT INTO note_fts(note_fts) VALUES ('rebuild');
        """
    )
    print("  MATCH '디스크'  ->", conn.execute(
        "SELECT rowid, title FROM note_fts WHERE note_fts MATCH '디스크'"
    ).fetchall())
    print("  실행계획(detail 원문):", plan(
        conn, "SELECT rowid FROM note_fts WHERE note_fts MATCH '디스크'"))
    print()

    print("  FTS5 가 만든 표:", [
        name for (name,) in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name LIKE 'note_fts%' ORDER BY name")
    ])
    print()


def show_tokens(conn: sqlite3.Connection) -> None:
    section("4. 기본 토크나이저가 만든 토큰 — 한국어에서 가장 자주 걸리는 곳")
    conn.execute("CREATE VIRTUAL TABLE note_vocab USING fts5vocab(note_fts, 'row')")
    terms = [t for (t,) in conn.execute("SELECT term FROM note_vocab ORDER BY term")]
    print(f"  토큰 {len(terms)}개")
    for i in range(0, len(terms), 6):
        print("   ", "  ".join(terms[i:i + 6]))
    print()

    print("  본문만 대상으로 같은 낱말을 세 가지로 찾아본다")
    print(f"    {'질의':8s} {'MATCH 낱말':12s} {'MATCH 낱말*':12s} {'LIKE %낱말%':12s}")
    for word in ("백업", "로그", "작업", "지연", "디스크"):
        exact = [r[0] for r in conn.execute(
            "SELECT rowid FROM note_fts WHERE note_fts MATCH 'body : ' || ? "
            "ORDER BY rowid", (word,))]
        prefix = [r[0] for r in conn.execute(
            "SELECT rowid FROM note_fts WHERE note_fts MATCH 'body : ' || ? || '*' "
            "ORDER BY rowid", (word,))]
        like = [r[0] for r in conn.execute(
            "SELECT id FROM note WHERE body LIKE '%' || ? || '%' ORDER BY id", (word,))]
        print(f"    {word:8s} {str(exact):12s} {str(prefix):12s} {str(like):12s}")
    print()


def show_helpers(conn: sqlite3.Connection) -> None:
    section("5. 어디가 맞았는지 보여주는 함수")
    for sql in (
        "SELECT highlight(note_fts, 1, '[', ']') FROM note_fts WHERE note_fts MATCH '디스크'",
        "SELECT snippet(note_fts, 1, '<', '>', '…', 4) FROM note_fts WHERE note_fts MATCH '디스크'",
    ):
        print(f"  {sql.split('SELECT ')[1].split(' FROM')[0]}")
        for (value,) in conn.execute(sql):
            print("   ", value)
        print()

    print("  bm25 로 매긴 순서 (값이 작을수록 위)")
    for rowid, score, title in conn.execute(
        "SELECT rowid, bm25(note_fts), title FROM note_fts "
        "WHERE note_fts MATCH '백업*' ORDER BY bm25(note_fts)"
    ):
        print(f"    rowid={rowid}  bm25={score:.4f}  {title}")
    print()


def show_scale() -> None:
    section("6. 5만 행에서 걸린 시간")
    big = sqlite3.connect(":memory:")
    big.executescript(
        """
        CREATE TABLE doc(id INTEGER PRIMARY KEY, body TEXT NOT NULL);
        CREATE VIRTUAL TABLE doc_fts USING fts5(
            body, content = 'doc', content_rowid = 'id');
        """
    )
    words = ["백업", "복구", "디스크", "네트워크", "인덱스", "트랜잭션", "로그", "캐시"]
    big.executemany(
        "INSERT INTO doc VALUES (?, ?)",
        [(i + 1, f"{words[i % len(words)]} 작업 {i} 번 기록 완료") for i in range(50_000)],
    )

    t0 = time.perf_counter()
    big.execute("INSERT INTO doc_fts(doc_fts) VALUES ('rebuild')")
    build_ms = (time.perf_counter() - t0) * 1000

    results = {}
    for label, sql in (
        ("LIKE '%트랜잭션%'", "SELECT COUNT(*) FROM doc WHERE body LIKE '%트랜잭션%'"),
        ("MATCH '트랜잭션'", "SELECT COUNT(*) FROM doc_fts WHERE doc_fts MATCH '트랜잭션'"),
    ):
        # 한 번 재면 캐시 상태에 휘둘린다. 다섯 번 중 가장 빠른 값을 쓴다
        best = min(_timed(big, sql) for _ in range(5))
        results[label] = best
        print(f"  {label:18s} {best[1]:5d}건  {best[0] * 1000:6.2f} ms")

    print(f"\n  색인 구축(rebuild)  {build_ms:.0f} ms")
    print(f"  색인이 차지한 행 수  doc_fts_data {big.execute('SELECT COUNT(*) FROM doc_fts_data').fetchone()[0]}행")
    like_ms, match_ms = results["LIKE '%트랜잭션%'"][0], results["MATCH '트랜잭션'"][0]
    print(f"  LIKE / MATCH 비율    {like_ms / match_ms:.0f}배")
    print()


def _timed(conn: sqlite3.Connection, sql: str) -> tuple[float, int]:
    t0 = time.perf_counter()
    n = conn.execute(sql).fetchone()[0]
    return time.perf_counter() - t0, n


def main() -> None:
    conn = build()
    print_environment()
    print_dataset(conn)
    show_like(conn)
    show_like_prefix_rule()
    show_fts(conn)
    show_tokens(conn)
    show_helpers(conn)
    show_scale()


if __name__ == "__main__":
    main()
