"""SW사업 대가산정 가이드(2025년 개정판) AI 서비스 도입 사업비 검산.

가이드 Ⅲ장 2.2의 산정식과 적용 사례 두 건(p.165~169)을 그대로 옮겨 다시 더한다.
금액은 모두 원 단위, 부가세 별도다.
"""

# 사업유형별로 어떤 비용 항목이 붙는지 — 가이드 p.158 <비용 구조> 표
COST_ITEMS_BY_TYPE = {
    "단순 AI 서비스 도입형": ("서비스 이용료",),
    "커스터마이징형": ("서비스 이용료", "커스터마이징 작업비용"),
    "시스템통합형": ("서비스 이용료", "커스터마이징 작업비용", "구축·개발 비용"),
}


def service_fee(months, users, unit_fee):
    """2단계: 도입 기간 × 사용 규모 × 단위 이용료."""
    return months * users * unit_fee


def print_line(label, amount):
    print(f"  {label:<28}{amount:>15,} 원")


def case_simple_translation():
    print("[사례 1] AI 번역 서비스 — 단순 AI 서비스 도입형")
    fee = service_fee(months=12, users=10, unit_fee=50_000)
    print_line("서비스 총이용료 (12개월 x 10명 x 50,000)", fee)
    print_line("커스터마이징 작업비용", 0)
    print_line("구축·개발 비용", 0)
    print_line("총 서비스 도입 사업비", fee)
    print()


def case_knowledge_management():
    print("[사례 2] AI 지식관리 서비스 — 커스터마이징형(데이터 구축 포함)")
    fee = service_fee(months=12, users=20, unit_fee=30_000)

    # 세부 작업 단위로 적힌 값에서 출발해야 항목 합계가 맞는지 따로 확인할 수 있다
    requirements = {
        "요구사항 정의 (2MD x 1,000,000)": 2 * 1_000_000,
        "데이터 구축 기획 (2MD x 1,200,000)": 2 * 1_200_000,
        "모델 구현 및 학습 기획 (3MD x 1,200,000)": 3 * 1_200_000,
    }
    data_build = {
        "수집 (1,000,000건 x 50)": 1_000_000 * 50,
        "정제 (1,000,000건 x 30)": 1_000_000 * 30,
        "가공 (1,000,000건 x 60)": 1_000_000 * 60,
        "검수 (10,000건 표본 x 1,000)": 10_000 * 1_000,
    }
    model_training = {
        "모델 튜닝": 6_000_000,
        "데이터 학습": 10_000_000,
        "테스트 및 개선": 4_500_000,
    }
    validation = {
        "모델 성능 검증 (2MD x 1,500,000)": 2 * 1_500_000,
        "배포 및 운영 안정화 (2MD x 1,800,000)": 2 * 1_800_000,
    }
    groups = {
        "요구사항 분석 및 설계": requirements,
        "데이터 구축": data_build,
        "모델 구현 및 학습": model_training,
        "검증 및 안정화": validation,
    }

    print_line("서비스 총이용료 (12개월 x 20명 x 30,000)", fee)
    group_totals = {}
    for name, details in groups.items():
        group_totals[name] = sum(details.values())
        print(f"  - {name}")
        for label, amount in details.items():
            print_line("    " + label, amount)
        print_line("    소계", group_totals[name])

    customizing = sum(group_totals.values())
    print_line("커스터마이징 작업비용 합계 (재계산)", customizing)
    print_line("총 서비스 도입 사업비 (재계산)", fee + customizing)
    print()

    stated_customizing = 178_500_000
    stated_total = 185_700_000
    print("  가이드에 적힌 값과 비교")
    print_line("가이드 커스터마이징 합계", stated_customizing)
    print_line("재계산 - 가이드", customizing - stated_customizing)
    print_line("가이드 총 사업비", stated_total)
    print_line("재계산 - 가이드", fee + customizing - stated_total)
    without_validation = customizing - group_totals["검증 및 안정화"]
    print_line("검증 및 안정화를 뺀 합계", without_validation)
    print()


def main():
    print("사업유형별 비용 항목 (AI 서비스 도입 사업비 = 이용료 + 커스터마이징 + 구축·개발)")
    for business_type, items in COST_ITEMS_BY_TYPE.items():
        print(f"  {business_type:<16}: {' + '.join(items)}")
    print()
    case_simple_translation()
    case_knowledge_management()


if __name__ == "__main__":
    main()
