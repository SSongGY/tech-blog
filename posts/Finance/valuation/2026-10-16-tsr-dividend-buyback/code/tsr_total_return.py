"""총주주수익률(TSR) — 배당과 자사주 매입·소각을 같은 자로 재는 예제.

여기 나오는 회사 `가나전자`·`다라물산`과 모든 숫자는 계산 원리를 보이려고 만든
가상 값이다. 실제 기업과 관계가 없다.

두 회사는 발행주식수·당기순이익·주주환원 총액이 전부 같고, 돌려주는 방식만 다르다.
가나전자는 전액을 현금배당으로, 다라물산은 전액을 자사주 매입·소각으로 돌려준다.
주가 차트만 나란히 놓으면 두 회사가 전혀 다르게 보이는데, TSR 로 재면 어떻게 되는지
숫자로 확인한다. 파이썬 표준 라이브러리만 쓴다.
"""

import sys

SHARES_0 = 10_000_000  # 기초 발행주식수
NET_INCOME = 20_000_000_000  # 매년 같은 당기순이익 (200억 원)
PER_BASE = 12.0  # 시장이 매기는 배수. [6] 전까지는 5년 내내 고정
PAYOUT = 10_000_000_000  # 매년 주주에게 돌려주는 총액 (100억 원)
YEARS = 5

# 배당소득 원천징수 14%(소득세법 제129조제1항제2호) + 지방소득세 1.4%(소득세의 10%)
DIV_TAX = 0.154


def won(x):
    return f"{x:>12,.0f}"


def pct(x):
    v = x * 100
    if v == 0:  # 부동소수점 잔차가 -0.00% 로 찍히는 것을 막는다
        v = 0.0
    return f"{v:>7.2f}%"


def flat_per():
    """5년 내내 같은 배수."""
    return [PER_BASE] * (YEARS + 1)


def drifting_per(end):
    """배수가 1년차부터 5년차까지 직선으로 움직이는 경로."""
    step = (end - PER_BASE) / YEARS
    return [PER_BASE + step * t for t in range(YEARS + 1)]


def path_dividend(per):
    """전액 현금배당. 발행주식수는 5년 내내 그대로다.

    매년 말 당기순이익이 쌓인 상태(배당락 전)에서 배당을 지급하고, 지급 직후
    시가총액은 그 해 배수 x 순이익이 된다고 둔다. 배당은 받는 즉시 같은 주식을
    배당락 후 주가로 다시 산다고 가정한다(재투자).
    """
    shares = SHARES_0
    price = per[0] * NET_INCOME / shares
    units = 1.0  # 1주로 시작해 배당 재투자로 늘어나는 보유 주식 수
    rows = []
    for t in range(1, YEARS + 1):
        prev = price
        cap_post = per[t] * NET_INCOME
        price_pre = (cap_post + PAYOUT) / shares  # 배당락 전 주가
        dps = PAYOUT / shares
        price = cap_post / shares  # 배당락 후 주가
        units *= 1 + dps / price
        rows.append(
            {
                "year": t,
                "shares": shares,
                "dps": dps,
                "price_pre": price_pre,
                "price": price,
                "cap_gain": price / prev - 1,
                "div_yield": dps / prev,
                "units": units,
                "value": units * price,
            }
        )
    return rows


def path_buyback(per, premium=0.0):
    """전액 자사주 매입·소각. 배당이 없는 대신 주식 수가 줄어든다.

    매입 단가는 배당락 전 주가에 해당하는 가격, 즉 그 해 이익이 아직 회사 안에
    남아 있는 상태의 주가로 둔다. 산 주식은 그 자리에서 소각한다.
    `premium` 은 그 가격보다 얼마나 비싸게(싸게) 샀는지다.
    """
    shares = SHARES_0
    price = per[0] * NET_INCOME / shares
    rows = []
    for t in range(1, YEARS + 1):
        prev = price
        cap_post = per[t] * NET_INCOME
        price_buy = (cap_post + PAYOUT) / shares * (1 + premium)  # 매입 단가
        bought = PAYOUT / price_buy
        shares -= bought
        price = cap_post / shares
        rows.append(
            {
                "year": t,
                "shares": shares,
                "bought": bought,
                "price_buy": price_buy,
                "price": price,
                "cap_gain": price / prev - 1,
                "div_yield": 0.0,
                "units": 1.0,
                "value": price,
            }
        )
    return rows


def cumulative(rows, per):
    """5년 누적 주가수익률과 누적 TSR."""
    start = per[0] * NET_INCOME / SHARES_0
    last = rows[-1]
    return {
        "start": start,
        "end_price": last["price"],
        "price_return": last["price"] / start - 1,
        "end_value": last["value"],
        "tsr": last["value"] / start - 1,
    }


def head(n, title):
    print(f"\n[{n}] {title}")
    print("-" * 72)


def main():
    per = flat_per()
    start = per[0] * NET_INCOME / SHARES_0

    head(1, "가상 회사 두 곳의 공통 설정")
    print(f"발행주식수        {SHARES_0:>14,} 주")
    print(f"당기순이익        {NET_INCOME:>14,} 원  (5년 내내 같다)")
    print(f"주당순이익(EPS)   {NET_INCOME / SHARES_0:>14,.0f} 원")
    print(f"적용 배수(PER)    {PER_BASE:>14,.1f} 배  ([6] 전까지 고정)")
    print(f"기초 주가         {start:>14,.0f} 원")
    print(f"매년 주주환원액   {PAYOUT:>14,} 원  (순이익의 {PAYOUT / NET_INCOME:.0%})")
    print()
    print("가나전자 : 환원액 전액을 현금배당으로 지급한다. 주식 수는 그대로다.")
    print("다라물산 : 환원액 전액으로 자사주를 사서 소각한다. 배당은 0 원이다.")

    div = path_dividend(per)
    buy = path_buyback(per)

    head(2, "가나전자 — 전액 배당")
    print("연차  발행주식수      주당배당금  배당락전주가  배당락후주가  주가수익률  배당수익률")
    for r in div:
        print(
            f"{r['year']:>3}   {r['shares']:>10,.0f}  {won(r['dps'])}  "
            f"{won(r['price_pre'])}  {won(r['price'])}  {pct(r['cap_gain'])}  {pct(r['div_yield'])}"
        )

    head(3, "다라물산 — 전액 자사주 매입·소각")
    print("연차  발행주식수      소각주식수    매입단가      기말주가      주가수익률  배당수익률")
    for r in buy:
        print(
            f"{r['year']:>3}   {r['shares']:>10,.0f}  {r['bought']:>12,.0f}  "
            f"{won(r['price_buy'])}  {won(r['price'])}  {pct(r['cap_gain'])}  {pct(r['div_yield'])}"
        )

    head(4, "5년 뒤 — 주가만 볼 때와 TSR 로 볼 때")
    cd, cb = cumulative(div, per), cumulative(buy, per)
    print("                      가나전자        다라물산")
    print(f"기초 주가          {won(cd['start'])}    {won(cb['start'])}")
    print(f"5년 뒤 주가        {won(cd['end_price'])}    {won(cb['end_price'])}")
    print(f"누적 주가수익률    {pct(cd['price_return'])}         {pct(cb['price_return'])}")
    print(f"5년 뒤 보유가치    {won(cd['end_value'])}    {won(cb['end_value'])}")
    print(f"누적 TSR           {pct(cd['tsr'])}         {pct(cb['tsr'])}")
    print()
    print(f"주가수익률 차이    {pct(cb['price_return'] - cd['price_return'])}")
    print(f"TSR 차이           {pct(cb['tsr'] - cd['tsr'])}")

    head(5, "단순합산 TSR 과 재투자 TSR — 가나전자")
    simple = sum(r["cap_gain"] + r["div_yield"] for r in div)
    geo = cd["tsr"]
    print("연차  주가수익률  배당수익률  단순합(연간)")
    for r in div:
        print(
            f"{r['year']:>3}   {pct(r['cap_gain'])}   {pct(r['div_yield'])}   "
            f"{pct(r['cap_gain'] + r['div_yield'])}"
        )
    print()
    print(f"5개 연도를 그냥 더한 값      {pct(simple)}")
    print(f"배당을 재투자한 누적 TSR     {pct(geo)}")
    print(f"차이                         {pct(geo - simple)}  (복리로 붙은 몫)")
    print(f"재투자 TSR 의 연환산         {pct((1 + geo) ** (1 / YEARS) - 1)}")

    head(6, "배수가 움직일 때 — 순이익과 환원액은 그대로 두고 PER 만 바꾼다")
    print("PER 경로        가나전자 TSR   다라물산 TSR    차이    다라물산 5년 소각비율")
    for end_per, label in ((9.0, "12 → 9 "), (12.0, "12 → 12"), (15.0, "12 → 15")):
        p = drifting_per(end_per)
        d, b = path_dividend(p), path_buyback(p)
        td, tb = cumulative(d, p)["tsr"], cumulative(b, p)["tsr"]
        burn = 1 - b[-1]["shares"] / SHARES_0
        print(
            f"{label}        {pct(td)}       {pct(tb)}   {pct(round(tb - td, 12))}"
            f"        {pct(burn)}"
        )
    print()
    print("세 줄 모두 두 회사의 TSR 이 소수점 아래까지 같다. 환원 방식은 TSR 을 바꾸지")
    print("못하고 주가수익률의 모양만 바꾼다. TSR 을 움직이는 것은 배수와 이익이다.")
    print("배수가 내려간 해에는 자사주를 싼값에 더 많이 사서 소각비율이 올라가지만,")
    print("싸진 만큼 기말 주가도 낮아져 둘이 정확히 상쇄된다.")

    head(7, "매입 단가가 흔들리면 — 등가가 깨지는 자리")
    print("이 등가는 '회사가 공정한 값에 산다'는 가정 위에 서 있다. 그 가정을 흔들어 본다.")
    print()
    print("매입 단가     다라물산 TSR   가나전자 대비    5년 소각비율")
    base_tsr = cd["tsr"]
    for prem, label in (
        (-0.20, "20% 싸게 "),
        (0.00, "공정가    "),
        (0.20, "20% 비싸게"),
        (0.40, "40% 비싸게"),
    ):
        rows = path_buyback(per, premium=prem)
        tb = cumulative(rows, per)["tsr"]
        burn = 1 - rows[-1]["shares"] / SHARES_0
        print(f"{label}    {pct(tb)}       {pct(tb - base_tsr)}       {pct(burn)}")
    print()
    print("배당은 받는 금액이 정해져 있어 이 줄이 생기지 않는다. 자사주만 '언제 샀는가'가")
    print("TSR 에 그대로 들어간다. 매입 공시를 볼 때 금액과 함께 단가를 보는 이유다.")

    head(8, "배당에 원천징수가 붙으면 — 재투자 금액이 줄어든다")
    shares, price, units_net = SHARES_0, start, 1.0
    for _ in range(YEARS):
        dps = PAYOUT / shares
        price = PER_BASE * NET_INCOME / shares
        units_net *= 1 + dps * (1 - DIV_TAX) / price
    net_tsr = units_net * price / start - 1
    print(f"세전 재투자 TSR              {pct(cd['tsr'])}")
    print(f"세후 재투자 TSR              {pct(net_tsr)}")
    print(f"차이                         {pct(net_tsr - cd['tsr'])}")
    print()
    print("자사주 매입·소각은 받는 현금이 없으므로 이 단계에서 떼이는 세금이 없다.")
    print("대신 과세가 주식을 파는 시점으로 미뤄진다. 사라지는 것이 아니다.")

    head(9, "주주환원율은 TSR 이 아니다")
    for name, rows in (("가나전자", div), ("다라물산", buy)):
        ret = PAYOUT / NET_INCOME
        tsr = cumulative(rows, per)["tsr"]
        print(f"{name}   주주환원율 {pct(ret)}   5년 누적 TSR {pct(tsr)}")
    print()
    p_down = drifting_per(9.0)
    print("같은 회사, 같은 환원율인데 배수만 12 → 9 로 내려간 경우:")
    for name, fn in (("가나전자", path_dividend), ("다라물산", path_buyback)):
        tsr = cumulative(fn(p_down), p_down)["tsr"]
        print(f"{name}   주주환원율 {pct(PAYOUT / NET_INCOME)}   5년 누적 TSR {pct(tsr)}")
    print()
    print("주주환원율은 회사가 이익을 얼마나 돌려줬는지를 재고,")
    print("TSR 은 주주가 받아 쥔 결과를 잰다. 분모도 분자도 다른 지표다.")

    print()
    print(f"python {sys.version.split()[0]}")


if __name__ == "__main__":
    main()
