"""Text-to-SQL 평가 지표 4가지(CM·EM·EX·VES)와 테스트 스위트 정확도를 SQLite로 재현한다.

정답 SQL(gold)과 '모델이 냈다고 치는' 예측 SQL(pred) 다섯 쌍을 두고,
같은 쌍이 지표마다 맞음·틀림으로 어떻게 갈리는지 본다.
Spider 공식 평가 스크립트가 아니라 원리를 보이려고 줄인 비교기다.
"""

import math
import random
import re
import sqlite3
import statistics
import time
from collections import Counter

from dbshow import print_dataset, print_environment

PAIRS = [
    ("30세 초과 직원 수",
     "SELECT count(*) FROM employee WHERE age > 30",
     "select COUNT(*)  from employee where age>30"),
    ("30세 초과 직원 수",
     "SELECT count(*) FROM employee WHERE age > 30",
     "SELECT count(*) FROM employee WHERE age >= 30"),
    ("30세 초과이고 급여 5000 초과인 직원 이름",
     "SELECT name FROM employee WHERE age > 30 AND salary > 5000",
     "SELECT name FROM employee WHERE salary > 5000 AND age > 30"),
    ("개발 부서 직원 이름",
     "SELECT e.name FROM employee e JOIN dept d ON e.dept_id = d.id WHERE d.name = '개발'",
     "SELECT name FROM employee WHERE dept_id IN (SELECT id FROM dept WHERE name = '개발')"),
    ("2026년 1월 매출 합계",
     "SELECT sum(amount) FROM sales WHERE sold_on >= '2026-01-01' AND sold_on < '2026-02-01'",
     "SELECT sum(amount) FROM sales WHERE strftime('%Y-%m', sold_on) = '2026-01'"),
]


def build_database(boundary_row=False):
    conn = sqlite3.connect(":memory:")
    conn.executescript("""
        CREATE TABLE dept (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
        CREATE TABLE employee (
            id INTEGER PRIMARY KEY, name TEXT NOT NULL,
            dept_id INTEGER REFERENCES dept(id), age INTEGER, salary INTEGER);
        CREATE TABLE sales (
            id INTEGER PRIMARY KEY, emp_id INTEGER, sold_on TEXT, amount INTEGER);
        CREATE INDEX ix_sales_sold_on ON sales(sold_on);
    """)
    conn.executemany("INSERT INTO dept VALUES (?, ?)", [(1, "개발"), (2, "영업"), (3, "재무")])
    conn.executemany("INSERT INTO employee VALUES (?, ?, ?, ?, ?)", [
        (1, "김하늘", 1, 28, 4200), (2, "이도윤", 1, 35, 6100),
        (3, "박서연", 2, 41, 5300), (4, "최민준", 2, 26, 3900),
        (5, "정유진", 3, 33, 4800), (6, "한지호", 1, 45, 7200),
    ])
    if boundary_row:
        # 테스트 스위트가 고르는 '구별하는 DB' 를 손으로 만든 것: 경계값 30 을 넣는다
        conn.execute("INSERT INTO employee VALUES (7, '오세린', 2, 30, 5000)")
    rng = random.Random(3)
    rows = []
    for i in range(1, 200_001):
        day = rng.randrange(730)                       # 2025-01-01 부터 2년
        year, doy = (2025, day) if day < 365 else (2026, day - 365)
        sold_on = time.strftime("%Y-%m-%d", time.strptime(f"{year} {doy + 1}", "%Y %j"))
        rows.append((i, rng.randrange(1, 7), sold_on, rng.randrange(100, 10_000)))
    conn.executemany("INSERT INTO sales VALUES (?, ?, ?, ?)", rows)
    conn.commit()
    return conn


# ── 내용 일치 지표: 문자열 비교와 구성요소 비교 ──────────────────
KEYWORDS = ["select", "from", "where", "group by", "order by"]


def normalize(sql):
    sql = sql.lower().strip().rstrip(";")
    sql = re.sub(r"\s*([=<>!]+|,|\(|\))\s*", r" \1 ", sql)
    return re.sub(r"\s+", " ", sql).strip()


def split_top(text, sep):
    """괄호 바깥에 있는 sep 로만 자른다. 하위 질의 안의 AND·쉼표는 건드리지 않는다."""
    parts, depth, cur, i = [], 0, "", 0
    while i < len(text):
        ch = text[i]
        depth += ch == "("
        depth -= ch == ")"
        if depth == 0 and text.startswith(sep, i):
            parts.append(cur.strip())
            cur, i = "", i + len(sep)
            continue
        cur += ch
        i += 1
    parts.append(cur.strip())
    return [p for p in parts if p]


def components(sql):
    """최상위 절을 잘라 절마다 '집합'으로 만든다. Spider 의 CM 이 순서를 무시하는 방식이다."""
    text = " " + normalize(sql) + " "
    marks, depth = [], 0
    for i, ch in enumerate(text):
        depth += ch == "("
        depth -= ch == ")"
        if depth == 0:
            for kw in KEYWORDS:
                if text.startswith(f" {kw} ", i):
                    marks.append((i, kw))
    comp = {kw: frozenset() for kw in KEYWORDS}
    for n, (pos, kw) in enumerate(marks):
        end = marks[n + 1][0] if n + 1 < len(marks) else len(text)
        body = text[pos + len(kw) + 2:end].strip()
        sep = " and " if kw == "where" else " , "
        comp[kw] = frozenset(split_top(" " + body + " ", sep))
    return comp


# ── 실행 지표 ─────────────────────────────────────────────────
def result(conn, sql):
    rows = conn.execute(sql).fetchall()
    return rows if "order by" in normalize(sql) else Counter(rows)


def median_time(conn, sql, runs=31):
    """BIRD 는 100회 돌려 이상값을 뺀 평균을 쓴다. 여기서는 31회 중앙값으로 줄였다."""
    spent = []
    for _ in range(runs):
        start = time.perf_counter()
        conn.execute(sql).fetchall()
        spent.append(time.perf_counter() - start)
    return statistics.median(spent)


def print_plan(conn, sql):
    """sqlite3 CLI 의 .eqp 트리 모양으로 찍는다."""
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    children = {}
    for node_id, parent, _, detail in rows:
        children.setdefault(parent, []).append((node_id, detail))

    def walk(parent, prefix):
        kids = children.get(parent, [])
        for n, (node_id, detail) in enumerate(kids):
            last = n == len(kids) - 1
            print(f"{prefix}{'`--' if last else '|--'}{detail}")
            walk(node_id, prefix + ("   " if last else "|  "))

    print("QUERY PLAN")
    walk(0, "")


def main():
    db1 = build_database()
    db2 = build_database(boundary_row=True)
    print_environment()
    print_dataset(db1)
    print("두 번째 DB(테스트 스위트용) = 위와 같고 employee 에 (7, '오세린', 2, 30, 5000) 한 행이 더 있다\n")

    print("=" * 72)
    print("쌍별 판정 — CM 칸은 SELECT/FROM/WHERE 절이 각각 같은지(O/X)")
    print("=" * 72)
    ex_hits, ves_sum, em_hits, str_hits, suite_hits = 0, 0.0, 0, 0, 0
    for n, (question, gold, pred) in enumerate(PAIRS, 1):
        g, p = components(gold), components(pred)
        cm = "".join("O" if g[k] == p[k] else "X" for k in ("select", "from", "where"))
        em = g == p
        same_text = normalize(gold) == normalize(pred)
        ex = result(db1, gold) == result(db1, pred)
        suite = ex and result(db2, gold) == result(db2, pred)
        reward = math.sqrt(median_time(db1, gold) / median_time(db1, pred)) if ex else 0.0
        em_hits += em
        str_hits += same_text
        ex_hits += ex
        suite_hits += suite
        ves_sum += reward
        print(f"[{n}] {question}")
        print(f"    gold: {gold}")
        print(f"    pred: {pred}")
        print(f"    문자열일치={'O' if same_text else 'X'}  CM={cm}  EM={'O' if em else 'X'}"
              f"  EX={'O' if ex else 'X'}  테스트스위트={'O' if suite else 'X'}  R={reward:.2f}")
    total = len(PAIRS)
    print()
    print(f"문자열 일치 {str_hits}/{total}  EM {em_hits}/{total}  EX {ex_hits}/{total}"
          f"  테스트 스위트 {suite_hits}/{total}  VES {ves_sum / total:.2f}")
    print()

    print("=" * 72)
    print("[5] 결과는 같은데 R 이 1 보다 작은 이유 — 실행계획")
    print("=" * 72)
    print("gold:")
    print_plan(db1, PAIRS[4][1])
    print("pred:")
    print_plan(db1, PAIRS[4][2])
    print()
    print("[2] 두 DB 에서의 결과")
    for label, conn in (("DB1", db1), ("DB2", db2)):
        gv = conn.execute(PAIRS[1][1]).fetchone()[0]
        pv = conn.execute(PAIRS[1][2]).fetchone()[0]
        print(f"    {label}: gold={gv}  pred={pv}")


if __name__ == "__main__":
    main()
