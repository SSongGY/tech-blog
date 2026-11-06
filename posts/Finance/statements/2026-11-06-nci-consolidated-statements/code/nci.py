"""비지배지분 — 당기순이익 귀속, 배당, 손실로 음수가 되는 경우, 추가 지분 취득.

가상 회사 가나전자(지배기업)와 다라물산(종속기업, 지분 80%)을 쓴다. 단위는 억원.
표준 라이브러리만 쓴다.
"""

import platform

STAKE = 0.80
NCI_RATE = 1 - STAKE


def attribution() -> None:
    sub_equity_start = 150.0
    net_income = 50.0
    oci = 10.0
    dividend = 10.0  # 다라물산이 주주 전체에 지급

    nci_start = sub_equity_start * NCI_RATE
    ni_parent = net_income * STAKE
    ni_nci = net_income * NCI_RATE
    oci_parent = oci * STAKE
    oci_nci = oci * NCI_RATE
    div_nci = dividend * NCI_RATE  # 지배기업 몫 8은 연결에서 내부거래로 제거된다
    nci_end = nci_start + ni_nci + oci_nci - div_nci

    print("[1] 연결 포괄손익 귀속 — 다라물산 당기순이익 50, 기타포괄이익 10, 배당 10")
    print(f"{'':>14}{'지배기업 소유주':>14}{'비지배지분':>10}{'합계':>8}")
    print(f"{'당기순이익':>14}{ni_parent:>14.1f}{ni_nci:>10.1f}{net_income:>8.1f}")
    print(f"{'기타포괄이익':>14}{oci_parent:>14.1f}{oci_nci:>10.1f}{oci:>8.1f}")
    print(f"{'총포괄이익':>14}{ni_parent + oci_parent:>14.1f}{ni_nci + oci_nci:>10.1f}{net_income + oci:>8.1f}")
    print()
    print(f"  비지배지분 기초 {nci_start:.1f} + 순이익 몫 {ni_nci:.1f} + 기타포괄 몫 {oci_nci:.1f}"
          f" - 배당 몫 {div_nci:.1f} = 기말 {nci_end:.1f}")

    parent_shares = 1000.0  # 만주, 가정
    parent_own_ni = 120.0  # 가나전자 자체 이익, 가정 (배당수익 제외)
    consolidated_ni = parent_own_ni + net_income
    eps_wrong = consolidated_ni / parent_shares * 10  # 억원/만주 -> 원 환산 계수 10000
    eps_right = (parent_own_ni + ni_parent) / parent_shares * 10
    print()
    print(f"  가나전자 자체 이익 {parent_own_ni:.0f}, 발행주식 {parent_shares:.0f}만주 (가정)")
    print(f"  연결 당기순이익 {consolidated_ni:.1f} 전부를 쓴 값  {eps_wrong * 1000:,.0f}원 (틀림)")
    print(f"  지배기업 소유주 귀속 {parent_own_ni + ni_parent:.1f}를 쓴 값  {eps_right * 1000:,.0f}원")


def negative_nci() -> None:
    sub_equity_start = 150.0
    loss = -200.0
    nci_start = sub_equity_start * NCI_RATE
    nci_loss = loss * NCI_RATE
    nci_end = nci_start + nci_loss
    print()
    print("[2] 큰 손실 — 다라물산 당기순손실 200")
    print(f"  종속기업 자본 {sub_equity_start:.0f} -> {sub_equity_start + loss:.0f}")
    print(f"  비지배지분 기초 {nci_start:.1f} + 손실 몫 {nci_loss:.1f} = 기말 {nci_end:.1f}")
    print(f"  지배기업 소유주 귀속 손실 {loss * STAKE:.1f}")
    print(f"  비지배지분이 {'음수(적자)' if nci_end < 0 else '양수'} — 손실 귀속을 0에서 멈추지 않는다")


def additional_purchase() -> None:
    nci_carrying = 40.0  # [1] 기말 비지배지분
    bought_share = 0.10  # 종속기업 전체 지분의 10%p를 비지배주주에게서 산다
    price = 22.0
    removed = nci_carrying * (bought_share / NCI_RATE)
    diff = price - removed
    print()
    print("[3] 지배력을 유지한 채 지분 10%p 추가 취득 — 지급 22")
    print(f"  비지배지분 장부금액 {nci_carrying:.1f} 중 {bought_share / NCI_RATE:.0%}를 제거 = {removed:.1f}")
    print(f"  지급액 {price:.1f} - 제거액 {removed:.1f} = 차이 {diff:.1f}")
    print(f"  차이는 손익이 아니라 지배기업 소유주지분에서 {diff:.1f}를 줄인다 (영업권·손익 없음)")
    print(f"  지분율 {STAKE:.0%} -> {STAKE + bought_share:.0%}, 비지배지분 {nci_carrying:.1f} -> {nci_carrying - removed:.1f}")


def main() -> None:
    print(f"환경: Python {platform.python_version()}")
    print()
    attribution()
    negative_nci()
    additional_purchase()


if __name__ == "__main__":
    main()
