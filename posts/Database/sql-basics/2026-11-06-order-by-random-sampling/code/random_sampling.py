"""무작위로 N행 뽑는 세 가지 방법을 비교한다.

1) ORDER BY RANDOM() LIMIT n — 행마다 난수를 만들고 정렬한다
2) rowid 범위에서 난수 하나 — 빠르지만 빈 번호가 있으면 표본이 치우친다
3) 시드를 둔 정렬 키 — 같은 시드면 같은 표본이 다시 나온다
"""
import random
import sqlite3
import time
from collections import Counter

from dbshow import _render, print_dataset, print_environment

BIG_ROW_COUNT = 200_000
SAMPLE_SIZE = 3
TRIAL_COUNT = 10_000
SEED = 42


def build_small():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE product (
            id   INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );
        INSERT INTO product(name) VALUES
            ('apple'), ('banana'), ('cherry'), ('grape'), ('kiwi'),
            ('lemon'), ('mango'), ('melon'), ('peach'), ('plum');
        """
    )
    return conn


def build_big(row_count):
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE big (id INTEGER PRIMARY KEY, payload TEXT NOT NULL)")
    conn.executemany(
        "INSERT INTO big(payload) VALUES (?)",
        (("row-%d" % i,) for i in range(row_count)),
    )
    return conn


def print_plan(conn, sql, params=()):
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql, params).fetchall()
    children = {}
    for node_id, parent, _, detail in rows:
        children.setdefault(parent, []).append((node_id, detail))

    def walk(parent, prefix):
        items = children.get(parent, [])
        for i, (node_id, detail) in enumerate(items):
            last = i == len(items) - 1
            print("  " + prefix + ("`--" if last else "|--") + detail)
            walk(node_id, prefix + ("   " if last else "|  "))

    print("  QUERY PLAN")
    walk(0, "")


def section_basic():
    print("\n-- 1) ORDER BY RANDOM() LIMIT 3 를 세 번 실행")
    conn = build_small()
    sql = "SELECT id, name FROM product ORDER BY RANDOM() LIMIT 3"
    for n in range(3):
        print("  %d회:" % (n + 1), conn.execute(sql).fetchall())
    print_plan(conn, sql)


def section_cost():
    print("\n-- 2) 난수를 몇 번 만드는가: 행 수를 바꿔 가며 random() 호출 수를 센다")
    rows = []
    for row_count in (1_000, 10_000, 100_000):
        conn = build_big(row_count)
        calls = [0]

        def counted_random():
            calls[0] += 1
            return random.getrandbits(63)

        conn.create_function("counted_random", 0, counted_random)
        conn.execute("SELECT id FROM big ORDER BY counted_random() LIMIT 3").fetchall()
        rows.append((row_count, SAMPLE_SIZE, calls[0]))
        conn.close()
    for line in _render(["표의 행 수", "뽑은 행", "난수 생성 횟수"], rows, [True, True, True]):
        print("  " + line)


def section_rowid_bias():
    print("\n-- 3) rowid 범위에서 난수 하나로 뽑기: 빈 번호가 있으면")
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE member (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
    conn.executemany(
        "INSERT INTO member(id, name) VALUES (?, ?)",
        ((i, "m%03d" % i) for i in range(1, 101)),
    )
    conn.execute("DELETE FROM member WHERE id BETWEEN 11 AND 60")
    left = conn.execute("SELECT COUNT(*), MIN(id), MAX(id) FROM member").fetchone()
    print("  남은 행 %d개, id 범위 %d~%d (11~60 삭제)" % left)

    sql = "SELECT id FROM member WHERE id >= ? ORDER BY id LIMIT 1"
    print_plan(conn, sql, (1,))
    rng = random.Random(SEED)
    picked = Counter()
    max_id = left[2]
    for _ in range(TRIAL_COUNT):
        target = rng.randint(1, max_id)
        picked[conn.execute(sql, (target,)).fetchone()[0]] += 1
    rows = [(i, picked[i], "%.1f%%" % (picked[i] / TRIAL_COUNT * 100)) for i in (1, 10, 61, 62, 100)]
    print("  %d번 뽑았을 때 행별로 뽑힌 횟수 (일부)" % TRIAL_COUNT)
    for line in _render(["id", "뽑힌 횟수", "비율"], rows, [True, True, True]):
        print("  " + line)
    print("  고르게 뽑혔다면 행마다 %.1f%% 근처여야 한다" % (100 / left[0]))


def section_speed():
    print("\n-- 4) %d행 표에서 한 행 뽑는 시간 (20회 평균)" % BIG_ROW_COUNT)
    conn = build_big(BIG_ROW_COUNT)
    order_sql = "SELECT id, payload FROM big ORDER BY RANDOM() LIMIT 1"
    rowid_sql = "SELECT id, payload FROM big WHERE id >= ? ORDER BY id LIMIT 1"
    print_plan(conn, rowid_sql, (1,))
    t0 = time.perf_counter()
    for _ in range(20):
        conn.execute(order_sql).fetchall()
    t1 = time.perf_counter()
    rng = random.Random(SEED)
    for _ in range(20):
        conn.execute(rowid_sql, (rng.randint(1, BIG_ROW_COUNT),)).fetchall()
    t2 = time.perf_counter()
    rows = [
        ("ORDER BY RANDOM() LIMIT 1", "%.3f" % ((t1 - t0) / 20 * 1000)),
        ("id >= 난수 LIMIT 1", "%.3f" % ((t2 - t1) / 20 * 1000)),
    ]
    for line in _render(["방법", "ms"], rows, [False, True]):
        print("  " + line)


def section_seeded():
    print("\n-- 5-A) 시드를 더한 정렬 키: (id * 1103515245 + seed) % 2147483648")
    conn = build_small()
    sql = (
        "SELECT id, name FROM product "
        "ORDER BY (id * 1103515245 + :seed) % 2147483648 LIMIT 3"
    )
    for seed in (7, 7, 8, 1_000_000_000):
        print("  seed=%d:" % seed, conn.execute(sql, {"seed": seed}).fetchall())

    print("\n-- 5-B) id 목록을 받아 파이썬에서 시드로 고른 뒤 IN 으로 읽기")
    ids = [r[0] for r in conn.execute("SELECT id FROM product ORDER BY id")]
    for seed in (7, 7, 8):
        chosen = random.Random(seed).sample(ids, SAMPLE_SIZE)
        rows = conn.execute(
            "SELECT id, name FROM product WHERE id IN (?, ?, ?) ORDER BY id", chosen
        ).fetchall()
        print("  seed=%d:" % seed, rows)


if __name__ == "__main__":
    print_environment()
    print_dataset(build_small())
    section_basic()
    section_cost()
    section_rowid_bias()
    section_speed()
    section_seeded()
