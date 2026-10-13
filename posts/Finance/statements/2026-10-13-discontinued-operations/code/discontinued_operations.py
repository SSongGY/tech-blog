"""중단영업 — 접기로 한 사업이 손익계산서에서 떨어져 나가는 과정.

K-IFRS 제1105호 '매각예정비유동자산과 중단영업' 문단 6~8(매각예정 분류 요건),
15(순공정가치 측정), 25(감가상각 중단), 32(중단영업의 정의), 33(단일금액 표시),
34(비교표시 재작성), 36(분류 취소), 40(재무상태표는 재작성하지 않음)을 근거로
가상 회사 마바중공업의 두 해 손익을 재작성 전후로 나란히 계산한다.

회사와 금액은 전부 가상이다. 금액 단위는 백만원.
"""

# 사업부별 매출과 영업이익. 20X2년 7월 1일에 설비사업부를 매각예정으로 분류했다.
SEGMENTS = {
    "기계사업부": {"20X1": (8000, 600), "20X2": (8800, 760)},
    "설비사업부": {"20X1": (2000, -150), "20X2": (1400, -200)},
}
DISCONTINUED = "설비사업부"
YEARS = ["20X1", "20X2"]

# 매각예정 분류 직전 설비사업부의 처분자산집단 장부금액과 순공정가치 (문단 15).
CARRYING_AMOUNT = 1200
FAIR_VALUE_LESS_COSTS_TO_SELL = 950

# 설비사업부의 연간 감가상각비. 7월 1일 분류 후로는 계상하지 않는다 (문단 25).
ANNUAL_DEPRECIATION = 80
MONTHS_AFTER_CLASSIFICATION = 6

TAX_RATE = 0.22
SHARES_OUTSTANDING = 10_000  # 천주


def fmt(value):
    return f"{value:,.0f}"


def signed(value):
    return f"{'+' if value >= 0 else ''}{value:,.0f}"


def growth(before, after):
    return (after - before) / before * 100


def totals(year, segments):
    revenue = sum(SEGMENTS[s][year][0] for s in segments)
    operating = sum(SEGMENTS[s][year][1] for s in segments)
    return revenue, operating


def section_1():
    print("[1] 매각예정 분류 요건 — 문단 6~8 을 전부 충족해야 한다")
    checks = [
        ("장부금액을 계속 사용이 아니라 매각거래로 회수할 예정인가", "문단 6", True),
        ("현재 상태에서 통상적인 거래조건만으로 즉시 매각 가능한가", "문단 7", True),
        ("경영진이 매각계획을 확약하고 매수자를 찾기 시작했는가", "문단 8(a)", True),
        ("현재 공정가치에 비추어 합리적인 가격으로 추진하는가", "문단 8(b)", True),
        ("분류 시점부터 1년 내 매각 완료가 예상되는가", "문단 8(c)", True),
        ("계획이 유의적으로 변경·철회될 가능성이 낮은가", "문단 8(d)", True),
    ]
    for question, paragraph, met in checks:
        mark = "충족" if met else "미충족"
        print(f"    {question:<46}{paragraph:<10}{mark}")
    print("    하나라도 깨지면 매각예정이 아니고, 따라서 중단영업도 아니다.")
    print()

    print("[2] 중단영업의 정의 — 문단 32 의 세 경우 중 하나여야 한다")
    cases = [
        ("별도의 주요 사업계열 또는 영업지역", "설비사업부가 여기 해당한다"),
        ("주요 사업계열·영업지역을 처분하려는 단일 계획의 일부", "여러 법인을 묶어 파는 경우"),
        ("매각만을 목적으로 취득한 종속기업", "되팔려고 산 회사"),
    ]
    for case, note in cases:
        print(f"    {case:<42}{note}")
    print("    생산라인 한 줄이나 거래처 몇 곳을 정리하는 것은 구분단위가 아니어서 해당하지 않는다.")
    print()


def section_3():
    print("[3] 감가상각 중단 — 분류 시점부터 계상하지 않는다 (문단 25)")
    skipped = ANNUAL_DEPRECIATION * MONTHS_AFTER_CLASSIFICATION / 12
    reported = SEGMENTS[DISCONTINUED]["20X2"][1]
    without_rule = reported - skipped
    print(f"    설비사업부 연간 감가상각비                {fmt(ANNUAL_DEPRECIATION):>6}")
    print(f"    20X2년 7월 1일 분류 — 계상하지 않은 하반기분   {fmt(skipped):>6}")
    print(f"    분류하지 않았다면 20X2년 영업손익         {fmt(without_rule):>6}")
    print(f"    실제 20X2년 영업손익                  {fmt(reported):>6}")
    print("    감가상각을 멈춘 만큼 중단영업의 손실이 작아 보인다.")
    print("    대신 그 자산은 아래 [4] 에서 순공정가치로 한 번에 떨어진다.")
    print()


def section_4():
    print("[4] 처분자산집단 측정 — 장부금액과 순공정가치 중 작은 금액 (문단 15)")
    impairment = max(0, CARRYING_AMOUNT - FAIR_VALUE_LESS_COSTS_TO_SELL)
    print(f"    분류 직전 장부금액                      {fmt(CARRYING_AMOUNT):>6}")
    print(f"    공정가치에서 처분부대원가를 뺀 금액            {fmt(FAIR_VALUE_LESS_COSTS_TO_SELL):>6}")
    print(f"    측정에 따른 손상차손                    {fmt(impairment):>6}")
    print(f"    재무상태표 매각예정 처분자산집단 금액          "
          f"{fmt(min(CARRYING_AMOUNT, FAIR_VALUE_LESS_COSTS_TO_SELL)):>6}")
    print()
    return impairment


def section_5(impairment):
    print("[5] 포괄손익계산서에 나가는 중단영업손익 — 단일금액으로 표시 (문단 33)")
    operating = SEGMENTS[DISCONTINUED]["20X2"][1]
    after_tax_operating = operating * (1 - TAX_RATE)
    after_tax_impairment = -impairment * (1 - TAX_RATE)
    total = after_tax_operating + after_tax_impairment
    print(f"    {'구분':<32}{'세전':>10}{'법인세효과':>12}{'세후':>10}")
    print(f"    {'중단영업의 영업손익':<32}{signed(operating):>10}"
          f"{signed(-operating * TAX_RATE):>12}{signed(after_tax_operating):>10}")
    print(f"    {'순공정가치 측정에 따른 손익':<32}{signed(-impairment):>10}"
          f"{signed(impairment * TAX_RATE):>12}{signed(after_tax_impairment):>10}")
    print(f"    {'중단영업손익 (단일금액)':<32}{'':>10}{'':>12}{signed(total):>10}")
    print("    본문에는 이 한 줄만 나가고, 위 두 갈래는 주석이나 본문에서 나누어 공시한다.")
    print()
    return total


def section_6():
    print("[6] 비교표시를 다시 쓴다 — 전기 숫자가 달라진다 (문단 34)")
    rows = []
    for year in YEARS:
        all_rev, all_op = totals(year, SEGMENTS.keys())
        cont_rev, cont_op = totals(year, [s for s in SEGMENTS if s != DISCONTINUED])
        rows.append((year, all_rev, all_op, cont_rev, cont_op))

    print(f"    {'':<8}{'전체 매출':>10}{'전체 영업익':>12}"
          f"{'계속영업 매출':>14}{'계속영업 영업익':>16}")
    for year, all_rev, all_op, cont_rev, cont_op in rows:
        print(f"    {year:<8}{fmt(all_rev):>10}{fmt(all_op):>12}"
              f"{fmt(cont_rev):>14}{fmt(cont_op):>16}")

    _, prev_rev, prev_op, prev_cont_rev, prev_cont_op = rows[0]
    _, curr_rev, curr_op, curr_cont_rev, curr_cont_op = rows[1]
    print()
    print(f"    {'':<22}{'재작성 전':>12}{'재작성 후 (계속영업)':>22}")
    print(f"    {'매출 성장률':<22}{growth(prev_rev, curr_rev):>11.1f}%"
          f"{growth(prev_cont_rev, curr_cont_rev):>21.1f}%")
    print(f"    {'영업이익률 (전기)':<22}{prev_op / prev_rev * 100:>11.1f}%"
          f"{prev_cont_op / prev_cont_rev * 100:>21.1f}%")
    print(f"    {'영업이익률 (당기)':<22}{curr_op / curr_rev * 100:>11.1f}%"
          f"{curr_cont_op / curr_cont_rev * 100:>21.1f}%")
    print("    같은 회사의 같은 두 해인데 성장률이 2.0% 와 10.0% 로 갈린다.")
    print("    숫자가 좋아진 것이 아니라 세는 범위가 바뀐 것이다.")
    print("    손익과 현금흐름만 다시 쓰고, 전기 재무상태표는 재분류·재작성하지 않는다 (문단 40).")
    print()
    return curr_cont_op


def section_7(continuing_operating, discontinued_profit):
    print("[7] 주당이익도 둘로 나뉜다 (문단 33)")
    continuing_after_tax = continuing_operating * (1 - TAX_RATE)
    net = continuing_after_tax + discontinued_profit
    print(f"    계속영업 세후손익                {signed(continuing_after_tax):>10}")
    print(f"    중단영업손익                    {signed(discontinued_profit):>10}")
    print(f"    당기순손익                      {signed(net):>10}")
    print(f"    계속영업 기본주당이익   {continuing_after_tax * 1000 / SHARES_OUTSTANDING:>10,.0f}원")
    print(f"    기본주당이익          {net * 1000 / SHARES_OUTSTANDING:>10,.0f}원")
    print("    두 해를 비교할 때는 같은 쪽끼리 본다. 계속영업 EPS 와 전체 EPS 를 섞지 않는다.")
    print()


def section_8():
    print("[8] 매각계획이 철회되면 전부 되돌린다 (문단 36)")
    print("    중단영업으로 표시했던 설비사업부의 영업성과를")
    print("    비교표시되는 모든 기간에 걸쳐 계속영업손익으로 다시 분류한다.")
    for year in YEARS:
        cont_rev, cont_op = totals(year, [s for s in SEGMENTS if s != DISCONTINUED])
        all_rev, all_op = totals(year, SEGMENTS.keys())
        print(f"    {year}  계속영업 매출 {fmt(cont_rev)} → {fmt(all_rev)}"
              f" · 계속영업 영업익 {fmt(cont_op)} → {fmt(all_op)}")
    print("    과거 기간이 재분류되었다는 사실도 주석에 적는다.")
    print("    [6] 에서 10.0% 였던 성장률은 다시 2.0% 가 된다.")
    print()


def main():
    print("중단영업 — 가상 회사 마바중공업 (단위: 백만원, 세율 22%)")
    print("K-IFRS 제1105호 문단 6~8·15·25·32·33·34·36·40")
    print()
    section_1()
    section_3()
    impairment = section_4()
    discontinued_profit = section_5(impairment)
    continuing_operating = section_6()
    section_7(continuing_operating, discontinued_profit)
    section_8()


if __name__ == "__main__":
    main()
