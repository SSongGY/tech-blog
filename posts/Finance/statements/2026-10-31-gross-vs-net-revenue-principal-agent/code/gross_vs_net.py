# -*- coding: utf-8 -*-
"""총액 인식과 순액 인식 — 같은 거래에서 매출액이 몇 배로 갈리는 자리를 계산한다.

가상 회사 가나플랫폼·다라커머스·마바여행의 숫자다. 실재하는 회사가 아니고,
거래 내용이 같아도 본인인지 대리인인지에 따라 매출액만 달라지고 영업이익은
그대로라는 것을 보이려고 만든 값이다. 단위는 백만원이다.

K-IFRS 제1115호 고객과의 계약에서 생기는 수익의 문단 47(제삼자를 대신해서
회수한 금액 제외), 문단 B34·B34A(본인·대리인 판단), B35(통제), B35A(통제하는
재화·용역의 예), B35B(본인은 총액), B36(대리인은 수수료), B37(통제 지표),
B37A(지표의 적용)를 따른다.
"""

import unicodedata

MONEY = "{:>18,}"
RATIO = "{:>17.1f}%"


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


# ── 전제 ────────────────────────────────────────────────────────────────
# 두 회사가 한 해 동안 중개하거나 직접 판 상품의 고객 결제 총액이 같다.
CUSTOMER_PAYMENT = 11_000      # 고객이 실제로 결제한 금액 (부가가치세 포함)
VALUE_ADDED_TAX = 1_000        # 그중 국가를 대신해 받아 납부하는 부가가치세
GROSS_MERCHANDISE = CUSTOMER_PAYMENT - VALUE_ADDED_TAX   # 거래가격 (문단 47)

SUPPLIER_SHARE = 9_200         # 판매자·공급자에게 돌아가는 몫
MARGIN = GROSS_MERCHANDISE - SUPPLIER_SHARE              # 회사에 남는 몫
OPERATING_EXPENSE = 500        # 두 회사의 판매비와관리비가 같다고 둔다

# 직매입 비중을 바꿔 볼 구간 — 거래액은 고정이다
DIRECT_SHARE = [0.10, 0.20, 0.30, 0.40]

# B37 지표를 적용해 볼 세 가지 거래 형태
# (사업 형태, 주된 책임, 재고위험, 가격 결정 재량, 판단 근거 문단)
CASES = [
    ("가나플랫폼 — 오픈마켓 중개", "판매자", "판매자", "판매자", "B35·B37", "대리인"),
    ("다라커머스 — 직매입 판매", "회사", "회사", "회사", "B35·B37", "본인"),
    ("마바여행 — 항공·숙박 묶음 상품", "회사", "회사", "회사", "B35A(3)", "본인"),
]


def income_statement(revenue, cost_of_sales):
    """매출액부터 영업이익까지 한 줄로 만든다."""
    gross_profit = revenue - cost_of_sales
    return {
        "매출액": revenue,
        "매출원가": cost_of_sales,
        "매출총이익": gross_profit,
        "판매비와관리비": OPERATING_EXPENSE,
        "영업이익": gross_profit - OPERATING_EXPENSE,
    }


def print_premise():
    heading("[1] 전제 — 두 회사의 거래 내용이 같다 (단위: 백만원)")
    rows = [
        ("고객이 결제한 금액", CUSTOMER_PAYMENT),
        ("  그중 부가가치세 — 국가를 대신해 받은 금액 (문단 47)", -VALUE_ADDED_TAX),
        ("거래가격", GROSS_MERCHANDISE),
        ("  판매자·공급자에게 돌아가는 몫", SUPPLIER_SHARE),
        ("  회사에 남는 몫", MARGIN),
        ("판매비와관리비 (두 회사 동일)", OPERATING_EXPENSE),
    ]
    for label, amount in rows:
        print("  " + left(label, 46) + MONEY.format(amount))


def print_two_statements():
    agent = income_statement(MARGIN, 0)
    principal = income_statement(GROSS_MERCHANDISE, SUPPLIER_SHARE)

    heading("[2] 같은 거래를 두 방식으로 — 매출액만 갈리고 영업이익은 같다")
    print("  " + left("", 20) + right("가나플랫폼(대리인)", 18)
          + right("다라커머스(본인)", 18) + right("차이", 14))
    print("  " + left("", 20) + right("순액 — 문단 B36", 18)
          + right("총액 — 문단 B35B", 18) + right("", 14))
    for key in agent:
        gap = principal[key] - agent[key]
        print("  " + left(key, 20) + MONEY.format(agent[key])
              + MONEY.format(principal[key]) + "{:>+14,}".format(gap))

    heading("[3] 매출액을 분모로 쓰는 지표가 갈리는 폭")
    metrics = [
        ("매출총이익률", agent["매출총이익"] / agent["매출액"],
         principal["매출총이익"] / principal["매출액"]),
        ("매출액영업이익률", agent["영업이익"] / agent["매출액"],
         principal["영업이익"] / principal["매출액"]),
    ]
    for name, a, p in metrics:
        print("  " + left(name, 24) + RATIO.format(a * 100) + RATIO.format(p * 100)
              + right("{:.1f}배".format(a / p), 14))
    print("  " + left("거래가격 대비 영업이익률", 24)
          + RATIO.format(agent["영업이익"] / GROSS_MERCHANDISE * 100)
          + RATIO.format(principal["영업이익"] / GROSS_MERCHANDISE * 100)
          + right("같다", 14))


def print_mix_shift():
    """거래액은 그대로인데 직매입 비중만 올렸을 때 매출액이 어떻게 움직이는가."""
    heading("[4] 거래액을 고정하고 직매입 비중만 올릴 때 — 매출은 늘고 이익은 그대로")
    print("  " + left("직매입 비중", 14) + right("직매입 매출", 14)
          + right("중개 수수료", 14) + right("매출액", 14)
          + right("매출총이익", 14) + right("영업이익", 12))
    commission_rate = MARGIN / GROSS_MERCHANDISE
    base_revenue = None
    for share in DIRECT_SHARE:
        direct = GROSS_MERCHANDISE * share
        brokered = GROSS_MERCHANDISE * (1 - share)
        commission = brokered * commission_rate
        revenue = direct + commission
        gross_profit = direct * commission_rate + commission
        if base_revenue is None:
            base_revenue = revenue
        print("  " + left("{:.0%}".format(share), 14)
              + "{:>14,.0f}".format(direct) + "{:>14,.0f}".format(commission)
              + "{:>14,.0f}".format(revenue) + "{:>14,.0f}".format(gross_profit)
              + "{:>12,.0f}".format(gross_profit - OPERATING_EXPENSE))
    final_revenue = revenue
    print()
    print("  거래가격 {:,} 은 네 경우 모두 같다. 매출액은 {:,.0f} 에서 {:,.0f} 까지 "
          "{:.0f}% 늘었고".format(GROSS_MERCHANDISE, base_revenue, final_revenue,
                                (final_revenue / base_revenue - 1) * 100))
    print("  영업이익은 {:,.0f} 으로 변하지 않았다.".format(
        gross_profit - OPERATING_EXPENSE))


def print_indicator_table():
    heading("[5] 문단 B37 의 세 가지 지표를 적용한 판단")
    print("  " + left("거래 형태", 32) + left("주된 책임", 12)
          + left("재고위험", 12) + left("가격 재량", 12)
          + left("근거", 12) + left("판단", 8))
    for name, duty, risk, pricing, basis, verdict in CASES:
        print("  " + left(name, 32) + left(duty, 12) + left(risk, 12)
              + left(pricing, 12) + left(basis, 12) + left(verdict, 8))
    print()
    print("  문단 B37A — 지표는 재화나 용역의 특성과 계약 조건에 따라 더 적합하거나")
    print("  덜 적합할 수 있다. 세 칸을 세어 다수결로 정하는 표가 아니다.")


def main():
    print("총액 인식과 순액 인식 — 가상 회사 가나플랫폼·다라커머스·마바여행")
    print("K-IFRS 제1115호 문단 47·B34~B37A, 단위 백만원")
    print_premise()
    print_two_statements()
    print_mix_shift()
    print_indicator_table()


if __name__ == "__main__":
    main()
