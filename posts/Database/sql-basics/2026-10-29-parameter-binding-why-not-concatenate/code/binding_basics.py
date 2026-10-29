"""문자열 조합과 파라미터 바인딩이 값에 하는 일을 나란히 돌려 본다.

값이 질의문 텍스트로 변환되면서 무엇이 달라지는지를 본다. 따옴표가 깨지는
것만이 아니라 저장되는 타입까지 바뀐다는 쪽이 이 예제의 중심이다.
"""

from __future__ import annotations

import sqlite3
import time

from dbshow import print_dataset, print_environment

RULE = "-" * 64

SCHEMA = """
CREATE TABLE member (
    member_id  INTEGER PRIMARY KEY,
    login      TEXT NOT NULL,
    nickname   TEXT,
    score      INTEGER
);

-- value 에 타입을 선언하지 않았다. SQLite 는 이 컬럼에 들어온 값을
-- 보낸 타입 그대로 저장한다 (어피니티 BLOB).
CREATE TABLE metric (
    name   TEXT NOT NULL,
    value
);
"""

# rowid 순서(= 넣은 순서)와 score 내림차순이 다르도록 섞어 둔다.
# 6절에서 ORDER BY 가 듣지 않는 것을 보려면 둘이 달라야 한다.
SEED = [
    (1, "lee", None, 610),
    (2, "kim", "김작가", 820),
    (3, "obrien", "O'Brien", 745),
]


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.executemany(
        "INSERT INTO member (member_id, login, nickname, score) VALUES (?, ?, ?, ?)",
        SEED,
    )
    conn.commit()
    return conn


def section(title: str) -> None:
    print(RULE)
    print(title)
    print(RULE)


def show_sql(sql: str) -> None:
    print(f"  SQL   : {sql}")


def run_concat(conn: sqlite3.Connection, value: str) -> None:
    """입력을 질의문 텍스트에 그대로 끼워 넣는다 — 하면 안 되는 쪽."""
    sql = f"SELECT login, nickname FROM member WHERE nickname = '{value}'"
    show_sql(sql)
    try:
        rows = conn.execute(sql).fetchall()
    except sqlite3.Error as exc:
        print(f"  결과  : {type(exc).__name__}: {exc}")
        return
    print(f"  결과  : {len(rows)}행 {rows}")


def run_bind(conn: sqlite3.Connection, value: object) -> None:
    sql = "SELECT login, nickname FROM member WHERE nickname = ?"
    show_sql(sql)
    print(f"  바인딩: {(value,)!r}")
    rows = conn.execute(sql, (value,)).fetchall()
    print(f"  결과  : {len(rows)}행 {rows}")


def demo_quote(conn: sqlite3.Connection) -> None:
    section("1. 값에 따옴표가 들어가면 — 조합은 문장이 깨진다")
    run_concat(conn, "O'Brien")
    print()
    run_bind(conn, "O'Brien")
    print()


def demo_none(conn: sqlite3.Connection) -> None:
    section("2. 값이 비어 있으면 — 조합은 조용히 틀린 답을 준다")
    # 파이썬 None 을 f-string 에 넣으면 문자열 'None' 이 된다
    run_concat(conn, None)
    print("  (닉네임이 비어 있는 lee 를 찾고 싶었지만 'None' 이라는 이름을 찾았다)")
    print()
    run_bind(conn, None)
    print("  (NULL = NULL 은 참이 아니므로 0행. SQL 에서 맞는 결과다)")
    print()
    sql = "SELECT login, nickname FROM member WHERE nickname IS NULL"
    show_sql(sql)
    rows = conn.execute(sql).fetchall()
    print(f"  결과  : {len(rows)}행 {rows}")
    print("  (NULL 을 찾을 때는 바인딩이 아니라 IS NULL 을 쓴다)")
    print()


def demo_type(conn: sqlite3.Connection) -> None:
    section("3. 저장할 때 — 조합은 값을 텍스트로 보낸다")
    # 85 를 고른 이유: 텍스트로 비교하면 900 보다 크다고 나오고
    # 숫자로 비교하면 작다고 나온다. 두 답이 갈리는 값이라야 차이가 보인다.
    reading = 85

    # 컬럼에 타입이 선언된 자리 (member.score INTEGER)
    conn.execute(
        "INSERT INTO member (member_id, login, nickname, score) "
        f"VALUES (10, 'concat', '조합', '{reading}')"
    )
    conn.execute(
        "INSERT INTO member (member_id, login, nickname, score) VALUES (?, ?, ?, ?)",
        (11, "bind", "바인딩", reading),
    )
    print("  member.score — INTEGER 로 선언된 컬럼")
    for login, score, kind in conn.execute(
        "SELECT login, score, typeof(score) FROM member "
        "WHERE login IN ('concat', 'bind') ORDER BY login"
    ):
        print(f"    {login:8s} {score!r:8} typeof={kind}")
    print("    (어느 쪽이든 integer. 선언된 타입이 텍스트를 숫자로 되돌렸다)")
    print()

    # 컬럼에 타입이 없는 자리 (metric.value)
    conn.execute(f"INSERT INTO metric (name, value) VALUES ('concat', '{reading}')")
    conn.execute("INSERT INTO metric (name, value) VALUES (?, ?)", ("bind", reading))
    print("  metric.value — 타입을 선언하지 않은 컬럼")
    for name, value, kind in conn.execute(
        "SELECT name, value, typeof(value) FROM metric ORDER BY name"
    ):
        print(f"    {name:8s} {value!r:8} typeof={kind}")
    print("    (되돌려 줄 선언이 없으니 조합 쪽은 텍스트인 채로 남았다)")
    print()

    print("  그래서 같은 조건이 다른 답을 준다 (85 는 900 보다 작다):")
    for name in ("concat", "bind"):
        hit = conn.execute(
            "SELECT COUNT(*) FROM metric WHERE name = ? AND value > 900", (name,)
        ).fetchone()[0]
        print(f"    {name:8s} value > 900 에 걸리는가: {bool(hit)}")
    print("    (텍스트는 모든 숫자보다 크다고 보므로 참이 됐다. 85 가 커서가 아니다)")
    for probe in ("'85' > 900", "'12' > 900", "'12' > 9000000"):
        answer = conn.execute(f"SELECT {probe}").fetchone()[0]
        print(f"    SELECT {probe:18s} ->  {answer}")
    print()

    conn.execute("DELETE FROM member WHERE login IN ('concat', 'bind')")
    conn.execute("DELETE FROM metric")
    conn.commit()


def demo_placeholder_styles(conn: sqlite3.Connection) -> None:
    section("4. 자리표시자 두 가지 — 위치식 ? 와 이름식 :name")
    sql = "SELECT login, score FROM member WHERE score >= ? AND score <= ?"
    show_sql(sql)
    print(f"  결과  : {conn.execute(sql, (600, 800)).fetchall()}")
    print()
    sql = "SELECT login, score FROM member WHERE score >= :low AND score <= :high"
    show_sql(sql)
    print(f"  결과  : {conn.execute(sql, {'low': 600, 'high': 800}).fetchall()}")
    print()
    sql = "SELECT login FROM member WHERE score > ?"
    show_sql(sql)
    try:
        conn.execute(sql, (600, 800)).fetchall()
    except sqlite3.Error as exc:
        print(f"  결과  : {type(exc).__name__}: {exc}")
    print("  (개수가 어긋나면 실행 전에 막힌다 — 조합에는 이 검사가 없다)")
    print()


def demo_in_list(conn: sqlite3.Connection) -> None:
    section("5. IN 목록 — 값이 아니라 자리표시자를 만든다")
    wanted = ["kim", "lee"]
    marks = ",".join("?" * len(wanted))
    sql = f"SELECT login, score FROM member WHERE login IN ({marks})"
    show_sql(sql)
    print(f"  바인딩: {tuple(wanted)!r}")
    print(f"  결과  : {conn.execute(sql, wanted).fetchall()}")
    print()


def demo_identifier(conn: sqlite3.Connection) -> None:
    section("6. 컬럼 이름은 바인딩되지 않는다")
    sql = "SELECT login, score FROM member ORDER BY ? DESC"
    show_sql(sql)
    print(f"  바인딩: {('score',)!r}")
    print(f"  결과  : {conn.execute(sql, ('score',)).fetchall()}")
    print("  (정렬되지 않았다. 에러도 안 난다)")
    print()
    allowed = {"score", "login"}
    column = "score"
    if column not in allowed:
        raise ValueError(column)
    sql = f"SELECT login, score FROM member ORDER BY {column} DESC"
    show_sql(sql)
    print(f"  결과  : {conn.execute(sql).fetchall()}")
    print("  (허용 목록으로 거른 뒤 문자열에 넣는다)")
    print()


def demo_reuse(conn: sqlite3.Connection, repeat: int = 20000) -> None:
    section(f"7. 같은 문장을 {repeat}번 반복 — 조합과 바인딩의 비용 차이")
    conn.execute("CREATE TABLE bench (n INTEGER)")

    start = time.perf_counter()
    for i in range(repeat):
        conn.execute(f"INSERT INTO bench (n) VALUES ({i})")
    concat_sec = time.perf_counter() - start

    conn.execute("DELETE FROM bench")
    start = time.perf_counter()
    for i in range(repeat):
        conn.execute("INSERT INTO bench (n) VALUES (?)", (i,))
    bind_sec = time.perf_counter() - start

    conn.execute("DELETE FROM bench")
    start = time.perf_counter()
    conn.executemany("INSERT INTO bench (n) VALUES (?)", ((i,) for i in range(repeat)))
    many_sec = time.perf_counter() - start

    print(f"  문자열 조합   {concat_sec:.3f}초")
    print(f"  바인딩        {bind_sec:.3f}초")
    print(f"  executemany   {many_sec:.3f}초")
    print()
    conn.execute("DROP TABLE bench")
    conn.commit()


def main() -> None:
    conn = build_database()
    print_environment()
    print_dataset(conn)

    demo_quote(conn)
    demo_none(conn)
    demo_type(conn)
    demo_placeholder_styles(conn)
    demo_in_list(conn)
    demo_identifier(conn)
    demo_reuse(conn)

    conn.close()


if __name__ == "__main__":
    main()
