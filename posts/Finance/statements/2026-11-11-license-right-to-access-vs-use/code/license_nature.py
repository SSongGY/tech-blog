"""라이선스가 접근권인지 사용권인지 가르고, 같은 계약금이 언제 수익이 되는지 계산한다.

가상 회사 가나라이선싱은 지적재산 라이선스 두 건을 같은 조건으로 판다.
계약금 1,200(단위 백만원)을 계약일에 한 번에 받고, 라이선스 기간은 4년이다.
회계연도는 1~12월이다.
근거: 기업회계기준서 제1115호 문단 B56, B58~B62, 106.
"""

UPFRONT_FEE = 1_200.0
LICENSE_YEARS = 4

# 문단 B58 의 세 기준. 셋을 모두 충족해야 접근권이다.
#   activity  — 지적재산에 유의적으로 영향을 미치는 활동을 기업이 할 것을 요구하거나 고객이 합리적으로 예상한다
#   exposed   — 고객이 그 활동의 긍정적·부정적 영향에 직접 노출된다
#   no_transfer — 그 활동이 고객에게 별도 재화나 용역을 이전하지 않는다
CONTRACTS = [
    {
        "name": "A. 캐릭터 상표 라이선스",
        "note": "기업이 캐릭터 애니메이션·광고를 계속 내보내 상표 가치를 유지한다",
        "activity": True,
        "exposed": True,
        "no_transfer": True,
        # 라이선스 기간 시작 = 계약일 = 1년차 1월 1일
        "start_year": 1,
    },
    {
        "name": "B. 완성 영화 방영 라이선스",
        "note": "영화는 완성돼 있고 기업이 내용을 바꿀 계획이 없다 (개별 기능성이 유의적, B59A)",
        "activity": False,
        "exposed": False,
        "no_transfer": True,
        # 라이선스 기간은 1년차 12월 1일에 시작하지만 방영용 원본 파일은 2년차 1월 10일에 넘긴다 (B61)
        "start_year": 1,
        "usable_year": 2,
    },
]

# B62 — 판단에서 빼는 요소. 두 계약 모두 같은 제약이 붙어 있다.
IGNORED_FACTORS = [
    "라이선스 기간 4년 (시간 제약)",
    "국내에서만 사용 (지역 제약)",
    "기업이 특허·상표 침해에 대응하겠다는 약속 (수행의무가 아니다)",
]


def nature(contract):
    if contract["activity"] and contract["exposed"] and contract["no_transfer"]:
        return "access"
    return "use"


def revenue_schedule(contract):
    years = range(1, LICENSE_YEARS + 2)
    schedule = {year: 0.0 for year in years}
    if nature(contract) == "access":
        # 기간에 걸쳐 이행 — 진행률은 경과 기간으로 본다 (B60, 문단 39~45)
        for i in range(LICENSE_YEARS):
            schedule[contract["start_year"] + i] = UPFRONT_FEE / LICENSE_YEARS
    else:
        # 한 시점에 이행 — 단, 고객이 사용할 수 있게 된 뒤에만 인식한다 (B61)
        schedule[contract.get("usable_year", contract["start_year"])] = UPFRONT_FEE
    return schedule


def fmt(value):
    return f"{value:>9,.1f}"


def mark(flag):
    return "충족" if flag else "미충족"


def main():
    print("[1] 문단 B58 세 기준 — 모두 충족해야 접근권")
    print(f"    {'계약':<18}{'⑴ 유의적 활동':>10}{'⑵ 직접 노출':>10}{'⑶ 별도 이전 없음':>12}  판단")
    for c in CONTRACTS:
        verdict = "접근권 → 기간에 걸쳐" if nature(c) == "access" else "사용권 → 한 시점"
        print(f"    {c['name']:<18}{mark(c['activity']):>10}{mark(c['exposed']):>10}"
              f"{mark(c['no_transfer']):>12}  {verdict}")
        print(f"      근거: {c['note']}")
    print()

    print("[2] 문단 B62 — 두 계약에 똑같이 붙어 있지만 판단에 넣지 않는 요소")
    for factor in IGNORED_FACTORS:
        print(f"    - {factor}")
    print()

    print("[3] 같은 계약금 1,200 의 연도별 수익")
    schedules = {c["name"]: revenue_schedule(c) for c in CONTRACTS}
    years = sorted(next(iter(schedules.values())))
    header = "".join(f"{f'{y}년차':>10}" for y in years)
    print(f"    {'계약':<18}{header}{'합계':>10}")
    for name, schedule in schedules.items():
        row = "".join(f"{fmt(schedule[y]):>10}" for y in years)
        print(f"    {name:<18}{row}{fmt(sum(schedule.values())):>10}")
    print()

    print("[4] 연말 계약부채 잔액 — 현금은 계약일에 이미 다 받았다 (문단 106)")
    print(f"    {'계약':<18}{header}")
    for name, schedule in schedules.items():
        received = 0.0
        recognised = 0.0
        row = ""
        for y in years:
            if y == 1:
                received = UPFRONT_FEE
            recognised += schedule[y]
            row += f"{fmt(received - recognised):>10}"
        print(f"    {name:<18}{row}")
    print()

    print("[5] 1년차만 놓고 본 두 계약")
    a = schedules[CONTRACTS[0]["name"]]
    b = schedules[CONTRACTS[1]["name"]]
    print(f"    A 수익 {fmt(a[1])}   B 수익 {fmt(b[1])}   차이 {fmt(a[1] - b[1])}")
    print(f"    2년차: A 수익 {fmt(a[2])}   B 수익 {fmt(b[2])}   차이 {fmt(b[2] - a[2])}")


if __name__ == "__main__":
    main()
