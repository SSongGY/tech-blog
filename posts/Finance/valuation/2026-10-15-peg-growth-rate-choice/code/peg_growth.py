"""PEG — 분모에 어느 성장률을 넣느냐에 따라 값이 어디까지 갈리는지 계산한다.

가상 회사 `가나전자` 한 곳의 EPS 이력과 추정치로 성장률 후보 여섯 가지를 만들고,
같은 PER 을 그 여섯으로 각각 나눈다. 이어서 단위 혼동, 기저효과, 그리고
2단계 배당할인모형이 말하는 '정당한 PEG' 가 위험과 성장률에 따라 어떻게
움직이는지를 본다. 파이썬 표준 라이브러리만 쓴다.
"""

# 가상 회사 가나전자. 전부 설명용 가정값이고 실재하는 기업과 관계가 없다.
PRICE = 72_000  # 주가(원)
EPS_HISTORY = {  # 주당순이익(원). 2025 이후는 추정치로 본다
    2021: 2_400,
    2022: 1_100,
    2023: 2_050,
    2024: 2_700,
    2025: 3_000,
    2026: 3_450,
    2027: 3_800,
    2028: 4_100,
}
BASE_YEAR = 2025
ONE_OFF_IMPAIRMENT_2022 = 900  # 2022년 EPS 에 들어간 일회성 손상(주당, 세후)
ROE = 0.12          # 자기자본이익률
PAYOUT = 0.30       # 배당성향


def pad(text: str, width: int) -> str:
    """한글은 터미널에서 두 칸을 차지하므로 글자 수가 아니라 폭으로 맞춘다."""
    shown = sum(2 if ord(ch) > 0x2E7F else 1 for ch in text)
    return text + " " * max(0, width - shown)


def cagr(begin: float, end: float, years: int) -> float:
    """연평균 성장률. 시작값이 0 이하면 정의되지 않는다."""
    return (end / begin) ** (1 / years) - 1


def two_stage_pe(growth, required_return, payout, years,
                 stable_growth, stable_payout):
    """2단계 배당할인모형이 정당화하는 PER.

    고성장 n 년 뒤 영구 안정성장으로 넘어간다고 본다. 분자를 EPS 로 나눈 꼴이라
    배당성향·요구수익률·성장률만으로 PER 이 정해진다.
    """
    g, r, n, gn = growth, required_return, years, stable_growth
    high = (payout * (1 + g) * (1 - ((1 + g) ** n) / ((1 + r) ** n))) / (r - g)
    stable = (stable_payout * ((1 + g) ** n) * (1 + gn)) / ((r - gn) * ((1 + r) ** n))
    return high + stable


def justified_peg(growth, required_return, payout, years,
                  stable_growth, stable_payout):
    """정당한 PER 을 성장률(%)로 나눈 값. 관습대로 성장률은 퍼센트 수치로 쓴다."""
    pe = two_stage_pe(growth, required_return, payout, years,
                      stable_growth, stable_payout)
    return pe / (growth * 100)


def solve_growth_for_peg_one(required_return, payout, years,
                             stable_growth, stable_payout,
                             low=0.01, high=0.80, steps=800):
    """정당한 PEG 가 1 을 지나는 성장률을 전부 찾는다.

    PEG 는 성장률에 대해 단조롭지 않으므로 구간 하나를 이분법으로 자르면
    교차점을 놓친다. 촘촘히 훑어 부호가 바뀌는 구간마다 따로 좁힌다.
    """
    def f(g):
        return justified_peg(g, required_return, payout, years,
                             stable_growth, stable_payout) - 1.0

    roots = []
    step = (high - low) / steps
    left = low
    for i in range(steps):
        right = low + step * (i + 1)
        if f(left) * f(right) <= 0:
            lo, hi = left, right
            for _ in range(80):
                mid = (lo + hi) / 2
                if f(lo) * f(mid) <= 0:
                    hi = mid
                else:
                    lo = mid
            roots.append((lo + hi) / 2)
        left = right
    return roots


def main() -> None:
    eps_base = EPS_HISTORY[BASE_YEAR]
    per = PRICE / eps_base

    print("[0] 산식")
    print("  PER = 주가 ÷ 주당순이익(EPS)")
    print("  PEG = PER ÷ 기대 EPS 성장률(%)")
    print("  2단계 모형의 정당한 PER")
    print("    PER = 배당성향×(1+g)×[1-(1+g)^n/(1+r)^n] / (r-g)")
    print("          + 안정기배당성향×(1+g)^n×(1+gn) / [(r-gn)×(1+r)^n]")
    print("  지속가능성장률 = ROE × (1 - 배당성향)")
    print()

    print("[1] 가나전자 — EPS 이력과 추정 (단위: 원)")
    for year, eps in EPS_HISTORY.items():
        mark = "  (추정)" if year > BASE_YEAR else ""
        base = "  ← 기준 연도" if year == BASE_YEAR else ""
        print(f"  {year}년  {eps:>7,}{mark}{base}")
    print(f"  주가 {PRICE:,}원 ÷ {BASE_YEAR}년 EPS {eps_base:,}원 "
          f"= PER {per:.1f}배")
    print()

    sustainable = ROE * (1 - PAYOUT)
    candidates = [
        ("과거 3년 CAGR (2022→2025)",
         cagr(EPS_HISTORY[2022], eps_base, 3)),
        ("과거 4년 CAGR (2021→2025)",
         cagr(EPS_HISTORY[2021], eps_base, 4)),
        ("직전 연도 대비 (2024→2025)",
         EPS_HISTORY[2025] / EPS_HISTORY[2024] - 1),
        ("내년 증가율 (2025→2026)",
         EPS_HISTORY[2026] / EPS_HISTORY[2025] - 1),
        ("향후 3년 CAGR (2025→2028)",
         cagr(eps_base, EPS_HISTORY[2028], 3)),
        (f"지속가능성장률 (ROE {ROE:.0%} × 유보율 {1 - PAYOUT:.0%})",
         sustainable),
    ]

    print("[2] 같은 PER 을 성장률 후보 여섯으로 나눈 PEG")
    print(f"  {pad('성장률 후보', 38)}{'성장률':>7}{'PEG':>9}")
    pegs = []
    for label, g in candidates:
        peg = per / (g * 100)
        pegs.append(peg)
        print(f"  {pad(label, 34)}{g * 100:>8.1f}%{peg:>9.2f}")
    print(f"  가장 낮은 값 {min(pegs):.2f} ~ 가장 높은 값 {max(pegs):.2f} "
          f"— {max(pegs) / min(pegs):.1f}배 차이")
    print()

    g_next = EPS_HISTORY[2026] / EPS_HISTORY[2025] - 1
    print("[3] 단위를 섞으면")
    print(f"  성장률을 퍼센트 수치로 ({g_next * 100:.1f})  PEG = "
          f"{per / (g_next * 100):>8.2f}")
    print(f"  성장률을 소수로      ({g_next:.3f})  PEG = "
          f"{per / g_next:>8.2f}")
    print(f"  두 값의 비 = {(per / g_next) / (per / (g_next * 100)):.0f}배")
    print()

    adjusted_2022 = EPS_HISTORY[2022] + ONE_OFF_IMPAIRMENT_2022
    g_raw = cagr(EPS_HISTORY[2022], eps_base, 3)
    g_adj = cagr(adjusted_2022, eps_base, 3)
    print("[4] 기저효과 — 2022년 일회성 손상 주당 "
          f"{ONE_OFF_IMPAIRMENT_2022:,}원을 빼고 다시 세면")
    print(f"  공시 EPS {EPS_HISTORY[2022]:,}원 기준  3년 CAGR "
          f"{g_raw * 100:>5.1f}%   PEG {per / (g_raw * 100):.2f}")
    print(f"  조정 EPS {adjusted_2022:,}원 기준  3년 CAGR "
          f"{g_adj * 100:>5.1f}%   PEG {per / (g_adj * 100):.2f}")
    print(f"  출발점 한 해를 바꿨을 뿐인데 PEG 가 "
          f"{per / (g_adj * 100) / (per / (g_raw * 100)):.1f}배가 된다")
    print()

    # Damodaran 강의자료의 예제로 구현을 검산한다. 고성장 5년, 베타 1,
    # 무위험이자율 1.5%, 시장위험프리미엄 5% → 요구수익률 6.5%, PEG 1.94.
    check = justified_peg(growth=0.15, required_return=0.065, payout=0.25,
                          years=5, stable_growth=0.015, stable_payout=0.925)
    print("[5] 구현 검산 — 공개 강의자료의 예제 값과 맞는지")
    print(f"  g 15%, r 6.5%, 고성장 5년, 배당성향 25%→92.5%, 안정성장 1.5%")
    print(f"  계산값 PEG = {check:.2f}  (강의자료에 적힌 값 1.94)")
    print()

    # 아래는 가나전자 가정과 같은 틀의 설명용 격자다.
    RF, ERP = 0.035, 0.06
    N, PAYOUT_HIGH = 5, 0.25
    GN, PAYOUT_STABLE = 0.03, 0.70
    betas = [0.8, 1.0, 1.3]
    growths = [0.05, 0.10, 0.15, 0.20, 0.25]

    print("[6] 2단계 모형이 정당화하는 PEG "
          f"(무위험 {RF:.1%}, 시장프리미엄 {ERP:.0%}, 고성장 {N}년,")
    print(f"     배당성향 {PAYOUT_HIGH:.0%}→{PAYOUT_STABLE:.0%}, "
          f"안정성장 {GN:.0%}. 행 = 베타, 열 = 기대성장률)")
    header = "".join(f"{g * 100:>10.0f}%" for g in growths)
    print(f"  {pad('베타', 8)}{pad('요구수익률', 10)}{header}")
    for beta in betas:
        r = RF + beta * ERP
        row = "".join(
            f"{justified_peg(g, r, PAYOUT_HIGH, N, GN, PAYOUT_STABLE):>11.2f}"
            for g in growths
        )
        print(f"  {beta:<8.1f}{r:>6.1%}{row}")
    print()

    print("[7] 정당한 PEG 가 1 을 지나는 성장률 (1~80% 구간을 훑어서)")
    for beta in betas:
        r = RF + beta * ERP
        roots = solve_growth_for_peg_one(r, PAYOUT_HIGH, N, GN, PAYOUT_STABLE)
        if not roots:
            print(f"  베타 {beta:.1f} (r {r:>5.1%})  "
                  f"구간 전체에서 1 아래로 내려가지 않는다")
        else:
            spots = ", ".join(f"{g * 100:.1f}%" for g in roots)
            print(f"  베타 {beta:.1f} (r {r:>5.1%})  g = {spots}")
    print("  같은 PEG 1 이라도 전제한 위험이 다르면 가리키는 성장률이 다르고,")
    print("  구간에 따라 두 번 지나기도 한다 — PEG 는 성장률에 단조롭지 않다")


if __name__ == "__main__":
    main()
