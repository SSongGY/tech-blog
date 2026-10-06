"""멱등키로 중복 결제를 막는 세 가지 서버 구현을 같은 장애 상황에 넣어 본다.

서버 구현
  naive          : 키를 받지 않는다. 요청마다 결제한다
  check_then_act : 키를 조회해 없으면 결제하고, 끝난 뒤 키와 응답을 저장한다
  claim_first    : 결제 전에 키를 먼저 '처리 중'으로 선점한다(UNIQUE 제약).
                   요청 본문 지문을 같이 저장하고, 외부 결제사에도 같은 키를 넘긴다

장애 상황
  A. 응답이 유실돼 클라이언트가 같은 요청을 다시 보낸다
  B. 같은 키로 금액이 다른 요청이 온다
  C. 같은 키 요청 두 개가 동시에 들어온다 (버튼 두 번 클릭)
  D. 외부 결제는 끝났는데 응답을 저장하기 전에 서버가 죽는다

결제 건수는 외부 결제사(PaymentGateway)가 실제로 승인한 건수로 센다.
"""

import hashlib
import json
import sqlite3
import tempfile
import threading
from pathlib import Path

LEASE_TICKS = 30  # '처리 중' 선점이 이보다 오래되면 주인이 죽은 것으로 보고 다시 처리한다


class PaymentGateway:
    """외부 결제사 흉내. 우리 DB 트랜잭션 밖에 있으므로 함께 롤백되지 않는다."""

    def __init__(self, honors_key: bool) -> None:
        self.honors_key = honors_key
        self.charges: list[tuple[str, int]] = []
        self._by_key: dict[str, str] = {}
        self._lock = threading.Lock()
        # 첫 호출만 응답을 붙잡아 두어 "결제사 응답이 느린 동안"을 만든다
        self.hold_first = False
        self.entered = threading.Event()
        self.release = threading.Event()

    def charge(self, amount: int, key: str | None = None) -> str:
        if self.hold_first:
            self.hold_first = False
            self.entered.set()
            self.release.wait()
        with self._lock:
            if self.honors_key and key in self._by_key:
                return self._by_key[key]
            charge_id = f"ch_{len(self.charges) + 1}"
            self.charges.append((charge_id, amount))
            if key:
                self._by_key[key] = charge_id
            return charge_id


class Crash(Exception):
    """응답을 저장하기 직전에 프로세스가 죽은 상황."""


def fingerprint(body: dict) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


class PaymentServer:
    def __init__(self, mode: str, gateway: PaymentGateway, db_path: Path) -> None:
        self.mode = mode
        self.gateway = gateway
        self.db_path = db_path
        self.crash_before_save = False
        conn = self._connect()
        try:
            conn.execute("DROP TABLE IF EXISTS idempotency_key")
            conn.execute("""
CREATE TABLE idempotency_key (
    idem_key    TEXT PRIMARY KEY,
    fingerprint TEXT,
    status      TEXT NOT NULL,      -- processing | done
    started_at  INTEGER NOT NULL,
    response    TEXT
)""")
        finally:
            conn.close()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, timeout=5, isolation_level=None)

    def handle(self, key: str | None, body: dict, now: int) -> tuple[int, dict]:
        if self.mode == "naive":
            charge_id = self.gateway.charge(body["amount"])
            return 201, {"charge_id": charge_id}
        # 요청마다 연결을 따로 연다 — 스레드가 연결을 나눠 쓰지 않게
        conn = self._connect()
        try:
            if self.mode == "check_then_act":
                return self._check_then_act(conn, key, body, now)
            return self._claim_first(conn, key, body, now)
        finally:
            conn.close()

    def _check_then_act(
        self, conn: sqlite3.Connection, key: str, body: dict, now: int
    ) -> tuple[int, dict]:
        row = conn.execute(
            "SELECT response FROM idempotency_key WHERE idem_key = ?", (key,)
        ).fetchone()
        if row:
            return 201, json.loads(row[0])
        charge_id = self.gateway.charge(body["amount"])
        response = {"charge_id": charge_id}
        if self.crash_before_save:
            raise Crash
        conn.execute(
            "INSERT OR REPLACE INTO idempotency_key VALUES (?, NULL, 'done', ?, ?)",
            (key, now, json.dumps(response)),
        )
        return 201, response

    def _claim_first(
        self, conn: sqlite3.Connection, key: str, body: dict, now: int
    ) -> tuple[int, dict]:
        body_fp = fingerprint(body)
        try:
            conn.execute(
                "INSERT INTO idempotency_key VALUES (?, ?, 'processing', ?, NULL)",
                (key, body_fp, now),
            )
        except sqlite3.IntegrityError:
            stored_fp, status, started_at, response = conn.execute(
                "SELECT fingerprint, status, started_at, response "
                "FROM idempotency_key WHERE idem_key = ?",
                (key,),
            ).fetchone()
            if stored_fp != body_fp:
                return 422, {"error": "이 키는 다른 요청 본문에 이미 쓰였다"}
            if status == "done":
                return 201, json.loads(response)
            if now - started_at <= LEASE_TICKS:
                return 409, {"error": "같은 키의 요청이 아직 처리 중이다"}
            # 선점한 쪽이 죽었다 — 선점을 넘겨받아 같은 키로 다시 처리한다
            conn.execute(
                "UPDATE idempotency_key SET started_at = ? WHERE idem_key = ?",
                (now, key),
            )
        charge_id = self.gateway.charge(body["amount"], key=key)
        response = {"charge_id": charge_id}
        if self.crash_before_save:
            raise Crash
        conn.execute(
            "UPDATE idempotency_key SET status = 'done', response = ? WHERE idem_key = ?",
            (json.dumps(response), key),
        )
        return 201, response


def new_server(mode: str, workdir: Path, honors_key: bool = True) -> PaymentServer:
    return PaymentServer(mode, PaymentGateway(honors_key), workdir / f"{mode}.db")


def scenario_a(workdir: Path) -> None:
    print("\n==== A. 응답 유실 후 재시도 ====")
    body = {"order_id": "ORD-1", "amount": 30000}
    for mode in ("naive", "check_then_act", "claim_first"):
        server = new_server(mode, workdir)
        first = server.handle("key-A", body, now=0)   # 이 응답이 클라이언트에 닿지 못했다
        retry = server.handle("key-A", body, now=5)
        print(f"  {mode:<15} 첫 요청 {first}  재시도 {retry}"
              f"  → 승인 {len(server.gateway.charges)}건")


def scenario_b(workdir: Path) -> None:
    print("\n==== B. 같은 키, 다른 금액 ====")
    for mode in ("check_then_act", "claim_first"):
        server = new_server(mode, workdir)
        server.handle("key-B", {"order_id": "ORD-2", "amount": 30000}, now=0)
        second = server.handle("key-B", {"order_id": "ORD-2", "amount": 50000}, now=5)
        print(f"  {mode:<15} 두 번째(50000원) 요청 응답 {second}"
              f"  → 승인 {server.gateway.charges}")


def scenario_c(workdir: Path) -> None:
    print("\n==== C. 첫 요청이 결제사 응답을 기다리는 동안 같은 키 요청이 또 온다 ====")
    body = {"order_id": "ORD-3", "amount": 30000}
    for mode in ("check_then_act", "claim_first"):
        server = new_server(mode, workdir)
        server.gateway.hold_first = True
        first = []
        worker = threading.Thread(
            target=lambda: first.append(server.handle("key-C", body, now=0)))
        worker.start()
        server.gateway.entered.wait()      # 첫 요청이 결제사 안에 들어갈 때까지
        second = server.handle("key-C", body, now=1)
        server.gateway.release.set()
        worker.join()
        print(f"  {mode:<15} 첫 요청 {first[0]}  두 번째 요청 {second}"
              f"  → 승인 {len(server.gateway.charges)}건")


def scenario_d(workdir: Path) -> None:
    print("\n==== D. 외부 결제 후, 응답 저장 전에 서버가 죽음 ====")
    body = {"order_id": "ORD-4", "amount": 30000}
    cases = [
        ("check_then_act", True, [5]),
        ("claim_first", True, [5, 40]),
        ("claim_first", False, [5, 40]),
    ]
    for mode, honors_key, retry_times in cases:
        server = new_server(mode, workdir, honors_key=honors_key)
        server.crash_before_save = True
        try:
            server.handle("key-D", body, now=0)
        except Crash:
            pass
        server.crash_before_save = False
        if mode == "check_then_act":
            label = f"{mode} (결제사에 키를 넘기지 않음)"
        else:
            label = f"{mode} (결제사가 키를 {'인식' if honors_key else '무시'})"
        print(f"  {label}")
        for now in retry_times:
            print(f"    t={now:<3} 재시도 {server.handle('key-D', body, now=now)}")
        print(f"    → 승인 {len(server.gateway.charges)}건 {server.gateway.charges}")


def main() -> None:
    print(f"Python sqlite3 / SQLite {sqlite3.sqlite_version}")
    print(f"선점 유효 시간 LEASE_TICKS = {LEASE_TICKS}")
    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        scenario_a(workdir)
        scenario_b(workdir)
        scenario_c(workdir)
        scenario_d(workdir)


if __name__ == "__main__":
    main()
