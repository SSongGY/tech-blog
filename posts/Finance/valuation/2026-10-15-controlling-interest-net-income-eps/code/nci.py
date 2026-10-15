"""연결 당기순이익을 지배주주지분과 비지배지분으로 갈라 EPS·PER·PBR 을 계산한다.

가상 지주회사 `자차홀딩스` 하나를 두고
  [1] 지배기업과 종속기업 둘을 합쳐 연결 당기순이익을 만들고 귀속을 나누고
  [2] 연결 전체로 계산한 PER·PBR 과 지배주주 기준 PER·PBR 을 비교하고
  [3] 비지배지분 비중을 0%에서 60%까지 옮겨 가며 그 격차를 재고
  [4] 종속기업 지분을 60% 에서 80% 로 추가 취득했을 때 연결 순이익은 그대로인데
      지배주주 순이익만 늘어나는 것을 보고
  [5] 종속기업이 적자일 때 비지배지분이 부(-)의 잔액이 되는 경우를 본다.

숫자는 전부 설명용 가정값이고 실재하는 기업과 관계가 없다. 표준 라이브러리만 쓴다.
"""

# --- 자차홀딩스 그룹의 가정 ------------------------------------------------
# 단위: 억원. 전부 설명을 위해 만든 값이다.
PARENT_NET_INCOME = 300.0       # 지배기업 자체의 당기순이익
SUB_NET_INCOME = 500.0          # 종속기업의 당기순이익
OWNERSHIP = 0.60                # 지배기업이 가진 종속기업 지분율

PARENT_EQUITY = 2_000.0         # 지배기업 자체의 자기자본
SUB_EQUITY = 3_000.0            # 종속기업의 자기자본

SHARES = 10.0                   # 지배기업 발행 보통주 (억주)
PRICE = 720.0                   # 주가 (원 단위가 아니라 설명용 지수값)
MARKET_CAP = SHARES * PRICE     # 시가총액 (억원)


def consolidate(parent_ni, sub_ni, ownership, parent_eq, sub_eq):
    """연결 손익과 연결 자본을 만들고 귀속을 나눈다.

    지배력이 있으면 지분율과 상관없이 종속기업을 전액 합산한다.
    내 몫이 아닌 부분은 비지배지분으로 따로 떼어 표시한다.
    """
    total_ni = parent_ni + sub_ni
    nci_ni = sub_ni * (1 - ownership)
    controlling_ni = total_ni - nci_ni

    total_eq = parent_eq + sub_eq
    nci_eq = sub_eq * (1 - ownership)
    controlling_eq = total_eq - nci_eq

    return {
        "total_ni": total_ni,
        "nci_ni": nci_ni,
        "controlling_ni": controlling_ni,
        "total_eq": total_eq,
        "nci_eq": nci_eq,
        "controlling_eq": controlling_eq,
    }


def won(value):
    return f"{value:>9,.1f}"


# --- [1] 연결 과정 ---------------------------------------------------------
base = consolidate(PARENT_NET_INCOME, SUB_NET_INCOME, OWNERSHIP,
                   PARENT_EQUITY, SUB_EQUITY)

print(f"[1] 자차홀딩스 — 종속기업 지분 {OWNERSHIP * 100:.0f}% (단위: 억원)")
print("  항목                        지배기업    종속기업      연결 합계")
print(f"  당기순이익              {won(PARENT_NET_INCOME)}   {won(SUB_NET_INCOME)}"
      f"   {won(base['total_ni'])}")
print(f"  자기자본                {won(PARENT_EQUITY)}   {won(SUB_EQUITY)}"
      f"   {won(base['total_eq'])}")
print("  연결 당기순이익의 귀속")
print(f"    지배기업 소유주 지분  {won(base['controlling_ni'])}"
      f"   ({base['controlling_ni'] / base['total_ni'] * 100:.1f}%)")
print(f"    비지배지분            {won(base['nci_ni'])}"
      f"   ({base['nci_ni'] / base['total_ni'] * 100:.1f}%)")
print("  연결 자기자본의 귀속")
print(f"    지배기업 소유주 지분  {won(base['controlling_eq'])}"
      f"   ({base['controlling_eq'] / base['total_eq'] * 100:.1f}%)")
print(f"    비지배지분            {won(base['nci_eq'])}"
      f"   ({base['nci_eq'] / base['total_eq'] * 100:.1f}%)")
print(f"  → 종속기업 순이익 {SUB_NET_INCOME:.0f} 억은 지분 {OWNERSHIP * 100:.0f}% 와")
print(f"     상관없이 전액 합산되고, 내 몫이 아닌 {base['nci_ni']:.0f} 억을 따로 뗀다.")
print()


# --- [2] 어느 분자를 쓰느냐로 배수가 갈린다 --------------------------------
def multiples(net_income, equity):
    eps = net_income / SHARES
    return {
        "eps": eps,
        "per": PRICE / eps,
        "bps": equity / SHARES,
        "pbr": MARKET_CAP / equity,
        "roe": net_income / equity,
    }


whole = multiples(base["total_ni"], base["total_eq"])
owner = multiples(base["controlling_ni"], base["controlling_eq"])

print(f"[2] 시가총액 {MARKET_CAP:,.0f} 억 · 발행주식 {SHARES:.0f} 억주 · 주가 {PRICE:.0f}")
print("  분자·분모로 무엇을 쓰는가            EPS      PER      BPS      PBR      ROE")
print(f"  연결 전체 (틀린 계산)          {whole['eps']:>8.2f} {whole['per']:>8.2f}"
      f" {whole['bps']:>8.2f} {whole['pbr']:>8.2f} {whole['roe'] * 100:>7.2f}%")
print(f"  지배주주지분 (기준서대로)      {owner['eps']:>8.2f} {owner['per']:>8.2f}"
      f" {owner['bps']:>8.2f} {owner['pbr']:>8.2f} {owner['roe'] * 100:>7.2f}%")
print(f"  PER 격차  {whole['per']:.2f} → {owner['per']:.2f}"
      f"  ({owner['per'] / whole['per'] - 1:+.1%})")
print(f"  PBR 격차  {whole['pbr']:.2f} → {owner['pbr']:.2f}"
      f"  ({owner['pbr'] / whole['pbr'] - 1:+.1%})")
print("  → 연결 전체로 계산하면 내 것이 아닌 이익과 자본까지 세어 배수가 낮게 보인다.")
print()

# --- [3] 비지배지분 비중을 옮기면 ------------------------------------------
print("[3] 종속기업 지분율을 옮기면 (연결 순이익 800.0 억·연결 자본 5,000.0 억 고정)")
print("   지분율  비지배 순이익  지배주주 순이익   지배주주 EPS   지배주주 PER"
      "   연결기준 PER   연결기준이 낮게 보이는 폭")
flat_per = None
for pct_own in [1.00, 0.90, 0.80, 0.70, 0.60, 0.50, 0.40]:
    row = consolidate(PARENT_NET_INCOME, SUB_NET_INCOME, pct_own,
                      PARENT_EQUITY, SUB_EQUITY)
    own_m = multiples(row["controlling_ni"], row["controlling_eq"])
    all_m = multiples(row["total_ni"], row["total_eq"])
    flat_per = all_m["per"]
    print(
        f"   {pct_own * 100:>4.0f}% {won(row['nci_ni'])}      {won(row['controlling_ni'])}"
        f"      {own_m['eps']:>9.2f}      {own_m['per']:>9.2f}"
        f"      {all_m['per']:>9.2f}      {all_m['per'] / own_m['per'] - 1:>+8.1%}"
    )
print(f"  → 연결 기준 PER 열은 지분율이 어떻게 바뀌어도 {flat_per:.2f} 에서 움직이지 않는다.")
print(f"     연결 순이익이 지분율과 무관하게 {PARENT_NET_INCOME + SUB_NET_INCOME:,.1f} 억으로"
      " 고정이기 때문이다.")
print()

# --- [4] 지분을 추가 취득하면 ----------------------------------------------
NEW_OWNERSHIP = 0.80
# 비지배지분에서 20%p 를 사 온다. 대가는 종속기업 자본의 해당 몫에 30% 를
# 얹어 준 값으로 가정한다. 지배력을 이미 가지고 있으므로 자본거래로 본다.
acquired_share = SUB_EQUITY * (NEW_OWNERSHIP - OWNERSHIP)
consideration = acquired_share * 1.30

after = consolidate(PARENT_NET_INCOME, SUB_NET_INCOME, NEW_OWNERSHIP,
                    PARENT_EQUITY, SUB_EQUITY)

print(f"[4] 종속기업 지분을 {OWNERSHIP * 100:.0f}% → {NEW_OWNERSHIP * 100:.0f}% 로"
      " 추가 취득하면 (단위: 억원)")
print("  항목                              취득 전     취득 후        변동")
print(f"  연결 당기순이익              {won(base['total_ni'])} {won(after['total_ni'])}"
      f" {won(after['total_ni'] - base['total_ni'])}")
print(f"  비지배지분 귀속 순이익       {won(base['nci_ni'])} {won(after['nci_ni'])}"
      f" {won(after['nci_ni'] - base['nci_ni'])}")
print(f"  지배주주 귀속 순이익         {won(base['controlling_ni'])}"
      f" {won(after['controlling_ni'])}"
      f" {won(after['controlling_ni'] - base['controlling_ni'])}")
print(f"  지배주주 EPS                 "
      f"{base['controlling_ni'] / SHARES:>9.2f} {after['controlling_ni'] / SHARES:>9.2f}"
      f" {(after['controlling_ni'] - base['controlling_ni']) / SHARES:>9.2f}")
print(f"  비지배지분 장부금액          {won(base['nci_eq'])} {won(after['nci_eq'])}"
      f" {won(after['nci_eq'] - base['nci_eq'])}")
print(f"  취득 대가 {consideration:,.1f} - 비지배지분 조정액 {acquired_share:,.1f}"
      f" = {consideration - acquired_share:,.1f}")
print("  → 차액은 손익이 아니라 자본에서 직접 차감되고 지배기업 소유주에게 귀속된다.")
print("     연결 당기순이익은 한 푼도 움직이지 않는데 지배주주 EPS 만 오른다.")
print()

# --- [5] 종속기업이 적자일 때 ----------------------------------------------
# 비지배지분이 가진 몫보다 큰 손실이 나도 배분을 멈추지 않는다.
LOSS_SUB_NI = -900.0
loss = consolidate(PARENT_NET_INCOME, LOSS_SUB_NI, OWNERSHIP,
                   PARENT_EQUITY, 200.0)

print(f"[5] 종속기업이 {LOSS_SUB_NI:,.0f} 억 적자이고 그 자기자본이 200.0 억뿐이라면")
print(f"  연결 당기순이익              {won(loss['total_ni'])}")
print(f"  비지배지분 귀속              {won(loss['nci_ni'])}")
print(f"  지배주주 귀속                {won(loss['controlling_ni'])}")
print(f"  비지배지분 장부금액          {won(loss['nci_eq'])}"
      f"  (기초 80.0 억에서 손실 {abs(LOSS_SUB_NI) * (1 - OWNERSHIP):,.1f} 억을 맞는다)")
print(f"  손실 배분 후 비지배지분      {won(loss['nci_eq'] + loss['nci_ni'])}"
      "  ← 부(-)의 잔액")
print("  → 잔액이 음수가 되더라도 배분을 멈추고 지배주주에게 떠넘기지 않는다.")
print("     멈추면 지배주주 순이익이 실제보다 좋게 보인다.")
