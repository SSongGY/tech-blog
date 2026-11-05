"""LIMIT/OFFSET 페이지 넘기기의 세 가지 문제를 재현한다.

1) OFFSET 이 커질수록 읽는 행이 늘어난다
2) 정렬 기준에 동률이 있으면 인덱스 유무에 따라 같은 쪽의 내용이 달라진다
3) 쪽을 넘기는 사이 새 행이 들어오면 앞 쪽의 행이 다음 쪽에 또 나온다
"""
import sqlite3
import time

from dbshow import print_dataset, print_environment

PAGE_SIZE = 5
BIG_ROW_COUNT = 200_000


def build_small():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE post (
            id    INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            score INTEGER NOT NULL
        );
        INSERT INTO post(title, score) VALUES
            ('a', 10), ('b', 20), ('c', 20), ('d', 20), ('e', 30), ('f', 30),
            ('g', 40), ('h', 40), ('i', 40), ('j', 50), ('k', 50), ('l', 60);
        """
    )
    return conn


def pages(conn, sql, count=3):
    out = []
    for n in range(count):
        rows = conn.execute(sql + " LIMIT ? OFFSET ?", (PAGE_SIZE, n * PAGE_SIZE)).fetchall()
        out.append([r[0] for r in rows])
    return out


def section_ties():
    print("\n-- 2) 동률이 있는 정렬: ORDER BY score DESC")
    conn = build_small()
    sql = "SELECT title FROM post ORDER BY score DESC"
    print("  인덱스 없음 :", pages(conn, sql))
    conn.execute("CREATE INDEX ix_post_score ON post(score)")
    print("  인덱스 생성 후:", pages(conn, sql))
    print("  id 를 덧붙여 동률을 없앤 정렬:")
    sql2 = "SELECT title FROM post ORDER BY score DESC, id"
    print("    인덱스 있음 :", pages(conn, sql2))
    conn.execute("DROP INDEX ix_post_score")
    print("    인덱스 없음 :", pages(conn, sql2))


def section_insert():
    print("\n-- 3) 쪽을 넘기는 사이 새 행이 들어올 때: ORDER BY id DESC")
    conn = build_small()
    sql = "SELECT title FROM post ORDER BY id DESC LIMIT ? OFFSET ?"
    first = [r[0] for r in conn.execute(sql, (PAGE_SIZE, 0))]
    conn.execute("INSERT INTO post(title, score) VALUES ('m', 70)")
    second = [r[0] for r in conn.execute(sql, (PAGE_SIZE, PAGE_SIZE))]
    print("  1쪽:", first)
    print("  (새 행 m 삽입)")
    print("  2쪽:", second, "<- 1쪽의 마지막 행 %s 이 또 나온다" % first[-1])


def section_speed():
    print("\n-- 1) OFFSET 이 커질수록: %d행 표, 쪽 크기 %d" % (BIG_ROW_COUNT, PAGE_SIZE))
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE big (id INTEGER PRIMARY KEY, payload TEXT NOT NULL, created INTEGER NOT NULL)")
    conn.executemany(
        "INSERT INTO big(payload, created) VALUES (?, ?)",
        ((("row-%d" % i), i) for i in range(BIG_ROW_COUNT)),
    )
    conn.execute("CREATE INDEX ix_big_created ON big(created)")
    conn.execute("ANALYZE")
    offset_sql = "SELECT id, payload FROM big ORDER BY created LIMIT ? OFFSET ?"
    key_sql = "SELECT id, payload FROM big WHERE created > ? ORDER BY created LIMIT ?"
    print("  OFFSET 방식 계획:")
    for row in conn.execute("EXPLAIN QUERY PLAN " + offset_sql, (PAGE_SIZE, 100000)):
        print("   ", row[3])
    print("  키셋 방식 계획:")
    for row in conn.execute("EXPLAIN QUERY PLAN " + key_sql, (100000, PAGE_SIZE)):
        print("   ", row[3])

    print("\n  OFFSET        OFFSET 방식 ms   키셋 방식 ms   같은 결과")
    for offset in (0, 1000, 10000, 100000, 190000):
        t0 = time.perf_counter()
        for _ in range(20):
            a = conn.execute(offset_sql, (PAGE_SIZE, offset)).fetchall()
        t1 = time.perf_counter()
        last = offset - 1  # created == 행 번호이므로 앞 쪽의 마지막 값
        for _ in range(20):
            b = conn.execute(key_sql, (last, PAGE_SIZE)).fetchall()
        t2 = time.perf_counter()
        print("  %7d  %14.3f  %13.3f   %s" % (offset, (t1 - t0) / 20 * 1000, (t2 - t1) / 20 * 1000, a == b))


if __name__ == "__main__":
    print_environment()
    print_dataset(build_small())
    section_speed()
    section_ties()
    section_insert()
