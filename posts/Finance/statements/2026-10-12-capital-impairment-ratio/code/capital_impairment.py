"""자본잠식률을 가상 회사로 계산한다.

자본잠식률 = (자본금 - 자본총계) / 자본금 x 100 (한국거래소 정기결산 유의사항, 2026-02)
금액 단위는 억원이다. 회사와 숫자는 모두 가상이다.
"""

import sys

UNIT = "억원"

# 같은 돈(100억)을 받고 상장했지만 액면을 다르게 정한 두 회사.
# 가나전자는 납입액 전부가 자본금이고, 다라물산은 대부분이 주식발행초과금이다.
COMPANIES = {
    "가나전자": {"shares": 2_000_000, "par_value": 5_000, "share_premium": 0.0},
    "다라물산": {"shares": 2_000_000, "par_value": 1_000, "share_premium": 80.0},
}

# 두 회사가 해마다 똑같이 낸 당기순손실
NET_LOSSES = [-30.0, -30.0, -30.0, -20.0]


def capital_stock(shares, par_value):
    # 자본금은 발행주식의 액면총액이다 (상법 제451조 제1항). 원 → 억원
    return shares * par_value / 100_000_000


def impairment_ratio(capital, equity):
    # 자본총계가 자본금 이상이면 잠식이 아니다. 음수 비율을 0으로 둔다
    if equity >= capital:
        return 0.0
    return (capital - equity) / capital * 100


def krx_status(ratio, equity, previous_ratio):
    # 유가증권시장 기준(투자자용 안내 자료의 요약). 사업연도말 하나만 본다
    if equity <= 0:
        return "자본전액잠식 → 상장폐지 절차"
    if ratio >= 50 and previous_ratio >= 50:
        return "2년 연속 50% 이상 → 실질심사"
    if ratio >= 50:
        return "50% 이상 → 관리종목"
    if ratio > 0:
        return "부분잠식 (지정 사유 아님)"
    return "-"


def print_definition():
    print("[1] 자본잠식률의 정의 (한국거래소 정기결산 유의사항)")
    print("    자본잠식률 = (자본금 - 자본총계) / 자본금 x 100")
    print("    자본총계 >= 자본금 : 잠식 없음 (0%)")
    print("    0 < 자본총계 < 자본금 : 부분잠식")
    print("    자본총계 <= 0 : 완전잠식(자본전액잠식) — 잠식률 100% 이상")
    print()


def simulate_losses():
    print("[2] 납입액이 같고 액면만 다른 두 회사에 같은 손실을 쌓는다")
    for name, info in COMPANIES.items():
        capital = capital_stock(info["shares"], info["par_value"])
        print(
            f"    {name}: 발행주식 {info['shares']:,}주 x 액면 {info['par_value']:,}원"
            f" = 자본금 {capital:.0f}{UNIT}, 주식발행초과금 {info['share_premium']:.0f}{UNIT}"
        )
    for name, info in COMPANIES.items():
        capital = capital_stock(info["shares"], info["par_value"])
        retained = 0.0
        previous_ratio = 0.0
        print()
        print(f"    {name}    연도   순손실   결손금   자본총계   잠식률   상태")
        for year, loss in enumerate(NET_LOSSES, start=1):
            retained += loss
            equity = capital + info["share_premium"] + retained
            ratio = impairment_ratio(capital, equity)
            status = krx_status(ratio, equity, previous_ratio)
            print(f"              {year}년차 {loss:>7.0f} {retained:>8.0f} {equity:>10.0f}"
                  f" {ratio:>7.0f}%   {status}")
            previous_ratio = ratio
    print()
    print("    결손금이 자본금 외의 자본(주식발행초과금 등)보다 커진 뒤부터 잠식률이 0을 넘는다")
    print()


def resolve_impairment():
    # 가나전자 3년차 말: 자본금 100, 결손금 -90, 자본총계 10
    shares = COMPANIES["가나전자"]["shares"]
    par_value = COMPANIES["가나전자"]["par_value"]
    capital = capital_stock(shares, par_value)
    deficit = sum(NET_LOSSES[:3])
    equity = capital + deficit

    print("[3] 가나전자 3년차 말 잠식을 푸는 세 가지 방법")
    print(f"    출발점: 자본금 {capital:.0f}, 결손금 {deficit:.0f}, 자본총계 {equity:.0f}{UNIT},"
          f" 주식 {shares:,}주, 잠식률 {impairment_ratio(capital, equity):.0f}%")
    print(f"    {'방법':<26}{'주식 수':>12}{'자본금':>8}{'결손금':>8}{'자본총계':>9}{'잠식률':>8}{'주당 순자산':>12}")

    def row(label, n_shares, cap, def_, eq):
        bps = eq * 100_000_000 / n_shares
        print(f"    {label:<26}{n_shares:>12,}{cap:>8.0f}{def_:>8.0f}{eq:>9.0f}"
              f"{impairment_ratio(cap, eq):>7.0f}%{bps:>12,.0f}원")

    row("그대로", shares, capital, deficit, equity)

    # 10주를 1주로 병합하는 무상감자. 줄어든 자본금 90은 감자차익이 되어 결손금을 메운다
    merged = shares // 10
    reduced_capital = capital_stock(merged, par_value)
    gain_on_reduction = capital - reduced_capital
    row("무상감자 10:1 (결손 보전)", merged, reduced_capital, deficit + gain_on_reduction, equity)

    # 액면가로 1,000,000주 유상증자 (50억 납입)
    new_shares = 1_000_000
    raised = capital_stock(new_shares, par_value)
    row("유상증자 50억 (액면 발행)", shares + new_shares, capital + raised, deficit, equity + raised)

    # 감자 후 같은 증자
    row("감자 10:1 후 유상증자 50억", merged + new_shares, reduced_capital + raised,
        deficit + gain_on_reduction, equity + raised)
    print("    무상감자는 자본총계를 바꾸지 않는다 — 자본금만 자본총계 아래로 낮춘다")
    print("    증자만 하면 자본금도 같이 늘어 50억을 넣고도 잠식률이 50% 아래로 내려가지 않는다")
    print()


def consolidated_basis():
    print("[4] 연결재무제표 기준 — 비지배지분을 뺀 자본총계로 계산한다")
    capital = 100.0
    controlling = 45.0
    non_controlling = 15.0
    total = controlling + non_controlling
    print(f"    마바화학 연결: 자본금 {capital:.0f}, 지배기업 소유주지분 {controlling:.0f},"
          f" 비지배지분 {non_controlling:.0f}, 자본총계 {total:.0f}{UNIT}")
    print(f"    자본총계 전체로 계산      : 잠식률 {impairment_ratio(capital, total):.0f}%")
    print(f"    비지배지분을 빼고 계산    : 잠식률 {impairment_ratio(capital, controlling):.0f}%"
          "  ← 거래소가 쓰는 값")
    print()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print_definition()
    simulate_losses()
    resolve_impairment()
    consolidated_basis()


if __name__ == "__main__":
    main()
