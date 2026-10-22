"""같은 연구개발 지출을 자산화했을 때와 비용 처리했을 때의 차이를 계산한다.

가상 회사 둘이 똑같은 프로젝트에 똑같은 금액을 쓴다. 가나전자는 개발단계 인식요건을
입증하지 못해 전액 비용으로 처리하고, 다라물산은 1년차 중반부터 요건을 충족했다고 보아
지출의 60%를 개발비로 자산화한다. 현금 지출이 같은데 영업이익·자산총계·ROA가 어떻게
갈리는지, 프로젝트 수명 전체로 보면 왜 같아지는지, 개발이 실패하면 무엇이 달라지는지를
계산한다.

금액 단위는 억원이다. 세금과 이자는 비교를 흐리지 않으려고 넣지 않았다.
파이썬 표준 라이브러리만 쓴다.
"""

SPEND_PER_YEAR = 300.0      # 개발 기간 중 해마다 쓰는 연구개발비
DEV_YEARS = 2               # 1~2년차에 개발하고 2년차 말에 완성한다
CAPITALISE_RATIO = 0.60     # 다라물산이 개발단계 이후로 판단한 비율
AMORT_YEARS = 5             # 완성한 개발비의 상각 기간 (정액법)
HORIZON = 7                 # 1년차부터 상각이 끝나는 7년차까지

OPERATING_BEFORE_RND = 400.0   # 연구개발비를 빼기 전 영업이익
OPENING_EQUITY = 1_800.0
DEBT = 1_200.0
OTHER_ASSETS = 3_000.0         # 연구개발 지출과 무관한 자산 (양사 동일)


def capitalised_total():
    return SPEND_PER_YEAR * DEV_YEARS * CAPITALISE_RATIO


def yearly_figures(capitalise_ratio):
    """해마다의 (비용 처리액, 상각비, 영업이익, 기말 개발비 장부금액)."""
    asset_total = SPEND_PER_YEAR * DEV_YEARS * capitalise_ratio
    amort_per_year = asset_total / AMORT_YEARS if asset_total else 0.0
    rows = []
    book = 0.0
    for year in range(1, HORIZON + 1):
        if year <= DEV_YEARS:
            expensed = SPEND_PER_YEAR * (1 - capitalise_ratio)
            book += SPEND_PER_YEAR * capitalise_ratio
            amort = 0.0
        else:
            expensed = 0.0
            amort = min(amort_per_year, book)
            book -= amort
        operating = OPERATING_BEFORE_RND - expensed - amort
        rows.append((year, expensed, amort, operating, book))
    return rows


def section_1():
    print("[1] 두 회사의 전제 — 쓰는 돈은 같고 판단만 다르다")
    print(f"    프로젝트: 1~2년차에 해마다 {SPEND_PER_YEAR:,.0f} 지출, "
          f"2년차 말 완성, 완성 후 {AMORT_YEARS}년 정액상각")
    print(f"    연구개발비를 빼기 전 영업이익: 해마다 {OPERATING_BEFORE_RND:,.0f}")
    print()
    print(f"    {'회사':<10}{'판단':<34}{'자산화':>10}{'즉시 비용':>12}")
    print(f"    {'가나전자':<10}{'개발단계 인식요건을 입증하지 못함':<34}"
          f"{0.0:>10,.1f}{SPEND_PER_YEAR * DEV_YEARS:>12,.1f}")
    print(f"    {'다라물산':<10}{'1년차 중반부터 6가지 요건 모두 충족':<34}"
          f"{capitalised_total():>10,.1f}"
          f"{SPEND_PER_YEAR * DEV_YEARS - capitalised_total():>12,.1f}")
    print(f"    현금으로 나가는 돈은 두 회사 모두 "
          f"{SPEND_PER_YEAR * DEV_YEARS:,.0f}으로 같다")
    print()


def section_2():
    kana = yearly_figures(0.0)
    dara = yearly_figures(CAPITALISE_RATIO)
    print("[2] 연도별 영업이익 — 같은 돈을 쓰는데 손익계산서가 갈린다")
    print(f"    {'연도':<8}{'가나 비용':>10}{'가나 상각':>10}{'가나 영업이익':>14}"
          f"{'다라 비용':>10}{'다라 상각':>10}{'다라 영업이익':>14}{'차이':>10}")
    for (y, ke, ka, kop, _), (_, de, da, dop, _) in zip(kana, dara):
        print(f"    {y}년차{'':<4}{ke:>10,.1f}{ka:>10,.1f}{kop:>14,.1f}"
              f"{de:>10,.1f}{da:>10,.1f}{dop:>14,.1f}{dop - kop:>+10,.1f}")
    print(f"    개발 기간에는 다라물산의 영업이익이 높고, 상각이 시작되면 역전된다")
    print()
    return kana, dara


def section_3(kana, dara):
    k_total = sum(r[3] for r in kana)
    d_total = sum(r[3] for r in dara)
    k_cost = sum(r[1] + r[2] for r in kana)
    d_cost = sum(r[1] + r[2] for r in dara)
    print("[3] 7년 합계는 같다 — 갈리는 것은 시점이지 총액이 아니다")
    print(f"    {'회사':<10}{'손익에 반영한 연구개발비':>24}{'7년 영업이익 합계':>20}")
    print(f"    {'가나전자':<10}{k_cost:>24,.1f}{k_total:>20,.1f}")
    print(f"    {'다라물산':<10}{d_cost:>24,.1f}{d_total:>20,.1f}")
    print(f"    자산화는 비용을 없애는 것이 아니라 뒤로 미루는 것이다")
    print(f"    다만 {AMORT_YEARS}년 상각이 끝나기 전에 잘라 보면 차이가 남는다 — "
          f"5년차까지만 더하면 "
          f"{sum(r[3] for r in kana[:5]):,.1f} 대 {sum(r[3] for r in dara[:5]):,.1f}")
    print()


def section_4(kana, dara):
    """2년차 말 재무상태표와 비율."""
    k_year2, d_year2 = kana[1], dara[1]
    k_cum = sum(r[3] for r in kana[:2])
    d_cum = sum(r[3] for r in dara[:2])

    k_assets = OTHER_ASSETS + k_cum
    k_equity = OPENING_EQUITY + k_cum
    d_assets = OTHER_ASSETS + k_cum + d_year2[4]
    d_equity = OPENING_EQUITY + d_cum

    print("[4] 2년차 말 재무상태표 — 현금은 같은데 자산총계가 다르다")
    print(f"    {'':<10}{'개발비 자산':>12}{'자산총계':>12}{'부채':>10}{'자본':>10}"
          f"{'부채비율':>10}{'ROA':>9}")
    print(f"    {'가나전자':<10}{0.0:>12,.1f}{k_assets:>12,.1f}{DEBT:>10,.1f}"
          f"{k_equity:>10,.1f}{DEBT / k_equity * 100:>9.1f}%"
          f"{k_year2[3] / k_assets * 100:>8.1f}%")
    print(f"    {'다라물산':<10}{d_year2[4]:>12,.1f}{d_assets:>12,.1f}{DEBT:>10,.1f}"
          f"{d_equity:>10,.1f}{DEBT / d_equity * 100:>9.1f}%"
          f"{d_year2[3] / d_assets * 100:>8.1f}%")
    print(f"    ROA는 분자(영업이익)와 분모(자산총계)가 함께 커지지만 "
          f"분자 쪽이 더 크게 움직인다")
    print(f"    두 회사의 현금 잔액은 같다 — 벌어진 것은 "
          f"개발비 자산 {d_year2[4]:,.1f}과 그만큼의 이익잉여금뿐이다")
    print()


def section_5(kana, dara):
    """3년차에 개발이 실패해 자산을 떨어내는 경우."""
    asset = capitalised_total()
    k_year3 = kana[2]
    d_year3 = dara[2]
    d_impaired = OPERATING_BEFORE_RND - asset   # 상각 대신 잔액 전부를 손상으로

    print("[5] 3년차에 프로젝트를 접으면 — 자산화한 쪽이 한꺼번에 떨어낸다")
    print(f"    {'회사':<10}{'3년차 비용':>12}{'3년차 영업이익':>16}{'남은 개발비 자산':>18}")
    print(f"    {'가나전자':<10}{0.0:>12,.1f}{k_year3[3]:>16,.1f}{0.0:>18,.1f}")
    print(f"    {'다라물산':<10}{asset:>12,.1f}{d_impaired:>16,.1f}{0.0:>18,.1f}")
    print(f"    가나전자는 1~2년차에 이미 털어 두었으므로 3년차에 추가 손실이 없다")
    print(f"    다라물산은 미리 당겨 놓았던 이익 {asset:,.1f}을 한 해에 반납한다")
    print(f"    계획대로 갔다면 3년차 영업이익 {d_year3[3]:,.1f} — "
          f"실패하면 {d_impaired:,.1f}로 떨어진다")
    print(f"    한 번 비용으로 인식한 지출은 나중에 자산으로 되돌릴 수 없다")
    print()


def main():
    print("가나전자와 다라물산의 연구개발비 — 금액 단위는 억원")
    print("=" * 78)
    print()
    section_1()
    kana, dara = section_2()
    section_3(kana, dara)
    section_4(kana, dara)
    section_5(kana, dara)


if __name__ == "__main__":
    main()
