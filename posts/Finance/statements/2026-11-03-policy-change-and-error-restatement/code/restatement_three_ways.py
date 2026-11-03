"""회계정책 변경·전기오류 수정·회계추정치 변경이 비교 숫자를 어떻게 다르게 건드리는지 계산한다.

기업회계기준서 제1008호는 세 갈래를 다르게 처리한다.
- 회계정책 변경: 소급적용 — 비교표시되는 과거기간을 새 정책으로 다시 적고, 그보다
  앞선 기간의 누적효과는 가장 이른 비교기간의 기초 자본(보통 이익잉여금)을 조정한다(문단 19·22·26)
- 전기오류: 소급재작성 — 오류가 난 비교기간을 다시 적고, 그 전이면 기초금액을 재작성한다(문단 42)
- 회계추정치 변경: 전진적용 — 과거를 손대지 않고 당기와 미래기간에만 반영한다(문단 36·38)

가상 회사 아자상사의 2년치 손익으로 세 경우를 각각 따라간다. 단위는 억원.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Year:
    revenue: float
    cogs: float  # 처음 보고한 매출원가 (선입선출)
    other_expense: float

    @property
    def net_income(self) -> float:
        return self.revenue - self.cogs - self.other_expense


# 처음 보고한 숫자. 1년차(비교기간)와 2년차(당기)
REPORTED = {1: Year(1000.0, 700.0, 200.0), 2: Year(1100.0, 760.0, 220.0)}
OPENING_RETAINED_EARNINGS_Y1 = 250.0  # 1년차 기초 이익잉여금 (처음 보고한 값)

# [A] 회계정책 변경 — 재고 단위원가를 선입선출에서 가중평균으로 바꾼다.
#     기말 재고가 두 방법에서 얼마였는지만 알면 매출원가 차이가 나온다.
INVENTORY_FIFO = {0: 100.0, 1: 120.0, 2: 140.0}  # 0년 말(=1년 초), 1년 말, 2년 말
INVENTORY_WAVG = {0: 92.0, 1: 105.0, 2: 110.0}

# [B] 전기오류 — 1년차에 잡았어야 할 비용 12 를 빠뜨렸고, 2년차에 지급하면서 2년차 비용으로 잡았다.
OMITTED_EXPENSE = 12.0

# [C] 회계추정치 변경 — 취득원가 200, 내용연수 5년이던 설비를 2년차 초에 잔여 7년으로 늘린다.
MACHINE_COST = 200.0
OLD_LIFE = 5
NEW_REMAINING_LIFE = 7


def row(cells: list[str], widths: list[int]) -> str:
    return "".join(cell.rjust(w) for cell, w in zip(cells, widths))


def growth(a: float, b: float) -> float:
    return (b - a) / a * 100


def policy_change() -> None:
    """[A] 매출원가 = 기초재고 + 매입 - 기말재고. 매입은 같으므로 재고 차이만 매출원가를 움직인다."""
    print("[A] 회계정책 변경 (선입선출 → 가중평균) — 소급적용, 문단 19·22")
    diff = {y: INVENTORY_WAVG[y] - INVENTORY_FIFO[y] for y in (0, 1, 2)}
    w = [18, 12, 12, 12]
    print(row(["항목", "0년 말", "1년 말", "2년 말"], w))
    print("-" * sum(w))
    print(row(["재고(선입선출)", f"{INVENTORY_FIFO[0]:.1f}", f"{INVENTORY_FIFO[1]:.1f}", f"{INVENTORY_FIFO[2]:.1f}"], w))
    print(row(["재고(가중평균)", f"{INVENTORY_WAVG[0]:.1f}", f"{INVENTORY_WAVG[1]:.1f}", f"{INVENTORY_WAVG[2]:.1f}"], w))
    print(row(["재고 차이", f"{diff[0]:+.1f}", f"{diff[1]:+.1f}", f"{diff[2]:+.1f}"], w))
    print()
    restated = {}
    for y in (1, 2):
        # 기초재고가 diff[y-1] 만큼 작아지면 매출원가도 그만큼 작아지고, 기말재고가 diff[y] 만큼 작아지면 그만큼 커진다
        cogs = REPORTED[y].cogs + diff[y - 1] - diff[y]
        restated[y] = Year(REPORTED[y].revenue, cogs, REPORTED[y].other_expense)
    w = [18, 14, 14, 14]
    print(row(["손익", "처음 보고", "소급적용 후", "조정"], w))
    print("-" * sum(w))
    for y in (1, 2):
        label = "1년차(비교)" if y == 1 else "2년차(당기)"
        print(row([f"{label} 매출원가", f"{REPORTED[y].cogs:.1f}", f"{restated[y].cogs:.1f}", f"{restated[y].cogs - REPORTED[y].cogs:+.1f}"], w))
        print(row([f"{label} 순이익", f"{REPORTED[y].net_income:.1f}", f"{restated[y].net_income:.1f}", f"{restated[y].net_income - REPORTED[y].net_income:+.1f}"], w))
    print()
    opening = OPENING_RETAINED_EARNINGS_Y1 + diff[0]
    print(f"  1년차 기초 이익잉여금: {OPENING_RETAINED_EARNINGS_Y1:.1f} → {opening:.1f} ({diff[0]:+.1f})")
    print("  0년 말 이전에 쌓인 누적효과는 비교표시되는 가장 이른 기간의 기초 이익잉여금으로 들어간다 (문단 22·26)")
    print(f"  순이익 성장률: 처음 보고 {growth(REPORTED[1].net_income, REPORTED[2].net_income):.1f}% → 소급적용 후 {growth(restated[1].net_income, restated[2].net_income):.1f}%")
    print()


def error_correction() -> None:
    """[B] 빠뜨린 비용은 원래 기간으로 돌려보낸다. 2년차에 잘못 잡힌 비용은 2년차에서 빠진다."""
    print("[B] 전기오류 수정 (1년차 비용 12 누락) — 소급재작성, 문단 42")
    r1 = Year(REPORTED[1].revenue, REPORTED[1].cogs, REPORTED[1].other_expense + OMITTED_EXPENSE)
    r2 = Year(REPORTED[2].revenue, REPORTED[2].cogs, REPORTED[2].other_expense - OMITTED_EXPENSE)
    w = [18, 14, 14, 14]
    print(row(["손익", "처음 보고", "재작성 후", "조정"], w))
    print("-" * sum(w))
    print(row(["1년차(비교) 순이익", f"{REPORTED[1].net_income:.1f}", f"{r1.net_income:.1f}", f"{r1.net_income - REPORTED[1].net_income:+.1f}"], w))
    print(row(["2년차(당기) 순이익", f"{REPORTED[2].net_income:.1f}", f"{r2.net_income:.1f}", f"{r2.net_income - REPORTED[2].net_income:+.1f}"], w))
    print(row(["두 해 합계", f"{REPORTED[1].net_income + REPORTED[2].net_income:.1f}", f"{r1.net_income + r2.net_income:.1f}", "+0.0"], w))
    print()
    print(f"  1년 말 미지급비용(부채) {OMITTED_EXPENSE:+.1f}, 1년 말 이익잉여금 {-OMITTED_EXPENSE:+.1f} 로 재작성")
    print(f"  순이익 성장률: 처음 보고 {growth(REPORTED[1].net_income, REPORTED[2].net_income):.1f}% → 재작성 후 {growth(r1.net_income, r2.net_income):.1f}%")
    print()


def estimate_change() -> None:
    """[C] 1년차 감가상각은 그대로 둔다. 2년차 초 장부금액을 새 잔여 내용연수로 나눈다."""
    print("[C] 회계추정치 변경 (내용연수 5년 → 잔여 7년) — 전진적용, 문단 36·38")
    old_dep = MACHINE_COST / OLD_LIFE
    carrying_y2_open = MACHINE_COST - old_dep
    new_dep = carrying_y2_open / NEW_REMAINING_LIFE
    w = [18, 14, 14, 14]
    print(row(["감가상각비", "변경 전 추정", "변경 후", "조정"], w))
    print("-" * sum(w))
    print(row(["1년차(비교)", f"{old_dep:.1f}", f"{old_dep:.1f}", "+0.0"], w))
    print(row(["2년차(당기)", f"{old_dep:.1f}", f"{new_dep:.1f}", f"{new_dep - old_dep:+.1f}"], w))
    print(row(["3년차 이후 매년", f"{old_dep:.1f}", f"{new_dep:.1f}", f"{new_dep - old_dep:+.1f}"], w))
    print()
    print(f"  2년차 초 장부금액 {carrying_y2_open:.1f} 을 잔여 {NEW_REMAINING_LIFE}년으로 나눈다. 1년차 숫자는 손대지 않는다")
    print(f"  2년차 순이익: {REPORTED[2].net_income:.1f} → {REPORTED[2].net_income + (old_dep - new_dep):.1f} ({old_dep - new_dep:+.1f})")
    print()


def summary() -> None:
    print("[D] 세 갈래가 손대는 자리")
    w = [16, 14, 16, 16, 12]
    print(row(["구분", "처리", "비교기간(1년차)", "기초 이익잉여금", "당기"], w))
    print("-" * sum(w))
    print(row(["정책 변경", "소급적용", "다시 적는다", "조정한다", "새 정책"], w))
    print(row(["전기오류", "소급재작성", "다시 적는다", "오류 시점 따라", "바로잡는다"], w))
    print(row(["추정치 변경", "전진적용", "그대로", "그대로", "새 추정"], w))
    print()


def main() -> None:
    policy_change()
    error_correction()
    estimate_change()
    summary()


if __name__ == "__main__":
    main()
