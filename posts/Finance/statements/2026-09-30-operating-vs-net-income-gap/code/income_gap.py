"""영업이익은 같은데 당기순이익이 흑자와 적자로 갈리는 두 가상 회사를 계산한다.

가나전자와 다라물산은 매출 500억, 영업이익 40억으로 본업 성과가 같다. 가나전자는
달러 차입금과 인수한 자회사를 안고 있어서 영업이익 아래에서 이자, 외화환산손실,
영업권 손상차손, 지분법손실이 빠진다. 다라물산은 부채가 적고 그런 항목이 없다.
금액 단위는 억원이고, 법인세는 계산을 단순하게 하려고 세전이익의 20%로 두었다.
"""

import platform
import sys

TAX_RATE = 0.20       # 실제 법인세율·세무조정과 무관한 가정값
USD_DEBT = 0.25       # 달러 차입금, 억달러 단위 (= 2,500만 달러)
RATE_OPEN = 1300      # 기초 원/달러 환율
RATE_CLOSE = 1420     # 기말 원/달러 환율

# 영업이익 아래 항목의 성격. 반복되는가, 현금이 나갔는가를 따로 적어 둔다
ITEM_KIND = {
    "금융수익":    ("반복", "현금"),
    "이자비용":    ("반복", "현금"),
    "외화환산손실": ("환율에 따라 부호가 바뀜", "현금 아님"),
    "영업권손상차손": ("일회성", "현금 아님"),
    "지분법손실":   ("관계기업 실적에 따름", "현금 아님"),
}


def fx_translation(debt_usd: float, rate_open: float, rate_close: float) -> float:
    """달러 부채를 기말 환율로 다시 잰 차이. 환율이 오르면 원화 부채가 커져 손실(음수)이다."""
    return round(-debt_usd * (rate_close - rate_open), 4) + 0.0   # + 0.0 은 -0 표기를 없앤다


COMPANIES = {
    "가나전자": {
        "매출액": 500, "영업이익": 40,
        "금융수익": 2, "이자비용": -18,
        "외화환산손실": fx_translation(USD_DEBT, RATE_OPEN, RATE_CLOSE),
        "영업권손상차손": -25, "지분법손실": -5,
    },
    "다라물산": {
        "매출액": 500, "영업이익": 40,
        "금융수익": 2, "이자비용": -3,
        "외화환산손실": 0, "영업권손상차손": 0, "지분법손실": 0,
    },
}
BELOW = list(ITEM_KIND)


def bottom_line(pl: dict) -> tuple[float, float, float]:
    """(법인세비용차감전순이익, 법인세비용, 당기순이익). 손실이면 세금 효과도 같은 비율로 잡는다."""
    pretax = round(pl["영업이익"] + sum(pl[k] for k in BELOW), 4)
    tax = round(pretax * TAX_RATE, 4)
    return pretax, tax, round(pretax - tax, 4)


def main() -> None:
    print(f"Python {sys.version.split()[0]} / {platform.system()}")
    print(f"단위: 억원 / 회사: 가나전자·다라물산(가상) / 법인세 = 세전이익 × {TAX_RATE:.0%}(가정)")

    print("\n[1] 영업이익에서 당기순이익까지")
    print("  항목                 " + "".join(f"{c:>10}" for c in COMPANIES))
    for n in ["매출액", "영업이익"] + BELOW:
        print(f"  {n:<16}" + "".join(f"{pl[n]:>12g}" for pl in COMPANIES.values()))
    results = {c: bottom_line(pl) for c, pl in COMPANIES.items()}
    for i, n in enumerate(["법인세비용차감전순이익", "법인세비용(−는 세금 효과)", "당기순이익"]):
        print(f"  {n:<16}" + "".join(f"{r[i]:>12g}" for r in results.values()))

    print(f"\n[2] 외화환산손실은 어디서 왔나 — 달러 차입금 {USD_DEBT * 1e4:,.0f}만 달러")
    print(f"  기초 {RATE_OPEN:,}원 → 원화 {USD_DEBT * RATE_OPEN:g}억")
    print(f"  기말 {RATE_CLOSE:,}원 → 원화 {USD_DEBT * RATE_CLOSE:g}억")
    print(f"  부채가 늘어난 만큼 손실 {fx_translation(USD_DEBT, RATE_OPEN, RATE_CLOSE):g}억 (현금은 한 푼도 안 나갔다)")

    gana = COMPANIES["가나전자"]
    gap = gana["영업이익"] - results["가나전자"][0]
    print(f"\n[3] 가나전자 영업이익과 세전이익의 차이 {gap:g}억을 성격별로 나누면")
    for k in sorted(BELOW, key=lambda k: gana[k]):
        repeat, cash = ITEM_KIND[k]
        print(f"  {k:<10}{gana[k]:>8g}   {repeat:<14} {cash}")
    non_cash = sum(gana[k] for k in BELOW if ITEM_KIND[k][1] == "현금 아님")
    print(f"  현금이 나가지 않은 항목 합계 {non_cash:g}")

    print("\n[4] 내년 환율만 바꿔 보면 — 손상차손은 다시 안 생긴다고 두고, 나머지는 올해와 같게")
    print(f"  {'기말 환율':<10}{'외화환산손익':>10}{'세전이익':>10}{'당기순이익':>10}")
    for rate in (1300, 1420, 1540):
        next_year = dict(gana, 영업권손상차손=0,
                         외화환산손실=fx_translation(USD_DEBT, RATE_CLOSE, rate))
        pretax, _, net = bottom_line(next_year)
        print(f"  {rate:<12,}{next_year['외화환산손실']:>12g}{pretax:>12g}{net:>12g}")

    print("\n[5] 영업이익이 이자비용의 몇 배인가")
    for c, pl in COMPANIES.items():
        print(f"  {c}  {pl['영업이익']:g} ÷ {-pl['이자비용']:g} = {pl['영업이익'] / -pl['이자비용']:.1f}배")


if __name__ == "__main__":
    main()
