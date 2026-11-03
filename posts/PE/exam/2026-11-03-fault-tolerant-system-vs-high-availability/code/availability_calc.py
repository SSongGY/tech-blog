"""가용성 답안에 쓴 수식을 직접 계산해 검산한다.

[1] 가용성 = MTBF / (MTBF + MTTR) — 같은 MTBF에서 MTTR 만 줄이면 어디까지 오르는가
[2] 가용성 수준(나인)별 연간 허용 중단 시간
[3] 직렬 의존(곱)과 병렬 중복(1 - 실패확률의 곱)
[4] 삼중 모듈 중복(TMR)의 다수결 신뢰도 3R^2 - 2R^3 — 8가지 경우를 셈으로 확인

외부 의존성은 없다.
"""

import itertools
import platform
import sys

HOURS_PER_YEAR = 365 * 24


def availability(mtbf_hours: float, mttr_hours: float) -> float:
    return mtbf_hours / (mtbf_hours + mttr_hours)


def downtime_text(minutes: float) -> str:
    days, rem = divmod(minutes, 24 * 60)
    hours, mins = divmod(rem, 60)
    parts = []
    if days >= 1:
        parts.append(f"{int(days)}일")
    if hours >= 1:
        parts.append(f"{int(hours)}시간")
    parts.append(f"{int(mins)}분")
    return " ".join(parts)


def tmr_by_enumeration(r: float) -> float:
    # 모듈 3개가 각각 독립으로 정상(확률 r)·고장(1-r). 2개 이상 정상이면 다수결이 맞는다.
    total = 0.0
    for state in itertools.product([True, False], repeat=3):
        p = 1.0
        for ok in state:
            p *= r if ok else (1 - r)
        if sum(state) >= 2:
            total += p
    return total


def main() -> None:
    print(f"Python {platform.python_version()} / {platform.system()}")

    print("\n[1] 가용성 = MTBF / (MTBF + MTTR)")
    mtbf = 150 * 24  # 150일. AWS Reliability Pillar 의 예제 값
    print(f"MTBF {mtbf}시간(150일) 으로 고정하고 MTTR 만 바꾼다")
    for label, mttr in [("1시간 (사람이 복구)", 1.0),
                        ("1분 (클러스터 장애 전환)", 1 / 60),
                        ("1초 (프로세스 쌍 인계)", 1 / 3600),
                        ("0 (락스텝 — 실패가 지연으로도 안 보임)", 0.0)]:
        print(f"  MTTR {label:<34} A = {availability(mtbf, mttr) * 100:.5f}%")

    print("\n[2] 가용성 수준별 연간 허용 중단 시간 (1년 = 365일 기준)")
    for nines in [0.99, 0.999, 0.9995, 0.9999, 0.99999]:
        minutes = HOURS_PER_YEAR * 60 * (1 - nines)
        print(f"  {nines * 100:>7.3f}%  →  {downtime_text(minutes):<16} ({minutes:.1f}분)")

    print("\n[3] 직렬 의존과 병렬 중복")
    a = 0.9999
    series = a ** 3
    print(f"  직렬: 99.99% 짜리 3개에 전부 의존  → {series * 100:.4f}%  (곱)")
    b = 0.999
    parallel = 1 - (1 - b) ** 2
    print(f"  병렬: 99.9% 짜리 2개 중 하나만 살면 됨 → {parallel * 100:.4f}%  (1 - 실패확률의 곱)")

    print("\n[4] TMR 다수결 신뢰도 — 식 3R^2 - 2R^3 과 8가지 경우의 합이 같은가")
    print(f"  {'R':>5}  {'식':>8}  {'열거':>8}  {'단일 대비':>8}")
    for r in [0.3, 0.5, 0.7, 0.9, 0.99]:
        formula = 3 * r ** 2 - 2 * r ** 3
        enum = tmr_by_enumeration(r)
        assert abs(formula - enum) < 1e-12
        mark = "유리" if formula > r else ("같음" if formula == r else "불리")
        print(f"  {r:>5.2f}  {formula:>8.5f}  {enum:>8.5f}  {mark:>6}")


if __name__ == "__main__":
    sys.exit(main())
