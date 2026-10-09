"""리스 회계 — 임차료가 부채로 올라가면 부채비율과 이익이 어떻게 움직이는가.

같은 매장을 같은 임차료로 쓰는 가상 회사 둘을 놓는다.
가나유통은 5년 계약을 맺어 K-IFRS 제1116호에 따라 사용권자산·리스부채를 올린다.
다라마트는 연장 옵션 없는 1년 계약을 매년 새로 맺어 단기리스 면제(문단 5·6)를
선택한다. 기준서 도입 전(2018년 이전) 방식과 같은 모양으로 임차료가 비용에 남는다.

[1] 리스부채 최초 측정 — 지급되지 않은 리스료의 현재가치(문단 26)
[2] 리스부채 상각표 — 이자로 늘고 지급으로 준다(문단 36)
[3] 연도별 비용 — 감가상각 + 이자 vs 임차료(합계는 같고 시점이 다르다)
[4] 첫해 재무제표 지표 — 부채비율·EBITDA·영업이익·현금흐름 분류(문단 49·50)
[5] 할인율에 따라 리스부채가 얼마나 움직이는가

단순화: 리스료는 매년 말 후급, 초기 직접원가·복구원가·리스 인센티브 없음,
사용권자산은 리스기간에 걸쳐 정액 상각, 법인세 없음. 금액 단위는 억원.
"""
import platform
import sys

ANNUAL_PAYMENT = 100      # 매년 말 지급하는 임차료
LEASE_YEARS = 5
BORROWING_RATE = 0.05     # 가나유통의 증분차입이자율 (내재이자율을 쉽게 알 수 없다고 둔다)

# 리스와 무관한 부분은 두 회사가 똑같다
BASE = {
    "assets": 1_000, "liabilities": 400, "equity": 600,
    "revenue": 1_000, "other_opex": 800, "other_depreciation": 50,  # other_opex 에 감가상각 50 포함
}


def present_value(payment: float, rate: float, years: int) -> float:
    """후급 연금의 현재가치. 매년 말 같은 금액을 years 번 받는다."""
    return sum(payment / (1 + rate) ** t for t in range(1, years + 1))


def amortization_schedule(liability: float, rate: float, payment: float, years: int) -> list[dict]:
    rows = []
    balance = liability
    for year in range(1, years + 1):
        interest = balance * rate
        principal = payment - interest
        closing = balance + interest - payment
        if year == years:
            closing = 0.0  # 반올림 찌꺼기를 지운다 — 마지막 지급으로 부채는 정확히 사라진다
        rows.append({"year": year, "opening": balance, "interest": interest,
                     "principal": principal, "closing": closing})
        balance = closing
    return rows


def print_initial(liability: float) -> None:
    print("[1] 리스개시일 — 리스부채와 사용권자산 최초 측정 (K-IFRS 제1116호 문단 22·24·26)")
    print(f"  리스료 {ANNUAL_PAYMENT} × {LEASE_YEARS}년, 매년 말 지급, 할인율 {BORROWING_RATE:.0%}")
    for t in range(1, LEASE_YEARS + 1):
        pv = ANNUAL_PAYMENT / (1 + BORROWING_RATE) ** t
        print(f"    {t}년 말 지급분 {ANNUAL_PAYMENT} ÷ 1.05^{t} = {pv:7.2f}")
    print(f"  리스부채 = 사용권자산 = {liability:.2f}   (명목 지급 합계 {ANNUAL_PAYMENT * LEASE_YEARS})")
    print()


def print_schedule(rows: list[dict]) -> None:
    print("[2] 리스부채 상각표 (문단 36 — 이자로 늘고 지급으로 준다)")
    print(f"  {'연도':>4}{'기초':>10}{'+ 이자':>10}{'− 지급':>10}{'원금 상환':>10}{'기말':>10}")
    for r in rows:
        print(f"  {r['year']:>4}{r['opening']:>10.2f}{r['interest']:>10.2f}{ANNUAL_PAYMENT:>10.2f}"
              f"{r['principal']:>12.2f}{r['closing']:>10.2f}")
    print(f"  이자 합계 {sum(r['interest'] for r in rows):.2f} · 원금 합계 {sum(r['principal'] for r in rows):.2f}")
    print()


def print_expense_profile(rows: list[dict], rou_depreciation: float) -> None:
    print("[3] 연도별 리스 관련 비용")
    print(f"  {'연도':>4}{'감가상각':>10}{'이자':>10}{'가나 합계':>10}{'다라 임차료':>12}{'차이':>9}")
    total_gana = total_dara = 0.0
    for r in rows:
        gana = rou_depreciation + r["interest"]
        total_gana += gana
        total_dara += ANNUAL_PAYMENT
        print(f"  {r['year']:>4}{rou_depreciation:>12.2f}{r['interest']:>10.2f}{gana:>12.2f}"
              f"{ANNUAL_PAYMENT:>12.2f}{gana - ANNUAL_PAYMENT:>+10.2f}")
    # 부동소수점 오차로 −0.00 이 찍히지 않게 둘째 자리에서 반올림한 뒤 0.0 을 더한다
    gap = round(total_gana - total_dara, 2) + 0.0
    print(f"  합계{'':>32}{total_gana:>10.2f}{total_dara:>12.2f}{gap:>+10.2f}")
    print()


def print_year_one(liability: float, rows: list[dict], rou_depreciation: float) -> None:
    b = BASE
    first = rows[0]

    # 다라마트: 임차료가 영업비용에 그대로 남는다
    dara_op_income = b["revenue"] - b["other_opex"] - ANNUAL_PAYMENT
    dara_ebitda = dara_op_income + b["other_depreciation"]
    dara_liab = b["liabilities"]

    # 가나유통: 임차료 대신 사용권자산 감가상각(영업비용)과 리스부채 이자(금융비용)
    gana_op_income = b["revenue"] - b["other_opex"] - rou_depreciation
    gana_ebitda = gana_op_income + b["other_depreciation"] + rou_depreciation
    gana_pretax = gana_op_income - first["interest"]
    gana_liab_open = b["liabilities"] + liability

    print("[4] 리스개시 직후 재무상태와 첫해 손익·현금흐름")
    print(f"  {'항목':<26}{'다라마트':>10}{'가나유통':>10}")
    lines = [
        ("자산", b["assets"], b["assets"] + liability),
        ("부채", dara_liab, gana_liab_open),
        ("자본", b["equity"], b["equity"]),
        ("부채비율(부채÷자본)", f"{dara_liab / b['equity']:.1%}", f"{gana_liab_open / b['equity']:.1%}"),
        ("", "", ""),
        ("매출", b["revenue"], b["revenue"]),
        ("영업비용(리스 외)", -b["other_opex"], -b["other_opex"]),
        ("임차료", -ANNUAL_PAYMENT, 0),
        ("사용권자산 감가상각", 0, -rou_depreciation),
        ("영업이익", dara_op_income, gana_op_income),
        ("EBITDA", dara_ebitda, gana_ebitda),
        ("리스부채 이자비용", 0, -first["interest"]),
        ("세전이익", dara_op_income, gana_pretax),
        ("", "", ""),
        ("영업활동 현금 유출(임차료/이자)", -ANNUAL_PAYMENT, -first["interest"]),
        ("재무활동 현금 유출(원금)", 0, -first["principal"]),
        ("현금 유출 합계", -ANNUAL_PAYMENT, -(first["interest"] + first["principal"])),
    ]
    for label, d, g in lines:
        if label == "":
            print()
            continue
        fmt = lambda v: f"{v:>10}" if isinstance(v, str) else f"{v:>10.2f}"
        print(f"  {label:<26}{fmt(d)}{fmt(g)}")
    print("  가나유통의 이자 지급은 영업활동으로 분류했다 (K-IFRS 제1007호 문단 33 선택)")
    print()


def print_rate_sensitivity() -> None:
    print("[5] 같은 리스료 100 × 5년, 할인율만 바꾸면")
    print(f"  {'할인율':>6}{'리스부채':>10}{'첫해 이자':>10}{'첫해 감가상각':>12}{'첫해 비용 합계':>12}")
    for rate in (0.03, 0.05, 0.07, 0.10):
        liab = present_value(ANNUAL_PAYMENT, rate, LEASE_YEARS)
        dep = liab / LEASE_YEARS
        interest = liab * rate
        print(f"  {rate:>6.0%}{liab:>12.2f}{interest:>10.2f}{dep:>14.2f}{dep + interest:>14.2f}")
    print()


def main() -> None:
    print(f"Python {platform.python_version()} · {sys.platform}")
    print()
    liability = present_value(ANNUAL_PAYMENT, BORROWING_RATE, LEASE_YEARS)
    rou_depreciation = liability / LEASE_YEARS
    rows = amortization_schedule(liability, BORROWING_RATE, ANNUAL_PAYMENT, LEASE_YEARS)
    print_initial(liability)
    print_schedule(rows)
    print_expense_profile(rows, rou_depreciation)
    print_year_one(liability, rows, rou_depreciation)
    print_rate_sensitivity()


if __name__ == "__main__":
    main()
