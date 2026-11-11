"""동등 분할과 분류 트리로 뽑은 테스트 케이스를 실제 구현에 돌리고,
같은 케이스가 구조 쪽에서 분기를 얼마나 덮는지 coverage.py 로 잰다."""

import importlib
import io
import platform
import sys
from pathlib import Path

import coverage

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# (TC 번호, 파티션 또는 잎 클래스, 입력, 명세에서 정한 기대 출력)
EQUIVALENCE_SUITE = [
    ("EP-1", "정수 · 10 미만", "5", "Fail"),
    ("EP-2", "정수 · 10 이상 100 이하", "50", "Pass"),
    ("EP-3", "정수 · 100 초과", "150", "Fail"),
    ("EP-4", "정수 아님", "abc", "Invalid Input"),
]

CLASSIFICATION_TREE_SUITE = [
    ("CT-1", "정수 > 10 미만", "5", "Fail"),
    ("CT-2", "정수 > 10 이상 100 이하", "50", "Pass"),
    ("CT-3", "정수 > 100 초과", "150", "Fail"),
    ("CT-4", "정수 아님 > 소수", "12.5", "Invalid Input"),
    ("CT-5", "정수 아님 > 문자", "abc", "Invalid Input"),
    ("CT-6", "정수 아님 > 빈 입력", "", "Invalid Input"),
]

# 분류 트리의 범위 클래스 경계에서 뽑은 값. 트리가 경계값을 드러내 주는 쓰임새다.
BOUNDARY_SUITE = [
    ("BV-1", "10 미만 상한", "9", "Fail"),
    ("BV-2", "10 이상 하한", "10", "Pass"),
    ("BV-3", "100 이하 상한", "100", "Pass"),
    ("BV-4", "100 초과 하한", "101", "Fail"),
]


def run_suite(module, suite):
    failed = []
    for case_id, _, raw_input, expected in suite:
        actual = module.check(raw_input)
        if actual != expected:
            failed.append((case_id, raw_input, expected, actual))
    return failed


def print_suite(title, suite):
    print(f"[{title}] {len(suite)}건")
    for case_id, label, raw_input, expected in suite:
        shown = repr(raw_input)
        print(f"  {case_id:<5} {label:<22} 입력 {shown:<7} 기대 {expected}")
    print()


def measure_branches(title, suite):
    """구현 checker.py 의 문장·분기 커버리지를 coverage.py 리포트 그대로 찍는다."""
    cov = coverage.Coverage(data_file=None, branch=True, include=[str(HERE / "checker.py")])
    cov.start()
    module = importlib.reload(importlib.import_module("checker"))
    failed = run_suite(module, suite)
    cov.stop()
    report = io.StringIO()
    cov.report(file=report, show_missing=True)
    print(f"[커버리지] {title} — 실패 {len(failed)}건")
    for line in report.getvalue().splitlines():
        print("  " + line.replace(str(HERE) + "\\", "").replace(str(HERE) + "/", ""))
    print()


def main():
    print(f"Python {platform.python_version()}, coverage {coverage.__version__}, {platform.system()} {platform.release()}")
    print()
    print_suite("동등 분할", EQUIVALENCE_SUITE)
    print_suite("분류 트리 최소 클래스 커버리지", CLASSIFICATION_TREE_SUITE)
    print_suite("분류 트리 경계값 보강", BOUNDARY_SUITE)

    measure_branches("동등 분할 4건", EQUIVALENCE_SUITE)
    measure_branches("분류 트리 6건", CLASSIFICATION_TREE_SUITE)

    defect = importlib.import_module("checker_defect")
    print("[결함 구현] 상한 비교를 >= 로 쓴 구현에 돌린 결과")
    for title, suite in [
        ("동등 분할 4건", EQUIVALENCE_SUITE),
        ("분류 트리 6건", CLASSIFICATION_TREE_SUITE),
        ("분류 트리 6건 + 경계값 4건", CLASSIFICATION_TREE_SUITE + BOUNDARY_SUITE),
    ]:
        failed = run_suite(defect, suite)
        verdict = "검출" if failed else "통과(놓침)"
        print(f"  {title:<26} {verdict}")
        for case_id, raw_input, expected, actual in failed:
            print(f"    {case_id} 입력 {raw_input!r} 기대 {expected} 실제 {actual}")


if __name__ == "__main__":
    main()
