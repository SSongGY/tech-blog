"""잔여이익모형(RIM)과 배당할인모형(DDM)을 같은 가정으로 돌려 비교한다.

가상 회사 `사아정밀` 하나를 두고
  [1] 잔여이익을 연도별로 만들어 RIM 가치를 구하고
  [2] 같은 가정에서 DDM 이 같은 값을 내는지 검산하고
  [3] 두 모형이 가치를 어디서 가져오는지(장부가 / 추정기간 / 종료가치) 나누고
  [4] 추정이 빗나갔을 때 어느 쪽이 덜 흔들리는지 재고
  [5] 장부가가 당기순이익과 배당 말고 다른 경로로 움직일 때(clean surplus 위반)
      RIM 이 얼마나 틀리는지 본다.

숫자는 전부 설명용 가정값이고 실재하는 기업과 관계가 없다. 표준 라이브러리만 쓴다.
"""

# --- 사아정밀의 가정 -------------------------------------------------------
# 단위: 억원. 전부 설명을 위해 만든 값이다.
BOOK_VALUE_0 = 1_000.0      # 기초 자기자본 장부금액
COST_OF_EQUITY = 0.09       # 자기자본비용 r
PAYOUT_RATIO = 0.40         # 배당성향 (당기순이익 대비)
FORECAST_YEARS = 5          # 명시적으로 추정하는 기간
ROE_FORECAST = [0.15, 0.14, 0.13, 0.12, 0.11]   # 연도별 자기자본이익률
TERMINAL_ROE = 0.10         # 추정기간 이후 영구히 유지된다고 본 ROE
TERMINAL_GROWTH = 0.03      # 추정기간 이후 영구성장률 g


def project(book_value_0, roe_list, payout, terminal_roe, years):
    """연도별 기초장부가·순이익·배당·기말장부가를 만든다.

    clean surplus 관계(기말 장부가 = 기초 장부가 + 순이익 - 배당)를 그대로 쓴다.
    이 관계가 성립해야 RIM 과 DDM 이 같은 답을 낸다.
    """
    rows = []
    book = book_value_0
    for year in range(1, years + 1):
        roe = roe_list[year - 1] if year <= len(roe_list) else terminal_roe
        net_income = book * roe
        dividend = net_income * payout
        closing = book + net_income - dividend
        rows.append({
            "year": year,
            "opening_book": book,
            "roe": roe,
            "net_income": net_income,
            "dividend": dividend,
            "closing_book": closing,
        })
        book = closing
    return rows


def discount(amount, rate, year):
    return amount / (1 + rate) ** year


def terminal_payout(terminal_roe, growth):
    """종료 단계의 배당성향은 자유롭게 고를 수 없다.

    장부가가 g 로 영구성장하려면 유보한 돈이 그만큼만 늘어야 하므로
    g = ROE x (1 - 배당성향) 이 성립해야 한다. 추정기간 성향을 그대로
    종료 단계에 쓰면 장부가 성장률과 배당 성장률이 어긋나고,
    RIM 과 DDM 이 다른 답을 낸다.
    """
    return 1 - growth / terminal_roe


def rim_value(rows, rate, terminal_roe, growth):
    """RIM: 기초 장부가 + 추정기간 잔여이익의 현재가치 + 종료 잔여이익의 현재가치."""
    pv_residual = 0.0
    details = []
    for row in rows:
        residual = row["net_income"] - rate * row["opening_book"]
        pv = discount(residual, rate, row["year"])
        pv_residual += pv
        details.append({**row, "residual": residual, "pv_residual": pv})

    # 추정기간 다음 해의 잔여이익이 g 로 영구성장한다고 본다.
    last_book = rows[-1]["closing_book"]
    terminal_residual = last_book * (terminal_roe - rate)
    terminal_value = terminal_residual / (rate - growth)
    pv_terminal = discount(terminal_value, rate, len(rows))

    total = rows[0]["opening_book"] + pv_residual + pv_terminal
    return {
        "book_value_0": rows[0]["opening_book"],
        "pv_residual": pv_residual,
        "terminal_residual": terminal_residual,
        "terminal_value": terminal_value,
        "pv_terminal": pv_terminal,
        "total": total,
        "details": details,
    }


def ddm_value(rows, rate, terminal_roe, growth):
    """DDM: 추정기간 배당의 현재가치 + 종료 배당의 현재가치.

    종료 배당은 추정기간 다음 해의 순이익에 종료 배당성향을 곱해 만든다.
    RIM 과 같은 가정을 쓰므로 두 결과는 같아야 한다.
    """
    pv_dividend = sum(discount(row["dividend"], rate, row["year"]) for row in rows)

    last_book = rows[-1]["closing_book"]
    next_income = last_book * terminal_roe
    next_dividend = next_income * terminal_payout(terminal_roe, growth)
    terminal_value = next_dividend / (rate - growth)
    pv_terminal = discount(terminal_value, rate, len(rows))

    return {
        "pv_dividend": pv_dividend,
        "terminal_value": terminal_value,
        "pv_terminal": pv_terminal,
        "total": pv_dividend + pv_terminal,
    }


def won(value):
    return f"{value:>10,.1f}"


def pct(value):
    return f"{value * 100:>7.2f}%"


# --- [1] 잔여이익을 연도별로 만든다 ----------------------------------------
rows = project(BOOK_VALUE_0, ROE_FORECAST, PAYOUT_RATIO, TERMINAL_ROE, FORECAST_YEARS)
rim = rim_value(rows, COST_OF_EQUITY, TERMINAL_ROE, TERMINAL_GROWTH)

print(f"[1] 사아정밀 — 잔여이익을 연도별로 만든다 (단위: 억원, r = {pct(COST_OF_EQUITY).strip()})")
print("     연도   기초장부가      ROE      순이익  자본비용분    잔여이익   할인계수    현재가치")
for row in rim["details"]:
    charge = COST_OF_EQUITY * row["opening_book"]
    factor = 1 / (1 + COST_OF_EQUITY) ** row["year"]
    print(
        f"      {row['year']}년 {won(row['opening_book'])} {pct(row['roe'])}"
        f" {won(row['net_income'])} {won(charge)} {won(row['residual'])}"
        f"     {factor:.4f} {won(row['pv_residual'])}"
    )
print(f"  기초 장부가                {won(rim['book_value_0'])}")
print(f"  추정기간 잔여이익의 현재가치 {won(rim['pv_residual'])}")
print(f"  종료 잔여이익 {rim['terminal_residual']:,.1f} / (r - g) = {rim['terminal_value']:,.1f}"
      f" → 현재가치 {rim['pv_terminal']:,.1f}")
print(f"  RIM 평가액                 {won(rim['total'])}")
print(f"  장부가 대비 배수(PBR)       {rim['total'] / rim['book_value_0']:.3f} 배")
print()

# --- [2] 같은 가정을 DDM 으로 돌려 검산한다 --------------------------------
ddm = ddm_value(rows, COST_OF_EQUITY, TERMINAL_ROE, TERMINAL_GROWTH)
print("[2] 같은 가정을 배당할인모형으로 돌려 본다 (검산)")
print(f"  종료 배당성향 = 1 - g/ROE = 1 - {TERMINAL_GROWTH}/{TERMINAL_ROE}"
      f" = {terminal_payout(TERMINAL_ROE, TERMINAL_GROWTH) * 100:.1f}%"
      f"  (추정기간 {PAYOUT_RATIO * 100:.0f}% 와 다르다)")
print(f"  추정기간 배당의 현재가치     {won(ddm['pv_dividend'])}")
print(f"  종료 배당의 현재가치         {won(ddm['pv_terminal'])}")
print(f"  DDM 평가액                 {won(ddm['total'])}")
print(f"  RIM 평가액                 {won(rim['total'])}")
print(f"  차이                       {won(ddm['total'] - rim['total'])}"
      f"  (clean surplus 가 성립하면 0 이다)")
print()

# --- [3] 가치를 어디서 가져오는가 ------------------------------------------
print("[3] 평가액을 구성 요소로 나눈다 (단위: 억원)")
print("  모형   구성요소                       금액      비중")
for label, amount in [
    ("기초 장부가", rim["book_value_0"]),
    ("추정기간 잔여이익", rim["pv_residual"]),
    ("종료 잔여이익", rim["pv_terminal"]),
]:
    print(f"  RIM    {label:<22} {won(amount)}  {amount / rim['total'] * 100:>7.1f}%")
for label, amount in [
    ("추정기간 배당", ddm["pv_dividend"]),
    ("종료 배당", ddm["pv_terminal"]),
]:
    print(f"  DDM    {label:<22} {won(amount)}  {amount / ddm['total'] * 100:>7.1f}%")
print(f"  종료가치 비중: RIM {rim['pv_terminal'] / rim['total'] * 100:.1f}%"
      f" vs DDM {ddm['pv_terminal'] / ddm['total'] * 100:.1f}%")
print()

# --- [4] 추정이 빗나가면 어느 쪽이 더 흔들리는가 ----------------------------
print("[4] 가정을 흔들어 본다 — 같은 변화에 두 모형이 각각 몇 % 움직이는가")
print("  흔든 값                       RIM 평가액   변동률   DDM 평가액   변동률")


def shock(label, roe_list=None, terminal_roe=None, growth=None, payout=None):
    r_list = roe_list if roe_list is not None else ROE_FORECAST
    t_roe = terminal_roe if terminal_roe is not None else TERMINAL_ROE
    g = growth if growth is not None else TERMINAL_GROWTH
    p = payout if payout is not None else PAYOUT_RATIO
    shocked_rows = project(BOOK_VALUE_0, r_list, p, t_roe, FORECAST_YEARS)
    r_value = rim_value(shocked_rows, COST_OF_EQUITY, t_roe, g)["total"]
    d_value = ddm_value(shocked_rows, COST_OF_EQUITY, t_roe, g)["total"]
    print(
        f"  {label:<28} {won(r_value)} {(r_value / rim['total'] - 1) * 100:>7.1f}%"
        f" {won(d_value)} {(d_value / ddm['total'] - 1) * 100:>7.1f}%"
    )


shock("기준")
shock("영구성장률 3% → 3.5%", growth=0.035)
shock("영구성장률 3% → 2.5%", growth=0.025)
shock("종료 ROE 10% → 9.5%", terminal_roe=0.095)
shock("추정기간 ROE 전부 -1%p", roe_list=[r - 0.01 for r in ROE_FORECAST])
shock("배당성향 40% → 20%", payout=0.20)
print("  두 열이 모든 줄에서 같다. 가정을 맞춰 두면 같은 모형이기 때문이다.")
print()

# --- [4-2] 종료가치를 아예 믿지 않는다면 ------------------------------------
# 종료가치는 6년 뒤부터 영원히를 한 줄로 요약한 값이라 가장 믿기 어려운 항이다.
# 그 항을 통째로 버렸을 때 손에 남는 값을 본다.
rim_truncated = rim["book_value_0"] + rim["pv_residual"]
ddm_truncated = ddm["pv_dividend"]
print("[4-2] 종료가치 항을 통째로 버리면 얼마가 남는가 (단위: 억원)")
print(f"  RIM  기초 장부가 + 추정기간 잔여이익 = {rim_truncated:,.1f}"
      f"  → 전체의 {rim_truncated / rim['total'] * 100:.1f}%")
print(f"  DDM  추정기간 배당만              = {ddm_truncated:,.1f}"
      f"  → 전체의 {ddm_truncated / ddm['total'] * 100:.1f}%")
print("  → 값은 같아도 추정에 기대는 몫이 다르다. RIM 이 남기는 1,000.0 억은")
print("     추정값이 아니라 재무상태표에서 그대로 읽은 금액이다.")
print()

# --- [5] ROE 가 자기자본비용과 같으면 ---------------------------------------
flat_rows = project(BOOK_VALUE_0, [COST_OF_EQUITY] * FORECAST_YEARS,
                    PAYOUT_RATIO, COST_OF_EQUITY, FORECAST_YEARS)
flat = rim_value(flat_rows, COST_OF_EQUITY, COST_OF_EQUITY, TERMINAL_GROWTH)
print(f"[5] ROE 를 전 기간 자기자본비용과 같은 {pct(COST_OF_EQUITY).strip()} 로 두면")
print(f"  연도별 잔여이익            "
      + " ".join(f"{row['residual']:.1f}" for row in flat["details"]))
print(f"  종료 잔여이익              {flat['terminal_residual']:.1f}")
print(f"  RIM 평가액                 {won(flat['total'])}")
print(f"  기초 장부가                {won(flat['book_value_0'])}")
print(f"  → 평가액이 장부가와 같아진다. PBR {flat['total'] / flat['book_value_0']:.3f} 배")
print()

# --- [6] clean surplus 가 깨지면 --------------------------------------------
# 당기순이익과 배당을 거치지 않고 자기자본이 움직이는 경로가 있다. 기타포괄손익이
# 대표적이다. 여기서는 매년 20억이 기타포괄손익으로 자본에 직접 쌓인다고 본다.
OCI_PER_YEAR = 20.0

dirty_rows = []
book = BOOK_VALUE_0
for year in range(1, FORECAST_YEARS + 1):
    roe = ROE_FORECAST[year - 1]
    net_income = book * roe
    dividend = net_income * PAYOUT_RATIO
    closing = book + net_income - dividend + OCI_PER_YEAR   # OCI 가 추가로 쌓인다
    dirty_rows.append({
        "year": year, "opening_book": book, "roe": roe,
        "net_income": net_income, "dividend": dividend, "closing_book": closing,
    })
    book = closing

dirty_rim = rim_value(dirty_rows, COST_OF_EQUITY, TERMINAL_ROE, TERMINAL_GROWTH)
dirty_ddm = ddm_value(dirty_rows, COST_OF_EQUITY, TERMINAL_ROE, TERMINAL_GROWTH)

print(f"[6] 매년 {OCI_PER_YEAR:.0f} 억이 당기순이익을 거치지 않고 자본에 직접 쌓이면"
      " (clean surplus 위반)")
print("     연도   기초장부가      순이익        배당        OCI  기말장부가")
for row in dirty_rows:
    print(
        f"      {row['year']}년 {won(row['opening_book'])} {won(row['net_income'])}"
        f" {won(row['dividend'])} {won(OCI_PER_YEAR)} {won(row['closing_book'])}"
    )
print(f"  RIM 평가액                 {won(dirty_rim['total'])}")
print(f"  DDM 평가액                 {won(dirty_ddm['total'])}")
gap = dirty_rim["total"] - dirty_ddm["total"]
annuity = sum(discount(OCI_PER_YEAR, COST_OF_EQUITY, y) for y in range(1, FORECAST_YEARS + 1))
print(f"  차이                       {won(gap)}"
      f"  (RIM 이 {abs(gap) / dirty_ddm['total'] * 100:.1f}% 낮다)")
print(f"  건너뛴 OCI {OCI_PER_YEAR:.0f} 억 x 5년의 현재가치 {annuity:,.1f} 억과 같다")
print("  → OCI 는 장부가를 늘려 자본비용분을 키우지만 그만큼이 순이익에 잡히지")
print("     않는다. 잔여이익이 그 몫만큼 깎이고, 깎인 값이 그대로 차이가 된다.")
