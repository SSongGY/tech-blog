"""사가 패턴에서 보상 트랜잭션이 어디서 무너지는지 돌려 본다.

실행:
    python saga.py

주문 한 건을 결제 → 재고 확보 → 배송 예약 세 단계로 처리한다. 각 단계에는
되돌리는 보상 단계가 붙어 있다. 실패 지점을 바꿔 가며 다섯 가지 상황을 본다.

난수는 쓰지 않는다. 실패는 전부 인자로 지정한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

INITIAL_BALANCE = 100_000
INITIAL_STOCK = 3
PRICE = 30_000
RETRY_LIMIT = 3


class ServiceError(Exception):
    """원격 서비스가 거부했거나 응답하지 않은 상황."""


@dataclass
class Store:
    """세 서비스의 상태를 한곳에 모아 둔 것. 각 줄이 다른 서비스라고 보면 된다."""

    balance: int = INITIAL_BALANCE
    stock: int = INITIAL_STOCK
    shipments: set[str] = field(default_factory=set)
    applied: set[tuple[str, str]] = field(default_factory=set)
    log: list[str] = field(default_factory=list)

    def snapshot(self) -> str:
        return (f"잔액 {self.balance:>7,} · 재고 {self.stock} · "
                f"배송 {len(self.shipments)}건")

    def record(self, line: str) -> None:
        self.log.append(line)
        print(f"      {line}")


# --- 각 서비스의 정상 동작과 보상 동작 -------------------------------------

def charge(store: Store, order_id: str) -> None:
    if store.balance < PRICE:
        raise ServiceError("잔액 부족")
    store.balance -= PRICE
    store.record(f"결제    -{PRICE:,}  → {store.snapshot()}")


def refund(store: Store, order_id: str, *, idempotent: bool = True) -> None:
    key = ("refund", order_id)
    if idempotent and key in store.applied:
        store.record(f"환불    건너뜀 (이미 처리된 키 {key[1]})")
        return
    store.applied.add(key)
    store.balance += PRICE
    store.record(f"환불    +{PRICE:,}  → {store.snapshot()}")


def reserve_stock(store: Store, order_id: str) -> None:
    if store.stock <= 0:
        raise ServiceError("재고 없음")
    store.stock -= 1
    store.record(f"재고확보 -1       → {store.snapshot()}")


def release_stock(store: Store, order_id: str, *, idempotent: bool = True) -> None:
    key = ("release", order_id)
    if idempotent and key in store.applied:
        store.record(f"재고반납 건너뜀 (이미 처리된 키 {key[1]})")
        return
    store.applied.add(key)
    store.stock += 1
    store.record(f"재고반납 +1       → {store.snapshot()}")


def book_shipment(store: Store, order_id: str) -> None:
    store.shipments.add(order_id)
    store.record(f"배송예약 {order_id}   → {store.snapshot()}")


def cancel_shipment(store: Store, order_id: str, *, idempotent: bool = True) -> None:
    store.shipments.discard(order_id)
    store.record(f"배송취소 {order_id}   → {store.snapshot()}")


@dataclass
class Step:
    name: str
    action: Callable[[Store, str], None]
    compensation: Callable[..., None]


STEPS = [
    Step("결제", charge, refund),
    Step("재고 확보", reserve_stock, release_stock),
    Step("배송 예약", book_shipment, cancel_shipment),
]


def run_saga(
    store: Store,
    order_id: str,
    *,
    fail_step: str | None = None,
    failing_compensations: dict[str, int] | None = None,
    idempotent_compensation: bool = True,
) -> str:
    """사가를 끝까지 돌리고 결과 문자열을 돌려준다.

    failing_compensations 는 {단계 이름: 연속 실패 횟수} 다. 지정한 횟수만큼
    보상이 예외를 내고, 그 뒤에는 성공한다. 재시도로 복구되는 경우와 끝내
    복구되지 않는 경우를 같은 코드로 보이기 위한 장치다.
    """
    failing = dict(failing_compensations or {})
    done: list[Step] = []

    for step in STEPS:
        try:
            step.action(store, order_id)
        except ServiceError as exc:
            store.record(f"[실패] {step.name}: {exc}")
            return compensate(store, order_id, done, failing, idempotent_compensation)
        if step.name == fail_step:
            store.record(f"[실패] {step.name}: 응답 없음 (타임아웃)")
            # 타임아웃은 '안 됐다'가 아니라 '모른다'다. 동작은 이미 반영됐으므로
            # 이 단계까지 포함해 되돌려야 한다.
            done.append(step)
            return compensate(store, order_id, done, failing, idempotent_compensation)
        done.append(step)

    store.record("[완료] 세 단계 모두 성공")
    return "완료"


def compensate(
    store: Store,
    order_id: str,
    done: list[Step],
    failing: dict[str, int],
    idempotent: bool,
) -> str:
    """수행된 단계를 역순으로 되돌린다. 보상 자체가 실패하면 재시도한다."""
    pending: list[str] = []

    for step in reversed(done):
        for attempt in range(1, RETRY_LIMIT + 1):
            if failing.get(step.name, 0) > 0:
                failing[step.name] -= 1
                store.record(f"[보상 실패] {step.name} {attempt}차 시도 — 서비스 무응답")
                continue
            step.compensation(store, order_id, idempotent=idempotent)
            break
        else:
            store.record(f"[보류] {step.name} 보상을 {RETRY_LIMIT}회 모두 실패 — 사람이 처리할 큐로")
            pending.append(step.name)

    if pending:
        return f"보상 미완료 ({', '.join(pending)})"
    return "보상 완료"


def scenario(title: str, note: str) -> Store:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)
    print(f"  {note}")
    store = Store()
    print(f"      시작    {store.snapshot()}")
    return store


def main() -> None:
    store = scenario("1. 정상 흐름", "세 단계가 모두 성공하면 보상은 돌지 않는다")
    print(f"  결과: {run_saga(store, 'ORD-1')}")
    print(f"  최종: {store.snapshot()}")

    store = scenario("2. 마지막 단계 실패", "수행된 단계를 역순으로 되돌린다")
    print(f"  결과: {run_saga(store, 'ORD-2', fail_step='배송 예약')}")
    print(f"  최종: {store.snapshot()}  ← 시작 상태로 돌아왔다")

    store = scenario("3. 보상이 두 번 실패한 뒤 성공",
                     "재시도가 있으면 일시적 장애는 넘어간다")
    print(f"  결과: {run_saga(store, 'ORD-3', fail_step='배송 예약', failing_compensations={'재고 확보': 2})}")
    print(f"  최종: {store.snapshot()}")

    store = scenario("4. 보상이 끝내 실패",
                     "되돌릴 수 없는 상태가 남는다. 사가는 여기서 사람에게 넘긴다")
    print(f"  결과: {run_saga(store, 'ORD-4', fail_step='배송 예약', failing_compensations={'결제': 5})}")
    print(f"  최종: {store.snapshot()}  ← 재고는 돌아왔는데 돈은 안 돌아왔다")

    store = scenario("5. 멱등하지 않은 보상을 두 번 돌림",
                     "재시도 프레임워크가 같은 보상을 두 번 보내면 어떻게 되는가")
    run_saga(store, 'ORD-5', fail_step='배송 예약', idempotent_compensation=False)
    print("  ─ 같은 보상 메시지가 중복 배달됐다고 하자")
    release_stock(store, 'ORD-5', idempotent=False)
    refund(store, 'ORD-5', idempotent=False)
    print(f"  최종: {store.snapshot()}  ← 재고와 잔액이 시작값을 넘었다")

    store = scenario("5-1. 같은 상황, 멱등 키를 쓴 보상",
                     "처리한 키를 기억하면 중복 배달이 상태를 넘기지 않는다")
    run_saga(store, 'ORD-6', fail_step='배송 예약', idempotent_compensation=True)
    print("  ─ 같은 보상 메시지가 중복 배달됐다고 하자")
    release_stock(store, 'ORD-6', idempotent=True)
    refund(store, 'ORD-6', idempotent=True)
    print(f"  최종: {store.snapshot()}  ← 시작 상태 그대로")

    store = scenario("6. 보상 전에 다른 주문이 끼어든다",
                     "사가는 중간 상태를 커밋한다. 그 사이에 남이 읽는다")
    charge(store, 'ORD-7')
    reserve_stock(store, 'ORD-7')
    print(f"  ─ 여기서 다른 손님이 재고를 묻는다 → {store.stock}개")
    print("  ─ ORD-7 은 곧 실패해 재고를 반납할 것이지만, 지금 답은 그 사실을 모른다")
    store.record("[실패] 배송 예약: 응답 없음 (타임아웃)")
    release_stock(store, 'ORD-7')
    refund(store, 'ORD-7')
    print(f"  최종: {store.snapshot()}  ← 되돌아왔지만, 그 사이의 답은 이미 나갔다")
    print()


if __name__ == "__main__":
    main()
