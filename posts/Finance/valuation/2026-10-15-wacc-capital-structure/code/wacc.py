"""WACC — 할인율이 만들어지는 과정과, 자본구조를 옮길 때 그것이 움직이는 방향.

가상 회사 `마바소재` 하나로 자기자본비용(CAPM)과 세후 타인자본비용을 각각
만들고 시가 기준으로 가중한다. 이어서 가중치를 장부가로 잡았을 때의 차이,
부채 비중을 0%에서 70%까지 옮겼을 때 WACC 가 그리는 모양, 법인세 절세효과가
빠졌을 때의 값, 그리고 그 차이가 현금흐름할인 결과를 얼마나 움직이는지를
계산한다. 파이썬 표준 라이브러리만 쓴다.
"""

# 가상 회사 마바소재. 전부 설명용 가정값이고 실재하는 기업과 관계가 없다.
RISK_FREE = 0.035          # 무위험이자율
EQUITY_RISK_PREMIUM = 0.06  # 시장위험프리미엄
UNLEVERED_BETA = 0.90      # 부채가 없다고 보았을 때의 베타
TAX_RATE = 0.22            # 평균유효세율 = 법인세비용 ÷ 회계이익

MARKET_EQUITY = 6_000      # 시가총액(억원)
DEBT = 2_000               # 이자부부채의 시가(억원). 장부가와 같다고 본다
BOOK_EQUITY = 2_500        # 자기자본 장부금액(억원)

# 부채 비중이 커질수록 붙는 신용스프레드(%p). 설명용 가정표다.
CREDIT_SPREAD = {
    0.0: 0.006, 0.1: 0.008, 0.2: 0.011, 0.3: 0.016,
    0.4: 0.024, 0.5: 0.036, 0.6: 0.055, 0.7: 0.085,
}

# 현금흐름할인에 쓸 가정 (단위: 억원)
FCF_YEAR1 = 100.0
FCF_GROWTH = 0.05
FORECAST_YEARS = 5
TERMINAL_GROWTH = 0.02


def shown_width(text: str) -> int:
    """한글은 터미널에서 두 칸을 차지하므로 글자 수와 표시 폭이 다르다."""
    return sum(2 if ord(ch) > 0x2E7F else 1 for ch in text)


def pad(text: str, width: int) -> str:
    """표시 폭 기준 왼쪽 정렬."""
    return text + " " * max(0, width - shown_width(text))


def rpad(text: str, width: int) -> str:
    """표시 폭 기준 오른쪽 정렬. 머리글을 아래 숫자 칸에 맞출 때 쓴다."""
    return " " * max(0, width - shown_width(text)) + text


def levered_beta(unlevered, tax, debt_to_equity):
    """하마다 식. 부채가 붙으면 주주가 지는 체계적 위험이 커진다."""
    return unlevered * (1 + (1 - tax) * debt_to_equity)


def cost_of_equity(beta):
    """자본자산가격결정모형(CAPM)."""
    return RISK_FREE + beta * EQUITY_RISK_PREMIUM


def spread_at(debt_ratio):
    """가정표를 선형보간해 그 부채 비중의 신용스프레드를 얻는다."""
    points = sorted(CREDIT_SPREAD)
    if debt_ratio <= points[0]:
        return CREDIT_SPREAD[points[0]]
    if debt_ratio >= points[-1]:
        return CREDIT_SPREAD[points[-1]]
    for low, high in zip(points, points[1:]):
        if low <= debt_ratio <= high:
            share = (debt_ratio - low) / (high - low)
            return CREDIT_SPREAD[low] + share * (CREDIT_SPREAD[high] - CREDIT_SPREAD[low])
    raise ValueError(debt_ratio)


def wacc_at(debt_ratio, tax=TAX_RATE):
    """부채 비중을 받아 베타·자기자본비용·타인자본비용·WACC 를 한 번에 만든다."""
    equity_ratio = 1 - debt_ratio
    d_over_e = debt_ratio / equity_ratio if equity_ratio else float("inf")
    beta = levered_beta(UNLEVERED_BETA, tax, d_over_e)
    ke = cost_of_equity(beta)
    kd = RISK_FREE + spread_at(debt_ratio)
    kd_after_tax = kd * (1 - tax)
    return {
        "debt_ratio": debt_ratio,
        "beta": beta,
        "ke": ke,
        "kd": kd,
        "kd_after_tax": kd_after_tax,
        "wacc": equity_ratio * ke + debt_ratio * kd_after_tax,
    }


def enterprise_value(rate):
    """예측 기간 현금흐름과 영구성장 잔존가치를 그 할인율로 현재가치화한다."""
    total = 0.0
    fcf = FCF_YEAR1
    for year in range(1, FORECAST_YEARS + 1):
        total += fcf / ((1 + rate) ** year)
        fcf *= 1 + FCF_GROWTH
    terminal_fcf = FCF_YEAR1 * ((1 + FCF_GROWTH) ** (FORECAST_YEARS - 1))
    terminal_fcf *= 1 + TERMINAL_GROWTH
    terminal = terminal_fcf / (rate - TERMINAL_GROWTH)
    return total + terminal / ((1 + rate) ** FORECAST_YEARS)


def main() -> None:
    value = MARKET_EQUITY + DEBT
    market_debt_ratio = DEBT / value

    print("[0] 산식")
    print("  자기자본비용 ke = 무위험이자율 + 베타 × 시장위험프리미엄   (CAPM)")
    print("  부채 반영 베타 = 무부채 베타 × [1 + (1 - 세율) × 부채/자기자본]  (하마다)")
    print("  타인자본비용 kd = 무위험이자율 + 신용스프레드")
    print("  WACC = (E/V) × ke + (D/V) × kd × (1 - 세율)")
    print("  평균유효세율 = 법인세비용 ÷ 회계이익")
    print()

    base = wacc_at(market_debt_ratio)
    print("[1] 마바소재 — 기준 WACC 를 만드는 과정 (시가 기준, 단위: 억원)")
    print(f"  시가총액 E {MARKET_EQUITY:,} · 부채 D {DEBT:,} · 합계 V {value:,}")
    print(f"  E/V {1 - market_debt_ratio:.1%} · D/V {market_debt_ratio:.1%} "
          f"· D/E {DEBT / MARKET_EQUITY:.4f}")
    print(f"  ① 부채 반영 베타 = {UNLEVERED_BETA} × "
          f"[1 + {1 - TAX_RATE:.2f} × {DEBT / MARKET_EQUITY:.4f}] = {base['beta']:.4f}")
    print(f"  ② ke = {RISK_FREE:.1%} + {base['beta']:.4f} × "
          f"{EQUITY_RISK_PREMIUM:.1%} = {base['ke']:.3%}")
    print(f"  ③ kd = {RISK_FREE:.1%} + {spread_at(market_debt_ratio):.3%} "
          f"= {base['kd']:.3%}  → 세후 {base['kd_after_tax']:.3%}")
    print(f"  ④ WACC = {1 - market_debt_ratio:.2f}×{base['ke']:.3%} + "
          f"{market_debt_ratio:.2f}×{base['kd_after_tax']:.3%} = {base['wacc']:.3%}")
    print()

    book_value = BOOK_EQUITY + DEBT
    book_debt_ratio = DEBT / book_value
    book_wacc = ((1 - book_debt_ratio) * base["ke"]
                 + book_debt_ratio * base["kd_after_tax"])
    print("[2] 가중치를 장부가로 잡으면 (ke·kd 는 그대로 두고 비중만 바꾼다)")
    print(f"  {pad('기준', 10)}{rpad('자기자본', 10)}{rpad('부채', 8)}"
          f"{rpad('D/V', 9)}{rpad('WACC', 10)}")
    print(f"  {pad('시가', 10)}{MARKET_EQUITY:>10,}{DEBT:>8,}"
          f"{market_debt_ratio:>9.1%}{base['wacc']:>10.3%}")
    print(f"  {pad('장부가', 10)}{BOOK_EQUITY:>10,}{DEBT:>8,}"
          f"{book_debt_ratio:>9.1%}{book_wacc:>10.3%}")
    print(f"  장부가 가중이 {(base['wacc'] - book_wacc) * 100:.2f}%p 낮다 — "
          f"싼 쪽(부채)의 비중이 커졌기 때문이다")
    print()

    print("[3] 부채 비중을 옮기면 (세율 "
          f"{TAX_RATE:.0%}, 무부채 베타 {UNLEVERED_BETA})")
    print(f"  {rpad('D/V', 6)}{rpad('D/E', 9)}{rpad('베타', 8)}{rpad('ke', 10)}"
          f"{rpad('kd', 9)}{rpad('세후 kd', 11)}{rpad('WACC', 10)}")
    rows = [wacc_at(r / 100) for r in range(0, 71, 10)]
    for row in rows:
        print(f"  {row['debt_ratio']:>6.0%}{row['debt_ratio'] / (1 - row['debt_ratio']):>9.4f}"
              f"{row['beta']:>8.3f}{row['ke']:>10.3%}{row['kd']:>9.2%}"
              f"{row['kd_after_tax']:>11.3%}{row['wacc']:>10.3%}")
    best = min(rows, key=lambda r: r["wacc"])
    worst = max(rows, key=lambda r: r["wacc"])
    print(f"  가장 낮은 칸 D/V {best['debt_ratio']:.0%} → WACC {best['wacc']:.3%}")
    print(f"  가장 높은 칸 D/V {worst['debt_ratio']:.0%} → WACC {worst['wacc']:.3%}")
    flat = [r for r in rows if r["wacc"] - best["wacc"] < 0.001]
    print(f"  최저값과 0.1%p 안에 드는 구간: "
          f"{', '.join(f'{r['debt_ratio']:.0%}' for r in flat)}")
    print()

    no_tax = wacc_at(market_debt_ratio, tax=0.0)
    print("[4] 법인세 절세효과를 빼면 (같은 자본구조에서 세율만 0 으로)")
    print(f"  세율 {TAX_RATE:.0%}  베타 {base['beta']:.4f}  "
          f"ke {base['ke']:.3%}  세후 kd {base['kd_after_tax']:.3%}  "
          f"WACC {base['wacc']:.3%}")
    print(f"  세율  0%  베타 {no_tax['beta']:.4f}  "
          f"ke {no_tax['ke']:.3%}  세후 kd {no_tax['kd_after_tax']:.3%}  "
          f"WACC {no_tax['wacc']:.3%}")
    print(f"  차이 {(no_tax['wacc'] - base['wacc']) * 100:.2f}%p — "
          f"이자비용이 과세소득을 줄여 주는 몫이다")
    print()

    print("[5] 할인율 차이가 기업가치에 미치는 영향 (1년차 FCF "
          f"{FCF_YEAR1:.0f}억, {FORECAST_YEARS}년간 연 {FCF_GROWTH:.0%} 성장,")
    print(f"     이후 영구성장 {TERMINAL_GROWTH:.0%}. 단위: 억원)")
    cases = [
        ("시가 가중 WACC", base["wacc"]),
        ("장부가 가중 WACC", book_wacc),
        ("절세효과를 뺀 WACC", no_tax["wacc"]),
        ("D/V 70% 로 갔을 때", rows[-1]["wacc"]),
    ]
    reference = enterprise_value(base["wacc"])
    print(f"  {pad('경우', 22)}{rpad('할인율', 9)}{rpad('기업가치', 12)}"
          f"{rpad('기준 대비', 12)}")
    for label, rate in cases:
        ev = enterprise_value(rate)
        print(f"  {pad(label, 22)}{rate:>9.3%}{ev:>12,.1f}"
              f"{(ev / reference - 1) * 100:>11.1f}%")


if __name__ == "__main__":
    main()
