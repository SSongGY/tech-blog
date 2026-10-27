"""정리매매 기간의 거래 조건이 가격과 손에 쥐는 돈에 무엇을 하는지 계산한다.

가나전자는 실재하지 않는 가상 회사이고, 종가 2,000원과 보유 수량 1,000주도
계산을 보이려고 정한 값이다. 실제 종목의 값이 아니다.

규정 근거(본문 참고 자료에 링크를 둔다)
  - 정리매매 기간: 매매거래일 기준 7일 (유가증권시장 상장규정 제9조,
    코스닥시장 상장규정 제23조)
  - 매매 방식: 가격제한폭 없이 09:00~15:30 매 30분 단일가매매
    (코스닥시장 업무규정 제23조, 거래소 상장폐지 공시 기재)
  - 호가가격단위: 2,000원 미만 1원 (한국거래소 호가가격단위표)
  - 증권거래세: 2026-01-01 이후 양도분 코스닥 0.20%
"""

from datetime import datetime, timedelta
from decimal import Decimal

CLOSE_BEFORE_HALT = Decimal("2000")  # 거래정지 직전 종가(가상)
SHARES = 1000                        # 보유 수량(가상)
SESSION_DAYS = 7                     # 정리매매 매매거래일 수
DAILY_LIMIT = Decimal("0.30")        # 정규장 가격제한폭 ±30%
TRANSACTION_TAX = Decimal("0.0020")  # 코스닥 증권거래세율(2026년)


def auction_times(start="09:00", end="15:30", step_minutes=30):
    """정규장 안에서 단일가 체결이 이뤄지는 시각을 나열한다."""
    base = datetime(2026, 1, 1)
    cur = base.replace(hour=int(start[:2]), minute=int(start[3:]))
    last = base.replace(hour=int(end[:2]), minute=int(end[3:]))
    out = []
    while cur <= last:
        out.append(cur.strftime("%H:%M"))
        cur += timedelta(minutes=step_minutes)
    return out


def print_environment():
    print("=" * 66)
    print("가나전자 — 상장폐지가 결정된 가상 회사")
    print("=" * 66)
    print(f"  거래정지 직전 종가   {CLOSE_BEFORE_HALT:>10,}원")
    print(f"  보유 수량           {SHARES:>10,}주")
    print(f"  평가금액            {CLOSE_BEFORE_HALT * SHARES:>10,}원")
    print(f"  정리매매 기간       {SESSION_DAYS:>10}매매거래일")
    print()


def show_auction_schedule():
    print("[1] 하루에 체결되는 횟수 — 30분 단일가매매")
    print("-" * 66)
    times = auction_times()
    for i in range(0, len(times), 7):
        print("  " + "  ".join(times[i:i + 7]))
    print(f"  → 하루 {len(times)}회 · {SESSION_DAYS}거래일이면 "
          f"{len(times) * SESSION_DAYS}회")
    print("  정규장은 09:00 시가단일가와 15:30 종가단일가를 빼면 그 사이가")
    print("  전부 접속매매다. 호가가 맞으면 그 자리에서 바로 체결된다.")
    print()


def show_price_limit_effect():
    """가격제한폭이 걸렸다고 가정했을 때 7거래일로 갈 수 있는 바닥."""
    print("[2] 가격제한폭이 있다면 7거래일로 어디까지 내려가는가 (가정)")
    print("-" * 66)
    print(f"  {'거래일':>6}  {'하한가':>12}  {'직전 종가 대비':>14}  {'누적':>10}")
    price = CLOSE_BEFORE_HALT
    for day in range(1, SESSION_DAYS + 1):
        price = price * (1 - DAILY_LIMIT)
        cum = price / CLOSE_BEFORE_HALT - 1
        print(f"  {day:>6}  {price:>11,.1f}원  {-DAILY_LIMIT:>13.1%}  "
              f"{cum:>9.2%}")
    print(f"  → 매일 하한가로 떨어져도 {SESSION_DAYS}거래일 뒤 "
          f"{price / CLOSE_BEFORE_HALT:.4%}가 남는다")
    print("  정리매매에는 이 제한이 없다. 첫날 한 번의 단일가로도 더 내려간다.")
    print()


def tick_size(price):
    """한국거래소 호가가격단위 — 2,000원 미만 구간만 쓴다."""
    return Decimal("1") if price < 2000 else Decimal("5")


def show_tick_ratio():
    print("[3] 가격이 내려갈수록 한 호가가 차지하는 비율")
    print("-" * 66)
    print(f"  {'주가':>10}  {'호가가격단위':>12}  {'한 호가의 비율':>14}")
    for price in [Decimal(p) for p in (1000, 500, 200, 100, 50, 20, 10, 5, 2, 1)]:
        tick = tick_size(price)
        print(f"  {price:>9,}원  {tick:>11,}원  {tick / price:>13.2%}")
    print("  → 1원 단위는 그대로인데 분모가 줄어 비율이 커진다.")
    print("  주가 1원에서는 한 호가 아래가 0원이라 더 내려갈 자리가 없다.")
    print()


def show_proceeds(avg_price):
    """정리매매로 전량 매도했을 때 손에 쥐는 돈."""
    gross = avg_price * SHARES
    tax = (gross * TRANSACTION_TAX).quantize(Decimal("1"))
    net = gross - tax
    before = CLOSE_BEFORE_HALT * SHARES
    return gross, tax, net, net / before


def show_exit_cases():
    print("[4] 정리매매로 전량 매도했을 때 손에 쥐는 돈")
    print("-" * 66)
    print(f"  {'평균 체결가':>12}  {'매도대금':>12}  {'증권거래세':>10}  "
          f"{'실수령':>12}  {'평가금액 대비':>12}")
    for avg in [Decimal(p) for p in (400, 200, 100, 50, 20, 5, 1)]:
        gross, tax, net, ratio = show_proceeds(avg)
        print(f"  {avg:>11,}원  {gross:>11,}원  {tax:>9,}원  "
              f"{net:>11,}원  {ratio:>11.2%}")
    print("  → 증권거래세는 이익이 아니라 매도대금에 붙는다. 손실이 나도 뗀다.")
    print()


def show_decision_table():
    """팔지 않고 상장폐지일을 넘겼을 때 남는 것."""
    print("[5] 정리매매 기간에 팔지 않으면")
    print("-" * 66)
    rows = [
        ("주식이 사라지는가", "아니다. 비상장 주식으로 그대로 남는다"),
        ("주주 지위", "유지된다. 의결권·잔여재산분배청구권은 그대로"),
        ("거래 가능한가", "장내에서는 불가. 장외에서 상대를 직접 찾아야 한다"),
        ("가격을 볼 수 있는가", "시세가 공표되지 않는다"),
        ("되살아날 수 있는가", "재상장은 별도 심사 절차이고 자동이 아니다"),
    ]
    for key, value in rows:
        print(f"  {key:<20} {value}")
    print()


if __name__ == "__main__":
    print_environment()
    show_auction_schedule()
    show_price_limit_effect()
    show_tick_ratio()
    show_exit_cases()
    show_decision_table()
