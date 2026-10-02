"""이자보상배율 — 영업이익으로 이자를 몇 번 낼 수 있는가.

가상 회사 넷을 둔다. 금리가 오를 때 배율이 어떻게 움직이는지(가나기계·다라유통),
1배 미만이 3년 이어지면 차입이 어떻게 불어나는지(마사건설),
이자수익이 큰 회사에서 이자보상비율과 순이자보상비율이 어떻게 갈리는지(바아전자)를 본다.
산식은 한국은행 기업경영분석 분석지표 해설을 따른다.
"""
import platform
import sys
from dataclasses import dataclass


@dataclass
class Borrower:
    name: str
    operating_profit: float
    borrowings: float
    fixed_share: float  # 고정금리 차입 비중. 나머지는 변동금리
    fixed_rate: float
    floating_rate: float

    def interest(self, floating_shift: float = 0.0) -> float:
        fixed = self.borrowings * self.fixed_share * self.fixed_rate
        floating = self.borrowings * (1 - self.fixed_share) * (self.floating_rate + floating_shift)
        return fixed + floating

    def coverage(self, floating_shift: float = 0.0) -> float:
        return self.operating_profit / self.interest(floating_shift)


GANA = Borrower("가나기계", operating_profit=120, borrowings=800,
                fixed_share=0.75, fixed_rate=0.04, floating_rate=0.04)
DARA = Borrower("다라유통", operating_profit=60, borrowings=1000,
                fixed_share=0.0, fixed_rate=0.0, floating_rate=0.05)


def print_definitions() -> None:
    print("[0] 산식 (한국은행 기업경영분석 분석지표 해설 629·630·625)")
    print("  이자보상비율   = 영업이익 ÷ 이자비용 × 100        (배율로 쓰면 × 100 을 뺀다)")
    print("  순이자보상비율 = 영업이익 ÷ (이자비용 − 이자수익) × 100")
    print("  차입금평균이자율 = 이자비용 ÷ (회사채 + 장단기차입금) 평균 × 100")
    print()


def print_base() -> None:
    print("[1] 기준 상태 (단위: 억원)")
    print(f"  {'':10}{'영업이익':>8}{'차입금':>8}{'고정금리 비중':>12}{'이자비용':>8}{'이자보상배율':>10}")
    for c in (GANA, DARA):
        print(f"  {c.name:10}{c.operating_profit:>8.0f}{c.borrowings:>8.0f}{c.fixed_share:>14.0%}"
              f"{c.interest():>10.1f}{c.coverage():>12.2f}배")
    print()


def print_rate_shock() -> None:
    print("[2] 영업이익은 그대로, 변동금리만 오를 때")
    shifts = (0.0, 0.01, 0.02, 0.03)
    print(f"  {'변동금리 상승폭':14}" + "".join(f"{f'+{s * 100:.0f}%p':>10}" for s in shifts))
    for c in (GANA, DARA):
        cells = "".join(f"{c.coverage(s):>9.2f}배" for s in shifts)
        print(f"  {c.name:14}{cells}")
    for c in (GANA, DARA):
        # 이자비용 = 차입금 × 평균이자율 이므로 배율 1 이 되는 평균이자율은 영업이익 ÷ 차입금
        breakeven_avg_rate = c.operating_profit / c.borrowings
        print(f"  {c.name}  배율 1이 되는 차입금평균이자율 = {c.operating_profit:.0f} ÷ {c.borrowings:.0f}"
              f" = {breakeven_avg_rate:.1%}")
    print()


def print_three_years() -> None:
    print("[3] 마사건설 — 배율 1 미만이 3년 이어질 때 (부족분을 새 차입으로 메운다고 가정)")
    borrowings = 1000.0
    rate = 0.05
    operating_profits = (40, 30, 20)
    print(f"  {'연도':6}{'기초 차입금':>10}{'이자비용':>8}{'영업이익':>8}{'배율':>8}{'부족분':>8}{'기말 차입금':>10}")
    for year, op in enumerate(operating_profits, start=1):
        interest = borrowings * rate
        shortfall = max(interest - op, 0)
        ending = borrowings + shortfall
        print(f"  {year}년차{borrowings:>12.1f}{interest:>10.1f}{op:>10.0f}{op / interest:>9.2f}배"
              f"{shortfall:>9.1f}{ending:>12.1f}")
        borrowings = ending
    print("  세금·원금 상환·투자는 뺐다. 이자만으로도 차입금이 해마다 늘고, 늘어난 차입금이 다음 해 이자를 키운다")
    print("  한국은행은 이자보상배율이 3년 이상 연속 1 미만인 기업을 한계기업으로 분류한다")
    print()


def print_net_coverage() -> None:
    print("[4] 바아전자 — 현금이 많아 이자수익이 큰 회사")
    operating_profit = 40
    interest_expense = 50
    cash = 1000
    deposit_rate = 0.03
    interest_income = cash * deposit_rate
    gross = operating_profit / interest_expense
    net = operating_profit / (interest_expense - interest_income)
    print(f"  영업이익 {operating_profit}, 이자비용 {interest_expense}, 현금 {cash} × 예금금리 {deposit_rate:.0%}"
          f" = 이자수익 {interest_income:.0f}")
    print(f"  이자보상배율   {operating_profit} ÷ {interest_expense} = {gross:.2f}배")
    print(f"  순이자보상배율 {operating_profit} ÷ ({interest_expense} − {interest_income:.0f}) = {net:.2f}배")
    print()


def print_negative() -> None:
    print("[5] 영업적자면 배율은 음수가 된다")
    for op in (30, 0, -20):
        print(f"  영업이익 {op:>4} / 이자비용 50 → {op / 50:>5.2f}배")
    print("  음수 배율의 크기는 '얼마나 못 내는가'를 비교하는 데 쓰기 어렵다. 적자 여부를 따로 본다")
    print()


def main() -> None:
    print(f"Python {platform.python_version()} / {platform.system()}")
    print("단위: 억원 / 회사: 가나기계·다라유통·마사건설·바아전자(모두 가상)")
    print()
    print_definitions()
    print_base()
    print_rate_shock()
    print_three_years()
    print_net_coverage()
    print_negative()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
