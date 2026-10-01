"""매출채권·재고자산 회전율과 회전일수 — 가상 회사 고노상사·도로상사.

두 회사는 매출·매출원가·영업이익이 똑같다. 다른 것은 2년차에 매출채권과
재고자산이 얼마나 불었느냐뿐이다. 그 차이가 회전율, 영업활동 현금흐름,
손실충당금과 재고 평가손실로 어떻게 번지는지 계산한다.
"""
import platform
import sys
from dataclasses import dataclass

DAYS = 365


@dataclass
class Company:
    name: str
    # 0년차 말, 1년차 말, 2년차 말 잔액
    receivables: tuple[float, float, float]
    inventory: tuple[float, float, float]


SALES = {1: 1000.0, 2: 1200.0}
COST_OF_SALES = {1: 700.0, 2: 840.0}
OPERATING_INCOME = {1: 100.0, 2: 120.0}

GONO = Company("고노상사", receivables=(150, 170, 200), inventory=(100, 110, 130))
DORO = Company("도로상사", receivables=(150, 170, 330), inventory=(100, 110, 220))

# 2년차 말 매출채권의 연령 분포(가정). 연체 구간별 기대신용손실률도 가정이다.
AGING_BUCKETS = ["만기 전", "1~30일 연체", "31~90일 연체", "90일 초과 연체"]
LOSS_RATES = [0.01, 0.03, 0.10, 0.40]
AGING = {
    "고노상사": [180, 15, 5, 0],
    "도로상사": [200, 60, 45, 25],
}

# 2년차 말 재고 가운데 1년 넘게 안 팔린 재고(가정)와 그 순실현가능가치
AGED_INVENTORY = {"고노상사": (10, 9), "도로상사": (60, 30)}


def average(values: tuple[float, float, float], year: int) -> float:
    return (values[year - 1] + values[year]) / 2


def turnover_rows(company: Company, year: int) -> dict[str, float]:
    ar_avg = average(company.receivables, year)
    inv_avg = average(company.inventory, year)
    ar_turnover = SALES[year] / ar_avg
    inv_turnover_sales = SALES[year] / inv_avg
    inv_turnover_cost = COST_OF_SALES[year] / inv_avg
    return {
        "ar_avg": ar_avg,
        "ar_turnover": ar_turnover,
        "ar_days": DAYS / ar_turnover,
        "inv_avg": inv_avg,
        "inv_turnover_sales": inv_turnover_sales,
        "inv_days_sales": DAYS / inv_turnover_sales,
        "inv_turnover_cost": inv_turnover_cost,
        "inv_days_cost": DAYS / inv_turnover_cost,
    }


def print_balances() -> None:
    print("[1] 두 회사의 숫자")
    print(f"  {'':10}{'1년차':>8}{'2년차':>8}   (두 회사 공통)")
    print(f"  {'매출액':10}{SALES[1]:>8.0f}{SALES[2]:>8.0f}")
    print(f"  {'매출원가':10}{COST_OF_SALES[1]:>8.0f}{COST_OF_SALES[2]:>8.0f}")
    print(f"  {'영업이익':10}{OPERATING_INCOME[1]:>8.0f}{OPERATING_INCOME[2]:>8.0f}")
    print()
    print(f"  {'기말 잔액':16}{'0년차':>7}{'1년차':>7}{'2년차':>7}  2년차 증가율")
    for company in (GONO, DORO):
        for label, values in (("매출채권", company.receivables), ("재고자산", company.inventory)):
            growth = values[2] / values[1] - 1
            print(f"  {company.name + ' ' + label:16}"
                  f"{values[0]:>7.0f}{values[1]:>7.0f}{values[2]:>7.0f}  {growth:>+8.1%}")
    print(f"  매출액 2년차 증가율 {SALES[2] / SALES[1] - 1:+.1%}")
    print()


def print_turnover() -> None:
    print("[2] 회전율과 회전일수 — 평균잔액 기준 (한국은행 기업경영분석 산식)")
    print(f"  {'':10}{'연도':>4}{'채권평균':>9}{'채권회전율':>10}{'회수일수':>9}"
          f"{'재고평균':>9}{'재고회전율':>10}{'재고일수':>9}{'영업순환':>9}")
    for company in (GONO, DORO):
        for year in (1, 2):
            r = turnover_rows(company, year)
            cycle = r["ar_days"] + r["inv_days_sales"]
            print(f"  {company.name:10}{year:>4}{r['ar_avg']:>9.0f}{r['ar_turnover']:>9.2f}회"
                  f"{r['ar_days']:>8.1f}일{r['inv_avg']:>9.0f}{r['inv_turnover_sales']:>9.2f}회"
                  f"{r['inv_days_sales']:>8.1f}일{cycle:>8.1f}일")
    print("  채권회전율 = 매출액 ÷ 평균매출채권, 회수일수 = 365 ÷ 회전율")
    print("  재고회전율 = 매출액 ÷ 평균재고자산, 영업순환 = 회수일수 + 재고일수")
    print()


def print_inventory_by_cost() -> None:
    print("[3] 재고회전율 분자를 매출원가로 바꾸면 (2년차)")
    for company in (GONO, DORO):
        r = turnover_rows(company, 2)
        print(f"  {company.name}  매출액 기준 {r['inv_turnover_sales']:.2f}회·{r['inv_days_sales']:.1f}일"
              f"  매출원가 기준 {r['inv_turnover_cost']:.2f}회·{r['inv_days_cost']:.1f}일")
    print("  분자가 다르면 숫자가 달라진다. 비교할 때는 같은 산식끼리 놓는다")
    print()


def print_year_end_days() -> None:
    print("[4] 평균잔액과 기말잔액 — 2년차 매출채권 회수일수")
    for company in (GONO, DORO):
        r = turnover_rows(company, 2)
        year_end_days = company.receivables[2] / SALES[2] * DAYS
        print(f"  {company.name}  평균잔액 기준 {r['ar_days']:.1f}일  기말잔액 기준 {year_end_days:.1f}일")
    print("  평균은 연중에 생긴 증가를 절반만 반영한다")
    print()


def print_cash_flow() -> None:
    print("[5] 2년차 영업활동 현금흐름 (간접법, 법인세·감가상각·매입채무 변동 없음 가정)")
    for company in (GONO, DORO):
        delta_ar = company.receivables[2] - company.receivables[1]
        delta_inv = company.inventory[2] - company.inventory[1]
        cash = OPERATING_INCOME[2] - delta_ar - delta_inv
        print(f"  {company.name}  영업이익 {OPERATING_INCOME[2]:.0f} − 매출채권 증가 {delta_ar:.0f}"
              f" − 재고자산 증가 {delta_inv:.0f} = {cash:+.0f}")
    print()


def print_impairment() -> None:
    print("[6] 2년차 말 손실충당금(충당금설정률표)과 재고 평가손실 — 연령 분포와 손실률은 가정")
    print(f"  {'구간':16}{'손실률':>6}" + "".join(f"{c.name:>14}" for c in (GONO, DORO)))
    for i, bucket in enumerate(AGING_BUCKETS):
        print(f"  {bucket:16}{LOSS_RATES[i]:>6.0%}"
              + "".join(f"{AGING[c.name][i]:>8.0f} → {AGING[c.name][i] * LOSS_RATES[i]:>4.1f}"
                        for c in (GONO, DORO)))
    results = {}
    for company in (GONO, DORO):
        assert sum(AGING[company.name]) == company.receivables[2]
        allowance = sum(a * r for a, r in zip(AGING[company.name], LOSS_RATES))
        aged_cost, aged_nrv = AGED_INVENTORY[company.name]
        write_down = aged_cost - aged_nrv
        results[company.name] = (allowance, write_down)
    print("  " + " " * 22 + "".join(f"{'합계 ' + format(results[c.name][0], '.1f'):>14}" for c in (GONO, DORO)))
    print()
    for company in (GONO, DORO):
        allowance, write_down = results[company.name]
        aged_cost, aged_nrv = AGED_INVENTORY[company.name]
        adjusted = OPERATING_INCOME[2] - allowance - write_down
        print(f"  {company.name}  장기재고 원가 {aged_cost} → 순실현가능가치 {aged_nrv}, 평가손실 {write_down}")
        print(f"  {'':8}  영업이익 {OPERATING_INCOME[2]:.0f} − 손상차손 {allowance:.1f} − 평가손실 {write_down}"
              f" = {adjusted:.1f}  ({adjusted / OPERATING_INCOME[2] - 1:+.1%})")
    print("  1년차 말 충당금과 평가손실은 두 회사 모두 0으로 두었다")


def main() -> None:
    print(f"Python {platform.python_version()} / {platform.system()}")
    print("단위: 억원 / 회사: 고노상사·도로상사(가상) / 2년치 매출·이익은 두 회사가 같다")
    print()
    print_balances()
    print_turnover()
    print_inventory_by_cost()
    print_year_end_days()
    print_cash_flow()
    print_impairment()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
