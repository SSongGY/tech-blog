"""같은 금융자산을 세 가지로 분류했을 때 손익과 자본이 어떻게 갈리는지 계산한다.

K-IFRS 제1109호의 분류 — 상각후원가(AC), 기타포괄손익-공정가치(FVOCI),
당기손익-공정가치(FVPL) — 를 가상 회사에 적용한다. 금액은 백만원이다.
"""

# 채권: 액면 1,000, 표면이자 연 5%, 3년 만기, 1년차 초에 액면으로 취득
FACE = 1000
COUPON_RATE = 0.05
YEARS = 3
# 해마다 말의 시장수익률. 이 값으로 남은 현금흐름을 할인해 공정가치를 정한다
MARKET_YIELDS = [0.07, 0.04, None]  # 3년차 말은 만기라 액면 상환

# 주식: 취득 500, 1년차 말 공정가치 600, 2년차 말 450 에 처분, 해마다 배당 20
SHARE_COST = 500
SHARE_FAIR_VALUES = [600, 450]
SHARE_DIVIDEND = 20


def classify(kind, sppi, business_model, oci_election=False, held_for_trading=False):
    """제1109호 문단 4.1.1~4.1.4 의 판단 순서를 그대로 옮긴다."""
    if kind == "지분상품":
        # 단기매매가 아닐 때만 최초 인식 시점에 취소불가로 선택할 수 있다 (문단 5.7.5)
        if oci_election and not held_for_trading:
            return "FVOCI (재분류 없음)"
        return "FVPL"
    if not sppi:
        return "FVPL"
    if business_model == "수취":
        return "AC"
    if business_model == "수취와 매도":
        return "FVOCI (처분 시 재분류)"
    return "FVPL"


CASES = [
    ("국고채, 만기까지 보유", "채무상품", True, "수취", False, False),
    ("국고채, 유동성 관리용", "채무상품", True, "수취와 매도", False, False),
    ("국고채, 트레이딩 데스크", "채무상품", True, "매매", False, False),
    ("전환사채", "채무상품", False, "수취", False, False),
    ("전략적 보유 비상장 주식", "지분상품", None, None, True, False),
    ("단기 시세차익용 상장 주식", "지분상품", None, None, False, True),
]


def print_classification():
    print("[1] 분류 판단 — 계약상 현금흐름 특성과 사업모형 (문단 4.1.1~4.1.4, 5.7.5)")
    print(f"    {'보유 자산':<16}{'원금·이자만':<8}{'사업모형':<9}{'분류'}")
    for name, kind, sppi, model, election, trading in CASES:
        sppi_text = "-" if sppi is None else ("예" if sppi else "아니오")
        model_text = "-" if model is None else model
        result = classify(kind, sppi, model, election, trading)
        print(f"    {name:<16}{sppi_text:<10}{model_text:<10}{result}")


def bond_fair_value(year_index):
    yld = MARKET_YIELDS[year_index]
    if yld is None:
        return float(FACE)
    remaining = YEARS - (year_index + 1)
    coupon = FACE * COUPON_RATE
    value = sum(coupon / (1 + yld) ** t for t in range(1, remaining + 1))
    return value + FACE / (1 + yld) ** remaining


def print_bond():
    coupon = FACE * COUPON_RATE
    print("[2] 같은 채권 1,000 을 세 회사가 다르게 분류 (문단 4.1.2·4.1.2A·5.7.1·5.7.10·5.7.11)")
    print(f"    액면 {FACE:,}, 표면이자 {COUPON_RATE:.0%}, {YEARS}년 만기, 액면 취득")
    print(f"    {'연도':<5}{'시장수익률':>8}{'공정가치':>9}{'변동':>8}"
          f" | {'AC 손익':>7} | {'FVOCI 손익':>9}{'OCI':>7} | {'FVPL 손익':>8}")
    prev = float(FACE)
    totals = {"ac": 0.0, "oci_pl": 0.0, "oci": 0.0, "pl": 0.0}
    for i in range(YEARS):
        fv = bond_fair_value(i)
        change = fv - prev
        yld = MARKET_YIELDS[i]
        yld_text = "만기" if yld is None else f"{yld:.0%}"
        ac_pl = coupon
        fvoci_pl = coupon
        fvoci_oci = change
        fvpl_pl = coupon + change
        totals["ac"] += ac_pl
        totals["oci_pl"] += fvoci_pl
        totals["oci"] += fvoci_oci
        totals["pl"] += fvpl_pl
        print(f"    {i + 1}년차{yld_text:>9}{fv:>10,.1f}{change:>+9.1f}"
              f" | {ac_pl:>8.1f} | {fvoci_pl:>10.1f}{fvoci_oci:>+8.1f} | {fvpl_pl:>9.1f}")
        prev = fv
    print(f"    {'합계':<23}"
          f" | {totals['ac']:>8.1f} | {totals['oci_pl']:>10.1f}{totals['oci']:>+8.1f} | {totals['pl']:>9.1f}")
    print("    1년차 말 재무상태표 장부금액: "
          f"AC {FACE:,.1f} / FVOCI {bond_fair_value(0):,.1f} / FVPL {bond_fair_value(0):,.1f}")
    print("    FVOCI 의 당기손익은 AC 와 같고, 공정가치 변동은 OCI 에 쌓였다가 만기에 0 으로 돌아온다")


def print_equity():
    print("[3] 같은 주식 500 — FVPL 과 FVOCI 선택 (문단 5.7.1·5.7.5·5.7.6, B5.7.1)")
    print(f"    {'연도':<6}{'공정가치':>8}{'변동':>8} | {'FVPL 손익':>9} | {'FVOCI 손익':>9}{'OCI':>8}")
    prev = SHARE_COST
    pl_total = 0
    oci_pl_total = 0
    oci_total = 0
    for i, fv in enumerate(SHARE_FAIR_VALUES):
        change = fv - prev
        fvpl = change + SHARE_DIVIDEND
        # 배당은 FVOCI 를 골라도 당기손익이다
        fvoci_pl = SHARE_DIVIDEND
        pl_total += fvpl
        oci_pl_total += fvoci_pl
        oci_total += change
        label = f"{i + 1}년차" + (" 처분" if i == len(SHARE_FAIR_VALUES) - 1 else "")
        print(f"    {label:<7}{fv:>8,}{change:>+8} | {fvpl:>+10} | {fvoci_pl:>+10}{change:>+8}")
        prev = fv
    print(f"    {'합계':<20} | {pl_total:>+10} | {oci_pl_total:>+10}{oci_total:>+8}")
    print(f"    처분 후 FVOCI 의 OCI 누계 {oci_total:+} 은 당기손익으로 재분류되지 않는다 (자본 안에서 이익잉여금으로만 옮길 수 있다)")
    print(f"    두 방식의 총포괄손익은 {pl_total:+} 으로 같고, 당기손익 합계만 {pl_total:+} 대 {oci_pl_total:+} 로 갈린다")


def main():
    print_classification()
    print()
    print_bond()
    print()
    print_equity()


if __name__ == "__main__":
    main()
