"""같은 평점 행렬 하나에 세 접근을 적용해 무엇이 달라지는지 확인한다.

- 사용자 기반: 사용자 간 상관계수 → 평균 편차의 가중평균 (GroupLens, CSCW 1994)
- 아이템 기반: 코사인 / 상관 / 조정 코사인 → 가중합 (Sarwar et al., WWW10 2001)
- 행렬 분해: 편향 포함 모델을 SGD 로 학습 (Koren et al., IEEE Computer 2009)
"""

import math
import platform
import random

USERS = ["u1", "u2", "u3", "u4", "u5", "u6"]
ITEMS = ["i1", "i2", "i3", "i4", "i5"]

# 0 은 미평가. u1 의 i5 를 예측 대상으로 비워 두었다.
# u1·u2·u4 는 i1~i3 을 좋아하고 i4 를 싫어한다. u3·u5 는 취향이 반대다.
# u6 은 u1 과 선호 순서가 같지만 전체적으로 낮게 주는 사용자다 (평점 척도 차이).
RATINGS = {
    "u1": {"i1": 5, "i2": 4, "i3": 5, "i4": 1, "i5": 0},
    "u2": {"i1": 4, "i2": 3, "i3": 4, "i4": 1, "i5": 2},
    "u3": {"i1": 2, "i2": 1, "i3": 2, "i4": 5, "i5": 4},
    "u4": {"i1": 5, "i2": 5, "i3": 4, "i4": 2, "i5": 1},
    "u5": {"i1": 1, "i2": 2, "i3": 1, "i4": 4, "i5": 5},
    "u6": {"i1": 3, "i2": 2, "i3": 3, "i4": 1, "i5": 2},
}

TARGET_USER = "u1"
TARGET_ITEM = "i5"


def rated_items(user):
    return [i for i in ITEMS if RATINGS[user][i] > 0]


def user_mean(user):
    values = [RATINGS[user][i] for i in rated_items(user)]
    return sum(values) / len(values)


def print_environment():
    print("환경")
    print(f"  Python {platform.python_version()} ({platform.system()})")
    print("  외부 라이브러리 없음 — 표준 라이브러리만 사용")
    print()


def print_matrix():
    print("[0] 평점 행렬 — 1~5점, '·' 는 미평가")
    print("       " + "".join(f"{i:>5}" for i in ITEMS) + "   평균")
    for u in USERS:
        cells = []
        for i in ITEMS:
            value = RATINGS[u][i]
            cells.append(f"{value:>5}" if value else f"{'·':>5}")
        print(f"  {u:<5}" + "".join(cells) + f"{user_mean(u):>7.2f}")
    print(f"\n  예측 대상: {TARGET_USER} 의 {TARGET_ITEM}")
    print()


def pearson_users(a, b):
    """두 사용자가 공통으로 평가한 아이템만으로 상관계수를 낸다."""
    common = [i for i in ITEMS if RATINGS[a][i] > 0 and RATINGS[b][i] > 0]
    if len(common) < 2:
        return None, common
    mean_a, mean_b = user_mean(a), user_mean(b)
    num = sum((RATINGS[a][i] - mean_a) * (RATINGS[b][i] - mean_b) for i in common)
    den_a = math.sqrt(sum((RATINGS[a][i] - mean_a) ** 2 for i in common))
    den_b = math.sqrt(sum((RATINGS[b][i] - mean_b) ** 2 for i in common))
    if den_a == 0 or den_b == 0:
        return None, common
    return num / (den_a * den_b), common


def user_based_prediction():
    print("[1] 사용자 기반 — 상관계수와 평균 편차의 가중평균")
    mean_target = user_mean(TARGET_USER)
    weights = {}
    for other in USERS:
        if other == TARGET_USER or RATINGS[other][TARGET_ITEM] == 0:
            continue
        w, common = pearson_users(TARGET_USER, other)
        weights[other] = w
        deviation = RATINGS[other][TARGET_ITEM] - user_mean(other)
        print(
            f"  {other}  공통 {len(common)}개  상관 {w:+.3f}"
            f"  {TARGET_ITEM} 평점 {RATINGS[other][TARGET_ITEM]}"
            f"  평균 {user_mean(other):.2f}  편차 {deviation:+.2f}"
        )
    num = sum(w * (RATINGS[o][TARGET_ITEM] - user_mean(o)) for o, w in weights.items())
    den = sum(abs(w) for w in weights.values())
    prediction = mean_target + num / den
    print(f"\n  {TARGET_USER} 평균 {mean_target:.2f} + ({num:+.3f} / {den:.3f})"
          f" = {prediction:.3f}")
    print()
    return prediction


def cosine_items(a, b):
    common = [u for u in USERS if RATINGS[u][a] > 0 and RATINGS[u][b] > 0]
    num = sum(RATINGS[u][a] * RATINGS[u][b] for u in common)
    den_a = math.sqrt(sum(RATINGS[u][a] ** 2 for u in common))
    den_b = math.sqrt(sum(RATINGS[u][b] ** 2 for u in common))
    return num / (den_a * den_b)


def correlation_items(a, b):
    """공통 평가자만으로 낸 상관계수. 아이템 평균을 뺀다."""
    common = [u for u in USERS if RATINGS[u][a] > 0 and RATINGS[u][b] > 0]
    mean_a = sum(RATINGS[u][a] for u in common) / len(common)
    mean_b = sum(RATINGS[u][b] for u in common) / len(common)
    num = sum((RATINGS[u][a] - mean_a) * (RATINGS[u][b] - mean_b) for u in common)
    den_a = math.sqrt(sum((RATINGS[u][a] - mean_a) ** 2 for u in common))
    den_b = math.sqrt(sum((RATINGS[u][b] - mean_b) ** 2 for u in common))
    return num / (den_a * den_b)


def adjusted_cosine_items(a, b):
    """사용자 평균을 빼서 평점 척도 차이를 상쇄한다."""
    common = [u for u in USERS if RATINGS[u][a] > 0 and RATINGS[u][b] > 0]
    num = sum(
        (RATINGS[u][a] - user_mean(u)) * (RATINGS[u][b] - user_mean(u)) for u in common
    )
    den_a = math.sqrt(sum((RATINGS[u][a] - user_mean(u)) ** 2 for u in common))
    den_b = math.sqrt(sum((RATINGS[u][b] - user_mean(u)) ** 2 for u in common))
    return num / (den_a * den_b)


def compare_similarities():
    print("[2] 아이템 유사도 세 가지 — 같은 쌍에 세 식을 적용")
    print(f"  {'쌍':<10}{'코사인':>10}{'상관':>10}{'조정 코사인':>14}")
    pairs = [("i1", "i3"), ("i1", "i2"), ("i1", "i5"), ("i1", "i4"), ("i4", "i5")]
    for a, b in pairs:
        print(
            f"  {a}-{b:<7}{cosine_items(a, b):>10.3f}"
            f"{correlation_items(a, b):>10.3f}"
            f"{adjusted_cosine_items(a, b):>14.3f}"
        )
    print()


def item_based_prediction():
    print("[3] 아이템 기반 — 조정 코사인 + 가중합")
    sims = {o: adjusted_cosine_items(TARGET_ITEM, o)
            for o in rated_items(TARGET_USER)}
    for other, sim in sims.items():
        print(
            f"  sim({TARGET_ITEM},{other}) = {sim:+.3f}"
            f"  × 평점 {RATINGS[TARGET_USER][other]}"
            f"  = {sim * RATINGS[TARGET_USER][other]:+.3f}"
        )

    print("\n  (가) 원 논문 식 그대로 — 분모는 유사도 절댓값의 합")
    num = sum(s * RATINGS[TARGET_USER][o] for o, s in sims.items())
    den = sum(abs(s) for s in sims.values())
    raw = num / den
    print(f"      ({num:+.3f}) / ({den:.3f}) = {raw:.3f}   ← 1~5 범위 밖")

    print("\n  (나) 유사도가 양수인 이웃만 남긴다")
    positive = {o: s for o, s in sims.items() if s > 0}
    num_p = sum(s * RATINGS[TARGET_USER][o] for o, s in positive.items())
    den_p = sum(positive.values())
    pos = num_p / den_p
    print(f"      이웃 {len(positive)}개 {list(positive)}"
          f"  ({num_p:+.3f}) / ({den_p:.3f}) = {pos:.3f}")

    print("\n  (다) 사용자 평균을 기준으로 편차를 더한다 (논문 식이 아니다)")
    mean_target = user_mean(TARGET_USER)
    num_c = sum(s * (RATINGS[TARGET_USER][o] - mean_target) for o, s in sims.items())
    centered = mean_target + num_c / den
    print(f"      {mean_target:.2f} + ({num_c:+.3f} / {den:.3f}) = {centered:.3f}")
    print()
    return raw, pos, centered


def matrix_factorization(factors=2, steps=4000, rate=0.02, reg=0.05, seed=20261025):
    """편향 포함 모델을 SGD 로 학습한다 (Koren et al. 식 4·5)."""
    rng = random.Random(seed)
    known = [(u, i) for u in USERS for i in ITEMS if RATINGS[u][i] > 0]
    mu = sum(RATINGS[u][i] for u, i in known) / len(known)
    p = {u: [rng.uniform(-0.1, 0.1) for _ in range(factors)] for u in USERS}
    q = {i: [rng.uniform(-0.1, 0.1) for _ in range(factors)] for i in ITEMS}
    bu = {u: 0.0 for u in USERS}
    bi = {i: 0.0 for i in ITEMS}

    for _ in range(steps):
        rng.shuffle(known)
        for u, i in known:
            pred = mu + bu[u] + bi[i] + sum(p[u][f] * q[i][f] for f in range(factors))
            err = RATINGS[u][i] - pred
            bu[u] += rate * (err - reg * bu[u])
            bi[i] += rate * (err - reg * bi[i])
            for f in range(factors):
                pu, qi = p[u][f], q[i][f]
                p[u][f] += rate * (err * qi - reg * pu)
                q[i][f] += rate * (err * pu - reg * qi)

    rmse = math.sqrt(
        sum(
            (RATINGS[u][i] - (mu + bu[u] + bi[i]
                              + sum(p[u][f] * q[i][f] for f in range(factors)))) ** 2
            for u, i in known
        )
        / len(known)
    )
    print(f"[4] 행렬 분해 — 잠재요인 {factors}개, SGD {steps}회, 정규화 λ={reg}")
    print(f"  전체 평균 μ = {mu:.3f}   학습 평점 {len(known)}개   학습 RMSE {rmse:.4f}")
    print(f"\n  사용자 편향·요인")
    for u in USERS:
        vec = " ".join(f"{p[u][f]:+.3f}" for f in range(factors))
        print(f"    {u}  b_u {bu[u]:+.3f}   p_u [{vec}]")
    print(f"\n  아이템 편향·요인")
    for i in ITEMS:
        vec = " ".join(f"{q[i][f]:+.3f}" for f in range(factors))
        print(f"    {i}  b_i {bi[i]:+.3f}   q_i [{vec}]")

    interaction = sum(p[TARGET_USER][f] * q[TARGET_ITEM][f] for f in range(factors))
    prediction = mu + bu[TARGET_USER] + bi[TARGET_ITEM] + interaction
    print(
        f"\n  {TARGET_USER}·{TARGET_ITEM} = μ {mu:.3f} + b_u {bu[TARGET_USER]:+.3f}"
        f" + b_i {bi[TARGET_ITEM]:+.3f} + q·p {interaction:+.3f} = {prediction:.3f}"
    )
    print()
    return prediction


def sparsity_report():
    print("[5] 희소성 — 빈칸이 늘면 공통 평가자가 먼저 사라진다")
    filled = sum(1 for u in USERS for i in ITEMS if RATINGS[u][i] > 0)
    total = len(USERS) * len(ITEMS)
    print(f"  채워진 칸 {filled}/{total} = {filled / total * 100:.1f}%")
    for a, b in [("i1", "i3"), ("i2", "i5"), ("i4", "i5")]:
        common = [u for u in USERS if RATINGS[u][a] > 0 and RATINGS[u][b] > 0]
        print(f"  {a}-{b} 공통 평가자 {len(common)}명: {', '.join(common)}")
    print()


def main():
    print_environment()
    print_matrix()
    user_pred = user_based_prediction()
    compare_similarities()
    raw, pos, centered = item_based_prediction()
    mf_pred = matrix_factorization()
    sparsity_report()

    print("[6] 세 접근이 같은 칸에 낸 값")
    print(f"  사용자 기반             {user_pred:.3f}")
    print(f"  아이템 기반 (가) 원 식  {raw:.3f}")
    print(f"  아이템 기반 (나) 양수만 {pos:.3f}")
    print(f"  아이템 기반 (다) 편차형 {centered:.3f}")
    print(f"  행렬 분해               {mf_pred:.3f}")


if __name__ == "__main__":
    main()
