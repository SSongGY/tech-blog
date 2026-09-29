"""유동·비유동 분류가 지급능력 판단을 어떻게 바꾸는지 두 가상 회사로 계산한다.

가나전자와 다라물산은 유동비율이 150%로 같다. 그런데 유동자산이 현금으로
돌아오는 시점과 유동부채를 갚아야 하는 시점을 달별로 놓으면 한쪽은 중간에
현금이 모자란다. 이어서 거래가 하나도 없어도 만기가 12개월 안으로 들어오는
것만으로 유동비율이 바뀌는 경우, 차환 약정을 언제 맺었느냐에 따라 분류가
갈리는 경우를 K-IFRS 제1001호 문단 66·69·70·72 규칙대로 분류해 본다.
금액 단위는 억원, 개월 수는 보고기간말(기말) 기준이다.
"""

import platform
import sys
from dataclasses import dataclass


@dataclass
class Item:
    name: str
    side: str            # "자산" 또는 "부채"
    amount: float
    months: int | None   # 기말부터 현금화·결제까지 개월. None 이면 현금화를 예정하지 않는 자산
    operating: bool = False       # 정상영업주기 안에서 돌아가는 운전자본 항목
    defer_right: bool = False     # 기말 현재 12개월 넘게 결제를 미룰 권리가 있는가


def classify(item: Item) -> str:
    """문단 66(자산)·69(부채)의 판정을 그대로 옮긴다."""
    if item.operating:
        # 문단 70: 운전자본 항목은 12개월을 넘겨 결제돼도 정상영업주기 안이면 유동이다
        return "유동"
    if item.side == "자산":
        return "유동" if item.months is not None and item.months <= 12 else "비유동"
    if item.defer_right:
        return "비유동"
    return "유동" if item.months <= 12 else "비유동"


def current_ratio(items: list[Item]) -> tuple[float, float, float]:
    ca = sum(i.amount for i in items if i.side == "자산" and classify(i) == "유동")
    cl = sum(i.amount for i in items if i.side == "부채" and classify(i) == "유동")
    return ca, cl, ca / cl


def show_sheet(name: str, items: list[Item]) -> None:
    print(f"  {name}")
    for i in items:
        when = "-" if i.months is None else f"{i.months}개월"
        tag = " (운전자본)" if i.operating else ""
        print(f"    {i.side}  {i.name:<8}{i.amount:>6g}  {when:>6}  → {classify(i)}{tag}")
    ca, cl, ratio = current_ratio(items)
    inventory = sum(i.amount for i in items if i.name == "재고자산")
    print(f"    유동자산 {ca:g} / 유동부채 {cl:g} = 유동비율 {ratio:.0%}"
          f", 재고를 뺀 당좌비율 {(ca - inventory) / cl:.0%}")


def cash_path(items: list[Item]) -> list[float]:
    """유동 항목만 놓고, 달마다 들어오고 나간 뒤 남는 현금을 누적한다."""
    path = []
    for month in range(13):
        balance = 0.0
        for i in items:
            if classify(i) != "유동" or i.months is None or i.months > month:
                continue
            balance += i.amount if i.side == "자산" else -i.amount
        path.append(balance)
    return path


def main() -> None:
    print(f"Python {sys.version.split()[0]} / {platform.system()}")
    print("단위: 억원 / 회사: 가나전자·다라물산(가상) / 개월 수는 기말 기준")

    gana = [
        Item("현금", "자산", 60, 0),
        Item("매출채권", "자산", 60, 1, operating=True),
        Item("재고자산", "자산", 30, 4, operating=True),
        Item("설비", "자산", 200, None),
        Item("매입채무", "부채", 70, 2, operating=True),
        Item("단기차입금", "부채", 30, 6),
        Item("장기차입금", "부채", 100, 18),
    ]
    dara = [
        Item("현금", "자산", 10, 0),
        Item("매출채권", "자산", 20, 2, operating=True),
        Item("재고자산", "자산", 120, 10, operating=True),
        Item("설비", "자산", 200, None),
        Item("매입채무", "부채", 20, 2, operating=True),
        Item("단기차입금", "부채", 80, 3),
        Item("장기차입금", "부채", 100, 18),
    ]

    print("\n[1] 기말 분류 — 두 회사 유동비율은 같다")
    show_sheet("가나전자", gana)
    show_sheet("다라물산", dara)

    print("\n[2] 유동 항목만 달별로 현금화·결제했을 때 남는 현금(누적)")
    print("  개월    " + "".join(f"{m:>6}" for m in range(13)))
    for name, items in (("가나전자", gana), ("다라물산", dara)):
        path = cash_path(items)
        print(f"  {name:<6}" + "".join(f"{v:>6g}" for v in path))
        low = min(path)
        print(f"          잔액이 가장 낮은 시점: 기말 후 {path.index(low)}개월, 잔액 {low:g}")

    print("\n[3] 거래 없이 1년이 지났다 — 장기차입금 만기가 18개월에서 6개월로")
    next_year = [Item(i.name, i.side, i.amount, 6 if i.name == "장기차입금" else i.months,
                      i.operating) for i in gana]
    for label, items in (("작년 기말", gana), ("올해 기말", next_year)):
        loan = next(i for i in items if i.name == "장기차입금")
        ca, cl, ratio = current_ratio(items)
        print(f"  가나전자 {label}: 장기차입금 {loan.months}개월 → {classify(loan)}"
              f", 유동부채 {cl:g}, 유동비율 {ratio:.0%}")

    print("\n[4] 만기 6개월 차입금 100의 분류 — 차환 약정을 언제 맺었나")
    cases = [
        ("약정 없음", False),
        ("기말 뒤·발행승인 전에 3년 차환 약정", False),   # 문단 72: 기말 현재 권리가 없었다
        ("기말 전에 3년 연장 권리 확보", True),           # 문단 69(4): 기말 현재 미룰 권리가 있다
    ]
    for label, right in cases:
        loan = Item("차입금", "부채", 100, 6, defer_right=right)
        print(f"  {label:<24} → {classify(loan)}")


if __name__ == "__main__":
    main()
