"""이진 분류 평가 지표를 혼동행렬에서 손계산과 같은 순서로 구한다.

거래 20건(사기 5건, 정상 15건)에 모델이 매긴 점수를 고정해 두고,
임계값을 바꿔 가며 혼동행렬과 지표가 어떻게 움직이는지 찍는다.
외부 라이브러리를 쓰지 않는 것은 답안에서 손으로 할 계산과
한 줄씩 대응시키기 위해서다.
"""

from math import sqrt

# (거래 번호, 실제 사기 여부, 모델 점수)
TRANSACTIONS = [
    ("T01", 1, 0.95), ("T02", 0, 0.91), ("T03", 1, 0.85), ("T04", 0, 0.66),
    ("T05", 1, 0.62), ("T06", 0, 0.55), ("T07", 0, 0.48), ("T08", 1, 0.45),
    ("T09", 0, 0.40), ("T10", 0, 0.35), ("T11", 0, 0.30), ("T12", 1, 0.28),
    ("T13", 0, 0.22), ("T14", 0, 0.18), ("T15", 0, 0.15), ("T16", 0, 0.12),
    ("T17", 0, 0.10), ("T18", 0, 0.08), ("T19", 0, 0.05), ("T20", 0, 0.02),
]

THRESHOLDS = [0.3, 0.5, 0.7, 0.9]


def safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else float("nan")


def confusion(threshold: float) -> dict[str, int]:
    counts = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    for _, actual, score in TRANSACTIONS:
        predicted = 1 if score >= threshold else 0
        key = ("t" if predicted == actual else "f") + ("p" if predicted else "n")
        counts[key] += 1
    return counts


def metrics(c: dict[str, int]) -> dict[str, float]:
    tp, fp, fn, tn = c["tp"], c["fp"], c["fn"], c["tn"]
    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    specificity = safe_div(tn, tn + fp)

    def f_beta(beta: float) -> float:
        b2 = beta * beta
        return safe_div((1 + b2) * tp, (1 + b2) * tp + fp + b2 * fn)

    mcc_den = sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return {
        "accuracy": safe_div(tp + tn, tp + fp + fn + tn),
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "fpr": safe_div(fp, fp + tn),
        "f1": f_beta(1.0),
        "f2": f_beta(2.0),
        "f0.5": f_beta(0.5),
        "balanced_acc": (recall + specificity) / 2,
        "mcc": safe_div(tp * tn - fp * fn, mcc_den),
    }


def print_dataset() -> None:
    positives = sum(actual for _, actual, _ in TRANSACTIONS)
    print("== 데이터: 거래 20건 (점수 내림차순) ==")
    print(f"  사기(양성) {positives}건 / 정상(음성) {len(TRANSACTIONS) - positives}건")
    for tx_id, actual, score in TRANSACTIONS:
        print(f"  {tx_id}  실제={'사기' if actual else '정상'}  점수={score:.2f}")


def print_threshold_table() -> None:
    print("\n== 1. 임계값별 혼동행렬 (점수 >= 임계값 이면 사기로 판정) ==")
    print("  임계값 | TP | FP | FN | TN")
    for threshold in THRESHOLDS:
        c = confusion(threshold)
        print(f"   {threshold:.1f}   | {c['tp']:2d} | {c['fp']:2d} | {c['fn']:2d} | {c['tn']:2d}")

    print("\n== 2. 임계값별 지표 ==")
    names = ["accuracy", "precision", "recall", "specificity", "f1", "f2", "f0.5",
             "balanced_acc", "mcc"]
    print("  임계값 | " + " | ".join(f"{n:>12s}" for n in names))
    for threshold in THRESHOLDS:
        m = metrics(confusion(threshold))
        print(f"   {threshold:.1f}   | " + " | ".join(f"{m[n]:12.3f}" for n in names))


def print_all_negative_baseline() -> None:
    print("\n== 3. 전부 '정상'이라고 답하는 모델 (임계값 1.01) ==")
    c = confusion(1.01)
    m = metrics(c)
    print(f"  TP={c['tp']} FP={c['fp']} FN={c['fn']} TN={c['tn']}")
    for name in ["accuracy", "precision", "recall", "balanced_acc", "mcc"]:
        print(f"  {name:12s} = {m[name]:.3f}")


def print_auc() -> None:
    """AUC 를 '양성 하나·음성 하나를 뽑았을 때 양성 점수가 더 높을 확률'로 센다."""
    positives = [s for _, a, s in TRANSACTIONS if a == 1]
    negatives = [s for _, a, s in TRANSACTIONS if a == 0]
    wins = sum(1.0 if p > n else 0.5 if p == n else 0.0
               for p in positives for n in negatives)
    pairs = len(positives) * len(negatives)
    print("\n== 4. ROC AUC — 양성·음성 쌍 세기 ==")
    print(f"  쌍 {pairs}개 중 양성 점수가 더 높은 쌍 {wins:g}개")
    print(f"  AUC = {wins:g} / {pairs} = {wins / pairs:.3f}")


def main() -> None:
    print_dataset()
    print_threshold_table()
    print_all_negative_baseline()
    print_auc()


if __name__ == "__main__":
    main()
