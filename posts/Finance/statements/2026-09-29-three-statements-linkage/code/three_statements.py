"""가상 회사 가나전자의 한 해를 분개로 기록하고 재무제표 세 장을 뽑는다.

세 장을 손으로 따로 적지 않고 같은 분개장에서 계산해 낸다. 그래야 "이어진다"는
말이 주장이 아니라 계산 결과가 된다. 금액 단위는 억원.
"""

import platform
import sys

# 계정 → (재무상태표 구분, 손익 구분). 손익 계정은 기말에 이익잉여금으로 닫힌다.
ACCOUNTS = {
    "현금": "자산",
    "매출채권": "자산",
    "재고자산": "자산",
    "유형자산": "자산",
    "차입금": "부채",
    "자본금": "자본",
    "이익잉여금": "자본",
    "매출": "수익",
    "매출원가": "비용",
    "판매관리비": "비용",
    "감가상각비": "비용",
    "이자비용": "비용",
    "법인세비용": "비용",
}

OPENING = {
    "현금": 100, "매출채권": 150, "재고자산": 200, "유형자산": 800,
    "차입금": 400, "자본금": 500, "이익잉여금": 350,
}

# (적요, 차변 계정, 대변 계정, 금액, 현금흐름 구분)
# 현금이 움직이지 않는 분개는 구분을 None 으로 둔다.
JOURNAL = [
    ("현금 매출",           "현금",       "매출",     800, "영업"),
    ("외상 매출",           "매출채권",   "매출",     200, None),
    ("원재료 현금 매입",     "재고자산",   "현금",     550, "영업"),
    ("판매분 원가 대체",     "매출원가",   "재고자산", 600, None),
    ("판매관리비 지급",      "판매관리비", "현금",     150, "영업"),
    ("설비 감가상각",        "감가상각비", "유형자산",  80, None),
    ("이자 지급",           "이자비용",   "현금",      20, "영업"),
    ("법인세 납부",          "법인세비용", "현금",      30, "영업"),
    ("설비 취득",           "유형자산",   "현금",     300, "투자"),
    ("은행 차입",           "현금",       "차입금",   200, "재무"),
    ("배당금 지급",          "이익잉여금", "현금",      40, "재무"),
]


def signed(account: str, amount: int, side: str) -> int:
    """자산·비용은 차변이 +, 부채·자본·수익은 대변이 + 인 쪽으로 잔액을 센다."""
    debit_normal = ACCOUNTS[account] in ("자산", "비용")
    return amount if (side == "차변") == debit_normal else -amount


def post(balances: dict) -> dict:
    for _, debit, credit, amount, _ in JOURNAL:
        balances[debit] = balances.get(debit, 0) + signed(debit, amount, "차변")
        balances[credit] = balances.get(credit, 0) + signed(credit, amount, "대변")
    return balances


def show(title: str, rows: list[tuple[str, int]]) -> None:
    print(f"\n[{title}]")
    for label, value in rows:
        print(f"  {label:<14}{value:>8,}")


def main() -> None:
    print(f"Python {sys.version.split()[0]} / {platform.system()}")
    print("단위: 억원 / 회사: 가나전자(가상)")

    print("\n[분개장]")
    for memo, debit, credit, amount, flow in JOURNAL:
        print(f"  {memo:<12} 차) {debit:<6} 대) {credit:<6} {amount:>5}  {flow or '-'}")

    ledger = post(dict(OPENING))

    # 1) 손익계산서 — 수익·비용 계정만 모은다
    revenue = ledger["매출"]
    expenses = [(a, ledger[a]) for a, kind in ACCOUNTS.items() if kind == "비용"]
    net_income = revenue - sum(v for _, v in expenses)
    show("손익계산서", [("매출", revenue)] + [(a, -v) for a, v in expenses]
         + [("당기순이익", net_income)])

    # 2) 자본변동표의 이익잉여금 줄 — 기초 + 순이익 - 배당 = 기말
    dividends = sum(amount for _, debit, _, amount, _ in JOURNAL if debit == "이익잉여금")
    closing_re = OPENING["이익잉여금"] + net_income - dividends
    show("이익잉여금 변동", [("기초", OPENING["이익잉여금"]), ("당기순이익", net_income),
                        ("배당", -dividends), ("기말", closing_re)])

    # 3) 현금흐름표(직접법) — 현금 계정을 건드린 분개를 구분별로 합친다
    flows = {"영업": 0, "투자": 0, "재무": 0}
    for _, debit, credit, amount, flow in JOURNAL:
        if flow:
            flows[flow] += amount if debit == "현금" else -amount
    net_cash = sum(flows.values())
    show("현금흐름표(직접법)", [(f"{k}활동", v) for k, v in flows.items()]
         + [("현금 증감", net_cash), ("기초 현금", OPENING["현금"]),
            ("기말 현금", OPENING["현금"] + net_cash)])

    # 4) 간접법 — 순이익에서 출발해 현금이 안 움직인 몫을 되돌린다
    delta = {a: ledger[a] - OPENING[a] for a in ("매출채권", "재고자산")}
    # 자산이 늘면 그만큼 현금이 묶였으므로 빼고, 줄면 풀렸으므로 더한다
    indirect = [("당기순이익", net_income), ("감가상각비", ledger["감가상각비"]),
                ("매출채권 변동", -delta["매출채권"]), ("재고자산 변동", -delta["재고자산"])]
    show("영업활동(간접법)", indirect + [("영업활동 계", sum(v for _, v in indirect))])

    # 5) 기말 재무상태표 — 마감분개로 수익·비용 잔액을 이익잉여금에 옮긴다.
    #    자본변동표 계산과 따로 구하므로 둘이 같은지가 검산이 된다.
    closing = {a: ledger[a] for a, kind in ACCOUNTS.items() if kind in ("자산", "부채", "자본")}
    closing["이익잉여금"] = ledger["이익잉여금"] + revenue - sum(v for _, v in expenses)
    print("\n[재무상태표]   기초      기말")
    for account in closing:
        print(f"  {account:<10}{OPENING[account]:>8,}{closing[account]:>10,}")

    def total(book: dict, kind: str) -> int:
        return sum(v for a, v in book.items() if ACCOUNTS[a] == kind)

    print("\n[이어지는 곳 검산]")
    checks = [
        ("자본변동표→재무상태표: 이익잉여금", closing_re, closing["이익잉여금"]),
        ("현금흐름→재무상태표: 기말 현금", OPENING["현금"] + net_cash, closing["현금"]),
        ("간접법 = 직접법 영업활동", sum(v for _, v in indirect), flows["영업"]),
        ("기말 자산 = 부채 + 자본", total(closing, "자산"),
         total(closing, "부채") + total(closing, "자본")),
    ]
    for label, left, right in checks:
        print(f"  {label:<24} {left:>6,} = {right:>6,}  {'일치' if left == right else '불일치'}")
        assert left == right, label

    print(f"\n순이익 {net_income:,} / 현금 증감 {net_cash:,} — 차이 {net_income - net_cash:,}")


if __name__ == "__main__":
    main()
