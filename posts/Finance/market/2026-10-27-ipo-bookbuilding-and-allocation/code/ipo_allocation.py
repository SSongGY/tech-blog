"""공모주 청약 — 수요예측으로 공모가를 정하고, 균등·비례로 배정한다.

가상 회사 `마루소재`의 기업공개를 놓고 두 단계를 계산한다.

1. 수요예측: 기관투자자가 가격별로 낸 주문을 누적해 가격마다 경쟁률을 구한다.
   어느 가격까지 물량이 다 차는지가 보이면 밴드 상단이 왜 나오는지도 보인다.
2. 배정: 공모주식을 유형군별로 나누고, 일반청약자 몫을 균등방식과 비례방식으로
   다시 나눠 청약자 세 명이 각각 몇 주를 받는지 센다.

실재하는 회사가 아니다. 주식수·가격·주문·청약자 전부 지어낸 값이다.
"""

import sys
from collections import OrderedDict

# ---------------------------------------------------------------- 공모 개요

OFFER_SHARES = 2_000_000       # 공모예정주식수
BAND_LOW = 12_000              # 공모희망가격 하단
BAND_HIGH = 15_000             # 공모희망가격 상단
DEPOSIT_RATE = 0.50            # 청약증거금률. 규정에 비율이 없고 주관사가 정한다

# 수요예측 주문: (참여 기관이 적어 낸 가격, 그 가격에 받겠다는 수량)
# 가격을 적지 않고 수량만 내는 주문이 실제로는 섞이지만, 여기서는 전부 가격을 적었다고 둔다.
BIDS = [
    (16_000, 14_000_000),
    (15_000, 23_000_000),
    (14_000, 9_000_000),
    (13_000, 4_000_000),
    (12_000, 2_500_000),
    (11_000, 1_500_000),
]

# 일반청약자 세 명. 균등방식은 최소 청약증거금만 넘으면 수량과 무관하게 같은 기회를 받는다.
RETAIL = OrderedDict([
    ("소액 청약자", 10),
    ("중간 청약자", 1_000),
    ("대량 청약자", 20_000),
])

EQUAL_APPLICANTS = 180_000     # 균등방식 청약 건수
PRO_RATA_APPLIED = 50_000_000  # 비례방식에 들어온 전체 청약수량


def print_environment():
    print("[환경]")
    print(f"  Python {sys.version.split()[0]}")
    print()


def print_offering():
    print("[공모 개요] 가상 회사 마루소재")
    print(f"  공모예정주식수   {OFFER_SHARES:>12,} 주")
    print(f"  공모희망가격     {BAND_LOW:>12,} ~ {BAND_HIGH:,} 원")
    print(f"  공모예정금액     {OFFER_SHARES * BAND_HIGH:>12,} 원  (밴드 상단 × 공모예정주식수)")
    print(f"  청약증거금률     {DEPOSIT_RATE:>12.0%}")
    print()


def demand_forecast():
    """가격을 내림차순으로 훑으며 누적 수요량과 경쟁률을 구한다."""
    print("[1단계] 수요예측 — 가격별 누적 수요")
    print(f"  {'가격':>8} {'해당 가격 주문':>14} {'누적 수요':>14} {'누적 경쟁률':>12} {'물량':>6}")
    print("  " + "-" * 60)

    cumulative = 0
    clearing = None
    for price, qty in sorted(BIDS, reverse=True):
        cumulative += qty
        ratio = cumulative / OFFER_SHARES
        filled = "충족" if cumulative >= OFFER_SHARES else "미달"
        if clearing is None and cumulative >= OFFER_SHARES:
            clearing = price
        band = "" if BAND_LOW <= price <= BAND_HIGH else "  <- 밴드 밖"
        print(f"  {price:>8,} {qty:>14,} {cumulative:>14,} {ratio:>11,.1f}:1 {filled:>6}{band}")

    print()
    print(f"  공모예정주식수를 처음 넘기는 가격: {clearing:,} 원")
    print(f"  밴드 상단({BAND_HIGH:,} 원) 이상에 들어온 수요만 세어도 "
          f"{sum(q for p, q in BIDS if p >= BAND_HIGH):,} 주")
    print()
    return clearing


def decide_price():
    """확정 공모가는 공식이 아니라 협의로 정해진다. 여기서는 밴드 상단으로 둔다."""
    final = BAND_HIGH
    print("[2단계] 확정 공모가")
    print(f"  확정 공모가      {final:>12,} 원")
    print(f"  공모금액         {OFFER_SHARES * final:>12,} 원")
    print()
    return final


def allocate_groups():
    """유형군별 배정. 비율은 증권 인수업무 등에 관한 규정 제9조제1항의 하한을 그대로 쓴다."""
    print("[3단계] 유형군별 배정 (유가증권시장 상장 가정)")
    plan = OrderedDict([
        ("우리사주조합원", 0.20),
        ("일반청약자", 0.25),
        ("고위험고수익투자신탁등", 0.05),
    ])
    assigned = 0
    for name, rate in plan.items():
        shares = int(OFFER_SHARES * rate)
        assigned += shares
        print(f"  {name:<22} {rate:>5.0%} {shares:>12,} 주")
    rest = OFFER_SHARES - assigned
    print(f"  {'기관투자자(잔여)':<22} {rest / OFFER_SHARES:>5.0%} {rest:>12,} 주")
    print(f"  {'합계':<22} {'':>5} {OFFER_SHARES:>12,} 주")
    print()
    return int(OFFER_SHARES * plan["일반청약자"])


def split_retail(retail_shares):
    equal = retail_shares // 2
    pro_rata = retail_shares - equal
    print("[4단계] 일반청약자 몫을 균등과 비례로 나눈다")
    print(f"  일반청약자 배정  {retail_shares:>12,} 주")
    print(f"  균등방식 (50%)   {equal:>12,} 주")
    print(f"  비례방식         {pro_rata:>12,} 주")
    print()
    return equal, pro_rata


def equal_allocation(equal_shares):
    """균등방식: 청약 건수로 나눈 몫만큼 모두에게 주고, 나머지는 추첨으로 돌린다.

    규정은 '동등한 배정기회'만 정하고 방법은 인수회사가 정하므로, 이 몫수와 추첨은
    계산을 보이려고 둔 가정이다.
    """
    base = equal_shares // EQUAL_APPLICANTS
    leftover = equal_shares - base * EQUAL_APPLICANTS
    print("[5단계] 균등방식 — 청약수량을 보지 않는다")
    print(f"  균등 배정물량    {equal_shares:>12,} 주")
    print(f"  균등 청약 건수   {EQUAL_APPLICANTS:>12,} 건")
    print(f"  1건당 기본 배정  {base:>12,} 주")
    print(f"  추첨에 돌릴 잔여 {leftover:>12,} 주 "
          f"(= {EQUAL_APPLICANTS:,}건 중 {leftover:,}건이 1주를 더 받는다)")
    print(f"  추첨에 걸릴 확률 {leftover / EQUAL_APPLICANTS:>12.1%}")
    print()
    return base


def pro_rata_allocation(pro_rata_shares, equal_base, price):
    """비례방식: 청약수량에 비례. 소수점 이하를 버린다고 둔다."""
    ratio = PRO_RATA_APPLIED / pro_rata_shares
    print("[6단계] 비례방식 — 청약수량에 비례")
    print(f"  비례 배정물량    {pro_rata_shares:>12,} 주")
    print(f"  비례 청약수량    {PRO_RATA_APPLIED:>12,} 주")
    print(f"  비례 경쟁률      {ratio:>11,.1f}:1  (청약 {ratio:,.0f}주당 1주)")
    print()
    header = (f"  {'청약자':<12} {'청약수량':>10} {'증거금':>14} "
              f"{'균등':>6} {'비례':>6} {'배정':>6} {'납입금':>12} {'환불금':>14}")
    print(header)
    print("  " + "-" * (len(header) - 2))

    for name, qty in RETAIL.items():
        deposit = int(qty * price * DEPOSIT_RATE)
        pro_rata = int(pro_rata_shares * qty / PRO_RATA_APPLIED)
        allotted = equal_base + pro_rata
        paid = allotted * price
        print(f"  {name:<12} {qty:>10,} {deposit:>14,} "
              f"{equal_base:>6,} {pro_rata:>6,} {allotted:>6,} {paid:>12,} {deposit - paid:>14,}")
    print()


def efficiency(price, equal_base, pro_rata_shares):
    """같은 증거금을 넣었을 때 한 주를 받는 데 얼마가 들었는지 센다."""
    print("[7단계] 증거금 대비 배정 — 균등방식이 바꾸는 자리")
    print(f"  {'청약자':<12} {'증거금':>14} {'배정':>6} {'1주당 묶인 증거금':>18}")
    print("  " + "-" * 56)
    for name, qty in RETAIL.items():
        deposit = int(qty * price * DEPOSIT_RATE)
        allotted = equal_base + int(pro_rata_shares * qty / PRO_RATA_APPLIED)
        print(f"  {name:<12} {deposit:>14,} {allotted:>6,} {deposit // allotted:>18,}")
    print()
    print("  증거금은 2,000배 차이가 나는데 배정은 100배 차이에 그친다.")
    print("  균등방식 1주가 소액 청약자 쪽에서만 비중을 갖기 때문이다.")
    print()


def main():
    print_environment()
    print_offering()
    demand_forecast()
    price = decide_price()
    retail = allocate_groups()
    equal_shares, pro_rata_shares = split_retail(retail)
    base = equal_allocation(equal_shares)
    pro_rata_allocation(pro_rata_shares, base, price)
    efficiency(price, base, pro_rata_shares)


if __name__ == "__main__":
    main()
