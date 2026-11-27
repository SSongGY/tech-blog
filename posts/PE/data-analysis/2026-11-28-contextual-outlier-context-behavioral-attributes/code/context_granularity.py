"""맥락을 얼마나 잘게 나누느냐에 따라 맥락 아웃라이어 검출 결과가 어떻게 달라지는지 계산한다.

데이터는 가상이다. 시간대별 요청 수 8주치(56일 x 24시간 = 1,344점)이고,
맥락 속성은 (시각, 요일), 행동 속성은 요청 수다.
검출기는 맥락마다 수정 Z 점수(중앙값·MAD)를 계산해 |Z| > 3.5 를 아웃라이어로 본다.
"""

import math
import random
import statistics
import sys

DAYS = 56
NOISE_SD = 5.0
THRESHOLD = 3.5  # Iglewicz-Hoaglin 수정 Z 점수 임계값 (NIST e-Handbook 1.3.5.17)
WEEKEND_FACTOR = 0.7
PLANTED = (20, 3, 120.0)  # 20일차(수요일) 03시에 낮 수준 값을 심는다


def base_level(hour, day_of_week):
    # 03시에 30, 15시에 180 이 되는 하루 곡선. 주말은 평일의 70%
    level = 105 - 75 * math.cos(2 * math.pi * (hour - 3) / 24)
    return level * (WEEKEND_FACTOR if day_of_week >= 5 else 1.0)


def build_series(seed, plant):
    rng = random.Random(seed)
    rows = []
    for day in range(DAYS):
        dow = day % 7  # 0=월 ... 6=일
        for hour in range(24):
            value = base_level(hour, dow) + rng.gauss(0, NOISE_SD)
            rows.append({"day": day, "dow": dow, "hour": hour, "value": value})
    if plant:
        day, hour, value = PLANTED
        rows[day * 24 + hour]["value"] = value
    return rows


# 맥락 정의 5가지. 키 함수가 같은 값을 돌려주는 행끼리 비교한다
LEVELS = [
    ("L0 맥락 없음(전역)", lambda r: 0),
    ("L1 시각", lambda r: r["hour"]),
    ("L2 시각 x 평일/주말", lambda r: (r["hour"], r["dow"] >= 5)),
    ("L3 시각 x 요일", lambda r: (r["hour"], r["dow"])),
    ("L4 시각 x 요일 x 전후 4주", lambda r: (r["hour"], r["dow"], r["day"] < 28)),
]


def modified_z(values):
    median = statistics.median(values)
    mad = statistics.median(abs(v - median) for v in values)
    if mad == 0:
        return [0.0 for _ in values]
    return [0.6745 * (v - median) / mad for v in values]


def detect(rows, key):
    groups = {}
    for index, row in enumerate(rows):
        groups.setdefault(key(row), []).append(index)
    scores = [0.0] * len(rows)
    for indexes in groups.values():
        for index, z in zip(indexes, modified_z([rows[i]["value"] for i in indexes])):
            scores[index] = z
    sizes = [len(v) for v in groups.values()]
    return scores, len(groups), min(sizes), max(sizes)


def single_run():
    rows = build_series(seed=7, plant=True)
    planted_index = PLANTED[0] * 24 + PLANTED[1]
    values = [r["value"] for r in rows]
    print("[데이터] 56일 x 24시간 = %d점, 노이즈 표준편차 %.0f" % (len(rows), NOISE_SD))
    print("  전체 최솟값 %.1f / 중앙값 %.1f / 최댓값 %.1f" % (min(values), statistics.median(values), max(values)))
    night = [r["value"] for r in rows if r["hour"] == 3 and r["dow"] < 5 and r["day"] != PLANTED[0]]
    print("  평일 03시(심은 점 제외) %d개: 중앙값 %.1f, 최댓값 %.1f" % (len(night), statistics.median(night), max(night)))
    print("  심은 맥락 아웃라이어: %d일차 %02d시 값 %.1f" % PLANTED)
    print()
    print("[한 번 실행 — seed 7, 심은 점 1개]")
    print("  %-26s %6s %8s %10s %10s" % ("맥락 정의", "맥락수", "표본크기", "심은점 Z", "그 외 검출"))
    for name, key in LEVELS:
        scores, count, smallest, largest = detect(rows, key)
        others = sum(1 for i, z in enumerate(scores) if abs(z) > THRESHOLD and i != planted_index)
        size = str(smallest) if smallest == largest else "%d~%d" % (smallest, largest)
        print("  %-26s %6d %8s %+10.2f %10d" % (name, count, size, scores[planted_index], others))


def repeated_runs(trials):
    print()
    print("[반복 실행 — seed 1~%d, 심은 점 없음: 검출된 것은 전부 오탐]" % trials)
    print("  %-26s %12s %14s" % ("맥락 정의", "평균 오탐 수", "오탐률(1,344점 중)"))
    totals = {name: 0 for name, _ in LEVELS}
    for seed in range(1, trials + 1):
        rows = build_series(seed=seed, plant=False)
        for name, key in LEVELS:
            scores, _, _, _ = detect(rows, key)
            totals[name] += sum(1 for z in scores if abs(z) > THRESHOLD)
    for name, _ in LEVELS:
        mean = totals[name] / trials
        print("  %-26s %12.2f %13.2f%%" % (name, mean, 100 * mean / (DAYS * 24)))


if __name__ == "__main__":
    print("Python %s" % sys.version.split()[0])
    single_run()
    repeated_runs(200)
