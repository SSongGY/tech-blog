"""주식기준보상의 보상원가를 가득기간에 걸쳐 나누어 계산한다.

가나전자·다라물산은 실재하지 않는 회사다. 숫자는 보이고 싶은 대비를
만들려고 지어낸 것이고, 법인세 효과는 비교를 흐리지 않으려고 뺐다.

K-IFRS 제1102호 문단 15·19·20·21의 계산 구조를 그대로 따른다.
"""

import unicodedata

WON = 1  # 금액 단위는 원


def width(text):
    """동아시아 문자를 두 칸으로 세어 실제 표시 폭을 구한다."""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def pad(text, size, align="left"):
    gap = max(0, size - width(text))
    return text + " " * gap if align == "left" else " " * gap + text


def money(value):
    return f"{round(value):,}"


def head(title):
    print()
    print(title)


# ---------------------------------------------------------------- 부여 조건

GANA = {
    "name": "가나전자",
    "grantees": 100,        # 부여 대상 임직원 수
    "options_each": 100,    # 1인당 주식선택권 수
    "fair_value": 4_000,    # 부여일 주식선택권 1개의 공정가치 (원)
    "vesting_years": 3,     # 가득기간 — 3년 근속
    # 보고기간 말마다 다시 세우는 '가득될 것으로 예상되는 인원'
    "expected": [90, 85, 88],
}


def cumulative_cost(plan, year_index, headcount):
    """문단 20 — 가득 예상 수량 × 부여일 공정가치 × 경과기간 / 가득기간."""
    total = plan["options_each"] * plan["fair_value"] * headcount
    return total * (year_index + 1) / plan["vesting_years"]


def schedule(plan, fair_value=None, expected=None):
    """연도별 누적 보상원가와 당기비용을 구한다."""
    fv = fair_value if fair_value is not None else plan["fair_value"]
    counts = expected if expected is not None else plan["expected"]
    rows, previous = [], 0.0
    for index, headcount in enumerate(counts):
        total = plan["options_each"] * fv * headcount
        cumulative = total * (index + 1) / plan["vesting_years"]
        rows.append(
            {
                "year": 2026 + index,
                "headcount": headcount,
                "cumulative": cumulative,
                "expense": cumulative - previous,
            }
        )
        previous = cumulative
    return rows


# ------------------------------------------------- [1] 부여 조건과 총 보상원가

head("[1] 가나전자의 주식선택권 부여 조건")
grant_total = GANA["grantees"] * GANA["options_each"]
print(f"    부여일: 2026-01-01 · 대상 {GANA['grantees']}명 · 1인당 {GANA['options_each']}개")
print(f"    부여일 공정가치: 1개당 {money(GANA['fair_value'])}원")
print(f"    가득조건: {GANA['vesting_years']}년 근속 (용역제공조건 하나뿐, 성과조건 없음)")
print(f"    전원이 가득한다면 총 보상원가 {money(grant_total * GANA['fair_value'])}원")
print("    회사에서 현금은 한 푼도 나가지 않는다 — 주식을 받을 권리를 준 것이다")

# ------------------------------------------- [2] 가득기간에 걸쳐 나누어 인식한다

head("[2] 연도별 보상원가 — 누적액을 먼저 구하고 전기까지의 누적을 뺀다")
rows = schedule(GANA)
cols = ["연도", "가득 예상 인원", "누적 보상원가", "전기까지 누적", "당기 비용"]
sizes = [8, 16, 18, 18, 18]
print("    " + "".join(pad(c, s) for c, s in zip(cols, sizes)))
previous = 0.0
for row in rows:
    cells = [
        str(row["year"]),
        f"{row['headcount']}명",
        money(row["cumulative"]),
        money(previous),
        money(row["expense"]),
    ]
    print("    " + "".join(pad(c, s) for c, s in zip(cells, sizes)))
    previous = row["cumulative"]
print(f"    3년 합계 {money(sum(r['expense'] for r in rows))}원 "
      f"= 실제 가득 {rows[-1]['headcount']}명분의 부여일 공정가치")
print("    2027년 비용이 2026년보다 작은 것은 가득 예상 인원이 90명에서 85명으로 내려갔기 때문이다")

# ------------------------------- [3] 비용이 생겼는데 자본총계는 줄지 않는다

head("[3] 같은 12,000,000원을 비용으로 잡아도 — 주식보상과 현금상여가 갈린다")
pre_tax = 500_000_000      # 보상비용을 반영하기 전 이익
cost = rows[0]["expense"]
cases = [
    ("주식선택권 부여", cost, 0, cost),
    ("같은 금액 현금상여", cost, cost, 0),
]
cols = ["보상 방식", "당기 비용", "현금 유출", "자본 증가(주식선택권)", "당기순이익", "자본총계 증감"]
sizes = [22, 16, 14, 24, 18, 18]
print("    " + "".join(pad(c, s) for c, s in zip(cols, sizes)))
for label, expense, outflow, to_equity in cases:
    profit = pre_tax - expense
    equity_change = profit + to_equity
    cells = [
        label,
        money(expense),
        money(outflow),
        money(to_equity),
        money(profit),
        money(equity_change),
    ]
    print("    " + "".join(pad(c, s) for c, s in zip(cells, sizes)))
print(f"    보상비용 반영 전 이익 {money(pre_tax)}원, 법인세 효과는 뺐다")
print("    비용이 이익잉여금을 깎는 만큼 주식선택권이 자본을 채운다 — 자본총계는 그대로다")

# ----------------------------------------- [4] 현금흐름표에서는 도로 더해진다

head("[4] 현금흐름표 영업활동 — 간접법에서 비용이 다시 가산된다")
cols = ["구분", "주식선택권 부여", "현금상여 지급"]
sizes = [34, 20, 20]
print("    " + "".join(pad(c, s) for c, s in zip(cols, sizes)))
lines = [
    ("당기순이익", pre_tax - cost, pre_tax - cost),
    ("(+) 주식보상비용 (현금 유출 없음)", cost, 0),
    ("영업활동 현금흐름", pre_tax, pre_tax - cost),
]
for label, a, b in lines:
    print("    " + pad(label, sizes[0]) + pad(money(a), sizes[1]) + pad(money(b), sizes[2]))
print(f"    두 회사의 당기순이익은 {money(pre_tax - cost)}원으로 같은데 영업활동 현금흐름은 "
      f"{money(cost)}원 차이가 난다")

# ------------------------- [5] 조건의 종류가 환입 여부를 가른다 (문단 19·21)

head("[5] 다라물산 — 같은 설계에 조건만 바꾼 두 갈래 (3년 뒤 목표 미달)")
DARA = dict(GANA, name="다라물산")
nonmarket = schedule(DARA, fair_value=4_000, expected=[90, 85, 0])
market = schedule(DARA, fair_value=2_800, expected=[90, 85, 88])
print("    설계 A — 3년 근속 + 영업이익 목표 (비시장조건)")
print(f"              부여일 공정가치 {money(4_000)}원 — 비시장조건은 공정가치에 반영하지 않는다")
print("    설계 B — 3년 근속 + 주가 목표 (시장조건)")
print(f"              부여일 공정가치 {money(2_800)}원 — 시장조건은 공정가치에 이미 깎여 들어가 있다")
print("    3년 뒤: 근속자 88명, 영업이익 목표와 주가 목표 모두 미달")
print()
cols = ["연도", "A 비시장조건 누적", "A 당기", "B 시장조건 누적", "B 당기"]
sizes = [8, 22, 18, 22, 18]
print("    " + "".join(pad(c, s) for c, s in zip(cols, sizes)))
for a, b in zip(nonmarket, market):
    cells = [
        str(a["year"]),
        money(a["cumulative"]),
        money(a["expense"]),
        money(b["cumulative"]),
        money(b["expense"]),
    ]
    print("    " + "".join(pad(c, s) for c, s in zip(cells, sizes)))
print(f"    A 누적 {money(nonmarket[-1]['cumulative'])}원 — 가득되지 않았으므로 "
      f"그간 인식한 {money(nonmarket[1]['cumulative'])}원을 전액 환입한다")
print(f"    B 누적 {money(market[-1]['cumulative'])}원 — 주가 목표를 못 채웠어도 환입하지 않는다")
print("    같은 '목표 미달'인데 손익계산서에 남는 금액이 갈린다")

# --------------------------------------- [6] 가득 이후에는 자본을 손대지 않는다

head("[6] 가득일 이후 — 행사하든 소멸하든 비용은 돌아오지 않는다")
vested = rows[-1]["cumulative"]
cols = ["가득 후 일어난 일", "주식선택권 계정", "손익계산서", "자본총계"]
sizes = [28, 32, 14, 18]
print("    " + "".join(pad(c, s) for c, s in zip(cols, sizes)))
after = [
    ("행사 — 주식 발행", "자본금·주식발행초과금으로 대체", "없음", "행사가만큼 증가"),
    ("미행사 — 권리 소멸", "다른 자본 항목으로 대체", "없음", "변화 없음"),
]
for cells in after:
    print("    " + "".join(pad(c, s) for c, s in zip(cells, sizes)))
print(f"    이미 인식한 {money(vested)}원은 어느 쪽이든 손익으로 되돌아오지 않는다")
