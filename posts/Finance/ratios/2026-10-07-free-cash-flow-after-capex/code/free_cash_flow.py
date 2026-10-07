"""잉여현금흐름(FCF) — 영업현금흐름에서 설비 투자를 뺀 뒤 남는 돈.

당기순이익이 120으로 똑같은 가상 회사 둘의 현금흐름표를 간접법으로 쌓는다.
가나전자는 운전자본이 조금 늘고 설비를 닳는 만큼만 산다. 다라물산은 매출채권과
재고가 크게 늘고 공장을 새로 짓는다. 순이익은 같아도 영업활동현금흐름과 FCF 가 갈린다.

FCF 는 회계기준서가 정한 항목이 아니다. 회사마다 정의가 달라 같은 회사의 숫자도
정의에 따라 움직이므로 [2] 에서 세 가지 정의로 같은 회사를 다시 계산한다.
[3] 은 설비 투자를 유지분과 확장분으로 나눠 본다(K-IFRS 제1007호 문단 51).

단순화: 법인세는 손익에 이미 반영됐고 현금 납부 시점 차이는 없다. 금액 단위는 억원.
"""
import platform
import sys

COMPANIES = {
    "가나전자": {
        "net_income": 120, "depreciation": 60,
        "receivable_change": 10, "inventory_change": 10,     # 운전자본 증가 → 현금 유출
        "capex": 70, "disposal": 20,                         # 설비 취득 / 설비 처분 수입
        "interest_paid": 15, "interest_in_financing": True,  # 이자 지급을 재무활동으로 분류
    },
    "다라물산": {
        "net_income": 120, "depreciation": 60,
        "receivable_change": 60, "inventory_change": 30,
        "capex": 150, "disposal": 0,
        "interest_paid": 15, "interest_in_financing": False, # 이자 지급을 영업활동으로 분류
    },
}


def operating_cash_flow(c: dict) -> int:
    """간접법. 순이익에 비현금 비용을 더하고 운전자본 증가분을 뺀다."""
    ocf = c["net_income"] + c["depreciation"] - c["receivable_change"] - c["inventory_change"]
    if c["interest_in_financing"]:
        # 이자를 재무활동에 넣는 회사는 순이익에서 빠진 이자비용을 영업활동에 되돌린다
        ocf += c["interest_paid"]
    return ocf


def fcf_simple(c: dict) -> int:
    """정의 A: 영업활동현금흐름 − 유형·무형자산 취득 (SEC C&DI 102.07 의 서술)."""
    return operating_cash_flow(c) - c["capex"]


def fcf_net_capex(c: dict) -> int:
    """정의 B: 영업활동현금흐름 − (취득 − 처분 수입). 처분이 많은 해에 커진다."""
    return operating_cash_flow(c) - (c["capex"] - c["disposal"])


def fcf_after_interest(c: dict) -> int:
    """정의 C: 이자 지급까지 뺀 값. 이자를 영업활동에 넣은 회사와 비교할 때 맞추는 용도."""
    ocf = operating_cash_flow(c)
    if c["interest_in_financing"]:
        ocf -= c["interest_paid"]
    return ocf - c["capex"]


def print_inputs() -> None:
    print("[0] 두 회사의 한 해 (억원)")
    cols = ["순이익", "감가상각", "매출채권 증가", "재고 증가", "설비 취득", "설비 처분", "이자 지급", "이자 분류"]
    print("  " + f"{'회사':<8}" + "".join(f"{c:>9}" for c in cols))
    for name, c in COMPANIES.items():
        where = "재무" if c["interest_in_financing"] else "영업"
        vals = [c["net_income"], c["depreciation"], c["receivable_change"], c["inventory_change"],
                c["capex"], c["disposal"], c["interest_paid"]]
        print("  " + f"{name:<8}" + "".join(f"{v:>11,}" for v in vals) + f"{where:>10}")
    print()


def print_statement() -> None:
    print("[1] 영업활동현금흐름(간접법)에서 FCF 까지")
    print(f"  {'항목':<22}{'가나전자':>10}{'다라물산':>10}")
    rows = [
        ("당기순이익", lambda c: c["net_income"]),
        ("+ 감가상각비", lambda c: c["depreciation"]),
        ("− 매출채권 증가", lambda c: -c["receivable_change"]),
        ("− 재고자산 증가", lambda c: -c["inventory_change"]),
        ("+ 이자 지급(재무로 분류 시)", lambda c: c["interest_paid"] if c["interest_in_financing"] else 0),
        ("= 영업활동현금흐름", operating_cash_flow),
        ("− 유형자산 취득", lambda c: -c["capex"]),
        ("= FCF", fcf_simple),
    ]
    for label, fn in rows:
        vals = "".join(f"{fn(c):>12,}" for c in COMPANIES.values())
        print(f"  {label:<24}{vals}")
    print()
    print(f"  {'영업활동현금흐름 ÷ 순이익':<24}"
          + "".join(f"{operating_cash_flow(c) / c['net_income']:>12.2f}" for c in COMPANIES.values()))
    print(f"  {'FCF ÷ 순이익':<24}"
          + "".join(f"{fcf_simple(c) / c['net_income']:>12.2f}" for c in COMPANIES.values()))
    print()


def print_definitions() -> None:
    print("[2] 같은 가나전자, 세 가지 FCF 정의")
    c = COMPANIES["가나전자"]
    print(f"  A  영업CF − 설비 취득                      {operating_cash_flow(c):,} − {c['capex']:,} = {fcf_simple(c):,}")
    print(f"  B  영업CF − (설비 취득 − 처분 수입)         {operating_cash_flow(c):,} − ({c['capex']:,} − {c['disposal']:,}) = {fcf_net_capex(c):,}")
    print(f"  C  (영업CF − 이자 지급) − 설비 취득        ({operating_cash_flow(c):,} − {c['interest_paid']:,}) − {c['capex']:,} = {fcf_after_interest(c):,}")
    print()


def print_maintenance_split() -> None:
    print("[3] 설비 투자를 유지분과 확장분으로 나누면 (K-IFRS 제1007호 문단 51)")
    print("    유지 투자는 그해 감가상각비만큼으로 둔다 — 닳은 만큼 다시 산다는 가정")
    print(f"  {'회사':<8}{'영업CF':>8}{'유지 투자':>10}{'확장 투자':>10}{'유지 후 FCF':>12}{'확장 후 FCF':>12}")
    for name, c in COMPANIES.items():
        ocf = operating_cash_flow(c)
        maintenance = min(c["capex"], c["depreciation"])
        growth = c["capex"] - maintenance
        print(f"  {name:<8}{ocf:>8,}{maintenance:>12,}{growth:>12,}{ocf - maintenance:>14,}{ocf - c['capex']:>14,}")
    print()


def main() -> None:
    print(f"Python {platform.python_version()} · {sys.platform}")
    print()
    print_inputs()
    print_statement()
    print_definitions()
    print_maintenance_split()


if __name__ == "__main__":
    main()
