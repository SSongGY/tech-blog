"""이중 쓰기와 아웃박스를 같은 실패 지점에서 각각 돌려 결과를 대조한다.

DB 커밋과 메시지 발행은 서로 다른 시스템이라 하나의 원자적 단위로 묶이지 않는다.
그 사이에서 프로세스가 죽거나 브로커가 거절하면 둘의 상태가 갈라진다.
갈라지는 자리를 다섯 곳으로 나눠, 이중 쓰기와 아웃박스가 각각 어떤 결과를 내는지
직접 돌려 센다.

장애는 난수로 만들지 않고 호출할 때 지정한다. 몇 번을 돌려도 같은 결과가 나와야
표가 뜻을 갖기 때문이다.
"""

import sqlite3
import sys

SCHEMA = """
CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    amount   INTEGER NOT NULL
);
CREATE TABLE outbox (
    seq      INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT    NOT NULL,
    payload  TEXT    NOT NULL,
    sent_at  TEXT
);
"""

ORDER_ID = "ORD-1"
PAYLOAD = f"OrderPlaced:{ORDER_ID}"

FAILURE_POINTS = [
    ("없음", "정상 경로"),
    ("P1", "DB 커밋 직전에 죽는다"),
    ("P2", "DB 커밋 직후, 발행 직전에 죽는다"),
    ("P3", "브로커가 발행을 거절한다"),
    ("P4", "발행은 됐는데 응답을 못 받는다 (같은 메시지를 다시 보낸다)"),
    ("P5", "발행을 먼저 하고 DB 커밋이 실패한다"),
]


class Crash(Exception):
    """프로세스가 그 자리에서 죽은 것으로 친다."""


class BrokerRejected(Exception):
    """브로커가 발행을 거절했다."""


class Broker:
    def __init__(self):
        self.published = []

    def publish(self, order_id, payload, *, reject=False, lose_ack=False):
        if reject:
            raise BrokerRejected(order_id)
        self.published.append((order_id, payload))
        if lose_ack:
            # 브로커에는 들어갔지만 보낸 쪽은 성공을 모른다
            raise Crash("ack lost")

    def count(self, order_id):
        return sum(1 for oid, _ in self.published if oid == order_id)


def new_db():
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.executescript(SCHEMA)
    return conn


# --- 이중 쓰기 ----------------------------------------------------------
def dual_write(conn, broker, point):
    if point == "P5":
        # 발행을 먼저 하는 변형. 커밋이 실패하면 주문 없는 이벤트만 남는다
        broker.publish(ORDER_ID, PAYLOAD)
        raise Crash("commit failed after publish")

    conn.execute("BEGIN")
    conn.execute("INSERT INTO orders VALUES (?, ?)", (ORDER_ID, 1000))
    if point == "P1":
        conn.execute("ROLLBACK")
        raise Crash("before commit")
    conn.execute("COMMIT")

    if point == "P2":
        raise Crash("after commit, before publish")

    broker.publish(ORDER_ID, PAYLOAD,
                   reject=(point == "P3"), lose_ack=(point == "P4"))


def dual_write_retry(conn, broker):
    """응답을 못 받았으니 보내는 쪽이 같은 메시지를 다시 보낸다."""
    broker.publish(ORDER_ID, PAYLOAD)


# --- 아웃박스 ----------------------------------------------------------
def outbox_write(conn):
    """업무 데이터와 보낼 메시지를 같은 트랜잭션에 함께 쓴다."""
    conn.execute("BEGIN")
    conn.execute("INSERT INTO orders VALUES (?, ?)", (ORDER_ID, 1000))
    conn.execute("INSERT INTO outbox (order_id, payload) VALUES (?, ?)",
                 (ORDER_ID, PAYLOAD))
    conn.execute("COMMIT")


def relay(conn, broker, point="없음"):
    """아웃박스에서 안 보낸 행을 읽어 발행하고, 발행이 끝난 뒤 보낸 표시를 남긴다."""
    rows = conn.execute(
        "SELECT seq, order_id, payload FROM outbox WHERE sent_at IS NULL ORDER BY seq"
    ).fetchall()
    for seq, order_id, payload in rows:
        broker.publish(order_id, payload,
                       reject=(point == "P3"), lose_ack=(point == "P4"))
        conn.execute("UPDATE outbox SET sent_at = datetime('now') WHERE seq = ?", (seq,))


def outbox_run(conn, broker, point):
    if point == "P1":
        conn.execute("BEGIN")
        conn.execute("INSERT INTO orders VALUES (?, ?)", (ORDER_ID, 1000))
        conn.execute("ROLLBACK")
        raise Crash("before commit")

    # P5 는 이 구조에서 성립하지 않는다. 발행을 먼저 하는 선택지가 없다
    outbox_write(conn)
    if point == "P2":
        raise Crash("after commit, before relay")
    relay(conn, broker, point)


def outbox_retry(conn, broker):
    """릴레이가 다시 뜬다. 보낸 표시가 없는 행을 다시 보낸다."""
    relay(conn, broker)


# --- 판정 --------------------------------------------------------------
def verdict(in_db, events):
    if in_db and events == 0:
        return "유실"
    if not in_db and events > 0:
        return "유령"
    if in_db and events > 1:
        return "중복"
    if in_db and events == 1:
        return "일치"
    return "일치 (둘 다 없음)"


def table(headers, rows):
    widths = [max(len(h), *(len(str(r[i])) for r in rows)) for i, h in enumerate(headers)]
    print("  " + " | ".join(h.ljust(w) for h, w in zip(headers, widths)))
    print("  " + "-+-".join("-" * w for w in widths))
    for row in rows:
        print("  " + " | ".join(str(c).ljust(w) for c, w in zip(row, widths)))


def scenario(title, runner, retry_fn, skip=(), show_pending=False):
    print("\n" + "=" * 76)
    print(title)
    print("=" * 76)
    rows = []
    for point, desc in FAILURE_POINTS:
        if point in skip:
            blanks = ["—"] * (3 if show_pending else 2)
            rows.append([point, desc, *blanks, "해당 없음"])
            continue
        conn, broker = new_db(), Broker()
        try:
            runner(conn, broker, point)
        except (Crash, BrokerRejected):
            pass
        if point == "P4":
            try:
                retry_fn(conn, broker)
            except (Crash, BrokerRejected):
                pass
        in_db = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE order_id = ?", (ORDER_ID,)
        ).fetchone()[0] > 0
        events = broker.count(ORDER_ID)
        row = [point, desc, "있음" if in_db else "없음", events]
        if show_pending:
            row.append(conn.execute(
                "SELECT COUNT(*) FROM outbox WHERE sent_at IS NULL").fetchone()[0])
        row.append(verdict(in_db, events))
        rows.append(row)
        conn.close()
    headers = ["지점", "무슨 일이 일어나는가", "주문 행", "발행 건수"]
    if show_pending:
        headers.append("미전송 행")
    headers.append("그 시점의 상태")
    table(headers, rows)


def recovery():
    print("\n" + "=" * 76)
    print("3. 아웃박스에서 P2·P3 로 멈춘 뒤 릴레이가 다시 뜨면")
    print("=" * 76)
    rows = []
    for point in ("P2", "P3"):
        conn, broker = new_db(), Broker()
        try:
            outbox_run(conn, broker, point)
        except (Crash, BrokerRejected):
            pass
        before = broker.count(ORDER_ID)
        pending_before = conn.execute(
            "SELECT COUNT(*) FROM outbox WHERE sent_at IS NULL").fetchone()[0]
        relay(conn, broker)
        pending_after = conn.execute(
            "SELECT COUNT(*) FROM outbox WHERE sent_at IS NULL").fetchone()[0]
        rows.append([point, before, pending_before, broker.count(ORDER_ID), pending_after])
        conn.close()
    table(["지점", "재가동 전 발행", "재가동 전 미전송 행",
           "재가동 후 발행", "재가동 후 미전송 행"], rows)


def main():
    print("=" * 76)
    print("이중 쓰기 대 아웃박스 — 같은 실패 지점에서 무엇이 달라지는가")
    print("=" * 76)
    print("  유실 : 주문은 남았는데 이벤트가 없다")
    print("  유령 : 이벤트는 갔는데 주문이 없다")
    print("  중복 : 같은 이벤트가 두 번 갔다")

    scenario("1. 이중 쓰기 — DB 커밋과 발행을 따로 한다", dual_write, dual_write_retry)
    scenario("2. 아웃박스 — 한 트랜잭션에 함께 쓰고 릴레이가 보낸다",
             outbox_run, outbox_retry, skip=("P5",), show_pending=True)
    recovery()
    return 0


if __name__ == "__main__":
    sys.exit(main())
