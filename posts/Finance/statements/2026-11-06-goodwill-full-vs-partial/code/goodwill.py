"""사업결합 영업권 — 비지배지분 측정 방법에 따른 영업권 차이와 염가매수차익.

가상 회사 가나전자(취득자)가 라마화학 지분 80%를 취득한다. 단위는 억원.
표준 라이브러리만 쓴다.
"""

import platform

STAKE = 0.80
NCI_RATE = 1 - STAKE
NET_ASSETS_FV = 450.0  # 식별가능 순자산 공정가치
NCI_FV = 110.0  # 비지배지분의 공정가치(가정). 지분 비례 금액 90보다 20 높게 두어 두 방법의 차이를 드러낸다


def goodwill(consideration: float, nci: float) -> float:
    return consideration + nci - NET_ASSETS_FV


def main() -> None:
    print(f"환경: Python {platform.python_version()}")
    print()

    consideration = 400.0
    nci_partial = NET_ASSETS_FV * NCI_RATE
    gw_full = goodwill(consideration, NCI_FV)
    gw_partial = goodwill(consideration, nci_partial)

    print("[1] 영업권 = 이전대가 + 비지배지분 - 식별가능 순자산 공정가치")
    print(f"  이전대가 {consideration:.0f}, 식별가능 순자산 {NET_ASSETS_FV:.0f}, 지분율 {STAKE:.0%}")
    print(f"{'비지배지분 측정':>22}{'비지배지분':>10}{'영업권':>8}{'자산':>8}")
    print(f"{'공정가치(전부영업권)':>22}{NCI_FV:>10.1f}{gw_full:>8.1f}{NET_ASSETS_FV + gw_full:>8.1f}")
    print(f"{'순자산 비례(부분영업권)':>22}{nci_partial:>10.1f}{gw_partial:>8.1f}{NET_ASSETS_FV + gw_partial:>8.1f}")
    print(f"  영업권 차이 {gw_full - gw_partial:.1f} = 비지배지분 {NCI_FV:.0f} - {nci_partial:.0f}")
    print(f"  차이는 전부 비지배지분에 귀속되는 영업권이다. 지배기업 몫 영업권은 두 방법이 같다: "
          f"{consideration - NET_ASSETS_FV * STAKE:.1f}")

    print()
    print("[2] 이전대가가 낮은 경우 — 이전대가 330")
    low = 330.0
    raw = goodwill(low, nci_partial)
    print(f"  부분영업권 방식: {low:.0f} + {nci_partial:.0f} - {NET_ASSETS_FV:.0f} = {raw:.1f}")
    if raw < 0:
        print(f"  음수이면 영업권이 아니다. 식별·측정을 재검토한 뒤에도 남으면 염가매수차익 {-raw:.1f}을 당기손익으로 인식")
    raw_full = goodwill(low, NCI_FV)
    print(f"  전부영업권 방식: {low:.0f} + {NCI_FV:.0f} - {NET_ASSETS_FV:.0f} = {raw_full:.1f}")
    print(f"  같은 거래라도 비지배지분 측정에 따라 염가매수차익 금액이 {-raw:.0f}과 {-raw_full:.0f}으로 갈린다")

    print()
    print("[3] 연결 재무상태표에 미치는 영향 (영업권 전액을 인식한 뒤의 자본)")
    for name, nci, gw in (("전부영업권", NCI_FV, gw_full), ("부분영업권", nci_partial, gw_partial)):
        owners = consideration  # 취득일 지배기업 소유주지분은 이전대가만큼 투입된 것으로 본다
        total_assets = NET_ASSETS_FV + gw
        print(f"  {name}: 자산(순자산+영업권) {total_assets:.1f} = 지배기업 투입 {owners:.1f} + 비지배지분 {nci:.1f}")


if __name__ == "__main__":
    main()
