"""상·하한가와 변동성완화장치(VI) — 같은 주문이 장치별로 어디서 멈추는지 센다.

여기 쓰는 호가창과 주문은 장치의 판정 순서를 보이려고 만든 가상 값이다. 실제
종목의 호가가 아니고, 호가 단계의 간격도 설명을 위해 임의로 벌려 두었다.

매도호가가 얇게 깔린 종목에 큰 시장가 매수 주문 하나가 들어오는 상황을 체결
단위로 따라간다. 아무 장치가 없을 때, 가격제한폭만 있을 때, 동적 VI 만 있을 때,
정적 VI 만 있을 때, 그리고 넷을 한꺼번에 걸었을 때를 각각 돌린다.

파이썬 표준 라이브러리만 쓴다.
"""

import sys

BASE_PRICE = 10_000  # 당일 기준가격(전일 종가). 정적 VI 의 최초 참조가격이기도 하다
ORDER_SIZE = 13_000  # 들어온 시장가 매수 수량(주)

# (매도호가, 잔량). 위로 갈수록 얇아진다.
ASK_BOOK = [
    (10_000, 3_000),
    (10_200, 2_500),
    (10_550, 2_000),
    (11_000, 1_500),
    (11_750, 1_200),
    (12_500, 1_000),
    (13_100, 900),
    (14_000, 800),
]

PRICE_LIMIT = 0.30  # 가격제한폭 ±30% (2015-06-15 시행, 코넥스 제외)
DYNAMIC_GENERAL = 0.06  # 동적 VI — 유가 일반종목·코스닥 접속매매
DYNAMIC_KOSPI200 = 0.03  # 동적 VI — 코스피200 구성종목 접속매매
STATIC_VI = 0.10  # 정적 VI (2015-06-15 시행)

EPS = 1e-12


def pct(x):
    v = x * 100
    if v == 0:
        v = 0.0
    return f"{v:+7.2f}%"


def sweep(size, *, dynamic=None, static=None, limit=None, repeat=False):
    """호가창을 위로 훑으면서 각 단계에서 장치가 걸리는지 본다.

    `repeat` 가 거짓이면 처음 걸린 자리에서 멈춘 모습을 본다. 참이면 2분 단일가를
    거쳐 재개하기를 반복한다. 재개된 단일가격이 정적 VI 의 새 참조가격이 된다.
    """
    last = BASE_PRICE  # 직전 체결가 — 동적 VI 의 참조가격
    static_ref = BASE_PRICE  # 직전 단일가격 — 정적 VI 의 참조가격
    remaining = size
    log, events, traded = [], [], 0

    for level, (price, qty) in enumerate(ASK_BOOK, start=1):
        if remaining <= 0:
            break

        if limit is not None and abs(price / BASE_PRICE - 1) > limit + EPS:
            entry = ("halt", level, price, "가격제한폭", "호가 접수 거부")
            log.append(entry)
            events.append(entry)
            break

        reasons = []
        if dynamic is not None and abs(price / last - 1) >= dynamic - EPS:
            reasons.append("동적VI")
        if static is not None and abs(price / static_ref - 1) >= static - EPS:
            reasons.append("정적VI")
        if reasons:
            entry = ("halt", level, price, "·".join(reasons), "2분 단일가매매로 전환")
            log.append(entry)
            events.append(entry)
            if not repeat:
                break
            static_ref = price  # 단일가로 재개된 가격이 다음 참조가격

        take = min(qty, remaining)
        log.append(("fill", level, price, take, price / last - 1, price / BASE_PRICE - 1))
        traded += price * take
        remaining -= take
        last = price

    done = size - remaining
    return {
        "log": log,
        "events": events,
        "filled": done,
        "unfilled": remaining,
        "last": last,
        "avg": traded / done if done else 0.0,
    }


def print_fills(res):
    print("단계    체결가    체결수량   직전체결가대비   기준가대비")
    for entry in res["log"]:
        if entry[0] == "fill":
            _, level, price, qty, d_last, d_base = entry
            print(
                f" {level}    {price:>7,}원   {qty:>6,}주      {pct(d_last)}      {pct(d_base)}"
            )
        else:
            _, level, price, kind, action = entry
            print(f" {level}    {price:>7,}원   >> {kind} 발동 — {action}")


def summary(res):
    print(
        f"  → 체결 {res['filled']:,}주 · 미체결 {res['unfilled']:,}주 · "
        f"마지막 체결가 {res['last']:,}원({pct(res['last'] / BASE_PRICE - 1).strip()}) · "
        f"평균 체결가 {res['avg']:,.0f}원"
    )


def head(n, title):
    print(f"\n[{n}] {title}")
    print("-" * 74)


def main():
    head(1, "호가창과 들어온 주문")
    print(f"당일 기준가격   {BASE_PRICE:>8,}원  (전일 종가. 정적 VI 의 최초 참조가격)")
    print(f"시장가 매수     {ORDER_SIZE:>8,}주")
    print()
    print("매도호가   잔량      기준가대비")
    for price, qty in ASK_BOOK:
        print(f"{price:>8,}원  {qty:>6,}주      {pct(price / BASE_PRICE - 1)}")
    print(f"{'합계':>8}   {sum(q for _, q in ASK_BOOK):>6,}주")
    print()
    print("들어온 주문이 깔린 잔량보다 많아, 장치가 없으면 호가창을 끝까지 훑는다.")

    head(2, "장치가 하나도 없을 때")
    none = sweep(ORDER_SIZE)
    print_fills(none)
    summary(none)

    head(3, "가격제한폭 ±30% 만 있을 때")
    lim = sweep(ORDER_SIZE, limit=PRICE_LIMIT)
    print_fills(lim)
    summary(lim)
    print("  상한가 밖 호가는 접수 자체가 거부되므로 그 위 잔량은 체결되지 않는다.")

    head(4, "동적 VI 만 있을 때 — 직전 체결가에서 얼마나 벌어졌는지로 본다")
    for rate, label in ((DYNAMIC_KOSPI200, "코스피200 구성종목 3%"), (DYNAMIC_GENERAL, "유가 일반·코스닥 6%")):
        print(f"\n  · {label}")
        res = sweep(ORDER_SIZE, dynamic=rate)
        print_fills(res)
        summary(res)

    head(5, "정적 VI 10% 만 있을 때 — 직전 단일가에서 얼마나 벌어졌는지로 본다")
    st = sweep(ORDER_SIZE, static=STATIC_VI)
    print_fills(st)
    summary(st)

    head(6, "넷을 한 종목에 같이 걸었을 때 — 먼저 걸리는 것이 멈춘다")
    print("일반종목(동적 6%) 기준. 첫 발동에서 세운다.")
    both = sweep(ORDER_SIZE, dynamic=DYNAMIC_GENERAL, static=STATIC_VI, limit=PRICE_LIMIT)
    print_fills(both)
    summary(both)
    print()
    print("장치              첫 발동 단계   그때 호가     기준가대비")
    first = [
        ("동적 VI 3%   ", sweep(ORDER_SIZE, dynamic=DYNAMIC_KOSPI200)),
        ("정적 VI 10%  ", st),
        ("동적 VI 6%   ", sweep(ORDER_SIZE, dynamic=DYNAMIC_GENERAL)),
        ("가격제한폭 30%", lim),
    ]
    for label, r in first:
        _, lv, p, _, _ = r["events"][0]
        print(f"{label}         {lv}단계      {p:>7,}원    {pct(p / BASE_PRICE - 1)}")
    print()
    print("참조가격이 서로 달라 걸리는 순서가 이렇게 갈린다. 동적 VI 는 바로 앞 체결가와,")
    print("정적 VI 는 직전 단일가와, 가격제한폭은 당일 기준가격과 비교한다.")

    head(7, "2분이 지나 재개하면 — 주문이 남아 있는 한 다시 걸린다")
    rep = sweep(
        ORDER_SIZE,
        dynamic=DYNAMIC_GENERAL,
        static=STATIC_VI,
        limit=PRICE_LIMIT,
        repeat=True,
    )
    print_fills(rep)
    summary(rep)
    print(f"  → VI 발동 {len(rep['events']) - 1}회 · 가격제한폭으로 접수 거부 1회")
    print()
    print("장치를 전부 켜도 마지막 체결가는 가격제한폭이 정한 자리에서 끝난다.")
    print(f"장치 없음 {none['last']:,}원 → 전부 켬 {rep['last']:,}원.")
    print("VI 가 바꾼 것은 도달점이 아니라 거기까지 가는 길이 몇 번 끊기느냐다.")

    head(8, "평균 체결가로 보면")
    print("경우                      체결수량   평균 체결가   마지막 체결가")
    for label, res in (
        ("장치 없음            ", none),
        ("가격제한폭만         ", lim),
        ("동적 VI 6% 에서 정지 ", sweep(ORDER_SIZE, dynamic=DYNAMIC_GENERAL)),
        ("정적 VI 10% 에서 정지", st),
        ("전부 켜고 재개 반복  ", rep),
    ):
        print(
            f"{label}    {res['filled']:>7,}주   {res['avg']:>9,.0f}원   "
            f"{res['last']:>9,}원"
        )
    print()
    print("정지하는 장치는 그 순간의 체결 수량을 줄인다. 남은 주문이 사라지는 것은")
    print("아니므로, 2분 뒤 호가가 보충되지 않으면 같은 길을 나눠서 갈 뿐이다.")

    print()
    print(f"python {sys.version.split()[0]}")


if __name__ == "__main__":
    main()
