"""리스제공자 주석 재구성 — 기업회계기준서 제1116호 문단 90·93·94·97.

가상 회사 아자리스가 금융리스 3건과 운용리스 2건을 가진 상태에서
20X5년 말 주석의 표 네 개(리스수익, 순투자 변동, 금융리스 만기분석,
운용리스 만기분석)를 계약 조건에서 직접 계산해 만든다.
"""

import platform
from dataclasses import dataclass

FAR_BUCKET = 6  # 문단 94·97: 첫 5개 연도는 연도별, 나머지는 합계


@dataclass(frozen=True)
class FinanceLease:
    name: str
    rate: float           # 내재이자율
    payment: float        # 매년 말 리스료
    remaining_open: int   # 20X5년 초 남은 리스료 횟수 (신규 계약은 0)
    remaining_close: int  # 20X5년 말 남은 리스료 횟수
    residual: float       # 리스기간 말 무보증잔존가치


@dataclass(frozen=True)
class OperatingLease:
    name: str
    payment: float
    remaining_close: int


# L3 는 20X5년 초에 개시해 6회 중 1회를 20X5년 말에 받았다
FINANCE = [
    FinanceLease("L1 물류 설비", 0.08, 20.0, 4, 3, 0.0),
    FinanceLease("L2 의료 장비", 0.07, 10.0, 9, 8, 5.0),
    FinanceLease("L3 건설 장비", 0.09, 12.0, 0, 5, 3.0),
]
L3_TERM = 6
OPERATING = [
    OperatingLease("O1 창고", 6.0, 4),
    OperatingLease("O2 사무동", 3.0, 7),
]
VARIABLE_FINANCE = 1.20    # 사용량 초과분 변동리스료 (순투자에 넣지 않은 몫)
VARIABLE_OPERATING = 0.80  # 매출 연동 임대료


def pv_payments(lease: FinanceLease, count: int) -> float:
    return sum(lease.payment / (1 + lease.rate) ** t for t in range(1, count + 1))


def pv_residual(lease: FinanceLease, count: int) -> float:
    return lease.residual / (1 + lease.rate) ** count


def net_investment(lease: FinanceLease, count: int) -> float:
    if count == 0:
        return 0.0
    return pv_payments(lease, count) + pv_residual(lease, count)


def bucket_label(year: int) -> str:
    return f"{year}년 이내" if year == 1 else (f"{year - 1}~{year}년" if year < FAR_BUCKET else "5년 초과")


def maturity(schedule: list[tuple[float, int]]) -> list[float]:
    buckets = [0.0] * FAR_BUCKET
    for payment, count in schedule:
        for t in range(1, count + 1):
            buckets[min(t, FAR_BUCKET) - 1] += payment
    return buckets


def main() -> None:
    print(f"환경: Python {platform.python_version()}")
    print("가상 회사 아자리스, 20X5년 말 기준 (단위: 억원)")
    print()

    print("[0] 계약 조건")
    print(f"  {'계약':<10}{'이자율':>6}{'연 리스료':>9}{'남은 횟수':>9}{'잔존가치':>9}")
    for lease in FINANCE:
        print(f"  {lease.name:<10}{lease.rate:>6.0%}{lease.payment:>9.2f}"
              f"{lease.remaining_close:>9}{lease.residual:>9.2f}")
    for lease in OPERATING:
        print(f"  {lease.name:<10}{'운용':>6}{lease.payment:>9.2f}{lease.remaining_close:>9}{'-':>9}")
    print()

    # 순투자 변동 (문단 93)
    opening = sum(net_investment(x, x.remaining_open) for x in FINANCE)
    new_lease = net_investment(FINANCE[2], L3_TERM)
    income_by_lease = []
    for lease in FINANCE:
        start = net_investment(lease, lease.remaining_open) if lease.remaining_open else new_lease
        income_by_lease.append(start * lease.rate)
    finance_income = sum(income_by_lease)
    collected = sum(x.payment for x in FINANCE)
    closing = sum(net_investment(x, x.remaining_close) for x in FINANCE)

    print("[1] 리스수익 (문단 90)")
    print("  금융리스")
    print(f"    매출손익                              {0.0:8.2f}  (제조·판매 리스 없음)")
    print(f"    리스순투자에 대한 금융수익            {finance_income:8.2f}")
    print(f"    순투자에 넣지 않은 변동리스료 수익    {VARIABLE_FINANCE:8.2f}")
    # 고정 리스료가 해마다 같으므로 정액 수익 = 그해 고정 리스료다
    fixed_operating = sum(x.payment for x in OPERATING)
    print("  운용리스")
    print(f"    리스수익                              {fixed_operating + VARIABLE_OPERATING:8.2f}")
    print(f"      고정 리스료 정액 인식               {fixed_operating:8.2f}")
    print(f"      지수·요율 외 변동리스료 수익        {VARIABLE_OPERATING:8.2f}  (별도 공시)")
    print()

    print("[2] 금융리스 순투자 변동 (문단 93의 양적 설명)")
    print(f"    기초 순투자                {opening:8.2f}")
    print(f"    신규 계약(L3)              {new_lease:8.2f}")
    print(f"    금융수익                   {finance_income:8.2f}")
    print(f"    리스료 수취               {-collected:8.2f}")
    print(f"    기말 순투자                {closing:8.2f}")
    print(f"    검산 기초+신규+수익-수취 = {opening + new_lease + finance_income - collected:.2f}")
    print()

    print("[3] 금융리스 만기분석과 순투자 조정 (문단 94)")
    fin_buckets = maturity([(x.payment, x.remaining_close) for x in FINANCE])
    for i, amount in enumerate(fin_buckets, start=1):
        print(f"    {bucket_label(i):<10}{amount:10.2f}")
    undiscounted = sum(fin_buckets)
    pv_pay = sum(pv_payments(x, x.remaining_close) for x in FINANCE)
    unearned = undiscounted - pv_pay
    pv_res = sum(pv_residual(x, x.remaining_close) for x in FINANCE)
    undiscounted_res = sum(x.residual for x in FINANCE)
    print("    " + "-" * 20)
    print(f"    {'할인 전 리스료 합계':<10}{undiscounted:10.2f}")
    print(f"    {'미실현 금융수익':<10}{-unearned:10.2f}")
    print(f"    {'리스료 현재가치':<10}{pv_pay:10.2f}")
    print(f"    {'할인된 무보증잔존가치':<10}{pv_res:10.2f}  (할인 전 {undiscounted_res:.2f})")
    print(f"    {'리스순투자':<10}{pv_pay + pv_res:10.2f}")
    # 부동소수 오차로 -0.00 이 찍히지 않게 반올림 뒤 절댓값을 쓴다
    print(f"    [2]의 기말 순투자와 차이 {abs(round(pv_pay + pv_res - closing, 6)):.2f}")
    print()

    print("[4] 운용리스 만기분석 (문단 97)")
    op_buckets = maturity([(x.payment, x.remaining_close) for x in OPERATING])
    for i, amount in enumerate(op_buckets, start=1):
        print(f"    {bucket_label(i):<10}{amount:10.2f}")
    print("    " + "-" * 20)
    print(f"    {'합계':<10}{sum(op_buckets):10.2f}  (재무상태표에 채권으로 없다)")
    print()

    print("[5] 만기분석에서 거꾸로 읽는 숫자")
    print(f"    미실현 금융수익 / 할인 전 리스료 = {unearned / undiscounted:.1%}")
    print(f"    다음 해 받을 금융리스료 {fin_buckets[0]:.2f} 중 이자 몫(기말 순투자 x 계약별 이자율)"
          f" = {sum(net_investment(x, x.remaining_close) * x.rate for x in FINANCE):.2f}")


if __name__ == "__main__":
    main()
