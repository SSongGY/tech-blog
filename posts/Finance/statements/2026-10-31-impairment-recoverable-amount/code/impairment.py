# -*- coding: utf-8 -*-
"""유형자산 손상차손 — 회수가능액이 둘 중 큰 값이라는 규칙을 계산으로 따라간다.

가상 회사 가나제철의 압연 설비 하나를 두고 계산한다. 실재하는 회사가 아니고,
순공정가치와 사용가치가 가깝게 붙어 있을 때 어느 쪽을 쓰느냐로 손상차손이
갈리는 것을 보이려고 만든 값이다. 단위는 백만원이다.

K-IFRS 제1036호 자산손상의 문단 6·18(회수가능액의 정의), 19(한쪽이 장부금액을
넘으면 다른 쪽을 추정하지 않는다), 30·31(사용가치), 33(추정 기간), 50(법인세와
재무활동 제외), 55(세전 할인율), 59·60·63(손상차손과 이후 감가상각),
114·117·119(환입과 그 한도), 124(영업권 환입 금지)를 따른다.
"""

import unicodedata

MONEY = "{:>14,.1f}"


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
COST = 1_500.0                 # 취득원가
ACCUMULATED = 500.0            # 감가상각누계액
REMAINING_LIFE = 5             # 잔존내용연수(년), 정액법·잔존가치 0

FAIR_VALUE = 820.0             # 설비의 공정가치
DISPOSAL_COST = 30.0           # 처분부대원가

# 계속 사용해서 얻을 세전 현금흐름 — 문단 50 에 따라 법인세와 재무활동은 뺀다
CASH_FLOWS = [220.0, 210.0, 200.0, 190.0, 180.0]
SALVAGE = 50.0                 # 5년 말 처분으로 얻을 순현금흐름
DISCOUNT_RATE = 0.10           # 문단 55 의 세전 할인율
RATE_CASES = [0.08, 0.10, 0.12]

LOWER_CARRYING = 700.0         # 문단 19 를 보이기 위한 다른 장부금액
RECOVERED_AMOUNT = 650.0       # 2년 뒤 회복된 회수가능액
YEARS_AFTER = 2                # 손상 인식 후 경과 연수


def carrying_amount():
    return COST - ACCUMULATED


def net_fair_value():
    """공정가치에서 처분부대원가를 뺀 금액 — 문단 6."""
    return FAIR_VALUE - DISPOSAL_COST


def value_in_use_schedule(rate):
    """계속 사용과 최종 처분에서 생길 현금흐름을 할인한다 — 문단 31."""
    rows = []
    for year, flow in enumerate(CASH_FLOWS, start=1):
        total = flow + (SALVAGE if year == len(CASH_FLOWS) else 0.0)
        factor = 1 / (1 + rate) ** year
        rows.append((year, flow, SALVAGE if year == len(CASH_FLOWS) else 0.0,
                     factor, total * factor))
    return rows


def value_in_use(rate):
    return sum(row[4] for row in value_in_use_schedule(rate))


def print_premise():
    heading("[1] 전제 — 가나제철의 압연 설비 한 대 (단위: 백만원)")
    for label, amount in [("취득원가", COST), ("감가상각누계액", -ACCUMULATED),
                          ("장부금액", carrying_amount())]:
        print("  " + left(label, 30) + MONEY.format(amount))
    print("  " + left("잔존내용연수", 30) + right("{}년 (정액법)".format(REMAINING_LIFE), 14))
    print("  " + left("손상 징후", 30)
          + right("주요 제품 시장 축소 — 문단 12(2)", 34))


def print_recoverable_amount():
    heading("[2] 회수가능액 — 둘 중 큰 금액 (문단 6·18)")
    nfv = net_fair_value()
    viu = value_in_use(DISCOUNT_RATE)
    print("  " + left("공정가치", 30) + MONEY.format(FAIR_VALUE))
    print("  " + left("처분부대원가", 30) + MONEY.format(-DISPOSAL_COST))
    print("  " + left("순공정가치", 30) + MONEY.format(nfv))
    print("  " + left("사용가치 (세전 할인율 {:.0%})".format(DISCOUNT_RATE), 30)
          + MONEY.format(viu))
    bigger = "사용가치" if viu > nfv else "순공정가치"
    recoverable = max(nfv, viu)
    print("  " + left("회수가능액 — 큰 쪽은 {}".format(bigger), 30)
          + MONEY.format(recoverable))
    print("  " + left("장부금액", 30) + MONEY.format(carrying_amount()))
    print("  " + left("손상차손 (문단 59·60)", 30)
          + MONEY.format(carrying_amount() - recoverable))
    print()
    print("  순공정가치만 보고 끊었다면 손상차손은 {:,.1f} — {:,.1f} 만큼 과대계상된다."
          .format(carrying_amount() - nfv, viu - nfv))
    return recoverable


def print_value_in_use_detail():
    heading("[3] 사용가치의 내역 — 세전 현금흐름을 세전 할인율로 할인한다 (문단 31·50·55)")
    print("  " + left("연도", 8) + right("사용 현금흐름", 16)
          + right("처분 현금흐름", 16) + right("현가계수", 12) + right("현재가치", 14))
    for year, flow, salvage, factor, present in value_in_use_schedule(DISCOUNT_RATE):
        print("  " + left("{}년차".format(year), 8) + "{:>16,.1f}".format(flow)
              + "{:>16,.1f}".format(salvage) + "{:>12.4f}".format(factor)
              + "{:>14,.1f}".format(present))
    print("  " + left("합계", 8) + right("", 16) + right("", 16) + right("", 12)
          + "{:>14,.1f}".format(value_in_use(DISCOUNT_RATE)))
    print()
    print("  추정 기간을 5년으로 둔 것은 문단 33(2) 의 상한을 따른 것이다.")
    print("  법인세와 차입금 이자는 현금흐름에 넣지 않는다 (문단 50).")


def print_rate_sensitivity():
    heading("[4] 할인율이 바뀌면 손상차손이 갈린다 (문단 55)")
    nfv = net_fair_value()
    print("  " + left("세전 할인율", 14) + right("사용가치", 14)
          + right("순공정가치", 14) + right("회수가능액", 14)
          + right("큰 쪽", 12) + right("손상차손", 14))
    for rate in RATE_CASES:
        viu = value_in_use(rate)
        recoverable = max(nfv, viu)
        bigger = "사용가치" if viu > nfv else "순공정가치"
        print("  " + left("{:.0%}".format(rate), 14) + "{:>14,.1f}".format(viu)
              + "{:>14,.1f}".format(nfv) + "{:>14,.1f}".format(recoverable)
              + right(bigger, 12)
              + "{:>14,.1f}".format(carrying_amount() - recoverable))
    print()
    print("  할인율을 2%p 올리면 사용가치가 순공정가치 아래로 내려가, 회수가능액을")
    print("  정하는 쪽이 사용가치에서 순공정가치로 바뀐다.")


def print_no_estimate_needed():
    heading("[5] 한쪽이 장부금액을 넘으면 다른 쪽을 추정하지 않는다 (문단 19)")
    nfv = net_fair_value()
    print("  " + left("장부금액이 {:,.1f} 인 설비라면".format(LOWER_CARRYING), 40))
    print("  " + left("  순공정가치", 30) + MONEY.format(nfv))
    print("  " + left("  장부금액", 30) + MONEY.format(LOWER_CARRYING))
    print("  " + left("  순공정가치가 장부금액을 넘는다", 30)
          + right("→ 손상되지 않았다", 20))
    print("  " + left("  사용가치", 30) + right("추정하지 않는다", 20))


def print_depreciation_after(recoverable):
    heading("[6] 손상 인식 후 감가상각은 수정된 장부금액 기준이다 (문단 63)")
    before = carrying_amount() / REMAINING_LIFE
    after = recoverable / REMAINING_LIFE
    print("  " + left("손상 전 연간 감가상각비", 30) + MONEY.format(before))
    print("  " + left("손상 후 연간 감가상각비", 30) + MONEY.format(after))
    print("  " + left("차이", 30) + MONEY.format(after - before))
    print()
    print("  " + left("연도", 10) + right("손상 없었을 때 비용", 22)
          + right("손상 인식 시 비용", 22) + right("차이", 14))
    print("  " + left("손상 연도", 10) + "{:>22,.1f}".format(0.0)
          + "{:>22,.1f}".format(carrying_amount() - recoverable)
          + "{:>14,.1f}".format(carrying_amount() - recoverable))
    for year in range(1, REMAINING_LIFE + 1):
        print("  " + left("{}년차".format(year), 10) + "{:>22,.1f}".format(before)
              + "{:>22,.1f}".format(after) + "{:>14,.1f}".format(after - before))
    print()
    print("  손상 연도에 {:,.1f} 을 한 번에 털고, 이후 5년 동안 해마다 {:,.1f} 씩"
          .format(carrying_amount() - recoverable, before - after))
    print("  비용이 줄어든다. 5년 합계로 보면 두 경로의 비용 총액은 같다.")


def print_reversal(recoverable):
    heading("[7] 환입과 그 한도 (문단 114·117·119·124)")
    after_rate = recoverable / REMAINING_LIFE
    now = recoverable - after_rate * YEARS_AFTER
    never = carrying_amount() - (carrying_amount() / REMAINING_LIFE) * YEARS_AFTER
    reversal = min(RECOVERED_AMOUNT, never) - now
    print("  " + left("{}년 뒤 손상 반영 장부금액".format(YEARS_AFTER), 36)
          + MONEY.format(now))
    print("  " + left("회복된 회수가능액", 36) + MONEY.format(RECOVERED_AMOUNT))
    print("  " + left("손상차손을 인식하지 않았을 경우의 장부금액", 36)
          + MONEY.format(never))
    print("  " + left("환입 한도 — 둘 중 작은 쪽 (문단 117)", 36)
          + MONEY.format(min(RECOVERED_AMOUNT, never)))
    print("  " + left("손상차손환입 (문단 114·119)", 36) + MONEY.format(reversal))
    print("  " + left("한도가 없었다면 올릴 수 있었던 금액", 36)
          + MONEY.format(RECOVERED_AMOUNT - now))
    print()
    print("  같은 상황이 영업권이면 환입액은 0 이다 — 영업권에 인식한 손상차손은")
    print("  후속 기간에 환입하지 않는다 (문단 124).")


def main():
    print("유형자산 손상차손 — 가상 회사 가나제철의 압연 설비")
    print("K-IFRS 제1036호 자산손상, 단위 백만원")
    print_premise()
    recoverable = print_recoverable_amount()
    print_value_in_use_detail()
    print_rate_sensitivity()
    print_no_estimate_needed()
    print_depreciation_after(recoverable)
    print_reversal(recoverable)


if __name__ == "__main__":
    main()
