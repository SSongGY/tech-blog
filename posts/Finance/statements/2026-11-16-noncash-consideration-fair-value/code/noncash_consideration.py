"""비현금 대가 — 기업회계기준서 제1115호 문단 66~69.

가상 회사 하거소프트가 가상 창업사 마바랩에 1년짜리 시스템 구축 용역을 제공하고
현금과 마바랩 주식으로 대가를 받는다. 금액 단위는 천원이다.

예제의 가정 (기준서가 정하지 않은 부분은 가정임을 밝힌다)
- 주식 공정가치는 계약 개시시점 값으로 잰다. 문단 66~69 는 측정 시점을 정하지 않는다.
- 용역은 기간에 걸쳐 이행되고, 분기마다 진행률이 25%씩 오른다.
"""

CASH = 100_000
BASE_SHARES = 2_000
BONUS_SHARES = 500           # 기한 내 완료하면 추가로 받는 주식
FV_AT_INCEPTION = 30         # 주당 공정가치, 계약 개시시점
FV_AT_RECEIPT = 45           # 주당 공정가치, 4분기 수령 시점
PROGRESS = [0.25, 0.50, 0.75, 1.00]
BONUS_UNCONSTRAINED_FROM = 3  # 3분기에 기한 내 완료 가능성이 매우 높아진다고 본다
SERVICE_SSP = 170_000        # 구축 용역의 개별 판매가격 (문단 67 경우에 쓴다)
SERVER_VALUE = 20_000        # 고객이 넘겨주는 서버 장비 (문단 69)


def fmt(amount):
    return f"{amount:>10,.0f}"


def transaction_price(include_bonus):
    shares = BASE_SHARES + (BONUS_SHARES if include_bonus else 0)
    return CASH + shares * FV_AT_INCEPTION


def show_inception():
    print("[1] 계약 개시시점 거래가격 — 문단 66·68")
    print(f"    현금                       {fmt(CASH)}")
    print(f"    주식 {BASE_SHARES:,}주 x {FV_AT_INCEPTION}       {fmt(BASE_SHARES * FV_AT_INCEPTION)}")
    print(f"    보너스 주식 {BONUS_SHARES}주 (제약)       {fmt(0)}")
    print(f"    거래가격                   {fmt(transaction_price(False))}")
    print()


def show_quarters():
    print("[2] 분기별 수익 — 보너스 주식은 제약이 풀린 분기에 누적 따라잡기")
    print("    분기  진행률   거래가격    누적 수익    분기 수익")
    cumulative = 0
    for quarter, progress in enumerate(PROGRESS, start=1):
        price = transaction_price(quarter >= BONUS_UNCONSTRAINED_FROM)
        new_cumulative = price * progress
        print(f"    {quarter}분기  {progress:>5.0%} {fmt(price)} {fmt(new_cumulative)} {fmt(new_cumulative - cumulative)}")
        cumulative = new_cumulative
    print(f"    합계                          {fmt(cumulative)}")
    print()
    return cumulative


def show_price_movement(revenue):
    shares = BASE_SHARES + BONUS_SHARES
    received = shares * FV_AT_RECEIPT
    print("[3] 주가 변동 — 대가의 형태 때문인 변동은 거래가격에 넣지 않는다 (문단 68)")
    print(f"    수령 주식 {shares:,}주 x {FV_AT_RECEIPT}         {fmt(received)}")
    print(f"    수익에 넣은 주식 몫            {fmt(revenue - CASH)}")
    print(f"    차이 (수익 밖)                 {fmt(received - (revenue - CASH))}")
    print(f"    수령 시점 값으로 잘못 잰 수익  {fmt(CASH + received)}")
    print()


def show_fair_value_unknown():
    noncash = SERVICE_SSP - CASH
    print("[4] 주식 공정가치를 추정할 수 없을 때 — 문단 67")
    print(f"    구축 용역 개별 판매가격        {fmt(SERVICE_SSP)}")
    print(f"    현금                           {fmt(CASH)}")
    print(f"    주식 대가로 보는 금액          {fmt(noncash)}")
    print()


def show_customer_server(base_price):
    print("[5] 고객이 넘겨주는 서버 장비 — 문단 69")
    print("    통제 여부    거래가격     서버 처리")
    print(f"    통제한다  {fmt(base_price + SERVER_VALUE)}     자산 인식, 비현금 대가")
    print(f"    통제 못함 {fmt(base_price)}     인식하지 않는다")


def main():
    print("환경: Python 표준 라이브러리, 금액 단위 천원, 가상 회사 하거소프트·마바랩")
    print()
    show_inception()
    revenue = show_quarters()
    show_price_movement(revenue)
    show_fair_value_unknown()
    show_customer_server(revenue)


if __name__ == "__main__":
    main()
