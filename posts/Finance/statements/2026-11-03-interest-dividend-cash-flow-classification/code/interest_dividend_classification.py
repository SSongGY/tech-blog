"""이자·배당금 현금흐름 분류 선택이 영업활동현금흐름을 어떻게 가르는지 계산한다.

기업회계기준서 제1007호 문단 31~34 는 이자지급·이자수입·배당금수입·배당금지급을
어느 활동으로 분류할지에 선택지를 둔다. 같은 거래, 같은 현금 순증감에서
세 칸의 금액만 달라진다는 것을 가상 회사 둘로 보인다.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Company:
    """단위는 억원. 모든 금액은 그 해에 실제로 오간 현금이다."""

    name: str
    core_operating: float  # 이자·배당 항목을 뺀 영업활동현금흐름
    interest_paid: float
    interest_received: float
    dividend_received: float
    dividend_paid: float
    capex: float
    borrowing_net: float
    net_income: float
    total_borrowing: float


# 가나전자: 차입이 많고 여유자금이 적다. 다라물산: 차입이 더 많고 이자수입은 거의 없다.
GANA = Company(
    name="가나전자",
    core_operating=202.0,
    interest_paid=45.0,
    interest_received=8.0,
    dividend_received=5.0,
    dividend_paid=40.0,
    capex=110.0,
    borrowing_net=60.0,
    net_income=120.0,
    total_borrowing=500.0,
)

DARA = Company(
    name="다라물산",
    core_operating=190.0,
    interest_paid=60.0,
    interest_received=4.0,
    dividend_received=0.0,
    dividend_paid=30.0,
    capex=95.0,
    borrowing_net=80.0,
    net_income=96.0,
    total_borrowing=720.0,
)


@dataclass(frozen=True)
class Policy:
    """문단 33·34 가 허용하는 분류 조합 하나."""

    label: str
    interest_paid_to: str  # "영업" 또는 "재무"
    interest_received_to: str  # "영업" 또는 "투자"
    dividend_received_to: str  # "영업" 또는 "투자"
    dividend_paid_to: str  # "재무" 또는 "영업"


# 문단 33 은 이자지급·이자수입·배당금수입을 묶어 두 갈래로 적고,
# 문단 34 는 배당금지급을 따로 두 갈래로 적는다.
OPERATING_HEAVY = Policy("영업 집중형", "영업", "영업", "영업", "재무")
NATURE_SPLIT = Policy("성격 분리형", "재무", "투자", "투자", "재무")


def statement(c: Company, p: Policy) -> dict[str, float]:
    """세 활동의 현금흐름을 분류 정책에 따라 집계한다."""
    buckets = {"영업": c.core_operating, "투자": -c.capex, "재무": c.borrowing_net}
    buckets[p.interest_paid_to] -= c.interest_paid
    buckets[p.interest_received_to] += c.interest_received
    buckets[p.dividend_received_to] += c.dividend_received
    buckets[p.dividend_paid_to] -= c.dividend_paid
    buckets["합계"] = buckets["영업"] + buckets["투자"] + buckets["재무"]
    return buckets


def to_operating_heavy(c: Company, p: Policy, operating: float) -> float:
    """어떤 정책으로 작성된 영업활동현금흐름을 영업 집중형 기준으로 되돌린다.

    문단 31 이 이자·배당금을 각각 별도로 공시하게 하므로 이 환산이 가능하다.
    """
    adjusted = operating
    if p.interest_paid_to != "영업":
        adjusted -= c.interest_paid
    if p.interest_received_to != "영업":
        adjusted += c.interest_received
    if p.dividend_received_to != "영업":
        adjusted += c.dividend_received
    if p.dividend_paid_to == "영업":  # 영업에서 빠져 있던 것을 되돌린다
        adjusted += c.dividend_paid
    return adjusted


def row(cells: list[str], widths: list[int]) -> str:
    return "".join(cell.rjust(w) for cell, w in zip(cells, widths))


def print_policies() -> None:
    print("[1] 제1007호 문단 33·34 가 허용하는 분류 — 금융회사가 아닌 기업")
    w = [18, 12, 12]
    print(row(["항목", "기본", "대체"], w))
    print("-" * sum(w))
    for item, primary, alt in [
        ("이자지급", "영업", "재무"),
        ("이자수입", "영업", "투자"),
        ("배당금수입", "영업", "투자"),
        ("배당금지급", "재무", "영업"),
    ]:
        print(row([item, primary, alt], w))
    print()


def print_two_statements(c: Company) -> None:
    a = statement(c, OPERATING_HEAVY)
    b = statement(c, NATURE_SPLIT)
    print(f"[2] {c.name} — 같은 해, 같은 거래를 두 가지로 작성 (단위: 억원)")
    w = [16, 14, 14, 10]
    print(row(["활동", OPERATING_HEAVY.label, NATURE_SPLIT.label, "차이"], w))
    print("-" * sum(w))
    for key in ("영업", "투자", "재무", "합계"):
        print(row([key, f"{a[key]:.1f}", f"{b[key]:.1f}", f"{b[key] - a[key]:+.1f}"], w))
    print()


def print_metrics(c: Company) -> None:
    a = statement(c, OPERATING_HEAVY)["영업"]
    b = statement(c, NATURE_SPLIT)["영업"]
    print(f"[3] {c.name} — 영업활동현금흐름을 쓰는 지표가 같이 움직인다")
    w = [26, 14, 14, 10]
    print(row(["지표", OPERATING_HEAVY.label, NATURE_SPLIT.label, "차이"], w))
    print("-" * sum(w))
    pairs = [
        ("영업활동현금흐름", a, b),
        ("영업현금흐름 / 당기순이익", a / c.net_income, b / c.net_income),
        ("잉여현금흐름 (OCF−CAPEX)", a - c.capex, b - c.capex),
        ("영업현금흐름 / 총차입금", a / c.total_borrowing, b / c.total_borrowing),
    ]
    for label, x, y in pairs:
        print(row([label, f"{x:.3f}", f"{y:.3f}", f"{y - x:+.3f}"], w))
    print()


def print_cross_company() -> None:
    gana_policy, dara_policy = OPERATING_HEAVY, NATURE_SPLIT
    gana = statement(GANA, gana_policy)["영업"]
    dara = statement(DARA, dara_policy)["영업"]
    print("[4] 정책이 서로 다른 두 회사를 그대로 비교하면 순위가 뒤집힌다")
    w = [14, 16, 16, 18]
    print(row(["회사", "채택한 분류", "공시된 OCF", "영업 집중형 환산"], w))
    print("-" * sum(w))
    for c, p, value in ((GANA, gana_policy, gana), (DARA, dara_policy, dara)):
        print(row([c.name, p.label, f"{value:.1f}", f"{to_operating_heavy(c, p, value):.1f}"], w))
    print()
    gana_norm = to_operating_heavy(GANA, gana_policy, gana)
    dara_norm = to_operating_heavy(DARA, dara_policy, dara)
    print(f"  공시된 숫자만 보면 {DARA.name} {dara:.1f} 이 더 크다 ({GANA.name} {gana:.1f}).")
    print(f"  같은 기준으로 맞추면 {GANA.name} {gana_norm:.1f} 이 더 크다 ({DARA.name} {dara_norm:.1f}).")
    print()


def print_coverage_trap() -> None:
    print("[5] 현금이자보상배율 공식을 그대로 쓰면 성격 분리형에서 이자가 두 번 센다")
    w = [26, 14, 14]
    print(row(["계산", OPERATING_HEAVY.label, NATURE_SPLIT.label], w))
    print("-" * sum(w))
    a = statement(GANA, OPERATING_HEAVY)["영업"]
    b = statement(GANA, NATURE_SPLIT)["영업"]
    naive = [(x + GANA.interest_paid) / GANA.interest_paid for x in (a, b)]
    fixed_a = (a + GANA.interest_paid) / GANA.interest_paid
    fixed_b = b / GANA.interest_paid
    print(row(["(OCF + 이자지급) / 이자지급", f"{naive[0]:.2f}", f"{naive[1]:.2f}"], w))
    print(row(["이자 분류를 보고 고친 값", f"{fixed_a:.2f}", f"{fixed_b:.2f}"], w))
    print()


def main() -> None:
    print_policies()
    print_two_statements(GANA)
    print_metrics(GANA)
    print_cross_company()
    print_coverage_trap()


if __name__ == "__main__":
    main()
