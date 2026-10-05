"""CPM 전진·후진 계산과 PERT 확률 계산을 손계산과 같은 순서로 수행한다.

외부 의존성 없이 파이썬 표준 라이브러리만 쓴다.
"""

import math
import platform
import random
import statistics

# 활동: (이름, 선행 활동, 낙관 a, 최빈 m, 비관 b) — 단위는 작업일
ACTIVITIES = {
    "A": ("요구분석", [], 3, 5, 7),
    "B": ("아키텍처 설계", ["A"], 4, 6, 14),
    "C": ("DB 설계", ["A"], 2, 4, 6),
    "D": ("인프라 구축", ["A"], 4, 8, 24),
    "E": ("애플리케이션 개발", ["B", "C"], 8, 12, 22),
    "F": ("데이터 이관 준비", ["C"], 3, 5, 13),
    "G": ("통합 테스트", ["D", "E", "F"], 4, 6, 8),
    "H": ("개통", ["G"], 1, 2, 3),
}
DEADLINE = 36
TRIALS = 100_000
SEED = 20261005


def expected_time(a, m, b):
    return (a + 4 * m + b) / 6


def variance(a, b):
    return ((b - a) / 6) ** 2


def successors_of(key):
    return [k for k, v in ACTIVITIES.items() if key in v[1]]


def cpm(durations):
    """전진 계산으로 ES·EF, 후진 계산으로 LS·LF를 구한다. 딕셔너리 순서가 위상 순서다."""
    es, ef = {}, {}
    for key, (_, preds, *_rest) in ACTIVITIES.items():
        es[key] = max((ef[p] for p in preds), default=0)
        ef[key] = es[key] + durations[key]
    finish = max(ef.values())

    ls, lf = {}, {}
    for key in reversed(list(ACTIVITIES)):
        succs = successors_of(key)
        lf[key] = min((ls[s] for s in succs), default=finish)
        ls[key] = lf[key] - durations[key]

    total_float = {k: ls[k] - es[k] for k in ACTIVITIES}
    # 자유 여유는 '바로 다음 활동의 가장 이른 시작'까지만 본다
    free_float = {
        k: min((es[s] for s in successors_of(k)), default=finish) - ef[k]
        for k in ACTIVITIES
    }
    return es, ef, ls, lf, total_float, free_float, finish


def print_dataset():
    print("== 입력: 활동·선행 관계·3점 추정 (작업일) ==")
    print(f"{'활동':<4}{'이름':<12}{'선행':<8}{'a':>4}{'m':>4}{'b':>4}")
    for key, (name, preds, a, m, b) in ACTIVITIES.items():
        print(f"{key:<4}{name:<12}{','.join(preds) or '-':<8}{a:>4}{m:>4}{b:>4}")
    print()


def print_cpm(durations):
    es, ef, ls, lf, tf, ff, finish = cpm(durations)
    print(f"{'활동':<4}{'te':>5}{'ES':>5}{'EF':>5}{'LS':>5}{'LF':>5}{'TF':>5}{'FF':>5}  주공정")
    for key in ACTIVITIES:
        mark = "*" if tf[key] == 0 else ""
        print(f"{key:<4}{durations[key]:>5g}{es[key]:>5g}{ef[key]:>5g}"
              f"{ls[key]:>5g}{lf[key]:>5g}{tf[key]:>5g}{ff[key]:>5g}  {mark}")
    critical = [k for k in ACTIVITIES if tf[k] == 0]
    print(f"프로젝트 기간 {finish:g}일, 주공정 {'-'.join(critical)}")
    print()
    return critical, finish


def delay_experiment(base, key, days):
    durations = dict(base)
    durations[key] += days
    es, ef, *_rest, finish = cpm(durations)
    shifted = [k for k in ACTIVITIES if es[k] != cpm(base)[0][k]]
    print(f"{key} +{days}일 → 프로젝트 {finish:g}일, ES가 밀린 활동 {shifted or '없음'}")


def pert_beta_sample(rng, a, m, b):
    # 평균이 (a+4m+b)/6 이 되도록 모수를 잡은 베타분포 (PERT-베타)
    alpha = 1 + 4 * (m - a) / (b - a)
    beta = 1 + 4 * (b - m) / (b - a)
    return a + (b - a) * rng.betavariate(alpha, beta)


def main():
    print(f"Python {platform.python_version()}")
    print()
    print_dataset()

    te = {k: expected_time(a, m, b) for k, (_, _, a, m, b) in ACTIVITIES.items()}
    print("== CPM: te로 전진·후진 계산 ==")
    critical, finish = print_cpm(te)

    print("== 지연 실험: 여유를 넘을 때만 종료일이 밀린다 ==")
    for key, days in [("B", 2), ("C", 3), ("C", 4), ("F", 10), ("F", 11)]:
        delay_experiment(te, key, days)
    print()

    print("== PERT: 주공정 분산으로 납기 확률 ==")
    var_cp = sum(variance(ACTIVITIES[k][2], ACTIVITIES[k][4]) for k in critical)
    sigma = math.sqrt(var_cp)
    z = (DEADLINE - finish) / sigma
    prob = 0.5 * (1 + math.erf(z / math.sqrt(2)))
    for k in critical:
        _, _, a, _, b = ACTIVITIES[k]
        print(f"{k}: 분산 ((b-a)/6)^2 = {variance(a, b):.3f}")
    print(f"주공정 분산 합 {var_cp:.3f}, 표준편차 {sigma:.3f}")
    print(f"납기 {DEADLINE}일: Z = ({DEADLINE}-{finish:g})/{sigma:.3f} = {z:.3f}, P = {prob:.3f}")
    print()

    print(f"== 몬테카를로 {TRIALS:,}회: 모든 경로를 함께 굴린다 (seed {SEED}) ==")
    simulate(te, critical, finish, prob)
    print()

    # D를 주공정에 가깝게 만든다. te 기준 주공정과 PERT 공식 값은 그대로다
    ACTIVITIES["D"] = ("인프라 구축", ["A"], 10, 18, 26)
    te = {k: expected_time(a, m, b) for k, (_, _, a, m, b) in ACTIVITIES.items()}
    print("== 변형: D를 (10, 18, 26)으로 — 여유 2일인 준주공정 ==")
    critical, finish = print_cpm(te)
    print(f"== 몬테카를로 {TRIALS:,}회 (seed {SEED}) ==")
    simulate(te, critical, finish, prob)


def simulate(te, critical, finish, prob):
    rng = random.Random(SEED)
    finishes, critical_hits = [], {k: 0 for k in ACTIVITIES}
    duration_sums = {k: 0.0 for k in ACTIVITIES}
    # 같은 표본에서 주공정만 더한 값 — 분포 모양 차이를 빼고 병합 효과만 남기려는 대조군
    critical_only = []
    for _ in range(TRIALS):
        sample = {k: pert_beta_sample(rng, a, m, b)
                  for k, (_, _, a, m, b) in ACTIVITIES.items()}
        *_rest, tf, _ff, end = cpm(sample)
        finishes.append(end)
        critical_only.append(sum(sample[k] for k in critical))
        for k in ACTIVITIES:
            duration_sums[k] += sample[k]
            if tf[k] < 1e-9:
                critical_hits[k] += 1
    on_time = sum(f <= DEADLINE for f in finishes) / TRIALS
    # 표본 평균이 te와 맞는지 보여 분포 설정이 PERT 가정과 같다는 것을 확인한다
    print("활동별 표본 평균 / te:",
          ", ".join(f"{k} {duration_sums[k] / TRIALS:.2f}/{te[k]:g}" for k in ACTIVITIES))
    cp_on_time = sum(f <= DEADLINE for f in critical_only) / TRIALS
    print(f"주공정 합의 표본 분산 {statistics.pvariance(critical_only):.3f}")
    print(f"종료일 평균: 주공정만 {statistics.fmean(critical_only):.2f}일, "
          f"전체 네트워크 {statistics.fmean(finishes):.2f}일 (CPM {finish:g}일)")
    print(f"납기 {DEADLINE}일 이내 비율: PERT 공식 {prob:.3f}, "
          f"주공정만 {cp_on_time:.3f}, 전체 네트워크 {on_time:.3f}")
    print("활동별 주공정에 든 비율:")
    for k in ACTIVITIES:
        print(f"  {k} {critical_hits[k] / TRIALS:.3f}")


if __name__ == "__main__":
    main()
