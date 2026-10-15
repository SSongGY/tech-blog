"""이상치와 편향이 분석 결과에 어떻게 다르게 나타나는지 숫자로 확인한다.

세 가지를 차례로 계산한다.
  1. 이상치 한 점이 요약통계를 얼마나 움직이는가 (평균 vs 중앙값, 표준편차 vs MAD)
  2. 표본 구성이 치우치면 집단별 결론과 전체 결론이 뒤집히는가 (심슨의 역설)
  3. 이상치를 일괄 제거하면 그 자체가 편향을 만드는가 (집단별 절삭률 차이)

검출 기준은 NIST/SEMATECH e-Handbook 의 것을 그대로 쓴다.
  - IQR 울타리: 안쪽 1.5*IQ, 바깥쪽 3*IQ (§7.1.6)
  - 수정 Z 점수: 0.6745*(x - 중앙값)/MAD, 절댓값 3.5 초과 시 이상치 후보 (§1.3.5.17)
"""

import platform
import statistics
import sys

# 가상 API 의 응답시간(ms) 20건. 마지막 한 건은 재시도 타임아웃이 섞여 들어간 값이다.
RESPONSE_MS = [
    182, 195, 201, 188, 210, 176, 199, 205, 191, 187,
    213, 178, 196, 203, 185, 208, 192, 180, 197, 4200,
]


def fences(values):
    """NIST e-Handbook §7.1.6 의 사분위 울타리를 돌려준다."""
    q1, _, q3 = statistics.quantiles(values, n=4, method="exclusive")
    iq = q3 - q1
    return q1, q3, iq, (q1 - 1.5 * iq, q3 + 1.5 * iq), (q1 - 3.0 * iq, q3 + 3.0 * iq)


def modified_z(values):
    """NIST e-Handbook §1.3.5.17 의 수정 Z 점수를 돌려준다."""
    med = statistics.median(values)
    mad = statistics.median([abs(v - med) for v in values])
    return [0.6745 * (v - med) / mad for v in values]


def summarize(label, values):
    med = statistics.median(values)
    mad = statistics.median([abs(v - med) for v in values])
    print(
        f"  {label:<12} n={len(values):>2}"
        f"  평균={statistics.mean(values):>8.2f}"
        f"  표준편차={statistics.stdev(values):>8.2f}"
        f"  중앙값={med:>7.2f}"
        f"  MAD={mad:>6.2f}"
    )


def part1_outlier_leverage():
    print("[1] 이상치 한 점이 요약통계를 움직이는 폭")
    print()
    summarize("전체", RESPONSE_MS)
    summarize("이상치 제외", RESPONSE_MS[:-1])
    print()

    q1, q3, iq, inner, outer = fences(RESPONSE_MS)
    print(f"  Q1={q1:.2f}  Q3={q3:.2f}  IQ={iq:.2f}")
    print(f"  안쪽 울타리 (1.5*IQ): [{inner[0]:.2f}, {inner[1]:.2f}]")
    print(f"  바깥쪽 울타리 (3*IQ): [{outer[0]:.2f}, {outer[1]:.2f}]")
    print()

    scores = modified_z(RESPONSE_MS)
    flagged = [(v, m) for v, m in zip(RESPONSE_MS, scores) if abs(m) > 3.5]
    print(f"  수정 Z 점수 절댓값 3.5 초과: {len(flagged)}건")
    for value, score in flagged:
        beyond = "바깥쪽" if value > outer[1] else "안쪽"
        print(f"    {value} ms  수정Z={score:.2f}  {beyond} 울타리 밖")
    print()


# 두 처리 모듈의 요청 처리 성공 건수. 요청 유형별로 쪼개 놓았다.
# 신규 모듈은 어려운 대형 요청을 주로 받았고, 기존 모듈은 쉬운 소형 요청을 주로 받았다.
ROUTING = {
    "신규 모듈": {"소형 요청": (81, 90), "대형 요청": (192, 310)},
    "기존 모듈": {"소형 요청": (234, 270), "대형 요청": (16, 30)},
}


def part2_selection_bias():
    print("[2] 표본 구성이 치우치면 집단별 결론과 전체 결론이 갈린다")
    print()
    print("  모듈        요청유형     성공/시도      성공률")
    for module, strata in ROUTING.items():
        total_ok = total_n = 0
        for kind, (ok, n) in strata.items():
            print(f"  {module:<10}  {kind:<9}  {ok:>4}/{n:<5}  {ok / n * 100:>9.1f}%")
            total_ok += ok
            total_n += n
        print(f"  {module:<10}  {'합계':<9}  {total_ok:>4}/{total_n:<5}"
              f"  {total_ok / total_n * 100:>9.1f}%")
    print()

    for kind in ("소형 요청", "대형 요청"):
        new_ok, new_n = ROUTING["신규 모듈"][kind]
        old_ok, old_n = ROUTING["기존 모듈"][kind]
        winner = "신규" if new_ok / new_n > old_ok / old_n else "기존"
        share = new_n / (new_n + old_n) * 100
        print(f"  {kind}: 우세={winner} 모듈, 이 유형에서 신규 모듈이 받은 비중 {share:.1f}%")

    new_rate = sum(o for o, _ in ROUTING["신규 모듈"].values()) / \
        sum(n for _, n in ROUTING["신규 모듈"].values())
    old_rate = sum(o for o, _ in ROUTING["기존 모듈"].values()) / \
        sum(n for _, n in ROUTING["기존 모듈"].values())
    print(f"  합계: 우세={'신규' if new_rate > old_rate else '기존'} 모듈")
    print()


# 두 고객군의 응답시간(ms). 대형 고객은 본래 느리고 분산도 크다.
SEGMENTS = {
    "소형 고객": [
        181, 190, 177, 195, 186, 202, 174, 188, 199, 183,
        192, 179, 205, 187, 196, 184, 191, 198, 175, 189,
    ],
    "대형 고객": [
        240, 288, 312, 265, 401, 355, 298, 274, 430, 336,
        259, 382, 303, 247, 368, 291, 455, 322, 276, 341,
    ],
}


def part3_trimming_creates_bias():
    print("[3] 전역 울타리로 이상치를 일괄 제거하면 그 자체가 편향이 된다")
    print()
    pooled = sorted(SEGMENTS["소형 고객"] + SEGMENTS["대형 고객"])
    _, _, _, inner, _ = fences(pooled)
    print(f"  두 고객군을 합쳐 계산한 안쪽 울타리: [{inner[0]:.2f}, {inner[1]:.2f}]")
    print("  -> 두 모집단이 섞이면서 IQ 가 부풀어, 전역 울타리에 걸리는 점이 없다(은폐).")
    print()

    print("  집단별로 울타리를 따로 계산하면:")
    for name, values in SEGMENTS.items():
        _, _, _, seg_inner, _ = fences(values)
        hit = [v for v in values if not seg_inner[0] <= v <= seg_inner[1]]
        print(f"    {name:<10} 울타리=[{seg_inner[0]:>7.2f}, {seg_inner[1]:>7.2f}]"
              f"  걸린 점 {len(hit)}건 {hit}")
    print("  -> 어느 기준으로도 이상치가 없다. 대형 고객의 긴 꼬리는 그 집단의 정상 범위다.")
    print()

    # 실무에서 흔한 관행: 전체 표본의 상위 5% 를 꼬리로 보고 잘라낸다.
    cutoff = statistics.quantiles(pooled, n=20, method="exclusive")[-1]
    print(f"  그런데도 전체 표본의 95 퍼센타일을 상한으로 두고 자르면 (상한 {cutoff:.2f} ms)")
    print("  고객군      원표본  절삭후  절삭률   평균(원)  평균(절삭후)   변화")
    for name, values in SEGMENTS.items():
        kept = [v for v in values if v <= cutoff]
        cut = (len(values) - len(kept)) / len(values) * 100
        before, after = statistics.mean(values), statistics.mean(kept)
        print(f"  {name:<10}  {len(values):>5}  {len(kept):>5}  {cut:>6.1f}%"
              f"  {before:>8.2f}  {after:>11.2f}  {after - before:>+7.2f}")
    print()


def main():
    print(f"환경: Python {platform.python_version()} on {platform.system()} "
          f"{platform.release()} ({sys.platform})")
    print("=" * 72)
    part1_outlier_leverage()
    print("=" * 72)
    part2_selection_bias()
    print("=" * 72)
    part3_trimming_creates_bias()


if __name__ == "__main__":
    main()
