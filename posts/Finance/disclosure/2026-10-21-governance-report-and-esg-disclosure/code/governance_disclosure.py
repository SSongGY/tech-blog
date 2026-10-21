"""서술형 공시에서 비교 가능한 항목만 골라내기.

기업지배구조보고서는 핵심원칙 10가지에 대한 서술과 핵심지표 15개에 대한 O/X 표로
이루어진다. 서술은 회사마다 길이도 범위도 달라 나란히 놓을 수 없지만, 15개 지표는
같은 자리에 같은 기준으로 찍히므로 비교가 된다.

가상 회사 `가나전자`·`다라물산`의 지표 응답을 두고 준수율을 계산하고, 같은
준수율이 전혀 다른 모양을 덮어 버리는 것을 보인다. 지속가능성 공시는 아직 대상
판정만 가능하므로, 가상 회사 세 곳이 언제부터 의무 대상이 되는지 계산한다.

지표 15개 항목과 준수율 정의는 한국거래소 「기업지배구조 보고서 가이드라인」
(2025.12)에서, 지속가능성 공시 일정은 금융위원회 「지속가능성(ESG) 공시 제도화
방안(최종안)」(2026.7.8.)에서 가져왔다. 회사와 응답은 실재하지 않는 가정값이다.
"""
import platform
import sys
import unicodedata

# 지배구조 핵심지표 15개 — (영역, 지표 이름)
# 가이드라인 「지배구조 핵심지표 준수 현황」 표의 순서를 그대로 따른다
INDICATORS = [
    ("주주",     "주주총회 4주 전 소집공고"),
    ("주주",     "전자투표 실시"),
    ("주주",     "주주총회 집중일 이외 개최"),
    ("주주",     "현금배당 관련 예측가능성 제공"),
    ("주주",     "배당정책·배당실시 계획 연 1회 이상 통지"),
    ("이사회",   "최고경영자 승계정책 마련·운영"),
    ("이사회",   "위험관리 등 내부통제정책 마련·운영"),
    ("이사회",   "사외이사가 이사회 의장"),
    ("이사회",   "집중투표제 채택"),
    ("이사회",   "기업가치 훼손 책임자의 임원 선임 방지 정책"),
    ("이사회",   "이사회 구성원 모두 단일성(性)이 아님"),
    ("감사기구", "독립적인 내부감사부서 설치"),
    ("감사기구", "내부감사기구에 회계·재무 전문가 존재"),
    ("감사기구", "분기별 1회 이상 경영진 없이 외부감사인과 회의"),
    ("감사기구", "경영 중요정보에 내부감사기구가 접근하는 절차"),
]

# 가상 회사의 응답 — True 가 준수. 전기는 직전 공시대상기간
COMPANIES = {
    "가나전자": {
        "당기": [True, True, True, True, True,
                True, True, False, False, True, False,
                False, True, False, False],
        "전기": [True, True, True, False, True,
                True, True, False, False, False, False,
                False, True, False, False],
    },
    "다라물산": {
        "당기": [True, False, False, False, False,
                True, True, False, False, True, True,
                True, True, True, True],
        "전기": [True, False, False, False, True,
                True, True, False, False, True, True,
                True, True, True, False],
    },
}

# 지속가능성 공시 의무 대상 — (적용 연도, 공시 대상 회계연도, 연결자산총액 기준)
ESG_SCHEDULE = [
    (2028, "FY2027", 10_000_000_000_000),
    (2029, "FY2028",  5_000_000_000_000),
]
ESG_UNDER_REVIEW = (2030, "FY2029", 2_000_000_000_000)  # 최종안에서 "검토" 단계

# 가상 회사의 연결자산총액 (원)
ESG_CANDIDATES = [
    ("가나전자", 12_400_000_000_000),
    ("다라물산",  6_800_000_000_000),
    ("마바산업",  2_900_000_000_000),
    ("사아텍",      740_000_000_000),
]

# 기업지배구조보고서 의무공시 대상 확대 — (적용 연도, 자산총액 기준)
GOVERNANCE_SCHEDULE = [
    (2019, 2_000_000_000_000),
    (2022, 1_000_000_000_000),
    (2024,   500_000_000_000),
    (2026, None),   # 코스피 전 상장사
]

AREAS = ["주주", "이사회", "감사기구"]


def width(text: str) -> int:
    """한글은 두 칸을 차지하므로 표를 맞추려면 글자 수가 아니라 폭을 센다."""
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)


def pad(text: str, size: int, align: str = "<") -> str:
    space = " " * max(0, size - width(text))
    return text + space if align == "<" else space + text


def jo(amount: int) -> str:
    """원 단위 금액을 조 단위로 — 자산 규모는 조로 읽는 편이 빠르다."""
    value = amount / 1_000_000_000_000
    return f"{value:,.0f}조원" if value == int(value) else f"{value:,.1f}조원"


def print_indicator_table() -> None:
    """두 회사의 15개 지표 응답을 나란히 놓는다 — 이것이 비교 가능한 층이다."""
    print("[1] 지배구조 핵심지표 15개 — 같은 자리에 같은 기준으로 찍히므로 나란히 놓을 수 있다")
    names = list(COMPANIES)
    print("  " + pad("영역", 10) + pad("핵심지표", 48)
          + "".join(pad(n, 12, ">") for n in names))
    for idx, (area, label) in enumerate(INDICATORS):
        cells = "".join(
            pad("O" if COMPANIES[n]["당기"][idx] else "X", 12, ">") for n in names)
        print("  " + pad(area, 10) + pad(label, 48) + cells)
    print()


def compliance(flags: list[bool]) -> float:
    """준수율 = 전체 핵심지표 15개 중 준수항목의 비율 (가이드라인 각주 9)."""
    return sum(flags) / len(INDICATORS)


def print_rate() -> None:
    print("[2] 준수율 — 한 숫자로 줄이면 두 회사가 같아 보인다")
    print("  " + pad("회사", 12) + pad("준수 항목", 12, ">")
          + pad("전체", 8, ">") + pad("준수율", 10, ">"))
    for name, data in COMPANIES.items():
        flags = data["당기"]
        print("  " + pad(name, 12) + pad(f"{sum(flags)}개", 12, ">")
              + pad(f"{len(flags)}개", 8, ">")
              + pad(f"{compliance(flags):.1%}", 10, ">"))
    print("  두 회사의 준수율이 같다. 여기서 멈추면 지배구조가 비슷하다고 읽게 된다")
    print()


def print_by_area() -> None:
    """같은 준수율을 영역별로 쪼개면 모양이 반대로 갈린다."""
    print("[3] 영역별로 쪼개면 — 같은 준수율이 정반대 모양을 덮고 있었다")
    header = "  " + pad("회사", 12)
    for area in AREAS:
        count = sum(1 for a, _ in INDICATORS if a == area)
        header += pad(f"{area}({count})", 14, ">")
    print(header + pad("합계", 12, ">"))
    for name, data in COMPANIES.items():
        row = "  " + pad(name, 12)
        for area in AREAS:
            idxs = [i for i, (a, _) in enumerate(INDICATORS) if a == area]
            got = sum(1 for i in idxs if data["당기"][i])
            row += pad(f"{got}/{len(idxs)}", 14, ">")
        row += pad(f"{sum(data['당기'])}/15", 12, ">")
        print(row)
    print("  가나전자는 주주 영역이 꽉 차 있고 감사기구가 비어 있다")
    print("  다라물산은 감사기구가 꽉 차 있고 주주 영역이 비어 있다")
    print("  준수율 60% 라는 같은 숫자가 서로 반대인 두 회사를 가린다")
    print()


def print_year_over_year() -> None:
    """전기 대비 변화 — 가이드라인 표에 직전 공시대상기간 준수여부가 함께 찍힌다."""
    print("[4] 전기 대비 변화 — 올랐는지가 아니라 어디가 바뀌었는지를 본다")
    flat = []
    for name, data in COMPANIES.items():
        before, now = data["전기"], data["당기"]
        delta = compliance(now) - compliance(before)
        print(f"  {name}  {compliance(before):.1%} → {compliance(now):.1%} "
              f"({sum(before)}/15 → {sum(now)}/15, {delta:+.1%}p)")
        moved = 0
        for i, (area, label) in enumerate(INDICATORS):
            if now[i] and not before[i]:
                print(f"    + {pad(area, 10)}{label}")
                moved += 1
            elif before[i] and not now[i]:
                print(f"    - {pad(area, 10)}{label}")
                moved += 1
        if delta == 0 and moved:
            flat.append((name, moved))
    for name, moved in flat:
        print(f"  {name}은 준수율이 그대로인데 지표 {moved}개가 자리를 바꿨다 — "
              f"숫자만 보면 아무 일도 없었던 해다")
    print("  준수율의 변화량이 아니라 붙고 빠진 항목을 봐야 무엇이 달라졌는지 알 수 있다")
    print()


def print_comparability() -> None:
    """보고서의 어느 층이 비교 가능한지 — 이 글의 본론."""
    print("[5] 보고서의 층별 비교 가능성")
    rows = [
        ("핵심지표 준수 현황", "O / X", "가능",
         "15개 항목이 고정, 판정 기준도 가이드라인이 정함"),
        ("준수율", "백분율", "가능",
         "분모가 15로 고정 — 다만 항목 가중치는 없다"),
        ("기업개요 요약 재무현황", "금액", "가능",
         "당기·전기·전전기 3개년이 같은 양식"),
        ("핵심원칙 10가지 서술", "서술형", "불가",
         "분량·범위·구체성이 회사마다 다름"),
        ("미준수 사유와 향후 계획", "서술형", "불가",
         "항목이 같아도 서술 수준이 갈림"),
        ("고유한 지배구조 특징", "서술형", "불가",
         "쓸지 말지부터 회사가 정함"),
    ]
    print("  " + pad("보고서 항목", 26) + pad("형태", 10)
          + pad("비교", 8) + "왜")
    for what, form, ok, why in rows:
        print("  " + pad(what, 26) + pad(form, 10) + pad(ok, 8) + why)
    print("  서술형을 비교하려 들면 긴 쪽이 잘한 것으로 보인다. 분량은 지배구조가 아니다")
    print("  가이드라인도 준수 여부에 매몰되지 말고 현황을 정확히 공시하는 것이 중요하다고 적는다")
    print()


def print_governance_schedule() -> None:
    print("[6] 기업지배구조보고서 의무공시 대상 확대 — 자산총액 기준 (코스피)")
    print("  " + pad("적용", 8) + pad("자산총액 기준", 18, ">") + "  비고")
    for year, threshold in GOVERNANCE_SCHEDULE:
        label = jo(threshold) + " 이상" if threshold else "전 상장사"
        note = "기준 없이 전체로 확대" if threshold is None else "단계적 확대"
        print("  " + pad(f"{year}년", 8) + pad(label, 18, ">") + "  " + note)
    print("  제출 기한은 매년 5월 31일이고, 공시대상 기간은 직전연도 1월 1일부터 12월 31일까지다")
    print("  기한까지 제출하지 않으면 불성실공시법인 지정 절차가 개시된다")
    print()


def print_esg_schedule() -> None:
    """지속가능성 공시 — 아직 계산할 수 있는 것은 대상 판정뿐이다."""
    print("[7] 지속가능성 공시 의무 대상 판정 — 연결자산총액 기준")
    print("  " + pad("적용", 8) + pad("공시대상", 11) + pad("연결자산총액 기준", 20, ">")
          + "  비고")
    for year, fy, threshold in ESG_SCHEDULE:
        print("  " + pad(f"{year}년", 8) + pad(fy, 11)
              + pad(jo(threshold) + " 이상", 20, ">") + "  최종안 확정")
    year, fy, threshold = ESG_UNDER_REVIEW
    print("  " + pad(f"{year}년", 8) + pad(fy, 11)
          + pad(jo(threshold) + " 이상", 20, ">") + "  추가 확대 검토 단계")
    print()
    print("  " + pad("회사", 12) + pad("연결자산총액", 15, ">")
          + pad("최초 대상", 17, ">") + "  근거")
    for name, assets in ESG_CANDIDATES:
        hit = next(((y, f, t) for y, f, t in ESG_SCHEDULE if assets >= t), None)
        if hit:
            y, f, t = hit
            print("  " + pad(name, 12) + pad(jo(assets), 15, ">")
                  + pad(f"{y}년({f})", 17, ">")
                  + f"  {jo(t)} 기준 충족")
        else:
            y, f, t = ESG_UNDER_REVIEW
            if assets >= t:
                print("  " + pad(name, 12) + pad(jo(assets), 15, ">")
                      + pad("미정", 17, ">")
                      + f"  {y}년 {jo(t)} 확대가 검토 단계")
            else:
                print("  " + pad(name, 12) + pad(jo(assets), 15, ">")
                      + pad("해당 없음", 17, ">") + "  확정·검토 기준 모두 아래")
    print("  제3자 검증(인증) 의무는 최초 공시 2년 뒤인 2030년부터 적용된다")
    print("  도입 초기 3년간은 공시 내용에 대해 손해배상·행정제재·형사처벌이 면제된다")
    print("    — 다만 고의적 그린워싱은 면책 대상이 아니다")
    print()


def print_schedule_drift() -> None:
    """같은 해에 두 번 바뀐 대상 기준 — 일정을 못 박아 읽으면 안 되는 이유."""
    print("[8] 적용 대상 기준이 다섯 달 사이에 바뀌었다")
    rows = [
        ("2026.2.25.", "로드맵 의견수렴안", "30조원 이상", "2028년(FY2027)"),
        ("2026.7.8.",  "제도화 방안 최종안", "10조원 이상", "2028년(FY2027)"),
    ]
    print("  " + pad("시점", 13) + pad("문서", 22)
          + pad("최초 대상 기준", 16, ">") + pad("최초 적용", 18, ">"))
    for when, doc, threshold, start in rows:
        print("  " + pad(when, 13) + pad(doc, 22)
              + pad(threshold, 16, ">") + pad(start, 18, ">"))
    print("  공시기준(KSSB)은 먼저 확정됐지만 누구에게 언제 적용할지는 뒤에 정해졌다")
    print("  시작 연도는 그대로인데 대상 기준만 3분의 1로 내려갔다")
    print("  제도 일정을 인용할 때 발효일과 문서 시점을 같이 적어야 하는 이유다")
    print()


def main() -> None:
    print(f"Python {platform.python_version()} / {platform.system()}")
    print("회사: 가나전자·다라물산·마바산업·사아텍(모두 가상) / 지표 응답과 자산 규모는 가정값")
    print()
    print_indicator_table()
    print_rate()
    print_by_area()
    print_year_over_year()
    print_comparability()
    print_governance_schedule()
    print_esg_schedule()
    print_schedule_drift()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
