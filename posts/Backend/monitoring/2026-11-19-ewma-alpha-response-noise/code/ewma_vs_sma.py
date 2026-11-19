"""응답 시간 계열에서 단순 이동평균(SMA)과 지수가중 이동평균(EWMA)을 나란히 잰다.

1) 정상 구간의 흔들림 — 측정 표준편차를 이론값 sigma*sqrt(a/(2-a)), sigma/sqrt(N) 과 비교
2) 계단 변화에 반응하는 속도 — 잡음 없는 계단에서 50%·90%·95% 도달 표본 수
3) alpha 를 바꿔 가며 — 흔들림, 반응 속도, 임계값 오경보 수
4) 초깃값 — 0 / 첫 표본 / 처음 5개 평균 으로 시작했을 때 편향이 사라지는 속도
5) 가중치 — EWMA 가중치의 평균 나이와 합, SMA 와 같아지는 N
"""
import math
import random
import statistics
from collections import deque

SEED = 20261119
BASE_MS = 100.0        # 정상 응답 시간 평균
NOISE_MS = 20.0        # 표본 하나의 표준편차
STEP_MS = 30.0         # 계단 변화 크기 (100 -> 130)
STEP_AT = 2000         # 이 표본부터 느려진다
SAMPLE_COUNT = 4000
ALARM_MS = 110.0       # 정상 평균 + 2*sigma/sqrt(19) 근처의 경보 임계값


def make_latency_series(seed):
    rng = random.Random(seed)
    return [
        rng.gauss(BASE_MS + (STEP_MS if i >= STEP_AT else 0.0), NOISE_MS)
        for i in range(SAMPLE_COUNT)
    ]


def ewma(values, alpha, initial):
    smoothed = []
    current = initial
    for value in values:
        current = alpha * value + (1 - alpha) * current
        smoothed.append(current)
    return smoothed


def sma(values, window):
    buffer = deque(maxlen=window)
    total = 0.0
    smoothed = []
    for value in values:
        if len(buffer) == window:
            total -= buffer[0]
        buffer.append(value)
        total += value
        smoothed.append(total / len(buffer))
    return smoothed


def samples_to_reach(smoothed, start, target):
    for i in range(start, len(smoothed)):
        if smoothed[i] >= target:
            return i - start + 1
    return None


def step_response(smoother, **kwargs):
    """잡음 없는 계단(0 -> 1)에 대한 반응. 몇 번째 표본에서 50·90·95% 에 닿는가."""
    step = [0.0] * 200 + [1.0] * 200
    out = smoother(step, **kwargs)
    return tuple(samples_to_reach(out, 200, level) for level in (0.5, 0.9, 0.95))


def false_alarms(smoothed):
    """계단 전 정상 구간(웜업 200개 제외)에서 임계값을 넘은 표본 수."""
    return sum(1 for value in smoothed[200:STEP_AT] if value > ALARM_MS)


def main():
    series = make_latency_series(SEED)
    normal = series[200:STEP_AT]
    print(f"seed={SEED}  표본 {SAMPLE_COUNT}개, {STEP_AT}번째부터 {BASE_MS}->{BASE_MS + STEP_MS}ms")
    print(f"원 계열 정상 구간 평균 {statistics.fmean(normal):.3f}  표준편차 {statistics.stdev(normal):.3f}")

    print("\n[1] 같은 '유효 창' N=19, alpha=2/(N+1)=0.1 의 흔들림 (정상 구간 표준편차)")
    sma_out = sma(series, 19)
    ewma_out = ewma(series, 0.1, initial=series[0])
    print(f"    SMA  N=19       측정 {statistics.stdev(sma_out[200:STEP_AT]):.3f}"
          f"  이론 sigma/sqrt(N)        {NOISE_MS / math.sqrt(19):.3f}")
    print(f"    EWMA alpha=0.1  측정 {statistics.stdev(ewma_out[200:STEP_AT]):.3f}"
          f"  이론 sigma*sqrt(a/(2-a)) {NOISE_MS * math.sqrt(0.1 / 1.9):.3f}")

    # 평활한 값은 앞뒤가 서로 닮아(자기상관) 1800개라도 독립 표본은 100개 남짓이다.
    # 시드 하나의 표준편차는 그만큼 흔들리므로 시드 100개의 분산을 평균 내 본다
    sma_var, ewma_var = [], []
    for k in range(100):
        other = make_latency_series(SEED + 1 + k)
        sma_var.append(statistics.variance(sma(other, 19)[200:STEP_AT]))
        ewma_var.append(statistics.variance(ewma(other, 0.1, other[0])[200:STEP_AT]))
    print(f"    시드 100개 평균 — SMA sqrt(평균 분산) {math.sqrt(statistics.fmean(sma_var)):.3f}"
          f"  EWMA {math.sqrt(statistics.fmean(ewma_var)):.3f}")
    print(f"    시드별 SMA 표준편차 범위 {math.sqrt(min(sma_var)):.3f} ~ {math.sqrt(max(sma_var)):.3f}")

    print("\n[2] 잡음 없는 계단 0->1 에 50%·90%·95% 닿는 표본 수")
    print(f"    SMA  N=19       {step_response(sma, window=19)}")
    print(f"    EWMA alpha=0.1  {step_response(ewma, alpha=0.1, initial=0.0)}")
    for level in (0.5, 0.9, 0.95):
        print(f"    EWMA 이론 ceil(ln(1-{level})/ln(0.9)) = "
              f"{math.ceil(math.log(1 - level) / math.log(0.9))}")

    print("\n[3] alpha 를 바꿔 가며 — 흔들림 / 계단 반응(50%,90%,95%) / 오경보 / 첫 경보까지")
    print("    alpha   유효N  표준편차(측정/이론)   계단 반응        오경보  계단 후 첫 경보")
    for alpha in (0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0):
        out = ewma(series, alpha, initial=series[0])
        measured = statistics.stdev(out[200:STEP_AT])
        theory = NOISE_MS * math.sqrt(alpha / (2 - alpha))
        first = samples_to_reach(out, STEP_AT, ALARM_MS)
        print(f"    {alpha:<6}  {2 / alpha - 1:>5.0f}  {measured:7.3f} / {theory:7.3f}"
              f"   {str(step_response(ewma, alpha=alpha, initial=0.0)):<15}"
              f"  {false_alarms(out):>5}  {first}")

    print("\n[4] 초깃값 — alpha=0.05 에서 |EWMA - 100| 이 처음 2ms 안에 드는 표본 번호")
    for label, initial in (
        ("0 으로 시작", 0.0),
        ("첫 표본", series[0]),
        ("처음 5개 평균", statistics.fmean(series[:5])),
    ):
        out = ewma(series, 0.05, initial)
        first_close = next(i for i, v in enumerate(out) if abs(v - BASE_MS) < 2.0)
        print(f"    {label:<12} 초깃값 {initial:8.3f}  -> {first_close + 1}번째, "
              f"10번째 값 {out[9]:7.3f}")
    corrected = [
        v / (1 - 0.95 ** (i + 1)) for i, v in enumerate(ewma(series, 0.05, 0.0))
    ]
    print(f"    0 으로 시작 + 1-(1-a)^t 로 나눈 보정  10번째 값 {corrected[9]:7.3f}")

    print("\n[5] 가중치 — k 표본 전 값의 가중치 a(1-a)^k")
    for alpha in (0.1, 0.05):
        weights = [alpha * (1 - alpha) ** k for k in range(10_000)]
        mean_age = sum(k * w for k, w in enumerate(weights))
        recent = sum(weights[: round(2 / alpha - 1)])
        print(f"    alpha={alpha}: 가중치 합 {sum(weights):.6f}  평균 나이 {mean_age:.3f}"
              f" (=(1-a)/a {(1 - alpha) / alpha:.3f})  최근 {round(2 / alpha - 1)}개 몫 {recent:.4f}")
    print(f"    SMA N=19 평균 나이 (N-1)/2 = {(19 - 1) / 2}")


if __name__ == "__main__":
    main()
