"""Capers Jones(2011) 표 1의 결함 출처별 수치로 전체 DRE 를 다시 계산해 검산한다.

표는 출처별 결함 잠재량(기능 점수당 결함 수)과 출처별 DRE 를 주고,
전달 결함과 전체 DRE 를 반올림해 적는다. 그 값이 출처별 값에서 나오는지 확인하고,
전달 결함이 어느 출처에서 오는지 비중을 본다.
"""

# (출처, 결함 잠재량[결함/FP], 출처별 DRE) — Jones 2011, Table 1
DEFECT_ORIGINS = [
    ("요구사항", 1.00, 0.77),
    ("설계", 1.25, 0.85),
    ("코딩", 1.75, 0.95),
    ("문서", 0.60, 0.80),
    ("잘못된 수정", 0.40, 0.70),
]

# 표가 적은 합계 — 계산 결과와 비교한다
PUBLISHED_TOTAL_POTENTIAL = 5.00
PUBLISHED_TOTAL_DRE = 0.85
PUBLISHED_TOTAL_DELIVERED = 0.75


def dre(removed: float, delivered: float) -> float:
    # 출시 전에 없앤 결함 / (출시 전에 없앤 결함 + 출시 후 고객이 찾은 결함)
    return removed / (removed + delivered)


def main() -> None:
    print("1. Jones 의 예: 개발팀 90건, 고객 보고 10건")
    print(f"   DRE = 90 / (90 + 10) = {dre(90, 10):.0%}\n")

    print("2. 출처별 전달 결함 = 잠재량 x (1 - 출처별 DRE)")
    print(f"   {'출처':<8} {'잠재량':>6} {'DRE':>5} {'제거':>7} {'전달':>7}")
    total_potential = total_removed = total_delivered = 0.0
    rows = []
    for origin, potential, origin_dre in DEFECT_ORIGINS:
        removed = potential * origin_dre
        delivered = potential - removed
        rows.append((origin, delivered))
        total_potential += potential
        total_removed += removed
        total_delivered += delivered
        print(f"   {origin:<8} {potential:>6.2f} {origin_dre:>5.0%} "
              f"{removed:>7.4f} {delivered:>7.4f}")
    print(f"   {'합계':<8} {total_potential:>6.2f} "
          f"{dre(total_removed, total_delivered):>5.1%} "
          f"{total_removed:>7.4f} {total_delivered:>7.4f}\n")

    print("3. 표가 적은 합계와 비교")
    print(f"   잠재량  계산 {total_potential:.2f} / 표 {PUBLISHED_TOTAL_POTENTIAL:.2f}")
    print(f"   전달    계산 {total_delivered:.4f} / 표 {PUBLISHED_TOTAL_DELIVERED:.2f}")
    print(f"   DRE     계산 {dre(total_removed, total_delivered):.2%}"
          f" / 표 {PUBLISHED_TOTAL_DRE:.0%}\n")

    print("4. 전달 결함은 어디서 오는가 (전달 결함 합계 대비)")
    for origin, delivered in sorted(rows, key=lambda r: r[1], reverse=True):
        print(f"   {origin:<8} {delivered / total_delivered:>6.1%}")
    non_code = sum(d for o, d in rows if o != "코딩")
    print(f"   코딩 외   {non_code / total_delivered:>6.1%}\n")

    print("5. 코딩 결함 DRE 만 95% -> 99% 로 올리면")
    improved = [(o, p, 0.99 if o == "코딩" else d) for o, p, d in DEFECT_ORIGINS]
    removed = sum(p * d for _, p, d in improved)
    delivered = sum(p * (1 - d) for _, p, d in improved)
    print(f"   전달 {delivered:.4f} / 전체 DRE {dre(removed, delivered):.2%}")

    print("6. 요구사항 결함 DRE 만 77% -> 95% 로 올리면")
    improved = [(o, p, 0.95 if o == "요구사항" else d) for o, p, d in DEFECT_ORIGINS]
    removed = sum(p * d for _, p, d in improved)
    delivered = sum(p * (1 - d) for _, p, d in improved)
    print(f"   전달 {delivered:.4f} / 전체 DRE {dre(removed, delivered):.2%}")


if __name__ == "__main__":
    main()
