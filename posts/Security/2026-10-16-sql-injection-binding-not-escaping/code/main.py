"""SQL 인젝션을 이스케이프로 막으려 할 때와 바인딩으로 막을 때를 나란히 돌린다.

쓰는 데이터는 전부 가상의 예제 값이다. 실제 계정이나 해시가 아니다.
"""

from __future__ import annotations

import sqlite3

from dbshow import print_dataset, print_environment

RULE = "=" * 64

SCHEMA = """
CREATE TABLE member (
    member_id INTEGER PRIMARY KEY,
    login     TEXT NOT NULL UNIQUE,
    secret    TEXT NOT NULL,
    role      TEXT NOT NULL
);
"""

ROWS = [
    (1, "kim",   "hash-aaaa", "admin"),
    (2, "lee",   "hash-bbbb", "member"),
    (3, "park",  "hash-cccc", "member"),
    (4, "choi",  "hash-dddd", "member"),
]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO member VALUES (?, ?, ?, ?)", ROWS)
    conn.commit()
    return conn


def run(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> None:
    """질의문과 결과를 함께 찍는다. 터지면 예외도 그대로 보인다."""
    print(f"  SQL   : {sql}")
    if params:
        print(f"  바인딩: {params}")
    try:
        rows = conn.execute(sql, params).fetchall()
    except sqlite3.Error as exc:
        print(f"  결과  : {type(exc).__name__}: {exc}\n")
        return
    print(f"  결과  : {len(rows)}행 {rows}\n")


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)

    normal = "kim"
    tautology = "' OR '1'='1"

    print(RULE)
    print("1. 문자열을 이어 붙여 만든 질의 — 정상 입력일 때는 잘 돈다")
    print(RULE)
    run(conn, f"SELECT login, role FROM member WHERE login = '{normal}'")

    print(RULE)
    print("2. 같은 코드에 따옴표가 든 입력을 넣으면")
    print(RULE)
    print(f"  입력  : {tautology!r}")
    run(conn, f"SELECT login, role FROM member WHERE login = '{tautology}'")
    print("  → 조건이 항상 참이 되어 표 전체가 나왔다\n")

    print(RULE)
    print("3. 문장을 하나 더 붙이려는 시도 — execute 는 한 문장만 받는다")
    print(RULE)
    multi = "x'; DROP TABLE member; --"
    print(f"  입력  : {multi!r}")
    run(conn, f"SELECT login, role FROM member WHERE login = '{multi}'")
    print("  → 다만 '한 문장 안에서 조건을 바꾸는' 2번은 그대로 통한다\n")

    print(RULE)
    print("4. 작은따옴표를 두 개로 바꾸는 이스케이프 — 2번은 막힌다")
    print(RULE)
    escaped = tautology.replace("'", "''")
    print(f"  이스케이프 결과: {escaped!r}")
    run(conn, f"SELECT login, role FROM member WHERE login = '{escaped}'")

    print(RULE)
    print("5. 그런데 따옴표가 없는 자리는 이스케이프가 닿지 않는다")
    print(RULE)
    numeric = "0 OR 1=1"
    print(f"  입력  : {numeric!r}  (이스케이프해도 그대로: {numeric.replace(chr(39), chr(39) * 2)!r})")
    run(conn, f"SELECT login, role FROM member WHERE member_id = {numeric}")
    print("  → 숫자 자리는 따옴표로 감싸지 않으므로 따옴표를 고쳐도 소용이 없다\n")

    print(RULE)
    print("6. 바인딩 — 같은 입력을 그대로 넘긴다")
    print(RULE)
    for value in (normal, tautology, multi):
        run(conn, "SELECT login, role FROM member WHERE login = ?", (value,))
    run(conn, "SELECT login, role FROM member WHERE member_id = ?", (numeric,))
    print("  → 값이 문법으로 해석되지 않으므로 '찾는 값이 없다'로 끝난다\n")

    print(RULE)
    print("7. 추적 콜백이 보여 주는 문장 — 바인딩은 이스케이프를 대신해 준다")
    print(RULE)
    print("  [1] 문자열 조합, [2] 바인딩. 콜백이 주는 것은 값을 끼워 넣어 복원한")
    print("  '확장 문장'이고, 엔진이 실제로 파싱한 것은 [2]의 경우 ? 가 든 쪽이다.")
    seen: list[str] = []
    conn.set_trace_callback(seen.append)
    conn.execute(f"SELECT login FROM member WHERE login = '{tautology}'").fetchall()
    conn.execute("SELECT login FROM member WHERE login = ?", (tautology,)).fetchall()
    conn.set_trace_callback(None)
    for i, stmt in enumerate(seen, 1):
        print(f"  [{i}] {stmt}")
    print()

    print(RULE)
    print("8. 바인딩으로 안 되는 자리 — 식별자는 값이 아니다")
    print(RULE)
    run(conn, "SELECT login FROM member ORDER BY ?", ("role",))
    print("  → 에러는 안 나지만 role 로 정렬되지 않았다. 바인딩된 값은 컬럼이 아니라")
    print("     문자열 상수 하나로 해석되어 모든 행의 정렬 키가 같아진다")
    run(conn, "SELECT login FROM ?", ("member",))

    allowed = {"login", "role", "member_id"}
    picked = "role"
    if picked in allowed:  # 허용 목록으로 거르고 나서 문자열에 넣는다
        run(conn, f"SELECT login, role FROM member ORDER BY {picked}, member_id")
    bad = "member_id; DROP TABLE member"
    print(f"  허용 목록 밖 입력 {bad!r} → 통과 여부: {bad in allowed}\n")

    print(RULE)
    print("9. 표가 아직 그대로인지 확인")
    print(RULE)
    run(conn, "SELECT COUNT(*) FROM member")

    conn.close()


if __name__ == "__main__":
    main()
