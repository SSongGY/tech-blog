"""드리프트의 발생원 두 가지를 같은 모델에 각각 먹여 결과를 비교한다.

Source I  : 입력 분포 P(X) 만 바뀌고 P(y|X) 는 그대로 — 데이터 드리프트
Source II : P(y|X) 가 바뀌고 P(X) 는 그대로 — 개념 드리프트

입력 분포 감시(PSI)와 정확도 감시가 각각 어느 쪽을 잡고 어느 쪽을 놓치는지
숫자로 확인하는 것이 목적이다.
"""

import math
import random

SEED = 20261015
SAMPLE_SIZE = 20000
BIN_COUNT = 10

# 기준 시점 t 의 참 개념. 모델은 이 경계를 그대로 학습했다고 둔다.
CONCEPT_T = (0.6, 0.4)
# 시점 t+1 에서 바뀐 참 개념 (Source II).
CONCEPT_T1 = (0.4, -0.6)


def sample(rng: random.Random, mean_x1: float, mean_x2: float) -> list[tuple[float, float]]:
    return [
        (rng.gauss(mean_x1, 1.0), rng.gauss(mean_x2, 1.0)) for _ in range(SAMPLE_SIZE)
    ]


def label(point: tuple[float, float], concept: tuple[float, float]) -> int:
    w1, w2 = concept
    return 1 if w1 * point[0] + w2 * point[1] > 0 else 0


def predict(point: tuple[float, float]) -> int:
    """배포된 모델. 시점 t 의 경계를 그대로 쓴다."""
    return label(point, CONCEPT_T)


def accuracy(points: list[tuple[float, float]], concept: tuple[float, float]) -> float:
    hit = sum(1 for p in points if predict(p) == label(p, concept))
    return hit / len(points)


def true_positive_rate(points: list[tuple[float, float]], concept: tuple[float, float]) -> float:
    """참 라벨의 양성 비율. 라벨이 도착해야 알 수 있는 값이다."""
    return sum(label(p, concept) for p in points) / len(points)


def predicted_positive_rate(points: list[tuple[float, float]]) -> float:
    """모델이 내놓은 양성 비율. 라벨 없이도 바로 잴 수 있다."""
    return sum(predict(p) for p in points) / len(points)


def bin_edges(values: list[float]) -> list[float]:
    """기준 표본의 분위수로 경계를 잡는다. 기준 쪽은 구간마다 10%씩 들어간다."""
    ordered = sorted(values)
    step = len(ordered) / BIN_COUNT
    return [ordered[int(i * step)] for i in range(1, BIN_COUNT)]


def share(values: list[float], edges: list[float]) -> list[float]:
    counts = [0] * (len(edges) + 1)
    for v in values:
        index = 0
        while index < len(edges) and v >= edges[index]:
            index += 1
        counts[index] += 1
    return [c / len(values) for c in counts]


def psi(reference: list[float], current: list[float]) -> float:
    """PSI = Σ (현재비율 - 기준비율) × ln(현재비율 / 기준비율)."""
    edges = bin_edges(reference)
    ref = share(reference, edges)
    cur = share(current, edges)
    total = 0.0
    for r, c in zip(ref, cur):
        # 빈 구간이 생기면 로그가 발산하므로 아주 작은 값으로 받친다.
        r = max(r, 1e-6)
        c = max(c, 1e-6)
        total += (c - r) * math.log(c / r)
    return total


def report(name: str, base: list[tuple[float, float]], now: list[tuple[float, float]],
           concept: tuple[float, float]) -> None:
    psi_x1 = psi([p[0] for p in base], [p[0] for p in now])
    psi_x2 = psi([p[1] for p in base], [p[1] for p in now])
    print(f"[{name}]")
    print(f"  PSI(x1)        {psi_x1:7.4f}")
    print(f"  PSI(x2)        {psi_x2:7.4f}")
    print(f"  예측 양성비율  {predicted_positive_rate(now):7.4f}   (라벨 없이 잴 수 있다)")
    print(f"  참 양성비율    {true_positive_rate(now, concept):7.4f}   (라벨이 와야 안다)")
    print(f"  모델 정확도    {accuracy(now, concept):7.4f}   (라벨이 와야 안다)")
    print()


def main() -> None:
    rng = random.Random(SEED)
    print(f"표본 {SAMPLE_SIZE}건 · 구간 {BIN_COUNT}개 · 시드 {SEED}")
    print(f"시점 t 의 참 경계      {CONCEPT_T[0]}·x1 + {CONCEPT_T[1]}·x2 > 0")
    print(f"Source II 의 참 경계   {CONCEPT_T1[0]}·x1 + {CONCEPT_T1[1]}·x2 > 0")
    print()

    base = sample(rng, 0.0, 0.0)
    report("기준 시점 t", base, base, CONCEPT_T)

    # Source I — x1 의 평균만 옮긴다. 참 경계는 그대로다.
    shifted = sample(rng, 1.2, 0.0)
    report("Source I · 입력 분포만 이동", base, shifted, CONCEPT_T)

    # Source II — 입력은 기준과 같은 분포에서 새로 뽑고, 참 경계만 바꾼다.
    same_input = sample(rng, 0.0, 0.0)
    report("Source II · 참 경계만 변경", base, same_input, CONCEPT_T1)

    # Source III — 둘이 겹친 경우.
    both = sample(rng, 1.2, 0.0)
    report("Source III · 둘이 함께", base, both, CONCEPT_T1)


if __name__ == "__main__":
    main()
