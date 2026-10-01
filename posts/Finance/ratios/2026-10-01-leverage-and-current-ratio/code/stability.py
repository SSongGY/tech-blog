"""부채비율과 유동비율 — 같은 200%가 업종마다 다르게 읽히는 이유.

부채비율이 똑같이 200%인 가상 회사 넷을 둔다. 제조업 둘(부채 구성만 다름),
전력 회사 하나, 은행 하나. 산식은 한국은행 기업경영분석을 따른다.
업종 집계값은 한국은행 「2024년 1/4분기 기업경영분석」(2024.6.20 발표)의 표를 옮겼다.
"""
import platform
import sys
from dataclasses import dataclass, field

# 한국은행 2024년 1/4분기 외감기업 부채비율(%). 개별 기업을 합산한 집계값이다.
BOK_DEBT_RATIO_2024Q1 = {
    "금속제품": 53.9,
    "제조업 전체": 70.3,
    "정보통신": 79.1,
    "건설": 159.9,
    "전기가스": 351.5,
}


@dataclass
class Company:
    name: str
    industry: str
    # 유동·비유동 구분이 없는 회사(은행)는 None
    current_assets: float | None
    quick_assets: float | None
    total_assets: float
    current_liabilities: float | None
    borrowings: float  # 장단기차입금 + 회사채
    total_liabilities: float
    interest_rate: float = 0.05
    note: str = ""
    liability_detail: dict[str, float] = field(default_factory=dict)

    @property
    def equity(self) -> float:
        return self.total_assets - self.total_liabilities


MABA = Company(
    "마바제조", "제조업", current_assets=300, quick_assets=180, total_assets=900,
    current_liabilities=250, borrowings=450, total_liabilities=600,
    liability_detail={"매입채무": 100, "선수금": 50, "단기차입금": 100, "장기차입금": 350},
)
SAJA = Company(
    "사자제조", "제조업", current_assets=400, quick_assets=250, total_assets=900,
    current_liabilities=500, borrowings=100, total_liabilities=600,
    liability_detail={"매입채무": 300, "선수금": 200, "장기차입금": 100},
)
AJA = Company(
    "아자전력", "전기가스", current_assets=90, quick_assets=80, total_assets=900,
    current_liabilities=150, borrowings=480, total_liabilities=600,
    liability_detail={"매입채무": 70, "단기차입금": 80, "회사채": 400, "기타": 50},
)

# 은행은 같은 200%가 아니라 은행으로서 흔한 모양의 숫자를 둔다(가정).
# 위험가중치는 설명용 가정값이다. 실제 가중치는 감독규정의 산출기준을 따른다.
BANK_ASSETS = {  # 항목: (금액, 가정한 위험가중치)
    "현금·중앙은행 예치금": (50, 0.0),
    "국공채": (250, 0.0),
    "주택담보대출": (400, 0.35),
    "기업대출": (300, 1.0),
}
BANK_LIABILITIES = {"예수금": 860, "차입금·사채": 60}


def debt_ratio(c: Company) -> float:
    return c.total_liabilities / c.equity


def print_definitions() -> None:
    print("[0] 산식 (한국은행 기업경영분석)")
    print("  부채비율     = (유동부채 + 비유동부채) ÷ 자기자본 × 100")
    print("  자기자본비율 = 자기자본 ÷ 총자본(=총자산) × 100")
    print("  유동비율     = 유동자산 ÷ 유동부채 × 100")
    print("  당좌비율     = 당좌자산(유동자산 − 재고자산 등) ÷ 유동부채 × 100")
    print("  차입금의존도 = (장단기차입금 + 회사채) ÷ 총자본 × 100")
    print()


def print_same_200() -> None:
    print("[1] 부채비율이 200%로 같은 세 회사 (단위: 억원)")
    header = f"  {'':10}{'업종':>8}{'자산':>6}{'부채':>6}{'자본':>6}{'부채비율':>9}{'자기자본비율':>9}{'차입금의존도':>9}"
    print(header)
    for c in (MABA, SAJA, AJA):
        print(f"  {c.name:10}{c.industry:>8}{c.total_assets:>6.0f}{c.total_liabilities:>6.0f}{c.equity:>6.0f}"
              f"{debt_ratio(c):>9.1%}{c.equity / c.total_assets:>12.1%}{c.borrowings / c.total_assets:>12.1%}")
    print()
    for c in (MABA, SAJA, AJA):
        detail = ", ".join(f"{k} {v:.0f}" for k, v in c.liability_detail.items())
        assert sum(c.liability_detail.values()) == c.total_liabilities
        print(f"  {c.name} 부채 구성: {detail}")
    print()


def print_interest() -> None:
    print("[2] 부채비율은 같아도 이자를 내는 부채가 다르다 (차입금 이자율 5% 가정)")
    for c in (MABA, SAJA, AJA):
        interest = c.borrowings * c.interest_rate
        print(f"  {c.name}  차입금 {c.borrowings:.0f} → 연 이자비용 {interest:.1f}")
    print("  매입채무·선수금은 부채비율의 분자에 들어가지만 이자가 붙지 않는다")
    print()


def print_vs_industry() -> None:
    print("[3] 같은 200%를 업종 집계와 나란히 놓으면 (한국은행 2024.1/4 외감기업, 부채비율 %)")
    for industry, value in BOK_DEBT_RATIO_2024Q1.items():
        print(f"  {industry:10}{value:>7.1f}%   200% ÷ 집계 = {200 / value:>4.2f}배")
    print("  금융·보험업은 기업경영분석 집계 대상(비금융 영리법인)에 들어 있지 않다")
    print()


def print_buffer() -> None:
    print("[4] 부채비율과 '자산이 몇 % 줄면 자본이 0이 되는가'")
    print(f"  {'부채비율':>8}{'자기자본비율':>12}{'자본이 0이 되는 자산 감소율':>20}")
    for ratio in (0.5, 1.0, 2.0, 3.515, 11.5):
        equity_share = 1 / (1 + ratio)
        print(f"  {ratio:>8.1%}{equity_share:>14.1%}{equity_share:>22.1%}")
    print("  자기자본비율 = 1 ÷ (1 + 부채비율). 부채가 그대로일 때 자산이 이만큼 줄면 자본이 사라진다")
    print()


def print_current() -> None:
    print("[5] 유동비율·당좌비율 (기말 잔액)")
    for c in (MABA, SAJA, AJA):
        current = c.current_assets / c.current_liabilities
        quick = c.quick_assets / c.current_liabilities
        short_debt = c.current_liabilities / c.equity
        print(f"  {c.name}  유동비율 {current:>6.1%}  당좌비율 {quick:>6.1%}  유동부채비율(유동부채÷자기자본) {short_debt:>6.1%}")
    print("  한국은행 해설: 유동부채비율이 100%를 넘으면 자본구성과 재무유동성이 불안정한 상태")
    print()


def print_bank() -> None:
    print("[6] 가상 은행 차카은행 — 같은 잣대를 대면")
    total_assets = sum(v for v, _ in BANK_ASSETS.values())
    total_liabilities = sum(BANK_LIABILITIES.values())
    equity = total_assets - total_liabilities
    rwa = sum(v * w for v, w in BANK_ASSETS.values())
    for name, (value, weight) in BANK_ASSETS.items():
        print(f"  자산 {name:14}{value:>5.0f}  가정 위험가중치 {weight:>4.0%} → 위험가중자산 {value * weight:>6.1f}")
    for name, value in BANK_LIABILITIES.items():
        print(f"  부채 {name:14}{value:>5.0f}")
    print(f"  자산 {total_assets:.0f}, 부채 {total_liabilities:.0f}, 자본 {equity:.0f}")
    print(f"  부채비율 {total_liabilities / equity:.1%}  자기자본비율 {equity / total_assets:.1%}")
    print("  유동비율: 산출 불가 — 재무상태표를 유동성 순서로 표시해 유동·비유동 구분이 없다")
    print(f"  위험가중자산 {rwa:.1f}, 자본 ÷ 위험가중자산 = {equity / rwa:.1%}"
          "  (자본 전액을 규제자본으로 본다는 가정)")
    print("  은행 규제 최저비율: 보통주자본 4.5%, 기본자본 6.0%, 총자본 8.0% (e-나라지표 BIS 기준자기자본비율)")
    print()


def main() -> None:
    print(f"Python {platform.python_version()} / {platform.system()}")
    print("단위: 억원 / 회사: 마바제조·사자제조·아자전력·차카은행(모두 가상)")
    print()
    print_definitions()
    print_same_200()
    print_interest()
    print_vs_industry()
    print_buffer()
    print_current()
    print_bank()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
