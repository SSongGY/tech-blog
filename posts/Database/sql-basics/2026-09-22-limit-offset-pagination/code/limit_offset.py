"""LIMIT / OFFSET 의 문법과, OFFSET 이 커질 때 실제로 무엇이 늘어나는지 측정한다.

측정은 SQLite 가상 머신이 실행한 명령 개수로 한다. 시간은 환경에 따라 흔들리지만
명령 개수는 같은 데이터·같은 질의면 몇 번을 돌려도 같은 값이 나온다.
"""

import sqlite3
import time

ROW_COUNT = 200_000
PAGE_SIZE = 10


def build_sample(conn):
    conn.execute(
        "CREATE TABLE article ("
        "  id INTEGER PRIMARY KEY,"
        "  title TEXT NOT NULL,"
        "  view_count INTEGER NOT NULL)"
    )
    conn.executemany(
        "INSERT INTO article (id, title, view_count) VALUES (?, ?, ?)",
        ((i, f"글 {i:06d}", (i * 7919) % 1000) for i in range(1, ROW_COUNT + 1)),
    )
    conn.commit()


def show(conn, label, sql, params=()):
    print(f"-- {label}")
    print(f"   {sql}")
    rows = conn.execute(sql, params).fetchall()
    if not rows:
        print("   (행 없음)")
    for row in rows:
        print("   " + "  ".join(str(col) for col in row))
    print()
    return rows


def count_vm_steps(conn, sql, params=()):
    """질의 하나가 실행한 SQLite 가상 머신 명령 개수를 센다."""
    steps = 0

    def tick():
        nonlocal steps
        steps += 1
        return 0

    conn.set_progress_handler(tick, 1)
    started = time.perf_counter()
    conn.execute(sql, params).fetchall()
    elapsed_ms = (time.perf_counter() - started) * 1000
    conn.set_progress_handler(None, 0)
    return steps, elapsed_ms


def plan_tree(conn, sql, params=()):
    """EXPLAIN QUERY PLAN 결과를 sqlite3 CLI 가 보여주는 모양 그대로 만든다.

    detail 문자열만 라벨 붙여 찍으면 사람이 정리한 표처럼 보인다. CLI 와 같은 모양이면
    도구가 돌려준 값이라는 것이 글에서 바로 드러난다. 트리 구조는 각 행의
    (id, parent) 로 만든다 — 서브쿼리나 조인이 있으면 실제로 여러 단이 나온다.
    """
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql, params).fetchall()
    children = {}
    for node_id, parent_id, _, detail in rows:
        children.setdefault(parent_id, []).append((node_id, detail))

    lines = ["QUERY PLAN"]

    def walk(parent_id, prefix):
        items = children.get(parent_id, [])
        for index, (node_id, detail) in enumerate(items):
            last = index == len(items) - 1
            lines.append(prefix + ("`--" if last else "|--") + detail)
            walk(node_id, prefix + ("   " if last else "|  "))

    walk(0, "")
    return "\n".join(lines)


def indented_plan(conn, sql, params=(), indent="   "):
    """plan_tree 를 본문에 넣기 좋게 들여쓴다."""
    return "\n".join(indent + line for line in plan_tree(conn, sql, params).splitlines())


def main():
    print(f"SQLite {sqlite3.sqlite_version}")
    print(f"전체 행 수 {ROW_COUNT:,} · 한 페이지 {PAGE_SIZE}행")
    print()

    conn = sqlite3.connect(":memory:")
    build_sample(conn)

    show(conn, "1. 앞에서 3행만", "SELECT id, title FROM article ORDER BY id LIMIT 3")
    show(
        conn,
        "2. 3행을 건너뛰고 3행",
        "SELECT id, title FROM article ORDER BY id LIMIT 3 OFFSET 3",
    )
    show(
        conn,
        "3. 쉼표 문법 — 앞이 OFFSET, 뒤가 개수다",
        "SELECT id, title FROM article ORDER BY id LIMIT 3, 3",
    )
    show(
        conn,
        "4. OFFSET 이 전체 행 수를 넘으면",
        f"SELECT id, title FROM article ORDER BY id LIMIT 3 OFFSET {ROW_COUNT}",
    )
    show(
        conn,
        "5. LIMIT 이 음수면 SQLite 는 제한 없음으로 읽는다 (OFFSET 은 살아 있다)",
        f"SELECT id, title FROM article ORDER BY id LIMIT -1 OFFSET {ROW_COUNT - 2}",
    )

    print("-- 6. OFFSET 을 키우면서 가상 머신 명령 개수를 센다")
    offset_sql = "SELECT id, title FROM article ORDER BY id LIMIT ? OFFSET ?"
    baseline = None
    for offset in (0, 1_000, 10_000, 100_000, 199_990):
        steps, elapsed_ms = count_vm_steps(conn, offset_sql, (PAGE_SIZE, offset))
        if baseline is None:
            baseline = steps
        print(
            f"   OFFSET {offset:>7,}  명령 {steps:>9,}개"
            f"  (첫 페이지의 {steps / baseline:>6.1f}배)  {elapsed_ms:6.1f} ms"
        )
    print()

    print("-- 7. 같은 10행을 마지막 읽은 id 로 집는다")
    keyset_sql = "SELECT id, title FROM article WHERE id > ? ORDER BY id LIMIT ?"
    for last_id in (0, 1_000, 10_000, 100_000, 199_990):
        steps, elapsed_ms = count_vm_steps(conn, keyset_sql, (last_id, PAGE_SIZE))
        print(
            f"   id > {last_id:>7,}   명령 {steps:>9,}개"
            f"  {elapsed_ms:6.1f} ms"
        )
    print()

    print("-- 8. 두 방식의 실행 계획")
    for label, sql in (
        ("OFFSET", "SELECT id, title FROM article ORDER BY id LIMIT 10 OFFSET 100000"),
        ("키셋", "SELECT id, title FROM article WHERE id > 100000 ORDER BY id LIMIT 10"),
    ):
        print(f"   {label}")
        print(indented_plan(conn, sql, indent="   "))
    print()

    print("-- 9. ORDER BY 없는 LIMIT 은 어느 행이 나올지 정해져 있지 않다")
    for label in ("인덱스 없음", "인덱스 생성 후"):
        if label == "인덱스 생성 후":
            conn.execute("CREATE INDEX ix_article_view_count ON article (view_count)")
        rows = conn.execute("SELECT id FROM article LIMIT 3").fetchall()
        print(f"   {label:<12} 결과 {[r[0] for r in rows]}")
        print(indented_plan(conn, "SELECT id FROM article LIMIT 3", indent="   "))
    print()

    conn.close()


if __name__ == "__main__":
    main()
