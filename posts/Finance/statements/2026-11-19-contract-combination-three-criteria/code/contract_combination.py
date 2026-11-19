"""계약의 결합 — 기업회계기준서 제1115호 문단 17 을 계산한다.

가상 회사 타파정밀이 장비와 2년 유지보수를 따로따로 계약서로 판다.
계약서가 둘이어도 문단 17 의 기준을 하나라도 충족하면 하나의 계약으로 회계처리한다.
결합하면 할인이 두 계약에 다시 배분되어 연도별 수익이 달라진다.
금액 단위: 백만원.
"""

# 계약 쌍마다 문단 17 의 전제(같은 고객·특수관계자, 동시·가까운 시기)와 세 기준을 적는다
PAIRS = [
    {"name": "P 장비+유지보수, 한 번의 협상", "same_party": "같은 고객",
     "days_apart": 3, "c1": True, "c2": False, "c3": False},
    {"name": "Q 유지보수 요금이 장비 가동률에 연동", "same_party": "같은 고객",
     "days_apart": 0, "c1": False, "c2": True, "c3": False},
    {"name": "R 설계 계약+제작 계약, 통합해 한 설비", "same_party": "같은 고객",
     "days_apart": 10, "c1": False, "c2": False, "c3": True},
    {"name": "S 고객의 종속기업과 같은 주 일괄 협상", "same_party": "특수관계자",
     "days_apart": 5, "c1": True, "c2": False, "c3": False},
    {"name": "T 8개월 뒤 별도 입찰로 추가 장비", "same_party": "같은 고객",
     "days_apart": 240, "c1": False, "c2": False, "c3": False},
]

CRITERIA = {
    "c1": "⑴ 하나의 상업적 목적으로 일괄 협상",
    "c2": "⑵ 한 계약의 대가가 다른 계약의 가격·수행에 따라 달라짐",
    "c3": "⑶ 약속한 재화·용역이 단일 수행의무",
}

# 계약 쌍 P 의 금액 — 계약서 가격과 개별 판매가격
EQUIPMENT = {"price": 400, "standalone": 600}   # 1년차 1월 인도, 한 시점 이행
MAINTENANCE = {"price": 500, "standalone": 400, "years": 2}  # 1월부터 24개월, 기간에 걸쳐 이행


def combine_decision(p):
    """문단 17 — 전제를 갖추고 세 기준 중 하나 이상이면 결합한다."""
    near = p["days_apart"] <= 30  # '가까운 시기'를 기준서는 숫자로 정하지 않는다. 예제의 가정이다
    hits = [CRITERIA[k] for k in ("c1", "c2", "c3") if p[k]]
    if not near:
        return False, "동시·가까운 시기가 아니다", hits
    if not hits:
        return False, "세 기준 모두 해당 없음", hits
    return True, "세 기준 중 하나 이상 충족", hits


def yearly_revenue(equipment_amt, maintenance_amt, years):
    """장비는 1년차에, 유지보수는 기간 정액으로 인식한다."""
    per_year = maintenance_amt / years
    return [equipment_amt + per_year] + [per_year] * (years - 1)


def main():
    print("[1] 계약 쌍별 결합 판정 — 문단 17")
    for p in PAIRS:
        ok, why, hits = combine_decision(p)
        print(f"  {p['name']}  ({p['same_party']}, {p['days_apart']}일 간격)")
        for h in hits:
            print(f"      해당: {h}")
        print(f"      → {'결합한다' if ok else '따로 회계처리'}  ({why})")
    print()

    total_price = EQUIPMENT["price"] + MAINTENANCE["price"]
    total_ssp = EQUIPMENT["standalone"] + MAINTENANCE["standalone"]
    discount = total_ssp - total_price
    print("[2] 계약 쌍 P — 계약서 가격과 개별 판매가격")
    print(f"  장비      계약서 {EQUIPMENT['price']:>5}  개별 판매가격 {EQUIPMENT['standalone']:>5}")
    print(f"  유지보수  계약서 {MAINTENANCE['price']:>5}  개별 판매가격 {MAINTENANCE['standalone']:>5}")
    print(f"  합계      계약서 {total_price:>5}  개별 판매가격 {total_ssp:>5}  할인 {discount}")
    print()

    # 따로 회계처리: 계약서마다 수행의무가 하나라 계약서 가격이 곧 배분액이다
    sep = {"장비": EQUIPMENT["price"], "유지보수": MAINTENANCE["price"]}
    # 결합: 거래가격 900 을 개별 판매가격 비율로 배분한다 (문단 74·76·81)
    comb = {
        "장비": total_price * EQUIPMENT["standalone"] / total_ssp,
        "유지보수": total_price * MAINTENANCE["standalone"] / total_ssp,
    }
    print("[3] 수행의무별 배분액")
    print("  수행의무   따로   결합   차이")
    for k in sep:
        print(f"  {k:<6} {sep[k]:>6.0f} {comb[k]:>6.0f} {comb[k] - sep[k]:>+6.0f}")
    print()

    years = MAINTENANCE["years"]
    rs = yearly_revenue(sep["장비"], sep["유지보수"], years)
    rc = yearly_revenue(comb["장비"], comb["유지보수"], years)
    print("[4] 연도별 수익")
    print("  연도    따로   결합   차이")
    for i in range(years):
        print(f"  {i + 1}년차  {rs[i]:>6.0f} {rc[i]:>6.0f} {rc[i] - rs[i]:>+6.0f}")
    print(f"  합계   {sum(rs):>6.0f} {sum(rc):>6.0f} {sum(rc) - sum(rs):>+6.0f}")
    print()

    # 1년차 말 계약부채 — 두 계약서 대가 900 을 1월에 전액 받았다고 가정
    print("[5] 1년차 말 계약부채 (두 계약서 대가 900 을 1월에 전액 받았다고 가정)")
    received = MAINTENANCE["price"]
    for label, alloc in (("따로", sep), ("결합", comb)):
        recognized = alloc["유지보수"] / years
        # 결합하면 받은 돈과 배분액이 어긋나므로, 계약 전체로 계약자산·부채를 본다
        contract_total_recognized = alloc["장비"] + recognized
        total_received = EQUIPMENT["price"] + received
        net = total_received - contract_total_recognized
        print(f"  {label}  누적 인식 수익 {contract_total_recognized:>5.0f}"
              f"  받은 대가 {total_received:>5}  계약부채 {net:>5.0f}")


if __name__ == "__main__":
    main()
