"""지분공시 세 갈래 — 어느 거래가 어느 보고서로 나오는가.

가상 회사 `가나전자`의 주주 구성과 대표이사의 한 해 거래 내역을 두고, 같은
거래가 대량보유상황보고(5%룰)·임원·주요주주 소유상황보고·거래계획 사전공시
중 어느 의무를 건드리는지 판정한다. 단기매매차익 반환액도 같은 거래로 계산한다.

판정 기준은 금융감독원 기업공시 길라잡이(지분공시 3종)와 금융위원회
「상장회사 내부자거래 사전공시제도 시행」 보도자료(2024.7.24. 시행)에서
가져왔고, 각 함수 머리에 근거를 적어 둔다. 금액은 모두 원이고, 실재하지 않는
회사의 가정값이다.
"""
import platform
import sys
import unicodedata
from datetime import date

# ── 가나전자의 자본금 구성 ────────────────────────────────────────────
SHARES_OUTSTANDING = 20_000_000   # 발행주식총수 (의결권 있는 보통주)
PRICE = 36_000                    # 기준 시점 주가 (원)

# 주주 — 이름, 본인 보유 주식 수, 특별관계자 합산분, 임원 여부
HOLDERS = [
    ("최대주주 가나홀딩스", 5_600_000, 400_000, False),
    ("대표이사 김가나",     1_900_000,       0, True),
    ("사외이사 박다라",         2_400,       0, True),
    ("기관 마바자산운용",   1_240_000,       0, False),
]

# 대표이사 김가나의 한 해 거래 — (순번, 날짜, 매수/매도, 수량, 단가)
TRADES = [
    (1, date(2026, 2, 3),  "매수",     100, 30_000),
    (2, date(2026, 2, 17), "매수",     120, 32_000),
    (3, date(2026, 3, 5),  "매수",     130, 34_000),
    (4, date(2026, 5, 21), "매도",     350, 38_000),
    (5, date(2026, 6, 10), "매수",     400, 42_000),
    (6, date(2026, 7, 15), "매도",     400, 39_000),
    (7, date(2026, 10, 5), "매도", 150_000, 36_000),
]
PLAN_TRADE_NO = 7                 # 사전공시 판정 대상으로 볼 거래

# 거래 수수료·세금 — 단기매매차익 산정에서 빼는 항목 (가정값)
COMMISSION_RATE = 0.0015   # 매매거래수수료
TRANSACTION_TAX = 0.0005   # 증권거래세 (유가증권시장 매도분)
RURAL_TAX = 0.0015         # 농어촌특별세 (유가증권시장 매도분)

# ── 판정 기준값 ──────────────────────────────────────────────────────
MASS_HOLDING_THRESHOLD = 0.05       # 5%룰 신규보고 기준
MASS_CHANGE_THRESHOLD = 0.01        # 5%룰 변동보고 기준 (보유비율 1% 이상 변동)
MAJOR_SHAREHOLDER_THRESHOLD = 0.10  # 주요주주 기준 (의결권 있는 주식 10%)
MINOR_CHANGE_SHARES = 1_000         # 소유상황보고 경미한 변동 — 주식 수
MINOR_CHANGE_AMOUNT = 10_000_000    # 소유상황보고 경미한 변동 — 금액
PRE_DISCLOSURE_RATIO = 0.01         # 사전공시 면제 — 발행주식총수 대비
PRE_DISCLOSURE_AMOUNT = 5_000_000_000   # 사전공시 면제 — 거래금액
SHORT_SWING_MONTHS = 6              # 단기매매차익 산정 기간


def width(text: str) -> int:
    """한글은 두 칸을 차지하므로 표를 맞추려면 글자 수가 아니라 폭을 센다."""
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)


def pad(text: str, size: int, align: str = "<") -> str:
    space = " " * max(0, size - width(text))
    return text + space if align == "<" else space + text


def pct(numerator: int, denominator: int) -> float:
    return numerator / denominator


def months_between(earlier: date, later: date) -> float:
    """두 날짜 사이가 몇 달인지 — 단기매매차익의 6개월 창을 재는 데만 쓴다."""
    return (later - earlier).days / 30.4375


def print_header() -> None:
    print(f"[0] 가나전자의 주주 구성 "
          f"(발행주식총수 {SHARES_OUTSTANDING:,}주, 주가 {PRICE:,}원)")
    print("  " + pad("주주", 22) + pad("본인", 12, ">") + pad("특별관계자", 14, ">")
          + pad("합산", 12, ">") + pad("본인 비율", 12, ">")
          + pad("합산 비율", 12, ">") + "  임원")
    for name, own, related, is_officer in HOLDERS:
        total = own + related
        print("  " + pad(name, 22)
              + pad(f"{own:,}", 12, ">") + pad(f"{related:,}", 14, ">")
              + pad(f"{total:,}", 12, ">")
              + pad(f"{pct(own, SHARES_OUTSTANDING):.2%}", 12, ">")
              + pad(f"{pct(total, SHARES_OUTSTANDING):.2%}", 12, ">")
              + ("  O" if is_officer else "  -"))
    print()


def print_who_reports() -> None:
    """보고의무자 판정.

    5%룰은 본인 + 특별관계자 합산이 5% 이상이면 본인에게 의무가 생긴다.
    소유상황보고는 임원이거나, 본인 계산으로 의결권 있는 주식 10% 이상을 가진
    주요주주이면 의무가 생긴다 — 특별관계자 보유분은 보지 않는다.
    (기업공시 길라잡이 · 대량 보유상황 보고 / 임원 소유상황 보고)
    """
    print("[1] 누가 어느 보고서를 내는가")
    print("  " + pad("주주", 22) + pad("5%룰", 8, ">")
          + pad("소유상황보고", 16, ">") + "  사유")
    for name, own, related, is_officer in HOLDERS:
        combined = pct(own + related, SHARES_OUTSTANDING)
        solo = pct(own, SHARES_OUTSTANDING)
        mass = combined >= MASS_HOLDING_THRESHOLD
        major = solo >= MAJOR_SHAREHOLDER_THRESHOLD
        reasons = []
        if mass:
            reasons.append(f"합산 {combined:.2%} ≥ 5%")
        if is_officer:
            reasons.append("임원")
        if major:
            reasons.append(f"본인 {solo:.2%} ≥ 10%")
        print("  " + pad(name, 22)
              + pad("O" if mass else "-", 8, ">")
              + pad("O" if (is_officer or major) else "-", 16, ">")
              + "  " + (", ".join(reasons) if reasons else "해당 없음"))
    print("  사외이사 박다라는 0.01% 만 가졌어도 임원이므로 소유상황보고 대상이다")
    print("  기관 마바자산운용은 6.20% 라 5%룰 대상이지만, 10% 에 못 미쳐 소유상황보고 대상이 아니다")
    print("  두 제도는 분모가 다르다 — 5%룰은 특별관계자를 합산하고, 소유상황보고는 본인 계산분만 본다")
    print()


def print_minor_change() -> None:
    """소유상황보고의 경미한 변동 면제 — 1,000주 미만 **그리고** 1천만원 미만.

    두 요건을 모두 채워야 면제된다. 면제된 거래는 사라지지 않고 누적되며,
    누적이 기준을 넘는 순간 직전 보고 이후의 거래를 모두 묶어 보고한다.
    (기업공시 길라잡이 · 임원 소유상황 보고)
    """
    print("[2] 대표이사 김가나의 거래 — 소유상황보고 의무가 언제 생기는가")
    print("  " + pad("순번", 6, ">") + pad("날짜", 13, ">") + pad("구분", 7, ">")
          + pad("수량", 10, ">") + pad("금액", 16, ">")
          + pad("누적수량", 11, ">") + pad("누적금액", 17, ">") + "  판정")
    cum_shares = 0
    cum_amount = 0
    for no, when, side, qty, price in TRADES:
        amount = qty * price
        cum_shares += qty
        cum_amount += amount
        over_shares = cum_shares >= MINOR_CHANGE_SHARES
        over_amount = cum_amount >= MINOR_CHANGE_AMOUNT
        if over_shares and over_amount:
            verdict = "보고 (수량·금액 모두 초과)"
        elif over_shares:
            verdict = "보고 (누적 1,000주 이상)"
        elif over_amount:
            verdict = "보고 (누적 1천만원 이상)"
        else:
            verdict = "면제 (1,000주 미만 & 1천만원 미만)"
        print("  " + pad(str(no), 6, ">") + pad(when.isoformat(), 13, ">")
              + pad(side, 7, ">") + pad(f"{qty:,}", 10, ">")
              + pad(f"{amount:,}", 16, ">") + pad(f"{cum_shares:,}", 11, ">")
              + pad(f"{cum_amount:,}", 17, ">") + "  " + verdict)
        if over_shares or over_amount:
            cum_shares = 0
            cum_amount = 0
    print("  1·2번은 두 기준을 모두 밑돌아 면제된다. 그 수량과 금액은 없어지지 않고 3번에 얹힌다")
    print("  3번에서 누적 금액이 1,126만원이 되어 1~3번을 묶어 한 번에 보고한다")
    print("  보고하고 나면 누적은 0 부터 다시 센다")
    print()


def print_mass_change() -> None:
    """5%룰 변동보고 — 보유비율이 1% 이상 변동할 때.

    분모가 발행주식총수라서 소유상황보고보다 훨씬 둔하다.
    (기업공시 길라잡이 · 대량 보유상황 보고)
    """
    start = next(own for name, own, _r, _o in HOLDERS if "김가나" in name)
    step = int(SHARES_OUTSTANDING * MASS_CHANGE_THRESHOLD)
    print(f"[3] 같은 거래가 5%룰로는 어떻게 보이는가 "
          f"(대표이사 김가나, 기초 보유 {start:,}주)")
    print("  " + pad("순번", 6, ">") + pad("구분", 7, ">") + pad("수량", 10, ">")
          + pad("보유주식", 12, ">") + pad("보유비율", 11, ">")
          + pad("직전 보고분 대비", 19, ">") + "  판정")
    position = start
    reported = start
    for no, _when, side, qty, _price in TRADES:
        position += qty if side == "매수" else -qty
        delta = abs(pct(position - reported, SHARES_OUTSTANDING))
        due = delta >= MASS_CHANGE_THRESHOLD
        print("  " + pad(str(no), 6, ">") + pad(side, 7, ">")
              + pad(f"{qty:,}", 10, ">") + pad(f"{position:,}", 12, ">")
              + pad(f"{pct(position, SHARES_OUTSTANDING):.2%}", 11, ">")
              + pad(f"{delta:.2%}p", 19, ">")
              + ("  변동보고" if due else "  보고 없음 (1% 미만 변동)"))
        if due:
            reported = position
    final_delta = abs(pct(position - start, SHARES_OUTSTANDING))
    print(f"  한 해 내내 변동보고가 한 번도 안 나온다. 7번 매도 한 건이 "
          f"{150_000 * 36_000:,}원짜리인데도 그렇다")
    print(f"  보유비율이 {final_delta:.2%}p 밖에 안 움직였기 때문이다 — "
          f"1% 를 채우려면 {step:,}주 이상을 움직여야 한다")
    print("  54억원 매도를 5%룰 공시에서 찾으면 안 나온다. 소유상황보고를 봐야 보인다")
    print()


def print_pre_disclosure() -> None:
    """거래계획 사전공시 — 과거 6개월분과 계획분을 합산해 면제 여부를 본다.

    발행주식총수의 1% 미만 **그리고** 50억원 미만이면 면제된다. 둘 다 채워야
    면제되므로 하나만 넘어도 거래 개시일 30일 전까지 보고한다.
    (금융위원회 「상장회사 내부자거래 사전공시제도 시행」, 2024.7.24. 시행)
    """
    plan = next(t for t in TRADES if t[0] == PLAN_TRADE_NO)
    _no, plan_date, _side, plan_qty, plan_price = plan
    past = [t for t in TRADES
            if t[0] != PLAN_TRADE_NO and 0 <= months_between(t[1], plan_date) <= 6]
    past_qty = sum(qty for _n, _d, _s, qty, _p in past)
    past_amount = sum(qty * price for _n, _d, _s, qty, price in past)
    plan_amount = plan_qty * plan_price
    total_qty = past_qty + plan_qty
    total_amount = past_amount + plan_amount
    ratio = pct(total_qty, SHARES_OUTSTANDING)

    print(f"[4] {PLAN_TRADE_NO}번 매도가 사전공시 대상인가 "
          f"(과거 6개월분 + 계획분 합산)")
    nos = ", ".join(f"{t[0]}번" for t in past)
    print("  " + pad("구분", 28) + pad("수량", 12, ">") + pad("금액", 18, ">"))
    print("  " + pad(f"과거 6개월 ({nos})", 28)
          + pad(f"{past_qty:,}주", 12, ">") + pad(f"{past_amount:,}원", 18, ">"))
    print("  " + pad("계획 거래", 28)
          + pad(f"{plan_qty:,}주", 12, ">") + pad(f"{plan_amount:,}원", 18, ">"))
    print("  " + pad("합산", 28)
          + pad(f"{total_qty:,}주", 12, ">") + pad(f"{total_amount:,}원", 18, ">"))
    print()
    over_ratio = ratio >= PRE_DISCLOSURE_RATIO
    over_amount = total_amount >= PRE_DISCLOSURE_AMOUNT
    print("  " + pad("면제 요건", 20) + pad("기준", 22, ">")
          + pad("합산값", 18, ">") + "  판정")
    print("  " + pad("발행주식총수 대비", 20)
          + pad(f"{PRE_DISCLOSURE_RATIO:.0%} 미만", 22, ">")
          + pad(f"{ratio:.2%}", 18, ">")
          + ("  초과" if over_ratio else "  충족"))
    print("  " + pad("거래금액", 20)
          + pad(f"{PRE_DISCLOSURE_AMOUNT:,}원 미만", 22, ">")
          + pad(f"{total_amount:,}원", 18, ">")
          + ("  초과" if over_amount else "  충족"))
    if over_ratio or over_amount:
        print("  → 면제는 두 요건을 모두 채워야 한다. 하나가 넘었으므로 "
              "거래 개시일 30일 전까지 거래계획을 보고한다")
    else:
        print("  → 두 요건을 모두 채웠으므로 사전공시 의무가 없다")
    print("  지분율은 1% 에 못 미치는데 금액이 50억원을 넘어 걸렸다. "
          "주가가 높은 회사일수록 금액 쪽이 먼저 걸린다")
    print("  이 보고만 거래 전에 나온다. 나머지 둘은 거래가 끝난 뒤에 나온다")
    print()


def print_short_swing() -> None:
    """단기매매차익 반환 — 6개월 안의 매수·매도를 선입선출로 짝지어 계산.

    차익 = (매도단가 - 매수단가) x 매매일치수량 - (매매거래수수료 + 증권거래세액
    + 농어촌특별세액). 손실이 나는 짝은 이익과 상계하지 않고 없던 거래로 본다.
    (기업공시 길라잡이 · 단기매매차익 반환)
    """
    print(f"[5] 단기매매차익 — {SHORT_SWING_MONTHS}개월 안의 매수·매도를 "
          f"선입선출로 짝지운다")
    buys = [[qty, price, no, when]
            for no, when, side, qty, price in TRADES if side == "매수"]
    sells = [[qty, price, no, when]
             for no, when, side, qty, price in TRADES if side == "매도"]
    print("  " + pad("짝", 14, ">") + pad("간격", 9, ">")
          + pad("일치수량", 11, ">") + pad("매수단가", 11, ">")
          + pad("매도단가", 11, ">") + pad("총차익", 13, ">")
          + pad("비용", 11, ">") + pad("반환액", 13, ">"))
    total_return = 0
    matched_total = 0
    unmatched_total = 0
    for sell in sells:
        for buy in buys:
            if sell[0] == 0:
                break
            if buy[0] == 0:
                continue
            gap = abs(months_between(min(buy[3], sell[3]), max(buy[3], sell[3])))
            if gap > SHORT_SWING_MONTHS:
                continue
            matched = min(buy[0], sell[0])
            gross = (sell[1] - buy[1]) * matched
            cost = round(matched * buy[1] * COMMISSION_RATE
                         + matched * sell[1]
                         * (COMMISSION_RATE + TRANSACTION_TAX + RURAL_TAX))
            net = gross - cost
            due = net if net > 0 else 0
            print("  " + pad(f"{buy[2]}번↔{sell[2]}번", 14, ">")
                  + pad(f"{gap:.1f}개월", 9, ">")
                  + pad(f"{matched:,}", 11, ">") + pad(f"{buy[1]:,}", 11, ">")
                  + pad(f"{sell[1]:,}", 11, ">") + pad(f"{gross:,}", 13, ">")
                  + pad(f"{cost:,}", 11, ">") + pad(f"{due:,}", 13, ">")
                  + ("  ← 손실 짝, 상계하지 않는다" if net <= 0 else ""))
            total_return += due
            matched_total += matched
            buy[0] -= matched
            sell[0] -= matched
        if sell[0] > 0:
            print("  " + pad(f"{sell[2]}번 (짝 없음)", 14, ">")
                  + pad("-", 9, ">") + pad(f"{sell[0]:,}", 11, ">")
                  + pad("-", 11, ">") + pad(f"{sell[1]:,}", 11, ">")
                  + pad("-", 13, ">") + pad("-", 11, ">") + pad("0", 13, ">"))
            unmatched_total += sell[0]
            sell[0] = 0
    print("  " + pad("반환 합계", 14, ">") + pad("", 68)
          + pad(f"{total_return:,}원", 13, ">"))
    print(f"  짝이 지어진 물량은 {matched_total:,}주, 짝이 없는 물량은 "
          f"{unmatched_total:,}주다")
    print("  7번 매도 150,000주는 6개월 안에 사 둔 물량이 남아 있지 않아 "
          "산정에서 통째로 빠진다")
    print("  5번↔6번은 비싸게 사서 싸게 판 짝이라 손실인데, 그 손실을 "
          "4번의 이익에서 빼 주지 않는다")
    print("  미공개정보를 썼는지는 따지지 않는다. 기간과 방향만 맞으면 반환 대상이다")
    print()


def print_timeline() -> None:
    """보고 시점 — 의무발생일 기산점이 제도마다 다르다.

    5%룰 장내매매의 의무발생일은 계약 체결일, 소유상황보고 장내매매의
    의무발생일은 결제일이다. 둘 다 그날부터 5영업일 이내에 보고한다.
    (기업공시 길라잡이 · 보고의무 발생일)
    """
    plan = next(t for t in TRADES if t[0] == PLAN_TRADE_NO)
    print(f"[6] {PLAN_TRADE_NO}번 매도가 공시로 보이기까지 (장내매매 기준)")
    rows = [
        ("거래계획 사전공시", "거래 개시일 30일 전", "거래 전",
         "면제 요건을 못 채운 경우만"),
        ("장내 매도 체결", plan[1].isoformat(), "-",
         "5%룰 의무발생일 = 계약 체결일"),
        ("5%룰 변동보고", "체결일 + 5영업일", "거래 후",
         "이번 거래는 1% 미만이라 보고 없음"),
        ("결제", "체결일 + 2영업일", "-",
         "소유상황보고 의무발생일 = 결제일"),
        ("소유상황보고", "결제일 + 5영업일", "거래 후", "소유 수량 변동"),
    ]
    print("  " + pad("보고/사건", 20) + pad("시점", 22)
          + pad("거래와의 선후", 16) + "비고")
    for what, when, order, note in rows:
        print("  " + pad(what, 20) + pad(when, 22) + pad(order, 16) + note)
    print("  같은 거래인데 두 보고의 기산일이 다르다 — 5%룰은 체결일, "
          "소유상황보고는 결제일이다")
    print("  그래서 소유상황보고가 며칠 늦게 뜬다. 공시 날짜를 거래 날짜로 "
          "읽으면 안 되는 이유다")
    print()


def main() -> None:
    print(f"Python {platform.python_version()} / {platform.system()}")
    print("회사: 가나전자(가상) / 주주 이름과 거래 내역은 판정 기준을 보이려고 만든 값")
    print()
    print_header()
    print_who_reports()
    print_minor_change()
    print_mass_change()
    print_pre_disclosure()
    print_short_swing()
    print_timeline()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
