"""시가총액에서 EV 로 건너가는 다리를 항목별로 계산한다.

가상 회사 마루정밀의 연결 숫자로 EV 를 조립하고, 구성 항목을 하나씩
빠뜨렸을 때 EV/EBITDA 가 얼마나 움직이는지 본다. 끝에 순현금 회사
새벌소프트를 하나 더 두어 EV 가 시가총액보다 작아지는 경우를 확인한다.

금액 단위는 억원이다. 모두 설명용으로 만든 가상 값이다.
"""

import unicodedata


def width(text: str) -> int:
    """한글은 터미널에서 두 칸을 차지하므로 그만큼 세어 준다."""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def pad(text: str, size: int) -> str:
    """표시 폭 기준으로 왼쪽 정렬한다."""
    return text + " " * max(0, size - width(text))

# --- 마루정밀 (가상) 입력값 ------------------------------------------------

COMMON_SHARES = 8_000_000          # 보통주 발행주식수
COMMON_PRICE = 12_000              # 보통주 주가 (원)
PREFERRED_SHARES = 1_200_000       # 상장 우선주 발행주식수
PREFERRED_PRICE = 7_500            # 우선주 주가 (원)

SHORT_TERM_DEBT = 150.0            # 단기차입금
LONG_TERM_DEBT = 320.0             # 장기차입금
LEASE_LIABILITY = 60.0             # 리스부채 (K-IFRS 제1116호)
CASH = 110.0                       # 현금및현금성자산
SHORT_TERM_FINANCIAL = 40.0        # 단기금융상품
NON_CONTROLLING = 70.0             # 비지배지분 장부금액
NON_OPERATING = 50.0               # 관계기업투자 등 비영업자산

EBITDA = 190.0                     # 영업이익 + 감가상각비 + 무형자산상각비
LEASE_EXPENSE = 18.0               # 연간 리스료. 리스부채를 빼면 이만큼 EBITDA 도 내린다


def to_eok(shares: int, price: int) -> float:
    """주식수 × 주가를 억원 단위로 바꾼다."""
    return shares * price / 100_000_000


MARKET_CAP = to_eok(COMMON_SHARES, COMMON_PRICE)
PREFERRED_CAP = to_eok(PREFERRED_SHARES, PREFERRED_PRICE)
TOTAL_DEBT = SHORT_TERM_DEBT + LONG_TERM_DEBT + LEASE_LIABILITY
TOTAL_CASH = CASH + SHORT_TERM_FINANCIAL
NET_DEBT = TOTAL_DEBT - TOTAL_CASH


def rule(char: str = "-", width: int = 74) -> None:
    print(char * width)


def print_inputs() -> None:
    print("[1] 마루정밀 — EV 를 조립하는 데 쓰는 연결 숫자 (단위: 억원)")
    rule()
    rows = [
        ("보통주 시가총액", MARKET_CAP, f"{COMMON_SHARES:,}주 × {COMMON_PRICE:,}원"),
        ("우선주 시가총액", PREFERRED_CAP, f"{PREFERRED_SHARES:,}주 × {PREFERRED_PRICE:,}원"),
        ("단기차입금", SHORT_TERM_DEBT, "유동부채"),
        ("장기차입금", LONG_TERM_DEBT, "비유동부채"),
        ("리스부채", LEASE_LIABILITY, "유동 + 비유동"),
        ("현금및현금성자산", CASH, "제1007호 문단 6"),
        ("단기금융상품", SHORT_TERM_FINANCIAL, "만기 3개월 초과 예금"),
        ("비지배지분", NON_CONTROLLING, "연결자본, 장부금액"),
        ("비영업자산", NON_OPERATING, "관계기업투자"),
        ("EBITDA", EBITDA, "영업이익 + 감가상각비 + 무형자산상각비"),
        ("연간 리스료", LEASE_EXPENSE, "리스부채를 뺄 때 EBITDA 에서 함께 내릴 금액"),
    ]
    for name, value, note in rows:
        print(f"  {pad(name, 20)} {value:>10,.1f}   {note}")
    rule()
    print(f"  총차입금 = {SHORT_TERM_DEBT:,.0f} + {LONG_TERM_DEBT:,.0f} + "
          f"{LEASE_LIABILITY:,.0f} = {TOTAL_DEBT:,.1f}")
    print(f"  현금성자산 합 = {CASH:,.0f} + {SHORT_TERM_FINANCIAL:,.0f} = {TOTAL_CASH:,.1f}")
    print(f"  순차입금 = {TOTAL_DEBT:,.1f} - {TOTAL_CASH:,.1f} = {NET_DEBT:,.1f}")
    print()


def print_bridge() -> None:
    print("[2] 시가총액에서 EV 까지 — 더하고 빼는 순서 (단위: 억원)")
    rule()
    steps = [
        ("보통주 시가총액", MARKET_CAP, "출발점. 보통주주 몫"),
        ("+ 우선주 시가총액", PREFERRED_CAP, "보통주보다 앞선 청구권"),
        ("+ 총차입금", TOTAL_DEBT, "채권자 몫. 리스부채 포함"),
        ("- 현금성자산", -TOTAL_CASH, "인수하면 그대로 돌려받는 돈"),
        ("+ 비지배지분", NON_CONTROLLING, "EBITDA 는 100% 인데 시가총액은 지배지분뿐"),
        ("- 비영업자산", -NON_OPERATING, "EBITDA 를 만들지 않는 자산"),
    ]
    running = 0.0
    for name, delta, note in steps:
        running += delta
        print(f"  {pad(name, 22)} {delta:>+10,.1f}  →  누계 {running:>9,.1f}   {note}")
    rule()
    print(f"  EV = {running:,.1f}        EV/EBITDA = {running / EBITDA:,.2f}배")
    print()
    return None


BASE_EV = (MARKET_CAP + PREFERRED_CAP + TOTAL_DEBT
           - TOTAL_CASH + NON_CONTROLLING - NON_OPERATING)


def case(label: str, ev: float, ebitda: float) -> tuple[str, float, float, float, float]:
    multiple = ev / ebitda
    base_multiple = BASE_EV / EBITDA
    return label, ev, ebitda, multiple, (multiple / base_multiple - 1) * 100


def print_omissions() -> None:
    print("[3] 항목을 하나씩 빠뜨리면 EV/EBITDA 가 어디까지 움직이는가")
    rule()
    cases = [
        case("기준 — 전부 반영", BASE_EV, EBITDA),
        case("우선주를 빼먹음", BASE_EV - PREFERRED_CAP, EBITDA),
        case("비지배지분을 빼먹음", BASE_EV - NON_CONTROLLING, EBITDA),
        case("우선주·비지배지분을 함께 빼먹음",
             BASE_EV - PREFERRED_CAP - NON_CONTROLLING, EBITDA),
        case("비영업자산을 안 뺌", BASE_EV + NON_OPERATING, EBITDA),
        case("단기금융상품을 현금으로 안 봄", BASE_EV + SHORT_TERM_FINANCIAL, EBITDA),
        case("리스부채만 제외", BASE_EV - LEASE_LIABILITY, EBITDA),
        case("리스부채 제외 + EBITDA 도 리스료만큼 내림",
             BASE_EV - LEASE_LIABILITY, EBITDA - LEASE_EXPENSE),
    ]
    print(f"  {pad('경우', 44)}{'EV':>9}{'EBITDA':>9}{'배수':>7}{'기준대비':>11}")
    for label, ev, ebitda, multiple, diff in cases:
        print(f"  {pad(label, 44)}{ev:>9,.1f}{ebitda:>9,.1f}"
              f"{multiple:>7,.2f}배{diff:>9,.1f}%")
    rule()
    multiples = [c[3] for c in cases]
    print(f"  최저 {min(multiples):,.2f}배 ~ 최고 {max(multiples):,.2f}배, "
          f"폭 {max(multiples) - min(multiples):,.2f}배")
    print(f"  기준 배수 {BASE_EV / EBITDA:,.2f}배의 "
          f"{(max(multiples) - min(multiples)) / (BASE_EV / EBITDA) * 100:,.1f}% 에 해당한다")
    print()


def print_net_cash_case() -> None:
    """순현금 회사에서는 EV 가 시가총액보다 작아진다."""
    market_cap = 620.0
    debt = 15.0
    cash = 280.0
    ebitda = 48.0
    ev = market_cap + debt - cash

    print("[4] 새벌소프트 — 순현금 회사에서는 EV 가 시가총액보다 작다 (단위: 억원)")
    rule()
    print(f"  시가총액 {market_cap:,.1f}   총차입금 {debt:,.1f}   현금성자산 {cash:,.1f}   "
          f"EBITDA {ebitda:,.1f}")
    print(f"  순차입금 = {debt:,.1f} - {cash:,.1f} = {debt - cash:,.1f}  (음수 = 순현금)")
    print(f"  EV = {market_cap:,.1f} + {debt:,.1f} - {cash:,.1f} = {ev:,.1f}")
    print(f"  EV 가 시가총액의 {ev / market_cap * 100:,.1f}% 다")
    print(f"  EV/EBITDA = {ev / ebitda:,.2f}배   (시가총액/EBITDA 로 재면 "
          f"{market_cap / ebitda:,.2f}배)")
    rule()
    print()


def main() -> None:
    print_inputs()
    print_bridge()
    print_omissions()
    print_net_cash_case()


if __name__ == "__main__":
    main()
