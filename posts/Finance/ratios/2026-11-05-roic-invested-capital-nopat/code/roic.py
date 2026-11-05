"""가상 회사 가나전자·다라물산의 ROIC 계산.

영업이익·매출·세율·이자율은 같고, 사업에 묶인 자본(투하자본)만 다르다.
금액 단위는 억원이며 모든 숫자는 계산 원리를 보이려고 만든 가상 값이다.
"""

from dataclasses import dataclass

TAX_RATE = 0.22          # 가정. 실제 세율이 아니라 계산을 위한 값이다
INTEREST_RATE = 0.05     # 가정. 차입금 평균 이자율
ASSUMED_COST_OF_CAPITAL = 0.08  # 가정. 자본비용을 어떻게 구하는지는 이 글의 범위 밖


@dataclass
class Company:
    name: str
    revenue: float
    operating_income: float
    # 영업 쪽
    operating_current_assets: float       # 매출채권 + 재고자산
    operating_current_liabilities: float  # 매입채무 등 영업부채
    fixed_assets: float                   # 유형·무형자산(사용권자산 포함)
    # 재무 쪽
    debt: float                           # 차입금 + 리스부채
    equity: float
    cash: float                           # 영업에 쓰이지 않는 현금·단기금융상품
    prev_invested_capital: float


def invested_capital_operating(c: Company) -> float:
    return (
        c.operating_current_assets
        - c.operating_current_liabilities
        + c.fixed_assets
    )


def invested_capital_financing(c: Company) -> float:
    return c.debt + c.equity - c.cash


def nopat(c: Company) -> float:
    return c.operating_income * (1 - TAX_RATE)


def net_income(c: Company) -> float:
    interest = c.debt * INTEREST_RATE
    return (c.operating_income - interest) * (1 - TAX_RATE)


GANA = Company(
    name="가나전자", revenue=2000.0, operating_income=200.0,
    operating_current_assets=500.0, operating_current_liabilities=200.0,
    fixed_assets=1200.0, debt=800.0, equity=900.0, cash=200.0,
    prev_invested_capital=1400.0,
)
DARA = Company(
    name="다라물산", revenue=2000.0, operating_income=200.0,
    operating_current_assets=350.0, operating_current_liabilities=150.0,
    fixed_assets=300.0, debt=100.0, equity=650.0, cash=250.0,
    prev_invested_capital=480.0,
)


def print_inputs() -> None:
    print("[1] 입력 — 같은 것과 다른 것")
    print(f"  가정: 세율 {TAX_RATE:.0%}, 차입금 이자율 {INTEREST_RATE:.0%}")
    head = f"  {'항목':<26}{'가나전자':>10}{'다라물산':>10}"
    print(head)
    rows = [
        ("매출액", "revenue"), ("영업이익", "operating_income"),
        ("영업유동자산", "operating_current_assets"),
        ("영업유동부채", "operating_current_liabilities"),
        ("유형·무형자산", "fixed_assets"),
        ("차입금", "debt"), ("자본", "equity"), ("비영업 현금", "cash"),
    ]
    for label, attr in rows:
        print(f"  {label:<24}{getattr(GANA, attr):>10.1f}{getattr(DARA, attr):>10.1f}")


def print_invested_capital() -> None:
    print("\n[2] 투하자본 — 영업 쪽에서 센 값과 재무 쪽에서 센 값")
    for c in (GANA, DARA):
        op = invested_capital_operating(c)
        fin = invested_capital_financing(c)
        wc = c.operating_current_assets - c.operating_current_liabilities
        print(f"  {c.name}")
        print(f"    영업 쪽  영업운전자본 {wc:.1f} + 고정자산 {c.fixed_assets:.1f} = {op:.1f}")
        print(f"    재무 쪽  차입금 {c.debt:.1f} + 자본 {c.equity:.1f} - 현금 {c.cash:.1f} = {fin:.1f}")
        print(f"    일치 여부  {op == fin}")


def print_roic() -> None:
    print("\n[3] ROIC 와 두 갈래 분해 (기말 투하자본 기준)")
    for c in (GANA, DARA):
        ic = invested_capital_operating(c)
        n = nopat(c)
        margin = n / c.revenue
        turnover = c.revenue / ic
        avg_ic = (ic + c.prev_invested_capital) / 2
        print(f"  {c.name}")
        print(f"    NOPAT {c.operating_income:.1f} x (1 - {TAX_RATE:.2f}) = {n:.1f}")
        print(f"    ROIC = {n:.1f} / {ic:.1f} = {n / ic:.2%}")
        print(f"    분해  NOPAT 마진 {margin:.2%} x 투하자본 회전율 {turnover:.2f}회 = {margin * turnover:.2%}")
        print(f"    평균 투하자본 {avg_ic:.1f} 기준 ROIC = {n / avg_ic:.2%}")


def print_roe_comparison() -> None:
    print("\n[4] ROE 와의 대비 — 가나전자 사업은 그대로 두고 차입금 비중만 바꾼다")
    print("  투하자본 1500·NOPAT 156.0 은 고정, 차입금 + 자본 = 1700 (현금 200 차감 전)")
    print(f"  {'차입금':>8}{'자본':>8}{'순이익':>9}{'ROE':>9}{'ROIC':>9}")
    base = GANA
    total_funding = base.debt + base.equity
    for debt in (0.0, 400.0, 800.0, 1200.0):
        equity = total_funding - debt
        ni = (base.operating_income - debt * INTEREST_RATE) * (1 - TAX_RATE)
        roic = nopat(base) / invested_capital_operating(base)
        print(f"  {debt:>8.1f}{equity:>8.1f}{ni:>9.1f}{ni / equity:>9.2%}{roic:>9.2%}")


def print_spread() -> None:
    print("\n[5] 자본비용과 나란히 놓기 (자본비용은 가정값 "
          f"{ASSUMED_COST_OF_CAPITAL:.0%})")
    for c in (GANA, DARA):
        ic = invested_capital_operating(c)
        roic = nopat(c) / ic
        spread = roic - ASSUMED_COST_OF_CAPITAL
        print(f"  {c.name}  ROIC {roic:.2%} - 자본비용 {ASSUMED_COST_OF_CAPITAL:.2%}"
              f" = {spread:+.2%}p, 투하자본에 곱하면 {spread * ic:+.1f}")


def print_roe_actual() -> None:
    print("\n[6] 두 회사의 실제 ROE (기말 자본 기준)")
    for c in (GANA, DARA):
        ni = net_income(c)
        print(f"  {c.name}  순이익 {ni:.1f} / 자본 {c.equity:.1f} = {ni / c.equity:.2%}")


def main() -> None:
    print_inputs()
    print_invested_capital()
    print_roic()
    print_roe_comparison()
    print_spread()
    print_roe_actual()


if __name__ == "__main__":
    main()
