"""SQLite 에서 구분자로 묶인 문자열을 행으로 펼치는 방법들.

재귀 CTE / json_each 두 갈래를 돌려 보고, 경계값에서 무엇이 어긋나는지와
애초에 쪼개 저장했을 때 실행계획이 어떻게 달라지는지까지 확인한다.
"""

import sqlite3

from dbshow import print_dataset, print_environment

SCHEMA = """
CREATE TABLE article (
    id     INTEGER PRIMARY KEY,
    title  TEXT NOT NULL,
    tags   TEXT NOT NULL          -- 쉼표로 묶어 둔 값. 이 글이 다루는 모양이다
);

CREATE TABLE article_tag (        -- 같은 자료를 쪼개 저장한 쪽
    article_id INTEGER NOT NULL,
    tag        TEXT NOT NULL,
    PRIMARY KEY (article_id, tag)
);
CREATE INDEX idx_article_tag_tag ON article_tag(tag);
"""

ARTICLES = [
    (1, "인덱스가 안 타는 이유", "db,index,sql"),
    (2, "컨테이너 격리 입문", "linux,container"),
    (3, "느린 쿼리 잡기", "db,performance"),
    (4, "정규화 다시 보기", "db"),
]

SPLIT_CTE = """
WITH RECURSIVE split(id, tag, rest) AS (
    SELECT id, '', tags || ','
      FROM article
    UNION ALL
    SELECT id,
           substr(rest, 1, instr(rest, ',') - 1),
           substr(rest, instr(rest, ',') + 1)
      FROM split
     WHERE rest <> ''
)
SELECT id, tag FROM split WHERE tag <> '' ORDER BY id, tag
"""

SPLIT_JSON = """
SELECT a.id, j.value AS tag
  FROM article a,
       json_each('["' || replace(a.tags, ',', '","') || '"]') j
 ORDER BY a.id, j.value
"""


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO article VALUES (?, ?, ?)", ARTICLES)
    # 쪼개 저장한 쪽은 같은 자료를 재귀 CTE 로 펼쳐 넣는다. 둘의 내용이 같아야
    # 뒤에서 실행계획만 놓고 비교할 수 있다.
    conn.execute("INSERT INTO article_tag(article_id, tag) " + SPLIT_CTE)
    conn.commit()
    return conn


def show(conn, caption, sql, params=()):
    print(f"\n-- {caption}")
    for row in conn.execute(sql, params):
        print("  ", row)


def show_plan(conn, caption, sql):
    """sqlite3 CLI 가 그리는 것과 같은 트리로 찍는다.

    EXPLAIN QUERY PLAN 은 (id, parent, notused, detail) 을 돌려준다. CLI 는
    parent 를 따라 들여쓰고 마지막 자식에 `-- 를 붙인다. 중첩이 드러나야
    CO-ROUTINE 안에서 무엇이 도는지가 보인다.
    """
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    children = {}
    for node_id, parent, _notused, detail in rows:
        children.setdefault(parent, []).append((node_id, detail))

    print(f"\n-- {caption}")
    print("QUERY PLAN")

    def walk(parent, prefix):
        kids = children.get(parent, [])
        for pos, (node_id, detail) in enumerate(kids):
            last = pos == len(kids) - 1
            print(prefix + ("`--" if last else "|--") + detail)
            walk(node_id, prefix + ("   " if last else "|  "))

    walk(0, "")


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("\n" + "=" * 64)
    print("1. LIKE 로 태그를 찾으면 무엇이 걸리는가")
    print("=" * 64)
    show(
        conn,
        "tags LIKE '%db%' — 'db' 를 찾았는데",
        "SELECT id, title, tags FROM article WHERE tags LIKE '%db%'",
    )
    show(
        conn,
        "tags LIKE '%in%' — 부분 문자열이 그대로 걸린다",
        "SELECT id, tags FROM article WHERE tags LIKE '%in%'",
    )

    print("\n" + "=" * 64)
    print("2. 재귀 CTE 로 펼치기")
    print("=" * 64)
    show(conn, "article 한 행이 태그 수만큼 행이 된다", SPLIT_CTE)

    print("\n-- 펼친 결과를 WHERE 로 거르면 정확히 맞는 것만 남는다")
    rows = conn.execute(
        f"SELECT id, tag FROM ({SPLIT_CTE}) WHERE tag = 'db'"
    ).fetchall()
    for row in rows:
        print("  ", row)

    print("\n" + "=" * 64)
    print("3. json_each 로 펼치기")
    print("=" * 64)
    show(conn, "문자열을 JSON 배열 모양으로 만들어 넘긴다", SPLIT_JSON)

    print("\n" + "=" * 64)
    print("4. 경계값에서 둘이 어떻게 갈리는가")
    print("=" * 64)
    cases = [
        ("빈 문자열", ""),
        ("태그 하나", "db"),
        ("뒤에 구분자", "db,"),
        ("구분자 연속", "db,,sql"),
        ("공백 섞임", "db, sql"),
        ('따옴표 포함', 'say"hi,db'),
    ]
    for caption, value in cases:
        cte = conn.execute(
            "WITH RECURSIVE split(tag, rest) AS ("
            "  SELECT '', ? || ','"
            "  UNION ALL"
            "  SELECT substr(rest, 1, instr(rest, ',') - 1),"
            "         substr(rest, instr(rest, ',') + 1)"
            "    FROM split WHERE rest <> ''"
            ") SELECT tag FROM split WHERE tag <> ''",
            (value,),
        ).fetchall()
        try:
            js = conn.execute(
                "SELECT value FROM json_each('[\"' || replace(?, ',', '\",\"') || '\"]')",
                (value,),
            ).fetchall()
            js_out = [r[0] for r in js]
        except sqlite3.Error as exc:
            js_out = f"{type(exc).__name__}: {exc}"
        print(f"\n  {caption}: {value!r}")
        print(f"    재귀 CTE  -> {[r[0] for r in cte]}")
        print(f"    json_each -> {js_out}")

    print("\n" + "=" * 64)
    print("5. 쪼개 저장한 쪽과 실행계획 비교")
    print("=" * 64)
    conn.execute("ANALYZE")
    show_plan(
        conn,
        "펼쳐서 거르기 — article 전체를 읽는다",
        f"SELECT id FROM ({SPLIT_CTE}) WHERE tag = 'db'",
    )
    show_plan(
        conn,
        "쪼개 저장한 표 — tag 인덱스를 탄다",
        "SELECT article_id FROM article_tag WHERE tag = 'db'",
    )

    print("\n-- 두 질의의 결과가 같은지 확인")
    left = conn.execute(f"SELECT id FROM ({SPLIT_CTE}) WHERE tag = 'db'").fetchall()
    right = conn.execute(
        "SELECT article_id FROM article_tag WHERE tag = 'db' ORDER BY article_id"
    ).fetchall()
    print("   펼쳐서 거르기 :", sorted(r[0] for r in left))
    print("   쪼개 저장     :", sorted(r[0] for r in right))

    conn.close()


if __name__ == "__main__":
    main()
