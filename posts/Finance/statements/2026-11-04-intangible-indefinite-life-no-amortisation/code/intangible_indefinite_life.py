"""같은 상표권을 비한정·유한으로 분류했을 때 5년간 손익과 장부금액이 어떻게 갈리는지 계산한다.

기업회계기준서 제1038호 문단 107~108 은 내용연수가 비한정인 무형자산을 상각하지 않고
매년 손상검사를 하게 한다. 내용연수가 유한하면 상각하고, 손상검사는 징후가 있을 때만 한다.
두 회사는 같은 상표권, 같은 영업 성과, 같은 회수가능액을 갖는다. 분류만 다르다.
"""

from dataclasses import dataclass

YEARS = 5


@dataclass(frozen=True)
class Brand:
    """단위는 억원."""

    cost: float  # 상표권 취득원가
    revenue: float  # 연간 매출액 (일정하다고 둔다)
    profit_before_amortisation: float  # 상표권 상각·손상 전 영업이익
    finite_life: int  # 유한 분류 시 내용연수 (잔존가치 0, 정액법)
    recoverable: tuple[float, ...]  # 연말마다 추정한 상표권의 회수가능액


BRAND = Brand(
    cost=1000.0,
    revenue=1500.0,
    profit_before_amortisation=300.0,
    finite_life=10,
    # 3년 차에 상표 가치가 떨어져 800 이 된 뒤 그대로라고 둔다
    recoverable=(1100.0, 1100.0, 800.0, 800.0, 800.0),
)


def indefinite(b: Brand) -> list[dict[str, float]]:
    """문단 107~108 — 상각하지 않고 매년 손상검사를 한다."""
    rows, carrying = [], b.cost
    for year in range(1, YEARS + 1):
        loss = max(0.0, carrying - b.recoverable[year - 1])
        carrying -= loss
        rows.append(_row(b, year, 0.0, loss, carrying))
    return rows


def finite(b: Brand) -> list[dict[str, float]]:
    """문단 97~ — 내용연수에 걸쳐 상각하고, 손상검사는 징후가 있을 때 한다.

    3년 차부터 가치 하락이라는 징후가 있다고 보고 같은 해부터 검사한다.
    """
    rows, carrying = [], b.cost
    amortisation = b.cost / b.finite_life
    for year in range(1, YEARS + 1):
        carrying -= amortisation
        loss = 0.0
        if year >= 3:
            loss = max(0.0, carrying - b.recoverable[year - 1])
            carrying -= loss
        rows.append(_row(b, year, amortisation, loss, carrying))
    return rows


def _row(b: Brand, year: int, amortisation: float, loss: float, carrying: float) -> dict[str, float]:
    operating_profit = b.profit_before_amortisation - amortisation - loss
    return {
        "연차": year,
        "상각비": amortisation,
        "손상차손": loss,
        "장부금액": carrying,
        "영업이익": operating_profit,
        "영업이익률": operating_profit / b.revenue * 100,
    }


def row(cells: list[str], widths: list[int]) -> str:
    return "".join(cell.rjust(w) for cell, w in zip(cells, widths))


def print_carrying(b: Brand, a: list[dict], f: list[dict]) -> None:
    print("[1] 상표권 장부금액 — 비한정은 상각 없이 손상차손으로만 줄고 유한은 해마다 깎인다 (단위: 억원)")
    w = [6, 12, 12, 12, 12, 12, 12]
    print(row(["연차", "회수가능액", "비한정 상각", "비한정 손상", "비한정 장부", "유한 상각", "유한 장부"], w))
    print("-" * sum(w))
    for i in range(YEARS):
        print(
            row(
                [
                    f"{i + 1}",
                    f"{b.recoverable[i]:.1f}",
                    f"{a[i]['상각비']:.1f}",
                    f"{a[i]['손상차손']:.1f}",
                    f"{a[i]['장부금액']:.1f}",
                    f"{f[i]['상각비']:.1f}",
                    f"{f[i]['장부금액']:.1f}",
                ],
                w,
            )
        )
    print()
    print("  유한 쪽은 3년 차에 장부 700 이 회수가능액 800 보다 작아 손상차손이 없다.")
    print()


def print_profit(a: list[dict], f: list[dict]) -> None:
    print("[2] 영업이익과 영업이익률 — 같은 상표권, 같은 성과 (단위: 억원, %)")
    w = [6, 14, 14, 14, 14]
    print(row(["연차", "비한정 영업이익", "유한 영업이익", "비한정 이익률", "유한 이익률"], w))
    print("-" * sum(w))
    for i in range(YEARS):
        print(
            row(
                [
                    f"{i + 1}",
                    f"{a[i]['영업이익']:.1f}",
                    f"{f[i]['영업이익']:.1f}",
                    f"{a[i]['영업이익률']:.1f}",
                    f"{f[i]['영업이익률']:.1f}",
                ],
                w,
            )
        )
    print()


def print_cumulative(a: list[dict], f: list[dict]) -> None:
    print("[3] 5년 누적 — 영업이익의 차이가 장부금액의 차이와 같다 (단위: 억원)")
    w = [22, 14, 14, 10]
    print(row(["항목", "비한정", "유한", "차이"], w))
    print("-" * sum(w))
    items = {
        "상각비 합계": (sum(r["상각비"] for r in a), sum(r["상각비"] for r in f)),
        "손상차손 합계": (sum(r["손상차손"] for r in a), sum(r["손상차손"] for r in f)),
        "영업이익 합계": (sum(r["영업이익"] for r in a), sum(r["영업이익"] for r in f)),
        "5년 말 장부금액": (a[-1]["장부금액"], f[-1]["장부금액"]),
    }
    for key, (x, y) in items.items():
        print(row([key, f"{x:.1f}", f"{y:.1f}", f"{x - y:.1f}"], w))
    print()
    profit_gap = items["영업이익 합계"][0] - items["영업이익 합계"][1]
    carrying_gap = items["5년 말 장부금액"][0] - items["5년 말 장부금액"][1]
    print(f"  영업이익 차이 {profit_gap:.1f} = 장부금액 차이 {carrying_gap:.1f}: {profit_gap == carrying_gap}")
    print()


def main() -> None:
    a, f = indefinite(BRAND), finite(BRAND)
    print_carrying(BRAND, a, f)
    print_profit(a, f)
    print_cumulative(a, f)


if __name__ == "__main__":
    main()
