"""국내 상장주식에 붙는 세 가지 세금이 세전 수익과 세후 수익을 얼마나 벌리는지 계산한다.

가나전자·다라물산은 실재하지 않는 가상 회사이고, 투자 금액과 수익률도
계산을 보이려고 정한 값이다. 실제 종목의 값이 아니다.

세율 근거 (본문 참고 자료에 링크를 둔다)
  - 증권거래세: 유가증권시장 0.05% · 코스닥/장외 0.20% · 코넥스 0.10%
    (증권거래세법 시행령 제5조, 2026-01-01 이후 양도분)
    유가증권시장에는 농어촌특별세 0.15%가 따로 붙어 합계 0.20%
  - 배당소득 원천징수 14% + 지방소득세 1.4% = 15.4% (소득세법 제129조)
  - 금융소득 2,000만원 초과분 종합과세, 비교과세 (소득세법 제14조·제62조)
  - 대주주 상장주식 양도: 과세표준 3억원 이하 20%,
    초과분은 6,000만원 + 초과액의 25%, 기본공제 연 250만원
    (소득세법 제104조 제1항 제11호, 제103조)
"""

from decimal import Decimal, ROUND_DOWN

MAN = Decimal("10000")        # 만원
EOK = Decimal("100000000")    # 억원

TRANSACTION_TAX = {           # 시장별 매도대금 대비 총 부담률
    "유가증권시장": Decimal("0.0005") + Decimal("0.0015"),  # 거래세 + 농특세
    "코스닥시장": Decimal("0.0020"),
    "코넥스시장": Decimal("0.0010"),
}
DIVIDEND_RATE = Decimal("0.14")          # 배당소득 원천징수세율
LOCAL_SURTAX = Decimal("0.10")           # 지방소득세 — 소득세액의 10%
FINANCIAL_THRESHOLD = Decimal("20000000")  # 금융소득 종합과세 기준금액
BASIC_DEDUCTION = Decimal("2500000")     # 양도소득 기본공제

# 종합소득세 누진세율 — (과세표준 상한, 세율)
BRACKETS = [
    (Decimal("14000000"), Decimal("0.06")),
    (Decimal("50000000"), Decimal("0.15")),
    (Decimal("88000000"), Decimal("0.24")),
    (Decimal("150000000"), Decimal("0.35")),
    (Decimal("300000000"), Decimal("0.38")),
    (Decimal("500000000"), Decimal("0.40")),
    (Decimal("1000000000"), Decimal("0.42")),
    (None, Decimal("0.45")),
]


def won(value):
    return value.quantize(Decimal("1"), rounding=ROUND_DOWN)


def progressive_tax(base):
    """종합소득 과세표준에 누진세율을 적용한 산출세액."""
    tax, lower = Decimal("0"), Decimal("0")
    for upper, rate in BRACKETS:
        if upper is None or base <= upper:
            return tax + (base - lower) * rate
        tax += (upper - lower) * rate
        lower = upper
    return tax


def print_environment():
    print("=" * 72)
    print("국내 상장주식에 붙는 세금 — 2026-10-27 기준 세율")
    print("=" * 72)
    for market, rate in TRANSACTION_TAX.items():
        print(f"  증권거래세 {market:<10} {rate:>8.2%}  (매도대금 기준)")
    print(f"  배당소득 원천징수           "
          f"{DIVIDEND_RATE * (1 + LOCAL_SURTAX):>8.2%}  (지방소득세 포함)")
    print(f"  금융소득 종합과세 기준     "
          f"{FINANCIAL_THRESHOLD / MAN:>8,.0f}만원")
    print()


def show_market_difference():
    print("[1] 같은 금액을 팔아도 시장에 따라 거래세가 다르다 — 매도대금 1,100만원")
    print("-" * 72)
    proceeds = Decimal("11000000")
    print(f"  {'시장':<12} {'부담률':>8} {'증권거래세':>12} {'실수령':>14}")
    for market, rate in TRANSACTION_TAX.items():
        tax = won(proceeds * rate)
        print(f"  {market:<12} {rate:>8.2%} {tax:>11,}원 {proceeds - tax:>13,}원")
    print("  → 2026-01-01 이후 양도분부터 유가증권시장과 코스닥시장의 합계 부담률이 같다.")
    print("     유가증권시장은 거래세 0.05% + 농어촌특별세 0.15%로 0.20%를 채운다.")
    print()


def show_income_type():
    """같은 세전 수익 100만원을 배당으로 받느냐 시세차익으로 받느냐."""
    print("[2] 같은 세전 수익 100만원, 받는 형태만 다르면 — 가나전자 1,000만원 투자")
    print("-" * 72)
    principal = Decimal("10000000")
    total_gain = Decimal("1000000")
    rate = TRANSACTION_TAX["유가증권시장"]
    print(f"  {'형태':<22} {'배당소득세':>11} {'증권거래세':>11} "
          f"{'세후 수익':>12} {'실효세율':>9}")
    cases = [
        ("시세차익 100%", Decimal("0")),
        ("배당 50% + 차익 50%", Decimal("500000")),
        ("배당 100%", Decimal("1000000")),
    ]
    for label, dividend in cases:
        capital_gain = total_gain - dividend
        proceeds = principal + capital_gain          # 매도대금
        div_tax = won(dividend * DIVIDEND_RATE * (1 + LOCAL_SURTAX))
        trade_tax = won(proceeds * rate)
        after = total_gain - div_tax - trade_tax
        print(f"  {label:<22} {div_tax:>10,}원 {trade_tax:>10,}원 "
              f"{after:>11,}원 {1 - after / total_gain:>8.2%}")
    print("  → 소액주주의 시세차익에는 양도소득세가 없다. 배당에는 원천징수가 먼저 붙는다.")
    print()


def show_turnover_drag():
    """같은 세전 연 수익률을 몇 번에 나눠 버느냐에 따른 10년 누적 차이."""
    print("[3] 세전 수익률이 같아도 매매 횟수가 다르면 — 연 10%, 10년")
    print("-" * 72)
    principal = Decimal("10000000")
    annual = Decimal("0.10")
    rate = TRANSACTION_TAX["유가증권시장"]
    years = 10
    print(f"  {'연 매매 횟수':>12} {'1회전 순배수':>14} {'10년 뒤 잔액':>16} "
          f"{'거래세 없을 때 대비':>18}")
    gross = principal * (1 + annual) ** years
    for n in (1, 4, 12, 52):
        step = (1 + annual / n) * (1 - rate)
        end = principal * step ** (n * years)
        print(f"  {n:>12} {step:>14.6f} {won(end):>15,}원 "
              f"{won(end - gross):>17,}원")
    print(f"  거래세가 없다면 10년 뒤 {won(gross):,}원")
    print("  → 거래세는 이익이 아니라 매도대금에 붙으므로 회전할 때마다 원금에서 깎인다.")
    print()


def comprehensive_tax(financial_income, other_base):
    """금융소득 종합과세의 비교과세 — 두 방식 중 큰 쪽이 산출세액이다."""
    if financial_income <= FINANCIAL_THRESHOLD:
        separate = financial_income * DIVIDEND_RATE
        return separate + progressive_tax(other_base), "분리과세(원천징수로 종결)"
    # ① 금융소득 전액에 원천징수세율
    plan_a = financial_income * DIVIDEND_RATE + progressive_tax(other_base)
    # ② 기준금액까지 원천징수세율, 초과분은 다른 소득과 합산
    excess = financial_income - FINANCIAL_THRESHOLD
    plan_b = (FINANCIAL_THRESHOLD * DIVIDEND_RATE
              + progressive_tax(other_base + excess))
    if plan_a >= plan_b:
        return plan_a, "비교과세 ① (전액 14%)"
    return plan_b, "비교과세 ② (초과분 합산)"


def show_threshold():
    print("[4] 금융소득 2,000만원 경계에서 무슨 일이 일어나는가")
    print("-" * 72)
    other_base = Decimal("50000000")   # 다른 종합소득 과세표준 5,000만원
    print(f"  다른 종합소득 과세표준 {other_base / MAN:,.0f}만원인 사람의 경우")
    print(f"  {'금융소득':>10} {'산출세액':>12} {'지방소득세 포함':>16} "
          f"{'적용 방식':<22}")
    for amount in (Decimal(a) for a in (10000000, 19000000, 20000000,
                                        21000000, 30000000, 50000000)):
        tax, how = comprehensive_tax(amount, other_base)
        total = tax * (1 + LOCAL_SURTAX)
        print(f"  {amount / MAN:>9,.0f}만 {won(tax):>11,}원 {won(total):>15,}원 "
              f"{how:<22}")
    print()
    print("  '2,000만원을 넘으면 전액이 누진세율로 합산된다'는 말과 비교하면")
    naive = progressive_tax(other_base + Decimal("21000000"))
    actual, _ = comprehensive_tax(Decimal("21000000"), other_base)
    print(f"    전액 합산이라고 보면   {won(naive):>12,}원")
    print(f"    실제 비교과세 결과     {won(actual):>12,}원")
    print(f"    차이                  {won(naive - actual):>12,}원")
    print("  → 기준금액까지는 14%가 보장되고 초과분만 다른 소득과 합쳐진다.")
    print()


def capital_gains_tax(gain):
    """대주주의 상장주식 양도소득세 — 기본공제 후 3억원 이하 20%, 초과 25%."""
    base = max(gain - BASIC_DEDUCTION, Decimal("0"))
    if base <= Decimal("300000000"):
        tax = base * Decimal("0.20")
    else:
        tax = Decimal("60000000") + (base - Decimal("300000000")) * Decimal("0.25")
    return base, tax


def show_capital_gains():
    print("[5] 대주주면 양도차익에도 세금이 붙는다 — 다라물산 주식")
    print("-" * 72)
    print(f"  {'양도차익':>10} {'과세표준':>14} {'양도소득세':>14} "
          f"{'지방소득세 포함':>16} {'차익 대비':>10}")
    for gain in (Decimal(g) for g in (50000000, 100000000, 300000000,
                                      500000000, 1000000000)):
        base, tax = capital_gains_tax(gain)
        total = tax * (1 + LOCAL_SURTAX)
        print(f"  {gain / EOK:>9,.2f}억 {won(base):>13,}원 {won(tax):>13,}원 "
              f"{won(total):>15,}원 {total / gain:>9.2%}")
    print("  소액주주가 장내에서 판 상장주식에는 이 세금이 없다.")
    print("  대주주 판정은 직전 사업연도 종료일 현재 보유분을 기준으로 한다.")
    print()


if __name__ == "__main__":
    print_environment()
    show_market_difference()
    show_income_type()
    show_turnover_drag()
    show_threshold()
    show_capital_gains()
