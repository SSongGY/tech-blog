"""가상 회사 여섯 곳에 내부회계관리제도 적용 요건을 걸어 본다.

자산총액·종업원 수는 전부 지어낸 값이고, 실재하는 회사의 수치가 아니다.
판정 규칙만 실제 요건이다. 금융감독원 '내부회계관리제도 관련 FAQ'(2025.12)가
정리한 외부감사법 제8조와 같은 법 시행령 제9조의 요건을 그대로 옮겼다.
"""

import sys
from dataclasses import dataclass

# 자산총액은 억원 단위로 적는다. 요건의 기준선(1천억·5천억·2조)이
# 전부 억원 단위로 떨어져서 환산 없이 바로 비교된다.
BILLION_WON = 1_000
HALF_TRILLION_WON = 5_000
TWO_TRILLION_WON = 20_000


@dataclass
class Company:
    """직전 사업연도말 기준으로 본 회사의 상태."""

    name: str
    listed: bool          # 주권상장법인(코넥스 포함) 여부
    assets: int           # 별도재무제표 기준 자산총액 (억원)
    employees: int        # 종업원 수
    parent: bool          # 연결재무제표를 작성하는 지배회사인지
    reporting: bool = False  # 금융회사·사업보고서 제출대상·공시대상기업집단 소속


def must_operate(company):
    """운영 의무가 있는가 — 외부감사법 제8조 제1항, 시행령 제9조 제1항."""
    # 종업원 요건이 자산·상장 요건보다 먼저 걸린다. 자산이 아무리 커도
    # 6명 미만이면 운영 의무 자체가 없다.
    if company.employees < 6:
        return False, "종업원 6명 미만이라 적용 예외"
    if company.listed:
        return True, "주권상장법인"
    line = BILLION_WON if company.reporting else HALF_TRILLION_WON
    if company.assets >= line:
        return True, f"대형 비상장회사 (기준선 {line:,}억원)"
    return False, f"비상장이고 자산이 기준선 {line:,}억원에 못 미침"


def assurance(company):
    """감사인이 감사를 하는가 검토를 하는가 — 외부감사법 제8조 제6항·제7항."""
    operating, _ = must_operate(company)
    if not operating:
        return "없음"
    if company.listed:
        return "감사" if company.assets >= BILLION_WON else "검토"
    return "검토"


def consolidated_start(company):
    """연결 내부회계관리제도 운영 의무가 시작되는 사업연도 — 시행령 제9조 제2항 제6호, 부칙 제3조."""
    operating, _ = must_operate(company)
    if not (operating and company.listed and company.parent):
        return "해당 없음"
    if company.assets >= TWO_TRILLION_WON:
        return "2022-12-31 이후 개시"
    if company.assets >= HALF_TRILLION_WON:
        return "2029-01-01 이후 개시"
    return "2030-01-01 이후 개시"


COMPANIES = [
    Company("가나전자", listed=True, assets=32_000, employees=4_100, parent=True),
    Company("다라물산", listed=True, assets=8_400, employees=620, parent=True),
    Company("마바소재", listed=True, assets=2_300, employees=310, parent=False),
    Company("사아정밀", listed=True, assets=740, employees=95, parent=True),
    Company("자차개발", listed=False, assets=6_100, employees=240, parent=True),
    Company("카타홀딩스", listed=True, assets=41_000, employees=4, parent=True),
]


def main():
    print(f"Python {sys.version.split()[0]}")
    print()
    print("[ 가상 회사 여섯 곳의 직전 사업연도말 상태 ]")
    header = f"{'회사':<10} {'상장':<6} {'별도 자산':>12} {'종업원':>8} {'지배회사':<10}"
    print(header)
    print("-" * len(header))
    for c in COMPANIES:
        print(
            f"{c.name:<10} {'상장' if c.listed else '비상장':<6} "
            f"{c.assets:>10,}억원 {c.employees:>8,} {'예' if c.parent else '아니오':<10}"
        )

    print()
    print("[ 판정 ]")
    header = f"{'회사':<10} {'운영 의무':<10} {'별도 인증':<8} {'연결 내부회계 개시':<22} 근거"
    print(header)
    print("-" * 86)
    for c in COMPANIES:
        operating, reason = must_operate(c)
        print(
            f"{c.name:<10} {'있음' if operating else '없음':<10} "
            f"{assurance(c):<8} {consolidated_start(c):<22} {reason}"
        )


if __name__ == "__main__":
    main()
