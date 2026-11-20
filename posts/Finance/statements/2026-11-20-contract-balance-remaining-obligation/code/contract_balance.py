"""계약 잔액과 나머지 수행의무 공시 — 기업회계기준서 제1115호 문단 116~122.

가상 회사 마바소프트의 한 해 거래로
  1) 계약부채·계약자산의 기초 → 기말 변동표(문단 116·118)를 만들고
  2) 기말 나머지 수행의무(문단 120)를 기간별로 나누며
  3) 실무적 간편법(문단 121)을 쓰면 공시 금액이 어떻게 바뀌는지 계산한다.
금액 단위 억원.
"""

# ── 1. 계약부채 변동 ─────────────────────────────────────────────
CL_OPENING = 300
CL_TO_REVENUE_FROM_OPENING = 260   # 문단 116⑵ 기초 잔액 중 당기 수익 인식
CL_NEW_ADVANCES = 420              # 당기에 이행 전에 받을 권리가 생긴 선청구액
CL_TO_REVENUE_FROM_NEW = 250       # 당기 선청구액 중 당기 수익 인식
CL_BUSINESS_COMBINATION = 30       # 문단 118⑴ 사업결합으로 넘어온 계약부채

# ── 2. 계약자산 변동 ─────────────────────────────────────────────
CA_OPENING = 80
CA_REVENUE_BEFORE_BILLING = 150    # 청구 전에 진행률로 인식한 수익
CA_CATCH_UP = -12                  # 문단 118⑵ 진행률 추정 변경에 따른 누적효과 일괄조정
CA_TO_RECEIVABLE = 140             # 문단 118⑷ 청구 조건 충족으로 수취채권 재분류
CA_IMPAIRMENT = 3                  # 문단 118⑶ 계약자산 손상

# ── 3. 그 밖의 당기 수익 ─────────────────────────────────────────
PRIOR_PO_REVENUE = 8               # 문단 116⑶ 전기에 이행한 수행의무의 거래가격 변동
BILLED_AS_RECOGNISED = 344         # 인식과 동시에 청구한 수익 (계약 잔액을 거치지 않음)

RECEIVABLE_OPENING = 120
RECEIVABLE_CLOSING = 135

# ── 4. 기말 나머지 수행의무 ──────────────────────────────────────
# (이름, 설명, 남은 금액, 1년 이내, 1~2년, 2년 초과, 간편법 근거)
# 간편법 근거가 None 이 아니면 문단 121 에 따라 공시에서 뺄 수 있다.
REMAINING = [
    ("A", "3년 구독 고정가격, 남은 24개월 × 10", 240, 120, 120, 0, None),
    ("D", "5년 구독 고정가격, 남은 40개월 × 6", 240, 72, 72, 96, None),
    ("B", "12개월 유지보수, 남은 7개월 × 8", 56, 56, 0, 0, "121⑴ 최초 예상 존속 기간 1년 이내"),
    ("C", "투입시간 정산 구축 용역, 남은 예상분", 90, 90, 0, 0, "121⑵ B16 청구권 간편법"),
]
CONSTRAINED_VARIABLE = 30          # 문단 122 제약되어 거래가격에 넣지 않은 성과 보수


def print_rollforward(title, opening, moves):
    print(title)
    print(f"  {'기초 잔액':<34}{opening:>6}")
    balance = opening
    for label, amount in moves:
        balance += amount
        print(f"  {label:<34}{amount:>+6}")
    print(f"  {'기말 잔액':<34}{balance:>6}")
    print()
    return balance


def main():
    cl_closing = print_rollforward(
        "[1] 계약부채 변동표 — 문단 116⑴·⑵, 118",
        CL_OPENING,
        [
            ("기초 잔액 중 당기 수익 인식 116⑵", -CL_TO_REVENUE_FROM_OPENING),
            ("당기 선청구", CL_NEW_ADVANCES),
            ("당기 선청구 중 당기 수익 인식", -CL_TO_REVENUE_FROM_NEW),
            ("사업결합 118⑴", CL_BUSINESS_COMBINATION),
        ],
    )
    ca_closing = print_rollforward(
        "[2] 계약자산 변동표 — 문단 116⑴, 118",
        CA_OPENING,
        [
            ("청구 전 수익 인식", CA_REVENUE_BEFORE_BILLING),
            ("누적효과 일괄조정 118⑵", CA_CATCH_UP),
            ("수취채권으로 재분류 118⑷", -CA_TO_RECEIVABLE),
            ("손상 118⑶", -CA_IMPAIRMENT),
        ],
    )

    print("[3] 문단 116⑴ 기초·기말 잔액")
    print(f"  {'':<10}{'기초':>6}{'기말':>6}")
    print(f"  {'수취채권':<10}{RECEIVABLE_OPENING:>6}{RECEIVABLE_CLOSING:>6}")
    print(f"  {'계약자산':<10}{CA_OPENING:>6}{ca_closing:>6}")
    print(f"  {'계약부채':<10}{CL_OPENING:>6}{cl_closing:>6}")
    print()

    # 수익 출처를 다 더하면 손익계산서의 고객과의 계약 수익과 같아야 한다.
    sources = [
        ("기초 계약부채에서 116⑵", CL_TO_REVENUE_FROM_OPENING),
        ("당기 선청구에서", CL_TO_REVENUE_FROM_NEW),
        ("청구 전 인식(계약자산)", CA_REVENUE_BEFORE_BILLING + CA_CATCH_UP),
        ("전기 이행분 거래가격 변동 116⑶", PRIOR_PO_REVENUE),
        ("인식과 동시에 청구", BILLED_AS_RECOGNISED),
    ]
    print("[4] 당기 수익의 출처")
    for label, amount in sources:
        print(f"  {label:<30}{amount:>6}")
    revenue = sum(a for _, a in sources)
    print(f"  {'고객과의 계약 수익 합계':<30}{revenue:>6}")
    ratio = CL_TO_REVENUE_FROM_OPENING / CL_OPENING * 100
    print(f"  기초 계약부채 중 당기에 수익이 된 비율  {CL_TO_REVENUE_FROM_OPENING} / {CL_OPENING} = {ratio:.1f}%")
    print()

    print("[5] 기말 나머지 수행의무 — 문단 120")
    print("  계약  금액  1년이내 1~2년 2년초과  간편법")
    for name, desc, amt, y1, y2, y3, expedient in REMAINING:
        assert y1 + y2 + y3 == amt
        print(f"  {name:<4}{amt:>6}{y1:>8}{y2:>6}{y3:>7}  {expedient or '-'}")
        print(f"      {desc}")
    print()

    def buckets(rows):
        return (sum(r[2] for r in rows), sum(r[3] for r in rows),
                sum(r[4] for r in rows), sum(r[5] for r in rows))

    full = buckets(REMAINING)
    disclosed = buckets([r for r in REMAINING if r[6] is None])
    print("[6] 간편법 적용 전후 — 문단 121")
    print(f"  {'':<16}{'합계':>6}{'1년이내':>8}{'1~2년':>6}{'2년초과':>7}")
    print(f"  {'간편법 미적용':<14}{full[0]:>6}{full[1]:>8}{full[2]:>6}{full[3]:>7}")
    print(f"  {'간편법 적용(공시)':<12}{disclosed[0]:>6}{disclosed[1]:>8}{disclosed[2]:>6}{disclosed[3]:>7}")
    print(f"  빠진 금액 {full[0] - disclosed[0]} — 전부 1년 이내 몫이다")
    print(f"  공시된 1년 이내 금액 / 당기 수익 = {disclosed[1]} / {revenue} = {disclosed[1] / revenue * 100:.1f}%")
    print(f"  미적용 1년 이내 금액 / 당기 수익 = {full[1]} / {revenue} = {full[1] / revenue * 100:.1f}%")
    print(f"  거래가격에서 빠진 제약 변동대가 {CONSTRAINED_VARIABLE} — 문단 122 질적 설명 대상")


if __name__ == "__main__":
    main()
