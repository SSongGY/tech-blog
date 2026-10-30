# -*- coding: utf-8 -*-
"""차입원가 자본화 — 이자가 비용이 아니라 자산이 되는 구간을 계산한다.

가상 회사 가나전자·다라물산의 숫자다. 실재하는 회사가 아니고, 같은 지출과
같은 차입 구조에서 자본화 여부가 손익과 자산을 어떻게 갈라놓는지 보이려고
만든 값이다.

K-IFRS 제1023호 차입원가의 문단 8(자본화 의무), 문단 12(특정차입금),
문단 14(일반차입금과 자본화이자율), 문단 17·20·22(개시·중단·종료)를 따른다.
"""

import unicodedata

WON = "{:>17,}"


def width(text):
    """한글은 터미널에서 두 칸을 차지하므로 자릿수 대신 표시 폭으로 센다."""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def left(text, size):
    return text + " " * max(0, size - width(text))


def right(text, size):
    return " " * max(0, size - width(text)) + text


def heading(text):
    print()
    print(text)


def line(label, amount, indent=6, pad=40):
    print(" " * indent + left(label, pad) + WON.format(amount))


# ── 전제 ────────────────────────────────────────────────────────────────
# 지출: (이름, 금액, 지출한 달) — 달은 1~12
SPENDING = [("1월 1일 착공 지출", 600_000_000, 1),
            ("7월 1일 기성 지출", 400_000_000, 7),
            ("10월 1일 기성 지출", 300_000_000, 10)]

SPECIFIC_PRINCIPAL = 500_000_000      # 특정차입금 원금
SPECIFIC_RATE = 0.05                  # 특정차입금 이자율
TEMP_INVESTED = 200_000_000           # 일시 운용액
TEMP_MONTHS = 6                       # 일시 운용 기간
TEMP_INCOME = 2_000_000               # 일시 운용 투자수익

# 일반차입금: (이름, 원금, 이자율, 차입 개월)
GENERAL = [("차입금 A", 800_000_000, 0.06, 12),
           ("차입금 B", 400_000_000, 0.08, 6)]

USEFUL_LIFE = 10                      # 공장 내용연수


def months_in_window(start_month, window):
    """지출한 달부터 연말까지 중 자본화 기간에 들어가는 달 수를 센다."""
    return sum(1 for m in window if m >= start_month)


def capitalisation_rate():
    """문단 14 — 일반차입금 전체의 가중평균차입이자율."""
    cost = sum(p * r * m / 12 for _, p, r, m in GENERAL)
    average = sum(p * m / 12 for _, p, _, m in GENERAL)
    return cost, average, cost / average


def compute(window, label):
    """자본화 기간 window(월 번호 집합)에 대해 자본화할 차입원가를 구한다."""
    months = len(window)

    # 연평균지출액 — 자본화 기간에 속한 달만 가중한다.
    weighted = [(name, amount, months_in_window(start, window))
                for name, amount, start in SPENDING]
    average_spending = sum(a * m / 12 for _, a, m in weighted)

    # 특정차입금이 충당한 평균 지출액. 일시 운용한 몫은 적격자산에 쓰이지
    # 않았으므로 빼고 본다.
    specific_average = (SPECIFIC_PRINCIPAL * months / 12
                        - TEMP_INVESTED * TEMP_MONTHS / 12)
    general_base = average_spending - specific_average

    # 문단 12 — 특정차입금은 실제 차입원가에서 일시 운용 투자수익을 뺀다.
    specific_cost = SPECIFIC_PRINCIPAL * SPECIFIC_RATE * months / 12
    specific_cap = specific_cost - TEMP_INCOME

    general_cost, general_average, rate = capitalisation_rate()
    general_cap = general_base * rate
    # 문단 14 단서 — 자본화액은 그 기간 실제 발생한 차입원가를 넘지 못한다.
    general_cap = min(general_cap, general_cost)

    heading(label)
    print("    자본화 기간 {}개월 (해당 월: {})".format(
        months, ", ".join(str(m) + "월" for m in sorted(window))))
    print()
    print("    연평균지출액")
    for name, amount, m in weighted:
        print("      " + left(name, 26)
              + right("{:,}".format(amount), 16)
              + right("× {}/12".format(m), 12)
              + right("{:,}".format(round(amount * m / 12)), 18))
    line("연평균지출액 합계", round(average_spending), indent=6, pad=54)
    print()
    line("(-) 특정차입금이 충당한 평균액", round(specific_average), indent=6, pad=54)
    line("= 일반차입금 적용 대상", round(general_base), indent=6, pad=54)
    print()
    line("특정차입금 차입원가", round(specific_cost), indent=6, pad=54)
    line("(-) 일시 운용 투자수익 (문단 12)", TEMP_INCOME, indent=6, pad=54)
    line("= 특정차입금 자본화액", round(specific_cap), indent=6, pad=54)
    print()
    line("일반차입금 적용 대상 × 자본화이자율 {:.1f}%".format(rate * 100),
         round(general_cap), indent=6, pad=54)
    line("  (한도: 일반차입금 실제 차입원가)", round(general_cost), indent=6, pad=54)
    print()
    line("자본화할 차입원가 합계", round(specific_cap + general_cap), indent=6, pad=54)

    return round(specific_cap + general_cap)


def main():
    print("[1] 전제 — 가상 회사이고 금액 단위는 원이다")
    print("    가나전자가 2026년 한 해에 걸쳐 제2공장을 짓는다. 상당한 기간을")
    print("    필요로 하므로 적격자산이다 (K-IFRS 제1023호 문단 5).")
    print()
    print("    적격자산 지출")
    for name, amount, start in SPENDING:
        print("      " + left(name, 26) + right("{:,}".format(amount), 18))
    total_spending = sum(a for _, a, _ in SPENDING)
    print("      " + left("지출 합계", 26) + right("{:,}".format(total_spending), 18))
    print()
    print("    차입 구조")
    print("      특정차입금  {:,}원 연 {:.0f}% (공장 건설 목적으로 특정하여 차입)".format(
        SPECIFIC_PRINCIPAL, SPECIFIC_RATE * 100))
    print("                  이 중 {:,}원을 {}개월간 예치해 투자수익 {:,}원".format(
        TEMP_INVESTED, TEMP_MONTHS, TEMP_INCOME))
    for name, principal, rate, months in GENERAL:
        print("      {}    {:,}원 연 {:.0f}% ({}개월)".format(
            name, principal, rate * 100, months))

    general_cost, general_average, rate = capitalisation_rate()
    heading("[2] 자본화이자율 — 일반차입금 전체의 가중평균 (문단 14)")
    print("    " + left("차입금", 14) + right("연평균 차입액", 20) + right("차입원가", 18))
    for name, principal, r, months in GENERAL:
        print("    " + left(name, 14)
              + right("{:,}".format(round(principal * months / 12)), 20)
              + right("{:,}".format(round(principal * r * months / 12)), 18))
    print("    " + left("합계", 14)
          + right("{:,}".format(round(general_average)), 20)
          + right("{:,}".format(round(general_cost)), 18))
    print()
    print("    자본화이자율 = {:,} / {:,} = {:.1f}%".format(
        round(general_cost), round(general_average), rate * 100))

    full_year = set(range(1, 13))
    normal = compute(full_year, "[3] 중단 없이 1년 내내 공사한 경우")

    paused = full_year - {8, 9}
    interrupted = compute(
        paused, "[4] 8~9월에 토지 소유권 분쟁으로 공사가 전면 중지된 경우 (문단 20)")
    print()
    print("    중단 2개월 때문에 자본화액이 {:,}원 줄고".format(normal - interrupted))
    print("    그만큼 2026년 비용이 늘어난다")

    # ── 두 회사 비교 ────────────────────────────────────────────────────
    total_cost = SPECIFIC_PRINCIPAL * SPECIFIC_RATE + general_cost
    gana_expense = total_cost - normal
    dara_expense = total_cost

    heading("[5] 2026년 — 자본화한 회사와 전액 비용 처리한 회사")
    print("    " + left("항목", 34) + right("가나전자(자본화)", 22)
          + right("다라물산(전액 비용)", 24))
    rows = [
        ("차입원가 총액", total_cost, total_cost),
        ("  그중 자본화", normal, 0),
        ("  그중 당기 비용", gana_expense, dara_expense),
        ("일시 운용 투자수익 (손익)", 0, TEMP_INCOME),
        ("세전이익 영향", -(gana_expense), -(dara_expense - TEMP_INCOME)),
        ("공장 취득원가", total_spending + normal, total_spending),
    ]
    for label, a, b in rows:
        print("    " + left(label, 34)
              + right("{:,}".format(round(a)), 22)
              + right("{:,}".format(round(b)), 24))

    gana_cost = total_spending + normal
    dara_cost = total_spending
    gana_dep = gana_cost / USEFUL_LIFE
    dara_dep = dara_cost / USEFUL_LIFE

    heading("[6] 2027~2036년 — 자본화한 이자는 감가상각으로 돌아온다")
    print("    내용연수 {}년, 정액법, 잔존가치 0".format(USEFUL_LIFE))
    print("    " + left("항목", 34) + right("가나전자", 22) + right("다라물산", 24))
    print("    " + left("연 감가상각비", 34)
          + right("{:,}".format(round(gana_dep)), 22)
          + right("{:,}".format(round(dara_dep)), 24))
    print("    " + left("{}년 누계".format(USEFUL_LIFE), 34)
          + right("{:,}".format(round(gana_cost)), 22)
          + right("{:,}".format(round(dara_cost)), 24))
    print()
    print("    해마다 {:,}원씩 가나전자의 비용이 더 크다".format(round(gana_dep - dara_dep)))

    gana_total = -(gana_expense) - gana_cost
    dara_total = -(dara_expense - TEMP_INCOME) - dara_cost

    heading("[7] 11년을 합치면 — 자본화는 이연일 뿐 총액을 바꾸지 않는다")
    print("    " + left("항목", 34) + right("가나전자", 22) + right("다라물산", 24))
    print("    " + left("2026년 세전이익 영향", 34)
          + right("{:,}".format(round(-(gana_expense))), 22)
          + right("{:,}".format(round(-(dara_expense - TEMP_INCOME))), 24))
    print("    " + left("2027~2036년 감가상각 누계", 34)
          + right("{:,}".format(round(-gana_cost)), 22)
          + right("{:,}".format(round(-dara_cost)), 24))
    print("    " + left("11년 합계", 34)
          + right("{:,}".format(round(gana_total)), 22)
          + right("{:,}".format(round(dara_total)), 24))
    print()
    print("    차이는 {:,}원뿐이고, 그것이 일시 운용 투자수익이다.".format(
        round(dara_total - gana_total)))
    print("    자본화한 회사는 그 수익을 손익에 올리지 않고 자본화액에서 뺐다 (문단 12).")


if __name__ == "__main__":
    main()
