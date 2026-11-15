"""획득가치관리(EVM) 지표를 가상 프로젝트로 직접 계산한다.

공식은 GAO-20-195G Table 22·23 과 EAC 일반식(265쪽)을 그대로 옮겼다.
  CV = BCWP - ACWP          SV = BCWP - BCWS
  CPI = BCWP / ACWP         SPI = BCWP / BCWS
  EAC = ACWP + (BAC - BCWP) / 효율 지수
  TCPI = (BAC - BCWP) / (목표 - ACWP)       목표는 BAC 또는 EAC
  VAC = BAC - EAC

1) GAO 철로 예시 검산 — 4주·4마일·400만 달러
2) 가상 프로젝트 월별 누계와 5개월 시점 지표
3) EAC 세 식을 5·8개월 시점에 계산해 실제 최종 원가와 비교
4) 완료 시점의 SPI·SV — 3개월 늦었는데 1.0·0 으로 돌아간다
"""

BAC = 1000  # 총 예산, 단위 백만 원
PLANNED_MONTHS = 10

# 계획: 10개월 동안 매달 100씩 고르게 쓴다
monthly_planned = [100] * PLANNED_MONTHS
# 실제: 13개월 걸렸다. 매달 끝낸 일의 예산 가치(EV)와 실제로 쓴 돈(AC)
monthly_earned = [60, 80, 90, 80, 70, 90, 100, 100, 100, 90, 80, 40, 20]
monthly_actual = [70, 95, 100, 95, 85, 100, 110, 105, 105, 95, 85, 45, 25]


def cumulative(values, months):
    total, result = 0, []
    for m in range(months):
        total += values[m] if m < len(values) else 0
        result.append(total)
    return result


def indicators(pv, ev, ac, bac):
    cpi = ev / ac
    spi = ev / pv
    return {
        "SV": ev - pv,
        "CV": ev - ac,
        "SPI": spi,
        "CPI": cpi,
        # 효율 지수만 바꿔 끼우는 일반식 하나로 세 EAC 를 만든다
        "EAC(1.0)": ac + (bac - ev) / 1.0,
        "EAC(CPI)": ac + (bac - ev) / cpi,
        "EAC(CPI×SPI)": ac + (bac - ev) / (cpi * spi),
        "TCPI(BAC)": (bac - ev) / (bac - ac),
    }


def print_railroad_check():
    print("[1] GAO 철로 예시 — 4마일·4주·400만 달러, 3주 뒤 1마일·200만 달러")
    bac, pv, ev, ac = 4.0, 3.0, 1.0, 2.0  # 백만 달러
    cpi, spi = ev / ac, ev / pv
    print(f"  PV {pv}  EV {ev}  AC {ac}")
    print(f"  CPI {cpi:.3f}  SPI {spi:.3f}")
    print(f"  EAC = BAC / CPI = {bac / cpi:.1f} 백만 달러")
    print(f"  기간 = 4주 / SPI = {4 / spi:.1f} 주")
    print()


def print_monthly_table():
    months = len(monthly_earned)
    pv = cumulative(monthly_planned, months)
    ev = cumulative(monthly_earned, months)
    ac = cumulative(monthly_actual, months)
    print(f"[2] 월별 누계 — BAC {BAC}, 계획 {PLANNED_MONTHS}개월")
    print("  월 |   PV |   EV |   AC |   SV |   CV |   SPI |   CPI")
    for m in range(months):
        print(
            f"  {m + 1:>2} | {pv[m]:>4} | {ev[m]:>4} | {ac[m]:>4} | "
            f"{ev[m] - pv[m]:>4} | {ev[m] - ac[m]:>4} | "
            f"{ev[m] / pv[m]:>5.3f} | {ev[m] / ac[m]:>5.3f}"
        )
    print()
    return pv, ev, ac


def print_status(month, pv, ev, ac):
    m = month - 1
    result = indicators(pv[m], ev[m], ac[m], BAC)
    print(f"  [{month}개월 시점] PV {pv[m]}  EV {ev[m]}  AC {ac[m]}")
    for name, value in result.items():
        print(f"    {name:<14} {value:>9.3f}")
    eac_cpi = result["EAC(CPI)"]
    print(f"    {'ETC(CPI)':<14} {eac_cpi - ac[m]:>9.3f}")
    print(f"    {'VAC(CPI)':<14} {BAC - eac_cpi:>9.3f}")
    print(f"    {'TCPI-CPI':<14} {result['TCPI(BAC)'] - result['CPI']:>9.3f}")
    print(f"    {'기간 추정':<12} {PLANNED_MONTHS / result['SPI']:>9.3f} 개월 (계획 기간 / SPI)")
    print()


def main():
    print_railroad_check()
    pv, ev, ac = print_monthly_table()

    print("[3] 시점별 지표와 EAC — 실제 최종 원가는", ac[-1])
    for month in (3, 5, 8):
        print_status(month, pv, ev, ac)

    # 대수적으로 AC + (BAC-EV)/CPI 는 BAC/CPI 와 같다 — 숫자로 확인한다
    m = 4
    cpi = ev[m] / ac[m]
    print("  검산: 5개월 시점 BAC / CPI =", f"{BAC / cpi:.3f}")
    print()

    print("[4] 완료 시점 — 실제 완료 13개월, 계획 10개월")
    last = len(ev) - 1
    print(f"  SV  = {ev[last] - pv[last]}")
    print(f"  SPI = {ev[last] / pv[last]:.3f}")
    print(f"  CV  = {ev[last] - ac[last]}")
    print(f"  CPI = {ev[last] / ac[last]:.3f}")


if __name__ == "__main__":
    main()
