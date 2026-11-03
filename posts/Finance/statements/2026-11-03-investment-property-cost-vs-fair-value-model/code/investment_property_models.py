"""투자부동산의 원가모형과 공정가치모형이 같은 건물을 어떻게 다르게 적는지 계산한다.

기업회계기준서 제1040호 문단 30 은 공정가치모형(문단 33~55)과 원가모형(문단 56) 중
하나를 골라 모든 투자부동산에 적용하게 한다. 원가모형은 제1016호의 원가모형, 즉
감가상각으로 장부금액을 줄이고, 공정가치모형은 매 기말 공정가치로 다시 재고
변동분을 당기손익에 넣는다(문단 35). 같은 임대 건물을 가상 회사로 5년간 따라간다.
"""

from dataclasses import dataclass

YEARS = 5


@dataclass(frozen=True)
class Building:
    """단위는 억원."""

    cost: float  # 취득원가 (건물만, 토지는 없다고 둔다)
    life: int  # 원가모형의 내용연수 (잔존가치 0, 정액법)
    fair_values: tuple[float, ...]  # 1년 말 ~ 5년 말 공정가치
    rent: float  # 연간 임대수익
    operating_cost: float  # 임대와 직접 관련된 연간 운영비용
    other_assets: float  # 건물을 뺀 나머지 자산 (일정하다고 둔다)
    liabilities: float  # 차입금 (일정하다고 둔다)


SAHA = Building(
    cost=500.0,
    life=25,
    fair_values=(520.0, 545.0, 560.0, 530.0, 500.0),  # 3년 오르고 2년 내린다
    rent=40.0,
    operating_cost=10.0,
    other_assets=300.0,
    liabilities=400.0,
)


def cost_model(b: Building, year: int) -> dict[str, float]:
    """문단 56 — 제1016호 원가모형. 감가상각비만 손익에 들어간다."""
    depreciation = b.cost / b.life
    carrying = b.cost - depreciation * year
    net_income = b.rent - b.operating_cost - depreciation
    return _wrap(b, year, carrying, depreciation, 0.0, net_income)


def fair_value_model(b: Building, year: int) -> dict[str, float]:
    """문단 33·35 — 매 기말 공정가치로 측정하고 변동분을 당기손익에 넣는다."""
    previous = b.cost if year == 1 else b.fair_values[year - 2]
    carrying = b.fair_values[year - 1]
    gain = carrying - previous
    net_income = b.rent - b.operating_cost + gain
    return _wrap(b, year, carrying, 0.0, gain, net_income)


def _wrap(
    b: Building, year: int, carrying: float, depreciation: float, gain: float, net_income: float
) -> dict[str, float]:
    # 임대로 번 현금은 배당하지 않고 쌓인다고 둔다. 그래야 자본총계가 순이익과 맞물린다
    cash_flow = b.rent - b.operating_cost
    assets = b.other_assets + cash_flow * year + carrying
    equity = assets - b.liabilities
    return {
        "연차": year,
        "장부금액": carrying,
        "감가상각비": depreciation,
        "평가손익": gain,
        "당기순이익": net_income,
        "영업현금흐름": b.rent - b.operating_cost,
        "총자산": assets,
        "자본총계": equity,
        "부채비율": b.liabilities / equity * 100,
        "ROE": net_income / equity * 100,
    }


def row(cells: list[str], widths: list[int]) -> str:
    return "".join(cell.rjust(w) for cell, w in zip(cells, widths))


def print_profit_path(b: Building) -> None:
    print("[1] 해마다 당기손익에 들어가는 금액 — 원가모형은 일정하고 공정가치모형은 시세를 따른다 (단위: 억원)")
    w = [6, 12, 14, 12, 14, 14, 14]
    print(row(["연차", "공정가치", "감가상각(원가)", "평가손익(FV)", "순이익(원가)", "순이익(FV)", "영업현금흐름"], w))
    print("-" * sum(w))
    for year in range(1, YEARS + 1):
        c, f = cost_model(b, year), fair_value_model(b, year)
        print(
            row(
                [
                    f"{year}",
                    f"{f['장부금액']:.1f}",
                    f"{-c['감가상각비']:.1f}",
                    f"{f['평가손익']:+.1f}",
                    f"{c['당기순이익']:.1f}",
                    f"{f['당기순이익']:.1f}",
                    f"{c['영업현금흐름']:.1f}",
                ],
                w,
            )
        )
    print()
    print("  영업현금흐름은 두 모형이 같다. 임대료가 들어오고 운영비가 나가는 것은 모형과 무관하다.")
    print()


def print_cumulative(b: Building) -> None:
    print("[2] 누적 순이익의 차이는 장부금액의 차이와 항상 같다")
    w = [6, 14, 14, 14, 14, 14]
    print(row(["연차", "누적NI(원가)", "누적NI(FV)", "누적 차이", "장부금액 차이", "자본 차이"], w))
    print("-" * sum(w))
    cum_c = cum_f = 0.0
    for year in range(1, YEARS + 1):
        c, f = cost_model(b, year), fair_value_model(b, year)
        cum_c += c["당기순이익"]
        cum_f += f["당기순이익"]
        print(
            row(
                [
                    f"{year}",
                    f"{cum_c:.1f}",
                    f"{cum_f:.1f}",
                    f"{cum_f - cum_c:.1f}",
                    f"{f['장부금액'] - c['장부금액']:.1f}",
                    f"{f['자본총계'] - c['자본총계']:.1f}",
                ],
                w,
            )
        )
    print()


def print_metrics(b: Building, year: int, label: str) -> None:
    c, f = cost_model(b, year), fair_value_model(b, year)
    print(f"[{label}] {year}년 말 지표 — 같은 건물, 같은 임대료, 같은 차입금")
    w = [14, 14, 14, 12]
    print(row(["항목", "원가모형", "공정가치모형", "차이"], w))
    print("-" * sum(w))
    for key, fmt in [
        ("장부금액", "{:.1f}"),
        ("당기순이익", "{:.1f}"),
        ("영업현금흐름", "{:.1f}"),
        ("총자산", "{:.1f}"),
        ("자본총계", "{:.1f}"),
        ("부채비율", "{:.1f}"),
        ("ROE", "{:.1f}"),
    ]:
        print(row([key, fmt.format(c[key]), fmt.format(f[key]), fmt.format(f[key] - c[key])], w))
    print()


def print_swing(b: Building) -> None:
    print("[5] 순이익의 흔들림 — 5년 동안 가장 좋은 해와 나쁜 해")
    w = [14, 12, 12, 12]
    print(row(["모형", "최고", "최저", "폭"], w))
    print("-" * sum(w))
    for name, fn in [("원가모형", cost_model), ("공정가치모형", fair_value_model)]:
        values = [fn(b, y)["당기순이익"] for y in range(1, YEARS + 1)]
        print(row([name, f"{max(values):.1f}", f"{min(values):.1f}", f"{max(values) - min(values):.1f}"], w))
    print()


def main() -> None:
    print_profit_path(SAHA)
    print_cumulative(SAHA)
    print_metrics(SAHA, 1, "3")
    print_metrics(SAHA, 4, "4")
    print_swing(SAHA)


if __name__ == "__main__":
    main()
