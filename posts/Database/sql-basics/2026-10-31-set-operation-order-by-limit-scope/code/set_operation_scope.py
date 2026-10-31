"""집합 연산에서 ORDER BY 와 LIMIT 이 어디에 걸리는지 확인한다.

UNION 으로 두 결과를 합칠 때 정렬과 개수 제한을 어디에 적느냐에 따라
받는 행이 달라진다. 피연산자에 적은 것과 전체에 적은 것, 그리고
서브쿼리로 감싸 피연산자에만 거는 방법을 나란히 돌려 비교한다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

SCHEMA = """
CREATE TABLE seoul (
    name  TEXT    NOT NULL,
    score INTEGER NOT NULL
);

CREATE TABLE busan (
    name  TEXT    NOT NULL,
    score INTEGER NOT NULL
);
"""

SEOUL_ROWS = [("가은", 90), ("나래", 70), ("다온", 50)]
# 가은/90 은 서울에도 있다. UNION 과 UNION ALL 의 차이를 보려고 겹쳐 두었다.
BUSAN_ROWS = [("라온", 80), ("마루", 60), ("가은", 90)]


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO seoul VALUES (?, ?)", SEOUL_ROWS)
    conn.executemany("INSERT INTO busan VALUES (?, ?)", BUSAN_ROWS)
    conn.commit()
    return conn


def show(conn, label, sql):
    """질의 하나를 돌려 결과를 찍는다. 문법 오류면 에러 메시지를 그대로 남긴다."""
    print(f"[{label}]")
    for line in sql.strip().splitlines():
        print("  SQL  :", line)
    try:
        rows = conn.execute(sql).fetchall()
    except sqlite3.Error as exc:
        print(f"  에러 : {type(exc).__name__}: {exc}")
        print()
        return
    for row in rows:
        print("  행   :", " | ".join("NULL" if v is None else str(v) for v in row))
    print(f"  합계 : {len(rows)}행")
    print()


def plan_tree(conn, sql):
    """EXPLAIN QUERY PLAN 결과를 sqlite3 CLI 가 그리는 트리 모양 그대로 만든다.

    detail 문자열만 라벨 붙여 찍으면 사람이 정리한 표처럼 보인다. CLI 와 같은
    모양이면 도구가 돌려준 값이라는 것이 글에서 바로 드러난다.
    """
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
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


def show_plan(conn, label, sql):
    print(f"[{label}]")
    for line in plan_tree(conn, sql).splitlines():
        print("  " + line)
    print()


def main():
    print_environment()
    conn = build_database()
    print_dataset(conn)

    print("=" * 64)
    print("1. 피연산자에 ORDER BY 나 LIMIT 을 적으면 파싱 단계에서 막힌다")
    print("=" * 64)
    show(conn, "왼쪽 SELECT 에 ORDER BY", """
SELECT name, score FROM seoul ORDER BY score DESC
UNION ALL
SELECT name, score FROM busan
""")
    show(conn, "왼쪽 SELECT 에 LIMIT", """
SELECT name, score FROM seoul LIMIT 2
UNION ALL
SELECT name, score FROM busan
""")

    print("=" * 64)
    print("2. 맨 끝에 적은 ORDER BY·LIMIT 은 합쳐진 결과 전체에 걸린다")
    print("=" * 64)
    show(conn, "전체 정렬", """
SELECT name, score FROM seoul
UNION ALL
SELECT name, score FROM busan
ORDER BY score DESC
""")
    show(conn, "전체 정렬 후 2행", """
SELECT name, score FROM seoul
UNION ALL
SELECT name, score FROM busan
ORDER BY score DESC
LIMIT 2
""")
    show(conn, "ORDER BY 없이 LIMIT 만 — UNION ALL", """
SELECT name, score FROM seoul
UNION ALL
SELECT name, score FROM busan
LIMIT 5
""")
    show(conn, "ORDER BY 없이 LIMIT 만 — UNION", """
SELECT name, score FROM seoul
UNION
SELECT name, score FROM busan
LIMIT 5
""")

    print("=" * 64)
    print("3. 피연산자마다 상위 N 개를 뽑고 싶으면 서브쿼리로 감싼다")
    print("=" * 64)
    show(conn, "지역별 상위 2명", """
SELECT * FROM (SELECT name, score FROM seoul ORDER BY score DESC LIMIT 2)
UNION ALL
SELECT * FROM (SELECT name, score FROM busan ORDER BY score DESC LIMIT 2)
""")
    show(conn, "지역별 상위 2명 + 전체 정렬", """
SELECT * FROM (SELECT name, score FROM seoul ORDER BY score DESC LIMIT 2)
UNION ALL
SELECT * FROM (SELECT name, score FROM busan ORDER BY score DESC LIMIT 2)
ORDER BY score DESC
""")

    print("=" * 64)
    print("4. 합친 뒤의 ORDER BY 항은 출력 컬럼으로만 해석된다")
    print("=" * 64)
    show(conn, "출력 컬럼 번호", """
SELECT name, score FROM seoul
UNION ALL
SELECT name, score FROM busan
ORDER BY 2 DESC
""")
    show(conn, "결과에 없는 소스 컬럼", """
SELECT name FROM seoul
UNION ALL
SELECT name FROM busan
ORDER BY score
""")
    show(conn, "출력 컬럼에 없는 표현식", """
SELECT name, score FROM seoul
UNION ALL
SELECT name, score FROM busan
ORDER BY score * -1
""")
    show(conn, "출력 컬럼과 글자까지 같은 표현식", """
SELECT name, score * -1 FROM seoul
UNION ALL
SELECT name, score * -1 FROM busan
ORDER BY score * -1
""")
    show(conn, "오른쪽 SELECT 에만 있는 별칭", """
SELECT name, score FROM seoul
UNION ALL
SELECT name AS who, score FROM busan
ORDER BY who
""")

    print("=" * 64)
    print("5. 콤마를 쓴 LIMIT 은 앞이 OFFSET 이다")
    print("=" * 64)
    show(conn, "LIMIT 2 OFFSET 2", """
SELECT name, score FROM seoul
UNION ALL
SELECT name, score FROM busan
ORDER BY score DESC
LIMIT 2 OFFSET 2
""")
    show(conn, "LIMIT 2, 3", """
SELECT name, score FROM seoul
UNION ALL
SELECT name, score FROM busan
ORDER BY score DESC
LIMIT 2, 3
""")

    print("=" * 64)
    print("6. 실행계획 — 어디서 정렬하고 어디서 중복을 지우는가")
    print("=" * 64)
    show_plan(conn, "UNION ALL + 전체 ORDER BY", """
SELECT name, score FROM seoul
UNION ALL
SELECT name, score FROM busan
ORDER BY score DESC
""")
    show_plan(conn, "UNION (중복 제거) + LIMIT", """
SELECT name, score FROM seoul
UNION
SELECT name, score FROM busan
LIMIT 5
""")
    show_plan(conn, "서브쿼리로 피연산자마다 LIMIT", """
SELECT * FROM (SELECT name, score FROM seoul ORDER BY score DESC LIMIT 2)
UNION ALL
SELECT * FROM (SELECT name, score FROM busan ORDER BY score DESC LIMIT 2)
""")

    conn.close()


if __name__ == "__main__":
    main()
