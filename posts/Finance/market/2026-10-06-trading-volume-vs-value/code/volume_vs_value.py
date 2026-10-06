"""거래량과 거래대금 — 주가가 다른 두 종목을 무엇으로 비교해야 하는가.

가상 종목 가나전자(주가 2천 원대)와 다라물산(주가 20만 원대)의 하루 체결 내역으로
거래량·거래대금·회전율을 계산하고, 액면분할이 거래량만 튀게 만드는 모양과
상장규정의 거래량 요건이 왜 유동주식수 대비 비율로 정해지는지를 숫자로 본다.
"""
import platform
import sys
import unicodedata
from dataclasses import dataclass


@dataclass
class Stock:
    name: str
    listed_shares: int     # 상장주식수
    floating_shares: int   # 유동주식수 — 최대주주 등 묶인 물량을 뺀 수
    trades: list[tuple[str, int, int]]  # (체결 시각, 체결가, 체결 수량)

    @property
    def volume(self) -> int:
        return sum(quantity for _, _, quantity in self.trades)

    @property
    def value(self) -> int:
        # 거래대금은 체결마다 가격×수량을 더한 값이다. 종가×거래량이 아니다
        return sum(price * quantity for _, price, quantity in self.trades)

    @property
    def close(self) -> int:
        return self.trades[-1][1]


def pad(text: str, width: int, right: bool = False) -> str:
    # 한글은 화면에서 두 칸을 차지하므로 글자 수가 아니라 표시 폭으로 맞춘다
    shown = sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)
    space = " " * max(width - shown, 0)
    return space + text if right else text + space


def print_trades(stock: Stock) -> None:
    print(f"  {stock.name}")
    print(f"    {pad('시각', 8)}{pad('체결가', 10, True)}{pad('수량', 12, True)}"
          f"{pad('가격×수량', 18, True)}")
    for time, price, quantity in stock.trades:
        print(f"    {time:<8}{price:>10,}{quantity:>12,}{price * quantity:>18,}")
    print(f"    {pad('합계', 8)}{'':>10}{stock.volume:>12,}{stock.value:>18,}")
    vwap = stock.value / stock.volume
    close_times_volume = stock.close * stock.volume
    print(f"    거래량가중평균가(거래대금÷거래량) {vwap:,.2f}원 · 종가 {stock.close:,}원")
    print(f"    종가×거래량 {close_times_volume:,}원 — 거래대금과 "
          f"{close_times_volume - stock.value:+,}원 차이")
    print()


def compare(stocks: list[Stock]) -> None:
    rows = [
        ("상장주식수(주)", lambda s: f"{s.listed_shares:,}"),
        ("종가(원)", lambda s: f"{s.close:,}"),
        ("시가총액(억 원)", lambda s: f"{s.close * s.listed_shares / 1e8:,.0f}"),
        ("거래량(주)", lambda s: f"{s.volume:,}"),
        ("거래대금(억 원)", lambda s: f"{s.value / 1e8:,.1f}"),
        ("회전율(거래량÷상장주식수)", lambda s: f"{s.volume / s.listed_shares:.2%}"),
        ("거래대금÷시가총액", lambda s: f"{s.value / (s.close * s.listed_shares):.2%}"),
    ]
    print(f"  {pad('항목', 28)}" + "".join(f"{pad(s.name, 16, right=True)}" for s in stocks))
    for label, render in rows:
        print(f"  {pad(label, 28)}" + "".join(f"{render(s):>16}" for s in stocks))
    a, b = stocks
    print(f"  거래량 배수   {a.name}÷{b.name} = {a.volume / b.volume:.1f}배")
    print(f"  거래대금 배수 {a.name}÷{b.name} = {a.value / b.value:.2f}배")
    print()


def split_series() -> None:
    # 다라물산이 4일차에 1주를 10주로 나눈다. 하루하루 손바뀜한 돈의 크기는 비슷하다고 둔다
    days = [
        (1, 200_000, 20_000), (2, 202_000, 19_000), (3, 199_000, 21_000),
        (4, 20_100, 205_000), (5, 20_300, 198_000), (6, 20_000, 210_000),
    ]
    print(f"  {pad('일차', 6)}{pad('종가', 10, True)}{pad('거래량', 12, True)}"
          f"{pad('거래대금(억 원)', 18, True)}  비고")
    for day, close, volume in days:
        note = "1:10 액면분할 후 첫 거래일" if day == 4 else ""
        print(f"  {day:<6}{close:>10,}{volume:>12,}{close * volume / 1e8:>18,.1f}  {note}")
    print("  (일별 거래대금은 체결 내역 대신 종가×거래량으로 근사했다)")
    print()


def thin_trading_check() -> None:
    floating_shares = 8_000_000
    monthly_volumes = [120_000, 60_000, 45_000, 70_000, 50_000, 85_000]
    threshold = floating_shares // 100
    average = sum(monthly_volumes) / len(monthly_volumes)
    print(f"  마바산업 유동주식수 {floating_shares:,}주 → 1%는 {threshold:,}주")
    for month, volume in enumerate(monthly_volumes, start=1):
        print(f"    {month}월 거래량 {volume:>9,}주")
    print(f"  반기 월평균거래량 {average:,.0f}주 = 유동주식수의 "
          f"{average / floating_shares:.3%}")
    print("  → 1% 미만이다" if average < threshold else "  → 1% 이상이다")
    print()
    # 같은 회사가 1:10 분할을 했다면 거래량과 유동주식수가 같이 10배가 된다
    ratio_after = (average * 10) / (floating_shares * 10)
    print(f"  1:10 분할 뒤라면 {average * 10:,.0f}주 ÷ {floating_shares * 10:,}주 = "
          f"{ratio_after:.3%} — 비율은 그대로다")


def main() -> None:
    print(f"Python {platform.python_version()} · {sys.platform}")
    print()

    ganada = Stock("가나전자", 50_000_000, 30_000_000, [
        ("09:00", 2_010, 300_000), ("10:30", 2_035, 400_000),
        ("12:10", 2_000, 250_000), ("14:00", 1_985, 350_000),
        ("15:30", 1_990, 200_000),
    ])
    dara = Stock("다라물산", 2_000_000, 1_400_000, [
        ("09:00", 198_500, 5_000), ("10:30", 201_000, 4_000),
        ("12:10", 203_500, 3_000), ("14:00", 200_500, 5_000),
        ("15:30", 200_000, 3_000),
    ])

    print("[1] 하루 체결 내역 — 체결마다 가격×수량을 더한다")
    print_trades(ganada)
    print_trades(dara)

    print("[2] 두 종목 나란히 — 거래량과 거래대금이 다른 순서를 낸다")
    compare([ganada, dara])

    print("[3] 다라물산 1:10 액면분할 전후 6거래일")
    split_series()

    print("[4] 상장규정의 거래량 요건 — 유동주식수 대비 비율로 본다")
    thin_trading_check()


if __name__ == "__main__":
    main()
