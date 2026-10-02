"""활동성 비율 — 한 회사의 3개년으로 회전율 추세를 본다.

가상 회사 마루식품의 4개 시점(0~3년차 말) 재무상태표와 3개년 매출액으로
한국은행 기업경영분석의 회전율(801 총자산, 806 유형자산, 807 재고자산,
809 매출채권, 810 매입채무)을 계산한다. 분자는 모두 매출액, 분모는 기초·기말
평균잔액이다. 금액 단위는 억원이다.
"""
import platform
import sys

DAYS = 365

# 연말 잔액. 0년차 말은 1년차의 기초 잔액으로만 쓰인다
BALANCES = {
    0: {"현금": 100, "매출채권": 150, "재고자산": 100, "유형자산": 400, "기타자산": 50, "매입채무": 90},
    1: {"현금": 110, "매출채권": 165, "재고자산": 110, "유형자산": 420, "기타자산": 55, "매입채무": 100},
    # 2년차에 공장을 증설했다. 가동은 3년차부터라 매출은 아직 따라오지 않는다
    2: {"현금": 80, "매출채권": 185, "재고자산": 130, "유형자산": 650, "기타자산": 55, "매입채무": 110},
    # 3년차에 재고가 쌓이고, 공급처가 결제 조건을 줄였다
    3: {"현금": 70, "매출채권": 210, "재고자산": 210, "유형자산": 640, "기타자산": 60, "매입채무": 95},
}
SALES = {1: 1000, 2: 1150, 3: 1300}

ASSET_ITEMS = ["현금", "매출채권", "재고자산", "유형자산", "기타자산"]


def total_assets(year: int) -> float:
    return sum(BALANCES[year][k] for k in ASSET_ITEMS)


def average(year: int, item: str) -> float:
    if item == "총자산":
        return (total_assets(year - 1) + total_assets(year)) / 2
    return (BALANCES[year - 1][item] + BALANCES[year][item]) / 2


def turnover(year: int, item: str) -> float:
    return SALES[year] / average(year, item)


def print_environment() -> None:
    print(f"Python {platform.python_version()} ({sys.platform})")
    print("금액 단위 억원 · 회전율 = 매출액 ÷ (기초+기말)/2 · 회전일수 = 365 ÷ 회전율")
    print()


def show_balances() -> None:
    print("[1] 마루식품 연말 재무상태표(요약)와 매출액")
    items = ASSET_ITEMS + ["총자산", "매입채무"]
    print(f"  {'':8}" + "".join(f"{f'{y}년차 말':>9}" for y in BALANCES))
    for item in items:
        values = [total_assets(y) if item == "총자산" else BALANCES[y][item] for y in BALANCES]
        print(f"  {item:8}" + "".join(f"{v:10.0f}" for v in values))
    print(f"  {'매출액':8}{'-':>10}" + "".join(f"{SALES[y]:10.0f}" for y in SALES))
    print()


def show_turnovers() -> None:
    print("[2] 회전율 (회)")
    items = ["총자산", "유형자산", "재고자산", "매출채권", "매입채무"]
    print(f"  {'':8}" + "".join(f"{f'{y}년차':>9}" for y in SALES) + f"{'1→3년차':>10}")
    for item in items:
        values = [turnover(y, item) for y in SALES]
        change = values[-1] / values[0] - 1
        print(f"  {item:8}" + "".join(f"{v:10.2f}" for v in values) + f"{change * 100:+10.1f}%")
    print()


def show_days() -> None:
    print("[3] 회전일수와 현금전환주기 (일)")
    print(f"  {'':16}" + "".join(f"{f'{y}년차':>9}" for y in SALES))
    rows = {
        "재고일수 (A)": [DAYS / turnover(y, "재고자산") for y in SALES],
        "매출채권 회수일수 (B)": [DAYS / turnover(y, "매출채권") for y in SALES],
        "매입채무 지급일수 (C)": [DAYS / turnover(y, "매입채무") for y in SALES],
    }
    rows["영업주기 A+B"] = [a + b for a, b in zip(rows["재고일수 (A)"], rows["매출채권 회수일수 (B)"])]
    rows["현금전환주기 A+B−C"] = [ab - c for ab, c in zip(rows["영업주기 A+B"], rows["매입채무 지급일수 (C)"])]
    for label, values in rows.items():
        print(f"  {label:16}" + "".join(f"{v:10.1f}" for v in values))
    print()


def show_intensity() -> None:
    # 총자산회전율의 역수(매출 1원당 총자산)는 항목별 '매출 1원당 자산'의 합이다.
    # 곱이 아니라 합이므로 총자산회전율 하락을 항목별로 남김없이 나눌 수 있다
    print("[4] 매출 1원당 평균자산 — 총자산회전율의 역수를 항목별로 나눈 것")
    print(f"  {'':8}" + "".join(f"{f'{y}년차':>9}" for y in SALES) + f"{'1→3년차 증감':>12}")
    first, last = 1, max(SALES)
    total_change = 0.0
    for item in ASSET_ITEMS:
        values = [average(y, item) / SALES[y] for y in SALES]
        delta = values[-1] - values[0]
        total_change += delta
        print(f"  {item:8}" + "".join(f"{v:10.3f}" for v in values) + f"{delta:+12.3f}")
    totals = [average(y, "총자산") / SALES[y] for y in SALES]
    print(f"  {'합계':8}" + "".join(f"{v:10.3f}" for v in totals) + f"{total_change:+12.3f}")
    print(f"  (검산: 1 ÷ 총자산회전율 = {1 / turnover(first, '총자산'):.3f} → {1 / turnover(last, '총자산'):.3f})")
    print()


def show_working_capital() -> None:
    print("[5] 영업에 묶인 운전자본 = 매출채권 + 재고자산 − 매입채무 (평균잔액)")
    for y in SALES:
        tied = average(y, "매출채권") + average(y, "재고자산") - average(y, "매입채무")
        # 현금전환주기 × 하루 매출과 같아야 한다. 세 회전율 분자가 모두 매출액이라서다
        by_days = (DAYS / turnover(y, "재고자산") + DAYS / turnover(y, "매출채권")
                   - DAYS / turnover(y, "매입채무")) * SALES[y] / DAYS
        print(f"  {y}년차  운전자본 {tied:6.1f}  (현금전환주기 × 하루 매출 = {by_days:6.1f})")


def main() -> None:
    print_environment()
    show_balances()
    show_turnovers()
    show_days()
    show_intensity()
    show_working_capital()


if __name__ == "__main__":
    main()
