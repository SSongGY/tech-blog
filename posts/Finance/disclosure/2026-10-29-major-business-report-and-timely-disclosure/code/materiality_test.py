"""중요한 영업·자산 양수도인가 — 주요사항보고서 제출사유를 기준으로 판정한다.

가상 회사 `가나전자`의 거래 네 건을 자본시장과 금융투자업에 관한 법률 시행령
제171조제2항의 네 가지 기준에 걸어 본다.

  1호  양수·양도하려는 영업부문의 자산액이 최근 사업연도말 자산총액의 10% 이상
  2호  양수·양도하려는 영업부문의 매출액이 최근 사업연도말 매출액의 10% 이상
  3호  영업의 양수로 인하여 인수할 부채액이 최근 사업연도말 부채총액의 10% 이상
  5호  양수·양도하려는 자산액이 최근 사업연도말 자산총액의 10% 이상
       (일상적인 영업활동으로서 상품·제품·원재료를 매매하는 행위 등은 제외)

자산액은 조문대로 **장부가액과 거래금액 중 큰 금액**을 쓴다. 어느 쪽을 쓰느냐로
결론이 뒤집히는 경우가 있어서, 판정표에 둘을 같이 찍는다.

회사와 거래는 전부 지어낸 것이다. 실재하는 회사가 아니다.
"""

import sys
import unicodedata

THRESHOLD = 0.10  # 시행령 제171조제2항이 정한 100분의 10

# 가나전자의 최근 사업연도말 연결재무제표 기준 규모. 단위는 억 원.
# 한국채택국제회계기준을 적용하는 연결재무제표 작성대상법인이면 연결 기준을 쓴다.
TOTAL_ASSETS = 8_400
TOTAL_REVENUE = 12_000
TOTAL_LIABILITIES = 3_600

# 거래 네 건. book=장부가액, deal=거래금액, revenue=해당 영업부문 매출액,
# liability=영업 양수로 인수할 부채액, routine=일상적인 상품·원재료 매매인지.
DEALS = [
    {
        "name": "A사업부 양도",
        "kind": "영업",
        "book": 720, "deal": 910, "revenue": 1_500, "liability": 0,
        "routine": False,
    },
    {
        "name": "B사업부 양수",
        "kind": "영업",
        "book": 760, "deal": 760, "revenue": 900, "liability": 420,
        "routine": False,
    },
    {
        "name": "보유 토지 매각",
        "kind": "자산",
        "book": 610, "deal": 830, "revenue": 0, "liability": 0,
        "routine": False,
    },
    {
        "name": "원재료 대량 매입",
        "kind": "자산",
        "book": 1_100, "deal": 1_100, "revenue": 0, "liability": 0,
        "routine": True,
    },
]


def width(text):
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def pad(text, size, align=">"):
    space = " " * max(0, size - width(text))
    return space + text if align == ">" else text + space


def print_environment():
    print("[환경]")
    print(f"  Python {sys.version.split()[0]}")
    print()


def print_company():
    print("[가나전자 — 최근 사업연도말 연결재무제표 (단위: 억 원)]")
    for name, value in [("자산총액", TOTAL_ASSETS),
                        ("매출액", TOTAL_REVENUE),
                        ("부채총액", TOTAL_LIABILITIES)]:
        print(f"  {pad(name, 12, '<')}{value:>10,}"
              f"    10% 기준 {value * THRESHOLD:>9,.1f}")
    print()


def asset_value(deal):
    """시행령이 말하는 자산액 — 장부가액과 거래금액 중 큰 금액."""
    return max(deal["book"], deal["deal"])


def judge(deal):
    """해당하는 호를 전부 모은다. 하나만 걸려도 제출사유가 된다."""
    hits = []
    value = asset_value(deal)
    if deal["kind"] == "영업":
        if value >= TOTAL_ASSETS * THRESHOLD:
            hits.append("1호(영업 자산액)")
        if deal["revenue"] >= TOTAL_REVENUE * THRESHOLD:
            hits.append("2호(영업 매출액)")
        if deal["liability"] >= TOTAL_LIABILITIES * THRESHOLD:
            hits.append("3호(인수 부채액)")
    else:
        if deal["routine"]:
            return []          # 5호 단서. 일상적인 상품·원재료 매매는 제외한다
        if value >= TOTAL_ASSETS * THRESHOLD:
            hits.append("5호(자산 자산액)")
    return hits


def print_judgement():
    print("[거래별 판정 — 시행령 제171조제2항]")
    widths = [(18, "거래"), (10, "장부가액"), (10, "거래금액"),
              (10, "자산액"), (10, "자산비율")]
    header = "  " + "".join(pad(name, size) for size, name in widths) + "  해당 호"
    print(header)
    print("  " + "-" * (width(header) + 28))
    for deal in DEALS:
        value = asset_value(deal)
        ratio = value / TOTAL_ASSETS * 100
        hits = judge(deal)
        mark = ", ".join(hits) if hits else "없음"
        print("  " + pad(deal["name"], 18, "<")
              + f"{deal['book']:>10,}{deal['deal']:>10,}{value:>10,}"
              + f"{ratio:>9.2f}%  {mark}")
    print()


def print_detail():
    print("[비율을 하나씩 — 어느 기준에서 갈리는가]")
    for deal in DEALS:
        value = asset_value(deal)
        print(f"  {deal['name']} ({deal['kind']})")
        lines = [
            ("자산액 / 자산총액", value, TOTAL_ASSETS),
        ]
        if deal["kind"] == "영업":
            lines.append(("영업부문 매출액 / 매출액", deal["revenue"], TOTAL_REVENUE))
            lines.append(("인수 부채액 / 부채총액", deal["liability"], TOTAL_LIABILITIES))
        for label, num, den in lines:
            ratio = num / den * 100
            flag = "기준 이상" if ratio >= THRESHOLD * 100 else "기준 미만"
            print(f"    {pad(label, 26, '<')}{num:>7,} / {den:>7,} = "
                  f"{ratio:>6.2f}%  {flag}")
        if deal["routine"]:
            print("    일상적인 상품·원재료 매매 — 5호 단서로 제외된다")
        hits = judge(deal)
        verdict = "주요사항보고서 제출사유" if hits else "제출사유 아님"
        print(f"    => {verdict}")
        print()


def print_deadline():
    """제출 시한. 법 제161조제1항 본문과 괄호 안의 예외 둘."""
    print("[제출 시한 — 법 제161조제1항]")
    rows = [
        ("원칙 (제1호~제5호, 제7호, 제8호, 제10호)", "사실이 발생한 날의 다음 날까지"),
        ("제6호 — 상법상 주식교환·주식이전·합병·분할", "사실이 발생한 날부터 3일까지"),
        ("제9호 — 전환사채·교환사채·신주인수권부사채 발행",
         "다음 날과 납입기일 1주 전 중 먼저 오는 날까지"),
    ]
    for label, deadline in rows:
        print(f"  {pad(label, 52, '<')}{deadline}")
    print()


def main():
    print_environment()
    print_company()
    print_judgement()
    print_detail()
    print_deadline()


if __name__ == "__main__":
    main()
