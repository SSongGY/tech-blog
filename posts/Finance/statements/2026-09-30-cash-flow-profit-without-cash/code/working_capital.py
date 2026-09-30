"""이익은 같은데 영업활동 현금흐름이 갈리는 두 가상 회사를 4년간 계산한다.

마바상사와 사아유통은 매출이 해마다 25%씩 같이 늘고 순이익률도 8%로 같다.
다른 것은 거래 조건뿐이다. 마바상사는 30일 만에 외상을 받고 재고도 30일치만 두지만,
사아유통은 외상을 120일 뒤에 받고 재고를 90일치 쌓아 둔다. 둘 다 원재료 대금은
30일 뒤에 준다. 4년째에는 성장이 멈춘다고 두고 현금이 어떻게 따라오는지 본다.

영업활동 현금흐름은 간접법(K-IFRS 제1007호 문단 20)으로
당기순이익 + 감가상각비 − 매출채권 증가 − 재고자산 증가 + 매입채무 증가 로 계산하고,
직접법(받은 현금 − 준 현금)으로 한 번 더 구해 둘이 같은지 검산한다. 금액 단위는 억원이다.
"""

import platform
import sys

DAYS = 365
COGS_RATIO = 0.70        # 매출원가율
NET_MARGIN = 0.08        # 순이익률. 세금·이자를 따로 두지 않으려고 비율로 고정한다
DEPRECIATION = 20        # 해마다 같은 감가상각비. 현금이 나가지 않는 비용이다
SALES = [800, 1000, 1250, 1562.5, 1562.5]   # 0년차(기초) + 1~4년차. 4년차는 성장 정지

TERMS = {   # (매출채권 회수일, 재고 보유일, 매입채무 지급일)
    "마바상사": (30, 30, 30),
    "사아유통": (120, 90, 30),
}


def balances(sales: float, dso: int, dio: int, dpo: int) -> dict:
    """연 매출과 거래 조건으로 기말 운전자본 잔액을 만든다."""
    cogs = sales * COGS_RATIO
    return {
        "매출채권": sales * dso / DAYS,
        "재고자산": cogs * dio / DAYS,
        "매입채무": cogs * dpo / DAYS,
    }


def simulate(dso: int, dio: int, dpo: int) -> list[dict]:
    rows = []
    prev = balances(SALES[0], dso, dio, dpo)
    for year, sales in enumerate(SALES[1:], start=1):
        cur = balances(sales, dso, dio, dpo)
        cogs = sales * COGS_RATIO
        net = sales * NET_MARGIN
        d_ar = cur["매출채권"] - prev["매출채권"]
        d_inv = cur["재고자산"] - prev["재고자산"]
        d_ap = cur["매입채무"] - prev["매입채무"]
        indirect = net + DEPRECIATION - d_ar - d_inv + d_ap

        # 직접법: 매출 중 받은 돈 − 원가 중 준 돈 − 그 밖의 현금비용
        collected = sales - d_ar
        purchases = cogs + d_inv            # 판 만큼 + 재고로 더 쌓은 만큼 샀다
        paid_suppliers = purchases - d_ap
        other_cash_costs = sales - cogs - net - DEPRECIATION
        direct = collected - paid_suppliers - other_cash_costs

        rows.append({"연도": year, "매출": sales, "순이익": net, "매출채권증가": d_ar,
                     "재고증가": d_inv, "매입채무증가": d_ap,
                     "영업CF": indirect, "직접법": direct, "회수": collected})
        prev = cur
    return rows


def main() -> None:
    print(f"Python {sys.version.split()[0]} / {platform.system()}")
    print(f"단위: 억원 / 회사: 마바상사·사아유통(가상) / 매출원가율 {COGS_RATIO:.0%}, "
          f"순이익률 {NET_MARGIN:.0%}, 감가상각비 {DEPRECIATION}(가정)")
    print(f"매출: 0년차 {SALES[0]:g} → " + " → ".join(f"{s:g}" for s in SALES[1:]) + " (4년차 성장 정지)")

    print("\n[1] 거래 조건 — 현금이 묶이는 날수")
    for name, (dso, dio, dpo) in TERMS.items():
        print(f"  {name}  회수 {dso:>3}일 + 재고 {dio:>3}일 − 지급 {dpo:>3}일 = {dso + dio - dpo:>3}일")

    results = {name: simulate(*t) for name, t in TERMS.items()}
    for name, rows in results.items():
        print(f"\n[2] {name} — 간접법 영업활동 현금흐름")
        print("  연도      매출    순이익  +감가상각  −채권증가  −재고증가  +채무증가    영업CF")
        for r in rows:
            print(f"  {r['연도']:>2}년 {r['매출']:>9,.1f} {r['순이익']:>8.1f} {DEPRECIATION:>9}"
                  # + 0.0 은 성장이 멈춘 해의 -0.0 표기를 없앤다
                  f" {-r['매출채권증가'] + 0.0:>10.1f} {-r['재고증가'] + 0.0:>10.1f} {r['매입채무증가']:>10.1f}"
                  f" {r['영업CF']:>9.1f}")

    print("\n[3] 직접법으로 다시 구한 값과 같은가")
    for name, rows in results.items():
        same = all(abs(r["영업CF"] - r["직접법"]) < 1e-9 for r in rows)
        print(f"  {name}  " + "  ".join(f"{r['직접법']:.1f}" for r in rows) + f"   → {'일치' if same else '불일치'}")

    print("\n[4] 1~3년차(성장기) 누계")
    for name, rows in results.items():
        grow = rows[:3]
        net = sum(r["순이익"] for r in grow)
        ocf = sum(r["영업CF"] for r in grow)
        print(f"  {name}  순이익 {net:.1f}  영업CF {ocf:.1f}  영업CF ÷ 순이익 = {ocf / net:.2f}")

    r3 = results["사아유통"][2]
    print(f"\n[5] 사아유통 3년차 — 매출 {r3['매출']:,.1f} 가운데 그해 받은 현금")
    print(f"  매출 {r3['매출']:,.1f} − 매출채권 증가 {r3['매출채권증가']:.1f} = 회수 {r3['회수']:,.1f}"
          f"  ({r3['회수'] / r3['매출']:.1%})")

    print("\n[6] 3년차 말 운전자본 잔액 — 채권 + 재고 − 채무 (현금 대신 들고 있는 것)")
    for name, t in TERMS.items():
        b = balances(SALES[3], *t)
        tied = b["매출채권"] + b["재고자산"] - b["매입채무"]
        print(f"  {name}  {b['매출채권']:.1f} + {b['재고자산']:.1f} − {b['매입채무']:.1f} = {tied:.1f}")


if __name__ == "__main__":
    main()
