"""사가(Saga)를 세 개의 독립된 SQLite DB 위에서 돌려 본다.

주문·결제·재고 서비스가 각자 DB를 갖는다고 보고, 오케스트레이터가 지역 트랜잭션
T1(주문 생성) → T2(결제) → T3(재고 차감) → T4(주문 확정)을 차례로 커밋한다. 세 DB를 묶는 트랜잭션은
없으므로, 실패하면 이미 커밋한 단계를 보상 트랜잭션 C2 → C1 으로 거꾸로 되돌린다.

확인하는 것은 세 가지다.
  A. 실행 순서가 Garcia-Molina & Salem(1987)이 보장한 두 모양 중 하나가 되는가
  B. 사가 도중에 다른 조회가 중간 상태(결제됐지만 곧 취소될 주문)를 보는가
  C. 보상을 "이전 값으로 되돌리기"로 짜면 그사이 다른 트랜잭션의 변경이 사라지는가
"""

import sqlite3
from typing import Callable

ORDER_AMOUNT = 30000
INITIAL_BALANCE = 100000


class StepFailed(Exception):
    pass


def open_services(stock_qty: int) -> dict[str, sqlite3.Connection]:
    # 서비스마다 DB를 따로 연다 — 한 커넥션으로 묶으면 사가가 아니라 그냥 트랜잭션이다
    order_db = sqlite3.connect(":memory:", isolation_level=None)
    order_db.execute("CREATE TABLE orders (order_id INTEGER PRIMARY KEY, status TEXT)")
    payment_db = sqlite3.connect(":memory:", isolation_level=None)
    payment_db.execute("CREATE TABLE account (account_id TEXT PRIMARY KEY, balance INTEGER)")
    payment_db.execute("INSERT INTO account VALUES ('A1', ?)", (INITIAL_BALANCE,))
    stock_db = sqlite3.connect(":memory:", isolation_level=None)
    stock_db.execute(
        "CREATE TABLE stock (item_id TEXT PRIMARY KEY, qty INTEGER CHECK (qty >= 0))"
    )
    stock_db.execute("INSERT INTO stock VALUES ('X', ?)", (stock_qty,))
    return {"order": order_db, "payment": payment_db, "stock": stock_db}


def local_tx(conn: sqlite3.Connection, work: Callable[[], None]) -> None:
    """한 서비스 안의 지역 트랜잭션. 여기서는 ACID가 그대로 성립한다."""
    conn.execute("BEGIN")
    try:
        work()
    except sqlite3.Error as exc:
        conn.execute("ROLLBACK")
        raise StepFailed(str(exc)) from exc
    conn.execute("COMMIT")


def snapshot(db: dict[str, sqlite3.Connection]) -> str:
    status = db["order"].execute("SELECT status FROM orders WHERE order_id = 1").fetchone()
    balance = db["payment"].execute("SELECT balance FROM account").fetchone()[0]
    qty = db["stock"].execute("SELECT qty FROM stock").fetchone()[0]
    return f"주문={status[0] if status else '없음'} 잔액={balance} 재고={qty}"


def run_saga(
    db: dict[str, sqlite3.Connection],
    after_payment: Callable[[], None] | None = None,
    refund_by_restore: bool = False,
) -> list[str]:
    trace: list[str] = []
    compensations: list[tuple[str, Callable[[], None]]] = []
    before_balance = db["payment"].execute("SELECT balance FROM account").fetchone()[0]

    def t1() -> None:
        db["order"].execute("INSERT INTO orders VALUES (1, 'PENDING')")

    def c1() -> None:
        # 지우지 않고 상태를 바꾼다 — 이미 이 주문을 본 쪽이 있으므로 흔적을 남긴다
        db["order"].execute("UPDATE orders SET status = 'CANCELLED' WHERE order_id = 1")

    def t2() -> None:
        db["payment"].execute(
            "UPDATE account SET balance = balance - ? WHERE account_id = 'A1'", (ORDER_AMOUNT,)
        )

    def c2() -> None:
        if refund_by_restore:
            db["payment"].execute(
                "UPDATE account SET balance = ? WHERE account_id = 'A1'", (before_balance,)
            )
        else:
            db["payment"].execute(
                "UPDATE account SET balance = balance + ? WHERE account_id = 'A1'",
                (ORDER_AMOUNT,),
            )

    def t3() -> None:
        db["stock"].execute("UPDATE stock SET qty = qty - 1 WHERE item_id = 'X'")

    def t4() -> None:
        db["order"].execute("UPDATE orders SET status = 'CONFIRMED' WHERE order_id = 1")

    # T1·T2 는 보상 가능, T3 는 피벗(성공하면 되돌리지 않는다), T4 는 재시도 대상
    steps = [
        ("T1", "order", t1, "C1", c1),
        ("T2", "payment", t2, "C2", c2),
        ("T3", "stock", t3, None, None),
        ("T4", "order", t4, None, None),
    ]
    for name, service, work, comp_name, comp in steps:
        try:
            local_tx(db[service], work)
        except StepFailed as exc:
            trace.append(f"{name}✗({exc})")
            for undo_name, undo in reversed(compensations):
                local_tx(db[undo_name[1]], undo)
                trace.append(undo_name[0])
            return trace
        trace.append(name)
        if comp is not None:
            compensations.append(((comp_name, service), comp))
        if name == "T2" and after_payment is not None:
            after_payment()
    return trace


def main() -> None:
    print(f"Python {__import__('sys').version.split()[0]} / SQLite {sqlite3.sqlite_version}")
    print(f"주문 금액 {ORDER_AMOUNT}, 시작 잔액 {INITIAL_BALANCE}\n")

    print("== A-1. 재고 1개 — 끝까지 간다 ==")
    db = open_services(stock_qty=1)
    print("  순서:", " → ".join(run_saga(db)))
    print("  끝  :", snapshot(db))

    print("\n== A-2. 재고 0개 — T3 가 CHECK 에 걸린다 ==")
    db = open_services(stock_qty=0)
    print("  순서:", " → ".join(run_saga(db)))
    print("  끝  :", snapshot(db))

    print("\n== B. T2 직후 다른 조회가 끼어든다 (격리 없음) ==")
    db = open_services(stock_qty=0)
    seen: list[str] = []
    run_saga(db, after_payment=lambda: seen.append(snapshot(db)))
    print("  끼어든 조회가 본 값:", seen[0])
    print("  사가가 끝난 뒤   :", snapshot(db))

    def deposit() -> None:
        # 같은 계좌에 다른 사람이 입금한다 — 사가와 무관한 정상 트랜잭션
        local_tx(
            db["payment"],
            lambda: db["payment"].execute(
                "UPDATE account SET balance = balance + 5000 WHERE account_id = 'A1'"
            ),
        )

    print("\n== C. T2 직후 5000원 입금이 커밋된 뒤 사가가 실패한다 ==")
    for label, restore in (("C-1 보상 = 금액만큼 더한다", False),
                           ("C-2 보상 = 이전 잔액으로 덮어쓴다", True)):
        db = open_services(stock_qty=0)
        trace = run_saga(db, after_payment=deposit, refund_by_restore=restore)
        print(f"  [{label}]")
        print("    순서:", " → ".join(trace))
        print("    끝  :", snapshot(db), f"(기대 잔액 {INITIAL_BALANCE + 5000})")


if __name__ == "__main__":
    main()
