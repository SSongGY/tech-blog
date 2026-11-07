"""연결 내부거래 미실현이익 — 재고·설비 하향거래와 재고 상향거래.

가상 회사 가나지주(지배기업)가 다라부품 지분 80%를 갖고 있다. 단위는 억원.
기업회계기준서 제1110호 적용지침 B86(3): 자산으로 남은 내부거래 손익은 모두 제거하고,
제거로 생긴 일시적차이에는 제1012호 '법인세'를 적용한다.
표준 라이브러리만 쓴다.
"""

import platform

STAKE = 0.80
TAX_RATE = 0.20  # 계산을 보이려고 정한 단일 세율


def inventory_downstream() -> float:
    """가나지주 -> 다라부품 재고 판매. 1년차 말 25%가 다라부품 창고에 남는다."""
    cost = 300.0
    intragroup_price = 400.0
    sold_out_ratio = 0.75
    outside_price_y1 = 450.0  # 다라부품이 75%를 외부에 판 금액
    outside_price_y2 = 150.0  # 남은 25%를 2년차에 외부에 판 금액

    left_at_price = intragroup_price * (1 - sold_out_ratio)  # 100
    left_at_cost = cost * (1 - sold_out_ratio)  # 75
    unrealised = left_at_price - left_at_cost  # 25

    sum_rev_y1 = intragroup_price + outside_price_y1
    sum_cogs_y1 = cost + intragroup_price * sold_out_ratio
    con_rev_y1 = outside_price_y1
    con_cogs_y1 = cost * sold_out_ratio

    print("[1] 재고 하향판매 — 가나지주가 원가 300을 400에 다라부품에 판다")
    print("  1년차: 다라부품이 75%를 외부에 450에 팔고 25%가 남는다")
    print(f"  {'':24}{'단순합산':>10}{'연결':>10}{'차이':>10}")
    print(f"  {'매출':24}{sum_rev_y1:>10.1f}{con_rev_y1:>10.1f}{con_rev_y1 - sum_rev_y1:>10.1f}")
    print(f"  {'매출원가':24}{sum_cogs_y1:>10.1f}{con_cogs_y1:>10.1f}{con_cogs_y1 - sum_cogs_y1:>10.1f}")
    gp_sum, gp_con = sum_rev_y1 - sum_cogs_y1, con_rev_y1 - con_cogs_y1
    print(f"  {'매출총이익':24}{gp_sum:>10.1f}{gp_con:>10.1f}{gp_con - gp_sum:>10.1f}")
    print(f"  {'기말 재고':24}{left_at_price:>10.1f}{left_at_cost:>10.1f}{left_at_cost - left_at_price:>10.1f}")
    dta = unrealised * TAX_RATE
    print(f"  미실현이익 {unrealised:.1f} 제거, 이연법인세자산 {dta:.1f} (세율 {TAX_RATE:.0%})")
    print(f"  연결 당기순이익 영향 1년차 {-(unrealised - dta):+.1f}")
    print()
    gp_sum_y2 = outside_price_y2 - left_at_price
    gp_con_y2 = outside_price_y2 - left_at_cost
    print("  2년차: 남은 25%를 외부에 150에 판다")
    print(f"  {'매출총이익':24}{gp_sum_y2:>10.1f}{gp_con_y2:>10.1f}{gp_con_y2 - gp_sum_y2:>10.1f}")
    print(f"  이연법인세자산 {dta:.1f} 소멸, 연결 당기순이익 영향 2년차 {unrealised - dta:+.1f}")
    print(f"  2년 합계 매출총이익 단순합산 {gp_sum + gp_sum_y2:.1f} = 연결 {gp_con + gp_con_y2:.1f}")
    return unrealised


def equipment_downstream() -> None:
    """가나지주 -> 다라부품 설비 이전. 장부 80을 120에 팔고 잔존 내용연수 4년 정액법."""
    carrying = 80.0
    price = 120.0
    life = 4
    gain = price - carrying  # 40
    dep_sub = price / life  # 다라부품 장부의 감가상각비 30
    dep_group = carrying / life  # 연결실체 관점 감가상각비 20

    print()
    print("[2] 설비 하향이전 — 장부 80을 120에 넘기고 다라부품이 4년 정액 상각")
    print(f"  처분이익 {gain:.1f} 은 1년차에 전부 제거, 감가상각비 차이 {dep_sub - dep_group:.1f}/년이 되돌린다")
    print(f"  {'연차':>4}{'처분이익 제거':>14}{'상각비 조정':>12}{'세전 영향':>10}"
          f"{'다라 장부':>10}{'연결 장부':>10}{'차이':>8}")
    total = 0.0
    for year in range(1, life + 1):
        gain_adj = -gain if year == 1 else 0.0
        dep_adj = dep_sub - dep_group
        effect = gain_adj + dep_adj
        total += effect
        sub_book = price - dep_sub * year
        group_book = carrying - dep_group * year
        print(f"  {year:>4}{gain_adj:>14.1f}{dep_adj:>12.1f}{effect:>10.1f}"
              f"{sub_book:>10.1f}{group_book:>10.1f}{group_book - sub_book:>8.1f}")
    print(f"  4년 합계 세전 영향 {total:.1f}")


def inventory_upstream(unrealised: float) -> None:
    """다라부품 -> 가나지주 재고 판매. 금액은 [1]과 같다. 법인세는 생략한다."""
    sub_net_income = 100.0  # 다라부품이 보고한 당기순이익 (내부거래 이익 포함)
    adjusted = sub_net_income - unrealised

    print()
    print("[3] 재고 상향판매 — 같은 거래를 다라부품이 가나지주에 판 경우 (법인세 생략)")
    print(f"  연결에서 제거하는 미실현이익은 하향과 같이 {unrealised:.1f} 전부 (B86(3))")
    print(f"  다라부품 보고 순이익 {sub_net_income:.1f}, 제거 후 {adjusted:.1f}")
    print(f"  {'배분 방식':30}{'지배기업 소유주':>14}{'비지배지분':>12}")
    nci_a = sub_net_income * (1 - STAKE)
    print(f"  {'(가) 제거액 전부 지배기업 부담':28}{sub_net_income * STAKE - unrealised:>14.1f}{nci_a:>12.1f}")
    nci_b = adjusted * (1 - STAKE)
    print(f"  {'(나) 제거 후 이익을 지분율로 배분':28}{adjusted * STAKE:>14.1f}{nci_b:>12.1f}")
    print(f"  두 방식 모두 연결 당기순이익은 {adjusted:.1f}, 갈리는 것은 귀속 {nci_a - nci_b:.1f}")


def main() -> None:
    print(f"환경: Python {platform.python_version()}")
    print(f"출발점: 가나지주가 다라부품 지분 {STAKE:.0%} 보유, 단위 억원")
    print()
    unrealised = inventory_downstream()
    equipment_downstream()
    inventory_upstream(unrealised)


if __name__ == "__main__":
    main()
