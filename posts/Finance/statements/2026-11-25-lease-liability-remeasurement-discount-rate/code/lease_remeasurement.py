"""리스부채 재측정 — 할인율을 바꾸는 경우와 그대로 두는 경우.

가상 회사 가나유통이 매장을 5년 빌린 리스를 2년차 말에 다시 잰다.
K-IFRS 제1116호 문단 39~43 이 고르는 할인율에 따라 리스부채·사용권자산·
남은 기간 비용이 어떻게 달라지는지 계산한다. 표준 라이브러리만 쓴다.
"""

import platform

ORIGINAL_RATE = 0.05   # 리스개시일 증분차입이자율
REVISED_RATE = 0.07    # 2년차 말 재평가일의 증분차입이자율
ANNUAL_PAYMENT = 100.0
LEASE_YEARS = 5
REASSESS_AFTER_YEAR = 2


def present_value(payments, rate):
    # 리스료는 매년 말 후급이라 t 년 뒤 지급액을 (1+r)^t 로 나눈다
    return sum(p / (1 + rate) ** t for t, p in enumerate(payments, start=1))


def amortise(liability, payments, rate):
    rows = []
    for year, payment in enumerate(payments, start=1):
        interest = liability * rate
        closing = liability + interest - payment
        rows.append((year, liability, interest, payment, closing))
        liability = closing
    return rows


def print_schedule(title, rows, year_offset=0):
    print(title)
    print(f"  {'연도':>4} {'기초':>9} {'이자':>8} {'지급':>8} {'기말':>9}")
    for year, opening, interest, payment, closing in rows:
        print(f"  {year + year_offset:>4} {opening:>9.2f} {interest:>8.2f}"
              f" {payment:>8.2f} {abs(closing):>9.2f}")
    print()


def remeasure(name, paragraph, payments, rate, liability_before, rou_before,
              remaining_years):
    new_liability = present_value(payments, rate)
    adjustment = new_liability - liability_before
    new_rou = rou_before + adjustment
    # 사용권자산은 남은 기간에 정액 상각한다(문단 31 → 제1016호)
    depreciation = new_rou / remaining_years
    rows = amortise(new_liability, payments, rate)
    total_interest = sum(r[2] for r in rows)
    return {
        "name": name, "paragraph": paragraph, "rate": rate,
        "liability": new_liability, "adjustment": adjustment,
        "rou": new_rou, "depreciation": depreciation, "rows": rows,
        "first_interest": rows[0][2], "total_interest": total_interest,
        "total_expense": total_interest + new_rou,
        "total_cash": sum(payments),
    }


def main():
    print("[0] 환경")
    print(f"  Python {platform.python_version()}")
    print("  가상 회사: 가나유통 (실재 기업 아님)")
    print(f"  리스료 {ANNUAL_PAYMENT:.0f} × {LEASE_YEARS}년 후급, 개시일 할인율 "
          f"{ORIGINAL_RATE:.0%}, 재평가일 증분차입이자율 {REVISED_RATE:.0%}")
    print()

    payments = [ANNUAL_PAYMENT] * LEASE_YEARS
    liability0 = present_value(payments, ORIGINAL_RATE)
    rows = amortise(liability0, payments, ORIGINAL_RATE)
    print(f"[1] 리스개시일 리스부채 = 사용권자산 원가 = {liability0:.2f}")
    print_schedule("[2] 재평가 전 상각표 (1~2년차만 실제로 흘렀다)",
                   rows[:REASSESS_AFTER_YEAR])

    liability_before = rows[REASSESS_AFTER_YEAR - 1][4]
    depreciation0 = liability0 / LEASE_YEARS
    rou_before = liability0 - depreciation0 * REASSESS_AFTER_YEAR
    remaining = LEASE_YEARS - REASSESS_AFTER_YEAR
    print("[3] 2년차 말 재평가 직전 장부")
    print(f"  리스부채 {liability_before:.2f} · 사용권자산 {rou_before:.2f}"
          f" (연 감가상각 {depreciation0:.2f})")
    print()

    # 사건 A: 물가지수 연동 조항으로 3년차부터 리스료가 6% 오른다
    index_payments = [ANNUAL_PAYMENT * 1.06] * remaining
    # 사건 B: 대규모 인테리어 후 2년 연장선택권 행사가 상당히 확실해졌다
    extension_payments = [ANNUAL_PAYMENT] * (remaining + 2)

    cases = [
        remeasure("A 지수 변동, 원래 할인율", "42⑵·43", index_payments,
                  ORIGINAL_RATE, liability_before, rou_before, remaining),
        remeasure("A 지수 변동, 수정 할인율(잘못)", "-", index_payments,
                  REVISED_RATE, liability_before, rou_before, remaining),
        remeasure("B 기간 연장, 수정 할인율", "40⑴·41", extension_payments,
                  REVISED_RATE, liability_before, rou_before, remaining + 2),
        remeasure("B 기간 연장, 원래 할인율(잘못)", "-", extension_payments,
                  ORIGINAL_RATE, liability_before, rou_before, remaining + 2),
    ]

    print("[4] 재측정 결과 — 같은 사건을 두 할인율로")
    print(f"  {'사건 · 할인율':<26} {'문단':>8} {'새 부채':>9} {'조정액':>8}"
          f" {'사용권자산':>10} {'연 상각':>8}")
    for c in cases:
        print(f"  {c['name']:<26} {c['paragraph']:>8} {c['liability']:>9.2f}"
              f" {c['adjustment']:>+8.2f} {c['rou']:>10.2f}"
              f" {c['depreciation']:>8.2f}")
    print("  조정액은 전액 사용권자산에 더한다 (문단 39) — 재측정 시점 손익 영향 0")
    print()

    print("[5] 재측정 뒤 남은 기간의 비용 — 총액은 같고 이름이 갈린다")
    print(f"  {'사건 · 할인율':<26} {'첫해 이자':>9} {'이자 합계':>9}"
          f" {'상각 합계':>9} {'비용 합계':>9} {'현금 합계':>9}")
    for c in cases:
        print(f"  {c['name']:<26} {c['first_interest']:>9.2f}"
              f" {c['total_interest']:>9.2f} {c['rou']:>9.2f}"
              f" {c['total_expense']:>9.2f} {c['total_cash']:>9.2f}")
    print()

    print_schedule("[6] 사건 B 재측정 뒤 상각표 (수정 할인율 7%)",
                   cases[2]["rows"], year_offset=REASSESS_AFTER_YEAR)

    print("[7] 사건 B 를 재평가일 할인율별로 — 금리가 오른 해의 재측정은 부채를 덜 늘린다")
    print(f"  {'할인율':>6} {'새 부채':>9} {'조정액':>8} {'남은 기간 이자':>12}")
    for rate in (0.03, 0.05, 0.07, 0.09):
        c = remeasure("", "", extension_payments, rate, liability_before,
                      rou_before, remaining + 2)
        print(f"  {rate:>6.0%} {c['liability']:>9.2f} {c['adjustment']:>+8.2f}"
              f" {c['total_interest']:>12.2f}")
    print()

    # 문단 39 끝 문장: 부채 감소가 사용권자산보다 크면 남는 몫은 당기손익
    print("[8] 부채가 줄어드는 재측정 — 사용권자산이 0 아래로 가지 않는다 (문단 39)")
    rou_small = 20.0
    decrease = 35.0
    to_profit = max(0.0, decrease - rou_small)
    print(f"  사용권자산 {rou_small:.2f}, 재측정으로 부채 {decrease:.2f} 감소")
    print(f"  사용권자산 조정 -{min(rou_small, decrease):.2f} → 0.00,"
          f" 남는 {to_profit:.2f} 은 당기손익(이익)")


if __name__ == "__main__":
    main()
