"""비율 분석이 틀리는 세 가지 경우 — 업종, 회계정책, 시점.

가상 회사 `한울산업`의 **같은 거래 집합**을 두고, 허용된 범위 안에서 회계정책을
바꾸거나 계산 시점을 바꾸면 비율이 어디까지 갈리는지 계산한다. 업종 착시는
비교 대상 `초록유통`을 세워 듀폰 분해로 본다.

근거가 되는 기준서 문단은 각 절 머리에 적어 둔다. 금액은 모두 억원이고,
실재하지 않는 회사의 가정값이다.
"""
import platform
import sys

# 한울산업의 1차연도 거래 — 아래 모든 계산이 이 한 벌에서 나온다
SALES = 2000.0            # 매출액: 100만개 x 20만원
PURCHASES = [             # 매입 (수량, 단가 원) — 매입 단가가 오르는 국면
    (500_000, 100_000),
    (500_000, 120_000),
    (500_000, 140_000),
]
UNITS_SOLD = 1_000_000
SGA_EXCL_DEP = 600.0      # 감가상각비를 뺀 판매관리비
EQUIPMENT_COST = 500.0    # 설비 취득원가
USEFUL_LIFE = 5           # 최초 추정 내용연수 (년)
DDB_RATE = 2 / USEFUL_LIFE  # 이중체감잔액법 상각률

OTHER_ASSETS = 1300.0     # 재고·설비를 뺀 나머지 자산 (현금 100 + 매출채권 300 + 기타 900)
EQUITY = 1100.0           # 자본
DEBT_EXCL_LEASE = 1100.0  # 리스를 뺀 부채

LEASE_PAYMENT = 100.0     # 연간 리스료
LEASE_YEARS = 4
LEASE_RATE = 0.05         # 리스이용자의 증분차입이자율 (가정)


def won_to_eok(amount_won: float) -> float:
    return amount_won / 100_000_000


def cogs_fifo() -> tuple[float, float]:
    """선입선출법 — 먼저 매입한 것이 먼저 팔린다고 본다 (제1002호 문단 27)."""
    remaining = UNITS_SOLD
    cost = 0.0
    for qty, price in PURCHASES:
        taken = min(remaining, qty)
        cost += taken * price
        remaining -= taken
    total = sum(q * p for q, p in PURCHASES)
    return won_to_eok(cost), won_to_eok(total - cost)


def cogs_weighted() -> tuple[float, float]:
    """가중평균법 — 기초재고와 당기 매입분의 원가를 가중평균한다 (제1002호 문단 27)."""
    total_qty = sum(q for q, _ in PURCHASES)
    total = sum(q * p for q, p in PURCHASES)
    unit = total / total_qty
    cost = unit * UNITS_SOLD
    return won_to_eok(cost), won_to_eok(total - cost)


def depreciation_straight() -> list[float]:
    """정액법 — 매 기간 일정액 (제1016호 문단 62)."""
    return [EQUIPMENT_COST / USEFUL_LIFE] * USEFUL_LIFE


def depreciation_declining() -> list[float]:
    """이중체감잔액법 — 상각액이 매 기간 줄어든다 (제1016호 문단 62).

    잔여 내용연수로 균등 배분한 금액이 더 커지는 해부터는 그쪽으로 바꾼다.
    바꾸지 않으면 내용연수가 끝나도 장부금액이 0 이 되지 않는다.
    """
    book = EQUIPMENT_COST
    schedule = []
    for year in range(USEFUL_LIFE):
        straight_rest = book / (USEFUL_LIFE - year)
        amount = max(book * DDB_RATE, straight_rest)
        schedule.append(amount)
        book -= amount
    return schedule


def annuity_pv(payment: float, years: int, rate: float) -> float:
    return sum(payment / (1 + rate) ** n for n in range(1, years + 1))


def print_header() -> None:
    print("[0] 이 글이 쓰는 한 벌의 거래 (한울산업 1차연도, 단위: 억원)")
    total_qty = sum(q for q, _ in PURCHASES)
    total_amt = won_to_eok(sum(q * p for q, p in PURCHASES))
    print(f"  매출액            {SALES:>8.0f}  ({UNITS_SOLD:,}개 x 20만원)")
    print(f"  매입액            {total_amt:>8.0f}  ({total_qty:,}개, 단가 10만 → 12만 → 14만원)")
    print(f"  판매수량          {UNITS_SOLD:>8,}개   기말 미판매 {total_qty - UNITS_SOLD:,}개")
    print(f"  판매관리비        {SGA_EXCL_DEP:>8.0f}  (감가상각비 제외)")
    print(f"  설비 취득원가     {EQUIPMENT_COST:>8.0f}  (내용연수 {USEFUL_LIFE}년, 잔존가치 0)")
    print(f"  자본 / 리스 외 부채 {EQUITY:>6.0f} / {DEBT_EXCL_LEASE:.0f}")
    print("  아래 [3]~[8] 은 전부 이 한 벌을 다르게 적은 것이다. 사업은 하나도 바뀌지 않는다")
    print()


def print_dupont() -> None:
    print("[1] 업종이 다를 때 — 듀폰 분해로 본 ROA (단위: 억원)")
    print("    ROA = 매출액순이익률 x 총자산회전율")
    rows = [
        ("한울산업(장치)", 2000.0, 240.0, 2400.0),
        ("초록유통(유통)", 8000.0, 240.0, 2400.0),
    ]
    print(f"  {'':16}{'매출액':>8}{'순이익':>8}{'총자산':>8}{'순이익률':>10}{'총자산회전율':>14}{'ROA':>9}")
    for name, sales, ni, assets in rows:
        margin = ni / sales
        turnover = sales / assets
        print(f"  {name:16}{sales:>8.0f}{ni:>8.0f}{assets:>8.0f}"
              f"{margin:>9.1%}{turnover:>13.3f}회{margin * turnover:>8.1%}")
    print("  순이익률은 4배 차이인데 ROA 는 같다. 마진만 떼어 보면 유통업은 늘 형편없어 보인다")
    print()


def print_current_ratio() -> None:
    print("[2] 업종이 다를 때 — 유동비율 (단위: 억원)")
    rows = [
        # 이름, 현금, 매출채권, 재고, 매입채무, 단기차입금
        ("한울산업(장치)", 100, 300, 400, 250, 150),
        ("초록유통(유통)", 200, 50, 450, 900, 100),
    ]
    print(f"  {'':16}{'현금':>6}{'매출채권':>9}{'재고':>7}{'유동자산':>9}"
          f"{'매입채무':>9}{'단기차입':>9}{'유동부채':>9}{'유동비율':>10}")
    for name, cash, ar, inv, ap, std in rows:
        ca = cash + ar + inv
        cl = ap + std
        print(f"  {name:16}{cash:>6}{ar:>8}{inv:>7}{ca:>8}{ap:>9}{std:>8}{cl:>8}{ca / cl:>10.1%}")
    print("  초록유통의 70% 는 현금으로 팔고 대금을 늦게 내는 구조에서 나온다. 같은 축에 세울 값이 아니다")
    print()


def print_inventory_policy() -> None:
    print("[3] 회계정책 ① 재고자산 원가결정방법 — 제1002호 문단 25·27 (단위: 억원)")
    print(f"  {'방법':14}{'매출원가':>10}{'기말재고':>10}{'매출총이익':>12}"
          f"{'매출총이익률':>14}{'재고회전율':>12}")
    results = {}
    for label, fn in (("선입선출법", cogs_fifo), ("가중평균법", cogs_weighted)):
        cogs, ending = fn()
        gross = SALES - cogs
        results[label] = (cogs, ending, gross)
        print(f"  {label:14}{cogs:>10.0f}{ending:>10.0f}{gross:>12.0f}"
              f"{gross / SALES:>13.1%}{SALES / ending:>11.2f}회")
    gap = results["선입선출법"][2] - results["가중평균법"][2]
    print(f"  매입 단가가 오르는 국면이라 선입선출법이 오래된 싼 원가를 먼저 털어낸다. 차이 {gap:.0f}억")
    print("  재고회전율은 한국은행 산식(매출액 ÷ 재고자산)을 쓴다")
    print()


def print_depreciation_policy() -> None:
    print("[4] 회계정책 ② 감가상각방법 5년 궤적 — 제1016호 문단 62 (단위: 억원)")
    straight = depreciation_straight()
    declining = depreciation_declining()
    print(f"  {'연차':8}{'정액법':>9}{'체감잔액법':>12}{'차이':>9}{'정액 장부금액':>15}{'체감 장부금액':>15}")
    book_s, book_d = EQUIPMENT_COST, EQUIPMENT_COST
    for year in range(USEFUL_LIFE):
        book_s -= straight[year]
        book_d -= declining[year]
        print(f"  {year + 1}년차{'':3}{straight[year]:>9.1f}{declining[year]:>12.1f}"
              f"{declining[year] - straight[year]:>+9.1f}{book_s:>14.1f}{book_d:>15.1f}")
    print(f"  5년 합계  {sum(straight):>9.1f}{sum(declining):>12.1f}      — 총액은 같고 배분만 다르다")
    print()


def print_policy_matrix() -> None:
    print("[5] 회계정책 ①x② 네 조합의 1차연도 — 거래는 하나다 (단위: 억원)")
    straight1 = depreciation_straight()[0]
    declining1 = depreciation_declining()[0]
    print(f"  {'재고':12}{'감가상각':12}{'매출총이익':>12}{'감가상각비':>12}{'영업이익':>10}"
          f"{'영업이익률':>12}{'총자산':>9}{'ROA(영업)':>12}")
    for inv_label, fn in (("선입선출", cogs_fifo), ("가중평균", cogs_weighted)):
        cogs, ending = fn()
        gross = SALES - cogs
        for dep_label, dep in (("정액", straight1), ("체감잔액", declining1)):
            op = gross - SGA_EXCL_DEP - dep
            assets = OTHER_ASSETS + ending + (EQUIPMENT_COST - dep)
            print(f"  {inv_label:12}{dep_label:12}{gross:>12.0f}{dep:>12.1f}{op:>10.1f}"
                  f"{op / SALES:>11.1%}{assets:>10.1f}{op / assets:>11.1%}")
    print("  영업이익률이 10.0% 에서 0.0% 까지 벌어진다. 네 줄 모두 기준서가 허용하는 적법한 작성이다")
    print("  가운데 두 줄은 5.0% 로 같지만 서로 다른 경로로 같아진 값이다")
    print()


def print_lease_policy() -> None:
    pv = annuity_pv(LEASE_PAYMENT, LEASE_YEARS, LEASE_RATE)
    print("[6] 회계정책 ③ 리스를 재무상태표에 올릴 때 — 제1116호 문단 22, 문단 5~8 (단위: 억원)")
    print(f"  연 리스료 {LEASE_PAYMENT:.0f}억 x {LEASE_YEARS}년, 할인율 {LEASE_RATE:.0%} "
          f"→ 리스부채 현재가치 {pv:.1f}")
    rows = [
        ("면제 선택 — 리스료를 비용으로만", 0.0),
        ("사용권자산·리스부채 인식", pv),
    ]
    straight1 = depreciation_straight()[0]
    cogs, ending = cogs_fifo()
    base_assets = OTHER_ASSETS + ending + (EQUIPMENT_COST - straight1)
    op = SALES - cogs - SGA_EXCL_DEP - straight1
    print(f"  {'':34}{'부채':>8}{'자본':>8}{'부채비율':>10}{'총자산':>9}{'ROA(영업)':>12}")
    for label, lease in rows:
        debt = DEBT_EXCL_LEASE + lease
        assets = base_assets + lease
        print(f"  {label:34}{debt:>8.1f}{EQUITY:>8.0f}{debt / EQUITY:>10.1%}"
              f"{assets:>9.1f}{op / assets:>11.1%}")
    print("  같은 점포를 같은 조건으로 빌리는데 부채비율이 32%p 갈린다. 2019년 이전 운용리스도 아래쪽이 아닌 위쪽이었다")
    print()


def print_timing_average() -> None:
    print("[7] 시점이 다를 때 ① 기말잔액과 평균잔액 — 재고에 계절성이 있는 경우 (단위: 억원)")
    monthly = [900, 950, 1000, 1050, 1000, 950, 900, 1000, 1100, 1000, 850, 700]
    labels = "1 2 3 4 5 6 7 8 9 10 11 12".split()
    print("  월별 재고잔액")
    print("  " + "".join(f"{m + '월':>7}" for m in labels))
    print("  " + "".join(f"{v:>7}" for v in monthly))
    year_end = monthly[-1]
    avg12 = sum(monthly) / len(monthly)
    avg2 = (monthly[-1] + 850) / 2  # 기초(전년 말)를 850 으로 가정한 기초·기말 평균
    print()
    print(f"  {'분모로 쓴 재고':24}{'금액':>8}{'재고회전율':>12}{'재고일수':>10}")
    for label, base in (("기말잔액", year_end), ("기초·기말 평균", avg2), ("12개월 평균", avg12)):
        turnover = SALES / base
        print(f"  {label:24}{base:>8.1f}{turnover:>11.2f}회{365 / turnover:>9.1f}일")
    print(f"  연말에 재고를 턴 회사라 기말잔액으로 재면 12개월 평균보다 회전이 "
          f"{SALES / year_end / (SALES / avg12) - 1:.1%} 빨라 보인다")
    print()


def print_timing_estimate() -> None:
    print("[8] 시점이 다를 때 ② 내용연수 재추정의 전진적용 — 제1008호 문단 36 (단위: 억원)")
    print(f"  3차연도 초에 잔여 내용연수를 3년에서 6년으로 다시 추정한다. 과거는 고치지 않는다")
    straight = depreciation_straight()
    book = EQUIPMENT_COST - straight[0] - straight[1]
    revised = book / 6
    cogs, _ = cogs_fifo()
    gross = SALES - cogs
    print(f"  {'연차':8}{'상각비':>9}{'영업이익':>10}{'영업이익률':>12}{'비고':>8}")
    for year, dep, note in (
        (1, straight[0], "최초 추정"),
        (2, straight[1], "최초 추정"),
        (3, revised, "재추정 후"),
        (4, revised, "재추정 후"),
    ):
        op = gross - SGA_EXCL_DEP - dep
        print(f"  {year}년차{'':3}{dep:>9.1f}{op:>10.1f}{op / SALES:>11.1%}  {note}")
    before = (gross - SGA_EXCL_DEP - straight[1]) / SALES
    after = (gross - SGA_EXCL_DEP - revised) / SALES
    print(f"  매출도 원가도 그대로인데 영업이익률이 {before:.1%} 에서 {after:.1%} 로 오른다")
    print("  추정치 변경은 전진적용이라 2차연도 수치는 그대로 남는다. 시계열만 보면 사업이 좋아진 것으로 읽힌다")
    print()


def main() -> None:
    print(f"Python {platform.python_version()} / {platform.system()}")
    print("회사: 한울산업·초록유통(모두 가상) / 모든 금액과 비율은 계산 원리를 보이려고 만든 값")
    print()
    print_header()
    print_dupont()
    print_current_ratio()
    print_inventory_policy()
    print_depreciation_policy()
    print_policy_matrix()
    print_lease_policy()
    print_timing_average()
    print_timing_estimate()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
