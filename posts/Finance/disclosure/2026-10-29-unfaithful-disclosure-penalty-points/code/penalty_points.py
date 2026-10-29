"""불성실공시 벌점이 어떻게 계산되고 어느 문턱에서 제재가 바뀌는지 계산한다.

기준은 코스닥시장 공시규정의 제재심의 기준이다.
  부과 벌점 = 심의 기준표상 벌점 ± min(|감경 사유 + 가중 사유|, 4)
  0 <= 부과 벌점 <= 14

마바건설·사아테크는 실재하지 않는 가상 회사다.
"""

import sys

# 제재심의 기준표 — (위반의 중요성, 위반의 동기) -> 기준 벌점
BASE_POINTS = {
    ("중대한 위반", "고의"): 10,
    ("중대한 위반", "중대한 과실"): 8,
    ("중대한 위반", "통상의 과실"): 6,
    ("중대한 위반", "경미한 과실"): 4,
    ("통상의 위반", "고의"): 8,
    ("통상의 위반", "중대한 과실"): 6,
    ("통상의 위반", "통상의 과실"): 4,
    ("통상의 위반", "경미한 과실"): 2,
    ("경미한 위반", "고의"): 6,
    ("경미한 위반", "중대한 과실"): 4,
    ("경미한 위반", "통상의 과실"): 2,
    ("경미한 위반", "경미한 과실"): 0,
}

ADJUST_CAP = 4          # 가중·감경 합산의 상한
MAX_POINTS = 14         # 1건당 최대 벌점
HALT_THRESHOLD = 8      # 이 이상이면 지정일 1일간 매매거래정지
REVIEW_THRESHOLD = 15   # 최근 1년 누계가 이 이상이면 상장적격성 실질심사
FINE_PER_POINT = 400    # 벌점 1점당 제재금 (만원)
LATE_MULTIPLIER = 1.2   # 제재금 미납시 가중벌점 배수

# 가상 회사의 공시위반 이력. 같은 사업연도 안에서 차례로 일어난다.
CASES = {
    "마바건설": [
        {
            "일자": "2026-02-13",
            "유형": "공시변경",
            "내용": "단일판매·공급계약 금액을 50% 이상 변경",
            "중요성": "통상의 위반",
            "동기": "통상의 과실",
            "조정": [("거래소 인지 전 자진 신고", -1.0),
                     ("최근 2년간 지정 사실 없음", -1.0)],
        },
        {
            "일자": "2026-06-05",
            "유형": "공시번복",
            "내용": "유상증자 결정을 전면 취소",
            "중요성": "중대한 위반",
            "동기": "중대한 과실",
            "조정": [("최근 1년간 1회 지정", 1.0),
                     ("법규설명회 4시간 이상 이수", -0.5)],
        },
        {
            "일자": "2026-09-18",
            "유형": "공시불이행",
            "내용": "최대주주 변경을 신고 기한까지 공시하지 않음",
            "중요성": "중대한 위반",
            "동기": "고의",
            "조정": [("최근 1년간 2회 이상 지정", 2.0),
                     ("자료 제출 거부", 1.0),
                     ("의무교육 미이수", 1.0)],
        },
    ],
    "사아테크": [
        {
            "일자": "2026-04-22",
            "유형": "공시변경",
            "내용": "의무 비율 미만의 자율공시 금액을 변경",
            "중요성": "경미한 위반",
            "동기": "경미한 과실",
            "조정": [("최근 2년간 지정 사실 없음", -1.0)],
        },
    ],
}


def assess(case):
    """한 건의 부과 벌점을 계산한다. 조정 폭은 ±4점으로 잘리고 결과는 0~14로 묶인다."""
    base = BASE_POINTS[(case["중요성"], case["동기"])]
    raw = sum(points for _, points in case["조정"])
    capped = max(-ADJUST_CAP, min(ADJUST_CAP, raw))
    return {
        "기준벌점": base,
        "조정합계": raw,
        "적용조정": capped,
        "부과벌점": max(0, min(MAX_POINTS, base + capped)),
    }


def print_matrix():
    print("[표 1] 제재심의 기준표 — 위반의 중요성 × 위반의 동기")
    motives = ["고의", "중대한 과실", "통상의 과실", "경미한 과실"]
    print(f"{'':<12}" + "".join(f"{m:>12}" for m in motives))
    for severity in ["중대한 위반", "통상의 위반", "경미한 위반"]:
        row = "".join(f"{BASE_POINTS[(severity, m)]:>12}" for m in motives)
        print(f"{severity:<12}{row}")
    print()


def print_company(name):
    print(f"[계산] {name} — 건별 부과 벌점과 누계")
    running = 0.0
    for case in CASES[name]:
        result = assess(case)
        running += result["부과벌점"]
        print(f"  {case['일자']}  {case['유형']}  {case['내용']}")
        detail = ", ".join(f"{label} {points:+.1f}" for label, points in case["조정"])
        print(f"      기준벌점 {result['기준벌점']}점"
              f"  ·  조정 {detail}")
        print(f"      합계 {result['조정합계']:+.1f} → 상한 적용 {result['적용조정']:+.1f}"
              f"  ⇒ 부과 벌점 {result['부과벌점']:.1f}점")
        halt = "매매거래정지 1일" if result["부과벌점"] >= HALT_THRESHOLD else "거래정지 없음"
        review = ("상장적격성 실질심사 대상" if running >= REVIEW_THRESHOLD
                  else f"실질심사 문턱까지 {REVIEW_THRESHOLD - running:.1f}점")
        print(f"      누계 {running:.1f}점  ·  {halt}  ·  {review}")
        print()
    return running


def print_fine_substitution():
    """벌점 대신 제재금을 내는 길과, 그 제재금을 미납했을 때를 비교한다."""
    case = CASES["마바건설"][0]
    points = assess(case)["부과벌점"]
    fine = points * FINE_PER_POINT
    late = (fine / FINE_PER_POINT) * LATE_MULTIPLIER

    print("[계산] 마바건설 첫 건 — 제재금 대체 부과를 신청하면")
    print(f"  부과 벌점 {points:.1f}점 (8점 미만이고 5점 미만이므로 전부 대체 가능)")
    print(f"  대체 제재금 = {points:.1f}점 × {FINE_PER_POINT}만원 = {fine:,.0f}만원")
    print(f"  납부하면 벌점 0점, 누계에 쌓이지 않는다.")
    print(f"  기한 내 미납하면 가중벌점 = ({fine:,.0f}만원 / {FINE_PER_POINT}만원)"
          f" × {LATE_MULTIPLIER} = {late:.1f}점")
    print(f"  대체를 신청하지 않았을 때의 {points:.1f}점보다 {late - points:.1f}점 많다.")
    print()


def main():
    print(f"Python {sys.version.split()[0]}")
    print()
    print_matrix()
    for name in CASES:
        total = print_company(name)
        print(f"  → {name} 1년 누계 {total:.1f}점"
              f" ({'실질심사 대상' if total >= REVIEW_THRESHOLD else '실질심사 대상 아님'})")
        print()
    print_fine_substitution()


if __name__ == "__main__":
    main()
