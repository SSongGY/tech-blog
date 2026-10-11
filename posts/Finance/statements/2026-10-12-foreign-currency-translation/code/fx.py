"""환율이 바뀔 때 외화 항목이 재무제표 어디로 움직이는지 가상 회사로 계산한다.

가나전자·다라물산은 기능통화가 원화인 회사다. 외화는 천 달러, 원화는 백만원,
환율은 원/달러로 적는다. 천 달러 × 환율 ÷ 1,000 = 백만원이다.
"""

USD_TO_KRW_MILLION = 1 / 1000


def krw(usd_thousand, rate):
    return usd_thousand * rate * USD_TO_KRW_MILLION


# 문단 16 의 구분 — 받거나 줄 화폐 수량이 정해져 있는가
ITEMS = [
    ("외화 매출채권", "화폐성", "받을 달러 수량이 정해져 있다"),
    ("외화 차입금", "화폐성", "갚을 달러 수량이 정해져 있다"),
    ("외화 예금", "화폐성", "달러 그 자체다"),
    ("외화 선급금", "비화폐성", "받을 것이 돈이 아니라 재화다"),
    ("수입 재고자산", "비화폐성", "팔아서 받을 돈이 정해져 있지 않다"),
    ("해외 구입 설비", "비화폐성", "쓰거나 팔아서 받을 돈이 정해져 있지 않다"),
]

RATE_AT_TRANSACTION = 1300
RATE_AT_YEAR_END = 1400

# 보고기간말 환율 경로 (0 은 거래일)
RATE_PATH = [1300, 1400, 1250, 1350]

# 해외 자회사: 기능통화 달러. (연도, 당기순이익 천 달러, 그해 거래일 환율, 기말 환율)
SUB_START_NET_ASSETS = 2000
SUB_START_RATE = 1300
SUB_YEARS = [("1년차", 200, 1350, 1400), ("2년차", 200, 1300, 1250)]


def print_classification():
    print("[1] 화폐성과 비화폐성 (문단 8·16)")
    for name, kind, reason in ITEMS:
        print(f"    {name:<10} {kind:<5} {reason}")
    print("    보고기간말 환산: 화폐성은 마감환율, 역사적원가 비화폐성은 거래일 환율 (문단 23)")
    print()


def print_two_companies():
    usd = 1000
    print("[2] 같은 날 같은 1,000 천 달러 — 하나는 매출채권, 하나는 선급금 (문단 21·23·28)")
    print(f"    거래일 환율 {RATE_AT_TRANSACTION:,} → 보고기간말 환율 {RATE_AT_YEAR_END:,}")
    print("    회사      항목          최초 인식   기말 장부금액   당기손익 외환차이")
    rows = [
        ("가나전자", "외화 매출채권", True),
        ("다라물산", "외화 선급금", False),
    ]
    for name, item, monetary in rows:
        first = krw(usd, RATE_AT_TRANSACTION)
        end = krw(usd, RATE_AT_YEAR_END if monetary else RATE_AT_TRANSACTION)
        print(f"    {name}  {item:<10} {first:>10,.0f}  {end:>12,.0f}  {end - first:>+14,.0f}")
    print("    같은 달러, 같은 환율 변동인데 선급금은 다시 환산하지 않는다")
    print()


def print_exposure():
    print("[3] 환율이 오르내린 3년 — 매출채권만 가진 회사와 같은 금액의 차입금도 가진 회사")
    print("    가나전자: 매출채권 1,000 + 차입금 1,000 (천 달러)  /  다라물산: 매출채권 1,000 만")
    print("    연도     기말 환율   가나 채권 차이  가나 차입금 차이  가나 순손익   다라 순손익")
    totals = [0.0, 0.0]
    for year in range(1, len(RATE_PATH)):
        before, after = RATE_PATH[year - 1], RATE_PATH[year]
        receivable = krw(1000, after) - krw(1000, before)
        # 부채는 환율이 오르면 갚을 원화가 늘어 손실이다
        borrowing = -(krw(1000, after) - krw(1000, before))
        gana = receivable + borrowing
        dara = receivable
        totals[0] += gana
        totals[1] += dara
        print(
            f"    {year}년차   {after:>8,}   {receivable:>+12,.0f}  {borrowing:>+14,.0f}"
            f"  {gana:>+10,.0f}  {dara:>+10,.0f}"
        )
    print(f"    3년 합계 외환손익: 가나전자 {totals[0]:+,.0f} / 다라물산 {totals[1]:+,.0f}")
    print("    다라물산의 외환손익이 해마다 영업과 무관하게 당기순이익을 움직인다")
    print()


def print_subsidiary():
    print("[4] 해외 자회사(기능통화 달러)를 원화로 표시 — 차이는 기타포괄손익으로 (문단 39·41)")
    print(f"    시작 순자산 {SUB_START_NET_ASSETS:,} 천 달러, 환율 {SUB_START_RATE:,}")
    print("    연도    순이익($)  거래일 환율  순이익(원화)  기말 순자산($)  기말 환율"
          "  환산 순자산  기초+순이익  환산차이(OCI)")
    net_assets_usd = SUB_START_NET_ASSETS
    carried = krw(SUB_START_NET_ASSETS, SUB_START_RATE)
    cumulative = 0.0
    for label, income_usd, income_rate, close_rate in SUB_YEARS:
        income_krw = krw(income_usd, income_rate)
        net_assets_usd += income_usd
        translated = krw(net_assets_usd, close_rate)
        expected = carried + income_krw
        diff = translated - expected
        cumulative += diff
        print(
            f"    {label}  {income_usd:>8,}  {income_rate:>10,}  {income_krw:>11,.0f}"
            f"  {net_assets_usd:>13,}  {close_rate:>9,}  {translated:>10,.0f}"
            f"  {expected:>10,.0f}  {diff:>+12,.0f}"
        )
        carried = translated
    print(f"    자본에 쌓인 해외사업환산차이 누계 {cumulative:+,.0f}")
    print("    순이익은 해마다 원화로 260~270 이고, 환율 효과는 순이익에 들어가지 않는다")
    print("    자회사를 처분하면 이 누계액이 당기손익으로 재분류된다 (문단 48)")


if __name__ == "__main__":
    print_classification()
    print_two_companies()
    print_exposure()
    print_subsidiary()
