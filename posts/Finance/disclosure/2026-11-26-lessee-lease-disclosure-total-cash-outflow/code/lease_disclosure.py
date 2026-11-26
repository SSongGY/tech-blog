"""리스이용자 주석 읽기 — 리스부채에 안 잡힌 리스료와 총 현금유출.

가상 회사 가나유통과 다라유통은 한 해에 리스로 내는 현금이 500 으로 같다.
가나유통은 거의 전부 고정리스료이고, 다라유통은 단기리스·소액자산 리스·
매출 연동 변동리스료가 많다. K-IFRS 제1116호 문단 50·53·58 이 요구하는
숫자를 두 회사에 대해 만들어 나란히 놓는다. 표준 라이브러리만 쓴다.
"""

import platform

RATE = 0.05
ORIGINAL_TERM = 10     # 고정리스료 계약의 리스기간
ELAPSED_YEARS = 2      # 당기 초까지 지난 햇수
VARIABLE_RATE = 0.04   # 다라유통 변동리스료 = 매출의 4%
DARA_SALES = 5000.0

COMPANIES = {
    "가나유통": {"fixed": 480.0, "short_term": 10.0, "low_value": 10.0,
                 "variable": 0.0},
    "다라유통": {"fixed": 150.0, "short_term": 120.0, "low_value": 30.0,
                 "variable": DARA_SALES * VARIABLE_RATE},
}


def annuity_pv(payment, years, rate=RATE):
    return sum(payment / (1 + rate) ** t for t in range(1, years + 1))


def build_note(lease):
    fixed = lease["fixed"]
    remaining_opening = ORIGINAL_TERM - ELAPSED_YEARS
    opening_liability = annuity_pv(fixed, remaining_opening)
    interest = opening_liability * RATE
    principal = fixed - interest
    closing_liability = opening_liability - principal
    initial_rou = annuity_pv(fixed, ORIGINAL_TERM)
    depreciation = initial_rou / ORIGINAL_TERM
    closing_rou = initial_rou - depreciation * (ELAPSED_YEARS + 1)
    off_liability = (lease["short_term"] + lease["low_value"]
                     + lease["variable"])
    remaining_closing = remaining_opening - 1
    # 문단 58 → 제1107호 문단 39·B11: 할인하지 않은 계약상 현금흐름을 구간별로
    within_1 = fixed * min(remaining_closing, 1)
    within_5 = fixed * max(min(remaining_closing, 5) - 1, 0)
    over_5 = fixed * max(remaining_closing - 5, 0)
    return {
        "depreciation": depreciation, "interest": interest,
        "short_term": lease["short_term"], "low_value": lease["low_value"],
        "variable": lease["variable"], "principal": principal,
        "closing_liability": closing_liability, "closing_rou": closing_rou,
        "off_liability": off_liability,
        "total_cash": fixed + off_liability,
        "total_expense": depreciation + interest + off_liability,
        "maturity": (within_1, within_5, over_5),
    }


def print_row(label, values, fmt="{:>12.2f}"):
    cells = "".join(fmt.format(v) for v in values)
    print(f"  {label:<26}{cells}")


def main():
    print("[0] 환경")
    print(f"  Python {platform.python_version()}")
    print("  가상 회사: 가나유통, 다라유통 (실재 기업 아님)")
    print(f"  고정리스료 계약은 {ORIGINAL_TERM}년 후급, 할인율 {RATE:.0%}, "
          f"당기는 {ELAPSED_YEARS + 1}년차")
    print(f"  다라유통 변동리스료 = 매출 {DARA_SALES:.0f} × {VARIABLE_RATE:.0%}")
    print()

    names = list(COMPANIES)
    notes = [build_note(COMPANIES[n]) for n in names]
    header = "".join(f"{n:>10}" for n in names)

    print("[1] 한 해에 낸 리스료 — 계약 종류별")
    print(f"  {'':<26}{header}")
    for key, label in (("fixed", "고정리스료"), ("short_term", "단기리스료"),
                       ("low_value", "소액자산 리스료"),
                       ("variable", "변동리스료(매출 연동)")):
        print_row(label, [COMPANIES[n][key] for n in names])
    print_row("합계", [n["total_cash"] for n in notes])
    print()

    print("[2] 재무상태표 — 기말")
    print(f"  {'':<26}{header}")
    print_row("사용권자산", [n["closing_rou"] for n in notes])
    print_row("리스부채", [n["closing_liability"] for n in notes])
    print()

    print("[3] 문단 53 금액 공시 — 당기")
    print(f"  {'':<26}{header}")
    print_row("⑴ 사용권자산 감가상각비", [n["depreciation"] for n in notes])
    print_row("⑵ 리스부채 이자비용", [n["interest"] for n in notes])
    print_row("⑶ 단기리스 비용", [n["short_term"] for n in notes])
    print_row("⑷ 소액자산 리스 비용", [n["low_value"] for n in notes])
    print_row("⑸ 변동리스료 비용", [n["variable"] for n in notes])
    print_row("   비용 합계", [n["total_expense"] for n in notes])
    print_row("⑺ 리스의 총 현금유출", [n["total_cash"] for n in notes])
    print()

    print("[4] 현금흐름표 분류 (문단 50) — 이자지급은 영업활동으로 분류했다고 둔다")
    print(f"  {'':<26}{header}")
    print_row("재무활동: 리스부채 원금", [n["principal"] for n in notes])
    print_row("영업활동: 리스부채 이자", [n["interest"] for n in notes])
    print_row("영업활동: 부채 밖 리스료", [n["off_liability"] for n in notes])
    print_row("합계 = 총 현금유출", [n["total_cash"] for n in notes])
    print()

    print("[5] 재무활동 줄만 보면 빠지는 금액")
    print(f"  {'':<26}{header}")
    print_row("재무활동 리스부채 상환", [n["principal"] for n in notes])
    print_row("리스의 총 현금유출", [n["total_cash"] for n in notes])
    print_row("상환 ÷ 총 현금유출",
              [n["principal"] / n["total_cash"] for n in notes],
              fmt="{:>12.1%}")
    print_row("부채 밖 리스료 ÷ 총 유출",
              [n["off_liability"] / n["total_cash"] for n in notes],
              fmt="{:>12.1%}")
    print_row("리스부채 ÷ 총 현금유출",
              [n["closing_liability"] / n["total_cash"] for n in notes],
              fmt="{:>11.2f}배")
    print()

    print("[6] 리스부채 만기분석 (문단 58) — 할인하지 않은 계약상 현금흐름")
    print(f"  {'':<26}{header}")
    for index, label in enumerate(("1년 이내", "1년 초과 5년 이내", "5년 초과")):
        print_row(label, [n["maturity"][index] for n in notes])
    print_row("할인 전 합계", [sum(n["maturity"]) for n in notes])
    print_row("리스부채 장부금액", [n["closing_liability"] for n in notes])
    print_row("차이 = 앞으로 낼 이자",
              [sum(n["maturity"]) - n["closing_liability"] for n in notes])
    print()

    print("[7] 다라유통 변동리스료의 매출 민감도 (문단 59⑵, B49)")
    print(f"  {'매출 변화':>8} {'매출':>9} {'변동리스료':>9} {'총 현금유출':>10}")
    dara = notes[1]
    for change in (-0.20, -0.10, 0.0, 0.10, 0.20):
        sales = DARA_SALES * (1 + change)
        variable = sales * VARIABLE_RATE
        total = dara["total_cash"] - dara["variable"] + variable
        print(f"  {change:>+9.0%} {sales:>11.2f} {variable:>12.2f} "
              f"{total:>13.2f}")
    print("  가나유통은 변동리스료가 없어 매출이 바뀌어도 총 현금유출 500.00")


if __name__ == "__main__":
    main()
