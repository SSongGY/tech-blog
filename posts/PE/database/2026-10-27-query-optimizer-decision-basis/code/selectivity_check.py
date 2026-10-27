"""비용 기반 옵티마이저가 쓰는 선택도 산식을 손으로 따라가 검산한다.

PostgreSQL 16 문서 "How the Planner Uses Statistics" 의 행 수 추정 예제에
적힌 수치를, 같은 산식에 통계값을 넣어 다시 계산해 본다. 문서에 적힌 값과
맞는지를 확인하는 것이 목적이므로, 계산 결과와 문서 값을 나란히 찍는다.

출처: https://www.postgresql.org/docs/16/row-estimation-examples.html
"""

TOTAL_ROWS = 10000

# 문서가 보여 주는 pg_stats 값 그대로
HISTOGRAM_BOUNDS = [0, 993, 1997, 3050, 4040, 5036, 5957, 7057, 8029, 9016, 9995]
MCV_FREQS = [0.00333333, 0.003, 0.003, 0.003, 0.003, 0.003, 0.003, 0.003, 0.003, 0.003]
N_DISTINCT = 676
NUM_MCV = len(MCV_FREQS)


def histogram_selectivity(value: int) -> float:
    """버킷을 찾아 그 안은 선형 분포라고 보고 비례 배분한다."""
    buckets = len(HISTOGRAM_BOUNDS) - 1
    for index in range(buckets):
        low, high = HISTOGRAM_BOUNDS[index], HISTOGRAM_BOUNDS[index + 1]
        if low <= value <= high:
            inside = (value - low) / (high - low)
            return (index + inside) / buckets
    return 1.0


def report(label: str, computed: float, documented: float, rows_doc: int) -> None:
    rows = TOTAL_ROWS * computed
    gap = abs(computed - documented)
    print(f"  {label}")
    print(f"    계산한 선택도 {computed:.7f} · 문서 {documented:.7f} · 차이 {gap:.2e}")
    print(f"    계산한 행 수 {rows:.1f} · 문서 {rows_doc}")


def main() -> None:
    print("전체 행 수 10,000 · 히스토그램 버킷 10개 · MCV 10개 · n_distinct 676")
    print()

    print("1) 범위 조건 unique1 < 1000 — 히스토그램 선형 보간")
    range_sel = histogram_selectivity(1000)
    report("(1 + (1000-993)/(1997-993)) / 10", range_sel, 0.100697, 1007)
    print()

    print("2) 등호 조건, 값이 MCV 안에 있음 stringu1 = 'CRAAAA'")
    mcv_sel = MCV_FREQS[2]
    report("most_common_freqs[3]", mcv_sel, 0.003, 30)
    print()

    print("3) 등호 조건, 값이 MCV 밖 stringu1 = 'xxx'")
    rest = 1 - sum(MCV_FREQS)
    other_sel = rest / (N_DISTINCT - NUM_MCV)
    report("(1 - Σmcf) / (n_distinct - num_mcv)", other_sel, 0.0014559, 15)
    print()

    print("4) MCV 와 히스토그램을 합친 경우 stringu1 < 'IAAAAA'")
    mcv_part = sum(MCV_FREQS[:6])
    hist_fraction = 1 - sum(MCV_FREQS)
    hist_part = 0.298387  # 문서가 제시한 히스토그램 추정값
    mixed = mcv_part + hist_part * hist_fraction
    report("mcv_sel + hist_sel * (1 - Σmcf)", mixed, 0.307669, 3077)
    print()

    print("5) 두 조건을 AND — 독립이라고 가정하고 곱한다")
    both = range_sel * other_sel
    report("0.100697 * 0.0014559", both, 0.0001466, 1)
    print()

    print("6) 조인 unique1 < 50 AND t1.unique2 = t2.unique2")
    outer_sel = histogram_selectivity(50)
    outer_rows = TOTAL_ROWS * outer_sel
    join_sel = (1 - 0) * (1 - 0) / max(10000, 10000)
    join_rows = outer_rows * TOTAL_ROWS * join_sel
    print(f"    바깥 필터 선택도 {outer_sel:.6f} · 문서 0.005035")
    print(f"    바깥 행 수 {outer_rows:.1f} · 문서 50")
    print(f"    조인 선택도 1/max(n_distinct) = {join_sel} · 문서 0.0001")
    print(f"    조인 결과 행 수 {join_rows:.1f} · 문서 50")
    print()

    print("7) 통계가 틀렸을 때 — n_distinct 만 어긋나면 추정이 어떻게 밀리는가")
    print("    같은 등호 조건 stringu1 = 'xxx' 에 n_distinct 만 바꿔 넣는다")
    for assumed in (676, 300, 100, 50):
        sel = rest / (assumed - NUM_MCV)
        print(f"    n_distinct {assumed:>4}  ->  선택도 {sel:.6f} · 추정 행 수 {TOTAL_ROWS * sel:8.1f}")


if __name__ == "__main__":
    main()
