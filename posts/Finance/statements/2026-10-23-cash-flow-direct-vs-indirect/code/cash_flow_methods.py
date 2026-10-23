"""가상 회사 가나전자의 영업활동 현금흐름을 직접법과 간접법으로 각각 만든다.

두 방법은 서술 방식만 다르고 끝 숫자는 같다. 그 사실을 계산으로 확인하고,
직접법으로 환산할 때 계정마다 솎아내야 하는 것들이 무엇인지 드러낸다.
금액 단위는 억원이고 파이썬 표준 라이브러리만 쓴다.
"""

import sys

# ── 포괄손익계산서 (당기) ────────────────────────────────────────────
SALES = 2400                 # 매출액
COGS = 1560                  # 매출원가
SGA_DEPRECIATION = 180       # 판관비 중 감가상각비
SGA_SALARY = 150             # 판관비 중 급여
SGA_OTHER = 90               # 판관비 중 그 밖의 비용
SGA_BAD_DEBT = 25            # 그 밖의 비용 안에 들어 있는 대손상각비
GAIN_ON_DISPOSAL = 30        # 유형자산처분이익 (투자활동 관련)
FX_LOSS = 15                 # 외화장기차입금 환산손실 (비현금)
INTEREST_EXPENSE = 60        # 이자비용 (재무활동으로 분류하기로 했다)
TAX_EXPENSE = 90             # 법인세비용

# ── 재무상태표 변동 (증가가 +) ──────────────────────────────────────
D_AR_NET = 220               # 매출채권 순액
D_INVENTORY = -60            # 재고자산
D_PREPAID = 5                # 선급비용
D_ACCOUNTS_PAYABLE = 40      # 매입채무
D_ACCRUED_SALARY = 10        # 미지급급여
D_DEFERRED_TAX = 20          # 이연법인세부채
D_TAX_PAYABLE = 5            # 미지급법인세

# [5] 에서만 쓴다 — 매입채무 증가분 가운데 설비 취득 대금인 몫
PAYABLE_FOR_EQUIPMENT = 15


def line(label, value, indent=0, width=34):
    pad = " " * indent
    return f"    {pad}{label:<{width - indent}}{value:>10,.0f}"


def income_statement():
    sga = SGA_DEPRECIATION + SGA_SALARY + SGA_OTHER
    operating = SALES - COGS - sga
    pretax = operating + GAIN_ON_DISPOSAL - FX_LOSS - INTEREST_EXPENSE
    net = pretax - TAX_EXPENSE
    return {"판관비": sga, "영업이익": operating, "법인세차감전순이익": pretax, "당기순이익": net}


def indirect_method(d_payable):
    """당기순이익에서 출발해 비현금·비영업 항목을 걷어낸다."""
    net = income_statement()["당기순이익"]
    noncash = [
        ("감가상각비", SGA_DEPRECIATION),
        ("외화환산손실", FX_LOSS),
        ("이자비용", INTEREST_EXPENSE),
        ("법인세비용", TAX_EXPENSE),
        ("유형자산처분이익", -GAIN_ON_DISPOSAL),
    ]
    working = [
        ("매출채권의 증가", -D_AR_NET),
        ("재고자산의 감소", -D_INVENTORY),
        ("선급비용의 증가", -D_PREPAID),
        ("매입채무의 증가", d_payable),
        ("미지급급여의 증가", D_ACCRUED_SALARY),
    ]
    generated = net + sum(v for _, v in noncash) + sum(v for _, v in working)
    return net, noncash, working, generated


def direct_method(d_payable):
    """총현금유입과 총현금유출을 주요 항목별로 뽑는다."""
    # 제각이 없으면 회수액은 매출에서 매출채권 순액 증가와 대손상각비를 함께 뺀 값이다
    from_customers = SALES - D_AR_NET - SGA_BAD_DEBT
    purchases = COGS + D_INVENTORY          # 재고 변동은 장부금액 기준이다
    to_suppliers = purchases - d_payable
    to_employees = SGA_SALARY - D_ACCRUED_SALARY
    to_others = (SGA_OTHER - SGA_BAD_DEBT) + D_PREPAID
    rows = [
        ("고객으로부터 유입된 현금", from_customers),
        ("공급자에 대한 현금유출", -to_suppliers),
        ("종업원에 대한 현금유출", -to_employees),
        ("그 밖의 영업비용 현금유출", -to_others),
    ]
    return rows, sum(v for _, v in rows)


def tax_paid():
    # 법인세비용 가운데 이연분과 아직 내지 않은 몫을 빼면 실제로 낸 금액이 남는다
    return TAX_EXPENSE - D_DEFERRED_TAX - D_TAX_PAYABLE


def main():
    print(f"[0] 환경 — Python {sys.version.split()[0]}")
    print("    가상 회사 가나전자. 금액 단위는 억원이다.")
    print("    이자지급은 재무활동, 법인세납부는 영업활동으로 분류했다.")

    inc = income_statement()
    print("\n[1] 포괄손익계산서 — 한 해 동안 벌었다고 적힌 숫자")
    print(line("매출액", SALES))
    print(line("매출원가", -COGS))
    print(line("판매비와관리비", -inc["판관비"]))
    print(line("감가상각비", SGA_DEPRECIATION, indent=2))
    print(line("급여", SGA_SALARY, indent=2))
    print(line("그 밖의 비용 (대손상각비 25 포함)", SGA_OTHER, indent=2))
    print(line("영업이익", inc["영업이익"]))
    print(line("유형자산처분이익", GAIN_ON_DISPOSAL))
    print(line("외화환산손실", -FX_LOSS))
    print(line("이자비용", -INTEREST_EXPENSE))
    print(line("법인세비용", -TAX_EXPENSE))
    print(line("당기순이익", inc["당기순이익"]))

    print("\n[2] 재무상태표 변동 — 영업과 맞물린 계정만 추렸다")
    for label, value in [
        ("매출채권 (순액)", D_AR_NET),
        ("재고자산", D_INVENTORY),
        ("선급비용", D_PREPAID),
        ("매입채무", D_ACCOUNTS_PAYABLE),
        ("미지급급여", D_ACCRUED_SALARY),
        ("이연법인세부채", D_DEFERRED_TAX),
        ("미지급법인세", D_TAX_PAYABLE),
    ]:
        print(line(label, value))

    paid = tax_paid()
    net, noncash, working, generated = indirect_method(D_ACCOUNTS_PAYABLE)
    print("\n[3] 간접법 — 당기순이익에서 거꾸로 걷어낸다")
    print(line("당기순이익", net))
    for label, value in noncash:
        print(line(label, value, indent=2))
    for label, value in working:
        print(line(label, value, indent=2))
    print(line("영업에서 창출된 현금", generated))
    print(line("법인세의 납부", -paid))
    print(line("영업활동 순현금흐름", generated - paid))

    rows, generated_d = direct_method(D_ACCOUNTS_PAYABLE)
    print("\n[4] 직접법 — 들어온 현금과 나간 현금을 항목별로 적는다")
    for label, value in rows:
        print(line(label, value))
    print(line("영업에서 창출된 현금", generated_d))
    print(line("법인세의 납부", -paid))
    print(line("영업활동 순현금흐름", generated_d - paid))
    print(f"\n    두 방법의 영업에서 창출된 현금: {generated:,.0f} / {generated_d:,.0f}"
          f"  → 일치 {generated == generated_d}")
    print(f"    당기순이익 {net:,.0f} 과 영업활동 순현금흐름 {generated - paid:,.0f} 의 차이는"
          f" {generated - paid - net:,.0f} 이다")

    print("\n[5] 매입채무 증가 40 가운데 15 가 설비 취득 대금이었다면")
    clean = D_ACCOUNTS_PAYABLE - PAYABLE_FOR_EQUIPMENT
    _, _, _, generated_fix = indirect_method(clean)
    _, generated_d_fix = direct_method(clean)
    print(line("섞인 채로 둔 영업활동 순현금흐름", generated - paid))
    print(line("설비 몫을 걷어낸 간접법", generated_fix - paid))
    print(line("설비 몫을 걷어낸 직접법", generated_d_fix - paid))
    print(line("부풀려졌던 금액", (generated - paid) - (generated_fix - paid)))
    print("    설비 대금은 투자활동이므로 영업활동 운전자본 변동에 넣어서는 안 된다.")


if __name__ == "__main__":
    main()
