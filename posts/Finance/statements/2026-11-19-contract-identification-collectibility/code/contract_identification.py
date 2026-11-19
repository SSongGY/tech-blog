"""계약의 식별 — 기업회계기준서 제1115호 문단 9~16 을 분기별로 계산한다.

가상 회사 자차소재가 고객 넷과 같은 조건의 공급 계약을 맺는다.
분기마다 250 어치를 인도하는 1년 계약(총 1,000)이다.
문단 9 의 다섯 조건을 충족하는지, 나중에 충족하지 못하게 되는지에 따라
같은 인도·같은 현금이 수익이 되기도 하고 부채로 남기도 한다.
금액 단위: 백만원.
"""

CRITERIA = {
    1: "승인·확약",
    2: "권리 식별",
    3: "지급조건 식별",
    4: "상업적 실질",
    5: "회수 가능성 높음",
}

# 계약 개시시점의 판정 — 고객별로 어느 조건을 충족하는지
CONTRACTS = {
    "갑": {"criteria": {1, 2, 3, 4, 5}, "both_can_cancel_free": False,
           "note": "신용등급 양호"},
    "을": {"criteria": {1, 2, 3, 4}, "both_can_cancel_free": False,
           "note": "개시 전부터 연체 이력, 지급 능력이 낮다"},
    "병": {"criteria": {1, 2, 3, 4, 5}, "both_can_cancel_free": False,
           "note": "개시 때는 양호, 3분기 초 주거래 은행 거래 정지"},
    "정": {"criteria": {1, 2, 3, 4, 5}, "both_can_cancel_free": True,
           "note": "기본거래약정만 있고 발주 전에는 양쪽 모두 무보상 해지 가능"},
}

# 분기별 사건 — (분기, 사건, 금액)
#   deliver: 재화 인도 / cash: 현금 수취 / reassess_fail: 문단 13 재검토에서 ⑸ 미충족
#   terminate: 계약 종료, 받은 대가는 환불하지 않는다
EVENTS = {
    "갑": [(q, "deliver", 250) for q in (1, 2, 3, 4)]
          + [(q, "cash", 250) for q in (1, 2, 3, 4)],
    "을": [(1, "cash", 300), (1, "deliver", 250), (2, "deliver", 250),
           (4, "terminate", 0)],
    "병": [(1, "deliver", 250), (1, "cash", 250), (2, "deliver", 250),
           (3, "reassess_fail", 0), (3, "cash", 250), (3, "deliver", 250),
           (4, "terminate", 0)],
    "정": [],  # 발주가 없었다
}


def is_contract(c):
    """문단 9 다섯 조건을 모두 충족하고, 문단 12 의 '계약 없음'이 아니어야 한다."""
    if c["both_can_cancel_free"]:
        return False, "문단 12 — 전혀 수행되지 않은 계약을 양쪽 모두 무보상 해지 가능"
    missing = [f"⑸{CRITERIA[k]}" if k == 5 else f"({k}){CRITERIA[k]}"
               for k in CRITERIA if k not in c["criteria"]]
    if missing:
        return False, "문단 9 미충족: " + ", ".join(missing)
    return True, "문단 9 다섯 조건 충족"


def simulate(name):
    ok, _ = is_contract(CONTRACTS[name])
    state = {"in_scope": ok, "revenue": 0, "liability": 0, "receivable": 0,
             "cash": 0, "delivered": 0}
    rows = []
    for q in (1, 2, 3, 4):
        for _, kind, amt in [e for e in EVENTS[name] if e[0] == q]:
            if kind == "deliver":
                state["delivered"] += amt
                if state["in_scope"]:
                    # 통제 이전 시점에 수익 — 먼저 받은 돈이 있으면 그것부터 줄인다
                    used = min(state["liability"], amt)
                    state["liability"] -= used
                    state["receivable"] += amt - used
                    state["revenue"] += amt
                    rows.append((q, f"인도 {amt}", f"수익 {amt}", "계약으로 회계처리"))
                else:
                    rows.append((q, f"인도 {amt}", "수익 0", "문단 15 사건 아님 — 의무가 남아 있다"))
            elif kind == "cash":
                state["cash"] += amt
                if state["in_scope"] and state["receivable"] >= amt:
                    state["receivable"] -= amt
                    rows.append((q, f"현금 {amt}", "수취채권 회수", ""))
                else:
                    state["liability"] += amt
                    why = "문단 16 — 받은 금액으로 부채 측정" if not state["in_scope"] else "선수금"
                    rows.append((q, f"현금 {amt}", f"부채 +{amt}", why))
            elif kind == "reassess_fail":
                state["in_scope"] = False
                rows.append((q, "재검토", "이후 인도분 수익 중단",
                             "문단 13 — 이미 인식한 수익은 그대로"))
            elif kind == "terminate":
                if not state["in_scope"] and state["liability"] > 0:
                    amt = state["liability"]
                    state["revenue"] += amt
                    state["liability"] = 0
                    rows.append((q, "계약 종료", f"수익 {amt}",
                                 "문단 15⑵ — 종료, 받은 대가 환불 안 함"))
                else:
                    rows.append((q, "계약 종료", "변동 없음", ""))
        rows.append((q, "분기 말", f"누적 수익 {state['revenue']}",
                     f"부채 {state['liability']}  수취채권 {state['receivable']}"))
    return rows, state


def main():
    print("[1] 계약 개시시점 판정 — 문단 9·12")
    for name, c in CONTRACTS.items():
        ok, why = is_contract(c)
        mark = "계약" if ok else "계약 아님"
        print(f"  {name}  {c['note']}")
        print(f"      → {mark}  ({why})")
    print()

    print("[2] 분기별 회계처리")
    results = {}
    for name in ("갑", "을", "병"):
        rows, state = simulate(name)
        results[name] = state
        print(f"  고객 {name}")
        for q, event, effect, why in rows:
            print(f"    {q}분기  {event:<8} {effect:<18} {why}")
    print()

    print("[3] 1년 합계 — 같은 계약 조건, 다른 수익")
    print("  고객  인도(판매가)  받은 현금  인식한 수익  기말 부채  기말 수취채권")
    for name, s in results.items():
        print(f"  {name}   {s['delivered']:>10}  {s['cash']:>9}  {s['revenue']:>11}"
              f"  {s['liability']:>9}  {s['receivable']:>13}")
    print("  정   발주 없음 — 문단 12 에 따라 계약이 존재하지 않는 것으로 본다")


if __name__ == "__main__":
    main()
