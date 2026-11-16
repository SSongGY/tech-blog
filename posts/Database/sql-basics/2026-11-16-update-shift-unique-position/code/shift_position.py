"""재생 목록의 순번(position, UNIQUE)을 한 칸씩 밀 때 무슨 일이 생기는지 본다.

1) 2번 자리에 끼워 넣으려고 position >= 2 를 +1 하면 — 실패하는가
2) 실패한 UPDATE 가 일부 행만 바꿔 놓았는가
3) 같은 UPDATE 를 행을 읽는 순서만 바꿔 돌리면 — 성공·실패가 갈리는가
4) UPDATE ... ORDER BY 로 순서를 정할 수 있는가
5) 우회 1: 음수로 한 번 뒤집었다가 되돌리기 (두 문장, 한 트랜잭션)
6) 우회 2: 큰 수를 더했다가 빼기
7) 두 행의 순번 맞바꾸기
"""
import sqlite3

from dbshow import print_dataset, print_environment


def build_database():
    # isolation_level=None: BEGIN/COMMIT 을 예제가 직접 쓴다
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.executescript(
        """
        CREATE TABLE playlist_item (
            item_id  INTEGER PRIMARY KEY,
            position INTEGER NOT NULL UNIQUE,
            title    TEXT    NOT NULL
        );
        INSERT INTO playlist_item (item_id, position, title) VALUES
            (1, 1, 'Intro'), (2, 2, 'Blue'), (3, 3, 'Rain'),
            (4, 4, 'Night'), (5, 5, 'Outro');
        """
    )
    return conn


def reset(conn):
    conn.executescript(
        """
        DELETE FROM playlist_item;
        INSERT INTO playlist_item (item_id, position, title) VALUES
            (1, 1, 'Intro'), (2, 2, 'Blue'), (3, 3, 'Rain'),
            (4, 4, 'Night'), (5, 5, 'Outro');
        """
    )


def run(conn, sql):
    print("  sql> " + " ".join(sql.split()))
    try:
        cursor = conn.execute(sql)
        print(f"  성공, 바뀐 행 {cursor.rowcount}")
    except sqlite3.Error as error:
        print(f"  {type(error).__name__}: {error}")


def plan(conn, sql):
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    for _, _, _, detail in rows:
        print(f"  plan> {detail}")


def show_items(conn):
    rows = conn.execute(
        "SELECT item_id, position, title FROM playlist_item ORDER BY position"
    ).fetchall()
    print("  item_id | position | title")
    for row in rows:
        print("  " + " | ".join(str(v) for v in row))


def visit_order(conn, sql):
    """UPDATE 가 행을 읽는 순서를 같은 WHERE 의 SELECT 로 확인한다."""
    rows = conn.execute(sql).fetchall()
    print("  읽는 순서(position): " + ", ".join(str(r[0]) for r in rows))


def main():
    conn = build_database()
    print_environment()
    print_dataset(conn)

    shift = "UPDATE playlist_item SET position = position + 1 WHERE position >= 2"

    print("[1] 2번 자리를 비우려고 position >= 2 를 +1")
    plan(conn, shift)
    visit_order(conn, "SELECT position FROM playlist_item WHERE position >= 2")
    run(conn, shift)
    print()

    print("[2] 실패한 뒤 표 상태 (일부만 바뀌었는가)")
    show_items(conn)
    print()

    print("[3-A] 인덱스를 쓰지 않게 하면 (rowid 순서로 읽는다)")
    no_index = (
        "UPDATE playlist_item NOT INDEXED SET position = position + 1 "
        "WHERE position >= 2"
    )
    plan(conn, no_index)
    run(conn, no_index)
    print()

    print("[3-B] rowid 가 position 과 반대 순서인 표에서 같은 UPDATE")
    conn.executescript(
        """
        DELETE FROM playlist_item;
        INSERT INTO playlist_item (item_id, position, title) VALUES
            (1, 5, 'Outro'), (2, 4, 'Night'), (3, 3, 'Rain'),
            (4, 2, 'Blue'), (5, 1, 'Intro');
        """
    )
    visit_order(conn, "SELECT position FROM playlist_item NOT INDEXED WHERE position >= 2")
    run(conn, no_index)
    show_items(conn)
    print()

    reset(conn)
    print("[4] UPDATE ... ORDER BY position DESC 로 순서를 정하면")
    run(
        conn,
        "UPDATE playlist_item SET position = position + 1 "
        "WHERE position >= 2 ORDER BY position DESC",
    )
    print()

    print("[5] 우회 1: 음수로 뒤집었다가 되돌린다")
    conn.execute("BEGIN")
    run(conn, "UPDATE playlist_item SET position = -(position + 1) WHERE position >= 2")
    run(conn, "UPDATE playlist_item SET position = -position WHERE position < 0")
    run(conn, "INSERT INTO playlist_item (item_id, position, title) VALUES (6, 2, 'New')")
    conn.execute("COMMIT")
    show_items(conn)
    print()

    reset(conn)
    print("[6] 우회 2: 큰 수를 더했다가 뺀다")
    conn.execute("BEGIN")
    run(conn, "UPDATE playlist_item SET position = position + 1000001 WHERE position >= 2")
    run(conn, "UPDATE playlist_item SET position = position - 1000000 WHERE position > 1000000")
    conn.execute("COMMIT")
    show_items(conn)
    print()

    reset(conn)
    print("[7-A] 두 행 맞바꾸기 — CASE 한 문장")
    run(
        conn,
        "UPDATE playlist_item SET position = CASE position WHEN 2 THEN 4 "
        "WHEN 4 THEN 2 END WHERE position IN (2, 4)",
    )
    print("[7-B] 두 행 맞바꾸기 — 비어 있는 값 0 을 거쳐 세 문장으로")
    conn.execute("BEGIN")
    run(conn, "UPDATE playlist_item SET position = 0 WHERE position = 2")
    run(conn, "UPDATE playlist_item SET position = 2 WHERE position = 4")
    run(conn, "UPDATE playlist_item SET position = 4 WHERE position = 0")
    conn.execute("COMMIT")
    show_items(conn)

    conn.close()


if __name__ == "__main__":
    main()
