"""가상 회사 세 곳의 발생액 비율 계산.

세 회사는 당기순이익 120·감가상각비 40·평균총자산 1,000 이 모두 같다.
운전자본 증감만 다르다. 금액 단위는 억원이며 모든 숫자는 계산 원리를 보이려고
만든 가상 값이다.
"""

from dataclasses import dataclass

DAYS_IN_YEAR = 365


@dataclass
class Company:
    name: str
    net_income: float
    depreciation: float
    revenue: float
    prev_revenue: float
    receivable: float
    prev_receivable: float
    inventory_change: float
    payable_change: float
    average_total_assets: float


MABA = Company(
    name="마바화학", net_income=120.0, depreciation=40.0,
    revenue=1500.0, prev_revenue=1480.0,
    receivable=250.0, prev_receivable=245.0,
    inventory_change=3.0, payable_change=8.0, average_total_assets=1000.0,
)
SAA = Company(
    name="사아식품", net_income=120.0, depreciation=40.0,
    revenue=1500.0, prev_revenue=1200.0,
    receivable=275.0, prev_receivable=220.0,
    inventory_change=40.0, payable_change=10.0, average_total_assets=1000.0,
)
AJA = Company(
    name="아자식품", net_income=120.0, depreciation=40.0,
    revenue=1500.0, prev_revenue=1500.0,
    receivable=275.0, prev_receivable=220.0,
    inventory_change=40.0, payable_change=10.0, average_total_assets=1000.0,
)
COMPANIES = (MABA, SAA, AJA)


def receivable_change(c: Company) -> float:
    return c.receivable - c.prev_receivable


def operating_cash_flow(c: Company) -> float:
    """간접법. 순이익에서 비현금 비용을 더하고 운전자본 증감을 조정한다."""
    return (
        c.net_income
        + c.depreciation
        - receivable_change(c)
        - c.inventory_change
        + c.payable_change
    )


def accrual(c: Company) -> float:
    return c.net_income - operating_cash_flow(c)


def receivable_days(receivable: float, revenue: float) -> float:
    return receivable / revenue * DAYS_IN_YEAR


def print_inputs() -> None:
    print("[1] 입력 — 같은 것과 다른 것")
    print(f"  {'항목':<18}" + "".join(f"{c.name:>10}" for c in COMPANIES))
    rows = [
        ("당기순이익", "net_income"), ("감가상각비", "depreciation"),
        ("매출(당기)", "revenue"), ("매출(전기)", "prev_revenue"),
        ("매출채권(기말)", "receivable"), ("매출채권(기초)", "prev_receivable"),
        ("재고자산 증가", "inventory_change"), ("매입채무 증가", "payable_change"),
        ("평균총자산", "average_total_assets"),
    ]
    for label, attr in rows:
        print(f"  {label:<16}" + "".join(f"{getattr(c, attr):>10.1f}" for c in COMPANIES))


def print_cash_flow() -> None:
    print("\n[2] 간접법 — 순이익에서 영업활동 현금흐름까지")
    for c in COMPANIES:
        running = c.net_income
        print(f"  {c.name}")
        print(f"    당기순이익               {c.net_income:8.1f}   누계 {running:8.1f}")
        steps = [
            ("감가상각비 가산", c.depreciation),
            ("매출채권 증가", -receivable_change(c)),
            ("재고자산 증가", -c.inventory_change),
            ("매입채무 증가", c.payable_change),
        ]
        for label, amount in steps:
            running += amount
            print(f"    {label:<18}{amount:8.1f}   누계 {running:8.1f}")
        print(f"    영업활동 현금흐름                     {operating_cash_flow(c):8.1f}")


def print_accrual() -> None:
    print("\n[3] 발생액 = 순이익 - 영업활동 현금흐름, 평균총자산으로 나눈 비율")
    print(f"  {'':<14}{'순이익':>8}{'영업CF':>8}{'발생액':>8}{'비율':>9}")
    for c in COMPANIES:
        a = accrual(c)
        print(f"  {c.name:<12}{c.net_income:>8.1f}{operating_cash_flow(c):>8.1f}"
              f"{a:>8.1f}{a / c.average_total_assets:>9.2%}")


def print_decomposition() -> None:
    print("\n[4] 발생액을 항목으로 쪼개면 (+ 는 이익을 현금보다 키운 쪽)")
    print(f"  {'항목':<14}" + "".join(f"{c.name:>10}" for c in COMPANIES))
    parts = [
        ("감가상각비", lambda c: -c.depreciation),
        ("매출채권 증가", receivable_change),
        ("재고자산 증가", lambda c: c.inventory_change),
        ("매입채무 증가", lambda c: -c.payable_change),
    ]
    for label, fn in parts:
        print(f"  {label:<12}" + "".join(f"{fn(c):>10.1f}" for c in COMPANIES))
    print(f"  {'합계':<12}" + "".join(f"{accrual(c):>10.1f}" for c in COMPANIES))


def print_days() -> None:
    print("\n[5] 같은 발생액인데 원인이 다른 두 회사 — 매출채권 회수일수")
    for c in COMPANIES:
        prev_days = receivable_days(c.prev_receivable, c.prev_revenue)
        days = receivable_days(c.receivable, c.revenue)
        growth = c.revenue / c.prev_revenue - 1
        print(f"  {c.name}  매출 증가율 {growth:+.1%}  회수일수 {prev_days:.1f}일 -> {days:.1f}일"
              f"  (매출채권 증가 {receivable_change(c):+.1f})")


def main() -> None:
    print_inputs()
    print_cash_flow()
    print_accrual()
    print_decomposition()
    print_days()


if __name__ == "__main__":
    main()
