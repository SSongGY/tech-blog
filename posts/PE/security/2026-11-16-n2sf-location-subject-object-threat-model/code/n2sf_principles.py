"""N2SF 보안원칙 두 가지를 규칙으로 옮겨, 부록2 정보서비스 모델의 판정과 맞는지 검산한다.

근거: 국가정보원, 국가 망 보안체계 보안 가이드라인 1.0 부록2 (2025-09)
  - 모델 1 「인터넷 단말의 업무 활용성 제고」 제2장 제2절 2~3 (PDF 13~14쪽)
  - 모델 2 「업무환경에서 생성형 AI 활용」 제2장 제2절 2~4 (PDF 13~16쪽)

규칙 (부록2 제2장 제2절 3의 적용 문장에서 뽑았다)
  - 정보 생산·저장: 시스템은 자기 등급 이하의 업무정보만 생산·저장한다
  - 정보 이동: 업무정보는 자기 등급 이상의 시스템으로만 이동한다
  - 보안조치(+): 모델 1은 보안조치를 하면 O 시스템에서도 S 이상을 생산·저장·이동할 수 있다고 적는다
"""
GRADE_RANK = {"O": 0, "S": 1, "C": 2}


def check_store(system_grade, info_grade, has_extra_control=False):
    if GRADE_RANK[info_grade] <= GRADE_RANK[system_grade]:
        return "허용"
    return "허용(보안조치+)" if has_extra_control else "위배"


def check_move(info_grade, target_grade, has_extra_control=False):
    if GRADE_RANK[info_grade] <= GRADE_RANK[target_grade]:
        return "허용"
    return "허용(보안조치+)" if has_extra_control else "위배"


# (설명, 계산 함수, 인자, 부록2 본문이 적은 판정, 근거 쪽)
MODEL_2 = {
    "name": "모델 2 업무환경에서 생성형 AI 활용",
    "grades": ("S", "S", "O"),   # 위치(기관 전산망)-주체(이용자 단말)-객체(생성형 AI)
    "cases": [
        ("이용자 단말(S)에 S 정보 작성·보관", check_store, ("S", "S"), "허용", 14),
        ("이용자 단말(S)에 O 정보 작성·보관", check_store, ("S", "O"), "허용", 14),
        ("생성형 AI(O)에서 S 정보 생산", check_store, ("O", "S"), "위배", 14),
        ("단말의 O 정보 → 생성형 AI(O)", check_move, ("O", "O"), "허용", 14),
        ("단말의 S 정보 → 생성형 AI(O)", check_move, ("S", "O"), "위배", 14),
        ("생성형 AI 의 O 결과 → 단말(S)", check_move, ("O", "S"), "허용", 14),
    ],
}

MODEL_1 = {
    "name": "모델 1 인터넷 단말의 업무 활용성 제고",
    "grades": ("O", "O", "O"),   # 위치(망 분리된 O 영역)-주체(인터넷 단말)-객체(인터넷 서비스)
    "cases": [
        ("인터넷 단말(O)에 O 정보 작성·보관", check_store, ("O", "O"), "허용", 14),
        ("인터넷 단말·서비스(O)에서 S 정보 생산", check_store, ("O", "S"), "위배", 14),
        ("같은 경우, 보안조치(+) 적용", check_store, ("O", "S", True), "허용(보안조치+)", 14),
        ("단말의 O 정보 → 인터넷 서비스(O)", check_move, ("O", "O"), "허용", 14),
        ("단말의 S 정보 → 인터넷 서비스(O), 보안조치(+)", check_move, ("S", "O", True),
         "허용(보안조치+)", 14),
        ("인터넷 서비스의 O 결과 → 단말(O)", check_move, ("O", "O"), "허용", 14),
    ],
}

# 각 모델 표 2-1 의 보안위협 번호를 대상별로 묶은 것
# 모델 1: PDF 15쪽, 모델 2: PDF 16쪽
MODEL_1["threats"] = {
    "이용자 단말(인터넷 단말)": range(1, 6),
    "인터넷 연계체계": range(6, 10),
}
MODEL_2["threats"] = {
    "이용자 단말(업무 단말·온북)": range(1, 9),
    "AI 연계체계": range(9, 20),
    "생성형 AI 서비스": range(20, 22),
}


def run_model(model):
    location, subject, obj = model["grades"]
    print(f"[{model['name']}]")
    print(f"  위치 {location} · 주체 {subject} · 객체 {obj}")
    mismatches = 0
    for label, rule, args, expected, page in model["cases"]:
        verdict = rule(*args)
        same = verdict == expected
        mismatches += not same
        print(f"  {label:<38} 계산 {verdict:<12} 문서 {expected:<12}"
              f" ({page}쪽) {'일치' if same else '불일치'}")
    print(f"  불일치 {mismatches}건")
    print()


def print_threats(model, prefix):
    print(f"[{model['name']} — 표 2-1 보안위협 대상별 개수]")
    total = 0
    for target, numbers in model["threats"].items():
        ids = f"{prefix}-{numbers.start}~{numbers.stop - 1}"
        print(f"  {target:<24} {len(numbers):>2}개 ({ids})")
        total += len(numbers)
    print(f"  합계 {total}개, 대상 {len(model['threats'])}곳")
    print()


def main():
    run_model(MODEL_2)
    run_model(MODEL_1)
    print_threats(MODEL_1, "TH-M1")
    print_threats(MODEL_2, "TH-M2")


if __name__ == "__main__":
    main()
