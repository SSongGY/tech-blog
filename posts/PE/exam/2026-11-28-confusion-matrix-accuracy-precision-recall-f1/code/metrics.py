"""혼동행렬 네 칸에서 평가 지표를 계산한다.

문항 조건: % 로 표시하고 소수점 아래는 버린다.
버림은 표시 단계에서만 한다. 버린 값을 다시 계산에 넣으면 F1 이 1%p 달라지는데,
그 차이를 보이려고 두 방식을 함께 찍는다.
"""

import math
import sys
from fractions import Fraction

TP, FP, FN, TN = 100, 5, 7, 9


def floor_percent(value: Fraction) -> int:
    # Fraction 으로 두어야 109/121 같은 값이 부동소수점 오차 없이 버려진다
    return math.floor(value * 100)


def show(name: str, formula: str, value: Fraction) -> None:
    print(f"{name:<14}{formula:<26}{str(value):>9} = {float(value):.5f} -> {floor_percent(value)}%")


def main() -> None:
    print(f"Python {sys.version.split()[0]}")
    print()
    total = TP + FP + FN + TN
    print("혼동행렬 (행: 실제, 열: 예측)")
    print(f"{'':<10}{'예측 양성':>10}{'예측 음성':>10}{'합계':>8}")
    print(f"{'실제 양성':<10}{TP:>12}{FN:>12}{TP + FN:>9}")
    print(f"{'실제 음성':<10}{FP:>12}{TN:>12}{FP + TN:>9}")
    print(f"{'합계':<12}{TP + FP:>12}{FN + TN:>12}{total:>9}")
    print()

    accuracy = Fraction(TP + TN, total)
    precision = Fraction(TP, TP + FP)
    recall = Fraction(TP, TP + FN)
    f1 = 2 * precision * recall / (precision + recall)
    specificity = Fraction(TN, TN + FP)
    npv = Fraction(TN, TN + FN)

    print("[문항이 묻는 지표]")
    show("정확도", "(TP+TN)/전체", accuracy)
    show("정밀도", "TP/(TP+FP)", precision)
    show("재현율", "TP/(TP+FN)", recall)
    show("F1", "2PR/(P+R)", f1)
    show("F1 (칸으로)", "2TP/(2TP+FP+FN)", Fraction(2 * TP, 2 * TP + FP + FN))
    print()

    p_cut, r_cut = Fraction(floor_percent(precision), 100), Fraction(floor_percent(recall), 100)
    f1_from_cut = 2 * p_cut * r_cut / (p_cut + r_cut)
    print("[버린 값을 다시 넣으면]")
    show("F1 (95%,93%)", "2*0.95*0.93/1.88", f1_from_cut)
    print()

    print("[해석을 위한 보조 지표]")
    show("특이도", "TN/(TN+FP)", specificity)
    show("음성 예측도", "TN/(TN+FN)", npv)
    baseline = Fraction(TP + FN, total)
    show("전부 양성 기준선", "(TP+FN)/전체", baseline)
    balanced = (recall + specificity) / 2
    show("균형 정확도", "(재현율+특이도)/2", balanced)
    mcc_num = TP * TN - FP * FN
    mcc_den = math.sqrt((TP + FP) * (TP + FN) * (TN + FP) * (TN + FN))
    print(f"{'MCC':<14}{'(TP*TN-FP*FN)/sqrt(...)':<26}{mcc_num:>5}/{mcc_den:.1f} = {mcc_num / mcc_den:.5f}")


if __name__ == "__main__":
    main()
