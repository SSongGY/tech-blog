"""손익분기점과 영업레버리지 — 고정비 비중이 이익 변동 폭을 키우는 이유.

매출 1,000 과 영업이익 100 이 같은 가상 회사 둘을 놓는다. 가나전자는 설비와 인력에
묶인 고정비가 크고, 다라물산은 매출에 따라 움직이는 변동비가 크다.

[1] 두 회사의 원가 구조 — 공헌이익, 손익분기점, 안전한계
[2] 매출이 ±10% 움직일 때 영업이익 — 영업레버리지도(DOL)로 예측한 값과 실제 값
[3] 매출 수준에 따라 달라지는 DOL
[4] 기능별 손익계산서 — 매출원가·판관비 안에 고정비와 변동비가 섞여 있다
[5] 성격별 주석(K-IFRS 제1001호 문단 104)으로 고정비를 어림하면
[6] 두 해 숫자로 DOL 을 거꾸로 추정할 때 — 고정비가 바뀌면 틀린다

단순화: 판매 단가와 단위당 변동비는 매출 규모와 무관하게 일정하다. 금액 단위는 억원.
"""
import platform
import sys

COMPANIES = {
    # variable_ratio: 매출 1 원당 변동비, fixed: 매출과 무관한 연간 원가
    "가나전자": {"variable_ratio": 0.30, "fixed": 600},
    "다라물산": {"variable_ratio": 0.70, "fixed": 200},
}
BASE_SALES = 1_000


def operating_income(name: str, sales: float, fixed: float | None = None) -> float:
    c = COMPANIES[name]
    fixed = c["fixed"] if fixed is None else fixed
    return sales * (1 - c["variable_ratio"]) - fixed


def contribution_margin(name: str, sales: float) -> float:
    return sales * (1 - COMPANIES[name]["variable_ratio"])


def break_even_sales(name: str) -> float:
    c = COMPANIES[name]
    return c["fixed"] / (1 - c["variable_ratio"])


def dol(name: str, sales: float) -> float:
    return contribution_margin(name, sales) / operating_income(name, sales)


def print_structure() -> None:
    print(f"[1] 원가 구조 — 매출 {BASE_SALES:,} 에서")
    print(f"  {'회사':<8}{'변동비':>8}{'고정비':>8}{'공헌이익':>9}{'영업이익':>9}"
          f"{'손익분기 매출':>12}{'안전한계':>10}{'안전한계율':>10}{'DOL':>7}")
    for name, c in COMPANIES.items():
        variable = BASE_SALES * c["variable_ratio"]
        bep = break_even_sales(name)
        margin = BASE_SALES - bep
        print(f"  {name:<8}{variable:>10,.0f}{c['fixed']:>10,}{contribution_margin(name, BASE_SALES):>11,.0f}"
              f"{operating_income(name, BASE_SALES):>11,.0f}{bep:>15,.1f}{margin:>12,.1f}"
              f"{margin / BASE_SALES:>12.1%}{dol(name, BASE_SALES):>9.1f}")
    print("  DOL = 공헌이익 ÷ 영업이익,  안전한계율 = (매출 − 손익분기 매출) ÷ 매출")
    for name in COMPANIES:
        margin_rate = (BASE_SALES - break_even_sales(name)) / BASE_SALES
        print(f"  {name}: 1 ÷ 안전한계율 {margin_rate:.4f} = {1 / margin_rate:.2f}  (DOL 과 같다)")
    print()


def print_swing() -> None:
    print("[2] 매출이 ±10% 움직일 때 영업이익")
    print(f"  {'회사':<8}{'매출':>8}{'영업이익':>10}{'변화율':>9}{'DOL × 매출 변화율':>18}")
    base_oi = {n: operating_income(n, BASE_SALES) for n in COMPANIES}
    for name in COMPANIES:
        for change in (-0.10, 0.0, 0.10):
            sales = BASE_SALES * (1 + change)
            oi = operating_income(name, sales)
            actual = oi / base_oi[name] - 1
            predicted = dol(name, BASE_SALES) * change
            print(f"  {name:<8}{sales:>10,.0f}{oi:>12,.0f}{actual:>+11.0%}{predicted:>+16.0%}")
    print()


def print_dol_by_level() -> None:
    print("[3] 매출 수준별 DOL — 손익분기점에 가까울수록 커진다")
    levels = (700, 900, 1_000, 1_200, 1_500)
    print(f"  {'매출':<10}" + "".join(f"{s:>10,}" for s in levels))
    for name in COMPANIES:
        cells = []
        for s in levels:
            oi = operating_income(name, s)
            cells.append(f"{'적자':>10}" if oi <= 0 else f"{dol(name, s):>11.1f}")
        print(f"  {name:<8}" + "".join(cells))
    print("  '적자'는 영업이익이 0 이하라 DOL 을 계산하지 않은 칸")
    print()


# 기능별 표시를 위해 원가를 어느 기능에서 썼는지로 나눈다.
# (성격, 고정/변동, 매출원가/판관비, 금액) — 매출 1,000 기준
GANA_COSTS = [
    ("원재료", "변동", "매출원가", 220),
    ("판매수수료", "변동", "판관비", 80),
    ("감가상각비", "고정", "매출원가", 260),
    ("종업원급여", "고정", "매출원가", 140),
    ("종업원급여", "고정", "판관비", 110),
    ("임차료·보험료", "고정", "판관비", 90),
]


def print_function_statement() -> None:
    print("[4] 가나전자 기능별 손익계산서 — 매출 1,000")
    by_function: dict[str, dict[str, int]] = {}
    for _, kind, function, amount in GANA_COSTS:
        by_function.setdefault(function, {"고정": 0, "변동": 0})[kind] += amount
    print(f"  {'항목':<10}{'금액':>8}   {'(안에 섞인 고정비':>10}{'변동비)':>8}")
    print(f"  {'매출':<10}{BASE_SALES:>10,}")
    for function in ("매출원가", "판관비"):
        f = by_function[function]
        print(f"  {function:<10}{f['고정'] + f['변동']:>10,}   ({f['고정']:>8,}{f['변동']:>10,})")
    total = sum(a for *_, a in GANA_COSTS)
    print(f"  {'영업이익':<10}{BASE_SALES - total:>10,}")
    print("  표에는 왼쪽 금액만 나온다 — 괄호 안 구분은 회사 내부 원가 자료에만 있다")
    cogs = sum(by_function["매출원가"].values())
    wrong_cm = BASE_SALES - cogs
    print(f"  매출원가율 {cogs / BASE_SALES:.0%} 를 변동비율로 잘못 두면 DOL = {wrong_cm} ÷ {BASE_SALES - total}"
          f" = {wrong_cm / (BASE_SALES - total):.1f}   (실제 {dol('가나전자', BASE_SALES):.1f})")
    print()


def print_nature_estimate() -> None:
    print("[5] 성격별 주석(문단 104)으로 고정비 어림하기")
    disclosed = {}
    for nature, _, _, amount in GANA_COSTS:
        if nature in ("감가상각비", "종업원급여"):
            disclosed[nature] = disclosed.get(nature, 0) + amount
    for nature, amount in disclosed.items():
        print(f"  주석 공시 {nature:<8}{amount:>6,}")
    estimate = sum(disclosed.values())
    true_fixed = COMPANIES["가나전자"]["fixed"]
    oi = operating_income("가나전자", BASE_SALES)
    est_dol = (oi + estimate) / oi
    print(f"  어림 고정비 {estimate:,} (실제 {true_fixed:,}, 임차료·보험료 90 이 빠짐)")
    print(f"  어림 DOL = (영업이익 {oi:.0f} + 고정비 {estimate}) ÷ {oi:.0f} = {est_dol:.1f}"
          f"   실제 DOL {dol('가나전자', BASE_SALES):.1f}")
    print()


def print_two_year_estimate() -> None:
    print("[6] 두 해 숫자로 DOL 거꾸로 추정 — 가나전자, 매출 1,000 → 1,100")
    sales0, sales1 = 1_000, 1_100
    oi0 = operating_income("가나전자", sales0)
    for label, fixed1 in (("고정비 그대로 600", 600), ("이듬해 설비 증설로 고정비 640", 640)):
        oi1 = operating_income("가나전자", sales1, fixed1)
        estimated = (oi1 / oi0 - 1) / (sales1 / sales0 - 1)
        print(f"  {label:<24} 영업이익 {oi0:.0f} → {oi1:.0f}  "
              f"추정 DOL = {oi1 / oi0 - 1:+.0%} ÷ +10% = {estimated:.1f}")
    print(f"  실제 원가 구조의 DOL 은 매출 1,000 에서 {dol('가나전자', 1_000):.1f}")
    print()


def main() -> None:
    print(f"Python {platform.python_version()} · {sys.platform}")
    print()
    print_structure()
    print_swing()
    print_dol_by_level()
    print_function_statement()
    print_nature_estimate()
    print_two_year_estimate()


if __name__ == "__main__":
    main()
