"""투입공수 방식 대가산정을 SW사업 대가산정 가이드(2025년 개정판)의 예제로 검산한다.

1) 가이드 ISP 예제 — 직무별 투입공수 x 평균임금 -> 직접인건비 -> 제경비 -> 기술료 -> 합계
2) 제경비율(144~154%)·기술료율(20~40%) 범위가 합계를 얼마나 벌리는가
3) 2026년 적용 SW기술자 평균임금 — 일평균 = 월평균 / 20.5, 시간평균 = 일평균 / 8 이 맞는가
4) M/D -> M/M 환산 — 가이드의 1M/M = 20.8M/D 와 임금 공표의 20.5일이 어긋나는 크기
5) 같은 예제를 2026년 평균임금으로 다시 계산
"""
from decimal import ROUND_HALF_UP, Decimal

# 가이드 표 2-8 예제(PDF 93~94쪽)의 투입 계획: (직무, 투입인원, 투입기간(월), 투입률)
ISP_PLAN = [
    ("IT컨설턴트", 2, 4, Decimal("0.5")),
    ("IT기획자", 3, 4, Decimal("0.5")),
    ("IT아키텍트(인프라)", 3, 4, Decimal("0.5")),
    ("IT아키텍트(SW)", 2, 2, Decimal("0.5")),
    ("IT컨설턴트", 2, 2, Decimal("0.5")),
]

# 가이드 예제에 적힌 월평균임금(원) — 2025년 적용 공표값
GUIDE_WAGE = {
    "IT컨설턴트": 9_706_020,
    "IT기획자": 11_597_656,
    "IT아키텍트(인프라)": 10_147_745,
    "IT아키텍트(SW)": 10_147_745,
}

# 2026년 적용 SW기술자 평균임금(2025-12-19 공표): 직무 -> (월평균, 일평균, 시간평균)
WAGE_2026 = {
    "IT기획자": (11_853_218, 578_206, 72_276),
    "IT컨설턴트": (10_707_960, 522_340, 65_292),
    "업무분석가": (9_740_667, 475_154, 59_394),
    "데이터분석가": (8_499_309, 414_600, 51_825),
    "IT PM": (10_086_804, 492_039, 61_505),
    "IT아키텍트": (11_103_230, 541_621, 67_703),
    "UI/UX 기획/개발자": (6_901_660, 336_666, 42_083),
    "UI/UX 디자이너": (5_159_246, 251_671, 31_459),
    "응용SW 개발자": (7_754_124, 378_250, 47_281),
    "시스템SW 개발자": (5_840_196, 284_888, 35_611),
    "정보시스템운용자": (10_649_117, 519_469, 64_934),
    "IT지원기술자": (5_170_016, 252_196, 31_524),
    "IT마케터": (11_793_500, 575_293, 71_912),
    "IT품질관리자": (11_042_071, 538_638, 67_330),
    "IT테스터": (4_053_137, 197_714, 24_714),
    "IT감리": (11_745_154, 572_934, 71_617),
    "정보보안전문가": (10_411_680, 507_887, 63_486),
}

OVERHEAD_RANGE = (Decimal("1.44"), Decimal("1.54"))   # 제경비율
TECH_FEE_RANGE = (Decimal("0.20"), Decimal("0.40"))   # 기술료율
VAT_RATE = Decimal("0.10")


def won(value):
    return f"{int(value):>15,}"


def estimate(plan, wage_of, overhead_rate, tech_fee_rate, direct_expense):
    """가이드의 6단계 중 3~6단계: 직접인건비 -> 제경비 -> 기술료 -> 합계."""
    man_month = sum(people * months * rate for _, people, months, rate in plan)
    labor = sum(
        people * months * rate * wage_of(role) for role, people, months, rate in plan
    )
    overhead = labor * overhead_rate
    tech_fee = (labor + overhead) * tech_fee_rate
    total = labor + overhead + tech_fee + direct_expense
    return man_month, labor, overhead, tech_fee, total


def main():
    print("[1] 가이드 ISP 예제 재계산 (제경비 150%, 기술료 30%, 직접경비 2,000,000원)")
    man_month, labor, overhead, tech_fee, total = estimate(
        ISP_PLAN, GUIDE_WAGE.get, Decimal("1.5"), Decimal("0.3"), 2_000_000
    )
    for role, people, months, rate in ISP_PLAN:
        mm = people * months * rate
        print(f"    {role:<14} {people}명 x {months}개월 x {rate} = {mm} M/M")
    print(f"    총 투입공수   {man_month} M/M")
    print(f"    직접인건비   {won(labor)}  (가이드: 209,004,016)")
    print(f"    제경비       {won(overhead)}  (가이드: 313,506,024)")
    print(f"    기술료       {won(tech_fee)}  (가이드: 156,753,012)")
    print(f"    합계(별도)   {won(total)}  (가이드: 681,263,052)")
    with_vat = total * (1 + VAT_RATE)
    print(f"    부가세 포함  {with_vat}  -> 원 미만 버림 {won(with_vat)}  (가이드: 749,389,357)")

    print("\n[2] 제경비율·기술료율 범위의 양 끝 (직접경비 제외, 직접인건비 대비 배수)")
    for overhead_rate in OVERHEAD_RANGE:
        for tech_fee_rate in TECH_FEE_RANGE:
            factor = (1 + overhead_rate) * (1 + tech_fee_rate)
            amount = labor * factor
            print(
                f"    제경비 {overhead_rate * 100:.0f}% 기술료 {tech_fee_rate * 100:.0f}%"
                f"  배수 {factor:.4f}  금액 {won(amount)}"
            )
    low = labor * (1 + OVERHEAD_RANGE[0]) * (1 + TECH_FEE_RANGE[0])
    high = labor * (1 + OVERHEAD_RANGE[1]) * (1 + TECH_FEE_RANGE[1])
    print(f"    최대/최소 = {high / low:.4f}  차액 {won(high - low)}")

    print("\n[3] 2026년 평균임금 — 일평균 = 월평균/근무일수, 시간평균 = 일평균/8 검산")
    for working_days in (Decimal("20.5"), Decimal("20.8")):
        daily_match = hourly_match = 0
        for monthly, daily, hourly in WAGE_2026.values():
            computed_daily = (Decimal(monthly) / working_days).quantize(
                Decimal("1"), ROUND_HALF_UP
            )
            computed_hourly = (Decimal(daily) / 8).quantize(Decimal("1"), ROUND_HALF_UP)
            daily_match += computed_daily == daily
            hourly_match += computed_hourly == hourly
        print(
            f"    근무일수 {working_days}일 가정: 일평균 일치 {daily_match}/{len(WAGE_2026)}"
            f"  시간평균 일치 {hourly_match}/{len(WAGE_2026)}"
        )
    print("    시간평균이 '반올림한 일평균/8' 과 어긋나는 직무 — 반올림 전 일평균/8 과 비교")
    for role, (monthly, daily, hourly) in WAGE_2026.items():
        from_rounded = (Decimal(daily) / 8).quantize(Decimal("1"), ROUND_HALF_UP)
        from_raw = (Decimal(monthly) / Decimal("20.5") / 8).quantize(
            Decimal("1"), ROUND_HALF_UP
        )
        if from_rounded != hourly:
            print(
                f"      {role}: 공표 {hourly:,}  일평균/8 {Decimal(daily) / 8}"
                f" -> {from_rounded:,}  월평균/20.5/8 {Decimal(monthly) / Decimal('164'):.4f}"
                f" -> {from_raw:,}"
            )
    raw_match = sum(
        (Decimal(m) / Decimal("164")).quantize(Decimal("1"), ROUND_HALF_UP) == h
        for m, _, h in WAGE_2026.values()
    )
    print(f"    월평균/(20.5x8) 로 계산하면 시간평균 일치 {raw_match}/{len(WAGE_2026)}")
    monthly, daily, hourly = WAGE_2026["IT기획자"]
    print(
        f"    예) IT기획자 {monthly:,} / 20.5 = {Decimal(monthly) / Decimal('20.5'):.2f}"
        f" -> {daily:,},  {daily:,} / 8 = {Decimal(daily) / 8} -> {hourly:,}"
    )

    print("\n[4] M/D 로 센 공수를 M/M 로 바꿀 때 — 20.8 과 20.5")
    man_day = Decimal(416)
    role = "응용SW 개발자"
    monthly, daily, _ = WAGE_2026[role]
    by_day = man_day * daily
    for working_days in (Decimal("20.8"), Decimal("20.5")):
        mm = man_day / working_days
        print(
            f"    {man_day} M/D / {working_days} = {mm:.4f} M/M"
            f"  x 월평균 {monthly:,} = {won(mm * monthly)}"
        )
    print(f"    {man_day} M/D x 일평균 {daily:,}         = {won(by_day)}")
    print(f"    20.8 환산 대비 일평균 직접 계산 비율 = {by_day / (man_day / Decimal('20.8') * monthly):.4f}")

    print("\n[5] 같은 예제를 2026년 평균임금으로")
    wage_2026_of = {
        "IT컨설턴트": WAGE_2026["IT컨설턴트"][0],
        "IT기획자": WAGE_2026["IT기획자"][0],
        "IT아키텍트(인프라)": WAGE_2026["IT아키텍트"][0],
        "IT아키텍트(SW)": WAGE_2026["IT아키텍트"][0],
    }.get
    _, labor_2026, _, _, total_2026 = estimate(
        ISP_PLAN, wage_2026_of, Decimal("1.5"), Decimal("0.3"), 2_000_000
    )
    print(f"    직접인건비   {won(labor_2026)}  (2025년 임금 {won(labor)})")
    print(f"    합계(별도)   {won(total_2026)}  (2025년 임금 {won(total)})")
    print(f"    직접인건비 증가율 {(labor_2026 / labor - 1) * 100:.2f}%")
    for role in ("IT컨설턴트", "IT기획자"):
        print(
            f"    {role} 월평균 {GUIDE_WAGE[role]:,} -> {WAGE_2026[role][0]:,}"
            f"  ({(Decimal(WAGE_2026[role][0]) / GUIDE_WAGE[role] - 1) * 100:.2f}%)"
        )
    print(
        f"    IT아키텍트 월평균 {GUIDE_WAGE['IT아키텍트(SW)']:,} -> {WAGE_2026['IT아키텍트'][0]:,}"
        f"  ({(Decimal(WAGE_2026['IT아키텍트'][0]) / GUIDE_WAGE['IT아키텍트(SW)'] - 1) * 100:.2f}%)"
    )


def check_other_examples():
    """가이드의 다른 투입공수 예제 3개를 같은 식으로 다시 더한다 (2025년 적용 임금)."""
    print("\n[6] 운영비 예제 (표 4-22·4-23, PDF 241·243쪽) — 제경비 150%, 기술료 20%")
    # (업무, 직무, 인원, 기간, 투입률, 가이드 표 4-22 에 적힌 투입공수, 월평균임금)
    operation = [
        ("월례보고 작성", "IT PM", 1, 12, "0.5", "6.0", 9_145_473),
        ("안내데스크 운영", "IT지원기술자", 1, 12, "0.3", "3.6", 5_058_021),
        ("품질관리", "IT품질관리자", 1, 6, "0.3", "1.8", 9_692_094),
        ("서비스 계획/시행", "IT PM", 1, 12, "0.5", "6.0", 9_145_473),
        ("게시판 운영", "응용SW개발자", 1, 12, "0.2", "3.0", 6_943_457),
        ("데이터 백업", "정보시스템운용자", 1, 6, "0.3", "1.8", 10_154_626),
        ("연동관리", "응용SW개발자", 1, 12, "0.3", "3.0", 6_943_457),
        ("성능관리", "응용SW개발자", 1, 12, "0.3", "3.6", 6_943_457),
        ("버전관리", "IT품질관리자", 1, 6, "0.2", "1.2", 9_692_094),
    ]
    labor = Decimal(0)
    for task, role, people, months, rate, written_mm, wage in operation:
        mm = people * months * Decimal(rate)
        labor += mm * wage
        mark = "" if mm == Decimal(written_mm) else f"   <- 표에는 {written_mm}"
        print(f"    {task:<10} {role:<9} {people}x{months}x{rate} = {mm}{mark}")
    total_mm = sum(p * m * Decimal(r) for _, _, p, m, r, _, _ in operation)
    written_total_mm = sum(Decimal(w) for *_, w, _ in operation)
    print(f"    총 투입공수 계산 {total_mm} / 표에 적힌 값의 합 {written_total_mm}")
    overhead = labor * Decimal("1.5")
    tech_fee = (labor + overhead) * Decimal("0.2")
    direct_expense = 500_000
    print(f"    직접인건비   {won(labor)}  (가이드: 241,966,348)")
    print(f"    제경비       {won(overhead)}  (가이드: 362,949,522)")
    print(f"    기술료       {won(tech_fee)}  (가이드: 120,983,174)")
    print(f"    네 항목 합   {won(labor + overhead + tech_fee + direct_expense)}  (가이드 합계: 484,432,696)")
    print(f"    직접인건비를 뺀 합 {won(overhead + tech_fee + direct_expense)}")

    print("\n[7] 고정비/변동비 혼합방식의 고정비 예제 (PDF 265~267쪽) — 제경비 150%, 기술료 20%")
    fixed = [
        ("IT PM", 1, 3, "0.3", 9_145_473), ("응용SW개발자", 1, 3, "0.5", 6_943_457),
        ("응용SW개발자", 1, 3, "0.5", 6_943_457), ("IT지원기술자", 1, 3, "1.0", 5_058_021),
        ("IT PM", 1, 3, "0.2", 9_145_473), ("IT지원기술자", 2, 3, "0.5", 5_058_021),
        ("IT PM", 1, 3, "0.5", 9_145_473), ("IT지원기술자", 2, 3, "0.5", 5_058_021),
    ]
    mm = sum(p * m * Decimal(r) for _, p, m, r, _ in fixed)
    labor = sum(p * m * Decimal(r) * w for _, p, m, r, w in fixed)
    overhead = labor * Decimal("1.5")
    tech_fee = (labor + overhead) * Decimal("0.2")
    print(f"    총 투입공수 {mm} M/M  직접인건비 {won(labor)}  (가이드: 93,788,979)")
    print(f"    제경비 {overhead}  기술료 {tech_fee}")
    print(f"    고정비 {won(labor + overhead + tech_fee)}  (가이드: 281,366,938)")

    print("\n[8] 부록 혼합사례의 디자인 부분 (PDF 445쪽) — UI/UX개발 2명 x 3개월")
    labor = 2 * 3 * Decimal(6_727_260)
    overhead = labor * Decimal("1.5")
    tech_fee = (labor + overhead) * Decimal("0.2")
    print(f"    직접인건비 {won(labor)}  제경비 {won(overhead)}  기술료 {won(tech_fee)}")
    print(f"    합계 {won(labor + overhead + tech_fee)}  (가이드: 121,090,680)")


if __name__ == "__main__":
    main()
    check_other_examples()
