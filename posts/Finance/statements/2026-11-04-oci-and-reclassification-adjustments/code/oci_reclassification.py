"""같은 평가이익 60억원이 세 경로로 자본에 닿는 과정을 2년간 계산한다.

기업회계기준서 제1001호 문단 7 은 기타포괄손익을 '당기손익으로 인식하지 않은 수익과
비용항목' 으로, 재분류조정을 '당기나 과거 기간에 기타포괄손익으로 인식되었으나
당기손익으로 재분류된 금액' 으로 정의한다. 같은 증권을 사서 같은 값에 판 세 회사가
당기순이익·기타포괄손익·총포괄이익을 어느 해에 얼마씩 적는지, 그래서 자본총계는
같은데 ROE 가 어떻게 갈리는지 본다.
"""

from dataclasses import dataclass

OPERATING_INCOME = 100.0  # 증권을 뺀 본업의 당기순이익 (억원, 매년 같다)
OPENING_EQUITY = 1000.0  # 1년 초 자본총계 (이익잉여금 1,000, 기타포괄손익누계액 0)
PURCHASE = 200.0  # 1년 초 증권 취득원가
FAIR_VALUE_Y1 = 260.0  # 1년 말 공정가치 — 평가이익 60
SALE_PRICE_Y2 = 260.0  # 2년 중 처분가액 — 2년에는 추가 변동이 없다
TAX_RATE = 0.0  # 세 경로의 과세소득 합계가 같으므로 비교에서 법인세를 끈다


@dataclass(frozen=True)
class YearResult:
    """한 회사의 한 해 포괄손익과 연말 자본 구성 (억원)."""

    net_income: float  # 당기순이익
    oci_arising: float  # 당기에 새로 생긴 기타포괄손익
    reclassification: float  # 재분류조정 — 기타포괄손익에서 빼서 당기손익으로 옮긴 금액
    retained_earnings: float  # 연말 이익잉여금
    accumulated_oci: float  # 연말 기타포괄손익누계액

    @property
    def oci_total(self) -> float:
        return self.oci_arising + self.reclassification

    @property
    def comprehensive_income(self) -> float:
        return self.net_income + self.oci_total

    @property
    def equity(self) -> float:
        return self.retained_earnings + self.accumulated_oci


def fvpl(gain: float) -> list[YearResult]:
    """당기손익-공정가치 측정 — 평가이익이 그 해 당기손익으로 바로 들어간다."""
    y1 = YearResult(OPERATING_INCOME + gain, 0.0, 0.0, OPENING_EQUITY + OPERATING_INCOME + gain, 0.0)
    y2 = YearResult(OPERATING_INCOME, 0.0, 0.0, y1.retained_earnings + OPERATING_INCOME, 0.0)
    return [y1, y2]


def fvoci_debt(gain: float) -> list[YearResult]:
    """채무상품 FVOCI (제1109호 문단 4.1.2A·5.7.10) — 처분할 때 재분류조정으로 당기손익에 들어온다."""
    y1 = YearResult(OPERATING_INCOME, gain, 0.0, OPENING_EQUITY + OPERATING_INCOME, gain)
    # 처분이익 gain 이 당기손익에 잡히고, 같은 금액이 기타포괄손익에서 재분류조정으로 빠진다
    y2 = YearResult(
        OPERATING_INCOME + gain,
        0.0,
        -gain,
        y1.retained_earnings + OPERATING_INCOME + gain,
        y1.accumulated_oci - gain,
    )
    return [y1, y2]


def fvoci_equity(gain: float) -> list[YearResult]:
    """지분상품 FVOCI 지정 (제1109호 문단 5.7.5·B5.7.1) — 처분해도 당기손익으로 돌아오지 않는다.

    누적액은 자본 안에서 이익잉여금으로 옮길 수 있다 (B5.7.1). 여기서는 옮기는 것으로 둔다.
    """
    y1 = YearResult(OPERATING_INCOME, gain, 0.0, OPENING_EQUITY + OPERATING_INCOME, gain)
    y2 = YearResult(
        OPERATING_INCOME,
        0.0,
        0.0,
        y1.retained_earnings + OPERATING_INCOME + gain,  # 자본 내 대체 — 손익을 거치지 않는다
        y1.accumulated_oci - gain,
    )
    return [y1, y2]


COMPANIES = [
    ("아자전자", "당기손익(FVPL)", fvpl),
    ("차카물산", "채무상품 FVOCI", fvoci_debt),
    ("타파산업", "지분상품 FVOCI", fvoci_equity),
]


def row(cells: list[str], widths: list[int]) -> str:
    return "".join(cell.rjust(w) for cell, w in zip(cells, widths))


def print_comprehensive_income(gain: float) -> None:
    print("[1] 포괄손익계산서 — 같은 60억원이 세 경로로 적힌다 (단위: 억원)")
    w = [10, 16, 6, 10, 10, 10, 10]
    print(row(["회사", "경로", "연도", "당기순이익", "OCI 발생", "재분류조정", "총포괄이익"], w))
    print("-" * sum(w))
    for name, route, fn in COMPANIES:
        for year, r in enumerate(fn(gain), start=1):
            print(
                row(
                    [
                        name,
                        route,
                        f"{year}",
                        f"{r.net_income:.0f}",
                        f"{r.oci_arising:.0f}",
                        f"{r.reclassification:.0f}",
                        f"{r.comprehensive_income:.0f}",
                    ],
                    w,
                )
            )
    print()


def print_equity_composition(gain: float) -> None:
    print("[2] 연말 자본 구성 — 자본총계는 세 회사가 매년 같다")
    w = [10, 16, 6, 12, 16, 10]
    print(row(["회사", "경로", "연도", "이익잉여금", "기타포괄손익누계액", "자본총계"], w))
    print("-" * sum(w))
    for name, route, fn in COMPANIES:
        for year, r in enumerate(fn(gain), start=1):
            print(
                row(
                    [
                        name,
                        route,
                        f"{year}",
                        f"{r.retained_earnings:.0f}",
                        f"{r.accumulated_oci:.0f}",
                        f"{r.equity:.0f}",
                    ],
                    w,
                )
            )
    print()


def print_two_year_sum(gain: float) -> None:
    print("[3] 2년 누계 — 당기순이익은 갈리고 총포괄이익은 같다")
    w = [10, 16, 14, 14, 14]
    print(row(["회사", "경로", "순이익 누계", "OCI 누계", "총포괄이익 누계"], w))
    print("-" * sum(w))
    for name, route, fn in COMPANIES:
        rs = fn(gain)
        ni = sum(r.net_income for r in rs)
        oci = sum(r.oci_total for r in rs)
        print(row([name, route, f"{ni:.0f}", f"{oci:.0f}", f"{ni + oci:.0f}"], w))
    print()
    print("  재분류조정이 2년 차 OCI 에서 60 을 빼기 때문에 차카물산의 총포괄이익 누계가 260 이 된다.")
    print("  빼지 않으면 같은 60 이 1년 차 OCI 와 2년 차 순이익에 두 번 들어간다 (문단 93).")
    print()


def print_roe(gain: float) -> None:
    print("[4] ROE — 분자를 당기순이익으로 쓰느냐 총포괄이익으로 쓰느냐 (기초 자본총계 기준, %)")
    w = [10, 16, 6, 12, 14, 16]
    print(row(["회사", "경로", "연도", "기초자본", "ROE(순이익)", "ROE(총포괄이익)"], w))
    print("-" * sum(w))
    for name, route, fn in COMPANIES:
        opening = OPENING_EQUITY
        for year, r in enumerate(fn(gain), start=1):
            print(
                row(
                    [
                        name,
                        route,
                        f"{year}",
                        f"{opening:.0f}",
                        f"{r.net_income / opening * 100:.1f}",
                        f"{r.comprehensive_income / opening * 100:.1f}",
                    ],
                    w,
                )
            )
            opening = r.equity
    print()


def main() -> None:
    gain = (FAIR_VALUE_Y1 - PURCHASE) * (1 - TAX_RATE)
    assert SALE_PRICE_Y2 == FAIR_VALUE_Y1, "2년 차에 추가 변동이 없다고 둔 모형이다"
    print_comprehensive_income(gain)
    print_equity_composition(gain)
    print_two_year_sum(gain)
    print_roe(gain)


if __name__ == "__main__":
    main()
