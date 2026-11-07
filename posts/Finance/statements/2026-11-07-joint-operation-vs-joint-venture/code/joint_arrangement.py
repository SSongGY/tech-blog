"""공동영업과 공동기업 — 같은 50% 약정을 두 방식으로 반영한 가나건설의 재무제표.

가상 회사 가나건설과 다라개발이 물류센터 약정을 50:50으로 공동지배한다. 단위는 억원.
기업회계기준서 제1111호 문단 20(공동영업자는 자산·부채·수익·비용 중 자기 몫을 인식)과
문단 24(공동기업 참여자는 지분법)를 비교한다. 표준 라이브러리만 쓴다.
"""

import platform

SHARE = 0.50

# 공동약정 전체 (1년차 말)
ARR_ASSETS = 1000.0
ARR_LIABILITIES = 600.0
ARR_REVENUE = 800.0
ARR_EXPENSES = 700.0

# 가나건설 자체 사업 (약정 지분 제외)
OWN_ASSETS = 1800.0
OWN_LIABILITIES = 1000.0
OWN_REVENUE = 3000.0
OWN_EXPENSES = 2800.0


def statements(kind: str) -> dict:
    if kind == "공동영업":
        assets = OWN_ASSETS + ARR_ASSETS * SHARE
        liabilities = OWN_LIABILITIES + ARR_LIABILITIES * SHARE
        revenue = OWN_REVENUE + ARR_REVENUE * SHARE
        expenses = OWN_EXPENSES + ARR_EXPENSES * SHARE
        equity_income = 0.0
    else:
        investment = (ARR_ASSETS - ARR_LIABILITIES) * SHARE  # 순자산 중 내 몫 한 줄
        assets = OWN_ASSETS + investment
        liabilities = OWN_LIABILITIES
        revenue = OWN_REVENUE
        expenses = OWN_EXPENSES
        equity_income = (ARR_REVENUE - ARR_EXPENSES) * SHARE  # 순이익 중 내 몫 한 줄
    net_income = revenue - expenses + equity_income
    return {
        "자산": assets,
        "부채": liabilities,
        "자본": assets - liabilities,
        "매출": revenue,
        "비용": expenses,
        "지분법이익": equity_income,
        "당기순이익": net_income,
        "부채비율 %": liabilities / (assets - liabilities) * 100,
        "매출 대비 순이익률 %": net_income / revenue * 100,
        "총자산이익률 %": net_income / assets * 100,
    }


def compare() -> None:
    print("[1] 약정 전체와 가나건설 자체 사업")
    print(f"  약정: 자산 {ARR_ASSETS:.0f}, 부채 {ARR_LIABILITIES:.0f}, "
          f"수익 {ARR_REVENUE:.0f}, 비용 {ARR_EXPENSES:.0f}, 순이익 {ARR_REVENUE - ARR_EXPENSES:.0f}")
    print(f"  가나건설 자체: 자산 {OWN_ASSETS:.0f}, 부채 {OWN_LIABILITIES:.0f}, "
          f"수익 {OWN_REVENUE:.0f}, 비용 {OWN_EXPENSES:.0f}")
    print()
    jo = statements("공동영업")
    jv = statements("공동기업")
    print(f"[2] 가나건설 재무제표 — 지분 {SHARE:.0%}")
    print(f"  {'항목':22}{'공동영업(문단 20)':>16}{'공동기업(문단 24)':>16}")
    for key in jo:
        print(f"  {key:22}{jo[key]:>16.1f}{jv[key]:>16.1f}")
    print()
    print(f"  자본과 당기순이익은 같다: 자본 {jo['자본']:.1f} / {jv['자본']:.1f}, "
          f"순이익 {jo['당기순이익']:.1f} / {jv['당기순이익']:.1f}")
    print(f"  공동영업에서 더 잡힌 자산 {jo['자산'] - jv['자산']:.1f} = "
          f"더 잡힌 부채 {jo['부채'] - jv['부채']:.1f}")


def sale_to_joint_operation() -> None:
    carrying = 100.0
    price = 160.0
    gain = price - carrying
    recognised = gain * (1 - SHARE)  # 다른 당사자 지분 한도까지만 (B34)
    print()
    print("[3] 가나건설이 장부 100인 토지를 공동영업에 160에 판다 (제1111호 B34)")
    print(f"  별도로 보면 처분이익 {gain:.1f}")
    print(f"  인식 = 처분이익 {gain:.1f} x 다른 당사자 지분 {1 - SHARE:.0%} = {recognised:.1f}")
    print(f"  자기 몫 {gain - recognised:.1f} 은 인식하지 않는다 — 토지 중 자기 몫 장부 "
          f"{price * SHARE - (gain - recognised):.1f} (= {carrying:.0f} x {SHARE:.0%})")


def main() -> None:
    print(f"환경: Python {platform.python_version()}")
    print("출발점: 가나건설·다라개발이 물류센터 약정을 50:50 공동지배, 단위 억원")
    print()
    compare()
    sale_to_joint_operation()


if __name__ == "__main__":
    main()
