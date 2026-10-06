"""같은 주문 이벤트 6건을 세 방식으로 저장하고, 스키마를 언제 강제하느냐가 무엇을 바꾸는지 본다.

- 웨어하우스: 적재할 때 스키마를 강제한다 (schema-on-write). SQLite STRICT 표로 흉내 낸다
- 레이크: 파일을 그대로 둔다. 읽는 쪽이 스키마를 정한다 (schema-on-read)
- 레이크하우스: 파일은 레이크처럼 두되, 트랜잭션 로그가 "어느 파일이 몇 번 버전의 표인가"와
  스키마를 들고 있다. 쓸 때 로그의 스키마로 검사하고, 읽을 때 로그로 파일 목록을 정한다

실제 제품을 돌린 것이 아니라 개념을 표준 라이브러리로 옮긴 모형이다.
"""

import json
import os
import sqlite3
import tempfile
from pathlib import Path

# 2번은 금액에 쉼표가 섞였고, 4번은 금액이 없고, 5번은 원천에 없던 coupon 필드가 붙었다
EVENTS = [
    {"order_id": 1, "amount": 12000, "ordered_at": "2026-10-01"},
    {"order_id": 2, "amount": "15,000", "ordered_at": "2026-10-01"},
    {"order_id": 3, "amount": 8000, "ordered_at": "2026-10-02"},
    {"order_id": 4, "ordered_at": "2026-10-02"},
    {"order_id": 5, "amount": 30000, "ordered_at": "2026-10-03", "coupon": "WELCOME"},
    {"order_id": 6, "amount": 5000, "ordered_at": "2026-10-03"},
]
SCHEMA = {"order_id": int, "amount": int, "ordered_at": str}


def warehouse() -> None:
    print("\n== 1. 웨어하우스 — 적재할 때 검사 ==")
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE TABLE orders (order_id INTEGER PRIMARY KEY, amount INTEGER NOT NULL,"
                     " ordered_at TEXT NOT NULL) STRICT")
        for event in EVENTS:
            row = (event.get("order_id"), event.get("amount"), event.get("ordered_at"))
            try:
                conn.execute("INSERT INTO orders VALUES (?, ?, ?)", row)
            except sqlite3.Error as exc:
                print(f"   적재 거부 order_id={row[0]}: {exc}")
        count, total = conn.execute("SELECT COUNT(*), SUM(amount) FROM orders").fetchone()
        print(f"   적재 {count}건 · SUM(amount) = {total}")
        print("   coupon 컬럼은 표에 없으므로 5번의 coupon 값은 적재 단계에서 버려졌다")
    finally:
        conn.close()


def read_lake(lake_dir: Path, parse_amount) -> tuple[int, int, int]:
    rows = skipped = total = 0
    for path in sorted(lake_dir.glob("*.json")):
        for line in path.read_text(encoding="utf-8").splitlines():
            amount = parse_amount(json.loads(line).get("amount"))
            if amount is None:
                skipped += 1
                continue
            rows += 1
            total += amount
    return rows, skipped, total


def strict_reader(value):
    return value if isinstance(value, int) else None


def lenient_reader(value):
    if isinstance(value, str):
        return int(value.replace(",", ""))
    return value if isinstance(value, int) else 0


def lake(base: Path) -> None:
    print("\n== 2. 레이크 — 그대로 쓰고, 읽는 쪽이 정한다 ==")
    lake_dir = base / "lake"
    lake_dir.mkdir()
    for event in EVENTS:
        (lake_dir / f"part-{event['order_id']}.json").write_text(json.dumps(event), encoding="utf-8")
    print(f"   쓰기: {len(list(lake_dir.glob('*.json')))}개 파일 전부 받아들였다")
    for name, reader in (("팀 A(정수만 인정)", strict_reader), ("팀 B(쉼표 제거, 없으면 0)", lenient_reader)):
        rows, skipped, total = read_lake(lake_dir, reader)
        print(f"   읽기 {name}: {rows}건 집계 · {skipped}건 건너뜀 · 합계 {total}")

    # 하루치(10-03) 파일을 고쳐 다시 쓰는 도중에 다른 사람이 읽으면
    (lake_dir / "part-5.json").unlink()
    (lake_dir / "part-6.json").unlink()
    rows, _, total = read_lake(lake_dir, lenient_reader)
    print(f"   10-03 파일을 지우고 새 파일을 쓰기 전에 읽으면: {rows}건 · 합계 {total}")


class LakehouseTable:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.log_dir = root / "_log"
        self.log_dir.mkdir(parents=True)
        self._commit([{"metaData": {"schema": {k: v.__name__ for k, v in SCHEMA.items()}}}])

    def _commit(self, actions: list[dict]) -> int:
        version = len(list(self.log_dir.glob("*.json")))
        # 같은 번호를 두 작성자가 만들지 못하게 한다 — 이미 있으면 FileExistsError
        fd = os.open(self.log_dir / f"{version:05d}.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        with os.fdopen(fd, "w", encoding="utf-8") as log:
            log.write("\n".join(json.dumps(a) for a in actions))
        return version

    def _replay(self, version: int) -> tuple[dict, set[str]]:
        schema, files = {}, set()
        for path in sorted(self.log_dir.glob("*.json"))[: version + 1]:
            for line in path.read_text(encoding="utf-8").splitlines():
                action = json.loads(line)
                if "metaData" in action:
                    schema = action["metaData"]["schema"]
                files |= {action["add"]} if "add" in action else set()
                files -= {action["remove"]} if "remove" in action else set()
        return schema, files

    def latest(self) -> int:
        return len(list(self.log_dir.glob("*.json"))) - 1

    def write(self, events: list[dict], replace: set[str] = frozenset()) -> int:
        schema, _ = self._replay(self.latest())
        good = [e for e in events
                if set(e) == set(schema) and all(type(e[k]).__name__ == t for k, t in schema.items())]
        for bad in (e for e in events if e not in good):
            print(f"   쓰기 거부 order_id={bad.get('order_id')}: 스키마 {schema} 와 다르다")
        name = f"data-{self.latest() + 1}.json"
        (self.root / name).write_text("\n".join(json.dumps(e) for e in good), encoding="utf-8")
        actions = [{"remove": f} for f in sorted(replace)] + [{"add": name}]
        return self._commit(actions)

    def read(self, version: int) -> tuple[int, int]:
        _, files = self._replay(version)
        rows = [json.loads(line) for f in sorted(files)
                for line in (self.root / f).read_text(encoding="utf-8").splitlines()]
        return len(rows), sum(r["amount"] for r in rows)


def lakehouse(base: Path) -> None:
    print("\n== 3. 레이크하우스 — 로그가 스키마와 파일 목록을 든다 ==")
    table = LakehouseTable(base / "lakehouse")
    v1 = table.write(EVENTS)
    print(f"   버전 {v1} 커밋 · 읽기: {table.read(v1)[0]}건 · 합계 {table.read(v1)[1]}")
    fixed = [{"order_id": 2, "amount": 15000, "ordered_at": "2026-10-01"},
             {"order_id": 4, "amount": 9000, "ordered_at": "2026-10-02"}]
    # 고친 행을 담은 새 파일을 써 두기만 하고, 로그에 커밋하기 전에 읽으면 어떻게 보이는가
    (base / "lakehouse" / "data-2.json").write_text("\n".join(json.dumps(e) for e in fixed), encoding="utf-8")
    print(f"   새 파일을 썼지만 커밋 전에 읽으면: {table.read(table.latest())[0]}건 · 합계 {table.read(table.latest())[1]}")
    (base / "lakehouse" / "data-2.json").unlink()
    v2 = table.write(fixed)
    print(f"   버전 {v2} 커밋 · 읽기: {table.read(v2)[0]}건 · 합계 {table.read(v2)[1]}")
    print(f"   버전 {v1} 을 다시 읽으면(시간 여행): {table.read(v1)[0]}건 · 합계 {table.read(v1)[1]}")
    try:
        os.open(table.log_dir / f"{v2:05d}.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    except FileExistsError:
        print(f"   같은 버전 {v2} 를 다른 작성자가 또 만들려 하면: FileExistsError — 한쪽만 커밋된다")
    print(f"   로그 파일: {', '.join(p.name for p in sorted(table.log_dir.glob('*.json')))}")


def main() -> None:
    print("원천 이벤트 6건")
    for event in EVENTS:
        print(f"   {json.dumps(event, ensure_ascii=False)}")
    warehouse()
    with tempfile.TemporaryDirectory() as tmp:
        lake(Path(tmp))
        lakehouse(Path(tmp))


if __name__ == "__main__":
    main()
