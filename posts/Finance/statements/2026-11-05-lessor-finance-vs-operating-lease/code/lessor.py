"""리스제공자 회계 — 같은 설비를 금융리스와 운용리스로 회계처리할 때의 숫자 비교.

가상 회사 마바리스가 취득원가 100억원(=공정가치)인 설비를 빌려준다. 단위는 억원.
표준 라이브러리만 쓴다.
"""

import platform

COST = 100.0  # 취득원가이자 리스개시일의 공정가치. 판매이익이 없는 단순한 경우다
RATE = 0.08  # 내재이자율


def annuity_payment(present_value: float, rate: float, years: int) -> float:
    """매년 말 같은 금액을 받아 현재가치가 present_value가 되는 리스료."""
    return present_value * rate / (1 - (1 + rate) ** -years)


def present_value(payments: list[float], rate: float) -> float:
    return sum(p / (1 + rate) ** (t + 1) for t, p in enumerate(payments))


def finance_lease(payment: float, years: int) -> list[dict[str, float]]:
    """리스순투자에 일정한 기간수익률(내재이자율)을 곱해 금융수익을 인식한다(문단 75)."""
    rows = []
    net = COST  # 문단 67: 개시일에 설비를 빼고 같은 금액의 수취채권을 올린다
    for year in range(1, years + 1):
        income = net * RATE
        end = net + income - payment
        rows.append(
            {"year": year, "begin": net, "income": income, "payment": payment, "end": end}
        )
        net = end
    return rows


def operating_lease(
    payments: list[float], useful_life: int
) -> list[dict[str, float]]:
    """리스료를 정액으로 수익 인식하고 설비는 계속 감가상각한다(문단 81·82)."""
    straight = sum(payments) / len(payments)
    dep = COST / useful_life
    rows = []
    carrying = COST
    for year, cash in enumerate(payments, start=1):
        carrying -= dep
        rows.append(
            {
                "year": year,
                "cash": cash,
                "income": straight,
                "dep": dep,
                "profit": straight - dep,
                "carrying": carrying,
                # 정액 수익과 받은 현금의 차이는 미수리스료(자산)로 쌓였다 풀린다
                "gap": 0.0,
            }
        )
    accrued = 0.0
    for r in rows:
        accrued += r["income"] - r["cash"]
        r["gap"] = accrued
    return rows


def main() -> None:
    print(f"환경: Python {platform.python_version()}")
    print()

    years = 5
    pmt = annuity_payment(COST, RATE, years)
    pv = present_value([pmt] * years, RATE)

    print("[0] 분류 판단에 쓰는 숫자 — 문단 63 ⑷ 리스료의 현재가치 대 공정가치 (단위: 억원)")
    print(f"{'공정가치':>12}{COST:>10.2f}")
    print(f"{'연 리스료':>12}{pmt:>10.2f}  (5년, 매년 말)")
    print(f"{'현재가치':>12}{pv:>10.2f}  (내재이자율 {RATE:.0%})")
    print(f"{'현재가치/공정가치':>12}{pv / COST:>10.1%}")
    print(f"{'리스기간/내용연수':>12}{years}년/{years}년 = {years / years:.0%}")
    print()

    fin = finance_lease(pmt, years)
    print("[1] 금융리스 — 리스순투자 상각표 (단위: 억원)")
    print(f"{'연차':>4}{'기초 순투자':>14}{'금융수익(8%)':>14}{'리스료 수취':>14}{'기말 순투자':>14}")
    print("-" * 60)
    for r in fin:
        print(
            f"{r['year']:>4}{r['begin']:>14.2f}{r['income']:>14.2f}"
            f"{r['payment']:>14.2f}{r['end']:>14.2f}"
        )
    total_fin = sum(r["income"] for r in fin)
    print(f"\n  금융수익 합계 {total_fin:.2f} = 리스료 합계 {pmt * years:.2f} - 원금 {COST:.2f}")
    print()

    op_payments = [20.0, 25.0, 30.0]
    op = operating_lease(op_payments, useful_life=10)
    print("[2] 운용리스 — 3년 계약, 내용연수 10년, 리스료 20/25/30 (단위: 억원)")
    print(
        f"{'연차':>4}{'받은 현금':>12}{'리스수익(정액)':>16}{'감가상각비':>12}"
        f"{'이익':>10}{'설비 장부':>12}{'미수리스료':>12}"
    )
    print("-" * 78)
    for r in op:
        print(
            f"{r['year']:>4}{r['cash']:>12.2f}{r['income']:>16.2f}{r['dep']:>12.2f}"
            f"{r['profit']:>10.2f}{r['carrying']:>12.2f}{r['gap']:>12.2f}"
        )
    print(f"\n  3년 말 설비 장부금액 {op[-1]['carrying']:.2f} — 마바리스가 계속 보유하고 감가상각한다")
    print()

    # 같은 5년·같은 현금흐름을 운용리스로 처리했다고 가정해 이익의 모양만 비교한다
    dep5 = COST / years
    print("[3] 같은 현금흐름 — 금융리스 대 운용리스로 처리했을 때의 연도별 이익 (단위: 억원)")
    print(f"{'연차':>4}{'금융리스 이익':>16}{'운용리스 이익':>16}")
    print("-" * 38)
    op_total = 0.0
    for r in fin:
        op_profit = pmt - dep5
        op_total += op_profit
        print(f"{r['year']:>4}{r['income']:>16.2f}{op_profit:>16.2f}")
    print("-" * 38)
    print(f"{'합계':>4}{total_fin:>16.2f}{op_total:>16.2f}")
    print(f"  합계 차이 {abs(total_fin - op_total):.2f}")


if __name__ == "__main__":
    main()
