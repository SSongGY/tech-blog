"""감사인 지정 사유에 걸리는지를 세 회사의 3개년 숫자로 판정한다.

두 갈래를 각각 센다.

1. 직권지정 — 외부감사법 제11조 제1항 제6호 가·나·다목의 재무 요건
   (3개 사업연도 연속 영업이익 0 미만 / 영업현금흐름 0 미만 / 이자보상배율 1 미만)
2. 주기적 지정 — 같은 조 제2항. 연속하는 6개 사업연도를 자유선임하면
   그다음 3개 사업연도는 증권선물위원회가 지정한다

회사와 숫자는 전부 지어낸 값이다. 실제 기업의 재무제표가 아니다.
단위는 억 원이다.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass


def pad(text: str, width: int) -> str:
    """한글은 터미널에서 두 칸을 차지하므로 len() 으로는 자리가 안 맞는다."""
    shown = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)
    return " " * max(0, width - shown) + text


@dataclass
class Year:
    """한 사업연도의 손익·현금흐름. 이자비용은 0보다 큰 값으로 둔다."""

    fiscal_year: int
    operating_income: float  # 영업이익
    operating_cash_flow: float  # 영업활동현금흐름
    interest_expense: float  # 이자비용

    @property
    def interest_coverage(self) -> float:
        """이자보상배율 = 영업이익 / 이자비용."""
        return self.operating_income / self.interest_expense


COMPANIES: dict[str, list[Year]] = {
    # 셋 다 영업이익이 나고 이자도 충분히 덮는다
    "가나전자": [
        Year(2023, 820.0, 910.0, 140.0),
        Year(2024, 760.0, 845.0, 150.0),
        Year(2025, 910.0, 1_020.0, 155.0),
    ],
    # 영업이익이 3년 내리 적자다
    "다라물산": [
        Year(2023, -45.0, 60.0, 90.0),
        Year(2024, -120.0, -30.0, 105.0),
        Year(2025, -80.0, 25.0, 118.0),
    ],
    # 영업이익도 현금흐름도 플러스인데 이자비용이 그보다 크다
    "마바산업": [
        Year(2023, 210.0, 340.0, 290.0),
        Year(2024, 185.0, 310.0, 315.0),
        Year(2025, 240.0, 405.0, 330.0),
    ],
}


def check_clause_6(years: list[Year]) -> dict[str, bool]:
    """제11조 제1항 제6호 가·나·다목. 세 목 모두 '3개 사업연도 연속'이 요건이다."""
    return {
        "가. 영업이익 3년 연속 0 미만": all(y.operating_income < 0 for y in years),
        "나. 영업현금흐름 3년 연속 0 미만": all(y.operating_cash_flow < 0 for y in years),
        "다. 이자보상배율 3년 연속 1 미만": all(y.interest_coverage < 1 for y in years),
    }


def periodic_schedule(first_free_year: int) -> list[tuple[int, str]]:
    """제10조 제3항의 3년 계약 두 번(=6년 자유선임) 뒤에 3년 지정이 붙는다."""
    schedule: list[tuple[int, str]] = []
    for offset in range(6):
        term = 1 if offset < 3 else 2
        schedule.append((first_free_year + offset, f"자유선임 {term}기"))
    for offset in range(6, 9):
        schedule.append((first_free_year + offset, "증선위 지정"))
    return schedule


def main() -> None:
    print("=" * 66)
    print("1. 직권지정 재무 요건 — 외부감사법 제11조 제1항 제6호 (단위: 억 원)")
    print("=" * 66)
    for name, years in COMPANIES.items():
        print(f"\n[{name}]")
        header = (
            pad("사업연도", 10)
            + pad("영업이익", 12)
            + pad("영업현금흐름", 16)
            + pad("이자비용", 12)
            + pad("이자보상배율", 16)
        )
        print(f"  {header}")
        for y in years:
            print(
                "  "
                + pad(str(y.fiscal_year), 10)
                + pad(f"{y.operating_income:,.0f}", 12)
                + pad(f"{y.operating_cash_flow:,.0f}", 16)
                + pad(f"{y.interest_expense:,.0f}", 12)
                + pad(f"{y.interest_coverage:.2f}", 16)
            )
        result = check_clause_6(years)
        hit = [label for label, matched in result.items() if matched]
        for label, matched in result.items():
            print(f"    {pad('해당' if matched else '해당 없음', 9)}  {label}")
        verdict = "지정 사유에 걸린다" if hit else "이 호로는 걸리지 않는다"
        print(f"  -> {verdict}")

    print()
    print("=" * 66)
    print("2. 주기적 지정 — 같은 조 제2항, 2020 사업연도부터 자유선임했다고 둘 때")
    print("=" * 66)
    print("  상장법인은 연속 3개 사업연도를 같은 감사인으로 선임해야 한다(제10조 제3항).")
    print("  그래서 자유선임 6년은 3년 계약 두 번이 된다.")
    print()
    for year, label in periodic_schedule(2020):
        mark = "  <-- 회사가 고르지 못한다" if label == "증선위 지정" else ""
        print(f"  {year} 사업연도   {label}{mark}")

    print()
    print("  지정 3년이 끝난 뒤에도 그 감사인을 곧바로 다시 선임할 수는 없다")
    print("  (제11조 제6항). 지정 사업연도 이후 최초로 도래하는 사업연도의")
    print("  감사인으로는 선임하지 못한다.")


if __name__ == "__main__":
    main()
