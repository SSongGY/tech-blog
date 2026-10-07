"""연결재무제표와 별도재무제표 — 같은 지배기업의 두 숫자.

가상 지주 가나홀딩스가 종속기업 둘(가나소재 100%, 가나물류 60%)과 관계기업 하나
(라마바이오 30%)를 가진다. 별도재무제표는 투자주식을 원가로 두고 받은 배당만
수익으로 잡는다. 연결재무제표는 종속기업을 줄 단위로 합산한 뒤 투자-자본 상계와
내부거래 제거를 하고, 관계기업은 지분법으로 반영한다.

단순화: 취득은 장부가로 해서 영업권이 없고, 내부거래 재고는 연말에 모두 팔렸으며,
법인세와 영업외손익이 없어 종속기업의 순이익이 곧 영업이익이다. 금액 단위는 억원.
"""
import platform
import sys

PARENT = {
    "name": "가나홀딩스",
    "revenue": 1000, "op_cost": 900,       # 매출 1,000 중 300 은 가나소재에 판 것
    "dividend_in": 50,                       # 가나소재에서 받은 배당
    "other_assets": 1010, "ic_receivable": 100, "liabilities": 800,
}
SUBS = [
    # share: 지분율, cost: 별도재무제표상 투자주식(원가), acq_equity: 취득 시 자본
    # post_equity: 취득 후 늘어난 자본(누적 이익 - 배당)
    {"name": "가나소재", "share": 1.0, "cost": 500, "acq_equity": 500, "post_equity": 100,
     "revenue": 800, "net_income": 120, "dividend_out": 50, "assets": 900, "liabilities": 300},
    {"name": "가나물류", "share": 0.6, "cost": 300, "acq_equity": 500, "post_equity": 80,
     "revenue": 600, "net_income": 80, "dividend_out": 0, "assets": 2180, "liabilities": 1600},
]
ASSOCIATE = {"name": "라마바이오", "share": 0.3, "cost": 90, "net_income": 40, "dividend_out": 0}
IC_SALES = 300        # 가나홀딩스 → 가나소재 매출
IC_BALANCE = 100      # 가나소재가 가나홀딩스에 진 매입채무


def separate() -> dict:
    investments = sum(s["cost"] for s in SUBS) + ASSOCIATE["cost"]
    assets = PARENT["other_assets"] + PARENT["ic_receivable"] + investments
    op_income = PARENT["revenue"] - PARENT["op_cost"]
    return {
        "revenue": PARENT["revenue"],
        "op_income": op_income,
        "net_income": op_income + PARENT["dividend_in"],
        "assets": assets,
        "liabilities": PARENT["liabilities"],
        "equity": assets - PARENT["liabilities"],
        "investments": investments,
    }


def consolidated() -> dict:
    sep = separate()
    revenue = PARENT["revenue"] + sum(s["revenue"] for s in SUBS) - IC_SALES
    # 내부 매출 300 은 가나소재의 매출원가에서도 같이 빠지므로 영업이익은 그대로다
    op_income = sep["op_income"] + sum(s["net_income"] for s in SUBS)
    equity_method = ASSOCIATE["share"] * ASSOCIATE["net_income"]
    net_income = op_income + equity_method   # 받은 배당 50 은 그룹 안에서 돈 것이라 지운다
    nci_income = sum((1 - s["share"]) * s["net_income"] for s in SUBS)

    associate_carrying = ASSOCIATE["cost"] + equity_method - ASSOCIATE["share"] * ASSOCIATE["dividend_out"]
    assets = (PARENT["other_assets"] + sum(s["assets"] for s in SUBS)
              + associate_carrying)          # 내부 채권 100 과 종속기업 투자주식은 빠진다
    liabilities = PARENT["liabilities"] + sum(s["liabilities"] for s in SUBS) - IC_BALANCE
    equity = assets - liabilities
    nci = sum((1 - s["share"]) * (s["acq_equity"] + s["post_equity"]) for s in SUBS)
    return {
        "revenue": revenue, "op_income": op_income, "equity_method": equity_method,
        "net_income": net_income, "nci_income": nci_income,
        "owners_income": net_income - nci_income,
        "assets": assets, "liabilities": liabilities, "equity": equity,
        "nci": nci, "owners_equity": equity - nci, "associate_carrying": associate_carrying,
    }


def print_inputs() -> None:
    print("[0] 회사별 숫자 (억원)")
    print(f"  {'회사':<8} {'지분율':>5} {'투자원가':>7} {'매출':>6} {'순이익':>6} {'배당':>5} {'자산':>6} {'부채':>6} {'자본':>6}")
    for s in SUBS:
        eq = s["acq_equity"] + s["post_equity"]
        assert s["assets"] - s["liabilities"] == eq
        print(f"  {s['name']:<8} {s['share']:>6.0%} {s['cost']:>8,} {s['revenue']:>7,} {s['net_income']:>7,}"
              f" {s['dividend_out']:>6,} {s['assets']:>7,} {s['liabilities']:>7,} {eq:>7,}")
    a = ASSOCIATE
    print(f"  {a['name']:<7} {a['share']:>6.0%} {a['cost']:>8,} {'-':>7} {a['net_income']:>7,} {a['dividend_out']:>6,}")
    print(f"  내부거래: 가나홀딩스 → 가나소재 매출 {IC_SALES}, 미결제 채권·채무 {IC_BALANCE}")
    print()


def print_compare(sep: dict, con: dict) -> None:
    print("[1] 같은 가나홀딩스, 두 재무제표 (억원)")
    rows = [
        ("매출", sep["revenue"], con["revenue"]),
        ("영업이익", sep["op_income"], con["op_income"]),
        ("배당금수익", PARENT["dividend_in"], 0),
        ("지분법이익", 0, con["equity_method"]),
        ("당기순이익", sep["net_income"], con["net_income"]),
        ("  지배기업 소유주 몫", sep["net_income"], con["owners_income"]),
        ("  비지배지분 몫", 0, con["nci_income"]),
        ("자산총계", sep["assets"], con["assets"]),
        ("부채총계", sep["liabilities"], con["liabilities"]),
        ("자본총계", sep["equity"], con["equity"]),
        ("  지배기업 소유주지분", sep["equity"], con["owners_equity"]),
        ("  비지배지분", 0, con["nci"]),
    ]
    print(f"  {'항목':<16} {'별도':>8} {'연결':>8}")
    for label, s, c in rows:
        print(f"  {label:<16} {s:>8,.0f} {c:>8,.0f}")
    print()


def print_ratios(sep: dict, con: dict) -> None:
    print("[2] 비율이 갈리는 자리")
    print(f"  부채비율(부채÷자본)      별도 {sep['liabilities'] / sep['equity']:7.1%}   연결 {con['liabilities'] / con['equity']:7.1%}")
    print(f"  ROE(지배 순이익÷지배 자본) 별도 {sep['net_income'] / sep['equity']:7.1%}   연결 {con['owners_income'] / con['owners_equity']:7.1%}")
    print()


def print_check(sep: dict, con: dict) -> None:
    print("[3] 검산 — 연결 지배지분 = 별도 자본 + 취득 후 늘어난 자본의 지배 몫")
    parts = [s["share"] * s["post_equity"] for s in SUBS]
    assoc = con["associate_carrying"] - ASSOCIATE["cost"]
    total = sep["equity"] + sum(parts) + assoc
    detail = " + ".join(f"{p:,.0f}" for p in parts)
    print(f"  {sep['equity']:,} + ({detail}) + 관계기업 {assoc:,.0f} = {total:,.0f}   연결 지배지분 {con['owners_equity']:,.0f}")
    assert round(total) == round(con["owners_equity"])
    print()


def main() -> None:
    print(f"Python {platform.python_version()} · {sys.platform}")
    print()
    sep = separate()
    con = consolidated()
    print_inputs()
    print_compare(sep, con)
    print_ratios(sep, con)
    print_check(sep, con)


if __name__ == "__main__":
    main()
