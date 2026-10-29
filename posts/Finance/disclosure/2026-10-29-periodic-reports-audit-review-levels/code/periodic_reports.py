"""정기보고서에 실리는 숫자가 어디서 확정되고 어디서 아직 흔들리는지 계산한다.

가나전자·다라물산은 실재하지 않는 가상 회사다. 두 회사는 같은 12월 결산이고
연간 영업이익도 같지만 자산총액이 달라서, 분기보고서에 회계감사인 의견이
붙는지가 갈린다(자본시장법 시행령 제170조 제1항 제2호).
"""

import sys

# 보고서에 실리는 것은 분기별 금액이 아니라 '연초 이후 누계'다.
# 중간재무보고를 누계 기준으로 측정하라는 K-IFRS 제1034호(IAS 34)의 원칙에서 온다.
# 단위: 억원
CUMULATIVE = {
    "가나전자": {"1분기": 120, "반기": 260, "3분기": 350, "연간": 500},
    "다라물산": {"1분기": 180, "반기": 300, "3분기": 410, "연간": 500},
}

# 보고서별 회계감사인의 관여 수준. 자본시장법 시행령 제170조 제1항은
# 반기보고서에 '확인 및 의견표시'(검토)를 요구하고 분기보고서는 감사의견을
# 생략할 수 있게 하되, 금융기관과 직전 사업연도말 자산총액 5천억원 이상인
# 주권상장법인은 분기에도 반기와 같은 기준을 적용한다.
ASSET_THRESHOLD = 5_000  # 억원
COMPANIES = {
    "가나전자": {"자산총액": 8_200, "금융기관": False},
    "다라물산": {"자산총액": 2_400, "금융기관": False},
}


def quarterly_from_cumulative(cum):
    """누계 금액에서 분기 단독 금액을 뽑는다. 4분기는 연간에서 3분기 누계를 뺀 값뿐이다."""
    return {
        "1Q": cum["1분기"],
        "2Q": cum["반기"] - cum["1분기"],
        "3Q": cum["3분기"] - cum["반기"],
        "4Q": cum["연간"] - cum["3분기"],
    }


def assurance_level(name):
    """보고서별로 회계감사인이 어디까지 관여하는지 판정한다."""
    info = COMPANIES[name]
    quarterly_reviewed = info["금융기관"] or info["자산총액"] >= ASSET_THRESHOLD
    return {
        "1분기보고서": "검토" if quarterly_reviewed else "관여 없음",
        "반기보고서": "검토",
        "3분기보고서": "검토" if quarterly_reviewed else "관여 없음",
        "사업보고서": "감사",
    }


def print_inputs():
    print("[표 1] 보고서에 실리는 누계 영업이익 (단위: 억원)")
    print(f"{'회사':<8}{'1분기':>8}{'반기':>8}{'3분기':>8}{'연간':>8}")
    for name, cum in CUMULATIVE.items():
        print(
            f"{name:<8}{cum['1분기']:>8}{cum['반기']:>8}"
            f"{cum['3분기']:>8}{cum['연간']:>8}"
        )
    print()
    print("[표 2] 회사 정보")
    print(f"{'회사':<8}{'자산총액(억원)':>16}{'금융기관':>10}")
    for name, info in COMPANIES.items():
        print(f"{name:<8}{info['자산총액']:>16,}{('예' if info['금융기관'] else '아니오'):>10}")
    print()


def print_quarterly():
    print("[계산 1] 누계에서 뽑아낸 분기 단독 영업이익 (단위: 억원)")
    print(f"{'회사':<8}{'1Q':>7}{'2Q':>7}{'3Q':>7}{'4Q':>7}{'합계':>8}")
    for name, cum in CUMULATIVE.items():
        q = quarterly_from_cumulative(cum)
        total = sum(q.values())
        print(
            f"{name:<8}{q['1Q']:>7}{q['2Q']:>7}{q['3Q']:>7}{q['4Q']:>7}{total:>8}"
        )
    print()
    print("  연간 합계는 두 회사가 같지만 분기 흐름은 반대다.")
    print("  4Q 는 어느 보고서에도 단독으로 실리지 않고 '연간 - 3분기 누계'로만 나온다.")
    print()


def print_assurance():
    print("[계산 2] 보고서별 회계감사인 관여 수준")
    header = f"{'회사':<8}{'1분기':>10}{'반기':>10}{'3분기':>10}{'사업':>10}"
    print(header)
    for name in COMPANIES:
        level = assurance_level(name)
        print(
            f"{name:<8}{level['1분기보고서']:>10}{level['반기보고서']:>10}"
            f"{level['3분기보고서']:>10}{level['사업보고서']:>10}"
        )
    print()
    print(f"  판정 기준: 금융기관이거나 직전 사업연도말 자산총액 {ASSET_THRESHOLD:,}억원 이상")
    print("  이면 분기보고서도 반기와 같은 기준을 따른다.")
    print()


def print_restatement():
    """감사 과정에서 연간 금액이 바뀌면 그 차이가 전부 4분기로 몰린다."""
    name = "가나전자"
    cum = CUMULATIVE[name]
    provisional_year = cum["연간"]          # 영업(잠정)실적으로 먼저 알린 연간 금액
    audited_year = 472                      # 감사 후 사업보고서에 실린 확정 금액

    before = quarterly_from_cumulative(cum)
    after = quarterly_from_cumulative({**cum, "연간": audited_year})

    print(f"[계산 3] {name} — 잠정 연간 영업이익이 감사 후 바뀌면 (단위: 억원)")
    print(f"{'구분':<12}{'1Q':>7}{'2Q':>7}{'3Q':>7}{'4Q':>7}{'연간':>8}")
    print(f"{'잠정실적':<12}{before['1Q']:>7}{before['2Q']:>7}"
          f"{before['3Q']:>7}{before['4Q']:>7}{provisional_year:>8}")
    print(f"{'사업보고서':<12}{after['1Q']:>7}{after['2Q']:>7}"
          f"{after['3Q']:>7}{after['4Q']:>7}{audited_year:>8}")
    diff_year = audited_year - provisional_year
    diff_q4 = after["4Q"] - before["4Q"]
    print(f"{'차이':<12}{0:>7}{0:>7}{0:>7}{diff_q4:>7}{diff_year:>8}")
    print()
    print(f"  연간이 {abs(diff_year)}억원 줄었는데 1~3분기 누계는 그대로이므로")
    print(f"  차이 {abs(diff_q4)}억원이 전부 4Q 에 들어간다.")
    print(f"  연간은 {diff_year / provisional_year * 100:+.1f}% 바뀌었지만"
          f" 4Q 단독은 {before['4Q']}억원 → {after['4Q']}억원"
          f" ({(after['4Q'] / before['4Q'] - 1) * 100:+.1f}%) 로 움직인다.")
    print()


def main():
    print(f"Python {sys.version.split()[0]}")
    print()
    print_inputs()
    print_quarterly()
    print_assurance()
    print_restatement()


if __name__ == "__main__":
    main()
