"""배당가능이익 — 이익잉여금 잔액과 배당할 수 있는 금액은 왜 다른가.

상법 제462조 제1항의 공제식을 항목별로 세우고, 제458조의 이익준비금 적립 의무가
한도를 한 번 더 깎는 경로를 계산한다.

1. 공제식 — 자기주식만 다른 두 회사
2. 이익잉여금 잔액과 공제 결과가 갈리는 지점
3. 적립 의무가 한도를 깎는 두 가지 모양 — 비례로 깎이는 경우와 상한에서 멈추는 경우
4. 세 회사의 최대 배당액
5. 준비금 감액으로 한도를 늘리는 길 (제461조의2)
"""
import platform
import sys
from dataclasses import dataclass

EOK = 100_000_000  # 1억원


@dataclass
class Firm:
    """가상 회사의 자본 구성. 단위는 억원."""
    name: str
    capital: float            # 자본금
    capital_reserve: float    # 자본준비금 (주식발행초과금 등)
    earned_reserve: float     # 그 결산기까지 적립된 이익준비금
    retained: float           # 이익잉여금
    treasury: float = 0.0     # 자기주식 — 자본에서 차감하는 음수 항목의 절댓값
    unrealised: float = 0.0   # 제462조 제1항 제4호의 미실현이익

    @property
    def net_assets(self) -> float:
        """대차대조표상 순자산액 = 자본총계."""
        return (self.capital + self.capital_reserve + self.earned_reserve
                + self.retained + self.unrealised - self.treasury)

    @property
    def available(self) -> float:
        """제462조 제1항 제1호~제4호를 뺀 금액. 아직 제3호는 빼지 않은 중간값."""
        return (self.net_assets - self.capital
                - (self.capital_reserve + self.earned_reserve) - self.unrealised)

    @property
    def reserve_room(self) -> float:
        """제458조 — 자본금의 2분의 1까지만 적립 의무가 있다."""
        return max(0.0, self.capital / 2 - self.earned_reserve)

    def max_dividend(self) -> tuple[float, float]:
        """배당액 D 와 그에 딸린 적립액의 합이 available 을 넘지 못한다.

        적립액은 배당액의 10분의 1이되 reserve_room 에서 멈추므로 두 갈래로 푼다.
        """
        # ① 적립 의무가 상한에 걸리지 않는 구간: D + D/10 <= available
        d_proportional = self.available * 10 / 11
        if d_proportional / 10 <= self.reserve_room:
            return d_proportional, d_proportional / 10
        # ② 적립액이 상한에서 멈추는 구간: D + reserve_room <= available
        return self.available - self.reserve_room, self.reserve_room


GANA = Firm("가나전자", capital=50, capital_reserve=200, earned_reserve=10, retained=710)
DARA = Firm("다라물산", capital=50, capital_reserve=200, earned_reserve=10, retained=710,
            treasury=150)
MABA = Firm("마바산업", capital=500, capital_reserve=300, earned_reserve=0, retained=100)
FIRMS = [GANA, DARA, MABA]


def print_environment() -> None:
    print(f"Python {platform.python_version()} ({sys.platform})")
    print("단위: 억원. 세 회사 모두 가상이다.")
    print("미실현이익(제462조 제1항 제4호)은 시행령에 위임되어 있어 범위를 확인하지 못했다.")
    print("이 예제에서는 전부 0으로 두고 계산에서 뺀다.")
    print()


def print_formula() -> None:
    print("[1] 상법 제462조 제1항의 공제 — 자기주식만 다른 두 회사")
    print(f"  {'':34}{GANA.name:>12}{DARA.name:>12}")
    rows = [
        ("자본금", "capital"),
        ("자본준비금(주식발행초과금)", "capital_reserve"),
        ("이익준비금 (적립 완료분)", "earned_reserve"),
        ("이익잉여금", "retained"),
        ("자기주식 (자본에서 차감)", "treasury"),
    ]
    for label, attr in rows:
        a, b = getattr(GANA, attr), getattr(DARA, attr)
        if attr == "treasury":   # 자본에서 빼는 항목이라 음수로 보여 준다
            a, b = -a or 0.0, -b or 0.0
        print(f"  {label:32}{a:>12,.3f}{b:>12,.3f}")
    print(f"  {'─' * 58}")
    print(f"  {'순자산액 (자본총계)':32} {GANA.net_assets:>11,.3f} {DARA.net_assets:>11,.3f}")
    print(f"  {'− 제1호 자본금':32} {GANA.capital:>11,.3f} {DARA.capital:>11,.3f}")
    print(f"  {'− 제2호 자본준비금+이익준비금':32} "
          f"{GANA.capital_reserve + GANA.earned_reserve:>11,.3f} "
          f"{DARA.capital_reserve + DARA.earned_reserve:>11,.3f}")
    print(f"  {'− 제4호 미실현이익':32} {GANA.unrealised:>11,.3f} {DARA.unrealised:>11,.3f}")
    print(f"  {'─' * 58}")
    print(f"  {'= 제3호를 빼기 전 금액':32} {GANA.available:>11,.3f} {DARA.available:>11,.3f}")
    print()


def print_gap() -> None:
    print("[2] 이익잉여금 잔액과 갈리는 지점")
    print(f"  {'':14}{'이익잉여금':>14}{'제3호 전 금액':>16}{'차이':>12}{'자기주식':>12}")
    for firm in (GANA, DARA):
        gap = firm.retained - firm.available
        print(f"  {firm.name:12}{firm.retained:>14,.3f}{firm.available:>16,.3f}"
              f"{gap:>12,.3f}{firm.treasury:>12,.3f}")
    print("  차이는 자기주식 금액과 정확히 같다 — 순자산은 자기주식만큼 줄지만")
    print("  자기주식은 제1항 각 호의 공제 대상이 아니라 빼 주지 않기 때문이다.")
    print()


def print_reserve_duty() -> None:
    print("[3] 제458조 이익준비금 적립 의무 — 배당액의 10분의 1, 자본금의 2분의 1까지")
    print(f"  {'':14}{'자본금':>10}{'자본금의 1/2':>14}{'적립 완료':>12}{'남은 적립 의무':>16}")
    for firm in FIRMS:
        print(f"  {firm.name:12}{firm.capital:>10,.3f}{firm.capital / 2:>14,.3f}"
              f"{firm.earned_reserve:>12,.3f}{firm.reserve_room:>16,.3f}")
    print("  배당을 하면 그 10분의 1을 같은 결산기에 적립해야 하고(제458조),")
    print("  그 적립액은 제462조 제1항 제3호로 한 번 더 빠진다 — 배당액이 한도에 두 번 닿는다.")
    print()


def print_max_dividend() -> None:
    print("[4] 최대 배당액 — 배당액과 적립액의 합이 [1] 의 금액을 넘지 못한다")
    print(f"  {'':14}{'제3호 전 금액':>16}{'최대 배당액':>14}{'딸린 적립액':>14}"
          f"{'합계':>12}{'걸린 조건':>16}")
    for firm in FIRMS:
        dividend, reserve = firm.max_dividend()
        binding = "상한에서 멈춤" if reserve >= firm.reserve_room - 1e-9 else "배당액의 1/10"
        print(f"  {firm.name:12}{firm.available:>16,.3f}{dividend:>14,.3f}"
              f"{reserve:>14,.3f}{dividend + reserve:>12,.3f}{binding:>14}")
    print(f"  마바산업은 적립 의무가 남아 있어 한도의 10/11 인 "
          f"{MABA.available * 10 / 11:,.3f} 까지만 배당할 수 있다.")
    print(f"  가나전자와 다라물산의 최대 배당액 차이 "
          f"{GANA.max_dividend()[0] - DARA.max_dividend()[0]:,.3f} 은 자기주식 "
          f"{DARA.treasury:,.3f} 과 같다.")
    print()


def print_reserve_reduction() -> None:
    print("[5] 준비금 감액 (제461조의2) — 자본금의 1.5배를 넘는 법정준비금은 줄일 수 있다")
    print(f"  {'':14}{'법정준비금 합계':>18}{'자본금의 1.5배':>16}{'감액 가능액':>14}"
          f"{'감액 후 최대 배당':>18}")
    for firm in FIRMS:
        total_reserve = firm.capital_reserve + firm.earned_reserve
        ceiling = firm.capital * 1.5
        reducible = max(0.0, total_reserve - ceiling)
        after = Firm(firm.name, firm.capital, firm.capital_reserve - reducible,
                     firm.earned_reserve, firm.retained + reducible,
                     firm.treasury, firm.unrealised)
        print(f"  {firm.name:12}{total_reserve:>18,.3f}{ceiling:>16,.3f}"
              f"{reducible:>14,.3f}{after.max_dividend()[0]:>18,.3f}")
    print("  감액은 순자산을 늘리지 않는다. 공제 항목이 줄어 한도만 올라간다.")
    print("  법정준비금은 결손 보전 외에는 처분하지 못하지만(제460조), 감액은 따로 열어 둔 길이다.")
    print()


def main() -> None:
    print_environment()
    print_formula()
    print_gap()
    print_reserve_duty()
    print_max_dividend()
    print_reserve_reduction()


if __name__ == "__main__":
    main()
