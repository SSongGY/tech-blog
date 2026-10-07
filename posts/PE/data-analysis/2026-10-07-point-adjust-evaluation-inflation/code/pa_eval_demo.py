"""점 조정(point-adjust)이 시계열 이상 탐지 점수를 얼마나 부풀리는지 재현한다.

근거
- 점 조정의 정의: Xu et al., Donut (WWW 2018) §4.2
- 지연 k 안에서만 조정: Ren et al., SR-CNN (KDD 2019) §5.2
- PA%K: Kim et al., Towards a Rigorous Evaluation of TSAD (AAAI 2022) §3.1, §4.2 식(4)·PA%K 식
- 범위 기반 정밀도·재현율: Tatbul et al. (NeurIPS 2018) §4.1~4.2, α=0·γ=1·평탄 편향

표준 라이브러리만 쓴다. 난수 시드를 고정해 같은 출력이 나온다.
"""

import random
import sys

SEED = 7


def make_labels(length, seg_len, n_seg, rng):
    """겹치지 않는 이상 구간 n_seg개를 고르게 흩어 놓는다."""
    labels = [0] * length
    gap = length // n_seg
    segments = []
    for i in range(n_seg):
        # 구간이 칸 경계를 넘지 않도록 칸 안에서만 시작점을 고른다
        start = i * gap + rng.randrange(0, gap - seg_len)
        end = start + seg_len - 1
        segments.append((start, end))
        for t in range(start, end + 1):
            labels[t] = 1
    return labels, segments


def score_random(labels, rng):
    return [rng.random() for _ in labels]


def score_informative(labels, segments, rng):
    """이상 구간 전체에서 평균이 1.5 올라간 점수. 정상과 분포가 겹친다."""
    return [rng.gauss(1.5 if y else 0.0, 1.0) for y in labels]


def score_late(labels, segments, rng):
    """구간 뒤쪽 20%에서만 점수가 오른다. 늦게 알아채는 탐지기."""
    scores = [rng.gauss(0.0, 1.0) for _ in labels]
    for start, end in segments:
        tail = start + int((end - start + 1) * 0.8)
        for t in range(tail, end + 1):
            scores[t] = rng.gauss(3.0, 1.0)
    return scores


def f1_from(pred, labels):
    tp = sum(1 for p, y in zip(pred, labels) if p and y)
    fp = sum(1 for p, y in zip(pred, labels) if p and not y)
    fn = sum(1 for p, y in zip(pred, labels) if not p and y)
    if tp == 0:
        return 0.0, 0.0, 0.0
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    return 2 * precision * recall / (precision + recall), precision, recall


def adjust_pa_k(pred, segments, k_percent):
    """PA%K. 구간 안 탐지 비율이 K%를 '넘으면' 구간 전체를 탐지로 바꾼다.
    K=0 이면 점 하나만 맞아도 조정되므로 원래의 PA와 같다."""
    out = list(pred)
    for start, end in segments:
        hit = sum(pred[start:end + 1])
        if hit / (end - start + 1) > k_percent / 100:
            for t in range(start, end + 1):
                out[t] = 1
    return out


def adjust_delay(pred, segments, k):
    """SR-CNN의 지연 제한 조정. 시작점에서 k 안에 탐지가 있어야 구간 전체를 인정하고,
    그렇지 않으면 구간 안의 늦은 탐지까지 모두 놓친 것으로 본다."""
    out = list(pred)
    for start, end in segments:
        early = any(pred[start:min(end, start + k) + 1])
        for t in range(start, end + 1):
            out[t] = 1 if early else 0
    return out


def ranges_of(pred):
    ranges, start = [], None
    for t, p in enumerate(pred):
        if p and start is None:
            start = t
        if not p and start is not None:
            ranges.append((start, t - 1))
            start = None
    if start is not None:
        ranges.append((start, len(pred) - 1))
    return ranges


def overlap(a, b):
    return max(0, min(a[1], b[1]) - max(a[0], b[0]) + 1)


def range_f1(pred, segments):
    """Tatbul 외 범위 기반 F1. α=0(존재 보상 없음), γ=1, 평탄 편향이면
    구간마다 겹친 비율의 평균이 된다."""
    predicted = ranges_of(pred)
    if not predicted:
        return 0.0
    recall = sum(sum(overlap(r, p) for p in predicted) / (r[1] - r[0] + 1)
                 for r in segments) / len(segments)
    precision = sum(sum(overlap(p, r) for r in segments) / (p[1] - p[0] + 1)
                    for p in predicted) / len(predicted)
    if recall + precision == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def thresholds_of(scores, steps=200):
    ordered = sorted(scores)
    n = len(ordered)
    # 상위 0.05%~50% 구간을 촘촘히 훑는다. 최적 임계값은 이 안에 있다
    return sorted({ordered[int(n * (1 - q))] for q in
                   [0.0005 * (1.04 ** i) for i in range(steps)] if q < 0.5})


def best(scores, labels, segments, metric):
    """논문들이 보고하는 방식대로 지표마다 가장 좋은 임계값을 따로 고른다."""
    top = (0.0, None)
    for th in thresholds_of(scores):
        pred = [1 if s >= th else 0 for s in scores]
        value = metric(pred, labels, segments)
        if value > top[0]:
            top = (value, th)
    return top[0]


METRICS = {
    "F1(점 단위)": lambda p, y, s: f1_from(p, y)[0],
    "F1-PA": lambda p, y, s: f1_from(adjust_pa_k(p, s, 0), y)[0],
    "F1-PA%20": lambda p, y, s: f1_from(adjust_pa_k(p, s, 20), y)[0],
    "F1-PA%50": lambda p, y, s: f1_from(adjust_pa_k(p, s, 50), y)[0],
    "F1-지연≤7": lambda p, y, s: f1_from(adjust_delay(p, s, 7), y)[0],
    "범위 F1": lambda p, y, s: range_f1(p, s),
}


def pa_k_auc(scores, labels, segments):
    values = []
    for k in range(0, 101, 10):
        values.append(best(scores, labels, segments,
                           lambda p, y, s, k=k: f1_from(adjust_pa_k(p, s, k), y)[0]))
    # K 0~100을 [0,1]로 보고 사다리꼴로 넓이를 잰다
    area = sum((values[i] + values[i + 1]) / 2 * 0.1 for i in range(10))
    return values, area


def main():
    print(f"Python {sys.version.split()[0]}  seed={SEED}")

    length, seg_len, n_seg = 10_000, 100, 5
    rng = random.Random(SEED)
    labels, segments = make_labels(length, seg_len, n_seg, rng)
    print(f"\n[데이터] 길이 {length}, 이상 구간 {n_seg}개 × {seg_len}점, "
          f"이상 비율 {sum(labels) / length:.2%}")
    print("  구간(시작~끝):", ", ".join(f"{s}~{e}" for s, e in segments))

    detectors = {
        "무작위 U(0,1)": score_random(labels, rng),
        "정보 있음(+1.5σ)": score_informative(labels, segments, rng),
        "늦게 앎(뒤 20%)": score_late(labels, segments, rng),
    }

    print("\n[실험1] 지표별 최고 F1 — 지표마다 최적 임계값을 따로 고름")
    header = f"  {'탐지기':<16}" + "".join(f"{m:>12}" for m in METRICS)
    print(header)
    for name, scores in detectors.items():
        row = f"  {name:<16}"
        for metric in METRICS.values():
            row += f"{best(scores, labels, segments, metric):>12.3f}"
        print(row)

    print("\n[실험2] 무작위 점수의 F1-PA — 이상 비율 5%는 그대로, 구간 길이만 바꿈")
    print(f"  {'구간 길이':>8}  {'구간 수':>6}  {'F1(점 단위)':>10}  {'F1-PA':>8}")
    for seg in (10, 50, 100, 500):
        rng2 = random.Random(SEED + seg)
        n = (length * 5 // 100) // seg
        y2, s2 = make_labels(length, seg, n, rng2)
        sc = score_random(y2, rng2)
        print(f"  {seg:>8}  {n:>6}  "
              f"{best(sc, y2, s2, METRICS['F1(점 단위)']):>10.3f}  "
              f"{best(sc, y2, s2, METRICS['F1-PA']):>8.3f}")

    print("\n[실험3] 이론값 — 점마다 확률 p로 경보를 내면 길이 l 구간을 한 번이라도 맞힐 확률 1-(1-p)^l")
    for p in (0.01, 0.02, 0.05):
        cells = "  ".join(f"l={l}: {1 - (1 - p) ** l:.3f}" for l in (10, 100, 500))
        print(f"  p={p:<5} {cells}")

    print("\n[실험4] PA%K 곡선 — K=0은 F1-PA, K=100은 점 단위 F1")
    print("  " + f"{'탐지기':<16}" + "".join(f"{'K=' + str(k):>7}" for k in range(0, 101, 10))
          + f"{'AUC':>8}")
    for name, scores in detectors.items():
        values, area = pa_k_auc(scores, labels, segments)
        print(f"  {name:<16}" + "".join(f"{v:>7.3f}" for v in values) + f"{area:>8.3f}")

    print("\n[실험5] 최고 F1-PA 임계값에서의 평균 경보 지연(구간 시작 → 첫 탐지, 단위: 점)")
    for name, scores in detectors.items():
        top = (0.0, None)
        for th in thresholds_of(scores):
            pred = [1 if s >= th else 0 for s in scores]
            v = f1_from(adjust_pa_k(pred, segments, 0), labels)[0]
            if v > top[0]:
                top = (v, pred)
        pred = top[1]
        delays = []
        for start, end in segments:
            hits = [t for t in range(start, end + 1) if pred[t]]
            if hits:
                delays.append(hits[0] - start)
        mean = sum(delays) / len(delays) if delays else float("nan")
        print(f"  {name:<16} 탐지 구간 {len(delays)}/{len(segments)}  "
              f"지연 {delays}  평균 {mean:.1f}")


if __name__ == "__main__":
    main()
