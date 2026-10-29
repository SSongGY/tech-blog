"""정량적 위험 분석 세 기법을 가상 프로젝트 하나에 함께 적용해 본다.

가상 회사 '마루정보시스템'의 레거시 재구축 프로젝트를 쓴다. 실제 사업 수치가
아니라 세 기법의 계산 과정을 드러내려고 만든 값이다.
"""

import math
import random
import statistics
import sys

MONEY = "백만원"


def banner(title):
    print()
    print("=" * 68)
    print(title)
    print("=" * 68)


# ---------------------------------------------------------------------------
# 1. 기대화폐가치 (EMV) — 위험 등록부 전체의 노출도를 한 수로 접는다
# ---------------------------------------------------------------------------

# (이름, 발생확률, 영향액). 영향액은 비용 증가를 음수로 둔다.
RISK_REGISTER = [
    ("데이터 이관 실패로 전면 재작업", 0.30, -800),
    ("핵심 설계 인력 이탈", 0.20, -500),
    ("성능 미달로 하드웨어 증설", 0.40, -300),
    ("패키지 조기 납품으로 기간 단축", 0.25, +400),
]


def expected_monetary_value(register):
    """각 위험의 확률 x 영향을 더해 전체 노출도를 낸다."""
    rows = [(name, p, impact, p * impact) for name, p, impact in register]
    return rows, sum(row[3] for row in rows)


def report_emv():
    banner("1. 기대화폐가치(EMV) — 위험 등록부")
    rows, total = expected_monetary_value(RISK_REGISTER)
    print(f"{'위험':<24}{'확률':>8}{'영향':>10}{'EMV':>10}")
    print("-" * 52)
    for name, p, impact, emv in rows:
        print(f"{name:<24}{p:>8.2f}{impact:>10,}{emv:>10,.1f}")
    print("-" * 52)
    print(f"{'합계 (예비비 산정 근거)':<24}{'':>8}{'':>10}{total:>10,.1f}")
    print()
    worst = sum(impact for _, _, impact in RISK_REGISTER if impact < 0)
    print(f"모든 위협이 동시에 터진 최악값 : {worst:>8,} {MONEY}")
    print(f"EMV 합계                       : {total:>8,.1f} {MONEY}")
    print("EMV 는 평균이므로 최악값과 다르다. 예비비를 EMV 로만 잡으면 꼬리가 비어 있다.")


# ---------------------------------------------------------------------------
# 2. 의사결정나무 — 대안별 EMV 를 잎에서 뿌리로 접는다(rollback)
# ---------------------------------------------------------------------------

# 각 대안: (이름, 선투자비, [(결과이름, 확률, 추가비용), ...])
ALTERNATIVES = [
    ("자체 개발", 2000, [("요건 충족", 0.60, 0), ("재작업 발생", 0.40, 900)]),
    ("패키지 도입", 2600, [("표준 기능으로 충족", 0.90, 0), ("커스터마이징", 0.10, 500)]),
    ("현행 유지 + 부분 개선", 900, [("운영 가능", 0.45, 0), ("장애 대응 비용", 0.55, 1500)]),
]


def rollback(alternatives):
    """기회 노드의 기대값을 먼저 내고, 선투자비를 더해 결정 노드로 올린다."""
    folded = []
    for name, upfront, outcomes in alternatives:
        chance = sum(p * extra for _, p, extra in outcomes)
        folded.append((name, upfront, chance, upfront + chance))
    return folded


def report_decision_tree():
    banner("2. 의사결정나무 — 대안 3가지의 기대비용")
    folded = rollback(ALTERNATIVES)
    for (name, upfront, outcomes), (_, _, chance, total) in zip(ALTERNATIVES, folded):
        print(f"[{name}]  선투자 {upfront:,} {MONEY}")
        for outcome, p, extra in outcomes:
            print(f"    {outcome:<20} p={p:.2f}  추가비용 {extra:>6,}  기여 {p * extra:>8,.1f}")
        print(f"    -> 기회노드 기대값 {chance:>8,.1f} / 가지 기대비용 {total:>8,.1f}")
        print()
    best = min(folded, key=lambda row: row[3])
    print(f"{'대안':<24}{'기대비용':>12}")
    print("-" * 36)
    for name, _, _, total in folded:
        mark = "  <= 선택" if name == best[0] else ""
        print(f"{name:<24}{total:>12,.1f}{mark}")
    print()
    print(f"선택: {best[0]} (기대비용 {best[3]:,.1f} {MONEY})")
    worst_case = ALTERNATIVES[2][1] + ALTERNATIVES[2][2][1][2]
    print(f"다만 선택된 가지의 최악 분기는 {worst_case:,}{MONEY}이고, 확률은 "
          f"{ALTERNATIVES[2][2][1][1]:.2f} 로 절반을 넘는다.")
    print("기대값은 가장 낮지만 빗나갈 확률이 가장 높은 대안이기도 하다.")


# ---------------------------------------------------------------------------
# 3. 몬테카를로 시뮬레이션 — 일정 분포를 만든다
# ---------------------------------------------------------------------------

# (작업, 최소, 최빈, 최대) 단위: 일
TASKS = [
    ("요건 정의", 15, 20, 35),
    ("데이터 이관 설계", 20, 30, 60),
    ("개발", 40, 55, 90),
    ("통합 시험", 10, 18, 45),
]

TRIALS = 10000
SEED = 20261029


def _normal_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def triangular_total(rng, tasks, rho=0.0):
    """직렬 작업의 합계 기간을 한 번 뽑는다.

    rho 가 0 보다 크면 모든 작업이 공유하는 지연 요인을 넣는다. 인력 수준이나
    요건 안정성처럼 작업마다 따로 놀지 않는 변수를 흉내낸 것이다.

    가우시안 코퓰러를 쓴다. 공통 성분과 개별 성분을 sqrt(rho), sqrt(1-rho) 로
    섞으면 각 작업의 분포는 그대로 두고 작업 사이 상관만 넣을 수 있다.
    두 수를 그냥 가중평균하면 개별 작업의 분산까지 줄어들어, 상관을 넣었는데
    꼬리가 오히려 얇아지는 결과가 나온다.
    """
    shared = rng.gauss(0.0, 1.0) if rho else 0.0
    total = 0.0
    for _, low, mode, high in tasks:
        own = rng.gauss(0.0, 1.0)
        if rho:
            z = math.sqrt(rho) * shared + math.sqrt(1.0 - rho) * own
        else:
            z = own
        total += _triangular_quantile(_normal_cdf(z), low, mode, high)
    return total


def _triangular_quantile(u, low, mode, high):
    """삼각분포의 역누적분포. 같은 난수열로 상관 구조만 바꿔 비교하려고 직접 쓴다."""
    span = high - low
    pivot = (mode - low) / span
    if u < pivot:
        return low + (span * (mode - low) * u) ** 0.5
    return high - (span * (high - mode) * (1 - u)) ** 0.5


def simulate(rho):
    rng = random.Random(SEED)
    return sorted(triangular_total(rng, TASKS, rho) for _ in range(TRIALS))


def percentile(sorted_values, q):
    """정렬된 표본에서 하위 q 백분위 값을 고른다(최근접 순위법)."""
    idx = min(len(sorted_values) - 1, max(0, round(q / 100 * len(sorted_values)) - 1))
    return sorted_values[idx]


def report_monte_carlo():
    banner("3. 몬테카를로 시뮬레이션 — 일정")
    mode_sum = sum(mode for _, _, mode, _ in TASKS)
    pert_sum = sum((low + 4 * mode + high) / 6 for _, low, mode, high in TASKS)
    print(f"{'작업':<18}{'최소':>6}{'최빈':>6}{'최대':>6}{'PERT 평균':>12}")
    print("-" * 48)
    for name, low, mode, high in TASKS:
        print(f"{name:<18}{low:>6}{mode:>6}{high:>6}{(low + 4 * mode + high) / 6:>12.2f}")
    print("-" * 48)
    print(f"{'합계':<18}{'':>6}{mode_sum:>6}{'':>6}{pert_sum:>12.2f}")
    print()
    print(f"시행 횟수 {TRIALS:,}회 / 난수 시드 {SEED}")
    print()

    header = f"{'가정':<22}{'평균':>9}{'P50':>9}{'P80':>9}{'P95':>9}{'최대':>9}"
    print(header)
    print("-" * len(header))
    results = {}
    for label, rho in [("작업 간 독립", 0.0), ("상관 rho=0.5", 0.5)]:
        samples = simulate(rho)
        results[label] = samples
        print(f"{label:<22}{statistics.fmean(samples):>9.1f}"
              f"{percentile(samples, 50):>9.1f}{percentile(samples, 80):>9.1f}"
              f"{percentile(samples, 95):>9.1f}{max(samples):>9.1f}")
    print()
    print(f"최빈값 단순 합계 : {mode_sum} 일")
    print(f"PERT 평균 합계   : {pert_sum:.2f} 일")
    indep = results["작업 간 독립"]
    corr = results["상관 rho=0.5"]
    print(f"독립 가정 P80    : {percentile(indep, 80):.1f} 일")
    print(f"상관 가정 P80    : {percentile(corr, 80):.1f} 일 "
          f"(차이 {percentile(corr, 80) - percentile(indep, 80):+.1f} 일)")
    print()
    print("누적 분포(S-커브) 일부")
    print(f"{'완료 확률':>10}{'독립 가정':>12}{'상관 가정':>12}")
    for q in (10, 25, 50, 75, 80, 90, 95, 99):
        print(f"{q:>9}%{percentile(indep, q):>12.1f}{percentile(corr, q):>12.1f}")
    print()
    over_mode_indep = sum(1 for v in indep if v > mode_sum) / TRIALS
    print(f"최빈값 합계({mode_sum}일) 안에 끝날 확률 : "
          f"{(1 - over_mode_indep) * 100:.1f}% (독립 가정)")


def main():
    print(f"Python {sys.version.split()[0]}")
    print("가상 회사 '마루정보시스템' 레거시 재구축 프로젝트 — 실재하지 않는 수치다.")
    report_emv()
    report_decision_tree()
    report_monte_carlo()


if __name__ == "__main__":
    main()
