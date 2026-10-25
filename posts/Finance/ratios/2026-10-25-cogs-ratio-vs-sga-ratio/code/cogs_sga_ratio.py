"""영업이익률이 같은 두 비용 구조가 매출 변동에 어떻게 다르게 반응하는가.

금액 단위는 억원이다. 회사와 숫자는 전부 가상이며 실제 기업과 관계가 없다.
변동비 비중은 설명용 가정값이다.
"""

from dataclasses import dataclass


@dataclass
class Company:
    name: str
    revenue: int             # 매출액
    cogs: int                # 매출원가
    sga: int                 # 판매비와관리비
    cogs_variable: float     # 매출원가 중 매출에 비례하는 몫
    sga_variable: float      # 판관비 중 매출에 비례하는 몫

    @property
    def operating_income(self) -> int:
        return self.revenue - self.cogs - self.sga

    @property
    def cogs_ratio(self) -> float:
        return self.cogs / self.revenue * 100

    @property
    def sga_ratio(self) -> float:
        return self.sga / self.revenue * 100

    @property
    def operating_margin(self) -> float:
        return self.operating_income / self.revenue * 100

    @property
    def variable_cost(self) -> float:
        return self.cogs * self.cogs_variable + self.sga * self.sga_variable

    @property
    def fixed_cost(self) -> float:
        return (self.cogs + self.sga) - self.variable_cost

    @property
    def contribution_margin_ratio(self) -> float:
        return (self.revenue - self.variable_cost) / self.revenue * 100

    @property
    def break_even_revenue(self) -> float:
        return self.fixed_cost / (self.contribution_margin_ratio / 100)

    def at(self, growth: float):
        """매출이 growth 만큼 변할 때의 매출원가·판관비·영업이익."""
        revenue = self.revenue * (1 + growth)
        cogs = self.cogs * self.cogs_variable * (1 + growth) \
            + self.cogs * (1 - self.cogs_variable)
        sga = self.sga * self.sga_variable * (1 + growth) \
            + self.sga * (1 - self.sga_variable)
        return revenue, cogs, sga, revenue - cogs - sga


# 영업이익률을 12.0% 로 똑같이 맞췄다. 그 12.0% 에 닿는 경로가 다르다
DURE = Company("두레상사", 1000, 820, 60, 0.95, 0.30)    # 사 와서 파는 구조
HANBYEOL = Company("한별정밀", 1000, 550, 330, 0.80, 0.20)  # 설계하고 파는 구조
COMPANIES = [DURE, HANBYEOL]


def rule(title):
    print()
    print(title)
    print("-" * 70)


def row(label, values, fmt="{:>14,.1f}"):
    print(f"{label:<24}" + "".join(fmt.format(v) for v in values))


def main():
    names = [c.name for c in COMPANIES]

    rule("[1] 같은 영업이익률에 닿는 두 경로 (단위: 억원)")
    row("", names, "{:>14}")
    row("매출액", [c.revenue for c in COMPANIES])
    row("매출원가", [c.cogs for c in COMPANIES])
    row("매출원가율(%)", [c.cogs_ratio for c in COMPANIES])
    row("판매비와관리비", [c.sga for c in COMPANIES])
    row("판관비율(%)", [c.sga_ratio for c in COMPANIES])
    row("영업비용률(%)",
        [c.cogs_ratio + c.sga_ratio for c in COMPANIES])
    row("영업이익", [c.operating_income for c in COMPANIES])
    row("영업이익률(%)", [c.operating_margin for c in COMPANIES])

    rule("[2] 두 비용을 변동비와 고정비로 갈라 보면 (단위: 억원)")
    row("", names, "{:>14}")
    row("매출원가 중 변동비",
        [c.cogs * c.cogs_variable for c in COMPANIES])
    row("매출원가 중 고정비",
        [c.cogs * (1 - c.cogs_variable) for c in COMPANIES])
    row("판관비 중 변동비", [c.sga * c.sga_variable for c in COMPANIES])
    row("판관비 중 고정비",
        [c.sga * (1 - c.sga_variable) for c in COMPANIES])
    row("변동비 합계", [c.variable_cost for c in COMPANIES])
    row("고정비 합계", [c.fixed_cost for c in COMPANIES])
    row("공헌이익률(%)",
        [c.contribution_margin_ratio for c in COMPANIES])

    rule("[3] 매출이 20% 늘면 (단위: 억원)")
    grown = [c.at(0.20) for c in COMPANIES]
    row("", names, "{:>14}")
    row("매출액", [g[0] for g in grown])
    row("매출원가", [g[1] for g in grown])
    row("매출원가율(%)", [g[1] / g[0] * 100 for g in grown])
    row("판매비와관리비", [g[2] for g in grown])
    row("판관비율(%)", [g[2] / g[0] * 100 for g in grown])
    row("영업이익", [g[3] for g in grown])
    row("영업이익률(%)", [g[3] / g[0] * 100 for g in grown])
    row("영업이익 증감률(%)",
        [(g[3] - c.operating_income) / c.operating_income * 100
         for g, c in zip(grown, COMPANIES)])

    rule("[4] 매출이 20% 줄면 — 같은 구조가 반대로 작동한다 (단위: 억원)")
    shrunk = [c.at(-0.20) for c in COMPANIES]
    row("", names, "{:>14}")
    row("매출액", [s[0] for s in shrunk])
    row("매출원가율(%)", [s[1] / s[0] * 100 for s in shrunk])
    row("판관비율(%)", [s[2] / s[0] * 100 for s in shrunk])
    row("영업이익", [s[3] for s in shrunk])
    row("영업이익률(%)", [s[3] / s[0] * 100 for s in shrunk])
    row("영업이익 증감률(%)",
        [(s[3] - c.operating_income) / c.operating_income * 100
         for s, c in zip(shrunk, COMPANIES)])
    row("영업레버리지도(배)",
        [abs((s[3] - c.operating_income) / c.operating_income) / 0.20
         for s, c in zip(shrunk, COMPANIES)], "{:>14.2f}")
    row("공헌이익÷영업이익(배)",
        [(c.revenue - c.variable_cost) / c.operating_income
         for c in COMPANIES], "{:>14.2f}")

    rule("[5] 손익분기점 매출액과 안전한계율 (단위: 억원)")
    row("", names, "{:>14}")
    row("고정비 합계", [c.fixed_cost for c in COMPANIES])
    row("공헌이익률(%)", [c.contribution_margin_ratio for c in COMPANIES])
    row("손익분기점 매출액", [c.break_even_revenue for c in COMPANIES])
    row("안전한계율(%)",
        [(c.revenue - c.break_even_revenue) / c.revenue * 100
         for c in COMPANIES])

    rule("[6] 가나전자 — 깎인 영업이익률을 두 비율로 나눠 보기 (단위: 억원)")
    prior = Company("전기", 1000, 650, 230, 1.0, 1.0)
    current = Company("당기", 1150, 770, 276, 1.0, 1.0)
    print(f"{'':<24}{'전기':>14}{'당기':>14}{'차이(%p)':>14}")
    print(f"{'매출액':<24}{prior.revenue:>14,}{current.revenue:>14,}{'':>14}")
    for label, before, after in [
        ("매출원가율(%)", prior.cogs_ratio, current.cogs_ratio),
        ("판관비율(%)", prior.sga_ratio, current.sga_ratio),
        ("영업이익률(%)", prior.operating_margin, current.operating_margin),
    ]:
        print(f"{label:<24}{before:>14.2f}{after:>14.2f}{after - before:>14.2f}")
    gap = current.operating_margin - prior.operating_margin
    parts = -(current.cogs_ratio - prior.cogs_ratio) \
        - (current.sga_ratio - prior.sga_ratio)
    print(f"\n영업이익률 변화 {gap:.2f}%p = −(매출원가율 변화) −(판관비율 변화) "
          f"= {parts:.2f}%p")
    print(f"금액은 둘 다 늘었다 — 매출원가 {prior.cogs}→{current.cogs} "
          f"({(current.cogs / prior.cogs - 1) * 100:.1f}%), "
          f"판관비 {prior.sga}→{current.sga} "
          f"({(current.sga / prior.sga - 1) * 100:.1f}%), "
          f"매출액 {(current.revenue / prior.revenue - 1) * 100:.1f}%")

    rule("[7] 같은 비용을 다른 칸에 적으면 — 두레상사의 물류비 50 (단위: %)")
    moved = Company("두레상사", 1000, 870, 10, 0.95, 0.30)
    print(f"{'':<24}{'옮기기 전':>14}{'옮긴 뒤':>14}{'차이(%p)':>14}")
    for label, before, after in [
        ("매출원가율", DURE.cogs_ratio, moved.cogs_ratio),
        ("판관비율", DURE.sga_ratio, moved.sga_ratio),
        ("영업비용률", DURE.cogs_ratio + DURE.sga_ratio,
         moved.cogs_ratio + moved.sga_ratio),
        ("영업이익률", DURE.operating_margin, moved.operating_margin),
    ]:
        print(f"{label:<24}{before:>14.1f}{after:>14.1f}{after - before:>14.1f}")


if __name__ == "__main__":
    main()
