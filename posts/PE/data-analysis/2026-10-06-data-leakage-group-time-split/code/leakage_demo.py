"""데이터 누수 세 갈래를 표준 라이브러리만으로 재현한다.

세 실험 모두 **특징과 정답 사이에 진짜 관계가 없거나 약하게** 만들었다.
그런데도 분할을 잘못하면 평가 점수가 높게 나온다 — 그 차이가 누수의 크기다.
난수 시드를 고정했으므로 돌릴 때마다 같은 값이 나온다.
"""
import math
import platform
import random
import sys
from statistics import mean

SEEDS = range(10)


def nearest_label(train, x):
    """1-최근접 이웃. train: (특징 벡터, 정답) 목록."""
    return min(train, key=lambda row: math.dist(row[0], x))[1]


def accuracy(train, test):
    return mean(1 if nearest_label(train, x) == y else 0 for x, y in test)


# ── 실험 1. 같은 환자의 기록이 학습과 평가에 갈라 들어간다 (묶음 누수) ─────────
PATIENTS, RECORDS_PER_PATIENT, DIM = 40, 5, 6


def make_patient_records(rng):
    """정답은 환자마다 동전 던지기다. 특징은 그 환자 고유값 + 작은 측정 잡음뿐이다."""
    rows = []
    for pid in range(PATIENTS):
        label = rng.randint(0, 1)
        signature = [rng.gauss(0, 1) for _ in range(DIM)]
        for _ in range(RECORDS_PER_PATIENT):
            rows.append((pid, [s + rng.gauss(0, 0.1) for s in signature], label))
    return rows


def experiment_group(seed):
    rng = random.Random(seed)
    rows = make_patient_records(rng)

    shuffled = rows[:]
    rng.shuffle(shuffled)
    cut = len(shuffled) * 4 // 5
    row_split = accuracy([(x, y) for _, x, y in shuffled[:cut]], [(x, y) for _, x, y in shuffled[cut:]])

    test_ids = set(rng.sample(range(PATIENTS), PATIENTS // 5))
    train = [(x, y) for pid, x, y in rows if pid not in test_ids]
    test = [(x, y) for pid, x, y in rows if pid in test_ids]
    group_split = accuracy(train, test)
    return row_split, group_split


# ── 실험 2. 분할 전에 전체 데이터로 특징을 고른다 (전처리 누수) ─────────────────
SAMPLES, FEATURES, KEEP, FOLDS = 50, 2000, 20, 5


def correlation(xs, ys):
    mx, my = mean(xs), mean(ys)
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    return sxy / math.sqrt(sxx * syy)


def top_features(X, y, idx):
    """idx 행만 보고 정답과 상관이 큰 특징 KEEP 개를 고른다."""
    ys = [y[i] for i in idx]
    scores = [(abs(correlation([X[i][j] for i in idx], ys)), j) for j in range(FEATURES)]
    return [j for _, j in sorted(scores, reverse=True)[:KEEP]]


def cv_accuracy(X, y, select_inside):
    folds = [list(range(k, SAMPLES, FOLDS)) for k in range(FOLDS)]
    chosen_once = None if select_inside else top_features(X, y, range(SAMPLES))
    scores = []
    for test_idx in folds:
        train_idx = [i for i in range(SAMPLES) if i not in test_idx]
        chosen = top_features(X, y, train_idx) if select_inside else chosen_once
        pick = lambda i: [X[i][j] for j in chosen]
        scores.append(accuracy([(pick(i), y[i]) for i in train_idx], [(pick(i), y[i]) for i in test_idx]))
    return mean(scores)


def experiment_feature_selection(seed):
    rng = random.Random(seed)
    X = [[rng.gauss(0, 1) for _ in range(FEATURES)] for _ in range(SAMPLES)]
    y = [i % 2 for i in range(SAMPLES)]  # 정답은 특징과 무관하다
    rng.shuffle(y)
    return cv_accuracy(X, y, select_inside=False), cv_accuracy(X, y, select_inside=True)


# ── 실험 3. 시계열을 무작위로 섞어 나눈다 (시간 누수) ──────────────────────────
STEPS = 500


def experiment_temporal(seed):
    """무작위 보행: 내일 값은 오늘 값 + 잡음. 미래를 예측할 정보는 오늘 값뿐이다."""
    rng = random.Random(seed)
    series = [0.0]
    for _ in range(STEPS - 1):
        series.append(series[-1] + rng.gauss(0, 1))

    def mae(train_t, test_t):
        # 시각이 가장 가까운 학습 시점의 값으로 예측한다. 그 시점이 미래일 수도 있다
        return mean(abs(series[min(train_t, key=lambda s: abs(s - t))] - series[t]) for t in test_t)

    times = list(range(STEPS))
    shuffled = times[:]
    rng.shuffle(shuffled)
    cut = STEPS * 4 // 5
    random_split = mae(shuffled[:cut], shuffled[cut:])
    time_split = mae(times[:cut], times[cut:])
    return random_split, time_split


def report(title, header, results):
    print(title)
    a = [r[0] for r in results]
    b = [r[1] for r in results]
    print(f"  {header[0]:<26} 평균 {mean(a):.3f}  (최소 {min(a):.3f} · 최대 {max(a):.3f})")
    print(f"  {header[1]:<26} 평균 {mean(b):.3f}  (최소 {min(b):.3f} · 최대 {max(b):.3f})")
    print()


def main():
    print(f"Python {platform.python_version()} ({sys.platform}) · 시드 {len(SEEDS)}개 평균")
    print()
    print(f"[데이터]")
    print(f"  실험1: 환자 {PATIENTS}명 × 기록 {RECORDS_PER_PATIENT}건, 특징 {DIM}개, 정답은 환자별 무작위")
    print(f"  실험2: 표본 {SAMPLES}개, 잡음 특징 {FEATURES}개 중 {KEEP}개 선택, {FOLDS}겹 교차검증, 정답 0/1 반반")
    print(f"  실험3: 무작위 보행 {STEPS}시점, 학습 80% / 평가 20%")
    print()
    report("[실험1] 1-최근접 이웃 정확도 — 기대값은 0.5",
           ("행 단위 무작위 분할", "환자(묶음) 단위 분할"),
           [experiment_group(s) for s in SEEDS])
    report("[실험2] 1-최근접 이웃 교차검증 정확도 — 기대값은 0.5",
           ("특징 선택을 분할 전에", "특징 선택을 폴드 안에서"),
           [experiment_feature_selection(s) for s in SEEDS])
    report("[실험3] 가까운 시점 값으로 예측한 평균절대오차 — 클수록 어렵다",
           ("시점을 섞어 분할", "앞 80% 학습 · 뒤 20% 평가"),
           [experiment_temporal(s) for s in SEEDS])


if __name__ == "__main__":
    main()
