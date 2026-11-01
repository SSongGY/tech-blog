"""영업활동 현금흐름 기준 상환능력 지표 — 이자보상배율과 무엇이 갈리는가.

영업이익과 이자비용이 같아 이자보상배율이 똑같이 나오는 두 가상 회사를 두고,
분자를 영업활동 현금흐름으로 바꿨을 때와 분모에 1년 내 갚을 원금까지 넣었을 때
지표가 어떻게 갈리는지를 계산한다. 금액 단위는 억원이다.
"""

from dataclasses import dataclass

DAYS_IN_YEAR = 365


@dataclass
class Company:
    """간접법 현금흐름표를 만들 수 있을 만큼의 최소 항목만 둔다.

    운전자본은 잔액을 직접 넣지 않고 회전일수로 둔다. 그래야 매출이 바뀔 때
    잔액과 증감이 함께 움직여, 성장률만 바꾼 경로를 같은 가정으로 뽑을 수 있다.
    """

    name: str
    revenue: float
    prev_revenue: float
    operating_margin: float
    depreciation: float
    receivable_days: float
    inventory_days: float
    payable_days: float
    income_tax_paid: float
    interest_expense: float
    gross_debt: float
    debt_due_within_year: float

    @property
    def operating_income(self) -> float:
        return self.revenue * self.operating_margin

    @property
    def net_wc_days(self) -> float:
        return self.receivable_days + self.inventory_days - self.payable_days

    def wc_balance(self, revenue: float) -> float:
        """해당 매출 수준에서 묶여 있는 순운전자본."""
        return revenue * self.net_wc_days / DAYS_IN_YEAR

    def item_increase(self, days: float) -> float:
        """회전일수가 그대로일 때 매출 증가로 늘어나는 항목별 잔액."""
        return (self.revenue - self.prev_revenue) * days / DAYS_IN_YEAR


# 두 회사는 매출·영업이익률·이자비용·차입금이 모두 같다. 감가상각비와 운전자본
# 회전일수, 그리고 직전 해 매출만 다르게 두어 손익계산서에서는 구분되지 않는
# 차이를 만든다.
GANA = Company(
    name="가나정밀",
    revenue=2000.0,
    prev_revenue=1950.0,
    operating_margin=0.09,
    depreciation=120.0,
    receivable_days=45.0,
    inventory_days=20.0,
    payable_days=35.0,
    income_tax_paid=40.0,
    interest_expense=50.0,
    gross_debt=1000.0,
    debt_due_within_year=200.0,
)

DARA = Company(
    name="다라소재",
    revenue=2000.0,
    prev_revenue=1700.0,
    operating_margin=0.09,
    depreciation=60.0,
    receivable_days=95.0,
    inventory_days=55.0,
    payable_days=30.0,
    income_tax_paid=40.0,
    interest_expense=50.0,
    gross_debt=1000.0,
    debt_due_within_year=200.0,
)


def wc_change(c: Company) -> float:
    """운전자본 증감이 영업활동 현금흐름에 더해지는 금액.

    자산은 늘면 현금 유출, 부채는 늘면 현금 유입이므로 부호가 반대다.
    """
    return c.wc_balance(c.prev_revenue) - c.wc_balance(c.revenue)


def ocf_before_interest(c: Company) -> float:
    """이자지급을 빼기 전의 영업활동 현금흐름."""
    return c.operating_income + c.depreciation + wc_change(c) - c.income_tax_paid


def ocf(c: Company) -> float:
    """이자지급을 영업활동으로 분류했을 때의 영업활동 현금흐름.

    이 예제는 발생 이자비용과 현금 이자지급액이 같다고 둔다. 미지급이자가
    변하면 둘이 갈리고, 그 차액이 운전자본 증감에 한 줄 더 붙는다.
    """
    return ocf_before_interest(c) - c.interest_expense


def print_cash_flow_statement(c: Company) -> None:
    rows = [
        ("영업이익", c.operating_income),
        ("감가상각비 가산", c.depreciation),
        ("매출채권 증가", -c.item_increase(c.receivable_days)),
        ("재고자산 증가", -c.item_increase(c.inventory_days)),
        ("매입채무 증가", c.item_increase(c.payable_days)),
        ("법인세 납부", -c.income_tax_paid),
        ("이자 지급", -c.interest_expense),
    ]
    print(f"  {c.name}  (순운전자본 회전일수 {c.net_wc_days:,.0f}일)")
    running = 0.0
    for label, amount in rows:
        running += amount
        print(f"    {label:<14} {amount:>9,.1f}   누계 {running:>9,.1f}")
    print(f"    {'영업활동 현금흐름':<12} {'':>9}        {running:>9,.1f}")


def coverage_table(companies: list[Company]) -> None:
    header = f"  {'지표':<24}{'산식':<34}" + "".join(
        f"{c.name:>12}" for c in companies
    )
    print(header)
    print("  " + "-" * (len(header) - 2))

    metrics = [
        (
            "이자보상배율",
            "영업이익 ÷ 이자비용",
            lambda c: c.operating_income / c.interest_expense,
        ),
        (
            "현금흐름이자보상배율",
            "(OCF+이자지급) ÷ 이자비용",
            lambda c: ocf_before_interest(c) / c.interest_expense,
        ),
        (
            "부채상환비율",
            "(OCF+이자지급) ÷ (이자+원금)",
            lambda c: ocf_before_interest(c)
            / (c.interest_expense + c.debt_due_within_year),
        ),
        (
            "원금상환배율",
            "OCF ÷ 1년내 상환 원금",
            lambda c: ocf(c) / c.debt_due_within_year,
        ),
        (
            "차입금 대비 OCF",
            "OCF ÷ 총차입금 (%)",
            lambda c: ocf(c) / c.gross_debt * 100,
        ),
        (
            "상환 소요 연수",
            "총차입금 ÷ OCF (년)",
            lambda c: c.gross_debt / ocf(c),
        ),
    ]
    for label, formula, fn in metrics:
        values = "".join(f"{fn(c):>12,.2f}" for c in companies)
        print(f"  {label:<24}{formula:<34}{values}")


def growth_path(c: Company, growth: float, years: int) -> list[dict]:
    """매출이 매년 같은 비율로 늘 때 운전자본과 영업활동 현금흐름의 경로.

    회전일수·영업이익률·감가상각비·이자비용은 그대로 두고 성장률만 바꾼다.
    """
    rows = []
    revenue = c.revenue
    for year in range(1, years + 1):
        prev_revenue = revenue
        revenue = prev_revenue * (1 + growth)
        wc_increase = c.wc_balance(revenue) - c.wc_balance(prev_revenue)
        op = revenue * c.operating_margin
        before_interest = op + c.depreciation - wc_increase - c.income_tax_paid
        rows.append(
            {
                "year": year,
                "revenue": revenue,
                "operating_income": op,
                "wc_increase": wc_increase,
                "ocf": before_interest - c.interest_expense,
                "icr": op / c.interest_expense,
                "dscr": before_interest
                / (c.interest_expense + c.debt_due_within_year),
            }
        )
    return rows


def main() -> None:
    companies = [GANA, DARA]

    print("[1] 두 가상 회사의 손익 — 여기까지는 구분되지 않는다")
    print(f"  {'항목':<18}" + "".join(f"{c.name:>12}" for c in companies))
    for label, fn in [
        ("매출액", lambda c: c.revenue),
        ("영업이익", lambda c: c.operating_income),
        ("영업이익률(%)", lambda c: c.operating_margin * 100),
        ("이자비용", lambda c: c.interest_expense),
        ("총차입금", lambda c: c.gross_debt),
        ("1년내 상환 원금", lambda c: c.debt_due_within_year),
    ]:
        print(f"  {label:<18}" + "".join(f"{fn(c):>12,.1f}" for c in companies))

    print()
    print("[2] 간접법 현금흐름표 — 영업이익에서 영업활동 현금흐름까지")
    for c in companies:
        print_cash_flow_statement(c)

    print()
    print("[3] 상환능력 지표 — 분자와 분모를 바꿔 가며")
    coverage_table(companies)

    print()
    print("[4] 부채상환비율이 1.00 이 되려면 현금이 얼마나 더 있어야 하는가")
    for c in companies:
        need = c.interest_expense + c.debt_due_within_year
        have = ocf_before_interest(c)
        gap = have - need
        verdict = f"여유 {gap:,.1f}" if gap >= 0 else f"부족 {-gap:,.1f}"
        print(
            f"  {c.name}: 필요 {need:,.1f} / 현재 {have:,.1f} / {verdict} "
            f"(현재의 {need / have:,.2f}배가 있어야 1.00)"
        )

    print()
    print("[5] 성장률만 바꿨을 때 — 다라소재의 3년 경로")
    for growth in (0.00, 0.10, 0.20):
        rows = growth_path(DARA, growth, 3)
        print(f"  매출 성장률 {growth * 100:,.0f}%")
        print(
            f"    {'연차':<6}{'매출액':>10}{'영업이익':>10}"
            f"{'운전자본증가':>14}{'영업CF':>10}"
            f"{'이자보상배율':>14}{'부채상환비율':>14}"
        )
        for r in rows:
            print(
                f"    {r['year']:<6}{r['revenue']:>10,.1f}"
                f"{r['operating_income']:>10,.1f}{r['wc_increase']:>14,.1f}"
                f"{r['ocf']:>10,.1f}{r['icr']:>14,.2f}{r['dscr']:>14,.2f}"
            )


if __name__ == "__main__":
    main()
