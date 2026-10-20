"""지수 구성종목이 바뀔 때 패시브 자금이 기계적으로 움직이는 금액을 계산한다.

가상 지수 '한빛100'은 유동주식수로 가중한 시가총액 지수다. 정기변경으로 한 종목이
빠지고 한 종목이 들어오면, 지수를 그대로 복제하는 펀드는 세 묶음을 동시에 조정한다.
제외 종목을 전량 팔고, 편입 종목을 새로 사고, 남는 98종목은 분모가 커진 만큼
비중이 줄어 조금씩 판다. 세 금액이 서로 맞아떨어지는지까지 검산한다.
"""

# 지수를 복제하는 펀드·ETF 자금의 합계 (가정)
PASSIVE_ASSETS = 4_000_000_000_000  # 4조 원
# 변경 전 지수 전체의 유동주식 시가총액 (가정)
FLOAT_CAP_BEFORE = 320_000_000_000_000  # 320조 원


class Stock:
    def __init__(self, name, shares, price, fif, daily_value):
        self.name = name
        self.shares = shares          # 상장주식수
        self.price = price            # 주가
        self.fif = fif                # 유동주식비율
        self.daily_value = daily_value  # 일평균거래대금

    @property
    def market_cap(self):
        return self.shares * self.price

    @property
    def float_cap(self):
        return round(self.market_cap * self.fif)


def won(amount):
    """조·억 단위로 끊어 읽는다."""
    amount = round(amount)
    sign = "-" if amount < 0 else ""
    jo, rest = divmod(abs(amount), 1_000_000_000_000)
    eok = rest / 100_000_000
    if jo and eok:
        return f"{sign}{jo:,}조 {eok:,.2f}억"
    if jo:
        return f"{sign}{jo:,}조"
    return f"{sign}{eok:,.2f}억"


incoming = Stock("사람반도체", 40_000_000, 32_000, 0.60, 3_000_000_000)
outgoing = Stock("다인바이오", 20_000_000, 18_000, 0.45, 1_200_000_000)

print("=" * 68)
print("1. 편입·제외 종목의 유동주식 시가총액")
print("=" * 68)
print(f"  {'종목':<10}{'상장주식수':>14}{'주가':>10}{'시가총액':>18}{'유동비율':>9}{'유동시총':>18}")
for s in (incoming, outgoing):
    print(
        f"  {s.name:<10}{s.shares:>14,}{s.price:>10,}{won(s.market_cap):>18}"
        f"{s.fif * 100:>8.0f}%{won(s.float_cap):>18}"
    )
print()

# 변경 전 분모에는 제외 종목이 들어 있고 편입 종목은 빠져 있다.
others = FLOAT_CAP_BEFORE - outgoing.float_cap
float_cap_after = others + incoming.float_cap

print("=" * 68)
print("2. 지수 전체 유동시총(분모)의 변화")
print("=" * 68)
print(f"  변경 전              {won(FLOAT_CAP_BEFORE):>22}")
print(f"  - 다인바이오 제외      {won(-outgoing.float_cap):>22}")
print(f"  + 사람반도체 편입      {won(incoming.float_cap):>22}")
print(f"  변경 후              {won(float_cap_after):>22}")
print(f"  분모 증가율          {(float_cap_after / FLOAT_CAP_BEFORE - 1) * 100:>21.4f}%")
print()

buy_incoming = PASSIVE_ASSETS * incoming.float_cap / float_cap_after
sell_outgoing = PASSIVE_ASSETS * outgoing.float_cap / FLOAT_CAP_BEFORE
others_before = PASSIVE_ASSETS * others / FLOAT_CAP_BEFORE
others_after = PASSIVE_ASSETS * others / float_cap_after
sell_others = others_before - others_after

print("=" * 68)
print("3. 패시브 자금이 움직여야 하는 금액")
print("=" * 68)
print(f"  {'묶음':<22}{'변경 전':>16}{'변경 후':>16}{'매매':>16}")
print(f"  {'사람반도체 (편입)':<22}{won(0):>16}{won(buy_incoming):>16}{'+' + won(buy_incoming):>16}")
print(f"  {'다인바이오 (제외)':<22}{won(sell_outgoing):>16}{won(0):>16}{'-' + won(sell_outgoing):>16}")
print(f"  {'나머지 98종목':<22}{won(others_before):>16}{won(others_after):>16}{'-' + won(sell_others):>16}")
print()
print(f"  검산: 제외 매도 + 나머지 희석 매도 = {won(sell_outgoing + sell_others)}")
print(f"        편입 매수                  = {won(buy_incoming)}")
print(f"        차이                      = {sell_outgoing + sell_others - buy_incoming:,.6f}원")
print()

print("=" * 68)
print("4. 그 금액은 평소 거래대금의 며칠치인가")
print("=" * 68)
print(f"  {'종목':<12}{'기계적 매매':>16}{'일평균거래대금':>16}{'며칠치':>10}")
print(f"  {incoming.name:<12}{won(buy_incoming):>16}{won(incoming.daily_value):>16}"
      f"{buy_incoming / incoming.daily_value:>9.2f}일")
print(f"  {outgoing.name:<12}{won(sell_outgoing):>16}{won(outgoing.daily_value):>16}"
      f"{sell_outgoing / outgoing.daily_value:>9.2f}일")
print()

print("=" * 68)
print("5. 같은 시가총액이라도 유동주식비율이 다르면")
print("=" * 68)
print(f"  {'유동비율':>9}{'유동시총':>18}{'지수 비중':>12}{'패시브 매수':>16}{'거래대금 대비':>14}")
for fif in (0.30, 0.45, 0.60, 0.75, 0.90):
    probe = Stock(incoming.name, incoming.shares, incoming.price, fif, incoming.daily_value)
    denominator = others + probe.float_cap
    weight = probe.float_cap / denominator
    buy = PASSIVE_ASSETS * weight
    print(f"  {fif * 100:>8.0f}%{won(probe.float_cap):>18}{weight * 100:>11.4f}%"
          f"{won(buy):>16}{buy / probe.daily_value:>13.2f}일")
