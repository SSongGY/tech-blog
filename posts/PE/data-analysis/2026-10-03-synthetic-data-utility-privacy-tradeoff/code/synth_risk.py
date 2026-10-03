"""합성데이터의 구별·연결·추론 위험도와 유용성을 한 원본에 대해 나란히 계산한다.

위험도 세 가지는 개인정보보호위원회 「합성데이터 생성·활용 안내서」(2024-12)
부록2의 산출 절차를, 추론 위험도 임계값은 부록4의 50:50 분할 반복 절차를 옮겼다.
합성 방식 네 가지는 생성 모델을 흉내 낸 것이다. 실제 모델을 돌리지 않는 이유는
위험도 지표가 '어떤 성질의 합성데이터에 어떻게 반응하는가'만 보면 되기 때문이다.
"""
import random
import statistics

SEED = 20261003
N_RECORDS = 300
N_SPLITS = 30
CAP_THRESHOLD = 0.7
JOBS = ["교사", "개발자", "간호사", "영업"]
BASE_INCOME = {"교사": 4.0, "개발자": 5.0, "간호사": 3.8, "영업": 4.4}  # 단위: 천만 원


def draw_person(rng):
    age = rng.randint(25, 59)
    job = rng.choice(JOBS)
    sex = rng.choice(["남", "여"])
    # 나이와 소득에 상관을 넣어야 '주변분포만 맞춘 합성'이 무엇을 잃는지 보인다
    income = round(BASE_INCOME[job] + 0.06 * (age - 25) + rng.gauss(0, 0.5), 1)
    return (age, job, sex, income)


def quasi_id(rec):
    return (rec[0] // 10 * 10, rec[1], rec[2])  # 연령대·직업·성별


def sensitive(rec):
    income = rec[3]
    return "4천 미만" if income < 4 else ("6천 이상" if income >= 6 else "4천~6천")


def gower(a, b, age_range, income_range):
    # 수치형은 범위로 나눈 차이, 범주형은 불일치 여부. 안내서가 예로 든 가워 거리다
    return (abs(a[0] - b[0]) / age_range + (a[1] != b[1]) + (a[2] != b[2])
            + abs(a[3] - b[3]) / income_range) / 4


def single_out_risk(synth, orig):
    orig_set = set(orig)
    return sum(rec in orig_set for rec in synth) / len(synth)


def cap_scores(synth, orig):
    """원본 레코드마다: 준식별자가 같은 합성 레코드 중 민감정보까지 같은 비율."""
    groups = {}
    for rec in synth:
        groups.setdefault(quasi_id(rec), []).append(sensitive(rec))
    scores = []
    for rec in orig:
        matched = groups.get(quasi_id(rec))
        if matched:  # 같은 준식별자가 합성에 없으면 공격자가 얻을 것이 없다
            scores.append(matched.count(sensitive(rec)) / len(matched))
    return scores


def inference_risk(synth, orig):
    """합성→가장 가까운 원본 거리(dS)가 그 원본→다른 원본 거리(dO)보다 작은 비율."""
    ages = [r[0] for r in orig]
    incomes = [r[3] for r in orig]
    age_range = max(ages) - min(ages)
    income_range = max(incomes) - min(incomes)
    nearest_other = []
    for i, r in enumerate(orig):
        nearest_other.append(min(gower(r, o, age_range, income_range)
                                 for j, o in enumerate(orig) if j != i))
    closer = counted = 0
    for s in synth:
        dists = [gower(s, o, age_range, income_range) for o in orig]
        d_s = min(dists)
        if d_s == 0:  # 원본과 같은 레코드는 구별 위험도가 따로 센다
            continue
        counted += 1
        closer += d_s < nearest_other[dists.index(d_s)]
    return closer / counted if counted else float("nan")


def corr_gap(synth, orig):
    """2차원 관계 유사성: 나이–소득 상관계수가 원본과 얼마나 벌어졌나."""
    def corr(data):
        return statistics.correlation([r[0] for r in data], [r[3] for r in data])
    return abs(corr(synth) - corr(orig))


def job_mean_gap(synth, orig):
    """과업 관점 유용성 대용: 직업별 평균 소득 차이 중 가장 큰 값 (천만 원)."""
    def means(data):
        return {j: statistics.mean([r[3] for r in data if r[1] == j]) for j in JOBS}
    ms, mo = means(synth), means(orig)
    return max(abs(ms[j] - mo[j]) for j in JOBS)


def make_synthetic_sets(orig, rng):
    overfit = []
    for rec in orig:
        if rng.random() < 0.4:  # 생성 모델이 학습 레코드를 그대로 다시 낸 경우
            overfit.append(rec)
        else:                   # 소득만 0.1 흔든 '거의 같은' 레코드
            overfit.append((rec[0], rec[1], rec[2], round(rec[3] + rng.choice([-0.1, 0.1]), 1)))
    fresh = [draw_person(rng) for _ in orig]  # 모집단을 완벽히 배운 모델의 출력과 같다
    columns = [list(col) for col in zip(*orig)]
    for col in columns:
        rng.shuffle(col)  # 열마다 따로 섞으면 주변분포는 같고 열 사이 관계는 끊긴다
    marginal = list(zip(*columns))
    noise = [(rng.randint(25, 59), rng.choice(JOBS), rng.choice(["남", "여"]),
              round(rng.uniform(2.0, 9.0), 1)) for _ in orig]
    return {"과적합": overfit, "새 표본": fresh, "주변분포만": marginal, "균등 잡음": noise}


def evaluate(name, synth, orig):
    caps = cap_scores(synth, orig)
    cap_mean = statistics.mean(caps) if caps else 0.0
    cap_over = sum(c > CAP_THRESHOLD for c in caps) / len(orig)
    print(f"{name:<6} | {single_out_risk(synth, orig):6.3f} | {cap_mean:6.3f} | "
          f"{cap_over:8.3f} | {inference_risk(synth, orig):6.3f} | "
          f"{corr_gap(synth, orig):7.3f} | {job_mean_gap(synth, orig):8.3f}")


def main():
    rng = random.Random(SEED)
    orig = [draw_person(rng) for _ in range(N_RECORDS)]
    print(f"[1] 원본 {N_RECORDS}건 — (나이, 직업, 성별, 연소득 천만 원). 앞 5건")
    for rec in orig[:5]:
        print("   ", rec, "준식별자", quasi_id(rec), "민감정보", sensitive(rec))
    print()
    print("[2] 합성 방식별 위험도와 유용성 (위험도는 0에 가까울수록 안전, 유용성 차이는 0에 가까울수록 좋다)")
    print("방식   |   구별 | CAP평균 | CAP>0.7 |   추론 | 상관차이 | 직업평균차")
    synth_sets = make_synthetic_sets(orig, rng)
    for name, synth in synth_sets.items():
        evaluate(name, synth, orig)
    print()

    print(f"[3] 추론 위험도 임계값 — 원본을 50:50으로 나눠 {N_SPLITS}회 측정한 분포 (부록4 절차)")
    values = []
    for _ in range(N_SPLITS):
        shuffled = orig[:]
        rng.shuffle(shuffled)
        half = len(shuffled) // 2
        values.append(inference_risk(shuffled[half:], shuffled[:half]))
    values.sort()
    p95 = values[int(0.95 * len(values)) - 1]
    print(f"    최소 {values[0]:.3f}  중앙 {statistics.median(values):.3f}  "
          f"최대 {values[-1]:.3f}  95% 분위수(임계값) {p95:.3f}")
    print()

    print("[4] 과적합 세트에서 원본과 같은 레코드를 지운 뒤")
    cleaned = [r for r in synth_sets["과적합"] if r not in set(orig)]
    print(f"    남은 레코드 {len(cleaned)}건")
    print("방식   |   구별 | CAP평균 | CAP>0.7 |   추론 | 상관차이 | 직업평균차")
    evaluate("삭제후", cleaned, orig)


if __name__ == "__main__":
    main()
