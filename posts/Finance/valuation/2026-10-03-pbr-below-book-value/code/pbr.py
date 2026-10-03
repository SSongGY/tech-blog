"""PBR 과 청산가치 — 같은 PBR 0.5배가 서로 다른 것을 뜻할 수 있다.

순자산·주식수·주가가 모두 같은 가상 회사 둘을 놓고, 재무상태표 항목별로
청산 시 회수율(가정)을 적용해 청산가치를 계산한다. 이어서 PBR = PER × ROE 관계,
K-IFRS 제1036호 문단 12 의 손상 징후(순자산 장부금액 > 시가총액)와
제1002호 문단 9 의 재고자산 저가 측정이 장부가를 낮추면 PBR 이 어떻게 되는지 본다.
세금 효과는 계산을 단순하게 하려고 무시한다.
"""
import platform
import sys

SHARES = 10_000_000
PRICE = 5_000  # 두 회사 모두 같은 주가(원)
EOK = 100_000_000
LIQUIDATION_COST = 50  # 청산 부대비용(억원, 가정): 처분 수수료·퇴직급여 정산 등

# 항목: (장부금액 억원, 사아유통 회수율, 자차섬유 장부금액, 자차섬유 회수율)
# 회수율은 설명용 가정이다. 회계기준이 정한 값이 아니다
SAA = {
    "현금및현금성자산": (300, 1.00),
    "매출채권": (100, 0.90),
    "재고자산": (100, 0.70),
    "토지": (400, 1.00),
    "건물·설비": (300, 0.50),
}
JACHA = {
    "현금및현금성자산": (50, 1.00),
    "매출채권(장기 미회수 포함)": (300, 0.40),
    "재고자산(유행 지난 원단)": (350, 0.20),
    "전용 생산설비": (500, 0.15),
}
LIABILITIES = 200  # 두 회사 모두 같다


def per_share(eok: float) -> float:
    return eok * EOK / SHARES


def book_equity(assets: dict) -> float:
    return sum(book for book, _ in assets.values()) - LIABILITIES


def liquidation_value(assets: dict) -> float:
    # 부채는 장부금액 그대로 갚아야 하므로 회수율을 적용하지 않는다
    recovered = sum(book * rate for book, rate in assets.values())
    return recovered - LIABILITIES - LIQUIDATION_COST


def print_definitions() -> None:
    print("[0] 산식")
    print("  PBR = 주가 ÷ 주당순자산(BPS) = 시가총액 ÷ 자본총계")
    print("  BPS = 자본총계 ÷ 발행주식수")
    print("  청산가치 = Σ(자산 장부금액 × 회수율) − 부채 − 청산 부대비용   (회수율은 가정값)")
    print()


def print_two_companies() -> None:
    print(f"[1] 주가 {PRICE:,}원, 주식 {SHARES:,}주, 부채 {LIABILITIES}억으로 같은 두 회사 (단위: 억원)")
    for name, assets in (("사아유통", SAA), ("자차섬유", JACHA)):
        print(f"  {name}")
        print(f"    {'항목':24}{'장부':>6}{'회수율':>8}{'회수액':>8}")
        for item, (book, rate) in assets.items():
            print(f"    {item:24}{book:>6}{rate:>8.0%}{book * rate:>8.0f}")
        equity = book_equity(assets)
        liq = liquidation_value(assets)
        print(f"    자본총계(장부) {equity:,.0f}억  BPS {per_share(equity):,.0f}원  PBR {PRICE / per_share(equity):.2f}배")
        print(f"    청산가치       {liq:,.0f}억  주당 {per_share(liq):,.0f}원  주가 ÷ 주당 청산가치 {PRICE / per_share(liq):.2f}배")
    print()


def print_per_roe() -> None:
    print("[2] PBR = PER × ROE  (주가/BPS = 주가/EPS × EPS/BPS)")
    equity = book_equity(SAA)
    net_income = 20  # 사아유통 당기순이익(억원, 가정)
    roe = net_income / equity
    per = PRICE / per_share(net_income)
    print(f"  사아유통: 순이익 {net_income}억, ROE {roe:.1%}, PER {per:.1f}배 → PBR {per * roe:.2f}배")
    print("  자차섬유: 당기순손실 80억(가정) → EPS 가 음수라 PER 이 정의되지 않는다. PBR 은 여전히 0.50배로 계산된다")
    print()
    print("  PER 10배로 고정하고 ROE 만 바꾸면")
    print(f"  {'ROE':>6}{'PBR':>8}")
    for r in (0.02, 0.05, 0.10, 0.15):
        print(f"  {r:>6.0%}{10 * r:>7.2f}배")
    print("  PER 이 같을 때 PBR 이 1배 아래면 ROE 가 이익수익률(E/P = 1/PER)보다 낮다는 뜻이다")
    print()


def print_impairment() -> None:
    print("[3] 자차섬유가 기준서대로 장부가를 낮추면 (주가는 그대로, 세금 효과 무시)")
    equity = book_equity(JACHA)
    market_cap = PRICE * SHARES / EOK
    print(f"  시가총액 {market_cap:,.0f}억 < 순자산 장부금액 {equity:,.0f}억 → K-IFRS 1036 문단 12 의 손상 징후")
    steps = [
        ("손상 전", 0),
        ("생산설비 손상차손 300억 (회수가능액 200억, 가정)", 300),
        ("재고자산 평가손실 200억 (순실현가능가치 150억, 가정)", 200),
    ]
    print(f"  {'단계':44}{'자본':>6}{'BPS(원)':>10}{'PBR':>8}")
    for label, loss in steps:
        equity -= loss
        print(f"  {label:44}{equity:>6,.0f}{per_share(equity):>10,.0f}{PRICE / per_share(equity):>7.2f}배")
    print("  주가가 움직이지 않았는데 PBR 이 0.50배에서 1.00배가 된다. 할인은 장부가 쪽에 있었다")
    print()


def main() -> None:
    print(f"Python {platform.python_version()} / {platform.system()}")
    print("회사: 사아유통·자차섬유(모두 가상) / 회수율·손상 금액은 설명용 가정값")
    print()
    print_definitions()
    print_two_companies()
    print_per_roe()
    print_impairment()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
