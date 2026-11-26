"""판매후리스 — 처분이익 중 계속 쓰는 몫은 인식하지 않는다.

가상 회사 가나물산이 본사 건물을 팔고 그 건물을 10년 다시 빌린다.
K-IFRS 제1116호 문단 98~103 에 따라 사용권자산과 처분이익을 계산하고,
판매가격이 공정가치와 다른 경우와 판매가 아닌 경우를 나란히 놓는다.
표준 라이브러리만 쓴다.
"""

import platform

CARRYING_AMOUNT = 600.0   # 건물의 종전 장부금액
FAIR_VALUE = 1000.0       # 판매일의 건물 공정가치
RATE = 0.05               # 리스의 내재이자율
LEASE_YEARS = 10
MARKET_PAYMENT = 60.0     # 시장 수준의 연 리스료 (매년 말 지급)


def present_value(payment, years, rate=RATE):
    return sum(payment / (1 + rate) ** t for t in range(1, years + 1))


def account_sale(name, sale_price, payment, years=LEASE_YEARS):
    """이전이 판매에 해당할 때의 판매자-리스이용자 회계처리 (문단 100·101)."""
    pv_payments = present_value(payment, years)
    # 문단 102⑴: 판매대가와 자산 공정가치의 차이로 조정액을 잰다
    difference = sale_price - FAIR_VALUE
    additional_financing = max(difference, 0.0)   # 문단 101⑵
    prepaid_lease = abs(min(difference, 0.0))     # 문단 101⑴
    lease_liability = pv_payments - additional_financing
    # 사용권의 대가 = 리스부채 + 리스료를 미리 낸 것으로 보는 금액
    retained_value = lease_liability + prepaid_lease
    retained_ratio = retained_value / FAIR_VALUE
    right_of_use = CARRYING_AMOUNT * retained_ratio   # 문단 100⑴
    total_gain = FAIR_VALUE - CARRYING_AMOUNT
    recognised_gain = total_gain * (1 - retained_ratio)
    return {
        "name": name, "sale_price": sale_price, "payment": payment,
        "years": years, "pv_payments": pv_payments,
        "additional_financing": additional_financing,
        "prepaid_lease": prepaid_lease, "lease_liability": lease_liability,
        "retained_ratio": retained_ratio, "right_of_use": right_of_use,
        "total_gain": total_gain, "recognised_gain": recognised_gain,
        "unrecognised_gain": total_gain - recognised_gain,
    }


def print_entry(result):
    debit = [("현금", result["sale_price"]),
             ("사용권자산", result["right_of_use"])]
    credit = [("건물", CARRYING_AMOUNT),
              ("리스부채", result["lease_liability"])]
    if result["additional_financing"]:
        credit.append(("금융부채(추가 금융)", result["additional_financing"]))
    credit.append(("처분이익", result["recognised_gain"]))
    print(f"  {result['name']}")
    for label, amount in debit:
        print(f"    (차) {label:<14} {amount:>9.2f}")
    for label, amount in credit:
        print(f"        (대) {label:<14} {amount:>9.2f}")
    total_debit = sum(a for _, a in debit)
    total_credit = sum(a for _, a in credit)
    print(f"    차변 합계 {total_debit:.2f} · 대변 합계 {total_credit:.2f}")
    print()


def main():
    print("[0] 환경")
    print(f"  Python {platform.python_version()}")
    print("  가상 회사: 가나물산 (실재 기업 아님)")
    print(f"  건물 장부금액 {CARRYING_AMOUNT:.0f}, 공정가치 {FAIR_VALUE:.0f}, "
          f"리스 {LEASE_YEARS}년 후급, 내재이자율 {RATE:.0%}")
    print()

    case_a = account_sale("A 공정가치로 판매, 시장 리스료", 1000.0, MARKET_PAYMENT)
    case_b = account_sale("B 공정가치보다 100 비싸게 판매", 1100.0, 73.0)
    case_c = account_sale("C 공정가치보다 100 싸게 판매", 900.0, 47.0)
    cases = [case_a, case_b, case_c]

    print("[1] 사례 A — 계속 보유하는 사용권의 비율")
    print(f"  리스료 현재가치   {case_a['pv_payments']:.2f}"
          f"  (= {MARKET_PAYMENT:.0f} × 연금현가계수 "
          f"{present_value(1.0, LEASE_YEARS):.4f})")
    print(f"  보유 비율         {case_a['retained_ratio']:.2%}"
          f"  (= {case_a['pv_payments']:.2f} ÷ {FAIR_VALUE:.0f})")
    print(f"  사용권자산        {case_a['right_of_use']:.2f}"
          f"  (= 장부금액 {CARRYING_AMOUNT:.0f} × 보유 비율)")
    print(f"  처분이익 총액     {case_a['total_gain']:.2f}"
          f"  (= {FAIR_VALUE:.0f} - {CARRYING_AMOUNT:.0f})")
    print(f"  인식하는 이익     {case_a['recognised_gain']:.2f}"
          f"  (이전한 권리 {1 - case_a['retained_ratio']:.2%})")
    print(f"  인식하지 않는 몫  {case_a['unrecognised_gain']:.2f}")
    print()

    print("[2] 판매일 분개 — 판매자-리스이용자")
    for result in cases:
        print_entry(result)

    print("[3] 세 사례 비교 — 판매가격이 달라도 처분이익은 거의 같다")
    print(f"  {'사례':<4} {'판매가':>8} {'연 리스료':>8} {'리스료 PV':>9} "
          f"{'추가 금융':>8} {'선급리스료':>8} {'리스부채':>9} "
          f"{'사용권자산':>9} {'인식 이익':>9}")
    for label, r in zip("ABC", cases):
        print(f"  {label:<4} {r['sale_price']:>9.2f} {r['payment']:>10.2f} "
              f"{r['pv_payments']:>10.2f} {r['additional_financing']:>10.2f} "
              f"{r['prepaid_lease']:>11.2f} {r['lease_liability']:>11.2f} "
              f"{r['right_of_use']:>12.2f} {r['recognised_gain']:>11.2f}")
    naive_b = 1100.0 - CARRYING_AMOUNT
    print(f"  조정이 없다면 B 의 처분이익 총액은 {naive_b:.2f} "
          f"(= 1100 - {CARRYING_AMOUNT:.0f}) 로 보인다")
    print()

    print("[4] 인식하지 않은 몫은 남은 기간의 감가상각비에서 돌아온다 (사례 A)")
    depreciation = case_a["right_of_use"] / LEASE_YEARS
    depreciation_at_pv = case_a["pv_payments"] / LEASE_YEARS
    print(f"  사용권자산 {case_a['right_of_use']:.2f} → 연 상각 {depreciation:.2f}")
    print(f"  리스부채와 같은 금액으로 쟀다면 {case_a['pv_payments']:.2f} "
          f"→ 연 상각 {depreciation_at_pv:.2f}")
    saved = (depreciation_at_pv - depreciation) * LEASE_YEARS
    print(f"  연 차이 {depreciation_at_pv - depreciation:.2f} × {LEASE_YEARS}년 "
          f"= {saved:.2f} (인식하지 않은 몫 "
          f"{case_a['unrecognised_gain']:.2f}와 같다)")
    print()

    print("[5] 리스기간별 — 오래 빌릴수록 판매일의 이익이 줄어든다")
    print(f"  {'리스기간':>6} {'리스료 PV':>9} {'보유 비율':>8} "
          f"{'사용권자산':>9} {'인식 이익':>9} {'미인식':>9}")
    for years in (3, 5, 10, 15, 20):
        r = account_sale("", 1000.0, MARKET_PAYMENT, years)
        print(f"  {years:>6}년 {r['pv_payments']:>11.2f} "
              f"{r['retained_ratio']:>10.2%} {r['right_of_use']:>12.2f} "
              f"{r['recognised_gain']:>11.2f} {r['unrecognised_gain']:>10.2f}")
    print()

    print("[6] 이전이 판매가 아닌 경우 (문단 103) — 사례 A 와 같은 현금 1000")
    print("    (차) 현금             1000.00")
    print("        (대) 금융부채         1000.00")
    print("  건물은 장부금액 600.00 그대로 남고 처분이익은 0.00")
    print()
    print(f"  {'':<14} {'판매 (사례 A)':>12} {'판매 아님':>10}")
    rows = [
        ("건물", 0.0, CARRYING_AMOUNT),
        ("사용권자산", case_a["right_of_use"], 0.0),
        ("리스부채", case_a["lease_liability"], 0.0),
        ("금융부채", 0.0, 1000.0),
        ("판매일 이익", case_a["recognised_gain"], 0.0),
    ]
    for label, sale, not_sale in rows:
        print(f"  {label:<12} {sale:>14.2f} {not_sale:>12.2f}")


if __name__ == "__main__":
    main()
