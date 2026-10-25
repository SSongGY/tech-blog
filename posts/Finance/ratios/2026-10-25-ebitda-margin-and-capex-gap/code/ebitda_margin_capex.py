"""EBITDA 마진이 같은 가상 회사 세 곳에서 잉여현금흐름이 갈리는 과정.

금액 단위는 억원이다. 회사와 숫자는 전부 가상이며 실제 기업과 관계가 없다.
"""

from dataclasses import dataclass


@dataclass
class Company:
    name: str
    revenue: int              # 매출액
    ebitda: int               # 영업이익 + 감가상각비와 무형자산상각비
    depreciation: int         # 감가상각비와 무형자산상각비 합계
    rou_amortization: int     # 그중 사용권자산 상각분 (K-IFRS 제1116호)
    interest_paid: int        # 이자 지급액
    lease_interest: int       # 그중 리스부채에 붙은 이자
    lease_principal: int      # 리스부채 원금 상환액 (재무활동)
    tax_paid: int             # 법인세 납부액
    capex: int                # 유형·무형자산 취득 현금유출 (K-IFRS 제1007호 문단 16)

    @property
    def operating_income(self) -> int:
        return self.ebitda - self.depreciation

    @property
    def ebitda_margin(self) -> float:
        return self.ebitda / self.revenue * 100

    @property
    def operating_margin(self) -> float:
        return self.operating_income / self.revenue * 100

    @property
    def operating_cash_flow(self) -> int:
        """운전자본 변동이 없다고 두고 EBITDA에서 이자와 법인세만 뺀 값."""
        return self.ebitda - self.interest_paid - self.tax_paid

    @property
    def free_cash_flow(self) -> int:
        return self.operating_cash_flow - self.capex


COMPANIES = [
    # 장치산업. 설비가 크고 매년 다시 사야 한다
    Company("한솔소재", 1000, 200, 120, 0, 25, 0, 0, 12, 150),
    # 소프트웨어. 자산이 가볍다
    Company("너른소프트", 1000, 200, 15, 0, 3, 0, 0, 38, 20),
    # 물류. 설비의 상당 부분을 리스로 쓴다
    Company("벼리물류", 1000, 200, 90, 60, 18, 10, 55, 20, 40),
]


def rule(title):
    print()
    print(title)
    print("-" * 74)


def row(label, values, fmt="{:>12,}"):
    print(f"{label:<22}" + "".join(fmt.format(v) for v in values))


def main():
    names = [c.name for c in COMPANIES]

    rule("[1] 손익 — EBITDA 마진은 셋이 같다 (단위: 억원)")
    row("", names, "{:>12}")
    row("매출액", [c.revenue for c in COMPANIES])
    row("EBITDA", [c.ebitda for c in COMPANIES])
    row("EBITDA 마진(%)", [c.ebitda_margin for c in COMPANIES], "{:>12.1f}")
    row("감가상각비", [c.depreciation for c in COMPANIES])
    row("영업이익", [c.operating_income for c in COMPANIES])
    row("영업이익률(%)", [c.operating_margin for c in COMPANIES], "{:>12.1f}")

    rule("[2] EBITDA에서 현금이 남는 자리까지 (단위: 억원)")
    row("", names, "{:>12}")
    row("EBITDA", [c.ebitda for c in COMPANIES])
    row("(−) 이자 지급", [-c.interest_paid for c in COMPANIES])
    row("(−) 법인세 납부", [-c.tax_paid for c in COMPANIES])
    row("= 영업활동현금흐름", [c.operating_cash_flow for c in COMPANIES])
    row("(−) 자본적지출", [-c.capex for c in COMPANIES])
    row("= 잉여현금흐름", [c.free_cash_flow for c in COMPANIES])
    row("잉여현금흐름 마진(%)",
        [c.free_cash_flow / c.revenue * 100 for c in COMPANIES], "{:>12.1f}")
    row("현금전환율(%)",
        [c.free_cash_flow / c.ebitda * 100 for c in COMPANIES], "{:>12.1f}")

    rule("[3] 리스 원금까지 빼면 — 리스료는 자본적지출에 잡히지 않는다 (단위: 억원)")
    row("", names, "{:>12}")
    row("잉여현금흐름", [c.free_cash_flow for c in COMPANIES])
    row("(−) 리스부채 원금", [-c.lease_principal for c in COMPANIES])
    row("= 리스 반영 후", [c.free_cash_flow - c.lease_principal for c in COMPANIES])
    row("현금전환율(%)",
        [(c.free_cash_flow - c.lease_principal) / c.ebitda * 100 for c in COMPANIES],
        "{:>12.1f}")

    rule("[4] 자본적지출이 감가상각비를 덮는가 (배)")
    row("", names, "{:>12}")
    row("자본적지출", [c.capex for c in COMPANIES])
    row("감가상각비", [c.depreciation for c in COMPANIES])
    row("자본적지출÷감가상각", [c.capex / c.depreciation for c in COMPANIES], "{:>12.2f}")
    row("리스 제외 감가상각",
        [c.depreciation - c.rou_amortization for c in COMPANIES])
    row("리스 제외 기준 배수",
        [c.capex / (c.depreciation - c.rou_amortization) for c in COMPANIES],
        "{:>12.2f}")

    rule("[5] 벼리물류 — 같은 거래를 운용리스로 적었을 때 (단위: 억원)")
    cargo = COMPANIES[2]
    lease_payment = cargo.lease_principal + cargo.lease_interest
    # 운용리스로 처리하면 리스료 전액이 영업비용이고 사용권자산 상각·리스이자는 없다
    old_operating_income = cargo.operating_income + cargo.rou_amortization - lease_payment
    old_depreciation = cargo.depreciation - cargo.rou_amortization
    old_ebitda = old_operating_income + old_depreciation
    print(f"{'':<26}{'운용리스':>12}{'사용권자산':>12}{'차이':>12}")
    print(f"{'리스료 지급액':<26}{lease_payment:>12,}{0:>12,}{-lease_payment:>12,}")
    print(f"{'사용권자산 상각':<26}{0:>12,}{cargo.rou_amortization:>12,}"
          f"{cargo.rou_amortization:>12,}")
    print(f"{'리스부채 이자':<26}{0:>12,}{cargo.lease_interest:>12,}"
          f"{cargo.lease_interest:>12,}")
    print(f"{'영업이익':<26}{old_operating_income:>12,}{cargo.operating_income:>12,}"
          f"{cargo.operating_income - old_operating_income:>12,}")
    print(f"{'EBITDA':<26}{old_ebitda:>12,}{cargo.ebitda:>12,}"
          f"{cargo.ebitda - old_ebitda:>12,}")
    print(f"{'EBITDA 마진(%)':<26}{old_ebitda / cargo.revenue * 100:>12.1f}"
          f"{cargo.ebitda_margin:>12.1f}"
          f"{cargo.ebitda_margin - old_ebitda / cargo.revenue * 100:>12.1f}")

    rule("[6] 자본적지출을 감가상각비만큼만 쓴다고 보면 (단위: 억원)")
    row("", names, "{:>12}")
    row("영업활동현금흐름", [c.operating_cash_flow for c in COMPANIES])
    row("(−) 유지 지출 대용치", [-c.depreciation for c in COMPANIES])
    row("= 성장 제외 현금",
        [c.operating_cash_flow - c.depreciation for c in COMPANIES])
    row("매출액 대비(%)",
        [(c.operating_cash_flow - c.depreciation) / c.revenue * 100
         for c in COMPANIES], "{:>12.1f}")

    rule("[7] 가나전자 — 설비를 덜 사며 버틴 5년 (단위: 억원)")
    book_value = 500          # 설비 순장부금액 기초 잔액
    annual_capex = 50
    annual_depreciation = 100
    revenue = 800
    ebitda = 160              # 매출액 대비 20.0% 로 5년간 고정
    print(f"{'연차':<8}{'기초 장부':>12}{'자본적지출':>12}{'감가상각':>12}"
          f"{'기말 장부':>12}{'EBITDA 마진(%)':>16}")
    for year in range(1, 6):
        opening = book_value
        book_value = opening + annual_capex - annual_depreciation
        print(f"{year:<8}{opening:>12,}{annual_capex:>12,}"
              f"{-annual_depreciation:>12,}{book_value:>12,}"
              f"{ebitda / revenue * 100:>16.1f}")
    print(f"\n5년 누적 자본적지출 {annual_capex * 5}, 누적 감가상각 "
          f"{annual_depreciation * 5}, 순장부금액 500 → {book_value}")


if __name__ == "__main__":
    main()
