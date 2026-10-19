"""이벤트 소싱의 복원 비용이 어디서 선형으로 늘고, 스냅샷이 무엇을 못 막는지 잰다.

측정 대상은 넷이다.
  1. 스냅샷 없는 애그리거트 복원 — 이벤트 수에 따라 어떻게 늘어나는가
  2. 스냅샷을 둔 복원 — 무엇이 상한이 되는가
  3. 프로젝션(읽기 모델) 재구축 — 스냅샷이 이 비용을 줄여 주는가
  4. 이벤트 스키마가 바뀐 뒤의 업캐스팅 — 복원마다 붙는 고정 비용

시간은 환경에 따라 흔들리므로 각 측정을 REPEAT 번 돌려 최솟값을 쓴다.
최솟값을 쓰는 이유는 다른 프로세스의 간섭이 시간을 늘리기만 하기 때문이다.
"""

from __future__ import annotations

import json
import sqlite3
import time

from dbshow import print_dataset, print_environment

RULE = "=" * 72
REPEAT = 7
SNAPSHOT_EVERY = 10_000

SCHEMA = """
CREATE TABLE event_log (
    seq          INTEGER PRIMARY KEY,
    aggregate_id TEXT    NOT NULL,
    version      INTEGER NOT NULL,
    event_type   TEXT    NOT NULL,
    schema_ver   INTEGER NOT NULL DEFAULT 2,
    payload      TEXT    NOT NULL
);
CREATE INDEX idx_event_log_aggregate ON event_log (aggregate_id, version);

CREATE TABLE snapshot (
    aggregate_id TEXT    NOT NULL,
    version      INTEGER NOT NULL,
    state        TEXT    NOT NULL,
    PRIMARY KEY (aggregate_id, version)
);
"""

AGGREGATE_COUNT = 20
EVENTS_PER_AGGREGATE = 20_000


def build_store() -> sqlite3.Connection:
    """계좌 20개에 각각 2만 건, 모두 40만 건의 이벤트를 넣는다."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    rows = []
    seq = 0
    for a in range(AGGREGATE_COUNT):
        account = f"acct-{a:03d}"
        for version in range(1, EVENTS_PER_AGGREGATE + 1):
            seq += 1
            # 입금과 출금을 번갈아 넣되 잔액이 음수가 되지 않게 금액을 맞춘다
            if version % 2 == 1:
                event_type, amount = "Deposited", 300
            else:
                event_type, amount = "Withdrawn", 100
            rows.append(
                (seq, account, version, event_type, 2, json.dumps({"amount": amount}))
            )
    conn.executemany(
        "INSERT INTO event_log (seq, aggregate_id, version, event_type, "
        "schema_ver, payload) VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    return conn


def apply_event(state: dict, event_type: str, payload: dict) -> None:
    if event_type == "Deposited":
        state["balance"] += payload["amount"]
    else:
        state["balance"] -= payload["amount"]
    state["applied"] += 1


def restore(conn: sqlite3.Connection, account: str, upto: int) -> dict:
    """스냅샷 없이 1번 이벤트부터 전부 다시 적용한다."""
    state = {"balance": 0, "applied": 0}
    cur = conn.execute(
        "SELECT event_type, payload FROM event_log "
        "WHERE aggregate_id = ? AND version <= ? ORDER BY version",
        (account, upto),
    )
    for event_type, payload in cur:
        apply_event(state, event_type, json.loads(payload))
    return state


def restore_with_snapshot(conn: sqlite3.Connection, account: str, upto: int) -> dict:
    """가장 가까운 스냅샷을 읽고 그 뒤 이벤트만 적용한다."""
    row = conn.execute(
        "SELECT version, state FROM snapshot WHERE aggregate_id = ? AND version <= ? "
        "ORDER BY version DESC LIMIT 1",
        (account, upto),
    ).fetchone()
    if row is None:
        state = restore(conn, account, upto)
        state["tail"] = state["applied"]
        return state
    base_version, state_json = row
    state = json.loads(state_json)
    before = state["applied"]
    cur = conn.execute(
        "SELECT event_type, payload FROM event_log WHERE aggregate_id = ? "
        "AND version > ? AND version <= ? ORDER BY version",
        (account, base_version, upto),
    )
    for event_type, payload in cur:
        apply_event(state, event_type, json.loads(payload))
    state["tail"] = state["applied"] - before
    return state


def write_snapshots(conn: sqlite3.Connection) -> int:
    """SNAPSHOT_EVERY 건마다 스냅샷을 남긴다."""
    made = 0
    for a in range(AGGREGATE_COUNT):
        account = f"acct-{a:03d}"
        state = {"balance": 0, "applied": 0}
        cur = conn.execute(
            "SELECT version, event_type, payload FROM event_log "
            "WHERE aggregate_id = ? ORDER BY version",
            (account,),
        )
        for version, event_type, payload in cur:
            apply_event(state, event_type, json.loads(payload))
            if version % SNAPSHOT_EVERY == 0:
                conn.execute(
                    "INSERT INTO snapshot (aggregate_id, version, state) VALUES (?, ?, ?)",
                    (account, version, json.dumps(state)),
                )
                made += 1
    conn.commit()
    return made


def rebuild_projection(conn: sqlite3.Connection) -> dict:
    """읽기 모델 재구축 — 저장소의 모든 이벤트를 처음부터 훑는다.

    스냅샷은 애그리거트 하나의 상태를 되살리려고 둔 것이라 이 경로에서는
    읽히지 않는다. 읽은 이벤트 수를 같이 돌려줘서 그것을 눈으로 확인한다.
    """
    totals: dict[str, int] = {}
    read = 0
    cur = conn.execute(
        "SELECT aggregate_id, event_type, payload FROM event_log ORDER BY seq"
    )
    for account, event_type, payload in cur:
        read += 1
        amount = json.loads(payload)["amount"]
        totals[account] = totals.get(account, 0) + (
            amount if event_type == "Deposited" else -amount
        )
    return {"read": read, "accounts": len(totals)}


def upcast(schema_ver: int, payload: dict) -> dict:
    """v1 은 금액을 문자열 필드 amount_str 에 담았다. v2 모양으로 올린다."""
    if schema_ver >= 2:
        return payload
    return {"amount": int(payload["amount_str"])}


def restore_with_upcast(conn: sqlite3.Connection, account: str, upto: int) -> dict:
    state = {"balance": 0, "applied": 0}
    cur = conn.execute(
        "SELECT event_type, schema_ver, payload FROM event_log "
        "WHERE aggregate_id = ? AND version <= ? ORDER BY version",
        (account, upto),
    )
    for event_type, schema_ver, payload in cur:
        apply_event(state, event_type, upcast(schema_ver, json.loads(payload)))
    return state


def add_legacy_aggregate(conn: sqlite3.Connection) -> str:
    """v1 로 쓰인 옛 이벤트와 v2 로 쓰인 새 이벤트가 섞인 계좌를 하나 만든다."""
    account = "acct-legacy"
    base = conn.execute("SELECT MAX(seq) FROM event_log").fetchone()[0]
    rows = [
        (base + 1, account, 1, "Deposited", 1, json.dumps({"amount_str": "500"})),
        (base + 2, account, 2, "Withdrawn", 1, json.dumps({"amount_str": "200"})),
        (base + 3, account, 3, "Deposited", 2, json.dumps({"amount": 300})),
    ]
    conn.executemany(
        "INSERT INTO event_log (seq, aggregate_id, version, event_type, "
        "schema_ver, payload) VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    return account


def best(fn, *args) -> tuple[float, object]:
    """예열 1회 뒤 REPEAT 번 재고 최솟값을 돌려준다.

    예열이 없으면 첫 호출이 SQLite 페이지 캐시를 채우는 비용까지 안고 가서,
    나중에 같은 데이터를 읽는 쪽이 부당하게 빨라 보인다.

    이 환경에서는 같은 일이 간헐적으로 2.7배까지 느려지는 구간이 관측됐다
    (하이브리드 CPU 의 코어 이동으로 보인다). 그래서 반복 횟수를 늘리고
    평균이 아니라 최솟값을 쓴다.
    """
    fn(*args)
    elapsed = []
    result = None
    for _ in range(REPEAT):
        start = time.perf_counter()
        result = fn(*args)
        elapsed.append(time.perf_counter() - start)
    return min(elapsed), result


def main() -> None:
    print_environment({"반복": f"{REPEAT}회 중 최솟값"})
    conn = build_store()
    print_dataset(conn)

    print(RULE)
    print("1. 스냅샷 없는 복원 — 이벤트 수를 늘려 가며")
    print(RULE)
    print("  적용 이벤트 수   복원 시간(ms)   이벤트당(마이크로초)   잔액")
    baseline = None
    for upto in (2_500, 5_000, 10_000, 20_000):
        seconds, state = best(restore, conn, "acct-000", upto)
        if baseline is None:
            baseline = seconds / upto
        print(
            f"  {upto:14,d}   {seconds * 1000:13.1f}   {seconds / upto * 1e6:20.3f}"
            f"   {state['balance']:,}"
        )
    print()

    print(RULE)
    print(f"2. {SNAPSHOT_EVERY:,}건마다 스냅샷을 둔 복원")
    print(RULE)
    made = write_snapshots(conn)
    print(f"  만들어진 스냅샷  {made}개")
    print("  복원 지점 버전   복원 시간(ms)   스냅샷 뒤로 적용한 이벤트 수")
    for upto in (10_001, 12_500, 15_000, 19_999):
        seconds, state = best(restore_with_snapshot, conn, "acct-000", upto)
        print(f"  {upto:14,d}   {seconds * 1000:13.1f}   {state['tail']:27,d}")
    print()
    plain, _ = best(restore, conn, "acct-000", 19_999)
    snap, _ = best(restore_with_snapshot, conn, "acct-000", 19_999)
    print(f"  최악의 지점(19,999)  스냅샷 없음 {plain * 1000:.1f}ms → "
          f"있음 {snap * 1000:.1f}ms ({plain / snap:.1f}배)")
    print()

    print(RULE)
    print("3. 읽기 모델 재구축 — 스냅샷이 줄여 주는가")
    print(RULE)
    total_events = conn.execute("SELECT COUNT(*) FROM event_log").fetchone()[0]
    snapshots = conn.execute("SELECT COUNT(*) FROM snapshot").fetchone()[0]
    seconds, result = best(rebuild_projection, conn)
    print(f"  저장소 전체 이벤트  {total_events:,}건")
    print(f"  보관 중인 스냅샷    {snapshots}개")
    print(f"  재구축이 읽은 이벤트 {result['read']:,}건  "
          f"(= 전체의 {result['read'] / total_events * 100:.0f}%)")
    print(f"  재구축 시간         {seconds * 1000:,.1f}ms")
    print(f"  살아난 계좌 수      {result['accounts']}개")
    print("  → 스냅샷 40개가 있어도 읽은 건수가 줄지 않는다. 이 경로의 입력은")
    print("     애그리거트의 현재 상태가 아니라 '모든 이벤트의 순서'이기 때문이다.")
    print()

    print(RULE)
    print("4. 이벤트 스키마가 바뀐 뒤 — 업캐스터는 영구 부채다")
    print(RULE)
    legacy = add_legacy_aggregate(conn)
    rows = conn.execute(
        "SELECT version, schema_ver, payload FROM event_log "
        "WHERE aggregate_id = ? ORDER BY version",
        (legacy,),
    ).fetchall()
    print(f"  {legacy} 의 이벤트 (v1 2건 + v2 1건)")
    for version, schema_ver, payload in rows:
        print(f"    v{schema_ver}  version={version}  {payload}")
    print()
    try:
        restore(conn, legacy, 3)
        print("  업캐스터 없이 복원: 성공")
    except KeyError as exc:
        print(f"  업캐스터 없이 복원: KeyError {exc} — 옛 이벤트를 해석하지 못한다")
    state = restore_with_upcast(conn, legacy, 3)
    print(f"  업캐스터를 끼운 복원: 잔액 {state['balance']:,} "
          f"(500 - 200 + 300 = 600 과 일치)")
    print("  → 이벤트는 불변이라 v1 레코드는 지워지지 않는다. v1 을 아는 코드는")
    print("     그 이벤트가 저장소에 남아 있는 동안 계속 유지해야 한다.")
    print()

    print(RULE)
    print("5. 이 측정의 잡음 폭 — 위 시간들을 어느 자리까지 믿을 수 있는가")
    print(RULE)
    again, _ = best(restore, conn, "acct-000", 20_000)
    print(f"  1절의 20,000건 복원을 맨 끝에서 다시 재면  {again * 1000:.1f}ms")
    print("  → 시간은 이만큼 흔들린다. 구조적 결과(이벤트당 비용이 일정하다,")
    print("     스냅샷이 꼬리 길이를 제한한다, 재구축이 전부를 읽는다)만 글에 쓴다.")
    print()


if __name__ == "__main__":
    main()
