"""신규성 탐지와 이상(아웃라이어) 탐지가 갈리는 지점을 1차원 데이터로 계산한다.

1) 깨끗한 학습 데이터로 정상 모델을 만든다 (신규성 탐지의 전제)
2) 같은 모델을 오염된 학습 데이터로 만들면 임곗값이 벌어져 놓친다
3) 강건 추정(중앙값·MAD)으로 오염을 견디게 한다 (아웃라이어 탐지 쪽의 대응)
4) 새 패턴이 계속 들어올 때 — 경보로 끝내는 모델과 정상 모델에 편입하는 모델
"""
import random
import statistics

K = 3.0                 # 임곗값: 중심에서 표준편차(또는 척도)의 몇 배
CONFIRM_COUNT = 30      # 신규 판정이 이만큼 쌓이고 서로 모여 있으면 새 정상으로 편입


class GaussianModel:
    """정상 데이터 한 덩어리를 평균·표준편차로 요약한다."""

    def __init__(self, center, scale):
        self.center = center
        self.scale = scale

    @classmethod
    def fit(cls, data):
        return cls(statistics.fmean(data), statistics.pstdev(data))

    @classmethod
    def fit_robust(cls, data):
        median = statistics.median(data)
        mad = statistics.median(abs(x - median) for x in data)
        return cls(median, 1.4826 * mad)   # 정규분포에서 MAD 를 표준편차 척도로 맞추는 상수

    def score(self, x):
        return abs(x - self.center) / self.scale


def normal_sample(rng, n, mu, sigma):
    return [rng.gauss(mu, sigma) for _ in range(n)]


def detect(models, x):
    """모든 정상 성분에서 K 배 넘게 떨어져 있으면 신규로 본다."""
    return min(m.score(x) for m in models) > K


def report_static(label, model, test_normal, test_novel):
    false_alarm = sum(detect([model], x) for x in test_normal)
    hit = sum(detect([model], x) for x in test_novel)
    print(f"  {label:<26} 중심 {model.center:7.2f}  척도 {model.scale:6.2f}"
          f"  임계 범위 {model.center - K * model.scale:7.2f}~{model.center + K * model.scale:7.2f}"
          f"  신규 검출 {hit}/{len(test_novel)}  오경보 {false_alarm}/{len(test_normal)}")


def run_stream(rng, incorporate):
    """t < 200 은 평균 100, t >= 200 부터는 평균 120 인 새 패턴이 정상으로 자리 잡는다."""
    models = [GaussianModel.fit(normal_sample(rng, 500, 100, 5))]
    pending = []
    alarms_per_block = []
    block_alarms = 0
    incorporated_at = None
    for t in range(600):
        mu = 100 if t < 200 else 120
        x = rng.gauss(mu, 5)
        if detect(models, x):
            block_alarms += 1
            if incorporate:
                pending.append(x)
                if (len(pending) >= CONFIRM_COUNT
                        and statistics.pstdev(pending[-CONFIRM_COUNT:]) < 2 * models[0].scale):
                    models.append(GaussianModel.fit(pending[-CONFIRM_COUNT:]))
                    incorporated_at = t
                    pending.clear()
        if t % 100 == 99:
            alarms_per_block.append(block_alarms)
            block_alarms = 0
    return alarms_per_block, incorporated_at, models


def main():
    rng = random.Random(20261128)
    clean_train = normal_sample(rng, 500, 100, 5)
    contaminated_train = clean_train + normal_sample(rng, 50, 130, 3)   # 학습 데이터의 약 9% 가 이상
    test_normal = normal_sample(rng, 200, 100, 5)
    test_novel = normal_sample(rng, 20, 122, 2)

    print("[1~3] 같은 시험 데이터(정상 200, 새 패턴 20)를 세 모델로 판정")
    report_static("1) 깨끗한 학습 + 평균·표준편차", GaussianModel.fit(clean_train), test_normal, test_novel)
    report_static("2) 오염된 학습 + 평균·표준편차", GaussianModel.fit(contaminated_train), test_normal, test_novel)
    report_static("3) 오염된 학습 + 중앙값·MAD", GaussianModel.fit_robust(contaminated_train), test_normal, test_novel)

    print("\n[4] 새 패턴이 t=200 부터 정상으로 자리 잡는 흐름 — 100건 단위 경보 수")
    for incorporate in (False, True):
        stream_rng = random.Random(7)
        blocks, at, models = run_stream(stream_rng, incorporate)
        label = "편입함 (신규성 탐지)" if incorporate else "경보로 끝냄"
        print(f"  {label:<20} {blocks}  합계 {sum(blocks)}")
        if incorporate:
            print(f"    편입 시점 t={at}, 정상 성분 {len(models)}개:",
                  ", ".join(f"중심 {m.center:.1f}" for m in models))


if __name__ == "__main__":
    main()
