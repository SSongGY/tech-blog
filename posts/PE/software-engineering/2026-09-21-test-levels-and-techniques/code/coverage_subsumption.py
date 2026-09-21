"""문장 커버리지 100%가 분기 커버리지 100%를 보장하지 않음을 실제 추적으로 계산한다.

측정 방식
  - 문장 커버리지: sys.settrace의 line 이벤트로 실행된 실행문 줄을 모은다.
  - 분기 커버리지: 판단문 줄 다음에 기록된 줄이 바로 아래 줄이면 참 분기,
    아니면 거짓 분기로 센다. 손으로 표시하지 않고 추적 기록에서 끌어낸다.
"""

import sys
from pathlib import Path

# 측정 대상. 판단문 두 개, 실행문 네 개.
SOURCE = '''def shipping_fee(weight_kg, is_member):
    fee = 3000
    if weight_kg > 10:
        fee = fee + 2000
    if is_member:
        fee = fee - 1000
    return fee
'''

TARGET_PATH = Path(__file__).with_name("_shipping_fee.py")
STATEMENT_LINES = (2, 3, 4, 5, 6, 7)   # def 줄(1)은 실행문에서 제외한다
DECISION_LINES = (3, 5)                # if 가 있는 줄


def trace_lines(func, cases):
    """각 테스트를 돌리며 대상 함수 안에서 밟은 줄 번호를 순서대로 모은다."""
    visited = set()
    branches = set()

    for args in cases:
        path = []

        def tracer(frame, event, arg):
            if frame.f_code is not func.__code__:
                return None
            if event == "line":
                path.append(frame.f_lineno)
            return tracer

        sys.settrace(tracer)
        try:
            func(*args)
        finally:
            sys.settrace(None)

        visited.update(path)
        for i, line in enumerate(path[:-1]):
            if line in DECISION_LINES:
                # 판단문 바로 아래 줄로 갔으면 참, 건너뛰었으면 거짓.
                branches.add((line, path[i + 1] == line + 1))

    return visited, branches


def percent(covered, total):
    return f"{covered}/{total} = {covered / total * 100:.0f}%"


def main():
    TARGET_PATH.write_text(SOURCE, encoding="utf-8")
    namespace = {}
    exec(compile(SOURCE, str(TARGET_PATH), "exec"), namespace)
    shipping_fee = namespace["shipping_fee"]

    suites = {
        "테스트 집합 A — 한 건": [(12, True)],
        "테스트 집합 B — 두 건": [(12, True), (5, False)],
    }

    total_branches = len(DECISION_LINES) * 2
    for label, cases in suites.items():
        visited, branches = trace_lines(shipping_fee, cases)
        print(f"\n{label}  입력 {cases}")
        print(f"  문장 커버리지: {percent(len(visited & set(STATEMENT_LINES)), len(STATEMENT_LINES))}")
        print(f"  분기 커버리지: {percent(len(branches), total_branches)}")
        for line in DECISION_LINES:
            taken = sorted(outcome for (dec, outcome) in branches if dec == line)
            print(f"    {line}번 줄 판단문이 밟은 결과: {taken}")

    TARGET_PATH.unlink()


if __name__ == "__main__":
    main()
