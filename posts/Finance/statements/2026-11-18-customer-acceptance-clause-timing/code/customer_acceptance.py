"""고객의 인수 조항 — 문단 38⑸·B83~B86 을 결산일 전후로 계산한다.

가상 회사 사아계측이 12월 결산 직전에 검사 장비 세 건을 인도한다.
세 건 모두 고객의 인수 조항이 붙어 있지만, 조항의 성격이 달라 수익 인식일이 갈린다.
금액 단위: 백만원.
"""

from datetime import date

FISCAL_YEAR_END = date(2026, 12, 31)

# 개별 판매가격 — 계약 A 는 장비와 설치가 별도 수행의무다 (B84 마지막 문장)
STANDALONE = {"장비": 280, "설치": 40}

CONTRACTS = [
    {
        "name": "A 객관적 규격(치수·정밀도)",
        "price": 300,
        "cost": 210,
        "delivered": date(2026, 12, 18),
        "accepted": date(2027, 1, 12),
        "installed": date(2027, 1, 20),
        "install_cost": 20,  # 원가 210 중 설치에 드는 몫, 설치하는 1월에 생긴다
        "objective": True,  # 출하 전 공장 시험으로 규격 충족을 확인할 수 있다
        "trial": False,
        "separate_install": True,
    },
    {
        "name": "B 고객 라인 연동 성능",
        "price": 300,
        "cost": 210,
        "delivered": date(2026, 12, 18),
        "accepted": date(2027, 1, 12),
        "installed": None,
        "objective": False,  # 고객 생산라인에 붙여 봐야만 규격 충족을 안다
        "trial": False,
        "separate_install": False,
    },
    {
        "name": "C 시험·평가용 인도(60일)",
        "price": 300,
        "cost": 210,
        "delivered": date(2026, 12, 1),
        "accepted": date(2027, 1, 15),
        "installed": None,
        "objective": True,
        "trial": True,
        "trial_days": 60,
        "separate_install": False,
    },
]

# 과거 출하 경험 — B84 는 비슷한 계약의 경험을 규격 충족의 증거로 쓸 수 있다고 본다
HISTORY = {
    "A 유형 (공장 시험 통과분)": {"shipped": 120, "rejected": 0},
    "B 유형 (현장 연동 후 판정)": {"shipped": 120, "rejected": 9},
}


def allocate(price):
    """할인을 개별 판매가격 비율로 배분한다 (문단 74·81)."""
    total = sum(STANDALONE.values())
    return {k: price * v / total for k, v in STANDALONE.items()}


def control_dates(c):
    """수행의무별 (이름, 금액, 원가, 통제 이전일, 근거) 목록."""
    if c["trial"]:
        trial_end = date.fromordinal(c["delivered"].toordinal() + c["trial_days"])
        when = min(c["accepted"], trial_end)
        return [("장비", c["price"], c["cost"], when, f"B86 인수일과 시험기간 종료({trial_end}) 중 이른 날")]
    if c["objective"]:
        if c["separate_install"]:
            alloc = allocate(c["price"])
            install_cost = c["install_cost"]
            return [
                ("장비", alloc["장비"], c["cost"] - install_cost, c["delivered"], "B84 인수는 형식적, 인도일"),
                ("설치", alloc["설치"], install_cost, c["installed"], "별도 수행의무, 설치 완료일"),
            ]
        return [("장비", c["price"], c["cost"], c["delivered"], "B84 인수는 형식적, 인도일")]
    return [("장비", c["price"], c["cost"], c["accepted"], "B85 객관적 판단 불가, 인수일")]


def main():
    print("[1] 과거 출하 경험 — 규격 충족의 증거 (B84)")
    for label, h in HISTORY.items():
        rate = h["rejected"] / h["shipped"]
        print(f"  {label}: 출하 {h['shipped']}건, 인수 거절·개선 요구 {h['rejected']}건 ({rate:.1%})")
    print()

    print(f"[2] 수행의무별 통제 이전일 — 결산일 {FISCAL_YEAR_END}")
    fy1 = {"revenue": 0.0, "cost": 0.0}
    fy2 = {"revenue": 0.0, "cost": 0.0}
    inventory_at_ye = 0.0
    receivable_at_ye = 0.0
    for c in CONTRACTS:
        print(f"  {c['name']}  계약가격 {c['price']}  원가 {c['cost']}  인도 {c['delivered']}  인수 {c['accepted']}")
        for po, amount, cost, when, why in control_dates(c):
            bucket = fy1 if when <= FISCAL_YEAR_END else fy2
            bucket["revenue"] += amount
            bucket["cost"] += cost
            year = "1년차" if when <= FISCAL_YEAR_END else "2년차"
            print(f"    {po}  수익 {amount:>6.1f}  인식일 {when}  ({year})  근거: {why}")
            if when <= FISCAL_YEAR_END:
                receivable_at_ye += amount
            elif po == "장비":
                # 설치원가는 1월에 생기므로 결산일 재고에 들어가지 않는다
                inventory_at_ye += cost
    print()

    print("[3] 1년차·2년차 손익 — 세 건 합계")
    for label, b in (("1년차", fy1), ("2년차", fy2)):
        print(f"  {label}  수익 {b['revenue']:>6.1f}  매출원가 {b['cost']:>6.1f}  이익 {b['revenue'] - b['cost']:>6.1f}")
    print()

    print("[4] 1년차 말 재무상태표에 남는 것")
    print(f"  수익을 인식한 금액(청구 조건에 따라 수취채권 또는 계약자산) {receivable_at_ye:.1f}")
    print(f"  고객 현장에 있으나 아직 회사 재고인 장비 원가 {inventory_at_ye:.1f}")


if __name__ == "__main__":
    main()
