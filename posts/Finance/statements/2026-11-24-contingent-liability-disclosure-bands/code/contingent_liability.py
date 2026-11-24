"""우발부채 공시 — 기업회계기준서 제1037호 문단 23·25~30·84·86·91·92.

가상 회사 마바건설이 분쟁 네 건을 안고 있다. 해마다 연말에 각 건의 유출 가능성과
금액 추정 가능 여부를 다시 평가하고(문단 30), 그 결과로 재무상태표와 주석이
어떻게 바뀌는지 계산한다. 숫자와 확률은 계산 원리를 보이려고 만든 가정이며
단위는 억원이다.
"""

# 기준서에는 '희박'의 수치 기준이 없다. 구간을 나눠 보이려고 둔 이 예제만의 가정이다.
REMOTE_BELOW = 0.05

CASES = {
    "A": "하도급 대금 분쟁",
    "B": "환경 과징금",
    "C": "제품 결함 집단소송",
    "D": "공사 지연 중재",
}

# 연말 평가: (유출 가능성, 추정 금액 또는 None, 공시가 분쟁에 현저히 불리한가, 종결 여부)
# 금액 None 은 신뢰성 있게 추정할 수 없는 극히 드문 경우(문단 25·26)다.
ASSESSMENTS = {
    2025: {
        "A": (0.03, 120.0, False, False),
        "B": (0.40, 80.0, False, False),
        "C": (0.60, None, False, False),
        "D": (0.20, 200.0, False, False),
    },
    2026: {
        "A": (0.30, 120.0, False, False),
        "B": (0.70, 80.0, False, False),
        "C": (0.60, 150.0, False, False),
        "D": (0.35, 200.0, True, False),
    },
    2027: {
        "A": (0.60, 120.0, False, False),
        "B": (1.00, 80.0, False, True),      # 과징금을 내고 종결
        "C": (0.60, 150.0, False, False),
        "D": (0.00, 0.0, False, True),       # 중재 신청 취하로 종결
    },
}


def classify(prob, amount, prejudicial, closed):
    """한 건을 연말에 어디로 보낼지 정한다."""
    if closed:
        return "종결", 0.0
    if prob > 0.5 and amount is not None:            # 문단 14·23
        return "충당부채", amount
    if prob < REMOTE_BELOW:                          # 문단 28·86 — 희박하면 공시도 안 함
        return "공시 안 함", 0.0
    if prejudicial:                                  # 문단 92
        return "우발부채 — 금액 생략, 특성·사유만 공시", 0.0
    if amount is None:                               # 문단 26·91
        return "우발부채 — 추정 불가 사실 공시", 0.0
    return "우발부채", amount                        # 문단 86⑴


def section_yearly():
    print("[1] 연말마다 다시 하는 평가 — 건별 분류 (문단 23·26·28·30·86·91·92)")
    for year, cases in ASSESSMENTS.items():
        provision = disclosed = 0.0
        print(f"  {year} 말")
        for key, (prob, amount, prejudicial, closed) in cases.items():
            label, value = classify(prob, amount, prejudicial, closed)
            shown = f"{value:>6.0f}" if value else "     —"
            print(f"    {key} {CASES[key]:<12} 유출 가능성 {prob:>4.0%}  {shown}  {label}")
            if label == "충당부채":
                provision += value
            elif label == "우발부채":
                disclosed += value
        print(f"    → 재무상태표 충당부채 {provision:.0f} / 주석 우발부채 금액 {disclosed:.0f}")
    print()


def provision_balances():
    balances = {}
    for year, cases in ASSESSMENTS.items():
        balances[year] = {
            key: classify(*cases[key])[1] if classify(*cases[key])[0] == "충당부채" else 0.0
            for key in cases
        }
    return balances


def section_rollforward():
    print("[2] 충당부채 변동표 (문단 84) — 우발부채가 넘어온 금액은 '추가'에 들어간다")
    balances = provision_balances()
    prev = {key: 0.0 for key in CASES}
    print(f"  {'연도':>4}{'기초':>8}{'추가':>8}{'사용':>8}{'환입':>8}{'기말':>8}  당기손익")
    for year, cases in ASSESSMENTS.items():
        added = used = reversed_ = 0.0
        for key in CASES:
            before, after = prev[key], balances[year][key]
            closed = cases[key][3]
            if closed and before:
                used += before                       # 종결하며 낸 돈은 사용(문단 61)
            elif after > before:
                added += after - before
            elif after < before:
                reversed_ += before - after
        opening, closing = sum(prev.values()), sum(balances[year].values())
        print(f"  {year:>4}{opening:>8.0f}{added:>8.0f}{used:>8.0f}{reversed_:>8.0f}{closing:>8.0f}"
              f"  {reversed_ - added:>+6.0f}")
        prev = balances[year]
    print()


def section_carryover():
    print("[3] 작년 주석이 올해 장부로 넘어온 경로")
    for year in (2026, 2027):
        before, now = ASSESSMENTS[year - 1], ASSESSMENTS[year]
        for key in CASES:
            label_before, value_before = classify(*before[key])
            label_now, value_now = classify(*now[key])
            if label_before.startswith("우발부채") or label_before == "공시 안 함":
                if label_now == "충당부채":
                    note = f"{value_before:.0f}" if value_before else "금액 없음"
                    print(f"  {year - 1} 주석 {key}({note}) → {year} 충당부채 {value_now:.0f}"
                          f"   [{label_before}]")
    print("  주석에 금액이 없던 C 가 이듬해 150 으로 장부에 올랐다")


if __name__ == "__main__":
    section_yearly()
    section_rollforward()
    section_carryover()
