"""관계기업 투자를 지분법과 연결로 각각 처리해 재무제표가 어떻게 달라지는지 계산한다.

가나전자가 마바소재 지분 40% 를 사들인 상황이다. 지분율을 고정하고 처리 방식만
바꿔 보려고, 같은 40% 를 유의적인 영향력(지분법)으로 볼 때와 지배력(연결)으로
볼 때를 나란히 계산한다. 금액 단위는 백만원이고 숫자는 모두 가상이다.
"""

OWNERSHIP = 0.40
PURCHASE_PRICE = 1200

# 마바소재 취득일 순자산. 공정가치와 장부금액이 같다고 둔다
INVESTEE_ASSETS_AT_ACQ = 6000
INVESTEE_LIABILITIES_AT_ACQ = 3500

# 마바소재 1년차: 매출, 순이익, 배당 총액, 기타포괄손익, 기말 부채
INVESTEE_YEAR1 = {"revenue": 5000, "net_income": 500, "dividend": 200,
                  "oci": 50, "liabilities_end": 3700}

# 가나전자 자체 영업 (투자 전): 자산, 부채, 매출, 순이익
INVESTOR_ASSETS = 10000
INVESTOR_LIABILITIES = 4000
INVESTOR_REVENUE = 8000
INVESTOR_OWN_NET_INCOME = 600

# 손실 구간을 보려고 1년차 뒤에 이어 붙이는 마바소재 순손익
LOSS_PATH = [("2년차", -2000), ("3년차", -2000), ("4년차", 1000)]


def classify(ratio):
    # 20%·50% 는 추정 기준이다. 반대 증거가 명백하면 뒤집힌다 (1028 문단 5)
    if ratio > 0.5:
        return "지배력 추정", "연결 (제1110호)"
    if ratio >= 0.2:
        return "유의적인 영향력 추정", "지분법 (제1028호)"
    return "영향력 없음 추정", "금융자산 (제1109호)"


def print_classification():
    print("[1] 지분율에 따른 처리 방식 (제1028호 문단 5, 추정은 반증 가능)")
    for ratio in (0.10, 0.19, 0.20, 0.40, 0.51):
        influence, method = classify(ratio)
        print(f"    {ratio:>4.0%}  {influence:<12} {method}")
    print("    20% 미만이라도 이사회 참여 등이 있으면 유의적인 영향력이 있을 수 있다 (문단 6)")


def equity_method_year1():
    net_assets = INVESTEE_ASSETS_AT_ACQ - INVESTEE_LIABILITIES_AT_ACQ
    share_of_net_assets = net_assets * OWNERSHIP
    goodwill = PURCHASE_PRICE - share_of_net_assets
    y = INVESTEE_YEAR1
    share_ni = y["net_income"] * OWNERSHIP
    share_div = y["dividend"] * OWNERSHIP
    share_oci = y["oci"] * OWNERSHIP
    carrying = PURCHASE_PRICE + share_ni - share_div + share_oci
    return {"net_assets": net_assets, "share": share_of_net_assets,
            "goodwill": goodwill, "share_ni": share_ni, "share_div": share_div,
            "share_oci": share_oci, "carrying": carrying}


def print_equity_method(e):
    y = INVESTEE_YEAR1
    print("[2] 지분법 장부금액 움직임 — 1년차 (문단 10·32)")
    print(f"    마바소재 취득일 순자산 {e['net_assets']:,} × 40% = {e['share']:,.0f}")
    print(f"    취득원가 {PURCHASE_PRICE:,} - 순자산 몫 {e['share']:,.0f} = 영업권 {e['goodwill']:,.0f} (장부금액에 포함)")
    print(f"    {'항목':<16}{'마바소재 전체':>10}{'40% 몫':>10}{'장부금액':>10}")
    print(f"    {'취득':<16}{'':>10}{'':>10}{PURCHASE_PRICE:>10,.0f}")
    running = PURCHASE_PRICE + e["share_ni"]
    print(f"    {'당기순이익 → 지분법이익':<12}{y['net_income']:>10,}{e['share_ni']:>+10,.0f}{running:>10,.0f}")
    running -= e["share_div"]
    print(f"    {'배당 수령 → 장부 감소':<13}{y['dividend']:>10,}{-e['share_div']:>+10,.0f}{running:>10,.0f}")
    running += e["share_oci"]
    print(f"    {'기타포괄손익':<16}{y['oci']:>10,}{e['share_oci']:>+10,.0f}{running:>10,.0f}")
    end_net_assets = e["net_assets"] + y["net_income"] - y["dividend"] + y["oci"]
    print(f"    검산: 기말 순자산 {end_net_assets:,} × 40% = {end_net_assets * OWNERSHIP:,.0f} + 영업권 {e['goodwill']:,.0f} = {end_net_assets * OWNERSHIP + e['goodwill']:,.0f}")


def investor_statements(e):
    y = INVESTEE_YEAR1
    # 가나전자 자체 자산: 현금으로 지분을 사고, 자기 이익과 받은 배당만큼 늘어난다
    own_assets = INVESTOR_ASSETS - PURCHASE_PRICE + INVESTOR_OWN_NET_INCOME + e["share_div"]

    eq_assets = own_assets + e["carrying"]
    eq_liab = INVESTOR_LIABILITIES
    eq_equity = eq_assets - eq_liab
    eq_ni = INVESTOR_OWN_NET_INCOME + e["share_ni"]

    investee_net_end = e["net_assets"] + y["net_income"] - y["dividend"] + y["oci"]
    investee_assets_end = investee_net_end + y["liabilities_end"]
    # 비지배지분은 식별가능 순자산의 비례 몫으로 측정한다고 둔다 (제1103호 문단 19)
    nci = investee_net_end * (1 - OWNERSHIP)
    co_assets = own_assets + investee_assets_end + e["goodwill"]
    co_liab = INVESTOR_LIABILITIES + y["liabilities_end"]
    co_equity_total = co_assets - co_liab
    co_parent_equity = co_equity_total - nci
    co_ni = INVESTOR_OWN_NET_INCOME + y["net_income"]
    co_ni_parent = INVESTOR_OWN_NET_INCOME + y["net_income"] * OWNERSHIP

    return [
        ("매출", INVESTOR_REVENUE, INVESTOR_REVENUE + y["revenue"]),
        ("당기순이익", eq_ni, co_ni),
        ("  지배기업 소유주 몫", eq_ni, co_ni_parent),
        ("  비지배지분 몫", 0, co_ni - co_ni_parent),
        ("자산총계", eq_assets, co_assets),
        ("  관계기업투자", e["carrying"], 0),
        ("부채총계", eq_liab, co_liab),
        ("자본총계", eq_equity, co_equity_total),
        ("  지배기업 소유주지분", eq_equity, co_parent_equity),
        ("  비지배지분", 0, nci),
        ("부채비율(%)", eq_liab / eq_equity * 100, co_liab / co_equity_total * 100),
        ("지배기업 ROE(%)", eq_ni / eq_equity * 100, co_ni_parent / co_parent_equity * 100),
    ]


def print_comparison(rows):
    print("[3] 같은 40% 지분, 처리 방식만 바꾼 가나전자 1년차 재무제표")
    print(f"    {'항목':<18}{'지분법':>10}{'연결(가정)':>12}")
    for name, eq, co in rows:
        print(f"    {name:<18}{eq:>10,.1f}{co:>12,.1f}" if "%" in name
              else f"    {name:<18}{eq:>10,.0f}{co:>12,.0f}")
    print("    지배기업 몫 순이익과 자본은 같고, 매출·자산·부채만 달라진다")


def print_losses(e):
    print("[4] 관계기업 손실이 장부금액을 넘으면 — 0 에서 멈춘다 (문단 38·39)")
    print(f"    {'연도':<6}{'마바 순손익':>10}{'40% 몫':>9}{'인식액':>9}{'미인식 누계':>11}{'장부금액':>9}")
    carrying = e["carrying"]
    unrecognized = 0.0
    print(f"    {'1년차 말':<6}{'':>10}{'':>9}{'':>9}{unrecognized:>11,.0f}{carrying:>9,.0f}")
    for year, ni in LOSS_PATH:
        share = ni * OWNERSHIP
        if share < 0:
            recognized = max(share, -carrying)
            unrecognized += recognized - share
        else:
            # 이익은 앞서 인식하지 못한 손실을 먼저 메운 뒤에야 인식한다
            offset = min(share, unrecognized)
            unrecognized -= offset
            recognized = share - offset
        carrying += recognized
        print(f"    {year:<7}{ni:>10,}{share:>+9,.0f}{recognized:>+9,.0f}{unrecognized:>11,.0f}{carrying:>9,.0f}")
    print("    법적·의제의무가 없으면 0 아래로 부채를 잡지 않는다")


def main():
    print_classification()
    print()
    e = equity_method_year1()
    print_equity_method(e)
    print()
    print_comparison(investor_statements(e))
    print()
    print_losses(e)


if __name__ == "__main__":
    main()
