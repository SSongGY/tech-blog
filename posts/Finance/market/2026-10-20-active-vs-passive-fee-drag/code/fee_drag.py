"""보수가 장기 잔액을 깎는 정도 — 가상 상품 세 개로 계산한다.

회사·상품·수치는 전부 가상이다. 실재하는 펀드나 ETF 가 아니다.
비용 전 수익률은 연 7% 로 고정해, 결과의 차이가 오직 비용에서만 나오게 두었다.
"""

import random
import unicodedata

GROSS = 0.07          # 비용 차감 전 연 수익률 (가정)
PRINCIPAL = 100_000_000

# 열 이름은 금융투자협회 전자공시 '펀드별 보수비용비교' 화면을 따랐다.
# 보수율 합계(A) + 기타비용(B) = TER, 매매·중개수수료율(D)는 TER 밖에 따로 적힌다.
PRODUCTS = [
    # 이름,             운용,  판매,  수탁,  사무관리, 기타비용, 매매중개
    ("가나액티브주식형", 0.75, 0.60, 0.04, 0.02, 0.12, 0.42),
    ("다라인덱스펀드",   0.18, 0.14, 0.03, 0.01, 0.04, 0.05),
    ("마바지수ETF",      0.04, 0.00, 0.02, 0.01, 0.02, 0.03),
]


def shown_width(text):
    """한글·한자는 터미널에서 두 칸을 차지한다."""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def pad(text, width):
    return text + " " * max(width - shown_width(text), 0)


def rpad(text, width):
    return " " * max(width - shown_width(text), 0) + text


def rows():
    for name, mgmt, sale, trust, admin, other, broker in PRODUCTS:
        total_fee = mgmt + sale + trust + admin
        ter = total_fee + other
        yield name, mgmt, sale, trust, admin, total_fee, other, ter, broker, ter + broker


def balance(cost_pct, years):
    """비용을 매년 잔액 비율로 뗄 때의 기말 잔액."""
    net = (1 + GROSS) * (1 - cost_pct / 100) - 1
    return PRINCIPAL * (1 + net) ** years


def breakeven_gross(cost_pct, target_cost_pct):
    """비용이 더 비싼 상품이 싼 상품과 같은 잔액이 되려면 필요한 비용 전 수익률."""
    return ((1 + GROSS) * (1 - target_cost_pct / 100) / (1 - cost_pct / 100) - 1) * 100


def win_rate(gap_pct, sigma_pct, samples=10000, seed=20261020):
    """비용 전 알파가 평균 0 인 정규분포일 때, 비용 격차를 넘는 비율."""
    rnd = random.Random(seed)
    draws = [rnd.gauss(0.0, sigma_pct) for _ in range(samples)]
    mean = sum(draws) / samples          # 평균을 정확히 0 으로 맞춘다
    draws = [d - mean for d in draws]
    return sum(1 for d in draws if d > gap_pct) / samples * 100


def main():
    print("[0] 가정")
    print(f"  비용 전 연 수익률 {GROSS * 100:.0f}% 고정 · 투자원금 {PRINCIPAL:,}원")
    print("  비용은 매년 잔액 비율로 뗀다. 세금과 판매수수료(선취·후취)는 넣지 않았다.")
    print()

    print("[1] 보수·비용의 자리 — 가상 상품 세 개 (단위 %)")
    cols = ("운용", "판매", "수탁", "사무관리", "기타비용", "합계A", "TER", "매매중개D", "실부담")
    print("  " + pad("상품", 20) + "".join(rpad(c, 10) for c in cols))
    for name, mgmt, sale, trust, admin, total_fee, other, ter, broker, real in rows():
        cells = (mgmt, sale, trust, admin, other, total_fee, ter, broker, real)
        print("  " + pad(name, 20) + "".join(f"{v:>10.2f}" for v in cells))
    print("  합계(A) = 운용 + 판매 + 수탁 + 사무관리 · TER = A + 기타비용(B) · 실부담 = TER + 매매·중개(D)")
    print()

    costs = {name: real for name, *_ , real in rows()}
    cheap = min(costs, key=costs.get)

    print("[2] 1억원을 굴렸을 때 남는 잔액 — 비용만 다르고 나머지는 같다")
    years = (1, 5, 10, 20, 30)
    print("  " + pad("상품", 20) + rpad("실부담", 8) + "".join(rpad(f"{y}년", 15) for y in years))
    for name, cost in costs.items():
        cells = "".join(f"{balance(cost, y):>15,.0f}" for y in years)
        print("  " + pad(name, 20) + f"{cost:>8.2f}" + cells)
    gaps = "".join(f"{balance(costs[cheap], y) - balance(costs['가나액티브주식형'], y):>15,.0f}"
                   for y in years)
    print("  " + pad("격차(ETF − 액티브)", 28) + gaps)
    for y in (10, 20, 30):
        ratio = balance(costs['가나액티브주식형'], y) / balance(costs[cheap], y) * 100
        print(f"  {y:>2}년 뒤 액티브 잔액은 ETF 의 {ratio:.1f}%")
    print()

    print("[3] 손익분기 — 액티브가 ETF 와 같은 잔액이 되려면 비용 전 수익률이 얼마여야 하나")
    need = breakeven_gross(costs['가나액티브주식형'], costs[cheap])
    print(f"  ETF 의 비용 전 수익률       {GROSS * 100:>6.2f} %")
    print(f"  액티브에 필요한 비용 전 수익률 {need:>6.2f} %")
    gap = costs['가나액티브주식형'] - costs[cheap]
    print(f"  매년 더 벌어야 하는 폭        {need - GROSS * 100:>6.2f} %p")
    print(f"  실부담 격차                 {gap:>6.2f} %p")
    print("  필요한 폭이 격차보다 큰 것은 비용을 수익률이 아니라 잔액 비율에서 떼기 때문이다.")
    print(f"  격차 × (1 + {GROSS:.2f}) ÷ (1 − 실부담) = {gap * (1 + GROSS) / (1 - costs['가나액티브주식형'] / 100):.2f} %p")
    print()

    print("[4] 비용 전 평균이 같을 때, 비용을 뺀 뒤 ETF 를 앞서는 액티브의 비율")
    print("  알파가 평균 0 · 표준편차 2.0 %p 인 정규분포라고 두고 10,000 개를 뽑았다")
    for gap in (0.30, 0.90, costs['가나액티브주식형'] - costs[cheap]):
        print(f"  실부담 격차 {gap:>5.2f} %p → 앞서는 비율 {win_rate(gap, 2.0):>5.2f} %")
    print("  격차가 0 이면 50% 다. 비용이 벌리는 만큼 그대로 깎인다.")
    print()

    print("[5] TER 밖에 있는 비용 — 회전율이 만드는 연간 부담")
    print("  왕복 거래비용 0.30% 가정. 회전율은 1년 동안 보유 종목을 몇 번 갈아끼웠나를 뜻한다")
    print("  " + rpad("회전율", 8) + rpad("연간 거래비용", 16) + rpad("30년 뒤 잔액", 20))
    for turnover in (20, 50, 100, 200, 400):
        cost = turnover / 100 * 0.30
        print(f"  {turnover:>7}%{cost:>15.2f}%{balance(costs[cheap] + cost, 30):>20,.0f}")


if __name__ == "__main__":
    main()
