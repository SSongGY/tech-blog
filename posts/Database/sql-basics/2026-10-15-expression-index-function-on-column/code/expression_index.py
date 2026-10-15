"""표현식 인덱스 — 함수를 씌운 컬럼이 인덱스를 타는지 직접 세어 본다.

보고 싶은 것은 둘이다.
1) `WHERE lower(email) = ?` 가 일반 인덱스를 못 타고, 표현식 인덱스는 타는가
2) 그때 표의 행을 실제로 몇 번 건드리는가

(2)는 실행계획만 봐서는 알 수 없다. 그래서 인덱스에 쓰는 함수를 파이썬 쪽에
직접 등록해 호출 횟수를 센다. 행마다 불리면 그만큼 세어지고, 인덱스에서
바로 찾으면 0회가 된다.
"""

from __future__ import annotations

import os
import sqlite3
import tempfile

from dbshow import print_dataset, print_environment

RULE = "=" * 64
ROW_COUNT = 240

# norm() 이 몇 번 불렸는지 센다. 질의 하나를 돌릴 때마다 0으로 되돌린다.
norm_calls = 0


def norm(value: str) -> str:
    """이메일을 비교용으로 다듬는다. 같은 입력이면 항상 같은 출력이라 결정적이다."""
    global norm_calls
    norm_calls += 1
    return value.strip().lower()


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    # 표현식 인덱스에 쓰려면 결정적 함수로 등록해야 한다 (SQLite 가 요구한다)
    conn.create_function("norm", 1, norm, deterministic=True)
    conn.executescript(
        """
        CREATE TABLE member (
            id       INTEGER PRIMARY KEY,
            email    TEXT NOT NULL,
            region   TEXT NOT NULL,
            points   INTEGER NOT NULL
        );
        """
    )
    regions = ["서울", "부산", "대구", "광주"]
    rows = []
    for i in range(1, ROW_COUNT + 1):
        # 가입 화면에서 대소문자를 섞어 친 상황을 그대로 만든다
        local = f"User{i:03d}" if i % 3 == 0 else f"user{i:03d}"
        rows.append((i, f"{local}@example.com", regions[i % len(regions)], i * 7 % 500))
    conn.executemany("INSERT INTO member VALUES (?, ?, ?, ?)", rows)
    conn.commit()
    return conn


def plan_tree(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> str:
    """EXPLAIN QUERY PLAN 결과를 sqlite3 CLI 가 그리는 모양 그대로 만든다.

    detail 문자열만 뽑아 라벨을 붙이면 사람이 정리한 표처럼 보인다. CLI 와 같은
    트리면 도구가 돌려준 값이라는 것이 글에서 바로 드러난다.
    """
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql, params).fetchall()
    children: dict[int, list[tuple[int, str]]] = {}
    for node_id, parent_id, _, detail in rows:
        children.setdefault(parent_id, []).append((node_id, detail))

    lines = ["QUERY PLAN"]

    def walk(parent_id: int, prefix: str) -> None:
        items = children.get(parent_id, [])
        for index, (node_id, detail) in enumerate(items):
            last = index == len(items) - 1
            lines.append(prefix + ("`--" if last else "|--") + detail)
            walk(node_id, prefix + ("   " if last else "|  "))

    walk(0, "")
    return "\n".join(lines)


def section(title: str) -> None:
    print(RULE)
    print(title)
    print(RULE)


def run_case(conn: sqlite3.Connection, label: str, sql: str, params: tuple = ()) -> None:
    global norm_calls
    print(f"[{label}]")
    print(f"  SQL  {sql}")
    print(plan_tree(conn, sql, params))
    norm_calls = 0
    result = conn.execute(sql, params).fetchall()
    print(f"  결과 {result}")
    print(f"  norm() 호출 {norm_calls}회")
    print()


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)

    target = "user120@example.com"

    section("1. 인덱스가 없을 때")
    run_case(conn, "함수 없이 비교", "SELECT id FROM member WHERE email = ?", (target,))
    run_case(conn, "함수를 씌워 비교", "SELECT id FROM member WHERE norm(email) = ?", (target,))

    section("2. 컬럼에 건 일반 인덱스")
    conn.execute("CREATE INDEX idx_member_email ON member(email)")
    run_case(conn, "함수 없이 비교", "SELECT id FROM member WHERE email = ?", (target,))
    run_case(conn, "함수를 씌워 비교", "SELECT id FROM member WHERE norm(email) = ?", (target,))
    # 인덱스에 어떤 키가 어떤 순서로 쌓였는지 — 도식의 근거다
    run_case(
        conn,
        "일반 인덱스에 쌓인 키의 앞 세 개",
        "SELECT email FROM member ORDER BY email LIMIT 3",
    )

    section("3. 표현식에 건 인덱스")
    conn.execute("CREATE INDEX idx_member_email_norm ON member(norm(email))")
    run_case(conn, "인덱스와 같은 표현식", "SELECT id FROM member WHERE norm(email) = ?", (target,))
    run_case(
        conn,
        "같은 뜻이지만 다르게 적은 표현식",
        "SELECT id FROM member WHERE norm(email || '') = ?",
        (target,),
    )
    run_case(
        conn,
        "정렬에도 쓰이는지",
        "SELECT id FROM member ORDER BY norm(email) LIMIT 3",
    )
    run_case(
        conn,
        "표현식 인덱스에 쌓인 키의 앞 세 개",
        "SELECT norm(email) FROM member ORDER BY norm(email) LIMIT 3",
    )
    run_case(
        conn,
        "앞부분 일치 (LIKE)",
        "SELECT count(*) FROM member WHERE norm(email) LIKE 'user1%'",
    )
    # LIKE 가 범위로 바뀌지 않은 이유를 짐작하지 않고 확인한다.
    # 기본값에서 LIKE 는 대소문자를 가리지 않는데, 인덱스는 대소문자를 가리는
    # BINARY 순서로 쌓여 있다. 둘이 어긋나면 앞부분 일치를 범위로 못 바꾼다.
    conn.execute("PRAGMA case_sensitive_like = ON")
    run_case(
        conn,
        "앞부분 일치 (LIKE) — case_sensitive_like = ON",
        "SELECT count(*) FROM member WHERE norm(email) LIKE 'user1%'",
    )
    conn.execute("PRAGMA case_sensitive_like = OFF")
    run_case(
        conn,
        "앞부분 일치를 범위로 직접 적으면",
        "SELECT count(*) FROM member WHERE norm(email) >= 'user1' AND norm(email) < 'user2'",
    )
    run_case(
        conn,
        "범위 조건",
        "SELECT count(*) FROM member WHERE norm(email) BETWEEN 'user100@example.com' "
        "AND 'user110@example.com'",
    )

    section("4. 대수 계산은 하지 않는다")
    conn.executescript(
        """
        CREATE TABLE score (x INTEGER, y INTEGER);
        INSERT INTO score
          WITH RECURSIVE seq(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n < 100)
          SELECT n, n * 2 FROM seq;
        CREATE INDEX idx_score_xy ON score(x + y);
        """
    )
    for label, sql in [
        ("인덱스와 같은 순서 x + y", "SELECT count(*) FROM score WHERE x + y = 60"),
        ("순서만 바꾼 y + x", "SELECT count(*) FROM score WHERE y + x = 60"),
        ("이항한 x = 60 - y", "SELECT count(*) FROM score WHERE x = 60 - y"),
    ]:
        print(f"[{label}]")
        print(f"  SQL  {sql}")
        print(plan_tree(conn, sql))
        print(f"  결과 {conn.execute(sql).fetchone()}")
        print()

    section("5. 할 수 없는 것 — 실제 에러 메시지")
    for label, sql in [
        ("비결정적 함수", "CREATE INDEX idx_bad1 ON member(random())"),
        ("부질의", "CREATE INDEX idx_bad2 ON member((SELECT max(points) FROM member))"),
        (
            "CREATE TABLE 의 UNIQUE 제약",
            "CREATE TABLE t_bad (a TEXT, UNIQUE(norm(a)))",
        ),
    ]:
        print(f"[{label}]")
        print(f"  SQL  {sql}")
        try:
            conn.execute(sql)
            print("  (에러 없이 통과)")
        except sqlite3.Error as exc:
            print(f"  {type(exc).__name__}: {exc}")
        print()

    section("6. 쓸 수 있는 것 — 표현식 UNIQUE 인덱스")
    conn.execute("CREATE UNIQUE INDEX uq_member_email_norm ON member(norm(email))")
    print("  CREATE UNIQUE INDEX uq_member_email_norm ON member(norm(email))  → 성공")
    try:
        # 이미 user120@example.com 이 있다. 대문자로 바꿔 넣으면 통과할까
        conn.execute(
            "INSERT INTO member VALUES (?, ?, ?, ?)",
            (9001, " USER120@Example.com ", "서울", 0),
        )
        print("  대소문자만 다른 주소 INSERT → 들어갔다")
    except sqlite3.Error as exc:
        print(f"  대소문자만 다른 주소 INSERT → {type(exc).__name__}: {exc}")
    print()

    section("7. 선택도 — ANALYZE 가 기록한 sqlite_stat1")
    conn.execute("ANALYZE")
    for name, stat in conn.execute(
        "SELECT idx, stat FROM sqlite_stat1 WHERE tbl = 'member' ORDER BY idx"
    ):
        print(f"  {name:28s} {stat}")
    print()
    print("  sqlite_stat1 의 stat 는 '표의 행 수, 같은 키를 가진 평균 행 수' 다.")
    print("  뒤 숫자가 1이면 그 인덱스로 한 행까지 바로 좁혀진다는 뜻이다.")
    print()

    section("8. 더 간단한 대안 — COLLATE NOCASE")
    conn.execute("CREATE INDEX idx_member_email_nocase ON member(email COLLATE NOCASE)")
    for label, sql, params in [
        ("COLLATE 를 붙인 비교", "SELECT id FROM member WHERE email = ? COLLATE NOCASE", (target,)),
        ("COLLATE 없이 비교", "SELECT id FROM member WHERE email = ?", (target,)),
    ]:
        print(f"[{label}]")
        print(f"  SQL  {sql}")
        print(plan_tree(conn, sql, params))
        print(f"  결과 {conn.execute(sql, params).fetchall()}")
        print()
    # NOCASE 가 어디까지 접어 주는지 — ASCII 밖 글자도 되는지 확인한다
    for left, right in [("ABC", "abc"), ("ÄÖÜ", "äöü"), ("가나", "가나")]:
        same = conn.execute(
            "SELECT ? = ? COLLATE NOCASE", (left, right)
        ).fetchone()[0]
        print(f"  '{left}' = '{right}' COLLATE NOCASE  →  {bool(same)}")
    print()

    section("9. 함수를 등록하지 않은 연결에서 그 DB 를 열면")
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "probe.db")
        writer = sqlite3.connect(path)
        writer.create_function("norm", 1, norm, deterministic=True)
        writer.executescript("CREATE TABLE t (email TEXT); INSERT INTO t VALUES ('A@b.com');")
        writer.execute("CREATE INDEX idx_t_norm ON t(norm(email))")
        writer.commit()
        writer.close()

        reader = sqlite3.connect(path)  # norm 을 등록하지 않은 연결
        for label, sql in [
            ("인덱스를 안 쓰는 조회", "SELECT email FROM t"),
            ("인덱스를 쓰는 조회", "SELECT email FROM t WHERE norm(email) = 'a@b.com'"),
            ("INSERT — 인덱스를 갱신해야 한다", "INSERT INTO t VALUES ('C@d.com')"),
        ]:
            print(f"[{label}]")
            print(f"  SQL  {sql}")
            try:
                print(f"  결과 {reader.execute(sql).fetchall()}")
            except sqlite3.Error as exc:
                print(f"  {type(exc).__name__}: {exc}")
            print()
        reader.close()

    conn.close()


if __name__ == "__main__":
    main()
