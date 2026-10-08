"""자사주 매입과 소각 — 주식 수가 줄 때 EPS·BPS·PBR·지분율이 어떻게 움직이는가.

1. 배당가능이익 한도: 상법 제341조 제1항 단서가 가리키는 제462조 제1항의 계산
2. 같은 비율(10%)을 사들이는 두 회사 — 주가가 BPS보다 높은 회사와 낮은 회사
3. 매입 가격에 따라 BPS가 오르는지 내리는지
4. 매입한 해의 가중평균유통주식수와 EPS
5. 보유 중일 때와 소각한 뒤 — 무엇이 바뀌고 무엇이 그대로인가
"""
import platform
import sys
from datetime import date

EOK = 100_000_000  # 1억원

SHARES = 10_000_000       # 상장(발행)주식수
BUYBACK = 1_000_000       # 사들이는 주식 수 — 10%
NET_INCOME = 150 * EOK
EQUITY = 1_000 * EOK
AFTER_TAX_YIELD = 0.02    # 매입에 쓴 현금이 벌던 세후 수익률 — 가정한 값
HOLDER = 1_000_000        # 주주 갑, 매도에 참여하지 않는다


def print_environment() -> None:
    print(f"Python {platform.python_version()} ({sys.platform})")
    print(f"가정: 순이익 {NET_INCOME // EOK}억원·자본총계 {EQUITY // EOK:,}억원(두 회사 같음), "
          f"매입 현금의 세후 수익률 {AFTER_TAX_YIELD:.0%}, 주가는 매입 전후 그대로")
    print()


def distributable_limit() -> None:
    # 제462조 제1항: 순자산 − 자본금 − 자본준비금·이익준비금 − 그 결산기에 적립할 이익준비금 − 미실현이익
    parts = {"자본금": 50, "자본준비금(주식발행초과금)": 200, "이익준비금": 25,
             "그 결산기에 적립할 이익준비금": 0, "미실현이익": 0}
    print("[1] 가나전자 직전 결산기 배당가능이익 — 자기주식 취득가액 총액의 한도 (단위 억원)")
    print(f"  순자산(자본총계) {EQUITY // EOK:>8,}")
    for name, amount in parts.items():
        print(f"  − {name:24}{amount:>6,}")
    limit = EQUITY // EOK - sum(parts.values())
    print(f"  = 배당가능이익    {limit:>8,}   이번 매입 {BUYBACK * 15_000 / EOK:,.0f}억원은 한도의 {BUYBACK * 15_000 / EOK / limit:.1%}")
    print("  같은 한도를 배당과 나눠 쓴다 — 자기주식에 150억원을 쓰면 남는 배당 여력은 그만큼 줄어든다")
    print()


def metrics(price: float, shares_out: int, equity: float, income: float) -> dict:
    eps = income / shares_out
    bps = equity / shares_out
    return {"EPS": eps, "BPS": bps, "PER": price / eps, "PBR": price / bps, "ROE": income / equity}


def before_after(name: str, price: int) -> None:
    cost = price * BUYBACK
    before = metrics(price, SHARES, EQUITY, NET_INCOME)
    lost = cost * AFTER_TAX_YIELD
    no_cost = metrics(price, SHARES - BUYBACK, EQUITY - cost, NET_INCOME)
    with_cost = metrics(price, SHARES - BUYBACK, EQUITY - cost, NET_INCOME - lost)
    # 회사 값에서 나간 현금만 빼고 남은 주식으로 나눈 값 — 시가에 샀으면 주가가 변하지 않는다
    theory = (price * SHARES - cost) / (SHARES - BUYBACK)
    print(f"  {name} — 주가 {price:,}원, 매입 {BUYBACK:,}주 = {cost / EOK:,.0f}억원,"
          f" 이론 주가 {theory:,.0f}원, 현금이 벌던 이익 {lost / EOK:.1f}억원")
    print(f"    {'':22}{'EPS':>10}{'BPS':>11}{'PER':>8}{'PBR':>8}{'ROE':>8}")
    for label, m in (("매입 전", before), ("매입 후(수익 감소 무시)", no_cost), ("매입 후(수익 감소 반영)", with_cost)):
        print(f"    {label:22}{m['EPS']:>10,.2f}{m['BPS']:>11,.2f}{m['PER']:>8.2f}{m['PBR']:>8.3f}{m['ROE']:>8.2%}")


def two_companies() -> None:
    print("[2] 순이익·자본·주식 수가 같고 주가만 다른 두 회사가 같은 10%를 사들이면 (매입한 다음 해 기준)")
    before_after("가나전자", 15_000)
    before_after("다라물산", 5_000)
    print()


def bps_by_price() -> None:
    bps_before = EQUITY / SHARES
    print(f"[3] 매입 가격별 BPS — 매입 전 BPS {bps_before:,.0f}원, 10% 매입")
    print(f"  {'매입 가격':>10}{'매입 가격/BPS':>14}{'매입 후 BPS':>14}{'변화':>10}")
    for price in (5_000, 10_000, 15_000, 20_000):
        after = (EQUITY - price * BUYBACK) / (SHARES - BUYBACK)
        print(f"  {price:>10,}{price / bps_before:>14.1f}{after:>14,.2f}{after / bps_before - 1:>10.2%}")
    print()


def buyback_year_eps() -> None:
    start, end = date(2025, 1, 1), date(2025, 12, 31)
    days_in_year = (end - start).days + 1
    bought = date(2025, 7, 1)
    before_days = (bought - start).days
    after_days = days_in_year - before_days
    weighted = (SHARES * before_days + (SHARES - BUYBACK) * after_days) / days_in_year
    cost = 15_000 * BUYBACK
    income = NET_INCOME - cost * AFTER_TAX_YIELD * after_days / days_in_year
    print("[4] 가나전자가 2025-07-01에 사들였을 때 그 해의 EPS (기업회계기준서 제1033호 문단 20)")
    print(f"  {SHARES:,}주 × {before_days}/{days_in_year} + {SHARES - BUYBACK:,}주 × {after_days}/{days_in_year}"
          f" = {weighted:,.0f}주")
    print(f"  순이익 {income / EOK:,.2f}억원 (하반기 현금 수익 감소 반영)")
    print(f"  매입한 해 EPS {income / weighted:,.2f}원 · 다음 해 EPS {(NET_INCOME - cost * AFTER_TAX_YIELD) / (SHARES - BUYBACK):,.2f}원"
          f" · 매입 전 EPS {NET_INCOME / SHARES:,.2f}원")
    print()


def hold_vs_cancel() -> None:
    price = 15_000
    cost = price * BUYBACK
    equity = EQUITY - cost
    income = NET_INCOME - cost * AFTER_TAX_YIELD
    rows = {
        "보유 중": {"listed": SHARES, "treasury": BUYBACK},
        "소각 후": {"listed": SHARES - BUYBACK, "treasury": 0},
    }
    print("[5] 가나전자 — 사들인 주식을 보유하고 있을 때와 소각한 뒤 (주가 15,000원)")
    print(f"  {'':8}{'상장주식수':>12}{'자기주식':>11}{'유통주식수':>12}{'자본총계(억)':>12}"
          f"{'EPS':>10}{'BPS':>11}{'시총-상장(억)':>13}{'시총-유통(억)':>13}{'갑 지분율':>10}")
    for label, r in rows.items():
        out = r["listed"] - r["treasury"]
        print(f"  {label:8}{r['listed']:>12,}{r['treasury']:>11,}{out:>12,}{equity / EOK:>12,.0f}"
              f"{income / out:>10,.2f}{equity / out:>11,.2f}{price * r['listed'] / EOK:>13,.0f}"
              f"{price * out / EOK:>13,.0f}{HOLDER / r['listed']:>10.2%}")
    print(f"  갑의 의결권 비율은 두 경우 모두 {HOLDER:,} / {SHARES - BUYBACK:,} = {HOLDER / (SHARES - BUYBACK):.2%}"
          " — 자기주식은 의결권이 없다")
    print()


if __name__ == "__main__":
    print_environment()
    distributable_limit()
    two_companies()
    bps_by_price()
    buyback_year_eps()
    hold_vs_cancel()
