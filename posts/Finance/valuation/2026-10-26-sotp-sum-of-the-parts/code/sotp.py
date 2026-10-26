"""가상 지주회사 가나홀딩스를 단일 배수와 SOTP 두 방식으로 평가한다.

세 사업부의 성격이 전부 다르다. 하나는 고성장 소재, 하나는 저성장 유통,
하나는 EBITDA 가 뜻을 갖지 못하는 금융이다. 전사 EBITDA 에 배수 하나를
곱하면 어디서 어긋나는지, 부문별로 쪼개면 그 어긋남이 얼마나 되돌아오는지
숫자로 본다. 파이썬 표준 라이브러리만 쓴다.
"""

# 단위는 전부 억원. 발행주식수만 만주.
SHARES_OUT = 2_000  # 만주

# --- 사업부문 (연결 기준) ---------------------------------------------------
# K-IFRS 제1108호 문단 13 의 양적기준(수익·손익·자산 각 10%)을 셋 다 넘으므로
# 세 부문 모두 별도 보고부문이 된다. 그래서 공시에서 이 숫자를 꺼낼 수 있다.
SEGMENTS = [
    # 이름,        수익,   EBITDA, 자산,   비교배수,  배수종류
    ("반도체소재", 4_000,    800,  5_000,   11.0, "EV/EBITDA"),
    ("유통",       6_000,    300,  2_500,    5.5, "EV/EBITDA"),
]

# 금융(캐피탈) 부문은 이자가 영업수익이라 EBITDA 가 영업성과를 뜻하지 않는다.
# 자기자본 대비 배수로 따로 평가한다.
FIN_NAME = "캐피탈"
FIN_REVENUE = 1_200
FIN_PRETAX = 250
FIN_ASSET = 12_000
FIN_EQUITY = 2_000
FIN_PBR = 0.7
FIN_OWNERSHIP = 0.60  # 가나홀딩스 보유 지분율. 나머지 40%는 비지배지분

# --- 지주회사 자체 ----------------------------------------------------------
HQ_COST = 120          # 어느 부문에도 배분되지 않은 본사 운영비 (연간)
NONFIN_NET_DEBT = 2_800   # 비금융 부문 순차입금
FIN_DEBT = 9_000          # 금융부문 차입금 — 영업을 위한 조달이다
FIN_CASH = 500

# 전사 하나로 묶었을 때 쓰이는 "복합기업 평균" 배수
BLENDED_MULTIPLE = 8.0


def line(title):
    print()
    print(title)
    print("-" * len(title) * 2)


def won(x):
    return f"{x:>10,.0f}"


def single_multiple():
    """전사 EBITDA 에 배수 하나를 곱하는 방식."""
    line("[1] 단일 배수 — 전사 EBITDA 에 복합기업 평균 배수를 곱한다")

    seg_ebitda = sum(s[2] for s in SEGMENTS)
    # 금융부문 세전이익을 EBITDA 자리에 그대로 끼워 넣는 흔한 처리
    total_ebitda = seg_ebitda + FIN_PRETAX - HQ_COST
    ev = total_ebitda * BLENDED_MULTIPLE

    print(f"  비금융 부문 EBITDA 합계      {won(seg_ebitda)}")
    print(f"  금융부문 세전이익 가산       {won(FIN_PRETAX)}")
    print(f"  본사 미배분비용 차감         {won(-HQ_COST)}")
    print(f"  전사 EBITDA                  {won(total_ebitda)}")
    print(f"  × 복합기업 평균 배수 {BLENDED_MULTIPLE:.1f}배")
    print(f"  = 기업가치(EV)               {won(ev)}")

    consolidated_net_debt = NONFIN_NET_DEBT + FIN_DEBT - FIN_CASH
    equity = ev - consolidated_net_debt
    print(f"  - 연결 순차입금              {won(-consolidated_net_debt)}"
          f"   (비금융 {NONFIN_NET_DEBT:,} + 금융 {FIN_DEBT:,} - 현금 {FIN_CASH:,})")
    print(f"  = 지분가치                   {won(equity)}")
    print(f"  주당가치                     {won(equity * 10_000 / SHARES_OUT)} 원")
    return equity


def sotp(holdco_discount=0.0, verbose=True):
    """부문별로 다른 배수를 적용해 합산하는 방식."""
    if verbose:
        line("[2] SOTP — 부문마다 배수를 따로 적용해 더한다")

    seg_ev = []
    for name, rev, ebitda, asset, mult, kind in SEGMENTS:
        value = ebitda * mult
        seg_ev.append((name, ebitda, mult, value))
        if verbose:
            print(f"  {name:<10} EBITDA {ebitda:>5,} × {mult:>4.1f}배 "
                  f"= {won(value)}")

    nonfin_ev = sum(v for _, _, _, v in seg_ev)
    nonfin_ebitda = sum(e for _, e, _, _ in seg_ev)

    # 본사비용은 어느 부문 EBITDA 에도 들어 있지 않다. 영구히 나간다고 보고
    # 부문 가중평균 배수로 자본화해 음수 항목으로 세운다.
    weighted_multiple = nonfin_ev / nonfin_ebitda
    hq_value = -HQ_COST * weighted_multiple
    if verbose:
        print(f"  {'본사비용':<10} 연 {HQ_COST:>5,} × {weighted_multiple:>4.1f}배 "
              f"= {won(hq_value)}   (부문 가중평균 배수로 자본화)")

    nonfin_ev_total = nonfin_ev + hq_value
    nonfin_equity = nonfin_ev_total - NONFIN_NET_DEBT
    if verbose:
        print(f"  비금융 EV 합계               {won(nonfin_ev_total)}")
        print(f"  - 비금융 순차입금            {won(-NONFIN_NET_DEBT)}"
              f"   (금융부문 차입금 {FIN_DEBT:,} 은 여기 넣지 않는다)")
        print(f"  = 비금융 지분가치            {won(nonfin_equity)}")

    fin_equity_full = FIN_EQUITY * FIN_PBR
    fin_equity_own = fin_equity_full * FIN_OWNERSHIP
    if verbose:
        print()
        print(f"  {FIN_NAME:<10} 자기자본 {FIN_EQUITY:>5,} × PBR {FIN_PBR:.1f}배 "
              f"= {won(fin_equity_full)}")
        print(f"  {'':<10} × 지분율 {FIN_OWNERSHIP:.0%}"
              f"{'':>14}= {won(fin_equity_own)}   (나머지는 비지배지분)")

    gross_equity = nonfin_equity + fin_equity_own
    discounted = gross_equity * (1 - holdco_discount)
    if verbose:
        print()
        print(f"  합산 지분가치                {won(gross_equity)}")
        print(f"  - 지주회사 할인 {holdco_discount:.0%}"
              f"{'':>12}{won(-(gross_equity - discounted))}")
        print(f"  = 주주귀속 가치              {won(discounted)}")
        print(f"  주당가치                     "
              f"{won(discounted * 10_000 / SHARES_OUT)} 원")
    return discounted


def segment_check():
    """세 부문이 K-IFRS 제1108호 문단 13 의 양적기준을 넘는지 확인한다."""
    line("[0] 보고부문 양적기준 — 세 부문이 공시에 따로 나오는가")

    rows = [(n, rev, asset) for n, rev, _, asset, _, _ in SEGMENTS]
    rows.append((FIN_NAME, FIN_REVENUE, FIN_ASSET))
    total_rev = sum(r for _, r, _ in rows)
    total_asset = sum(a for _, _, a in rows)

    print(f"  {'부문':<10}{'수익':>8}{'비중':>8}{'자산':>9}{'비중':>8}  10% 기준")
    for name, rev, asset in rows:
        rs, as_ = rev / total_rev, asset / total_asset
        passed = "충족" if rs >= 0.10 or as_ >= 0.10 else "미달"
        print(f"  {name:<10}{rev:>8,}{rs:>7.1%}{asset:>9,}{as_:>7.1%}  {passed}")
    print(f"  {'합계':<10}{total_rev:>8,}{'':>7}{total_asset:>9,}")


def discount_sensitivity():
    line("[3] 지주회사 할인율을 바꿔 본다")
    zero = sotp(holdco_discount=0.0, verbose=False)
    print(f"  {'할인율':>8}{'주주귀속 가치':>16}{'주당가치':>14}"
          f"{'할인 전 대비':>16}")
    for d in (0.00, 0.10, 0.20, 0.30, 0.40):
        v = sotp(holdco_discount=d, verbose=False)
        print(f"  {d:>7.0%}{v:>16,.0f}{v * 10_000 / SHARES_OUT:>13,.0f} 원"
              f"{v - zero:>16,.0f}")


def multiple_sensitivity():
    line("[4] 부문 배수를 하나씩 움직여 본다 — 어느 부문이 결론을 쥐는가")
    print(f"  {'대상 부문':<12}{'배수 -2배':>14}{'기준':>12}{'배수 +2배':>14}"
          f"{'폭':>10}")
    base_defs = [list(s) for s in SEGMENTS]
    for i, (name, _, ebitda, _, mult, _) in enumerate(SEGMENTS):
        values = []
        for delta in (-2.0, 0.0, 2.0):
            SEGMENTS[i] = tuple(base_defs[i][:4] + [mult + delta] + base_defs[i][5:])
            values.append(sotp(holdco_discount=0.20, verbose=False))
        SEGMENTS[i] = tuple(base_defs[i])
        span = values[2] - values[0]
        print(f"  {name:<12}{values[0]:>14,.0f}{values[1]:>12,.0f}"
              f"{values[2]:>14,.0f}{span:>10,.0f}")


def omission_cost():
    """SOTP 에서 자주 빠뜨리는 항목을 하나씩 빼고 주당가치를 다시 구한다."""
    global HQ_COST, FIN_OWNERSHIP, NONFIN_NET_DEBT
    line("[5] 자주 빠뜨리는 항목 — 하나씩 빼고 다시 계산한다")

    base = sotp(holdco_discount=0.20, verbose=False)
    rows = [("기준 (전부 반영)", base)]

    keep_hq, HQ_COST = HQ_COST, 0
    rows.append(("본사비용을 안 뺐을 때", sotp(holdco_discount=0.20, verbose=False)))
    HQ_COST = keep_hq

    keep_own, FIN_OWNERSHIP = FIN_OWNERSHIP, 1.0
    rows.append(("지분율 60%를 안 썼을 때", sotp(holdco_discount=0.20, verbose=False)))
    FIN_OWNERSHIP = keep_own

    keep_debt = NONFIN_NET_DEBT
    NONFIN_NET_DEBT = keep_debt + FIN_DEBT - FIN_CASH
    rows.append(("금융차입금까지 뺐을 때", sotp(holdco_discount=0.20, verbose=False)))
    NONFIN_NET_DEBT = keep_debt

    print(f"  {'경우':<26}{'주주귀속 가치':>14}{'주당가치':>14}{'기준 대비':>12}")
    for name, v in rows:
        per = v * 10_000 / SHARES_OUT
        gap = "—" if v == base else f"{v - base:+,.0f}"
        print(f"  {name:<26}{v:>14,.0f}{per:>11,.0f} 원{gap:>12}")


if __name__ == "__main__":
    segment_check()
    single_multiple()
    sotp(holdco_discount=0.20)
    discount_sensitivity()
    multiple_sensitivity()
    omission_cost()
