"""매각예정으로 분류한 설비와 계속 사용하는 설비의 5년을 비교한다.

기업회계기준서 제1105호는 매각예정 비유동자산을 장부금액과 순공정가치(공정가치에서
처분부대원가를 뺀 금액) 중 작은 금액으로 재고(문단 15), 분류한 뒤에는 감가상각하지
않게 한다(문단 25). 순공정가치가 오르면 과거 손상차손누계액을 한도로 이익을 인식한다(문단 21).
"""

from dataclasses import dataclass

YEARS = 5


@dataclass(frozen=True)
class Plant:
    """단위는 억원."""

    cost: float  # 설비 취득원가
    life: int  # 내용연수 (잔존가치 0, 정액법)
    classified_year: int  # 매각예정으로 분류하는 연도 (그 해 감가상각까지 인식한 뒤)
    fair_value: tuple[float, ...]  # 연말 공정가치 (분류 이후 연도만 쓴다)
    disposal_cost: float  # 처분부대원가 (1년 안에 매각되므로 현재가치 계산은 생략)
    profit_before_plant: float  # 설비 감가상각·손상 전 연간 세전이익
    revenue: float


PLANT = Plant(
    cost=1000.0,
    life=10,
    classified_year=4,
    fair_value=(0.0, 0.0, 0.0, 540.0, 580.0),
    disposal_cost=20.0,
    profit_before_plant=250.0,
    revenue=800.0,
)


def keep_using(p: Plant) -> list[dict[str, float]]:
    """계속 사용한다고 가정한다 — 5년 내내 상각하고 손상 징후는 없다."""
    depreciation = p.cost / p.life
    rows, carrying = [], p.cost
    for year in range(1, YEARS + 1):
        carrying -= depreciation
        rows.append(_row(p, year, depreciation, 0.0, 0.0, carrying))
    return rows


def held_for_sale(p: Plant) -> list[dict[str, float]]:
    """분류 연도 말부터 순공정가치와 장부금액 중 작은 금액으로 재고 상각을 멈춘다."""
    depreciation = p.cost / p.life
    rows, carrying, cumulative_loss = [], p.cost, 0.0
    for year in range(1, YEARS + 1):
        if year <= p.classified_year:
            carrying -= depreciation
            dep = depreciation
        else:
            dep = 0.0  # 문단 25 — 분류된 비유동자산은 감가상각하지 않는다
        loss = reversal = 0.0
        if year >= p.classified_year:
            net_fair = p.fair_value[year - 1] - p.disposal_cost
            if net_fair < carrying:
                loss = carrying - net_fair  # 문단 20
                carrying = net_fair
                cumulative_loss += loss
            elif net_fair > carrying and cumulative_loss > 0:
                reversal = min(net_fair - carrying, cumulative_loss)  # 문단 21
                carrying += reversal
                cumulative_loss -= reversal
        rows.append(_row(p, year, dep, loss, reversal, carrying))
    return rows


def _row(
    p: Plant, year: int, depreciation: float, loss: float, reversal: float, carrying: float
) -> dict[str, float]:
    plant_effect = -depreciation - loss + reversal
    return {
        "연차": year,
        "감가상각비": depreciation,
        "손상차손": loss,
        "환입이익": reversal,
        "설비 손익": plant_effect,
        "장부금액": carrying,
        "세전이익": p.profit_before_plant + plant_effect,
    }


def row(cells: list[str], widths: list[int]) -> str:
    return "".join(cell.rjust(w) for cell, w in zip(cells, widths))


def print_measurement(p: Plant) -> None:
    depreciation = p.cost / p.life
    before = p.cost - depreciation * p.classified_year
    print("[1] 분류 시점(4년 말)의 측정 — 장부금액과 순공정가치 중 작은 금액 (단위: 억원)")
    w = [28, 12]
    fair = p.fair_value[p.classified_year - 1]
    net_fair = fair - p.disposal_cost
    for label, value in [
        ("분류 직전 장부금액", before),
        ("공정가치", fair),
        ("처분부대원가", p.disposal_cost),
        ("순공정가치", net_fair),
        ("측정액 (작은 금액)", min(before, net_fair)),
        ("손상차손", max(0.0, before - net_fair)),
    ]:
        print(row([label, f"{value:.1f}"], w))
    print()


def print_path(a: list[dict], b: list[dict]) -> None:
    print("[2] 연차별 비교 — 계속 사용 대 매각예정 분류 (단위: 억원)")
    w = [6, 12, 12, 12, 12, 12, 12]
    print(row(["연차", "사용 상각", "분류 상각", "분류 손상", "분류 환입", "사용 장부", "분류 장부"], w))
    print("-" * sum(w))
    for i in range(YEARS):
        print(
            row(
                [
                    f"{i + 1}",
                    f"{a[i]['감가상각비']:.1f}",
                    f"{b[i]['감가상각비']:.1f}",
                    f"{b[i]['손상차손']:.1f}",
                    f"{b[i]['환입이익']:.1f}",
                    f"{a[i]['장부금액']:.1f}",
                    f"{b[i]['장부금액']:.1f}",
                ],
                w,
            )
        )
    print()
    print("  5년 차: 분류한 쪽은 상각이 0이고 순공정가치 상승분 40 을 환입한다 (한도는 누계 손상차손 80).")
    print()


def print_profit(a: list[dict], b: list[dict]) -> None:
    print("[3] 세전이익과 5년 누적 — 설비 손익이 두 번 갈린다 (단위: 억원)")
    w = [6, 14, 14]
    print(row(["연차", "사용 세전이익", "분류 세전이익"], w))
    print("-" * sum(w))
    for i in range(YEARS):
        print(row([f"{i + 1}", f"{a[i]['세전이익']:.1f}", f"{b[i]['세전이익']:.1f}"], w))
    print()
    total_a = sum(r["세전이익"] for r in a)
    total_b = sum(r["세전이익"] for r in b)
    gap_profit = total_b - total_a
    gap_carrying = b[-1]["장부금액"] - a[-1]["장부금액"]
    print(f"  세전이익 합계: 사용 {total_a:.1f} / 분류 {total_b:.1f} / 차이 {gap_profit:.1f}")
    print(f"  5년 말 장부금액 차이 {gap_carrying:.1f}")
    print(f"  세전이익 차이 = 장부금액 차이: {gap_profit == gap_carrying}")
    print()


def main() -> None:
    a, b = keep_using(PLANT), held_for_sale(PLANT)
    print_measurement(PLANT)
    print_path(a, b)
    print_profit(a, b)


if __name__ == "__main__":
    main()
