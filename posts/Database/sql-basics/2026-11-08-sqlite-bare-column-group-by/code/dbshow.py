"""예제가 쓰는 표와 데이터를 출력 맨 앞에 찍어 주는 도우미.

왜 필요한가. 예제 출력만 보면 `(28,)` 같은 숫자가 왜 그 값인지 알 수 없다.
어떤 컬럼이 있고 어떤 행이 들어 있는지를 독자가 스크립트 소스까지 열어 봐야
알 수 있다면, 돌린 기록으로서 반쪽이다. 질의 결과 앞에 표 정의와 실제 행을
먼저 깔아 두면 그 아래 출력이 전부 따라 읽힌다.

**이 파일은 글 폴더의 `code/` 아래로 복사해 쓴다.** 예제는 그 자체로 돌아가야
하므로(CLAUDE.md §3) 저장소 어딘가를 import 하지 않는다. 원본은
`references/dbshow.py` 이고, 고칠 일이 있으면 원본을 고친 뒤 다시 뿌린다:

    python scripts/blog.py sync-dbshow

쓰는 쪽:

    import sqlite3
    from dbshow import print_environment, print_dataset

    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    ...
    print_environment()
    print_dataset(conn)
"""

from __future__ import annotations

import platform
import sqlite3
import unicodedata

MAX_ROWS = 12          # 이보다 많으면 앞부분만 보이고 몇 행이 더 있는지 적는다
RULE = "=" * 64


def _width(text: str) -> int:
    """한글은 터미널에서 두 칸을 차지한다. 그대로 len 으로 재면 표가 어긋난다."""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in str(text))


def _pad(text: str, width: int, *, right: bool = False) -> str:
    gap = " " * max(0, width - _width(text))
    return gap + str(text) if right else str(text) + gap


def _render(headers: list[str], rows: list[tuple], aligns: list[bool]) -> list[str]:
    """aligns[i] 가 True 면 그 칸을 오른쪽으로 붙인다 (숫자 칸)."""
    cells = [[("NULL" if v is None else str(v)) for v in row] for row in rows]
    widths = [
        max(_width(headers[i]), *(_width(r[i]) for r in cells)) if cells
        else _width(headers[i])
        for i in range(len(headers))
    ]
    out = [
        "  " + " | ".join(_pad(h, w) for h, w in zip(headers, widths)),
        "  " + "-+-".join("-" * w for w in widths),
    ]
    out += [
        "  " + " | ".join(_pad(c, w, right=a) for c, w, a in zip(row, widths, aligns))
        for row in cells
    ]
    return [line.rstrip() for line in out]


def print_environment(extra: dict[str, str] | None = None) -> None:
    print(RULE)
    print("환경")
    print(RULE)
    print(f"  SQLite  {sqlite3.sqlite_version}  (파이썬 sqlite3 모듈 내장)")
    print(f"  Python  {platform.python_version()}")
    print(f"  OS      {platform.system()} {platform.release()}")
    for key, value in (extra or {}).items():
        print(f"  {key:7s} {value}")
    print()


def print_table(conn: sqlite3.Connection, table: str, *, max_rows: int = MAX_ROWS) -> None:
    """표 하나의 컬럼 정의와 실제 행을 찍는다."""
    columns = conn.execute(f"PRAGMA table_info({table})").fetchall()
    total = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    print(f"[{table}]  {total}행")
    spec = []
    for _cid, name, decl_type, not_null, default, pk in columns:
        notes = []
        if pk:
            notes.append("PK")
        if not_null:
            notes.append("NOT NULL")
        if default is not None:
            notes.append(f"DEFAULT {default}")
        spec.append((name, decl_type or "(타입 없음)", " ".join(notes)))
    for line in _render(["컬럼", "타입", "제약"], spec, [False, False, False]):
        print(line)
    print()

    if total == 0:
        print("  (행 없음)\n")
        return

    names = [c[1] for c in columns]
    rows = conn.execute(f"SELECT * FROM {table} LIMIT {max_rows}").fetchall()
    # 숫자 컬럼은 오른쪽 정렬해야 자릿수가 눈에 들어온다
    numeric = [
        all(isinstance(r[i], (int, float)) or r[i] is None for r in rows)
        for i in range(len(names))
    ]
    for line in _render(names, rows, numeric):
        print(line)
    if total > max_rows:
        print(f"  … {total - max_rows}행 더 있음")
    print()


def print_dataset(conn: sqlite3.Connection, *, max_rows: int = MAX_ROWS) -> None:
    """예제가 만든 표를 전부 찍는다. sqlite_ 로 시작하는 내부 표는 뺀다."""
    print(RULE)
    print("스키마와 데이터 — 아래 질의는 전부 이 표를 대상으로 한다")
    print(RULE)
    tables = [
        name for (name,) in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]
    for table in tables:
        print_table(conn, table, max_rows=max_rows)

    indexes = conn.execute(
        "SELECT name, tbl_name, sql FROM sqlite_master WHERE type = 'index' "
        "AND sql IS NOT NULL ORDER BY tbl_name, name"
    ).fetchall()
    if indexes:
        print("[인덱스]")
        for line in _render(
            ["이름", "대상 표", "정의"],
            [(n, t, s.strip()) for n, t, s in indexes],
            [False, False, False],
        ):
            print(line)
        print()
