"""빌린 돈으로 산 자리(신용융자)와 빌린 주식으로 판 자리(대차)를 나란히 센다.

여기 나오는 가나전자는 실재하지 않는 가상 회사다. 주가·융자금·담보유지비율은
계산 구조를 보이려고 만든 값이고, 실제 종목이나 특정 증권사의 기준이 아니다.

- 신용융자: 주가가 내려가면 담보비율이 깨진다. 어느 주가에서 깨지는지 센다.
- 대차: 잔고를 금액으로 보면 주가가 움직이기만 해도 변한다. 그 크기를 센다.

파이썬 표준 라이브러리만 쓴다.
"""

import math
import sys

QTY = 1_000  # 가나전자 보유 수량(주)
BUY_PRICE = 10_000  # 매수 체결가(원)
OWN_CASH = 4_000_000  # 자기 자금(원)
LOAN = QTY * BUY_PRICE - OWN_CASH  # 신용융자금 6,000,000원

# 담보유지비율. 금융투자업규정이 정한 최소 담보비율은 신용공여액의 140% 이고,
# 실제 비율은 그 이상에서 증권사 약관이 종목군별로 정한다.
MAINTENANCE = {"A": 1.40, "B": 1.45, "C": 1.50, "D": 1.60}

PRICES = [10_000, 9_500, 9_000, 8_400, 8_300, 8_000, 7_200, 6_500]

PREV_CLOSE = 10_000  # 반대매매 수량 산정에 쓰는 전일 종가
LOWER_LIMIT = 0.30  # 가격제한폭 ±30%. 하한가 = 전일 종가 × 0.7

# 대차잔고를 금액으로 바꿀 때 쓰는 수량. 이 수량은 아래 표 내내 고정이다.
LENT_QTY = 1_000_000


def won(x):
    return f"{round(x):>14,}원"


def section(no, title):
    print()
    print(f"[{no}] {title}")
    print("-" * 72)


def collateral_ratio():
    section(1, f"신용융자 {LOAN:,}원 — 주가별 담보비율과 유지비율 미달 여부")
    head = f"{'주가':>9} {'담보평가액':>14} {'담보비율':>9}"
    for grade in MAINTENANCE:
        head += f" {grade + '군':>5}"
    print(head)
    for price in PRICES:
        value = QTY * price
        ratio = value / LOAN
        row = f"{price:>8,}원 {won(value)} {ratio * 100:>8.1f}%"
        for keep in MAINTENANCE.values():
            row += f" {'부족' if ratio < keep else '유지':>5}"
        print(row)
    print()
    print("  담보는 당일 종가로 평가한다. 융자금은 주가와 무관하게 그대로이므로,")
    print("  비율은 분자만 움직여서 내려간다.")


def fill_the_gap(keep=1.40):
    """담보 부족을 현금으로 메울 때와 반대매매로 메울 때."""
    floor_price = round(PREV_CLOSE * (1 - LOWER_LIMIT) / 10) * 10
    section(2, f"유지비율 {keep * 100:.0f}% 를 회복하는 두 가지 길 (하한가 {floor_price:,}원 기준)")
    print(f"{'주가':>9} {'담보비율':>9} {'추가담보 현금':>16} {'반대매매 수량':>14} {'처분금액':>14}")
    for price in PRICES:
        value = QTY * price
        ratio = value / LOAN
        if ratio >= keep:
            print(f"{price:>8,}원 {ratio * 100:>8.1f}% {'-':>16} {'-':>14} {'-':>14}")
            continue
        # 현금을 넣으면 담보만 늘고 융자금은 그대로다.
        cash_needed = keep * LOAN - value
        # 주식을 팔면 처분대금이 융자금을 갚으므로 분모도 함께 줄어든다.
        # (QTY-n)*price >= keep * (LOAN - n*floor_price) 를 n 에 대해 푼다.
        denom = keep * floor_price - price
        qty_needed = math.ceil((keep * LOAN - value) / denom) if denom > 0 else QTY
        qty_needed = min(qty_needed, QTY)
        print(
            f"{price:>8,}원 {ratio * 100:>8.1f}% {cash_needed:>15,.0f}원"
            f" {qty_needed:>13,}주 {qty_needed * floor_price:>13,}원"
        )
    print()
    print("  현금은 부족분만큼만 넣으면 되지만, 주식은 보수적인 하한가로 수량을")
    print("  세므로 훨씬 많이 팔린다. 산식은 증권사마다 다르다 — 여기서는 처분 뒤")
    print("  비율이 유지비율을 회복하는 최소 수량을 하한가 기준으로 계산했다.")


def two_balances():
    section(3, "같은 포지션을 그대로 둔 채 주가만 움직일 때, 두 잔고가 보이는 값")
    print(f"  신용융자 잔고: 빌린 돈 {LOAN:,}원 — 단위가 원이다")
    print(f"  대차 잔고    : 빌린 주식 {LENT_QTY:,}주 — 단위가 주식 수다")
    print()
    print(f"{'주가':>9} {'신용융자 잔고':>16} {'대차 잔고(수량)':>17} {'대차 잔고(금액)':>18}")
    for price in PRICES:
        print(
            f"{price:>8,}원 {LOAN:>15,}원 {LENT_QTY:>16,}주"
            f" {LENT_QTY * price:>17,}원"
        )
    print()
    base = LENT_QTY * PRICES[0]
    last = LENT_QTY * PRICES[-1]
    print(f"  한 주도 더 빌리거나 갚지 않았는데 금액은 {base:,}원에서")
    print(f"  {last:,}원으로 {(last - base) / base * 100:.0f}% 움직였다. 잔고'금액'은")
    print("  잔고주수 × 종가라서 주가를 그대로 안고 있다.")


def lending_vs_short():
    section(4, f"빌린 {LENT_QTY:,}주 중 공매도로 나간 비중을 모를 때")
    print(f"{'공매도 비중(가정)':>18} {'시장에 나온 매도':>16} {'남은 용도':>14}")
    for share in (0.0, 0.3, 0.6, 1.0):
        sold = round(LENT_QTY * share)
        print(f"{share * 100:>17.0f}% {sold:>15,}주 {LENT_QTY - sold:>13,}주")
    print()
    print("  대차잔고는 빌려서 아직 갚지 않은 수량이다. 빌린 주식은 공매도 말고도")
    print("  차익거래·헤지·결제 목적으로 쓰이므로, 비중을 모르면 대차잔고 하나로는")
    print("  매도 물량이 0주인지 100만 주인지 가릴 수 없다. 위 비중은 가정값이고")
    print("  실제 비중을 뜻하지 않는다. 공매도 수량은 따로 공표되는 공매도 통계를 본다.")


def main():
    print(f"python {sys.version.split()[0]}")
    print("가나전자 — 실재하지 않는 가상 회사. 아래 숫자는 전부 만든 값이다.")
    collateral_ratio()
    fill_the_gap()
    two_balances()
    lending_vs_short()


if __name__ == "__main__":
    main()
