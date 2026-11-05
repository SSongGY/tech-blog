"""연결 범위와 연결 절차 — 지배력 세 요소로 대상을 정하고, 합산·제거·비지배지분을 계산한다.

가상 회사 가나지주(지배기업)와 다라부품(종속기업)을 쓴다. 단위는 억원.
표준 라이브러리만 쓴다.
"""

import platform
from dataclasses import dataclass


@dataclass
class Case:
    name: str
    stake: float  # 지분율(의결권)
    power: bool  # 관련 활동을 지시할 현재의 능력이 있는가
    exposure: bool  # 변동이익에 노출되거나 권리가 있는가
    use: bool  # 힘으로 이익 금액에 영향을 미치는 능력이 있는가
    note: str

    @property
    def consolidate(self) -> bool:
        return self.power and self.exposure and self.use  # 세 가지 모두 충족해야 한다


def judge() -> list[Case]:
    return [
        Case("가", 0.60, True, True, True, "이사 과반 선임, 예산·대표 결정"),
        Case("나", 0.40, True, True, True, "나머지는 분산, 총회 실제 의결권의 과반"),
        Case("다", 0.60, False, True, False, "핵심 활동은 계약상 다른 투자자가 결정"),
    ]


def effective_vote_share() -> tuple[float, float]:
    """사례 '나'의 총회 참석 가정. 나머지 주주 60% 중 평균 30%만 참석했다."""
    own = 0.40
    others_present = 0.60 * 0.30
    return own, own / (own + others_present)


def main() -> None:
    print(f"환경: Python {platform.python_version()}")
    print()

    print("[1] 지배력 세 요소 판단 — 지분율만으로 정해지지 않는다")
    print(f"{'사례':>4}{'지분율':>8}{'힘':>6}{'변동이익':>8}{'영향력':>8}  결과")
    print("-" * 52)
    for c in judge():
        mark = lambda b: "O" if b else "X"
        result = "연결" if c.consolidate else "연결 제외"
        print(
            f"{c.name:>4}{c.stake:>8.0%}{mark(c.power):>6}{mark(c.exposure):>10}"
            f"{mark(c.use):>9}  {result}  ({c.note})"
        )
    own, share = effective_vote_share()
    print(f"\n  사례 나: 지분율 {own:.0%}, 총회에서 행사된 의결권 중 비중 {share:.1%} (가정)")
    print()

    # 가나지주 별도재무상태표(내부 재고 50은 다라부품에서 산 것, 거기에 이익 10이 들어 있다)
    ga = {"현금": 300.0, "종속기업투자": 160.0, "재고자산": 100.0, "기타자산": 240.0}
    ga_debt, ga_equity = 400.0, 400.0  # 부채에 다라부품에 줄 매입채무 20 포함
    # 다라부품 별도재무상태표. 취득 후 이익 30(내부 판매이익 10 포함)이 쌓였다
    da = {"현금": 60.0, "재고자산": 120.0, "기타자산": 250.0}  # 기타자산에 가나지주 채권 20 포함
    da_debt, da_equity = 200.0, 230.0
    acq_equity = 200.0  # 취득일 자본, 공정가치와 같아 영업권이 없다
    stake = 0.80
    intra_balance = 20.0
    unrealised = 10.0

    assert sum(ga.values()) == ga_debt + ga_equity
    assert sum(da.values()) == da_debt + da_equity

    print("[2] 연결 절차 — 가나지주가 다라부품 80%를 지배하는 경우 (단위: 억원)")
    items = ["현금", "종속기업투자", "재고자산", "기타자산"]
    print(f"{'':>10}{'가나지주':>10}{'다라부품':>10}{'합산':>10}{'제거':>10}{'연결':>10}")
    print("-" * 60)
    elim = {"현금": 0.0, "종속기업투자": -160.0, "재고자산": -unrealised, "기타자산": -intra_balance}
    cons_assets = 0.0
    for k in items:
        a, d = ga.get(k, 0.0), da.get(k, 0.0)
        total = a + d
        cons = total + elim[k]
        cons_assets += cons
        print(f"{k:>10}{a:>10.1f}{d:>10.1f}{total:>10.1f}{elim[k]:>10.1f}{cons:>10.1f}")
    print(f"{'자산 합계':>10}{sum(ga.values()):>10.1f}{sum(da.values()):>10.1f}"
          f"{sum(ga.values()) + sum(da.values()):>10.1f}{sum(elim.values()):>10.1f}{cons_assets:>10.1f}")

    cons_debt = ga_debt + da_debt - intra_balance
    post_acq = da_equity - acq_equity  # 취득 후 다라부품 자본 증가
    owners_extra = post_acq * stake - unrealised * stake  # 지배기업 몫 이익 - 내부이익 제거 몫
    owners = ga_equity + owners_extra
    nci = da_equity * (1 - stake) - unrealised * (1 - stake)
    print(f"\n  부채 {ga_debt:.1f} + {da_debt:.1f} - 내부채무 {intra_balance:.1f} = {cons_debt:.1f}")
    print(f"  지배기업 소유주지분 {ga_equity:.1f} + 취득 후 이익 몫 {post_acq * stake:.1f}"
          f" - 내부이익 제거 몫 {unrealised * stake:.1f} = {owners:.1f}")
    print(f"  비지배지분 {da_equity:.1f} x {1 - stake:.0%} - 내부이익 제거 몫 {unrealised * (1 - stake):.1f} = {nci:.1f}")
    print(f"  부채 + 자본 = {cons_debt + owners + nci:.1f}, 자산 = {cons_assets:.1f}"
          f", 일치: {abs(cons_debt + owners + nci - cons_assets) < 1e-9}")
    print()

    print("[3] 연결 전후 비율 — 같은 두 회사, 다른 부채비율")
    ga_ratio = ga_debt / ga_equity
    cons_ratio = cons_debt / (owners + nci)
    print(f"  가나지주 별도 부채비율      {ga_ratio:>6.1%}  (부채 {ga_debt:.0f} / 자본 {ga_equity:.0f})")
    print(f"  연결 부채비율               {cons_ratio:>6.1%}  (부채 {cons_debt:.0f} / 자본 {owners + nci:.0f})")


if __name__ == "__main__":
    main()
