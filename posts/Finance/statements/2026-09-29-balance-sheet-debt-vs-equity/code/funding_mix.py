"""자산은 같고 자산을 마련한 출처만 다른 두 가상 회사를 비교한다.

가나전자는 설비 100억을 빌린 돈으로, 다라물산은 주주가 낸 돈으로 샀다.
거래마다 자산 = 부채 + 자본이 유지되는지 검산하고, 영업이익이 같을 때
출처의 차이가 순이익과 자본수익률(ROE)을 어떻게 갈라놓는지 계산한다.
금액 단위는 억원. 계산을 단순하게 하려고 법인세는 뺐다.
"""

import platform
import sys

SIDE = {"현금": "자산", "설비": "자산", "차입금": "부채", "자본금": "자본", "이익잉여금": "자본"}
INTEREST_RATE = 0.05


def apply(book: dict, memo: str, changes: dict) -> None:
    """거래 하나를 반영하고, 양쪽 변동이 같은지 확인한다."""
    left = sum(v for a, v in changes.items() if SIDE[a] == "자산")
    right = sum(v for a, v in changes.items() if SIDE[a] != "자산")
    for account, delta in changes.items():
        book[account] = book.get(account, 0) + delta
    moves = ", ".join(f"{a} {d:+g}" for a, d in changes.items())
    print(f"  {memo:<14} {moves:<34} 자산 변동 {left:+g} / 부채+자본 변동 {right:+g}")
    assert left == right, memo


def totals(book: dict) -> tuple[float, float, float]:
    assets = sum(v for a, v in book.items() if SIDE[a] == "자산")
    debt = sum(v for a, v in book.items() if SIDE[a] == "부채")
    equity = sum(v for a, v in book.items() if SIDE[a] == "자본")
    return assets, debt, equity


def show(name: str, book: dict) -> None:
    assets, debt, equity = totals(book)
    rows = "  ".join(f"{a} {book[a]:g}" for a in SIDE if book.get(a))
    print(f"  {name:<6} {rows:<40} → 자산 {assets:g} = 부채 {debt:g} + 자본 {equity:g}")
    assert assets == debt + equity


def main() -> None:
    print(f"Python {sys.version.split()[0]} / {platform.system()}")
    print("단위: 억원 / 회사: 가나전자·다라물산(가상) / 법인세 없음")

    print("\n[1] 설립 거래 — 거래마다 양쪽이 같은 만큼 움직인다")
    gana, dara = {}, {}
    apply(gana, "가나 주주 출자", {"현금": 50, "자본금": 50})
    apply(gana, "가나 은행 차입", {"현금": 100, "차입금": 100})
    apply(gana, "가나 설비 구입", {"설비": 100, "현금": -100})
    apply(dara, "다라 주주 출자", {"현금": 150, "자본금": 150})
    apply(dara, "다라 설비 구입", {"설비": 100, "현금": -100})

    print("\n[2] 설립 직후 재무상태표 — 자산은 같고 오른쪽만 다르다")
    show("가나전자", gana)
    show("다라물산", dara)

    print(f"\n[3] 한 해 영업 결과 — 이자율 {INTEREST_RATE:.0%}, 영업이익만 바꿔 본다")
    print("  영업이익  회사      이자   순이익  영업이익/자산  순이익/자본  기말 자본")
    for operating_profit in (15, 7.5, 3):
        for name, book in (("가나전자", gana), ("다라물산", dara)):
            assets, debt, equity = totals(book)
            interest = debt * INTEREST_RATE
            net_income = operating_profit - interest
            asset_yield = operating_profit / assets   # 출처와 무관한 자산 자체의 수익률
            roe = net_income / equity                 # 기초 자본 기준 주주 몫의 수익률
            print(f"  {operating_profit:>6g}  {name:<8}{interest:>6g}{net_income:>8g}"
                  f"{asset_yield:>13.1%}{roe:>12.1%}{equity + net_income:>10g}")

    print("\n[4] 자산이 안 바뀌는 거래 — 차입금 30을 주식으로 바꾼다(출자전환)")
    apply(gana, "가나 출자전환", {"차입금": -30, "자본금": 30})
    show("가나전자", gana)


if __name__ == "__main__":
    main()
