"""같은 건물을 원가모형과 재평가모형으로 들고 있을 때의 차이를 계산한다.

가상 회사 둘이 같은 건물을 같은 값에 사서 같은 방식으로 감가상각한다. 가나전자는
원가모형을 계속 쓰고, 다라물산은 2년차 말에 재평가모형으로 공정가치를 반영한다.
재평가 직후의 자본·부채비율, 그 뒤의 감가상각비와 영업이익, 건물을 팔 때의 처분이익이
어떻게 갈리는지 계산한다. 마지막으로 토지 하나로 평가증과 평가감이 서로 다른 곳으로
가는 비대칭을 따로 보인다.

금액 단위는 억원이다. 비교를 흐리지 않으려고 법인세와 이연법인세는 넣지 않았다.
파이썬 표준 라이브러리만 쓴다.
"""

BUILDING_COST = 1_000.0     # 건물 취득원가
USEFUL_LIFE = 10            # 내용연수, 잔존가치 0, 정액법
REVALUE_YEAR = 2            # 다라물산이 재평가하는 해 (그 해 말)
FAIR_VALUE = 1_200.0        # 2년차 말 공정가치
SALE_YEAR = 5               # 건물을 파는 해 (그 해 말, 그 해 감가상각 후)
SALE_PRICE = 1_050.0

OTHER_ASSETS = 2_000.0      # 건물 말고 나머지 자산 (양사 동일)
DEBT = 1_500.0
OPERATING_BEFORE_DEP = 300.0   # 감가상각비를 빼기 전 영업이익


def carrying_after(years, cost=BUILDING_COST, life=USEFUL_LIFE):
    return cost - cost / life * years


def section_1():
    print("[1] 두 회사의 전제 — 같은 건물, 같은 감가상각, 정책만 다르다")
    print(f"    건물 취득원가 {BUILDING_COST:,.0f}, 내용연수 {USEFUL_LIFE}년, "
          f"정액법, 잔존가치 0")
    print(f"    {REVALUE_YEAR}년차 말 공정가치 {FAIR_VALUE:,.0f}")
    print(f"    가나전자: 원가모형 / 다라물산: {REVALUE_YEAR}년차 말부터 재평가모형")
    print()


def section_2():
    book = carrying_after(REVALUE_YEAR)
    surplus = FAIR_VALUE - book
    print(f"[2] {REVALUE_YEAR}년차 말 재평가 — 늘어난 금액은 손익을 거치지 않는다")
    print(f"    재평가 직전 장부금액 {book:,.1f}  ->  공정가치 {FAIR_VALUE:,.1f}")
    print(f"    차이 {surplus:,.1f} 을 기타포괄손익으로 인식해 재평가잉여금에 쌓는다")
    print(f"    그 해 당기순이익에 들어간 금액: 0.0")
    print()
    print(f"    {'회사':<10}{'건물':>10}{'자산총계':>10}{'부채':>10}"
          f"{'자본':>10}{'부채비율':>10}")
    base_equity = OTHER_ASSETS + book - DEBT
    for name, building in (("가나전자", book), ("다라물산", FAIR_VALUE)):
        assets = OTHER_ASSETS + building
        equity = assets - DEBT
        print(f"    {name:<10}{building:>10,.1f}{assets:>10,.1f}{DEBT:>10,.1f}"
              f"{equity:>10,.1f}{DEBT / equity:>10.1%}")
    print(f"    차입금은 한 푼도 갚지 않았는데 부채비율이 "
          f"{DEBT / base_equity:.1%} 에서 {DEBT / (base_equity + surplus):.1%} 로 내려간다")
    print()
    return surplus


def section_3(surplus):
    remaining = USEFUL_LIFE - REVALUE_YEAR
    dep_cost = BUILDING_COST / USEFUL_LIFE
    dep_reval = FAIR_VALUE / remaining
    transfer = dep_reval - dep_cost
    print(f"[3] {REVALUE_YEAR + 1}년차부터 — 올린 장부가는 감가상각비로 돌아온다")
    print(f"    {'연도':<8}{'가나 상각비':>12}{'가나 영업이익':>14}"
          f"{'다라 상각비':>12}{'다라 영업이익':>14}{'잉여금 대체':>12}")
    for year in range(REVALUE_YEAR + 1, REVALUE_YEAR + 4):
        print(f"    {str(year) + '년차':<8}{dep_cost:>12,.1f}"
              f"{OPERATING_BEFORE_DEP - dep_cost:>14,.1f}"
              f"{dep_reval:>12,.1f}{OPERATING_BEFORE_DEP - dep_reval:>14,.1f}"
              f"{transfer:>12,.1f}")
    print(f"    다라물산은 해마다 {transfer:,.1f} 을 재평가잉여금에서 이익잉여금으로 "
          f"직접 옮길 수 있다 (손익을 거치지 않음)")
    print(f"    {remaining}년 동안 영업이익 합계 차이: "
          f"{(dep_reval - dep_cost) * remaining:,.1f} = 재평가로 늘린 {surplus:,.1f}")
    print()
    return dep_reval, transfer


def section_4(surplus, dep_reval, transfer):
    years_after = SALE_YEAR - REVALUE_YEAR
    book_cost = carrying_after(SALE_YEAR)
    book_reval = FAIR_VALUE - dep_reval * years_after
    surplus_left = surplus - transfer * years_after
    print(f"[4] {SALE_YEAR}년차 말에 {SALE_PRICE:,.0f} 에 팔면 — 처분이익이 갈린다")
    print(f"    {'회사':<10}{'처분 직전 장부금액':>18}{'처분이익(손익)':>16}"
          f"{'이익잉여금 직접 대체':>20}")
    print(f"    {'가나전자':<10}{book_cost:>18,.1f}{SALE_PRICE - book_cost:>16,.1f}"
          f"{0.0:>20,.1f}")
    print(f"    {'다라물산':<10}{book_reval:>18,.1f}{SALE_PRICE - book_reval:>16,.1f}"
          f"{surplus_left:>20,.1f}")
    cum_cost = (OPERATING_BEFORE_DEP - BUILDING_COST / USEFUL_LIFE) * SALE_YEAR \
        + SALE_PRICE - book_cost
    cum_reval = (OPERATING_BEFORE_DEP - BUILDING_COST / USEFUL_LIFE) * REVALUE_YEAR \
        + (OPERATING_BEFORE_DEP - dep_reval) * years_after + SALE_PRICE - book_reval
    print(f"    1~{SALE_YEAR}년차 영업이익+처분이익 합계: 가나전자 {cum_cost:,.1f} / "
          f"다라물산 {cum_reval:,.1f}")
    reval_retained = cum_reval + transfer * years_after + surplus_left
    print(f"    다라물산은 손익이 {cum_cost - cum_reval:,.1f} 적지만, 잉여금 대체 "
          f"{transfer * years_after + surplus_left:,.1f} 이 손익을 거치지 않고 "
          f"이익잉여금에 들어간다")
    print(f"    {SALE_YEAR}년차 말 이익잉여금 증가액: 가나전자 {cum_cost:,.1f} / "
          f"다라물산 {reval_retained:,.1f}")
    print()


def land_path(cost, values):
    """토지(감가상각 없음)의 연속 재평가. 해마다 (당기손익, 기타포괄손익, 잉여금 잔액)."""
    book, surplus, pl_loss = cost, 0.0, 0.0
    rows = []
    for value in values:
        change = value - book
        if change >= 0:
            # 앞서 손익으로 인식한 평가감이 있으면 그만큼은 손익으로 되돌린다
            to_pl = min(change, pl_loss)
            to_oci = change - to_pl
            pl_loss -= to_pl
        else:
            # 잉여금 잔액까지는 기타포괄손익에서 깎고, 넘는 부분만 손익으로 간다
            to_oci = 0.0 - min(-change, surplus)
            to_pl = change - to_oci
            pl_loss += -to_pl
        surplus += to_oci
        book = value
        rows.append((value, to_pl, to_oci, surplus))
    return rows


def section_5():
    cost = 500.0
    cases = (
        ("올랐다가 내림", (700.0, 500.0)),
        ("내렸다가 오름", (300.0, 500.0)),
        ("내렸다가 더 오름", (400.0, 700.0)),
        ("올랐다가 더 내림", (600.0, 350.0)),
    )
    print(f"[5] 비대칭 — 취득원가 {cost:,.0f} 인 토지를 두 번 재평가한다")
    print(f"    {'경로':<16}{'평가액':>8}{'당기손익':>10}{'기타포괄손익':>12}"
          f"{'잉여금 잔액':>12}")
    for label, values in cases:
        for i, (value, to_pl, to_oci, surplus) in enumerate(land_path(cost, values)):
            head = label if i == 0 else ""
            print(f"    {head:<16}{value:>8,.0f}{to_pl:>+10,.1f}{to_oci:>+12,.1f}"
                  f"{surplus:>12,.1f}")
    print("    같은 가격 경로라도 오르고 내린 순서에 따라 손익으로 가는 금액이 달라진다")


def main():
    section_1()
    surplus = section_2()
    dep_reval, transfer = section_3(surplus)
    section_4(surplus, dep_reval, transfer)
    section_5()


if __name__ == "__main__":
    main()
