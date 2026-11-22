"""구조조정 충당부채 — 인식 시점과 포함 원가 (기업회계기준서 제1037호 문단 70~83, 제1019호 165).

가상 회사 가나전자가 공장 한 곳을 닫는다. 같은 계획을 두고
(1) 보고기간 말 전에 무엇이 일어났느냐에 따라 충당부채가 생기는지,
(2) 계획서에 적힌 비용 가운데 무엇이 충당부채에 들어가는지,
(3) 그 결과 두 해의 손익이 어떻게 나뉘는지를 계산한다. 단위는 억원.
"""

from dataclasses import dataclass

REPORTING_DATE = "2026-12-31"


@dataclass(frozen=True)
class CostItem:
    name: str
    amount: float
    included: bool
    basis: str


# 계획서에 적힌 항목. included 는 문단 80(직접비용 두 요건)과 81·82·83 으로 판정한다.
PLAN_ITEMS = [
    CostItem("해고급여(기업 요청 해고 추가분)", 42.0, True, "80 직접비용 / 1019호 165⑵"),
    CostItem("원재료 장기공급계약 해지 위약금", 8.0, True, "80 직접비용"),
    CostItem("설비 철거·폐기물 처리", 6.0, True, "80 직접비용"),
    CostItem("계속 근무 직원 재배치·교육", 5.0, False, "81⑴ 미래 영업 관련"),
    CostItem("다른 공장 제품 마케팅", 3.0, False, "81⑵ 미래 영업 관련"),
    CostItem("새 물류 시스템 구축", 12.0, False, "81⑶ 미래 영업 관련"),
    CostItem("폐쇄일까지 예상 영업손실", 9.0, False, "82 예상 영업손실"),
]
EXPECTED_DISPOSAL_GAIN = 4.0  # 설비 매각 예상 이익 — 문단 51·83 으로 측정에서 빼지 않는다


@dataclass(frozen=True)
class Scenario:
    label: str
    detailed_plan: bool        # 72⑴ 다섯 항목이 계획서에 다 있는가
    started_or_announced: str  # 착수·공표한 날 (없으면 "")
    is_sale: bool = False      # 사업 매각인가 (78·79)
    binding_sale_date: str = ""


SCENARIOS = [
    Scenario("A 12-10 이사회 결의만, 공표는 01-15", True, "2027-01-15"),
    Scenario("B 12-10 결의, 12-20 노조·직원에 세부 계획 통보", True, "2026-12-20"),
    Scenario("C 12-20 공표했으나 인원·지출이 계획서에 없음", False, "2026-12-20"),
    Scenario("D 12-20 사업 매각 공표, 매각약정은 03-02", True, "2026-12-20",
             is_sale=True, binding_sale_date="2027-03-02"),
]


def provision_amount() -> float:
    return sum(item.amount for item in PLAN_ITEMS if item.included)


def judge(s: Scenario) -> tuple[str, str]:
    """보고기간 말 현재 의제의무가 있는지와 그 근거를 돌려준다."""
    if s.is_sale:
        # 매각은 구속력 있는 약정을 맺어야 의무가 생긴다 — 공표만으로는 번복할 수 있다
        if s.binding_sale_date and s.binding_sale_date <= REPORTING_DATE:
            return "인식", "78 구속력 있는 매각약정"
        return "인식 안 함", "78·79 매각약정 전 — 자산은 1036호 손상검토"
    if not s.detailed_plan:
        return "인식 안 함", "72⑴ 구체적 공식 계획 요건 미충족"
    if s.started_or_announced and s.started_or_announced <= REPORTING_DATE:
        return "인식", "72⑵ 공표로 정당한 기대 형성"
    return "인식 안 함", "75 기말 후 공표 — 1010호에 따라 공시"


def main() -> None:
    print("[1] 계획서의 비용 가운데 충당부채에 들어가는 것 (문단 80~83)")
    print(f"  {'항목':<24}{'금액':>7}  {'포함':<4}  근거")
    for item in PLAN_ITEMS:
        mark = "O" if item.included else "X"
        print(f"  {item.name:<24}{item.amount:>7.1f}  {mark:<4}  {item.basis}")
    plan_total = sum(item.amount for item in PLAN_ITEMS)
    provision = provision_amount()
    print(f"  설비 매각 예상 이익 {EXPECTED_DISPOSAL_GAIN:.1f} — 차감하지 않음 (51·83)")
    print(f"  계획서 비용 합계 {plan_total:.1f} / 구조조정충당부채 {provision:.1f}"
          f" / 빠진 금액 {plan_total - provision:.1f}")
    print()

    print(f"[2] 같은 계획, 보고기간 말({REPORTING_DATE})까지 일어난 일만 다른 네 경우 (문단 72~79)")
    print(f"  {'경우':<38}{'판정':<8}{'2026 비용':>9}  근거")
    for s in SCENARIOS:
        verdict, basis = judge(s)
        expense = provision if verdict == "인식" else 0.0
        print(f"  {s.label:<38}{verdict:<8}{expense:>9.1f}  {basis}")
    print("  A·C·D 는 계획 비용이 그대로여도 2026 년 부채가 0 이다")
    print()

    print("[3] 경우 B 의 두 해 — 충당부채 변동과 손익 (문단 59·61·81·82·52)")
    actual_direct = {"해고급여(기업 요청 해고 추가분)": 40.0,
                     "원재료 장기공급계약 해지 위약금": 8.0,
                     "설비 철거·폐기물 처리": 6.0}
    used = sum(actual_direct.values())
    reversal = provision - used
    print(f"  2026 말 설정 {provision:.1f} → 2027 사용 {used:.1f}"
          f" (해고급여 실제 {actual_direct['해고급여(기업 요청 해고 추가분)']:.1f})"
          f" → 환입 {reversal:.1f} → 2027 말 잔액 {provision - used - reversal:.1f}")
    excluded_expense = 5.0 + 3.0 + 9.0  # 재배치·마케팅·영업손실은 생길 때 비용
    capitalised = 12.0                  # 새 시스템은 자산 요건을 충족한다고 가정
    print(f"  {'연도':<6}{'구조조정 비용':>12}{'환입':>8}{'제외 항목 비용':>14}"
          f"{'처분이익':>10}{'손익 영향 합계':>14}")
    # 손익에 주는 방향 그대로(비용은 음수) 담아 -0.0 이 찍히지 않게 한다
    rows = [
        ("2026", -provision, 0.0, 0.0, 0.0),
        ("2027", 0.0, reversal, -excluded_expense, EXPECTED_DISPOSAL_GAIN),
    ]
    for year, cost, rev, excl, gain in rows:
        total = cost + rev + excl + gain
        print(f"  {year:<6}{cost:>12.1f}{rev:>8.1f}{excl:>14.1f}{gain:>10.1f}{total:>14.1f}")
    print(f"  새 물류 시스템 {capitalised:.1f} 은 2027 년 자산으로 잡고 이후 상각한다고 가정")
    print("  2026 년에는 직접비용만, 나머지는 생기는 해에 따로 들어온다")


if __name__ == "__main__":
    main()
