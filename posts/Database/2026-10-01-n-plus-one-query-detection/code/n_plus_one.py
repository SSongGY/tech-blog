"""N+1 쿼리는 왜 반복해서 생기고 어떻게 잡아내는가.

ORM 의 지연 로딩(lazy loading)을 표준 라이브러리만으로 흉내 낸 작은 모델 계층을 두고,
sqlite3 의 trace 콜백으로 실제로 실행된 문장을 모아 N+1 을 잡는다.
1~2절: 같은 화면을 세 방식(지연 로딩 / JOIN / IN 묶음)으로 그리며 문장 수를 센다.
3절: 문장을 지문(fingerprint)으로 묶어 반복을 찾는다.
4절: 저자 수를 늘려 가며 문장 수 · VDBE 명령 수 · 경과 시간을 잰다.
"""

import re
import sqlite3
import time
import unittest
from collections import Counter
from contextlib import contextmanager

from dbshow import print_dataset, print_environment

POSTS_PER_AUTHOR = 3


def build_database(author_count: int) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE author (
            id   INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );
        CREATE TABLE post (
            id        INTEGER PRIMARY KEY,
            author_id INTEGER NOT NULL REFERENCES author(id),
            title     TEXT NOT NULL
        );
        CREATE INDEX post_author_id ON post(author_id);
        """
    )
    conn.executemany(
        "INSERT INTO author VALUES (?, ?)",
        [(i, f"저자{i:04d}") for i in range(1, author_count + 1)],
    )
    conn.executemany(
        "INSERT INTO post (author_id, title) VALUES (?, ?)",
        [
            (a, f"글{a:04d}-{k}")
            for a in range(1, author_count + 1)
            for k in range(1, POSTS_PER_AUTHOR + 1)
        ],
    )
    conn.commit()
    return conn


# ---------------------------------------------------------------- 모델 계층
class Session:
    """요청 하나 동안 이미 읽은 저자를 기본 키로 기억한다(식별자 맵)."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.author_names: dict[int, str] = {}


class Post:
    """ORM 엔티티처럼 author 를 처음 읽을 때 SELECT 한 번을 보낸다."""

    def __init__(self, session: Session, row: tuple) -> None:
        self._session = session
        self.id, self.author_id, self.title = row

    @property
    def author_name(self) -> str:
        cache = self._session.author_names
        if self.author_id not in cache:
            # 지연 로딩 — 화면 코드에는 이 줄이 보이지 않는다
            row = self._session.conn.execute(
                "SELECT name FROM author WHERE id = ?", (self.author_id,)
            ).fetchone()
            cache[self.author_id] = row[0]
        return cache[self.author_id]


def render_lazy(conn: sqlite3.Connection) -> list[str]:
    session = Session(conn)
    rows = conn.execute("SELECT id, author_id, title FROM post")
    posts = [Post(session, r) for r in rows]
    return [f"{p.title} / {p.author_name}" for p in posts]


def render_join(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT p.title, a.name FROM post p JOIN author a ON a.id = p.author_id"
    )
    return [f"{title} / {name}" for title, name in rows]


def render_in_batch(conn: sqlite3.Connection) -> list[str]:
    posts = conn.execute("SELECT id, author_id, title FROM post").fetchall()
    author_ids = sorted({r[1] for r in posts})
    marks = ",".join("?" * len(author_ids))
    names = dict(
        conn.execute(f"SELECT id, name FROM author WHERE id IN ({marks})", author_ids)
    )
    return [f"{title} / {names[author_id]}" for _, author_id, title in posts]


# ---------------------------------------------------------------- 탐지기
_LITERAL = re.compile(r"'(?:[^']|'')*'|\b\d+(?:\.\d+)?\b")
_IN_LIST = re.compile(r"\(\s*\?(?:\s*,\s*\?)*\s*\)")


def fingerprint(sql: str) -> str:
    """값만 다른 문장을 같은 모양으로 묶는다. 리터럴 → ?, IN 목록 → (?+)."""
    shape = _LITERAL.sub("?", sql)
    shape = _IN_LIST.sub("(?+)", shape)
    return " ".join(shape.split())


@contextmanager
def capture_queries(conn: sqlite3.Connection):
    statements: list[str] = []
    conn.set_trace_callback(statements.append)
    try:
        yield statements
    finally:
        conn.set_trace_callback(None)


@contextmanager
def assert_no_repeated_query(conn: sqlite3.Connection, max_repeat: int = 2):
    """같은 지문이 max_repeat 번을 넘게 나오면 실패시킨다.

    전체 개수 상한은 데이터가 늘면 다시 맞춰야 하지만,
    지문 반복 횟수는 데이터 크기와 무관하게 고정할 수 있다.
    """
    with capture_queries(conn) as statements:
        yield statements
    counts = Counter(fingerprint(s) for s in statements)
    shape, repeat = counts.most_common(1)[0] if counts else ("", 0)
    if repeat > max_repeat:
        raise AssertionError(
            f"같은 모양의 문장이 {repeat}번 실행됐다 (허용 {max_repeat}): {shape}"
        )


# ---------------------------------------------------------------- 측정
def count_vdbe_steps(conn: sqlite3.Connection, render) -> int:
    steps = 0

    def tick() -> int:
        nonlocal steps
        steps += 1
        return 0

    conn.set_progress_handler(tick, 1)
    try:
        render(conn)
    finally:
        conn.set_progress_handler(None, 1)
    return steps


RENDERERS = [("지연 로딩", render_lazy), ("JOIN", render_join), ("IN 묶음", render_in_batch)]


def section_counts(conn: sqlite3.Connection) -> None:
    print("\n== 1. 같은 화면, 세 방식 — 실행된 문장 수 ==")
    for label, render in RENDERERS:
        with capture_queries(conn) as statements:
            lines = render(conn)
        print(f"\n[{label}] 화면 {len(lines)}줄 · 문장 {len(statements)}개")
        for sql in statements[:4]:
            print(f"  {' '.join(sql.split())}")
        if len(statements) > 4:
            print(f"  … {len(statements) - 4}개 더")


def section_fingerprint(conn: sqlite3.Connection) -> None:
    print("\n== 2. 지문으로 묶기 ==")
    with capture_queries(conn) as statements:
        render_lazy(conn)
    for shape, n in Counter(fingerprint(s) for s in statements).most_common():
        print(f"  {n:>3}회  {shape}")


def section_assert(conn: sqlite3.Connection) -> None:
    print("\n== 3. 테스트에 거는 탐지기 ==")
    for label, render in RENDERERS:
        try:
            with assert_no_repeated_query(conn):
                render(conn)
            print(f"  [{label}] 통과")
        except AssertionError as exc:
            print(f"  [{label}] 실패 — {exc}")


def section_scaling() -> None:
    print("\n== 4. 저자 수를 늘리면 ==")
    print("  저자 |      방식 | 문장 수 | VDBE 명령 수 | 경과(ms)")
    for author_count in (10, 100, 1000):
        conn = build_database(author_count)
        for label, render in RENDERERS:
            with capture_queries(conn) as statements:
                render(conn)
            steps = count_vdbe_steps(conn, render)
            started = time.perf_counter()
            render(conn)
            elapsed_ms = (time.perf_counter() - started) * 1000
            print(
                f"  {author_count:>4} | {label:>9} | {len(statements):>7} |"
                f" {steps:>12,} | {elapsed_ms:>8.2f}"
            )
        conn.close()


def section_unittest() -> None:
    print("\n== 5. unittest 로 돌리면 ==", flush=True)
    import test_n_plus_one

    suite = unittest.defaultTestLoader.loadTestsFromModule(test_n_plus_one)
    # 트레이스백에는 이 PC 의 절대 경로가 찍히므로 결과와 실패 메시지만 남긴다
    result = unittest.TestResult()
    suite.run(result)
    failed = {test.id(): trace for test, trace in result.failures + result.errors}
    for test in test_n_plus_one.PostListQueryTest.__dict__:
        if not test.startswith("test_"):
            continue
        test_id = f"test_n_plus_one.PostListQueryTest.{test}"
        if test_id in failed:
            print(f"  {test} ... FAIL")
            print(f"    {failed[test_id].strip().splitlines()[-1]}")
        else:
            print(f"  {test} ... ok")
    print(f"  {result.testsRun}개 중 실패 {len(failed)}개")


def main() -> None:
    conn = build_database(author_count=4)
    print_environment()
    print_dataset(conn)
    section_counts(conn)
    section_fingerprint(conn)
    section_assert(conn)
    section_scaling()
    section_unittest()


if __name__ == "__main__":
    main()
