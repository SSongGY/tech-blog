"""전환사채와 신주인수권부사채를 부채요소와 자본요소로 나누는 계산.

가상 회사 가나전자가 발행한 전환사채를 K-IFRS 제1032호의 잔여법으로 나누고,
부채요소에 유효이자율법을 적용한 상각표를 만든다. 같은 금액을 일반사채·유상증자로
조달했을 때와 재무상태표를 비교하고, 전환권 행사와 만기 상환이 갈리는 지점,
그리고 신주인수권부사채가 전환사채와 달라지는 지점을 계산한다.

금액 단위는 억원, 전환가액과 주식 수는 원과 주다. 파이썬 표준 라이브러리만 쓴다.
"""

FACE = 1_000.0          # 액면총액 (억원)
COUPON_RATE = 0.02      # 표면이자율 — 전환권이 붙은 덕에 낮게 발행된다
MARKET_RATE = 0.08      # 전환권 없는 같은 조건 일반사채의 시장이자율
YEARS = 3
ISSUE_PRICE = 1_000.0   # 발행가액 (액면발행)

CONVERSION_PRICE = 20_000  # 전환가액·행사가액 (원/주)


def cash_flows(face, coupon_rate, years):
    """사채가 앞으로 내보낼 현금흐름. 마지막 해에 원금이 함께 나간다."""
    coupon = face * coupon_rate
    return [coupon] * (years - 1) + [coupon + face]


def present_value(flows, rate):
    return sum(cf / (1 + rate) ** (t + 1) for t, cf in enumerate(flows))


def split_components(issue_price, face, coupon_rate, market_rate, years):
    """잔여법 — 부채요소를 먼저 공정가치로 재고, 남은 금액을 자본요소로 본다."""
    flows = cash_flows(face, coupon_rate, years)
    liability = present_value(flows, market_rate)
    equity = issue_price - liability
    return liability, equity, flows


def amortisation_table(opening, face, coupon_rate, market_rate, years):
    rows = []
    coupon = face * coupon_rate
    book = opening
    for year in range(1, years + 1):
        interest = book * market_rate
        amort = interest - coupon
        closing = book + amort
        rows.append((year, book, interest, coupon, amort, closing))
        book = closing
    return rows


def debt_ratio(debt, equity):
    return debt / equity * 100


def section_1():
    liability, equity, flows = split_components(
        ISSUE_PRICE, FACE, COUPON_RATE, MARKET_RATE, YEARS
    )
    print("[1] 발행 — 부채요소를 먼저 재고 남은 금액을 자본요소로 본다 (잔여법)")
    print(f"    가나전자 전환사채: 액면 {FACE:,.0f}, 표면이자율 {COUPON_RATE:.0%}, "
          f"{YEARS}년 만기, 액면발행")
    print(f"    전환권 없는 같은 조건 일반사채의 시장이자율: {MARKET_RATE:.0%}")
    print(f"    현금흐름: " + ", ".join(f"{cf:,.0f}" for cf in flows))
    print()
    print(f"    {'구분':<14}{'금액':>12}{'계산':>14}")
    print(f"    {'발행가액':<14}{ISSUE_PRICE:>12,.1f}{'받은 돈':>16}")
    print(f"    {'부채요소':<14}{liability:>12,.1f}{'현금흐름을 8%로 할인':>22}")
    print(f"    {'자본요소':<14}{equity:>12,.1f}{'발행가액 - 부채요소':>22}")
    print(f"    자본요소 {equity:,.1f}은 발행 시점에 자본으로 들어가고 "
          f"그 뒤 다시 재측정하지 않는다")
    print()
    return liability, equity


def section_2(liability):
    rows = amortisation_table(liability, FACE, COUPON_RATE, MARKET_RATE, YEARS)
    coupon = FACE * COUPON_RATE
    print("[2] 부채요소의 상각표 — 표면이자는 2%인데 이자비용은 8%로 쌓인다")
    print(f"    최초 장부금액 {liability:,.1f}, 유효이자율 {MARKET_RATE:.4%}")
    print(f"    {'연도':<8}{'기초 장부':>12}{'이자비용':>12}{'표면이자':>12}"
          f"{'상각액':>12}{'기말 장부':>12}")
    for year, book, interest, cpn, amort, closing in rows:
        print(f"    {year}년차{'':<4}{book:>12,.1f}{interest:>12,.1f}{cpn:>12,.1f}"
              f"{amort:>+12,.1f}{closing:>12,.1f}")
    total_interest = sum(r[2] for r in rows)
    total_coupon = coupon * YEARS
    print(f"    이자비용 합계 {total_interest:,.1f} = 표면이자 합계 {total_coupon:,.1f} "
          f"+ 액면과 부채요소의 차이 {FACE - liability:,.1f}")
    print(f"    현금으로 나가는 이자는 해마다 {coupon:,.1f}뿐이고 나머지는 부채를 "
          f"액면 쪽으로 올린다")
    print()
    return rows


def section_3(liability, equity):
    """같은 1,000을 세 가지로 조달했을 때 재무상태표와 3년 이자비용."""
    other_debt = 800.0
    base_equity = 1_200.0
    coupon = FACE * COUPON_RATE

    cb_interest = sum(
        r[2] for r in amortisation_table(liability, FACE, COUPON_RATE, MARKET_RATE, YEARS)
    )
    plain_interest = FACE * MARKET_RATE * YEARS

    print("[3] 같은 1,000을 조달하는 세 가지 — 부채비율과 3년 이자비용")
    print(f"    발행 직전: 부채 {other_debt:,.0f}, 자본 {base_equity:,.0f}, "
          f"부채비율 {debt_ratio(other_debt, base_equity):.1f}%")
    print()
    print(f"    {'조달 방법':<22}{'부채 증가':>12}{'자본 증가':>12}"
          f"{'부채비율':>12}{'3년 이자비용':>14}")
    rows = [
        ("일반사채 (표면 8%)", FACE, 0.0, plain_interest),
        ("전환사채 (표면 2%)", liability, equity, cb_interest),
        ("유상증자", 0.0, FACE, 0.0),
    ]
    for name, d, e, interest in rows:
        ratio = debt_ratio(other_debt + d, base_equity + e)
        print(f"    {name:<22}{d:>12,.1f}{e:>12,.1f}{ratio:>11.1f}%{interest:>14,.1f}")
    wrong_ratio = debt_ratio(other_debt + FACE, base_equity)
    print(f"    전환사채를 나누지 않고 전액 부채로 보면 부채비율 {wrong_ratio:.1f}% — "
          f"{wrong_ratio - debt_ratio(other_debt + liability, base_equity + equity):.1f}%포인트 차이")
    print()


def section_4(liability, rows):
    """만기 시점에 전환하는 경우와 현금으로 갚는 경우."""
    equity = ISSUE_PRICE - liability
    book_at_maturity = rows[2][5]   # 3년차 말 부채요소 장부금액 = 액면
    coupon = FACE * COUPON_RATE
    shares = int(FACE * 100_000_000 / CONVERSION_PRICE)

    print("[4] 만기 시점에 갈린다 — 주식으로 줄 때와 현금으로 갚을 때")
    print(f"    3년차 말 부채요소 장부금액 {book_at_maturity:,.1f} "
          f"(상각이 끝나 액면과 같아졌다), 자본요소 {equity:,.1f}")
    print(f"    3년차 표면이자 {coupon:,.1f}은 어느 쪽이든 현금으로 나간다 — "
          f"갈리는 것은 액면 {FACE:,.0f}의 처리다")
    print()
    print(f"    전환 — 전환가액 {CONVERSION_PRICE:,}원, 액면총액 {FACE:,.0f}억원 "
          f"→ 신주 {shares:,}주")
    print(f"      부채 {book_at_maturity:,.1f} 제거 → 같은 금액이 자본으로 간다")
    print(f"      발행 때 들어간 자본요소 {equity:,.1f}과 합치면 "
          f"자본에 {book_at_maturity + equity:,.1f}이 남는다")
    print(f"      액면만큼의 현금은 오가지 않고, 전환으로 인식할 손익도 없다")
    print()
    print(f"    상환 — 전환하지 않고 만기를 맞으면")
    print(f"      현금 {FACE:,.1f} 유출, 부채 {book_at_maturity:,.1f} 제거")
    print(f"      자본요소 {equity:,.1f}은 자본에 그대로 남는다 — "
          f"손익으로 돌리지 않는다")
    print()


def section_5(liability, rows):
    """전환사채와 신주인수권부사채가 권리 행사 뒤에 갈리는 지점."""
    equity = ISSUE_PRICE - liability
    book_at_2 = rows[1][5]
    other_debt = 800.0
    base_equity = 1_200.0
    exercise_cash = FACE          # 행사가액 = 전환가액, 신주인수 대금이 새로 들어온다
    shares = int(FACE * 100_000_000 / CONVERSION_PRICE)

    print("[5] 전환사채(CB)와 신주인수권부사채(BW) — 권리를 쓴 뒤에 사채가 남는가")
    print(f"    두 사채의 발행 조건은 같다. 2년차 말에 전량 권리 행사, "
          f"신주 {shares:,}주 발행")
    print(f"    행사 직전: 부채 {other_debt:,.0f} + 사채 {book_at_2:,.1f}, "
          f"자본 {base_equity:,.0f} + 자본요소 {equity:,.1f}")
    print()
    print(f"    {'':<10}{'현금 유입':>12}{'사채 부채':>12}{'자본 증가':>12}"
          f"{'부채':>10}{'자본':>10}{'부채비율':>11}")
    cb_debt = other_debt
    cb_equity = base_equity + book_at_2 + equity
    print(f"    {'CB':<10}{0.0:>12,.1f}{'소멸':>12}{book_at_2:>12,.1f}"
          f"{cb_debt:>10,.1f}{cb_equity:>10,.1f}{debt_ratio(cb_debt, cb_equity):>10.1f}%")
    bw_debt = other_debt + book_at_2
    bw_equity = base_equity + exercise_cash + equity
    print(f"    {'BW(분리형)':<10}{exercise_cash:>12,.1f}{book_at_2:>12,.1f}"
          f"{exercise_cash:>12,.1f}"
          f"{bw_debt:>10,.1f}{bw_equity:>10,.1f}{debt_ratio(bw_debt, bw_equity):>10.1f}%")
    print(f"    '자본 증가'는 행사로 새로 늘어난 금액이다 — "
          f"자본요소 {equity:,.1f}은 발행 때 이미 자본에 들어가 있다")
    print(f"    CB는 사채가 주식으로 바뀌어 사라지고, BW는 사채가 남은 채 "
          f"신주 대금 {exercise_cash:,.0f}이 따로 들어온다")
    print(f"    BW는 만기에 액면 {FACE:,.0f}을 갚아야 하고, "
          f"3년차 이자비용 {rows[2][2]:,.1f}도 그대로 발생한다")
    print()


def main():
    print("가나전자 전환사채 — 금액 단위는 억원, 전환가액은 원")
    print("=" * 78)
    print()
    liability, equity = section_1()
    rows = section_2(liability)
    section_3(liability, equity)
    section_4(liability, rows)
    section_5(liability, rows)


if __name__ == "__main__":
    main()
