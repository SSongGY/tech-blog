"""같은 매입·판매 내역에 선입선출법과 총평균법을 적용해 매출원가와 기말재고를 비교한다.

가나전자는 선입선출법, 다라물산은 총평균법(기간 단위 가중평균)을 쓴다.
두 회사는 같은 날 같은 값으로 사서 같은 날 같은 값에 판다. 다른 것은 원가 공식뿐이다.
단위는 백만원, 수량은 개다.
"""

# (연도, 분기별 매입 [(수량, 단가)], 판매 수량, 판매 단가)
YEARS = [
    ("1년차", [(100, 10), (100, 12), (100, 14), (100, 16)], 300, 25),
    ("2년차", [(100, 18), (100, 20), (100, 22), (100, 24)], 400, 30),
    ("3년차", [(100, 22), (100, 20), (100, 18), (100, 16)], 400, 30),
]

# 3년차 말 순실현가능가치를 구하는 가정: 예상 판매가 17, 판매에 드는 비용 2
NRV_SELLING_PRICE = 17
NRV_COST_TO_SELL = 2


def fifo_year(layers, purchases, sold_qty):
    """먼저 들어온 층부터 판다. layers 는 [(수량, 단가)] 이고 앞쪽이 오래된 것이다."""
    layers = layers + purchases
    cogs = 0
    remaining = sold_qty
    kept = []
    for qty, cost in layers:
        take = min(qty, remaining)
        cogs += take * cost
        remaining -= take
        if qty - take > 0:
            kept.append((qty - take, cost))
    return cogs, kept


def average_year(begin_qty, begin_cost, purchases, sold_qty):
    """기초재고와 당기 매입을 합쳐 한 번만 평균을 낸다 (기간 단위 가중평균)."""
    total_qty = begin_qty + sum(q for q, _ in purchases)
    total_cost = begin_cost + sum(q * c for q, c in purchases)
    unit = total_cost / total_qty
    cogs = sold_qty * unit
    end_qty = total_qty - sold_qty
    return cogs, end_qty, end_qty * unit, unit


def print_purchases():
    print("[1] 두 회사가 똑같이 겪은 매입·판매 내역")
    print("    연도      분기별 매입 (수량×단가)                 판매 수량  판매 단가")
    for label, purchases, sold, price in YEARS:
        detail = ", ".join(f"{q}×{c}" for q, c in purchases)
        print(f"    {label}   {detail:<40} {sold:>6}  {price:>7}")
    print("    1·2년차는 매입 단가가 오르고, 3년차는 내린다")
    print()


def run():
    fifo_layers = []
    avg_qty, avg_cost = 0, 0.0
    totals = {"fifo_cogs": 0, "avg_cogs": 0.0, "fifo_gp": 0, "avg_gp": 0.0}
    rows = []
    for label, purchases, sold, price in YEARS:
        revenue = sold * price
        bought = sum(q * c for q, c in purchases)
        f_cogs, fifo_layers = fifo_year(fifo_layers, purchases, sold)
        f_end = sum(q * c for q, c in fifo_layers)
        a_cogs, avg_qty, avg_cost, unit = average_year(avg_qty, avg_cost, purchases, sold)
        rows.append((label, revenue, bought, f_cogs, f_end, a_cogs, avg_cost, unit))
        totals["fifo_cogs"] += f_cogs
        totals["avg_cogs"] += a_cogs
        totals["fifo_gp"] += revenue - f_cogs
        totals["avg_gp"] += revenue - a_cogs
    return rows, totals, fifo_layers, avg_qty, avg_cost


def print_1st_year_detail(rows):
    label, revenue, bought, f_cogs, f_end, a_cogs, a_end, unit = rows[0]
    print("[2] 1년차를 풀어 본다 — 400개 사서 300개 팔았다 (문단 25·27)")
    print(f"    매입 합계 {bought:,}  /  매출 {revenue:,}")
    print(f"    선입선출 (가나전자): 팔린 300개 = 10·12·14 짜리 100개씩 → 매출원가 {f_cogs:,}")
    print(f"                         남은 100개 = 16 짜리             → 기말재고 {f_end:,}")
    print(f"    총평균   (다라물산): 단가 {bought:,} ÷ 400 = {unit:.2f}")
    print(f"                         팔린 300개 × {unit:.2f}          → 매출원가 {a_cogs:,.0f}")
    print(f"                         남은 100개 × {unit:.2f}          → 기말재고 {a_end:,.0f}")
    print(f"    매출원가 + 기말재고 = 매입 합계: 가나 {f_cogs + f_end:,} / 다라 {a_cogs + a_end:,.0f}")
    print()


def print_three_years(rows, totals):
    print("[3] 3년 동안 — 매출총이익과 기말재고")
    header = (
        "    연도        매출   선입 매출원가  평균 매출원가  선입 매출총이익  평균 매출총이익"
        "     차이  선입 기말재고  평균 기말재고"
    )
    print(header)
    for label, revenue, bought, f_cogs, f_end, a_cogs, a_end, unit in rows:
        f_gp = revenue - f_cogs
        a_gp = revenue - a_cogs
        print(
            f"    {label}  {revenue:>8,}  {f_cogs:>12,}  {a_cogs:>12,.0f}"
            f"  {f_gp:>14,}  {a_gp:>14,.0f}  {f_gp - a_gp:>+7,.0f}"
            f"  {f_end:>12,}  {a_end:>12,.0f}"
        )
    print(
        f"    3년 합계 매출총이익: 가나전자 {totals['fifo_gp']:,} / 다라물산 {totals['avg_gp']:,.0f}"
        f"  (차이 {totals['fifo_gp'] - totals['avg_gp']:+,.0f})"
    )
    print("    차이 = 기말재고 차이 — 3년 동안 같은 매입액 21,200 이 두 칸에 다르게 나뉜 결과다")
    print("    두 회사가 낸 현금(매입)과 받은 현금(매출)은 3년 내내 같다")
    print()


def print_nrv(fifo_layers, avg_qty, avg_cost, totals):
    nrv_unit = NRV_SELLING_PRICE - NRV_COST_TO_SELL
    fifo_qty = sum(q for q, _ in fifo_layers)
    fifo_cost = sum(q * c for q, c in fifo_layers)
    nrv_total = nrv_unit * avg_qty
    print("[4] 3년차 말 판매가가 떨어졌다 — 저가법 (문단 9·28·34)")
    print(
        f"    순실현가능가치 = 예상 판매가 {NRV_SELLING_PRICE} − 판매비용 {NRV_COST_TO_SELL}"
        f" = 개당 {nrv_unit}, 100개면 {nrv_total:,}"
    )
    print("    회사        장부 원가     순실현가능가치   평가손실   평가 후 장부금액")
    after = []
    companies = (
        ("가나전자", fifo_qty, fifo_cost, totals["fifo_gp"]),
        ("다라물산", avg_qty, avg_cost, totals["avg_gp"]),
    )
    for name, qty, cost, gp in companies:
        nrv = nrv_unit * qty
        loss = max(cost - nrv, 0)
        after.append((name, gp, loss))
        print(f"    {name}  {cost:>10,.0f}  {nrv:>14,}  {loss:>9,.0f}  {cost - loss:>14,.0f}")
    print("    같은 100개, 같은 순실현가능가치인데 원가 공식에 따라 평가손실이 다르다")
    print("    평가손실을 매출원가에 더한 3년 합계 매출총이익:")
    for name, gp, loss in after:
        print(f"      {name}  {gp:,.0f} − {loss:,.0f} = {gp - loss:,.0f}")


if __name__ == "__main__":
    print_purchases()
    rows, totals, fifo_layers, avg_qty, avg_cost = run()
    print_1st_year_detail(rows)
    print_three_years(rows, totals)
    print_nrv(fifo_layers, avg_qty, avg_cost, totals)
