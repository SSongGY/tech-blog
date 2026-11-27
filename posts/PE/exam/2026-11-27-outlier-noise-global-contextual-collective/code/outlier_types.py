"""아웃라이어의 세 유형(전역·맥락·군집)과 노이즈를 한 시계열에 넣고,
검출 기준을 바꿔 가며 무엇이 잡히고 무엇이 빠지는지 확인한다.

데이터는 가상이다. 시간대별 API 요청 수(14일 x 24시간)를 만들고 세 가지를 심는다.
  - 전역: 어느 시간대 기준으로도 나올 수 없는 값 한 점
  - 맥락: 낮에는 흔하지만 새벽 3시에는 나올 수 없는 값 한 점
  - 군집: 수집기가 멈춰 직전 값을 6시간 동안 되풀이한 구간
"""

import platform
import random
import statistics

DAYS = 56
# 시간대별 기대 요청 수. 10~17시를 평탄하게 둔 것은 군집 아웃라이어의 개별 값이
# 맥락 기준으로도 정상 범위에 들도록 하기 위해서다.
HOURLY_PROFILE = [
    30, 30, 30, 30, 30, 30, 30,          # 00~06시
    70, 110, 150,                        # 07~09시
    180, 180, 180, 180, 180, 180, 180, 180,  # 10~17시
    150, 120, 90, 60, 45, 35,            # 18~23시
]
NOISE_SIGMA = 5.0
Z_THRESHOLD = 3.5      # NIST/SEMATECH e-Handbook 수정 Z 점수 기준
STUCK_WINDOW = 6       # 군집 검출 창 길이(시간)
STUCK_STD_LIMIT = 0.1  # 노이즈가 섞인 정상 구간에서는 나올 수 없는 수준. 사실상 같은 값의 반복

GLOBAL_AT = (3, 14)       # 4일차 14시
CONTEXTUAL_AT = (5, 3)    # 6일차 03시
COLLECTIVE_DAY = 9        # 10일차
COLLECTIVE_HOURS = range(11, 17)  # 11~16시, 6시간


def build_series(seed=20261127):
    rng = random.Random(seed)
    series = []
    for day in range(DAYS):
        for hour in range(24):
            # 노이즈: 관심 대상이 아닌 무작위 변동. 모든 점에 섞인다
            value = HOURLY_PROFILE[hour] + rng.gauss(0, NOISE_SIGMA)
            series.append([day, hour, round(value, 1)])
    index = {(d, h): i for i, (d, h, _) in enumerate(series)}

    series[index[GLOBAL_AT]][2] = 600.0
    series[index[CONTEXTUAL_AT]][2] = 175.0
    # 수집기가 10시 값을 마지막으로 멈춰 같은 값을 계속 기록한 상황
    stuck_value = series[index[(COLLECTIVE_DAY, 10)]][2]
    for hour in COLLECTIVE_HOURS:
        series[index[(COLLECTIVE_DAY, hour)]][2] = stuck_value
    return series


def modified_z(values):
    """중앙값과 MAD 로 계산한다. 평균·표준편차는 아웃라이어에 이미 끌려가 있다."""
    med = statistics.median(values)
    mad = statistics.median(abs(v - med) for v in values)
    return [0.6745 * (v - med) / mad for v in values], med, mad


def detect_global(series):
    values = [v for _, _, v in series]
    scores, med, mad = modified_z(values)
    hits = [(series[i], z) for i, z in enumerate(scores) if abs(z) > Z_THRESHOLD]
    return hits, med, mad


def detect_contextual(series):
    """맥락 속성(시간대)으로 묶은 뒤, 행동 속성(요청 수)을 그 묶음 안에서만 비교한다."""
    hits = []
    for hour in range(24):
        group = [row for row in series if row[1] == hour]
        scores, _, _ = modified_z([v for _, _, v in group])
        hits += [(row, z) for row, z in zip(group, scores) if abs(z) > Z_THRESHOLD]
    return sorted(hits, key=lambda h: (h[0][0], h[0][1]))


def detect_collective(series):
    """점 하나가 아니라 이어진 구간의 성질(변동이 사라짐)을 본다."""
    values = [v for _, _, v in series]
    flagged = set()
    for start in range(len(values) - STUCK_WINDOW + 1):
        window = values[start:start + STUCK_WINDOW]
        if statistics.pstdev(window) < STUCK_STD_LIMIT:
            flagged.update(range(start, start + STUCK_WINDOW))
    return [series[i] for i in sorted(flagged)]


def median_filter(series, width=3):
    """흔한 노이즈 제거 방식. 이웃 3점의 중앙값으로 바꾼다."""
    values = [v for _, _, v in series]
    half = width // 2
    smoothed = []
    for i in range(len(values)):
        lo, hi = max(0, i - half), min(len(values), i + half + 1)
        smoothed.append([series[i][0], series[i][1], statistics.median(values[lo:hi])])
    return smoothed


PLANTED = {
    GLOBAL_AT: "심은 전역",
    CONTEXTUAL_AT: "심은 맥락",
    (COLLECTIVE_DAY, 10): "멈추기 직전 실측",
    **{(COLLECTIVE_DAY, h): "심은 군집" for h in COLLECTIVE_HOURS},
}


def label(row):
    day, hour, value = row
    tag = PLANTED.get((day, hour), "노이즈")
    return f"{day + 1:>2}일차 {hour:02d}시  값={value:>6.1f}  [{tag}]"


def runs(rows):
    """연속된 시각끼리 묶는다. 군집 아웃라이어는 점이 아니라 구간으로 보고한다."""
    groups = []
    for row in rows:
        pos = row[0] * 24 + row[1]
        if groups and pos == groups[-1][-1][0] * 24 + groups[-1][-1][1] + 1:
            groups[-1].append(row)
        else:
            groups.append([row])
    return groups


def report(title, series, raw=None):
    print(f"\n[{title}]")
    hits, med, mad = detect_global(series)
    print(f"  전역 기준 (전체 중앙값={med:.1f}, MAD={mad:.1f}): {len(hits)}건")
    for row, z in hits:
        print(f"    {label(row)}  수정Z={z:+.2f}")
    ctx = detect_contextual(series)
    print(f"  맥락 기준 (시간대별 수정 Z): {len(ctx)}건")
    for row, z in ctx:
        print(f"    {label(row)}  수정Z={z:+.2f}")
    col = detect_collective(series)
    groups = runs(col)
    print(f"  군집 기준 ({STUCK_WINDOW}시간 창 표준편차 < {STUCK_STD_LIMIT}): "
          f"{len(groups)}구간 {len(col)}점")
    for group in groups:
        print(f"    {label(group[0])}  ~  {group[-1][1]:02d}시  ({len(group)}점)")
        if raw is not None:
            # 필터를 거치기 전 값과 나란히 놓아야 구간이 원래 있던 것인지 필터가 만든 것인지 보인다
            start = group[0][0] * 24 + group[0][1]
            before = " ".join(f"{raw[i][2]:.1f}" for i in range(start, start + len(group)))
            after = " ".join(f"{row[2]:.1f}" for row in group)
            print(f"      필터 전: {before}")
            print(f"      필터 후: {after}")


def main():
    print(f"Python {platform.python_version()}")
    series = build_series()
    print(f"\n데이터: {DAYS}일 x 24시간 = {len(series)}점, 노이즈 표준편차 {NOISE_SIGMA}")
    print("시간대별 기대값:", " ".join(str(v) for v in HOURLY_PROFILE))

    print("\n심은 아웃라이어")
    index = {(d, h): i for i, (d, h, _) in enumerate(series)}
    for name, key in (("전역", GLOBAL_AT), ("맥락", CONTEXTUAL_AT)):
        i = index[key]
        around = "  ".join(f"{series[j][1]:02d}시={series[j][2]:.1f}" for j in range(i - 2, i + 3))
        print(f"  {name}: {around}")
    start = index[(COLLECTIVE_DAY, 9)]
    around = "  ".join(f"{series[j][1]:02d}시={series[j][2]:.1f}" for j in range(start, start + 9))
    print(f"  군집: {around}")

    hour3 = [v for d, h, v in series if h == 3 and (d, h) != CONTEXTUAL_AT]
    print(f"\n맥락 아웃라이어 175.0 은 전체 분포 안에 있는가")
    print(f"  03시 나머지 {len(hour3)}일: 중앙값={statistics.median(hour3):.1f}, "
          f"최댓값={max(hour3):.1f}")
    print(f"  10~17시 중앙값={statistics.median(v for _, h, v in series if 10 <= h <= 17):.1f}, "
          f"전체 최솟값={min(v for *_, v in series):.1f}")

    # 노이즈의 크기: 시간대 기대값을 뺀 잔차. 심은 점은 뺀다
    planted = {index[GLOBAL_AT], index[CONTEXTUAL_AT]}
    planted |= {index[(COLLECTIVE_DAY, h)] for h in COLLECTIVE_HOURS}
    residuals = [v - HOURLY_PROFILE[h] for i, (_, h, v) in enumerate(series) if i not in planted]
    print(f"\n노이즈 잔차 {len(residuals)}점: 평균={statistics.mean(residuals):+.2f}, "
          f"표준편차={statistics.stdev(residuals):.2f}, "
          f"최대 절댓값={max(abs(r) for r in residuals):.2f}")

    report("원본에 검출 적용", series)
    report("노이즈 제거(이웃 3점 중앙값 필터) 후 검출 적용", median_filter(series), raw=series)


if __name__ == "__main__":
    main()
