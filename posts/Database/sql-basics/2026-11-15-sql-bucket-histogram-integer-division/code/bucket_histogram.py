"""기온 값을 5도 구간으로 묶어 센다. 음수와 빈 구간에서 결과가 어떻게 틀어지는지 본다.

1) CASE 로 구간 나누기 — BETWEEN 경계가 겹치면 한 값이 두 번 세진다
2) 정수 나눗셈 버킷 (temp / 5) * 5 — 음수가 0 쪽으로 잘린다
3) / 와 % 가 음수에서 내는 값, floor() 가 있는지
4) 고친 버킷 — floor() 와, floor() 없이 CASE 로 내림하기
5) 빈 구간이 사라지는 것과 재귀 CTE 로 채우기, 막대를 그리는 두 방법
6) REAL 값의 버킷 — CAST 와 floor
"""
import sqlite3

from dbshow import print_dataset, print_environment

BUCKET_WIDTH = 5


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE reading (
            reading_id INTEGER PRIMARY KEY,
            temp       INTEGER NOT NULL,   -- 섭씨, 정수
            temp_exact REAL    NOT NULL    -- 소수점까지 잰 값
        );
        INSERT INTO reading (temp, temp_exact) VALUES
            (-12, -12.4), (-7, -6.6), (-5, -5.0), (-3, -3.2), (-1, -0.8),
            (0, 0.0), (2, 2.3), (4, 4.9), (5, 5.0), (9, 9.1),
            (13, 12.7), (18, 18.2), (21, 21.4), (22, 22.0), (33, 33.3);
        """
    )
    return conn


def show(conn, title, sql, params=()):
    print(title)
    print("  sql> " + " ".join(sql.split()))
    try:
        cursor = conn.execute(sql, params)
    except sqlite3.Error as error:
        print(f"  {type(error).__name__}: {error}")
        print()
        return
    headers = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    print("  " + " | ".join(headers))
    for row in rows:
        print("  " + " | ".join("NULL" if v is None else str(v) for v in row))
    print(f"  ({len(rows)}행)")
    print()


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)

    show(
        conn,
        "[1-A] BETWEEN 으로 구간을 나누면 (경계값 5 가 두 구간에 걸린다)",
        """
        SELECT SUM(temp BETWEEN 0 AND 5)  AS b_0_5,
               SUM(temp BETWEEN 5 AND 10) AS b_5_10,
               SUM(temp BETWEEN 0 AND 10) AS b_0_10
        FROM reading
        """,
    )
    show(
        conn,
        "[1-B] CASE 로 반열린 구간 [하한, 상한) 을 쓰면",
        """
        SELECT CASE
                 WHEN temp < 0  THEN '영하'
                 WHEN temp < 10 THEN '0~9'
                 WHEN temp < 20 THEN '10~19'
                 ELSE '20 이상'
               END AS band,
               COUNT(*) AS n
        FROM reading
        GROUP BY band
        ORDER BY MIN(temp)
        """,
    )

    show(
        conn,
        "[2] 정수 나눗셈 버킷 (temp / 5) * 5",
        """
        SELECT (temp / ?) * ? AS bucket_start,
               COUNT(*) AS n,
               group_concat(temp, ',') AS members
        FROM reading
        GROUP BY bucket_start
        ORDER BY bucket_start
        """,
        (BUCKET_WIDTH, BUCKET_WIDTH),
    )

    show(
        conn,
        "[3-A] 음수에서 / 와 % 가 내는 값",
        """
        SELECT temp, temp / 5 AS div, temp % 5 AS rem,
               (temp / 5) * 5 + temp % 5 AS restored
        FROM reading WHERE temp < 1
        ORDER BY temp
        """,
    )
    show(conn, "[3-B] floor() 가 있는가", "SELECT floor(-3 / 5.0) AS f, floor(-0.6) AS g")

    show(
        conn,
        "[4-A] floor() 로 내림한 버킷",
        """
        SELECT CAST(floor(temp * 1.0 / ?) AS INTEGER) * ? AS bucket_start,
               COUNT(*) AS n,
               group_concat(temp, ',') AS members
        FROM reading
        GROUP BY bucket_start
        ORDER BY bucket_start
        """,
        (BUCKET_WIDTH, BUCKET_WIDTH),
    )
    show(
        conn,
        "[4-B] floor() 없이 — 나머지가 음수면 한 칸 내린다",
        """
        SELECT (temp / ? - (temp % ? < 0)) * ? AS bucket_start,
               COUNT(*) AS n,
               group_concat(temp, ',') AS members
        FROM reading
        GROUP BY bucket_start
        ORDER BY bucket_start
        """,
        (BUCKET_WIDTH, BUCKET_WIDTH, BUCKET_WIDTH),
    )

    show(
        conn,
        "[5] 빈 구간까지 0 으로 채우기 (재귀 CTE 로 구간표를 만들고 LEFT JOIN)",
        """
        WITH RECURSIVE bucket(start) AS (
            SELECT -15
            UNION ALL
            SELECT start + ? FROM bucket WHERE start + ? <= 30
        ),
        tagged AS (
            SELECT temp, (temp / ? - (temp % ? < 0)) * ? AS start FROM reading
        )
        SELECT b.start AS bucket_start, b.start + ? - 1 AS bucket_end,
               COUNT(t.temp) AS n,
               printf('%.*c', COUNT(t.temp), '#') AS bar_printf,
               substr('##########', 1, COUNT(t.temp)) AS bar_substr
        FROM bucket AS b
        LEFT JOIN tagged AS t ON t.start = b.start
        GROUP BY b.start
        ORDER BY b.start
        """,
        (BUCKET_WIDTH,) * 6,
    )
    show(
        conn,
        "[5-B] printf 의 %.*c 에 반복 횟수 0, 1, 3 을 주면",
        """
        SELECT printf('[%.*c]', 0, '#') AS zero,
               printf('[%.*c]', 1, '#') AS one,
               printf('[%.*c]', 3, '#') AS three,
               printf('[%.*c]', -1, '#') AS minus_one
        """,
    )

    show(
        conn,
        "[6] REAL 값 — CAST 는 0 쪽으로 자르고 floor 는 내린다",
        """
        SELECT temp_exact,
               CAST(temp_exact / 5 AS INTEGER) * 5 AS by_cast,
               CAST(floor(temp_exact / 5) AS INTEGER) * 5 AS by_floor
        FROM reading WHERE temp_exact < 6
        ORDER BY temp_exact
        """,
    )


if __name__ == "__main__":
    main()
