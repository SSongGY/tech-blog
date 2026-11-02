"""합병비율이 지분율을 어떻게 바꾸고, 주식매수청구가 그 위에 무엇을 더하는지 계산한다.

세 덩어리로 나뉜다.

1. 자본시장법 시행령 제176조의7 제3항 제1호의 매수가격 산정 — 2개월·1개월·1주일
   가중산술평균가격을 각각 구하고 그 셋을 단순평균한다
2. 합병비율에 따른 합병 후 지분율
3. 매수청구 물량이 늘어날 때 회사가 내야 하는 현금과, 그 결과 남은 주주의 지분율

회사와 주가는 전부 지어낸 값이다. 실제 사건의 숫자가 아니다.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

# 이사회 결의일 전일까지 40영업일치 종가와 거래량을 만든다.
# 시드를 고정해 돌릴 때마다 같은 값이 나오게 한다.
SEED = 20261102
SESSIONS = 40


@dataclass
class Session:
    """하루치 종가와 거래량. 뒤로 갈수록 이사회 결의일에 가깝다."""

    close: int
    volume: int


def build_price_history() -> list[Session]:
    rng = random.Random(SEED)
    sessions: list[Session] = []
    close = 12_000
    for _ in range(SESSIONS):
        close = max(8_000, close + rng.randint(-280, 300))
        sessions.append(Session(close=close, volume=rng.randint(40_000, 260_000)))
    return sessions


def weighted_average(sessions: list[Session]) -> float:
    """거래량을 가중치로 한 가중산술평균가격."""
    traded = sum(s.close * s.volume for s in sessions)
    volume = sum(s.volume for s in sessions)
    return traded / volume


def statutory_price(sessions: list[Session]) -> tuple[float, dict[str, float]]:
    """시행령 제176조의7 제3항 제1호 가·나·다목을 각각 구하고 산술평균한다.

    2개월·1개월·1주일을 영업일로 환산해 각각 40·20·5거래일로 둔다.
    실제로는 달력 기준이라 거래일 수가 달라질 수 있다.
    """
    legs = {
        "2개월(40거래일)": weighted_average(sessions[-40:]),
        "1개월(20거래일)": weighted_average(sessions[-20:]),
        "1주일(5거래일)": weighted_average(sessions[-5:]),
    }
    return sum(legs.values()) / len(legs), legs


def merged_ownership(
    surviving_shares: int, target_shares: int, ratio: float
) -> dict[str, float]:
    """합병비율 ratio 로 신주를 발행했을 때의 지분율."""
    new_shares = round(target_shares * ratio)
    total = surviving_shares + new_shares
    return {
        "발행 신주": new_shares,
        "합병 후 총주식수": total,
        "존속회사 기존 주주 지분율": surviving_shares / total * 100,
        "소멸회사 주주 지분율": new_shares / total * 100,
    }


def after_buyback(
    total_shares: int, holder_shares: int, bought_shares: int
) -> dict[str, float]:
    """회사가 매수한 주식은 자기주식이 되어 의결권이 없다(상법 제369조 제2항).

    그래서 의결권 기준 지분율의 분모가 줄고, 남은 주주의 몫이 올라간다.
    """
    voting_base = total_shares - bought_shares
    return {
        "자기주식": bought_shares,
        "의결권 있는 주식수": voting_base,
        "지분율(%)": holder_shares / voting_base * 100,
    }


def main() -> None:
    sessions = build_price_history()

    print("=" * 62)
    print("1. 협의가 깨졌을 때의 법정 매수가격 — 가나전자")
    print("=" * 62)
    print(f"이사회 결의일 전일 종가: {sessions[-1].close:,}원")
    price, legs = statutory_price(sessions)
    for label, value in legs.items():
        print(f"  {label:<16} 가중산술평균 {value:>12,.2f}원")
    print(f"  {'세 가격의 산술평균':<16} {price:>12,.2f}원  ← 법정 매수가격")
    print(f"  원 단위 절사                {int(price):>12,}원")

    print()
    print("=" * 62)
    print("2. 합병비율이 지분율을 바꾼다 — 가나전자(존속) ← 다라물산(소멸)")
    print("=" * 62)
    surviving, target = 10_000_000, 4_000_000
    print(f"가나전자 발행주식 {surviving:,}주 / 다라물산 발행주식 {target:,}주")
    for ratio in (0.3, 0.5, 0.8):
        result = merged_ownership(surviving, target, ratio)
        print(f"\n  합병비율 1 : {ratio}")
        print(f"    발행 신주            {result['발행 신주']:>12,}주")
        print(f"    합병 후 총주식수      {result['합병 후 총주식수']:>12,}주")
        print(f"    기존 가나전자 주주    {result['존속회사 기존 주주 지분율']:>11.2f}%")
        print(f"    다라물산 주주        {result['소멸회사 주주 지분율']:>11.2f}%")

    print()
    print("=" * 62)
    print("3. 매수청구가 몰리면 — 합병비율 1 : 0.5, 매수가격은 1번의 값")
    print("=" * 62)
    merged = merged_ownership(surviving, target, 0.5)
    total = merged["합병 후 총주식수"]
    holder = 1_000_000  # 가나전자 지분 10%를 들고 합병에 찬성한 주주
    unit = int(price)
    print(f"합병 후 총주식수 {total:,}주, 매수가격 {unit:,}원")
    print(f"합병에 찬성한 주주 보유 {holder:,}주")
    print()
    print(f"  {'청구 물량':>12} {'회사가 낼 현금':>18} {'의결권 주식수':>14} {'그 주주 지분율':>14}")
    for claimed in (0, 200_000, 600_000, 1_200_000):
        result = after_buyback(total, holder, claimed)
        cash = claimed * unit
        print(
            f"  {claimed:>11,}주 {cash:>17,}원"
            f" {result['의결권 있는 주식수']:>13,}주 {result['지분율(%)']:>13.3f}%"
        )

    print()
    print("매수대금은 회사의 현금에서 나간다. 청구가 몰릴수록 합병 뒤 회사에 남는")
    print("현금이 줄고, 그래서 합병계약서에 매수대금 한도를 걸고 그 한도를 넘으면")
    print("계약을 해제할 수 있게 적어 두는 일이 많다.")


if __name__ == "__main__":
    main()
