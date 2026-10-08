"""기본 EPS와 희석 EPS — 기업회계기준서 제1033호의 계산 순서를 그대로 따라간다.

1. 가중평균유통보통주식수: 기중에 신주 발행·자기주식 취득이 있는 가상 회사
2. 순이익이 같은 세 회사의 희석 EPS: 전환사채, 주식선택권, 둘 다
3. 반희석 판정과 '희석효과가 큰 것부터' 순서가 결과를 바꾸는 경우
"""
import platform
import sys
from datetime import date

EOK = 100_000_000  # 1억원

TAX_RATE = 0.20          # 가정한 법인세율 — 실제 세율이 아니라 계산을 보이기 위한 값
NET_INCOME = 120 * EOK   # 세 회사 공통 보통주 귀속 당기순이익
BASIC_SHARES = 10_000_000
AVG_MARKET_PRICE = 16_000  # 회계기간 평균시장가격(원)


def print_environment() -> None:
    print(f"Python {platform.python_version()} ({sys.platform})")
    print(f"가정: 법인세율 {TAX_RATE:.0%}, 회계기간 2025-01-01 ~ 2025-12-31, 잠재적보통주는 모두 기초부터 존재")
    print()


def weighted_average_shares() -> None:
    start, end = date(2025, 1, 1), date(2025, 12, 31)
    days_in_year = (end - start).days + 1
    # (날짜, 변동 주식 수, 사유) — 날짜 당일부터 유통주식에 반영한다(문단 21: 발행일 기산)
    events = [
        (date(2025, 4, 1), 1_200_000, "유상증자 신주 발행"),
        (date(2025, 10, 1), -300_000, "자기주식 취득"),
    ]
    print("[1] 가중평균유통보통주식수 — 사바산업 (기초 10,000,000주)")
    print(f"  {'구간':25}{'유통주식수':>14}{'일수':>6}{'가중치':>10}{'주식수×가중치':>16}")
    outstanding = 10_000_000
    boundaries = [start] + [e[0] for e in events] + [date(2026, 1, 1)]
    changes = [0] + [e[1] for e in events]
    total = 0.0
    for i in range(len(boundaries) - 1):
        outstanding += changes[i]
        days = (boundaries[i + 1] - boundaries[i]).days
        weight = days / days_in_year
        total += outstanding * weight
        label = f"{boundaries[i]} ~ {date.fromordinal(boundaries[i + 1].toordinal() - 1)}"
        print(f"  {label:25}{outstanding:>14,}{days:>6}{weight:>10.4f}{outstanding * weight:>16,.0f}")
    print(f"  가중평균유통보통주식수 = {total:,.0f}주   (기말 유통주식수 {outstanding:,}주)")
    profit = 120 * EOK
    print(f"  기본 EPS = {profit / EOK:.0f}억원 / {total:,.0f}주 = {profit / total:,.2f}원"
          f"   (기말 주식수로 나누면 {profit / outstanding:,.2f}원)")
    print()


def convertible(face: int, coupon: float, conversion_price: int) -> dict:
    # 분자에 되돌릴 금액은 세후 이자비용(문단 33). 예제는 표면이자를 이자비용으로 둔다
    shares = face // conversion_price
    add_back = face * coupon * (1 - TAX_RATE)
    return {"kind": "전환사채", "desc": f"액면 {face // EOK}억·표면 {coupon:.2%}·전환가 {conversion_price:,}원",
            "add_back": add_back, "shares": shares}


def option(count: int, exercise_price: int) -> dict:
    # 자기주식법(문단 45~46): 행사대금으로 평균시장가격에 되사는 만큼은 효과가 없고,
    # 나머지만 대가 없이 발행한 주식으로 본다
    bought_back = count * exercise_price / AVG_MARKET_PRICE
    shares = max(count - bought_back, 0)
    return {"kind": "주식선택권", "desc": f"{count:,}주·행사가 {exercise_price:,}원",
            "add_back": 0.0, "shares": shares}


def incremental(item: dict) -> float:
    return float("inf") if item["shares"] == 0 else item["add_back"] / item["shares"]


def diluted_eps(items: list[dict], ordered: bool = True, verbose: bool = True) -> float:
    """희석효과가 큰 것(증분주식당 이익이 작은 것)부터 하나씩 넣고, EPS를 낮추지 못하면 뺀다."""
    earnings, shares = float(NET_INCOME), float(BASIC_SHARES)
    eps = earnings / shares
    queue = sorted(items, key=incremental) if ordered else items
    for item in queue:
        trial = (earnings + item["add_back"]) / (shares + item["shares"]) if item["shares"] else eps
        dilutive = trial < eps
        if verbose:
            inc = incremental(item)
            inc_text = "—" if inc == float("inf") else f"{inc:,.2f}"
            print(f"    {item['kind']:6}{item['desc']:34}증분주식 {item['shares']:>11,.0f}  "
                  f"주당 증분이익 {inc_text:>9}  {eps:>9,.2f} → {trial:>9,.2f}  "
                  f"{'희석 — 포함' if dilutive else '반희석 — 제외'}")
        if dilutive:
            earnings += item["add_back"]
            shares += item["shares"]
            eps = trial
    return eps


def three_companies() -> None:
    basic = NET_INCOME / BASIC_SHARES
    print(f"[2] 순이익 {NET_INCOME // EOK}억원, 가중평균유통보통주식수 {BASIC_SHARES:,}주가 같은 세 회사"
          f" — 기본 EPS {basic:,.2f}원, 평균시장가격 {AVG_MARKET_PRICE:,}원")
    companies = {
        "가나전자": [convertible(200 * EOK, 0.04, 10_000)],
        "다라물산": [option(1_000_000, 8_000)],
        "마바화학": [option(1_000_000, 8_000), convertible(200 * EOK, 0.0725, 20_000)],
    }
    results = {}
    for name, items in companies.items():
        print(f"  {name}")
        results[name] = diluted_eps(items)
    print()
    print(f"  {'회사':8}{'기본 EPS':>12}{'희석 EPS':>12}{'희석률':>10}")
    for name, eps in results.items():
        print(f"  {name:8}{basic:>12,.2f}{eps:>12,.2f}{1 - eps / basic:>10.2%}")
    print()


def ordering_and_antidilution() -> None:
    print("[3] 순서와 반희석 — 마바화학의 전환사채를 기본 EPS 하고만 비교하면")
    cb = convertible(200 * EOK, 0.0725, 20_000)
    opt = option(1_000_000, 8_000)
    basic = NET_INCOME / BASIC_SHARES
    print(f"  전환사채 주당 증분이익 {incremental(cb):,.2f}원 < 기본 EPS {basic:,.2f}원 → 단독으로는 희석")
    wrong = (NET_INCOME + cb["add_back"]) / (BASIC_SHARES + cb["shares"] + opt["shares"])
    right = diluted_eps([opt, cb], verbose=False)
    print(f"  둘 다 넣으면       ({NET_INCOME / EOK:.0f}억 + {cb['add_back'] / EOK:.1f}억) / "
          f"{BASIC_SHARES + cb['shares'] + opt['shares']:,.0f}주 = {wrong:,.2f}원")
    print(f"  순서대로 판정하면  선택권만 포함 = {right:,.2f}원   ← 더 작은 쪽이 희석 EPS(문단 44)")
    print()
    print("  같은 조건에서 전환사채 표면이자율만 바꾸면 (선택권은 그대로)")
    print(f"  {'표면이자율':>10}{'주당 증분이익':>14}{'단독 판정':>12}{'순서 판정':>12}{'희석 EPS':>12}")
    for coupon in (0.04, 0.06, 0.0725, 0.09):
        c = convertible(200 * EOK, coupon, 20_000)
        alone = "희석" if incremental(c) < basic else "반희석"
        eps = diluted_eps([opt, c], verbose=False)
        in_order = "포함" if eps < NET_INCOME / (BASIC_SHARES + opt["shares"]) else "제외"
        print(f"  {coupon:>10.2%}{incremental(c):>14,.2f}{alone:>12}{in_order:>12}{eps:>12,.2f}")
    print()
    print("  행사가격이 평균시장가격 이상인 선택권 (문단 46)")
    for price in (8_000, 12_000, 16_000, 18_000):
        o = option(1_000_000, price)
        print(f"    행사가 {price:>6,}원 → 증분주식 {o['shares']:>9,.0f}주, 희석 EPS {diluted_eps([o], verbose=False):,.2f}원")
    print()


if __name__ == "__main__":
    print_environment()
    weighted_average_shares()
    three_companies()
    ordering_and_antidilution()
