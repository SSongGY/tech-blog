"""PSR 과 PCR — 분모를 손익계산서 위쪽으로 올리면 무엇을 얻고 무엇을 잃는가.

적자라서 PER 이 성립하지 않는 구간에서 매출액과 영업활동현금흐름을 분모로 쓸 때,
(1) 어떤 회사는 PCR 도 같이 깨지고, (2) 같은 거래량을 다루는 두 회사의 PSR 이
수익 인식 방식 때문에 열 배 갈리고, (3) PSR 을 해석하려면 장래 마진 가정이
필요하고, (4) PCR 의 분모가 운전자본과 이자 분류 선택에 흔들리는 것을 계산한다.

금액 단위는 억원이고, 실재하지 않는 회사의 가정값이다.
"""
import platform
import sys

# 이름, 매출액, 순이익, 영업활동현금흐름, 시가총액, 한 줄 설명
COMPANIES = [
    ("가나전자", 5000.0, 300.0, 450.0, 4500.0, "흑자. 세 배수가 모두 성립한다"),
    ("다라바이오", 800.0, -200.0, -120.0, 6000.0, "적자이고 영업현금흐름도 음수"),
    ("마바커머스", 3000.0, -100.0, 250.0, 3000.0, "적자이나 상각비가 커서 현금은 남는다"),
    ("사아장터", 300.0, 30.0, 50.0, 3000.0, "중개 수수료만 수익으로 적는 대리인"),
]

MARGIN_CASES = [0.05, 0.10, 0.15, 0.20, 0.30, 0.50]
WORKING_CAPITAL_CASES = [-100.0, 0.0, 100.0, 200.0]

# 마바커머스·사아장터가 중개하는 같은 규모의 거래
GMV = 3000.0
COMMISSION_RATE = 0.10

# 가나전자의 이자지급 — 제1007호 문단 33 이 분류 선택을 허용한다
INTEREST_PAID = 80.0


def ratio_or_none(numerator: float, denominator: float) -> float | None:
    """분모가 0 이하면 배수가 성립하지 않는다. 음수 배수는 뜻이 없다."""
    if denominator <= 0:
        return None
    return numerator / denominator


def fmt(value: float | None, suffix: str = "배") -> str:
    if value is None:
        return "성립안함"
    return f"{value:.2f}{suffix}"


def print_definitions() -> None:
    print("[0] 산식 — 분자는 셋 다 시가총액이고 분모만 다르다")
    print("  PER = 시가총액 ÷ 당기순이익          (손익계산서 맨 아랫줄)")
    print("  PSR = 시가총액 ÷ 매출액              (손익계산서 맨 윗줄)")
    print("  PCR = 시가총액 ÷ 영업활동현금흐름    (현금흐름표, 제1007호 문단 6)")
    print("  분모가 0 이하면 배수를 쓰지 않는다. 음수 배수는 대소 비교가 되지 않는다")
    print()


def print_multiples() -> None:
    print("[1] 네 회사의 세 배수 (단위: 억원)")
    print(f"  {'':12}{'매출액':>8}{'순이익':>8}{'영업CF':>8}{'시가총액':>10}"
          f"{'PER':>11}{'PSR':>10}{'PCR':>11}")
    for name, sales, ni, ocf, cap, _ in COMPANIES:
        print(f"  {name:12}{sales:>8.0f}{ni:>8.0f}{ocf:>8.0f}{cap:>10.0f}"
              f"{fmt(ratio_or_none(cap, ni)):>12}{fmt(ratio_or_none(cap, sales)):>10}"
              f"{fmt(ratio_or_none(cap, ocf)):>12}")
    print()
    for name, _, _, _, _, note in COMPANIES:
        print(f"  {name:12}{note}")
    print("  적자라고 PSR·PCR 이 자동으로 대신해 주지 않는다. 다라바이오는 둘 중 PSR 만 남는다")
    print()


def print_agent_vs_principal() -> None:
    print("[2] 같은 거래량을 다루는 두 회사의 PSR — 제1115호 문단 B35B·B36 (단위: 억원)")
    commission = GMV * COMMISSION_RATE
    rows = [
        ("마바커머스", "본인", GMV, "총액", 3000.0, 3000.0),
        ("사아장터", "대리인", GMV, "순액", commission, 3000.0),
    ]
    print(f"  {'':12}{'구분':8}{'중개 거래액':>12}{'인식':>7}{'매출액':>9}{'시가총액':>10}{'PSR':>10}")
    for name, role, gmv, basis, sales, cap in rows:
        print(f"  {name:12}{role:8}{gmv:>12.0f}{basis:>7}{sales:>9.0f}{cap:>10.0f}"
              f"{cap / sales:>9.2f}배")
    print(f"  본인은 '대가의 총액'을, 대리인은 '보수나 수수료'를 수익으로 인식한다(수수료율 {COMMISSION_RATE:.0%} 가정)")
    print(f"  거래액도 시가총액도 같은데 PSR 이 {3000.0 / commission / (3000.0 / 3000.0):.0f}배 갈린다. "
          f"분모가 같은 뜻인지부터 확인해야 한다")
    print()


def print_implied_per() -> None:
    print("[3] PSR 을 PER 로 되돌리려면 — PSR = 순이익률 x PER")
    print("    따라서 내재 PER = PSR ÷ 가정 순이익률")
    targets = [("다라바이오", 6000.0 / 800.0), ("마바커머스", 1.00), ("가나전자", 4500.0 / 5000.0)]
    print(f"  {'':12}{'PSR':>8}" + "".join(f"{'마진 ' + f'{m:.0%}':>12}" for m in MARGIN_CASES))
    for name, psr in targets:
        cells = "".join(f"{psr / m:>11.1f}배" for m in MARGIN_CASES)
        print(f"  {name:12}{psr:>7.2f}배{cells}")
    print("  가나전자의 실제 PER 은 15.0배다. 다라바이오가 그 수준으로 읽히려면 순이익률 50% 가 필요하다")
    print("  PSR 은 마진을 가정 안에 숨긴 PER 이다. 마진 가정을 빼고 PSR 끼리 비교하면 비교가 아니다")
    print()


def print_working_capital() -> None:
    print("[4] PCR 의 분모는 운전자본에 흔들린다 — 제1007호 문단 20 간접법 (단위: 억원)")
    ni, depreciation, cap = -100.0, 350.0, 3000.0
    print(f"  마바커머스: 당기순손익 {ni:.0f} + 감가상각비 {depreciation:.0f} − 운전자본 증가 = 영업활동현금흐름")
    print(f"  {'운전자본 증감':>14}{'영업CF':>10}{'PCR':>11}{'비고':>10}")
    for delta in WORKING_CAPITAL_CASES:
        ocf = ni + depreciation - delta
        note = "회수" if delta < 0 else ("그대로" if delta == 0 else "성장으로 묶임")
        shown = "0" if delta == 0 else f"{delta:+.0f}"
        print(f"  {shown:>14}{ocf:>10.0f}{fmt(ratio_or_none(cap, ocf)):>12}  {note}")
    best = cap / (ni + depreciation - WORKING_CAPITAL_CASES[0])
    worst = cap / (ni + depreciation - WORKING_CAPITAL_CASES[-1])
    print(f"  같은 해 같은 순손익인데 PCR 이 {best:.2f}배에서 {worst:.2f}배까지 "
          f"{worst / best:.1f}배 움직인다")
    print("  매출이 빠르게 느는 회사는 운전자본이 함께 늘어 영업CF 가 눌리고, PCR 은 그만큼 높게 나온다")
    print()


def print_interest_classification() -> None:
    print("[5] 이자지급을 어디로 분류하느냐 — 제1007호 문단 33 (단위: 억원)")
    base_ocf, cap = 450.0, 4500.0
    rows = [
        ("영업활동으로 분류", base_ocf),
        ("재무활동으로 분류", base_ocf + INTEREST_PAID),
    ]
    print(f"  가나전자의 이자지급 {INTEREST_PAID:.0f}억 — 기준서는 두 분류를 모두 허용한다")
    print(f"  {'분류':24}{'영업CF':>9}{'PCR':>10}")
    for label, ocf in rows:
        print(f"  {label:24}{ocf:>9.0f}{cap / ocf:>9.2f}배")
    print(f"  선택만으로 PCR 이 {cap / base_ocf:.2f}배와 {cap / (base_ocf + INTEREST_PAID):.2f}배로 갈린다")
    print("  배수를 나란히 놓기 전에 두 회사가 같은 분류를 쓰는지 현금흐름표에서 확인한다")
    print()


def main() -> None:
    print(f"Python {platform.python_version()} / {platform.system()}")
    print("회사: 가나전자·다라바이오·마바커머스·사아장터(모두 가상) / 모든 금액은 계산 원리를 보이려고 만든 값")
    print()
    print_definitions()
    print_multiples()
    print_agent_vs_principal()
    print_implied_per()
    print_working_capital()
    print_interest_classification()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
