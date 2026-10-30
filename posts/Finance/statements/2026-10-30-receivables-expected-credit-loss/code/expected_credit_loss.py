# -*- coding: utf-8 -*-
"""매출채권 손실충당금 — 충당금 설정률표로 기대신용손실을 계산한다.

가상 회사 가나전자·다라물산의 숫자다. 실재하는 회사가 아니고, 연령 구간별
분포 차이가 충당금을 얼마나 갈라놓는지 보이려고 만든 값이다.

K-IFRS 제1109호 문단 5.5.15(간편법), 문단 5.5.17(측정 요구),
문단 B5.5.35(충당금 설정률표)를 따른다.
"""

import unicodedata

WON = "{:>15,}"


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


def rate_table():
    """과거 손실 실적에서 과거 손실률을 구하고 전망 정보로 조정한다.

    문단 B5.5.35 는 과거 손실 경험을 출발점으로 삼되 현재 상황과 미래 전망을
    반영해 조정하도록 한다. 여기서는 경기 둔화 전망을 단일 배수 1.25 로 얹는다.
    """
    history = [
        # (연령 구간, 3년간 그 구간을 거친 채권, 끝내 회수하지 못한 금액)
        ("연체 없음", 5_000_000_000, 32_000_000),
        ("30일 이하", 1_250_000_000, 16_000_000),
        ("31~90일", 625_000_000, 30_000_000),
        ("91~180일", 250_000_000, 40_000_000),
        ("180일 초과", 125_000_000, 60_000_000),
    ]
    overlay = 1.25

    rows = []
    for bucket, base, loss in history:
        past = loss / base
        rows.append((bucket, base, loss, past, past * overlay))
    return rows, overlay


def ecl(balances, rates):
    """연령 구간별 잔액에 충당률을 곱해 전체기간 기대신용손실을 구한다."""
    rows = []
    for (bucket, balance), rate in zip(balances, rates):
        rows.append((bucket, balance, rate, round(balance * rate)))
    return rows


def main():
    print("[1] 전제 — 가상 회사이고 금액 단위는 원이다")
    print("    가나전자·다라물산 모두 2026-12-31 현재 매출채권 총액 1,920,000,000원")
    print("    둘 다 유의적인 금융요소를 포함하지 않는 매출채권이므로 간편법이 의무다")
    print("    (K-IFRS 제1109호 문단 5.5.15(1)(가))")

    rows, overlay = rate_table()

    heading("[2] 과거 손실 실적에서 충당률을 뽑는다 — 전망 조정 배수 {:.2f}".format(overlay))
    print("    " + left("연령 구간", 14) + right("3년간 구간 통과액", 20)
          + right("미회수 금액", 16) + right("과거 손실률", 14) + right("당기 충당률", 14))
    for bucket, base, loss, past, adj in rows:
        print("    " + left(bucket, 14) + right("{:,}".format(base), 20)
              + right("{:,}".format(loss), 16)
              + right("{:.2f}%".format(past * 100), 14)
              + right("{:.2f}%".format(adj * 100), 14))

    rates = [adj for _, _, _, _, adj in rows]

    gana = [
        ("연체 없음", 1_200_000_000),
        ("30일 이하", 400_000_000),
        ("31~90일", 180_000_000),
        ("91~180일", 90_000_000),
        ("180일 초과", 50_000_000),
    ]
    dara = [
        ("연체 없음", 900_000_000),
        ("30일 이하", 420_000_000),
        ("31~90일", 300_000_000),
        ("91~180일", 180_000_000),
        ("180일 초과", 120_000_000),
    ]

    gana_rows = ecl(gana, rates)
    dara_rows = ecl(dara, rates)
    gana_ecl = sum(r[3] for r in gana_rows)
    dara_ecl = sum(r[3] for r in dara_rows)

    def print_matrix(title, source, computed, total_ecl):
        heading(title)
        print("    " + left("연령 구간", 14) + right("매출채권 잔액", 20)
              + right("충당률", 12) + right("기대신용손실", 18))
        for bucket, balance, rate, loss in computed:
            print("    " + left(bucket, 14) + right("{:,}".format(balance), 20)
                  + right("{:.2f}%".format(rate * 100), 12)
                  + right("{:,}".format(loss), 18))
        print("    " + left("합계", 14) + right("{:,}".format(sum(b for _, b in source)), 20)
              + right("", 12) + right("{:,}".format(total_ecl), 18))

    print_matrix("[3] 가나전자 — 충당금 설정률표를 적용한다", gana, gana_rows, gana_ecl)
    print_matrix("[4] 다라물산 — 총액은 같고 분포만 다르다", dara, dara_rows, dara_ecl)
    print()
    print("    매출채권 총액은 양쪽 다 {:,}원으로 같은데".format(sum(b for _, b in gana)))
    print("    손실충당금은 {:,}원 더 크다 ({:.2f}배)".format(
        dara_ecl - gana_ecl, dara_ecl / gana_ecl))

    # 손실충당금 계정의 1년치 흐름. 제각은 총액과 충당금을 같은 금액으로 깎으므로
    # 순장부금액을 건드리지 않고, 손익에도 나타나지 않는다.
    opening_allowance = 50_000_000
    write_off = 12_000_000
    closing_allowance = gana_ecl
    impairment_loss = closing_allowance - (opening_allowance - write_off)

    heading("[5] 가나전자 손실충당금 계정 — 당기 손상차손이 거꾸로 구해진다")
    for label, amount in [("기초 손실충당금", opening_allowance),
                          ("(-) 당기 제각", write_off),
                          ("(+) 당기 손상차손", impairment_loss),
                          ("기말 손실충당금", closing_allowance)]:
        print("    " + left(label, 24) + WON.format(amount))
    print()
    print("    손익계산서에 {:,}원이 손상차손으로 들어간다".format(impairment_loss))
    print("    제각 {:,}원은 손익을 거치지 않는다 — 이미 충당금으로 잡아 둔 금액이다".format(write_off))

    opening_gross = 1_500_000_000
    closing_gross = 1_920_000_000
    opening_net = opening_gross - opening_allowance
    closing_net = closing_gross - closing_allowance
    # 제각은 현금이 오가지 않으므로 영업자산 변동에서 빼고 본다.
    gross_change_excl_writeoff = closing_gross + write_off - opening_gross
    net_change = closing_net - opening_net

    heading("[6] 현금흐름표 영업활동(간접법) — 같은 답에 이르는 두 방식")
    print("    매출채권 총액   기초 {:,} → 기말 {:,}".format(opening_gross, closing_gross))
    print("    순장부금액      기초 {:,} → 기말 {:,}".format(opening_net, closing_net))
    print()
    def line(label, amount):
        print("      " + left(label, 34) + WON.format(amount))

    print("    방식 A — 총액으로 본다")
    line("(+) 손상차손 가산", impairment_loss)
    line("(-) 매출채권 총액 증가(제각 제외)", gross_change_excl_writeoff)
    line("순 영향", impairment_loss - gross_change_excl_writeoff)
    print()
    print("    방식 B — 순장부금액으로 본다")
    line("(+) 손상차손 가산", 0)
    line("(-) 매출채권 순장부금액 증가", net_change)
    line("순 영향", -net_change)
    print()
    print("    틀린 방식 — 순액 증가를 쓰면서 손상차손까지 가산한다")
    line("순 영향", impairment_loss - net_change)
    print("      영업활동 현금흐름이 {:,}원 과대계상된다".format(impairment_loss))


if __name__ == "__main__":
    main()
