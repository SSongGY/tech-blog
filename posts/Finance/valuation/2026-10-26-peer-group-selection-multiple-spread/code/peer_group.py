"""비교기업을 어떻게 고르느냐에 따라 같은 회사의 적정주가가 얼마나 갈리는지 센다.

평가 대상은 가상 회사 다온소재다. 후보 10개사도 전부 가상 회사다.
세 가지를 본다. (1) 요건을 걸지 않은 비교군과 건 비교군의 배수 차이,
(2) 평균·중앙값·절사평균·조화평균이 같은 자료에서 얼마나 벌어지는지,
(3) 비교군이 몇 사까지 줄면 중앙값이 한 회사의 값과 같아지는지.
파이썬 표준 라이브러리만 쓴다.
"""

from statistics import mean, median

# --- 평가 대상 -------------------------------------------------------------
TARGET = "다온소재"
T_PRETAX_PS = 1_500      # 주당 법인세비용차감전계속사업이익 (원)
T_BPS = 12_000           # 주당순자산 (원)
T_EBITDA = 500           # 억원
T_NET_DEBT = 300         # 억원
T_SHARES = 1_000         # 만주

# 「증권의 발행 및 공시 등에 관한 규정 시행세칙」 제7조가 유사회사에 요구하는 폭.
# 주당 세전계속사업이익과 주당순자산이 각각 평가 대상의 ±30% 안에 들어야 한다.
BAND = 0.30
MIN_PEERS = 3            # 같은 조문이 요구하는 최소 유사회사 수

# --- 후보 10개사 (전부 가상) ------------------------------------------------
# 이름, 주당세전이익, 주당순자산, EV/EBITDA, PER
CANDIDATES = [
    ("가람케미칼",   1_400, 11_200,  6.4,  9.5),
    ("나루머티리얼", 1_750, 14_000,  8.9, 12.1),
    ("다솜첨단소재", 1_150,  9_800,  9.1, 10.8),
    ("라온테크",       600,  6_200, 22.0, 31.0),
    ("마루정밀",     2_600, 21_000,  6.1,  8.2),
    ("바로소재",     1_300,  5_900, 11.8, 14.0),
    ("사월바이오",     150, 10_500, 42.0, 88.0),
    ("아람전자",     1_900, 16_800, 10.2, 13.3),
    ("자온신소재",   1_020, 11_500, 12.5, 18.4),
    ("차율소재",     1_600, 13_100,  8.4, 11.0),
]


def line(title):
    print()
    print(title)
    print("-" * len(title) * 2)


def trimmed_mean(values, trim=1):
    """양 끝에서 trim 개씩 떼고 평균을 낸다."""
    s = sorted(values)
    return mean(s[trim:len(s) - trim])


def harmonic_mean(values):
    """배수의 역수(수익률)를 평균한 뒤 되돌린다."""
    return len(values) / sum(1 / v for v in values)


def screen():
    """시행세칙 제7조의 폭을 그대로 걸어 후보를 거른다."""
    line(f"[1] 요건을 걸어 본다 — 평가 대상({TARGET})의 ±{BAND:.0%} 안에 드는가")

    lo_e, hi_e = T_PRETAX_PS * (1 - BAND), T_PRETAX_PS * (1 + BAND)
    lo_b, hi_b = T_BPS * (1 - BAND), T_BPS * (1 + BAND)
    print(f"  주당세전이익 허용 폭 {lo_e:,.0f} ~ {hi_e:,.0f} 원"
          f"   (대상 {T_PRETAX_PS:,} 원)")
    print(f"  주당순자산   허용 폭 {lo_b:,.0f} ~ {hi_b:,.0f} 원"
          f"   (대상 {T_BPS:,} 원)")
    print()
    print(f"  {'회사':<14}{'주당세전이익':>12}{'주당순자산':>12}"
          f"{'EV/EBITDA':>11}{'PER':>8}  판정")

    passed = []
    for name, eps, bps, ev, per in CANDIDATES:
        ok_e, ok_b = lo_e <= eps <= hi_e, lo_b <= bps <= hi_b
        if ok_e and ok_b:
            verdict = "통과"
            passed.append((name, eps, bps, ev, per))
        elif not ok_e and not ok_b:
            verdict = "탈락 (둘 다)"
        elif not ok_e:
            verdict = "탈락 (이익)"
        else:
            verdict = "탈락 (순자산)"
        print(f"  {name:<14}{eps:>12,}{bps:>12,}{ev:>11.1f}{per:>8.1f}  {verdict}")

    print()
    print(f"  통과 {len(passed)}사 / 후보 {len(CANDIDATES)}사"
          f"   (최소 요건 {MIN_PEERS}사)")
    return passed


def spread(passed):
    line("[2] 같은 자료, 다른 비교군 — 적정주가가 어디까지 갈리는가")

    all_ev = [c[3] for c in CANDIDATES]
    pass_ev = [c[3] for c in passed]
    no_outlier = [c[3] for c in CANDIDATES if c[0] != "사월바이오"]

    cases = [
        ("후보 10사 전부 · 평균", mean(all_ev)),
        ("후보 10사 전부 · 중앙값", median(all_ev)),
        ("이상치 1사만 뺀 평균", mean(no_outlier)),
        (f"요건 통과 {len(passed)}사 · 평균", mean(pass_ev)),
    ]

    print(f"  {'비교군':<26}{'EV/EBITDA':>11}{'기업가치':>11}"
          f"{'지분가치':>11}{'주당가치':>14}")
    values = []
    for label, mult in cases:
        ev = T_EBITDA * mult
        eq = ev - T_NET_DEBT
        ps = eq * 10_000 / T_SHARES
        values.append(ps)
        print(f"  {label:<26}{mult:>11.2f}{ev:>11,.0f}{eq:>11,.0f}"
              f"{ps:>11,.0f} 원")

    print()
    print(f"  가장 높은 값 / 가장 낮은 값 = "
          f"{max(values) / min(values):.2f}배")


def averaging(passed):
    line("[3] 더하는 방법만 바꿔 본다 — 평균이냐 중앙값이냐 조화평균이냐")

    groups = [
        ("후보 10사 전부", [c[3] for c in CANDIDATES]),
        (f"요건 통과 {len(passed)}사", [c[3] for c in passed]),
    ]
    print(f"  {'비교군':<20}{'산술평균':>10}{'중앙값':>10}"
          f"{'절사평균':>10}{'조화평균':>10}{'평균-조화':>12}")
    for label, vals in groups:
        am, md = mean(vals), median(vals)
        tm = trimmed_mean(vals) if len(vals) > 2 else am
        hm = harmonic_mean(vals)
        print(f"  {label:<20}{am:>10.2f}{md:>10.2f}{tm:>10.2f}"
              f"{hm:>10.2f}{am - hm:>12.2f}")

    print()
    print("  조화평균은 배수의 역수(EBITDA/EV, 즉 수익률)를 평균한 뒤 되돌린 값이다.")
    print("  배수가 큰 회사일수록 역수는 0 에 가까워지므로 영향력이 줄어든다.")


def per_share(mult):
    return (T_EBITDA * mult - T_NET_DEBT) * 10_000 / T_SHARES


def leave_one_out(passed):
    """비교군에서 한 회사씩 빼고 결론이 얼마나 움직이는지 본다."""
    line("[4] 한 회사를 빼 본다 — 어느 비교군이 더 흔들리는가")

    for label, group in (("후보 10사", CANDIDATES), (f"요건 통과 {len(passed)}사", passed)):
        vals = [c[3] for c in group]
        base = mean(vals)
        results = []
        for drop in group:
            rest = [c[3] for c in group if c[0] != drop[0]]
            results.append((drop[0], mean(rest)))

        lo = min(results, key=lambda r: r[1])
        hi = max(results, key=lambda r: r[1])
        span = per_share(hi[1]) - per_share(lo[1])
        print(f"  {label} — 기준 평균 {base:.2f}배 · 주당 {per_share(base):,.0f} 원")
        print(f"    가장 많이 내리는 회사: {lo[0]:<12} 제외 시 {lo[1]:.2f}배"
              f" · 주당 {per_share(lo[1]):,.0f} 원")
        print(f"    가장 많이 올리는 회사: {hi[0]:<12} 제외 시 {hi[1]:.2f}배"
              f" · 주당 {per_share(hi[1]):,.0f} 원")
        print(f"    한 회사 교체로 벌어지는 폭: {span:,.0f} 원"
              f" (기준 대비 {span / per_share(base):.0%})")
        print()


if __name__ == "__main__":
    kept = screen()
    spread(kept)
    averaging(kept)
    leave_one_out(kept)
