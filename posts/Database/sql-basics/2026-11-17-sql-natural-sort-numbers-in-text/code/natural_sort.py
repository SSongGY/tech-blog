"""숫자가 섞인 문자열을 ORDER BY 로 정렬하면 무슨 순서가 나오는지 본다.

1) 파일 이름을 그대로 정렬하면 — img10 이 img2 보다 앞에 오는가
2) 문자열 '10' 과 '9' 는 어느 쪽이 작은가, 숫자 10 과 9 는
3) 숫자만 든 문자열은 CAST 로 정수로 바꿔 정렬한다
4) CAST 는 숫자가 아닌 글자를 만나면 무엇을 돌려주는가
5) 길이 먼저 정렬 — 앞자리 0 이 있으면 무너진다
6) 접두어와 숫자를 떼어 정렬한다 (자연 정렬)
7) 버전 문자열을 점으로 세 토막 내어 정렬한다
8) 정렬 식에 인덱스를 걸면 정렬 단계(TEMP B-TREE)가 없어지는가
"""
import sqlite3

from dbshow import print_dataset, print_environment

# 접두어: 끝의 숫자를 걷어낸 나머지. 숫자: 접두어 뒤를 정수로 바꾼 값
PREFIX_EXPR = "rtrim(file_name, '0123456789')"
NUMBER_EXPR = (
    "CAST(substr(file_name, length(rtrim(file_name, '0123456789')) + 1) AS INTEGER)"
)


def build_database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE scan_file (
            file_id   INTEGER PRIMARY KEY,
            file_name TEXT    NOT NULL
        );
        INSERT INTO scan_file (file_id, file_name) VALUES
            (1, 'img1'), (2, 'img2'), (3, 'img10'), (4, 'img9'),
            (5, 'img100'), (6, 'img20'), (7, 'doc3'), (8, 'doc12'),
            (9, 'img007'), (10, 'img7');

        CREATE TABLE ticket (
            ticket_id INTEGER PRIMARY KEY,
            ticket_no TEXT    NOT NULL
        );
        INSERT INTO ticket (ticket_id, ticket_no) VALUES
            (1, '9'), (2, '10'), (3, '100'), (4, '25'), (5, '007'), (6, '12A');

        CREATE TABLE app_release (
            release_id INTEGER PRIMARY KEY,
            version    TEXT    NOT NULL
        );
        INSERT INTO app_release (release_id, version) VALUES
            (1, '1.2.0'), (2, '1.10.0'), (3, '1.9.3'),
            (4, '2.0.0'), (5, '1.10.12'), (6, '1.10.2');
        """
    )
    return conn


def column_values(conn, sql):
    print("  sql> " + " ".join(sql.split()))
    rows = conn.execute(sql).fetchall()
    print("  결과: " + ", ".join(str(row[0]) for row in rows))


def show_rows(conn, sql):
    print("  sql> " + " ".join(sql.split()))
    for row in conn.execute(sql):
        print("   ", row)


def plan(conn, sql):
    """sqlite3 CLI 의 .eqp 와 같은 트리 모양으로 찍는다 (|-- 와 `--)."""
    print("  plan> " + " ".join(sql.split()))
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    children = {}
    for node_id, parent_id, _, detail in rows:
        children.setdefault(parent_id, []).append((node_id, detail))

    def draw(parent_id, indent):
        siblings = children.get(parent_id, [])
        for position, (node_id, detail) in enumerate(siblings):
            is_last = position == len(siblings) - 1
            print(f"    {indent}{'`--' if is_last else '|--'}{detail}")
            draw(node_id, indent + ("   " if is_last else "|  "))

    print("    QUERY PLAN")
    draw(0, "")


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)

    print("\n[1] 파일 이름을 그대로 정렬한다")
    column_values(conn, "SELECT file_name FROM scan_file ORDER BY file_name")

    print("\n[2] 문자열 비교와 숫자 비교")
    show_rows(conn, "SELECT '10' < '9', 10 < 9, typeof('10'), typeof(10)")

    print("\n[3] 숫자만 든 문자열: 그대로 vs CAST")
    column_values(conn, "SELECT ticket_no FROM ticket ORDER BY ticket_no")
    column_values(
        conn, "SELECT ticket_no FROM ticket ORDER BY CAST(ticket_no AS INTEGER)"
    )

    print("\n[4] CAST 가 돌려주는 값")
    show_rows(
        conn,
        "SELECT CAST('12A' AS INTEGER), CAST('A12' AS INTEGER), "
        "CAST('007' AS INTEGER), CAST('1.10.2' AS INTEGER)",
    )

    print("\n[5] 길이 먼저 정렬")
    column_values(
        conn, "SELECT ticket_no FROM ticket ORDER BY length(ticket_no), ticket_no"
    )

    print("\n[6] 접두어와 숫자를 떼어 정렬한다")
    show_rows(
        conn,
        f"SELECT file_name, {PREFIX_EXPR} AS prefix, {NUMBER_EXPR} AS num "
        "FROM scan_file WHERE file_id IN (3, 7, 9, 10)",
    )
    # img7 과 img007 은 접두어도 숫자도 같다. 둘 사이 순서는 정해져 있지 않다
    column_values(
        conn,
        f"SELECT file_name FROM scan_file ORDER BY {PREFIX_EXPR}, {NUMBER_EXPR}",
    )
    column_values(
        conn,
        f"SELECT file_name FROM scan_file "
        f"ORDER BY {PREFIX_EXPR}, {NUMBER_EXPR}, file_name",
    )

    print("\n[7] 버전 문자열을 세 토막으로 나눈다")
    column_values(conn, "SELECT version FROM app_release ORDER BY version")
    version_sql = """
        WITH part AS (
            SELECT version,
                   substr(version, instr(version, '.') + 1) AS rest
            FROM app_release
        )
        SELECT version,
               CAST(version AS INTEGER)                          AS major,
               CAST(rest AS INTEGER)                             AS minor,
               CAST(substr(rest, instr(rest, '.') + 1) AS INTEGER) AS patch
        FROM part
        ORDER BY major, minor, patch
    """
    show_rows(conn, version_sql)

    print("\n[8] 정렬 식과 인덱스")
    conn.execute("CREATE INDEX idx_scan_file_name ON scan_file (file_name)")
    plan(conn, "SELECT file_name FROM scan_file ORDER BY file_name")
    natural_sql = (
        f"SELECT file_name FROM scan_file ORDER BY {PREFIX_EXPR}, {NUMBER_EXPR}"
    )
    plan(conn, natural_sql)
    conn.execute(
        f"CREATE INDEX idx_scan_file_natural ON scan_file ({PREFIX_EXPR}, {NUMBER_EXPR})"
    )
    plan(conn, natural_sql)
    # 식을 한 글자라도 다르게 쓰면 인덱스와 같은 식으로 보지 않는다
    plan(
        conn,
        "SELECT file_name FROM scan_file ORDER BY rtrim(file_name, '9876543210'), "
        + NUMBER_EXPR,
    )


if __name__ == "__main__":
    main()
