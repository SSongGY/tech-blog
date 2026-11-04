"""같은 500억원을 영구채(자본)와 상환우선주(부채)로 조달한 두 회사의 지표를 계산한다.

기업회계기준서 제1032호 문단 16 은 현금 등 금융자산을 인도할 계약상 의무가 없어야
지분상품이라고 정한다. 발행자가 상환을 결정하는 영구채는 자본, 보유자가 상환을 청구할 수
있는 우선주는 부채다 (문단 18, AG25). 분류가 갈리면 같은 5% 분배금이 한쪽은 자본에서 직접
빠지고(문단 35) 다른 쪽은 이자처럼 비용이 된다(문단 36). 그 결과를 부채비율·이자보상배율·
당기순이익·ROE·보통주 EPS 로 본다.
"""

from dataclasses import dataclass

RAISED = 500.0  # 조달 금액 (억원)
COUPON = 0.05  # 영구채 이자율 = 상환우선주 배당률
BASE_LIABILITIES = 1000.0  # 조달 전 부채 — 전부 차입금, 이자율 4%
BASE_EQUITY = 1000.0  # 조달 전 자본 — 전부 보통주 몫
BASE_INTEREST = 40.0  # 기존 차입금 이자
OPERATING_PROFIT = 150.0  # 영업이익
ORDINARY_SHARES = 1.0  # 보통주 수 (억 주) — EPS 를 원 단위로 만들기 위한 값
TAX_RATE = 0.0  # 분배금의 손금 인정 여부는 세법 문제이므로 비교에서 세금을 끈다


@dataclass(frozen=True)
class Issuer:
    name: str
    instrument: str
    classified_as_equity: bool  # 제1032호 문단 16 판단 결과


TAPA = Issuer("타파중공업", "영구채 (발행자가 상환 결정)", True)
HAGEO = Issuer("하거물산", "상환우선주 (보유자가 상환 청구)", False)


def statements(issuer: Issuer, raised: float = RAISED) -> dict[str, float]:
    distribution = raised * COUPON
    if issuer.classified_as_equity:
        liabilities = BASE_LIABILITIES
        equity = BASE_EQUITY + raised
        interest_expense = BASE_INTEREST  # 분배금은 비용이 아니다 — 문단 35
        net_income = (OPERATING_PROFIT - interest_expense) * (1 - TAX_RATE)
        ordinary_income = net_income - distribution  # 보통주 몫을 셀 때는 뺀다 — 제1033호 문단 12
    else:
        liabilities = BASE_LIABILITIES + raised
        equity = BASE_EQUITY
        interest_expense = BASE_INTEREST + distribution  # 배당이 이자처럼 비용이 된다 — 문단 36
        net_income = (OPERATING_PROFIT - interest_expense) * (1 - TAX_RATE)
        ordinary_income = net_income
    return {
        "총부채": liabilities,
        "자본총계": equity,
        "보통주 자본": BASE_EQUITY,
        "부채비율": liabilities / equity * 100,
        "이자비용": interest_expense,
        "이자보상배율": OPERATING_PROFIT / interest_expense,
        "당기순이익": net_income,
        "자본에서 직접 뺀 분배": distribution if issuer.classified_as_equity else 0.0,
        "보통주 귀속 순이익": ordinary_income,
        "ROE(자본총계)": net_income / equity * 100,
        "ROE(보통주)": ordinary_income / BASE_EQUITY * 100,
        "EPS(원)": ordinary_income / ORDINARY_SHARES,
    }


def row(cells: list[str], widths: list[int]) -> str:
    return "".join(cell.rjust(w) for cell, w in zip(cells, widths))


def print_balance_sheet() -> None:
    print("[1] 조달 직후 재무상태표 — 같은 500 이 다른 칸에 앉는다 (단위: 억원)")
    w = [16, 12, 12, 12, 12]
    print(row(["회사", "총부채", "자본총계", "총자산", "부채비율(%)"], w))
    print("-" * sum(w))
    for issuer in (TAPA, HAGEO):
        s = statements(issuer)
        print(
            row(
                [
                    issuer.name,
                    f"{s['총부채']:.0f}",
                    f"{s['자본총계']:.0f}",
                    f"{s['총부채'] + s['자본총계']:.0f}",
                    f"{s['부채비율']:.1f}",
                ],
                w,
            )
        )
    print()


def print_income_path() -> None:
    print("[2] 영업이익에서 보통주 몫까지 — 분배금 25 가 빠지는 자리가 다르다")
    w = [20, 16, 16]
    print(row(["항목", TAPA.name, HAGEO.name], w))
    print("-" * sum(w))
    a, b = statements(TAPA), statements(HAGEO)
    print(row(["영업이익", f"{OPERATING_PROFIT:.0f}", f"{OPERATING_PROFIT:.0f}"], w))
    print(row(["이자비용(배당 포함)", f"{a['이자비용']:.0f}", f"{b['이자비용']:.0f}"], w))
    print(row(["당기순이익", f"{a['당기순이익']:.0f}", f"{b['당기순이익']:.0f}"], w))
    print(row(["자본에서 직접 뺀 분배", f"{a['자본에서 직접 뺀 분배']:.0f}", f"{b['자본에서 직접 뺀 분배']:.0f}"], w))
    print(row(["보통주 귀속 순이익", f"{a['보통주 귀속 순이익']:.0f}", f"{b['보통주 귀속 순이익']:.0f}"], w))
    print(row(["EPS(원)", f"{a['EPS(원)']:.0f}", f"{b['EPS(원)']:.0f}"], w))
    print()


def print_metrics() -> None:
    print("[3] 지표 — 자본총계를 쓰는 지표는 갈리고 보통주 기준 지표는 같다")
    w = [18, 16, 16, 12]
    print(row(["지표", TAPA.name, HAGEO.name, "차이"], w))
    print("-" * sum(w))
    a, b = statements(TAPA), statements(HAGEO)
    for key, fmt in [
        ("부채비율", "{:.1f}"),
        ("이자보상배율", "{:.2f}"),
        ("당기순이익", "{:.0f}"),
        ("ROE(자본총계)", "{:.1f}"),
        ("ROE(보통주)", "{:.1f}"),
        ("EPS(원)", "{:.0f}"),
    ]:
        print(row([key, fmt.format(a[key]), fmt.format(b[key]), fmt.format(a[key] - b[key])], w))
    print()


def print_sensitivity() -> None:
    print("[4] 조달 금액에 따른 부채비율 — 자본 분류는 내려가고 부채 분류는 올라간다 (%)")
    w = [12, 16, 16, 12]
    print(row(["조달 금액", "영구채(자본)", "상환우선주(부채)", "차이(%p)"], w))
    print("-" * sum(w))
    for raised in (0.0, 250.0, 500.0, 750.0, 1000.0):
        a = statements(TAPA, raised)["부채비율"]
        b = statements(HAGEO, raised)["부채비율"]
        print(row([f"{raised:.0f}", f"{a:.1f}", f"{b:.1f}", f"{b - a:.1f}"], w))
    print()


def main() -> None:
    print_balance_sheet()
    print_income_path()
    print_metrics()
    print_sensitivity()


if __name__ == "__main__":
    main()
