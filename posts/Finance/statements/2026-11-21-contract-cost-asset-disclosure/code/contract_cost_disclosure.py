"""가상 회사 카타서비스의 계약원가 자산 공시를 만든다.

기업회계기준서 제1115호 문단 127·128 이 요구하는 범주별 기말 잔액, 상각액, 손상차손을
연도별 원가 묶음(코호트)에서 계산하고, 문단 100 의 상각기간 변경과 문단 129 의 간편법
공시가 숫자를 어떻게 바꾸는지 본다. 숫자는 모두 가상이다. 금액 단위는 억원.
"""

import sys

# 범주별로 해마다 자산으로 둔 원가. 상각은 지출한 해부터 정액으로 한다고 둔다.
COMMISSION = {1: 120, 2: 150, 3: 180}      # 계약체결원가(영업 수수료), 4년
SETUP = {1: 80, 2: 60, 3: 90}              # 준비원가(계약이행원가), 5년
PRE_CONTRACT_Y3 = 30                       # 4년차에 시작할 예상 계약의 설계원가
COMMISSION_LIFE = 4
SETUP_LIFE = 5
SETUP_IMPAIRMENT_Y3 = 12                   # 3년차 고객 한 곳의 남은 대가가 모자람
REVISED_COMMISSION_LIFE = 3                # 4년차부터 고객 이탈이 빨라졌다
COMMISSION_Y4 = 200


def straight_line_rollforward(costs, life, year):
    """year 해의 기초 잔액, 증가, 상각, 기말 잔액(손상 전)을 돌려준다."""
    opening = additions = amortization = 0.0
    for paid_year, cost in costs.items():
        annual = cost / life
        used_before = max(0, min(life, year - paid_year))
        if paid_year < year:
            opening += cost - annual * used_before
        elif paid_year == year:
            additions += cost
        if paid_year <= year and used_before < life:
            amortization += annual
    return opening, additions, amortization, opening + additions - amortization


def print_row(label, opening, additions, amortization, impairment, closing):
    print(f"  {label:<14}{opening:8.1f}{additions:8.1f}{-amortization:8.1f}"
          f"{-impairment:8.1f}{closing:8.1f}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    print("[1] 3년차 계약원가 자산 변동 — 문단 128⑴⑵")
    print("  범주                기초      증가      상각      손상      기말")
    c = straight_line_rollforward(COMMISSION, COMMISSION_LIFE, 3)
    s = straight_line_rollforward(SETUP, SETUP_LIFE, 3)
    print_row("계약체결원가", c[0], c[1], c[2], 0, c[3])
    print_row("계약 전 원가", 0, PRE_CONTRACT_Y3, 0, 0, PRE_CONTRACT_Y3)
    setup_closing = s[3] - SETUP_IMPAIRMENT_Y3
    print_row("준비원가", s[0], s[1], s[2], SETUP_IMPAIRMENT_Y3, setup_closing)
    total_open = c[0] + s[0]
    total_add = c[1] + s[1] + PRE_CONTRACT_Y3
    total_amort = c[2] + s[2]
    total_close = c[3] + PRE_CONTRACT_Y3 + setup_closing
    print_row("합계", total_open, total_add, total_amort,
              SETUP_IMPAIRMENT_Y3, total_close)
    print("  계약 전 원가는 관련 계약이 시작되지 않아 아직 상각하지 않는다 (문단 99)\n")

    print("[2] 공시만으로 거꾸로 읽는 상각 속도 — 평균 잔액 = 기초 + 증가 ÷ 2")
    for label, amort, opening, add in (("계약체결원가", c[2], c[0], c[1]),
                                       ("준비원가", s[2], s[0], s[1])):
        average = opening + add / 2
        print(f"  {label:<10} 상각 {amort:6.1f} / 평균 잔액 {average:6.1f}"
              f" = {amort / average:5.1%}")
    print("  상각 방법(문단 127⑵)을 읽기 전에는 이 비율이 무엇을 뜻하는지 알 수 없다\n")

    print("[3] 4년차 계약체결원가 상각 — 상각기간 4년 → 3년 (문단 100)")
    print("  지출 연도   상각 대상 잔액  남은 기간(전)  상각(전)  남은 기간(후)  상각(후)")
    before_total = after_total = 0.0
    cohorts = {**COMMISSION, 4: COMMISSION_Y4}
    for paid_year, cost in cohorts.items():
        used = 4 - paid_year
        balance = cost - cost / COMMISSION_LIFE * used
        left_before = COMMISSION_LIFE - used
        left_after = max(REVISED_COMMISSION_LIFE - used, 1)
        before = balance / left_before
        after = balance / left_after
        before_total += before
        after_total += after
        print(f"  {paid_year}년차 {balance:12.1f} {left_before:10}년 {before:9.1f}"
              f" {left_after:11}년 {after:9.1f}")
    print(f"  합계{'':22}{before_total:22.1f}{after_total:22.1f}")
    print(f"  추정 변경으로 4년차 상각이 {after_total - before_total:+.1f} 늘었다"
          " — 회계추정치의 변경, 소급하지 않는다\n")

    print("[4] 3년차에 영업 수수료 180을 지급한 두 회사 — 문단 94 간편법과 129 공시")
    print("  회사          3년차 수수료 비용  3년차 말 체결원가 잔액  129 공시")
    print(f"  카타서비스 {c[2]:16.1f} {c[3]:20.1f}   간편법 미사용")
    print(f"  타파서비스 {COMMISSION[3]:16.1f} {0:20.1f}   간편법 사용 사실")
    print("  타파서비스는 계약이 1년이고 갱신 수수료를 다시 준다 — 상각기간 1년 이하")


if __name__ == "__main__":
    main()
