"""지배력 상실 — 처분손익, 잔존 지분 재측정, OCI 재분류. 지배력 유지 시 자본거래와 비교.

가상 회사 가나전자(지배기업)가 다라물산 지분 80%를 갖고 있다. 단위는 억원.
표준 라이브러리만 쓴다.
"""

import platform

STAKE = 0.80
NET_ASSETS = 250.0  # 다라물산 순자산 장부금액 (연결 기준, 영업권 제외)
GOODWILL = 30.0  # 취득 때 생긴 영업권 (부분영업권)
NCI_CARRYING = NET_ASSETS * (1 - STAKE)  # 50
FX_RESERVE_PARENT = 12.0  # 지배기업 몫 해외사업환산 누적 기타포괄손익


def loss_of_control() -> None:
    sold = 0.50
    retained = STAKE - sold
    proceeds = 150.0
    retained_fv = proceeds / sold * retained  # 같은 주당 가격을 쓴다고 가정

    derecognised = NET_ASSETS + GOODWILL - NCI_CARRYING  # 지배기업 몫 장부금액
    gain_before_oci = proceeds + retained_fv - derecognised
    gain = gain_before_oci + FX_RESERVE_PARENT

    per_point = derecognised / STAKE  # 지분 100%당 장부금액
    sold_carrying = per_point * sold
    retained_carrying = per_point * retained

    print("[1] 지배력 상실 — 80% 중 50%p를 150에 처분, 30% 잔존 (제1110호 B98)")
    print("  제거")
    print(f"    종속기업 자산·부채 순액 (영업권 포함)  {NET_ASSETS + GOODWILL:>7.1f}")
    print(f"    비지배지분 장부금액                    {-NCI_CARRYING:>7.1f}")
    print(f"    = 지배기업 몫 장부금액                 {derecognised:>7.1f}")
    print("  인식")
    print(f"    받은 대가                              {proceeds:>7.1f}")
    print(f"    잔존 {retained:.0%} 지분 공정가치                {retained_fv:>7.1f}")
    print(f"  차이                                     {gain_before_oci:>7.1f}")
    print(f"  해외사업환산 누적 OCI 재분류             {FX_RESERVE_PARENT:>7.1f}")
    print(f"  지배력 상실 처분이익 (당기손익)          {gain:>7.1f}")
    print()
    print("  처분이익을 출처별로 나누면")
    print(f"    판 {sold:.0%}p   대가 {proceeds:.1f} - 장부 {sold_carrying:.2f} = {proceeds - sold_carrying:>6.2f}")
    print(f"    남긴 {retained:.0%}p 공정가치 {retained_fv:.1f} - 장부 {retained_carrying:.2f} = {retained_fv - retained_carrying:>6.2f}")
    print(f"    OCI 재분류                          = {FX_RESERVE_PARENT:>6.2f}")
    print(f"    합계                                 = {gain:>6.2f}")
    print()
    print(f"  잔존 30% 지분은 관계기업 투자로 원가 {retained_fv:.1f}에서 지분법을 시작한다")


def keep_control() -> None:
    sold = 0.10
    proceeds = 30.0
    nci_increase = NET_ASSETS * sold  # 순자산 비례 몫만큼 비지배지분이 늘어난다
    diff = proceeds - nci_increase
    print()
    print("[2] 비교 — 10%p만 30에 처분해 70%로 지배력 유지 (제1110호 문단 23)")
    print(f"  비지배지분 증가 = 순자산 {NET_ASSETS:.0f} x {sold:.0%} = {nci_increase:.1f}")
    print(f"  받은 대가 {proceeds:.1f} - 비지배지분 증가 {nci_increase:.1f} = {diff:.1f}")
    print(f"  차이 {diff:.1f}는 지배기업 소유주지분에 직접 인식 — 당기손익 0")
    print("  잔존 지분 재측정 없음, 해외사업환산 누적액도 당기손익으로 재분류하지 않음")
    print(f"  지분율 {STAKE:.0%} -> {STAKE - sold:.0%}, 비지배지분 {NCI_CARRYING:.1f} -> {NCI_CARRYING + nci_increase:.1f}")


def main() -> None:
    print(f"환경: Python {platform.python_version()}")
    print()
    print(f"출발점: 지분 {STAKE:.0%}, 순자산 {NET_ASSETS:.0f}, 영업권 {GOODWILL:.0f}, "
          f"비지배지분 {NCI_CARRYING:.0f}, 지배기업 몫 환산 OCI {FX_RESERVE_PARENT:.0f}")
    print()
    loss_of_control()
    keep_control()


if __name__ == "__main__":
    main()
