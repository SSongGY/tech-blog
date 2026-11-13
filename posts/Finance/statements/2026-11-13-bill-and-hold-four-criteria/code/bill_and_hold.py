"""미인도청구약정을 기업회계기준서 제1115호 문단 B79~B82 에 따라 처리한다.

가상 회사 타파기계가 포장 설비 5대를 4,800 에 만들어 2026년 12월 말에 완성하고
대금을 받는다. 고객 공장 증설이 늦어져 설비는 2027년 6월 말까지 타파기계 창고에 둔다.
B81 의 네 기준을 모두 충족하는 경우와 하나가 빠지는 경우를 비교한다.
단위는 백만원이다. 숫자는 계산을 보이려고 만든 가상 자료다.
"""

import sys

UNITS = 5
CONTRACT_PRICE = 4_800.0
TOTAL_COST = 3_500.0
# 개별 판매가격 (가정). 거래가격을 이 비율로 나눈다 (문단 73~86, B82).
SSP_MACHINES = 4_750.0
SSP_STORAGE = 250.0
STORAGE_MONTHS = 6
# 분기: 2026Q4 에 완성·청구, 2027Q1~Q2 동안 보관, 2027Q2 말 인도
QUARTERS = ["2026Q4", "2027Q1", "2027Q2"]

CRITERIA = [
    "⑴ 약정 이유가 실질적(고객 요청)",
    "⑵ 고객 소유물로 구분 식별",
    "⑶ 지금 물리적으로 이전할 준비",
    "⑷ 기업이 쓰거나 다른 고객에게 넘길 수 없음",
]


def control_transferred(flags):
    """B81: 문단 38 을 적용하는 것 외에 네 기준을 '모두' 충족해야 고객이 통제한다."""
    return all(flags)


def allocate():
    """B82: 보관 용역이 별도 수행의무이면 개별 판매가격 비율로 거래가격을 나눈다."""
    total_ssp = SSP_MACHINES + SSP_STORAGE
    machines = CONTRACT_PRICE * SSP_MACHINES / total_ssp
    storage = CONTRACT_PRICE * SSP_STORAGE / total_ssp
    return machines, storage


def case_bill_and_hold():
    machines, storage = allocate()
    per_quarter = storage / (STORAGE_MONTHS / 3)
    return {
        "2026Q4": {"설비 매출": machines, "보관 용역 매출": 0.0, "매출원가": -TOTAL_COST},
        "2027Q1": {"설비 매출": 0.0, "보관 용역 매출": per_quarter, "매출원가": 0.0},
        "2027Q2": {"설비 매출": 0.0, "보관 용역 매출": per_quarter, "매출원가": 0.0},
    }


def case_not_transferred():
    """통제가 넘어가지 않았으면 설비는 기업의 재고이고, 보관은 자기 재고를 두는 일일 뿐이다."""
    return {
        "2026Q4": {"설비 매출": 0.0, "보관 용역 매출": 0.0, "매출원가": 0.0},
        "2027Q1": {"설비 매출": 0.0, "보관 용역 매출": 0.0, "매출원가": 0.0},
        "2027Q2": {"설비 매출": CONTRACT_PRICE, "보관 용역 매출": 0.0, "매출원가": -TOTAL_COST},
    }


def print_rows(label, rows):
    print(f"  {label}")
    by_year = {}
    for q in QUARTERS:
        r = rows[q]
        profit = sum(r.values())
        by_year[q[:4]] = by_year.get(q[:4], 0.0) + profit
        print(f"    {q}  설비 {r['설비 매출']:>8,.1f}  보관 {r['보관 용역 매출']:>6,.1f}"
              f"  매출원가 {r['매출원가']:>8,.1f}  이익 {profit:>8,.1f}")
    years = "  ".join(f"{y}년 이익 {v:>8,.1f}" for y, v in by_year.items())
    print(f"    {years}")


def main():
    print(f"[0] 환경  Python {sys.version.split()[0]}")
    print()
    print("[1] B81 네 기준과 통제 이전 판단")
    variants = [
        ("가. 네 기준 모두 충족", [True, True, True, True]),
        ("나. 기업이 출고 일정을 맞추려고 먼저 청구", [False, True, True, True]),
        ("다. 같은 모델 재고와 섞어 보관", [True, False, True, True]),
        ("라. 마지막 시운전이 남음", [True, True, False, True]),
        ("마. 급한 다른 주문에 돌려쓸 수 있음", [True, True, True, False]),
    ]
    for name, flags in variants:
        marks = " ".join("O" if f else "X" for f in flags)
        result = "통제 이전 -> 지금 수익" if control_transferred(flags) else "통제 미이전 -> 인도 때 수익"
        print(f"    {name:<26} {marks}   {result}")
    print("    (O/X 순서: " + " / ".join(CRITERIA) + ")")
    print()

    machines, storage = allocate()
    print("[2] 거래가격 배분 (B82, 개별 판매가격 비율)")
    print(f"    개별 판매가격  설비 {SSP_MACHINES:,.1f}  보관 {SSP_STORAGE:,.1f}"
          f"  합계 {SSP_MACHINES + SSP_STORAGE:,.1f}")
    print(f"    거래가격 {CONTRACT_PRICE:,.1f} -> 설비 {machines:,.1f}  보관 {storage:,.1f}"
          f"  (월 {storage / STORAGE_MONTHS:,.1f})")
    print()

    print(f"[3] 설비 {UNITS}대, 2026년 12월 말 완성·대금 수령, 2027년 6월 말 인도")
    print_rows("가. 네 기준 충족 — 미인도청구 판매", case_bill_and_hold())
    print_rows("마. 기준 ⑷ 미충족 — 인도 때 판매", case_not_transferred())
    print()

    print("[4] 2026년 말 재무상태표에서 갈리는 줄 (대금 4,800 은 둘 다 받았다)")
    print(f"    가. 재고 {0.0:>8,.1f}  계약부채 {storage:>8,.1f}  (남은 보관 용역)")
    print(f"    마. 재고 {TOTAL_COST:>8,.1f}  계약부채 {CONTRACT_PRICE:>8,.1f}  (설비 전체)")


if __name__ == "__main__":
    main()
