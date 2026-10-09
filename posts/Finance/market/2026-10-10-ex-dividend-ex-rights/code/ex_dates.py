"""배당락·권리락 — 기준일에서 마지막 매수일을 거꾸로 세고, 락일의 이론 가격을 계산한다.

회사 `마바식품`과 모든 숫자는 계산 원리를 보이려고 만든 가상 값이다.
"""
import datetime as dt

WEEKDAY_KO = "월화수목금토일"

# 예제 날짜에 걸리는 휴장일만 넣었다. 12월 31일은 거래소가 매매·결제를 하지 않는 날이다.
HOLIDAYS = {
    dt.date(2026, 12, 25): "성탄절",
    dt.date(2026, 12, 31): "연말 휴장",
    dt.date(2027, 1, 1): "신정",
}

SETTLEMENT_LAG = 2      # T+2 결제
DIVIDEND_TAX_RATE = 0.154   # 소득세 14% + 지방소득세 1.4%


def fmt(day):
    return f"{day.isoformat()}({WEEKDAY_KO[day.weekday()]})"


def is_trading_day(day):
    return day.weekday() < 5 and day not in HOLIDAYS


def next_trading_day(day):
    day += dt.timedelta(days=1)
    while not is_trading_day(day):
        day += dt.timedelta(days=1)
    return day


def prev_trading_day(day):
    day -= dt.timedelta(days=1)
    while not is_trading_day(day):
        day -= dt.timedelta(days=1)
    return day


def settlement_day(trade_day):
    day = trade_day
    for _ in range(SETTLEMENT_LAG):
        day = next_trading_day(day)
    return day


def last_cum_day(record_day):
    """기준일까지 결제가 끝나는 마지막 매매일. 기준일 당일이나 그 전에 결제돼야 주주명부에 오른다."""
    day = record_day if is_trading_day(record_day) else prev_trading_day(record_day)
    while settlement_day(day) > record_day:
        day = prev_trading_day(day)
    return day


def section_dates():
    print("[1] 기준일에서 거꾸로 센다 — T+2 결제, 주말·휴장일은 매매거래일에서 뺀다")
    print(f"  {'기준일':<18}{'마지막 매수일':<18}{'그 결제일':<18}{'락일':<18}{'락일에 산 주식의 결제일'}")
    cases = [dt.date(2026, 11, 16), dt.date(2026, 12, 31), dt.date(2027, 4, 15)]
    for record in cases:
        cum = last_cum_day(record)
        ex = next_trading_day(cum)
        print(f"  {fmt(record):<20}{fmt(cum):<20}{fmt(settlement_day(cum)):<20}"
              f"{fmt(ex):<20}{fmt(settlement_day(ex))}")
    print("  * 락일 = 마지막 매수일의 다음 매매거래일. 락일에 사면 결제가 기준일을 넘겨 권리가 없다")
    print("  * 12-31(목)은 휴장일이라 그 주에 결제가 일어나는 마지막 날은 12-30(수)이다")
    print()


def section_cash_dividend():
    close_before = 50_000
    print(f"[2] 마바식품 현금배당 — 락일 전 매매거래일 종가 {close_before:,}원")
    print(f"  {'주당배당금':>8}{'배당수익률':>10}{'이론 락일 가격':>14}{'전일 종가 대비':>14}")
    for dps in (500, 1_500, 2_500):
        ex_price = close_before - dps
        print(f"  {dps:>10,}{dps / close_before:>12.2%}{ex_price:>16,}"
              f"{(ex_price - close_before) / close_before:>15.2%}")
    print()

    dps = 2_500
    ex_price = close_before - dps
    tax = dps * DIVIDEND_TAX_RATE
    print(f"  마지막 매수일에 {close_before:,}원에 1주를 사서 락일 이론 가격 {ex_price:,}원에 판 경우 "
          f"(수수료·거래세 제외)")
    print(f"    매매 차손 {ex_price - close_before:+,}원 · 배당 {dps:,}원 → 세전 {ex_price - close_before + dps:+,}원")
    print(f"    배당소득 원천징수 {DIVIDEND_TAX_RATE:.1%} = {tax:,.0f}원 → 세후 "
          f"{ex_price - close_before + dps - tax:+,.0f}원")
    print()


def section_stock_dividend():
    close_before = 50_000
    ratio = 0.05
    holding = 100
    theo = close_before / (1 + ratio)
    print(f"[3] 마바식품 주식배당 — 1주당 {ratio}주, 락일 전 종가 {close_before:,}원")
    print(f"  이론 기준가격 = {close_before:,} / (1 + {ratio}) = {theo:,.2f}원")
    print(f"  주주 {holding}주 → {holding * (1 + ratio):.0f}주 · 평가액 "
          f"{holding * close_before:,}원 → {holding * (1 + ratio) * theo:,.0f}원")
    print()


def section_rights():
    close_before = 10_000
    ratio = 0.20
    issue_price = 7_150
    terp = (close_before + issue_price * ratio) / (1 + ratio)
    print(f"[4] 주주배정 유상증자 권리락 — 락일 전 종가 {close_before:,}원, 증자비율 {ratio:.0%}, "
          f"발행가 {issue_price:,}원")
    print(f"  이론 권리락 가격 = ({close_before:,} + {issue_price:,} × {ratio}) / (1 + {ratio}) = {terp:,.2f}원")
    print(f"  전일 종가 대비 {(terp - close_before) / close_before:.2%} · 신주 1주를 받을 권리의 이론값 "
          f"{terp - issue_price:,.2f}원")
    print()


def main():
    section_dates()
    section_cash_dividend()
    section_stock_dividend()
    section_rights()


if __name__ == "__main__":
    main()
