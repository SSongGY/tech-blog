"""ROE와 ROA — 분모가 자본이냐 자산이냐가 만드는 차이.

자산과 영업이익이 똑같고 자금 조달만 다른 가상 회사 둘(타파기계·하나기계)로
ROE와 ROA를 계산한다. 산식은 한국은행 기업경영분석을 따르되, 설명을 단순하게
하려고 기초·기말 잔액이 같다고 두어 평균잔액 = 기말잔액이 되게 했다.
"""
import platform
import sys
from dataclasses import dataclass

TAX_RATE = 0.20       # 설명용 단일 세율(가정)
INTEREST_RATE = 0.05  # 차입금 이자율(가정)
TOTAL_ASSETS = 1000.0


@dataclass
class Result:
    debt: float
    equity: float
    operating_income: float
    interest: float
    pretax: float
    tax: float
    net_income: float

    @property
    def roa(self) -> float:
        return self.net_income / TOTAL_ASSETS

    @property
    def roe(self) -> float:
        return self.net_income / self.equity

    @property
    def roa_before_financing(self) -> float:
        # 한국은행 기업순이익률: (당기순이익 + 이자비용) ÷ 총자산
        return (self.net_income + self.interest) / TOTAL_ASSETS


def compute(debt: float, operating_income: float) -> Result:
    equity = TOTAL_ASSETS - debt
    interest = debt * INTEREST_RATE
    pretax = operating_income - interest
    # 손실이면 법인세 0으로 둔다(이월결손금 효과는 다루지 않는다)
    tax = max(pretax, 0) * TAX_RATE
    return Result(debt, equity, operating_income, interest, pretax, tax, pretax - tax)


def print_pair() -> None:
    print("[1] 자산·영업이익이 같고 부채만 다른 두 회사 (영업이익 100)")
    print(f"  {'':8}{'부채':>6}{'자본':>6}{'이자':>6}{'세전':>6}{'순이익':>7}{'ROA':>8}{'ROE':>8}")
    for name, debt in (("타파기계", 200), ("하나기계", 700)):
        r = compute(debt, 100)
        print(f"  {name:8}{r.debt:>6.0f}{r.equity:>6.0f}{r.interest:>6.1f}{r.pretax:>6.1f}"
              f"{r.net_income:>7.1f}{r.roa:>8.1%}{r.roe:>8.1%}")
    print("  ROA = 당기순이익 ÷ 총자산, ROE = 당기순이익 ÷ 자기자본")
    print()


def print_leverage_ladder() -> None:
    print("[2] 한 회사가 차입금으로 자사주를 사들여 자본을 줄여 갈 때 (자산 1000, 영업이익 100 고정)")
    print(f"  {'부채':>6}{'자본':>6}{'부채비율':>9}{'순이익':>8}{'ROA':>8}{'ROE':>8}{'이자보상배율':>10}")
    for debt in (0, 200, 400, 600, 700, 800, 900):
        r = compute(debt, 100)
        coverage = f"{r.operating_income / r.interest:.1f}배" if r.interest else "-"
        print(f"  {debt:>6.0f}{r.equity:>6.0f}{r.debt / r.equity:>9.0%}{r.net_income:>8.1f}"
              f"{r.roa:>8.1%}{r.roe:>8.1%}{coverage:>12}")
    print("  이자보상배율 = 영업이익 ÷ 이자비용")
    print()


def print_downturn() -> None:
    print("[3] 영업이익이 줄면 — 자산수익률(영업이익÷자산)이 이자율 5% 아래로 내려갈 때")
    print(f"  {'영업이익':>8}{'영업이익÷자산':>12}{'타파 ROE':>10}{'하나 ROE':>10}{'타파 ROA':>10}{'하나 ROA':>10}")
    for oi in (150, 100, 50, 30):
        t = compute(200, oi)
        h = compute(700, oi)
        print(f"  {oi:>8.0f}{oi / TOTAL_ASSETS:>14.1%}{t.roe:>11.1%}{h.roe:>10.1%}{t.roa:>10.1%}{h.roa:>10.1%}")
    print()


def print_formula_check() -> None:
    print("[4] 레버리지 식으로 검산 — ROE = [r + (r − i) × 부채/자본] × (1 − t)  (세전이익이 양수일 때)")
    for name, debt in (("타파기계", 200), ("하나기계", 700)):
        r = compute(debt, 100)
        asset_return = r.operating_income / TOTAL_ASSETS
        formula = (asset_return + (asset_return - INTEREST_RATE) * debt / r.equity) * (1 - TAX_RATE)
        assert abs(formula - r.roe) < 1e-12
        print(f"  {name}  r={asset_return:.0%}, i={INTEREST_RATE:.0%}, 부채/자본={debt / r.equity:.3f}"
              f" → 식 {formula:.4%}  직접 계산 {r.roe:.4%}")
    print()


def print_before_financing() -> None:
    print("[5] 이자를 되돌려 더한 ROA — 한국은행 기업순이익률 (당기순이익 + 이자비용) ÷ 총자산")
    for name, debt in (("타파기계", 200), ("하나기계", 700)):
        r = compute(debt, 100)
        tax_saved = r.interest * TAX_RATE
        print(f"  {name}  ROA {r.roa:.1%}  기업순이익률 {r.roa_before_financing:.1%}"
              f"  (이자비용 때문에 줄어든 법인세 = {r.interest:.0f} × {TAX_RATE:.0%} = {tax_saved:.1f})")
    print("  남는 차이는 이자비용이 법인세를 줄여 준 몫이다")
    print()


def print_negative_equity() -> None:
    print("[6] 자본이 음수인 회사 — 자본잠식 상태의 가상 회사 가하상사")
    equity, net_income = -50.0, -20.0
    print(f"  자기자본 {equity:.0f}, 당기순이익 {net_income:.0f} → ROE {net_income / equity:+.1%}")
    print("  손실인데 ROE가 양수로 나온다. 분모가 음수면 ROE는 해석하지 않는다")


def main() -> None:
    print(f"Python {platform.python_version()} / {platform.system()}")
    print(f"단위: 억원 / 회사: 타파기계·하나기계·가하상사(가상) / 자산 {TOTAL_ASSETS:.0f}, "
          f"이자율 {INTEREST_RATE:.0%}, 세율 {TAX_RATE:.0%} (가정)")
    print()
    print_pair()
    print_leverage_ladder()
    print_downturn()
    print_formula_check()
    print_before_financing()
    print_negative_equity()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
