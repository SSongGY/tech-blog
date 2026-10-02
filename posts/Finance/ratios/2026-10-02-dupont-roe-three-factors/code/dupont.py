"""듀폰 분석 — ROE를 순이익률 × 총자산회전율 × 재무레버리지로 쪼갠다.

ROE가 똑같이 15%인 가상 회사 셋(가람유통·나래제약·다온건설)과, ROE가 3년 동안
오른 가상 회사 하나(라온전자)로 세 요인을 계산한다. 금액 단위는 억원이다.
산식은 한국은행 기업경영분석을 따른다. 잔액은 기초·기말 평균잔액으로 주어졌다고 둔다.
"""
import math
import platform
import sys
from dataclasses import dataclass

TAX_RATE = 0.25       # 설명용 단일 세율(가정)
INTEREST_RATE = 0.04  # 차입금 이자율(가정). 부채 전체가 이자부라고 단순화했다


@dataclass
class Company:
    name: str
    sales: float
    ebit: float          # 이자·법인세 차감 전 이익. 여기서는 영업이익과 같다고 둔다
    assets: float        # 총자산 평균
    equity: float        # 자기자본 평균

    @property
    def debt(self) -> float:
        return self.assets - self.equity

    @property
    def interest(self) -> float:
        return self.debt * INTEREST_RATE

    @property
    def pretax(self) -> float:
        return self.ebit - self.interest

    @property
    def net_income(self) -> float:
        # 손실이면 법인세가 없다고 둔다
        return self.pretax * (1 - TAX_RATE) if self.pretax > 0 else self.pretax

    # --- 3요인 ---
    @property
    def margin(self) -> float:
        return self.net_income / self.sales

    @property
    def turnover(self) -> float:
        return self.sales / self.assets

    @property
    def leverage(self) -> float:
        return self.assets / self.equity

    @property
    def roe(self) -> float:
        return self.net_income / self.equity

    # --- 5요인에서 순이익률을 더 쪼갠 세 조각 ---
    @property
    def tax_burden(self) -> float:
        return self.net_income / self.pretax

    @property
    def interest_burden(self) -> float:
        return self.pretax / self.ebit

    @property
    def ebit_margin(self) -> float:
        return self.ebit / self.sales


def pct(x: float) -> str:
    return f"{x * 100:6.1f}%"


def print_environment() -> None:
    print(f"Python {platform.python_version()} ({sys.platform})")
    print(f"가정: 법인세율 {TAX_RATE:.0%}, 이자율 {INTEREST_RATE:.0%}, 금액 단위 억원")
    print()


def show_three(companies: list[Company]) -> None:
    print("[1] ROE가 같은 세 회사 — 재무제표에서 가져온 값")
    print(f"  {'':8}{'매출액':>8}{'영업이익':>8}{'이자':>6}{'세전':>7}{'순이익':>7}"
          f"{'총자산':>7}{'부채':>6}{'자본':>6}")
    for c in companies:
        print(f"  {c.name:8}{c.sales:8.0f}{c.ebit:8.0f}{c.interest:6.0f}{c.pretax:7.0f}"
              f"{c.net_income:7.1f}{c.assets:7.0f}{c.debt:6.0f}{c.equity:6.0f}")
    print()
    print("[2] 3요인 분해 — ROE = 순이익률 × 총자산회전율 × 재무레버리지")
    print(f"  {'':8}{'순이익률':>9}{'총자산회전율':>10}{'재무레버리지':>10}{'곱':>8}{'직접 ROE':>9}")
    for c in companies:
        product = c.margin * c.turnover * c.leverage
        print(f"  {c.name:8}{pct(c.margin):>9}{c.turnover:9.2f}회{c.leverage:9.2f}배"
              f"{pct(product):>8}{pct(c.roe):>9}")
    print()


def show_five(companies: list[Company]) -> None:
    print("[3] 5요인 분해 — 순이익률 = 세부담 × 이자부담 × 영업이익률")
    print(f"  {'':8}{'세부담':>7}{'이자부담':>8}{'영업이익률':>9}{'회전율':>7}{'레버리지':>8}{'곱':>8}")
    for c in companies:
        product = (c.tax_burden * c.interest_burden * c.ebit_margin
                   * c.turnover * c.leverage)
        print(f"  {c.name:8}{c.tax_burden:7.3f}{c.interest_burden:8.3f}{pct(c.ebit_margin):>9}"
              f"{c.turnover:7.2f}{c.leverage:8.2f}{pct(product):>8}")
    print()


def show_shock(companies: list[Company], drop: float) -> None:
    print(f"[4] 영업이익이 세 회사 모두 {drop:.0%} 줄면")
    print(f"  {'':8}{'영업이익':>8}{'순이익':>8}{'ROE 전':>8}{'ROE 후':>8}{'ROE 감소율':>10}")
    for c in companies:
        after = Company(c.name, c.sales, c.ebit * (1 - drop), c.assets, c.equity)
        change = after.roe / c.roe - 1
        print(f"  {c.name:8}{after.ebit:8.1f}{after.net_income:8.1f}{pct(c.roe):>8}"
              f"{pct(after.roe):>8}{pct(change):>10}")
    print()


def show_trend(years: list[tuple[int, Company]]) -> None:
    print("[5] 라온전자 3개년 — ROE가 오른 이유")
    print(f"  {'연도':>4}{'매출액':>7}{'순이익':>7}{'총자산':>7}{'자본':>6}"
          f"{'순이익률':>9}{'회전율':>8}{'레버리지':>8}{'ROE':>8}")
    for year, c in years:
        print(f"  {year:4d}{c.sales:7.0f}{c.net_income:7.1f}{c.assets:7.0f}{c.equity:6.0f}"
              f"{pct(c.margin):>9}{c.turnover:7.2f}회{c.leverage:7.2f}배{pct(c.roe):>8}")
    print()

    # 곱으로 묶인 식은 로그를 취하면 합이 되므로, ROE 변화를 세 요인의 몫으로 정확히 나눌 수 있다
    first, last = years[0][1], years[-1][1]
    total = math.log(last.roe / first.roe)
    parts = [
        ("순이익률", math.log(last.margin / first.margin)),
        ("총자산회전율", math.log(last.turnover / first.turnover)),
        ("재무레버리지", math.log(last.leverage / first.leverage)),
    ]
    print(f"[6] 1년차 → 3년차 ROE 변화(로그 기준 {total:+.4f})를 세 요인으로 나누면")
    for label, value in parts:
        print(f"  {label:10} {value:+.4f}  몫 {value / total * 100:+7.1f}%")
    print(f"  {'합계':10} {sum(v for _, v in parts):+.4f}  몫 {sum(v for _, v in parts) / total * 100:+7.1f}%")


def main() -> None:
    print_environment()
    # 셋 다 ROE 15%가 나오도록 숫자를 설계했다. 출처가 다른 15%를 나란히 보기 위해서다
    companies = [
        Company("가람유통", sales=3000, ebit=120, assets=1000, equity=500),
        Company("나래제약", sales=500, ebit=120, assets=1000, equity=500),
        Company("다온건설", sales=600, ebit=72, assets=1000, equity=200),
    ]
    show_three(companies)
    show_five(companies)
    show_shock(companies, drop=0.20)

    # 이익 규모와 마진은 그대로 두고 자산과 자본 구성만 바꿨다
    years = [
        (1, Company("라온전자", sales=1200, ebit=120, assets=1000, equity=600)),
        (2, Company("라온전자", sales=1210, ebit=128, assets=1100, equity=500)),
        (3, Company("라온전자", sales=1200, ebit=128, assets=1200, equity=400)),
    ]
    show_trend(years)


if __name__ == "__main__":
    main()
