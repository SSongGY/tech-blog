"""단계적 취득 — 기존 보유 지분 재측정, 영업권, 기존 지분 분류별 당기손익 차이.

가상 회사 가나전자(취득자)가 마바화학 지분 35%를 갖고 있다가 40%를 더 사 75%로
지배력을 얻는다. 단위는 억원. 표준 라이브러리만 쓴다.
"""

import platform

OLD_STAKE = 0.35
NEW_STAKE = 0.40
TOTAL_STAKE = OLD_STAKE + NEW_STAKE
NCI_RATE = 1 - TOTAL_STAKE

PRICE_FOR_NEW = 100.0  # 40%를 사며 낸 현금
NET_ASSETS_FV = 200.0  # 취득일 식별 가능한 순자산 공정가치
# 같은 날 같은 값으로 거래된 주당 가격을 기존 지분에도 쓴다고 가정한다
OLD_STAKE_FV = PRICE_FOR_NEW / NEW_STAKE * OLD_STAKE


def goodwill() -> float:
    nci = NET_ASSETS_FV * NCI_RATE  # 비례적 지분으로 측정
    gw = PRICE_FOR_NEW + nci + OLD_STAKE_FV - NET_ASSETS_FV
    gw_wrong_carrying = 70.0  # 지분법 장부금액을 그대로 넣었을 때
    gw_wrong = PRICE_FOR_NEW + nci + gw_wrong_carrying - NET_ASSETS_FV

    print("[1] 영업권 — 제1103호 문단 32")
    print(f"  지분율 {OLD_STAKE:.0%} + {NEW_STAKE:.0%} = {TOTAL_STAKE:.0%}, 비지배지분 {NCI_RATE:.0%}")
    print(f"  (가) 이전대가 (새로 산 {NEW_STAKE:.0%})       {PRICE_FOR_NEW:>7.1f}")
    print(f"  (나) 비지배지분 (순자산 x {NCI_RATE:.0%})       {nci:>7.1f}")
    print(f"  (다) 기존 {OLD_STAKE:.0%} 지분의 취득일 공정가치  {OLD_STAKE_FV:>7.1f}")
    print(f"  (2) 식별 가능한 순자산 공정가치      -{NET_ASSETS_FV:>6.1f}")
    print(f"  영업권                               {gw:>7.1f}")
    print()
    print(f"  (다)에 공정가치 대신 장부금액 {gw_wrong_carrying:.1f}를 넣으면 영업권 {gw_wrong:.1f} (틀림)")
    return gw


def by_classification() -> None:
    print()
    print("[2] 기존 35% 지분을 어떻게 분류해 왔느냐에 따라 취득일 당기손익이 갈린다")
    cases = [
        # 이름, 직전 장부금액, 누적 기타포괄손익(지배기업 몫), 재측정 차액이 가는 곳, OCI 재분류 여부
        ("관계기업(지분법)", 70.0, 4.0, "당기손익", True),
        ("FVOCI 지정 지분상품", 80.0, 20.0, "기타포괄손익", False),
        ("FVPL 금융자산", 80.0, 0.0, "당기손익", False),
    ]
    print(f"  {'분류':<14}{'장부':>7}{'공정가치':>8}{'차액':>7}{'차액이 가는 곳':>12}"
          f"{'OCI 재분류':>10}{'당기손익':>9}")
    for name, carrying, acc_oci, where, recycle in cases:
        diff = OLD_STAKE_FV - carrying
        recycled = acc_oci if recycle else 0.0
        pl = (diff if where == "당기손익" else 0.0) + recycled
        print(f"  {name:<14}{carrying:>7.1f}{OLD_STAKE_FV:>8.1f}{diff:>7.1f}{where:>12}"
              f"{recycled:>10.1f}{pl:>9.1f}")
    print()
    print("  관계기업: 지분법으로 쌓인 외화환산 몫 4.0은 직접 처분한 것처럼 당기손익으로 재분류")
    print("  FVOCI   : 차액 7.5도 기타포괄손익, 누적 27.5는 당기손익으로 옮기지 않는다")
    print("            (자본 안에서 이익잉여금으로 대체할 수는 있다)")
    print("  영업권은 세 경우 모두 같다 — 공정가치 87.5가 들어가기 때문")


def main() -> None:
    print(f"환경: Python {platform.python_version()}")
    print()
    goodwill()
    by_classification()


if __name__ == "__main__":
    main()
