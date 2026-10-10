"""이연법인세 — 회계이익과 과세소득이 다를 때 생기는 자산과 부채.

가상 회사 가나전자가 설비 300 을 사서 3년 동안 쓴다. 회계에서는 정액법(해마다 100),
세무에서는 앞에 많이 상각하는 방법(150·100·50)으로 상각한다고 둔다. 해마다 감가상각비가
달라도 3년 합계는 같으므로, 차이는 생겼다가 풀린다 — 일시적차이다(K-IFRS 제1012호 문단 5).

[1] 연도별 장부금액과 세무기준액 — 가산할 일시적차이
[2] 당기법인세와 이연법인세 — 법인세비용 = 당기 + 이연
[3] 일시적차이만 있으면 유효세율은 법정세율과 같다
[4] 영구적차이(손금불산입 비용)가 끼면 유효세율이 달라진다 — 문단 81(3) 조정
[5] 차감할 일시적차이(제품보증충당부채)와 이연법인세자산 인식 여부(문단 24·56)

단순화: 세율은 해마다 20% 단일세율로 둔다(가정, 실제 법인세율은 누진 구조다).
설비 외 다른 자산·부채와 세무조정은 없다. 금액 단위는 억원.
"""
import platform
import sys

TAX_RATE = 0.20
COST = 300
BOOK_DEPRECIATION = [100, 100, 100]
TAX_DEPRECIATION = [150, 100, 50]
PROFIT_BEFORE_DEPRECIATION = 400     # 감가상각비를 빼기 전 이익, 3년 같다


def schedule() -> list[dict]:
    rows = []
    book, tax_base, prev_dtl = COST, COST, 0.0
    for year, (bd, td) in enumerate(zip(BOOK_DEPRECIATION, TAX_DEPRECIATION), start=1):
        book -= bd
        tax_base -= td
        accounting_profit = PROFIT_BEFORE_DEPRECIATION - bd
        taxable_income = PROFIT_BEFORE_DEPRECIATION - td
        temp_diff = book - tax_base                  # 양수면 가산할 일시적차이
        dtl = temp_diff * TAX_RATE                   # 문단 47: 실현될 기간의 세율, 문단 53: 할인 안 함
        current_tax = taxable_income * TAX_RATE
        deferred_tax = dtl - prev_dtl
        rows.append({
            "year": year, "book": book, "tax_base": tax_base, "temp_diff": temp_diff,
            "accounting_profit": accounting_profit, "taxable_income": taxable_income,
            "current_tax": current_tax, "dtl": dtl, "deferred_tax": deferred_tax,
            "tax_expense": current_tax + deferred_tax,
        })
        prev_dtl = dtl
    return rows


def print_carrying_vs_base(rows: list[dict]) -> None:
    print("[1] 설비 300 — 장부금액과 세무기준액 (제1012호 문단 5)")
    print(f"  {'연도':<6}{'회계 상각':>10}{'세무 상각':>10}{'장부금액':>10}{'세무기준액':>11}{'일시적차이':>11}")
    for r, bd, td in zip(rows, BOOK_DEPRECIATION, TAX_DEPRECIATION):
        print(f"  {r['year']}년차{bd:>12}{td:>12}{r['book']:>12}{r['tax_base']:>13}{r['temp_diff']:>13}")
    print(f"  합계 {sum(BOOK_DEPRECIATION):>11}{sum(TAX_DEPRECIATION):>12}   — 3년 합계는 같다")
    print("  장부금액 > 세무기준액 → 나중에 과세소득을 늘리는 가산할 일시적차이")
    print()


def print_tax_expense(rows: list[dict]) -> None:
    print(f"[2] 법인세비용 = 당기법인세 + 이연법인세 (세율 {TAX_RATE:.0%} 가정)")
    print(f"  {'연도':<6}{'회계이익':>9}{'과세소득':>9}{'당기법인세':>11}{'이연법인세부채':>13}"
          f"{'이연법인세':>11}{'법인세비용':>11}")
    for r in rows:
        print(f"  {r['year']}년차{r['accounting_profit']:>11}{r['taxable_income']:>11}{r['current_tax']:>13.0f}"
              f"{r['dtl']:>15.0f}{r['deferred_tax']:>+13.0f}{r['tax_expense']:>13.0f}")
    total_current = sum(r["current_tax"] for r in rows)
    total_expense = sum(r["tax_expense"] for r in rows)
    print(f"  3년 합계: 당기법인세 {total_current:.0f}, 법인세비용 {total_expense:.0f} — 낸 세금과 비용이 결국 같다")
    print()


def print_effective_rate(rows: list[dict]) -> None:
    print("[3] 유효세율 = 법인세비용 ÷ 회계이익")
    for r in rows:
        print(f"  {r['year']}년차  당기법인세만 비용으로 잡으면 {r['current_tax'] / r['accounting_profit']:.1%}"
              f"   이연법인세까지 잡으면 {r['tax_expense'] / r['accounting_profit']:.1%}")
    print()


def print_permanent_difference(rows: list[dict]) -> None:
    print("[4] 1년차에 세법상 비용으로 인정되지 않는 비용 30 이 있으면 (영구적차이)")
    r = rows[0]
    non_deductible = 30
    accounting_profit = r["accounting_profit"] - non_deductible   # 회계에서는 비용
    taxable_income = r["taxable_income"]                           # 세무에서는 비용 아님
    current_tax = taxable_income * TAX_RATE
    tax_expense = current_tax + r["deferred_tax"]
    print(f"  회계이익 {accounting_profit}, 과세소득 {taxable_income}, 법인세비용 {tax_expense:.0f}")
    print(f"  유효세율 {tax_expense / accounting_profit:.1%}  (법정세율 {TAX_RATE:.0%})")
    print("  문단 81(3)(가) 형식의 조정:")
    expected = accounting_profit * TAX_RATE
    effect = non_deductible * TAX_RATE
    print(f"    회계이익 {accounting_profit} × {TAX_RATE:.0%}           = {expected:>6.1f}")
    print(f"    비공제 비용 {non_deductible} × {TAX_RATE:.0%} 의 효과    = {effect:>+6.1f}")
    print(f"    법인세비용                    = {expected + effect:>6.1f}")
    print("  비용 30 은 다음 해에도 공제되지 않아 이연법인세가 생기지 않는다")
    print()


def print_deductible_difference() -> None:
    print("[5] 제품보증충당부채 50 — 회계는 판매 연도 비용, 세무는 실제 지급 연도에 공제")
    provision = 50
    accounting_profit = 300
    taxable_income = accounting_profit + provision     # 올해는 공제되지 않는다
    current_tax = taxable_income * TAX_RATE
    dta = provision * TAX_RATE
    print(f"  회계이익 {accounting_profit}, 과세소득 {taxable_income}, 당기법인세 {current_tax:.0f}")
    print(f"  부채 장부금액 {provision} > 세무기준액 0 → 차감할 일시적차이 {provision}, 이연법인세자산 후보 {dta:.0f}")
    print(f"  {'회사':<8}{'미래 과세소득 전망':>16}{'이연법인세자산':>14}{'법인세비용':>12}{'유효세율':>10}")
    for name, probable in (("가나전자", True), ("다라물산", False)):
        recognized = dta if probable else 0.0       # 문단 24: 과세소득 발생 가능성이 높을 때만
        expense = current_tax - recognized
        outlook = "충분" if probable else "불확실"
        print(f"  {name:<8}{outlook:>16}{recognized:>16.0f}{expense:>14.0f}{expense / accounting_profit:>12.1%}")
    print("  다라물산은 같은 거래에서 이연법인세자산을 못 올려 법인세비용이 10 더 크다")
    print()


def main() -> None:
    print(f"Python {platform.python_version()} · {sys.platform}")
    print()
    rows = schedule()
    print_carrying_vs_base(rows)
    print_tax_expense(rows)
    print_effective_rate(rows)
    print_permanent_difference(rows)
    print_deductible_difference()


if __name__ == "__main__":
    main()
