"""자산관련 정부보조금의 두 가지 표시 방법이 재무제표를 어떻게 가르는지 계산한다.

기업회계기준서 제1020호 문단 24~27 은 자산관련보조금을 이연수익으로 표시하는 방법과
자산의 장부금액에서 차감하는 방법을 모두 인정한다. 당기손익 효과는 같고
재무상태표의 크기와 감가상각비가 갈린다는 것을 가상 회사로 5년간 따라간다.
"""

from dataclasses import dataclass

YEARS = 5


@dataclass(frozen=True)
class Grant:
    """단위는 억원."""

    asset_cost: float  # 설비 취득원가
    grant: float  # 수령한 자산관련 정부보조금
    life: int  # 내용연수 (잔존가치 0, 정액법)
    revenue: float  # 연간 매출액 (일정하다고 둔다)
    cash_operating_profit: float  # 감가상각·보조금 환입 전 영업이익
    other_assets: float  # 설비를 뺀 나머지 자산
    other_liabilities: float  # 이연수익을 뺀 나머지 부채
    tax_rate: float


MABA = Grant(
    asset_cost=600.0,
    grant=240.0,
    life=YEARS,
    revenue=1000.0,
    cash_operating_profit=200.0,
    other_assets=800.0,
    other_liabilities=300.0,
    tax_rate=0.0,  # 두 방법의 과세소득이 같으므로 비교에서 세금을 끈다
)


def deferred_income_method(g: Grant, year: int) -> dict[str, float]:
    """문단 26 — 보조금을 이연수익으로 두고 내용연수에 걸쳐 당기손익에 인식한다."""
    depreciation = g.asset_cost / g.life
    grant_income = g.grant / g.life
    carrying = g.asset_cost - depreciation * year
    deferred = g.grant - grant_income * year
    return _wrap(g, depreciation, grant_income, carrying, deferred)


def deduction_method(g: Grant, year: int) -> dict[str, float]:
    """문단 27 — 장부금액에서 보조금을 차감하고 감가상각비를 그만큼 줄인다."""
    net_cost = g.asset_cost - g.grant
    depreciation = net_cost / g.life
    carrying = net_cost - depreciation * year
    return _wrap(g, depreciation, 0.0, carrying, 0.0)


def _wrap(
    g: Grant, depreciation: float, grant_income: float, carrying: float, deferred: float
) -> dict[str, float]:
    operating_profit = g.cash_operating_profit - depreciation + grant_income
    net_income = operating_profit * (1 - g.tax_rate)
    assets = g.other_assets + carrying
    liabilities = g.other_liabilities + deferred
    equity = assets - liabilities
    return {
        "감가상각비": depreciation,
        "보조금 환입": grant_income,
        "영업이익": operating_profit,
        "당기순이익": net_income,
        "EBITDA": operating_profit + depreciation,
        "설비 장부금액": carrying,
        "이연수익": deferred,
        "총자산": assets,
        "총부채": liabilities,
        "자본총계": equity,
        "부채비율": liabilities / equity * 100,
        "총자산회전율": g.revenue / assets,
    }


def row(cells: list[str], widths: list[int]) -> str:
    return "".join(cell.rjust(w) for cell, w in zip(cells, widths))


def print_profit_path(g: Grant) -> None:
    print("[1] 당기손익에 닿는 경로 — 두 방법의 순효과가 같다 (단위: 억원)")
    w = [22, 14, 14]
    print(row(["연간 금액", "이연수익법", "자산차감법"], w))
    print("-" * sum(w))
    a, b = deferred_income_method(g, 1), deduction_method(g, 1)
    for key in ("감가상각비", "보조금 환입"):
        print(row([key, f"{a[key]:.1f}", f"{b[key]:.1f}"], w))
    net_a = -a["감가상각비"] + a["보조금 환입"]
    net_b = -b["감가상각비"] + b["보조금 환입"]
    print(row(["설비가 깎는 손익", f"{net_a:.1f}", f"{net_b:.1f}"], w))
    print()


def print_year_table(g: Grant) -> None:
    print("[2] 재무상태표 — 해마다 벌어졌다가 5년 뒤 다시 만난다")
    w = [6, 14, 12, 14, 12, 12]
    print(row(["연차", "설비(이연)", "이연수익", "설비(차감)", "자산 차이", "부채 차이"], w))
    print("-" * sum(w))
    for year in range(g.life + 1):
        a, b = deferred_income_method(g, year), deduction_method(g, year)
        print(
            row(
                [
                    f"{year}",
                    f"{a['설비 장부금액']:.1f}",
                    f"{a['이연수익']:.1f}",
                    f"{b['설비 장부금액']:.1f}",
                    f"{a['총자산'] - b['총자산']:.1f}",
                    f"{a['총부채'] - b['총부채']:.1f}",
                ],
                w,
            )
        )
    print()
    print("  자산 차이와 부채 차이가 매년 같다. 그래서 자본총계는 두 방법이 같다.")
    print()


def print_metrics(g: Grant, year: int) -> None:
    a, b = deferred_income_method(g, year), deduction_method(g, year)
    print(f"[3] {year}년 말 지표 — 순이익은 같고 재무상태표를 쓰는 지표가 갈린다")
    w = [18, 14, 14, 12]
    print(row(["항목", "이연수익법", "자산차감법", "차이"], w))
    print("-" * sum(w))
    for key, fmt in [
        ("영업이익", "{:.1f}"),
        ("당기순이익", "{:.1f}"),
        ("EBITDA", "{:.1f}"),
        ("총자산", "{:.1f}"),
        ("총부채", "{:.1f}"),
        ("자본총계", "{:.1f}"),
        ("부채비율", "{:.1f}"),
        ("총자산회전율", "{:.3f}"),
    ]:
        print(row([key, fmt.format(a[key]), fmt.format(b[key]), fmt.format(a[key] - b[key])], w))
    print()


def print_ratio_drift(g: Grant) -> None:
    print("[4] 부채비율과 총자산회전율이 연차에 따라 좁혀진다")
    w = [6, 16, 16, 18, 18]
    print(row(["연차", "부채비율(이연)", "부채비율(차감)", "회전율(이연)", "회전율(차감)"], w))
    print("-" * sum(w))
    for year in range(g.life + 1):
        a, b = deferred_income_method(g, year), deduction_method(g, year)
        print(
            row(
                [
                    f"{year}",
                    f"{a['부채비율']:.1f}",
                    f"{b['부채비율']:.1f}",
                    f"{a['총자산회전율']:.3f}",
                    f"{b['총자산회전율']:.3f}",
                ],
                w,
            )
        )
    print()


def main() -> None:
    print_profit_path(MABA)
    print_year_table(MABA)
    print_metrics(MABA, 1)
    print_ratio_drift(MABA)


if __name__ == "__main__":
    main()
