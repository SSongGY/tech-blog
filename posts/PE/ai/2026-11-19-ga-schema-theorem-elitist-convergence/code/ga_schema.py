"""스키마 정리의 하한과 Rudolph(1994)의 수렴 결과를 작은 예로 검산한다.

1부: 길이 5 염색체 6개 집단에서 스키마 하나의 기대 개수 하한을 손으로 계산하고,
     한 세대를 20만 번 돌려 실제 평균 개수가 그 하한 이상인지 본다.
2부: 길이 2, 집단 2의 기본형 GA를 유한 마르코프 체인으로 정확히 계산해,
     기본형은 최적해 보유 확률이 1로 가지 않고 최고 해 보존 변형은 1로 간다는 것을 본다.
"""
import random
import platform

# ---------- 1부: 스키마 정리 ----------

POPULATION = ["10110", "11000", "10100", "01110", "00011", "11010"]
SCHEMA = "1***0"
PC, PM = 0.6, 0.01
TRIALS = 200_000


def fitness(chrom):
    # 이진수 값 그대로를 적합도로 쓴다. 손으로 검산하기 쉽게 하려는 것이다
    return int(chrom, 2)


def matches(chrom, schema):
    return all(s == "*" or s == c for s, c in zip(schema, chrom))


def order(schema):
    return sum(1 for s in schema if s != "*")


def defining_length(schema):
    fixed = [i for i, s in enumerate(schema) if s != "*"]
    return fixed[-1] - fixed[0]


def roulette(pop, fits, rng):
    pick = rng.random() * sum(fits)
    acc = 0.0
    for chrom, f in zip(pop, fits):
        acc += f
        if pick < acc:
            return chrom
    return pop[-1]


def one_generation(pop, rng):
    fits = [fitness(c) for c in pop]
    length = len(pop[0])
    nxt = []
    while len(nxt) < len(pop):
        a, b = roulette(pop, fits, rng), roulette(pop, fits, rng)
        if rng.random() < PC:
            cut = rng.randint(1, length - 1)  # 자를 수 있는 자리는 length-1곳이다
            a, b = a[:cut] + b[cut:], b[:cut] + a[cut:]
        for child in (a, b):
            child = "".join(("1" if g == "0" else "0") if rng.random() < PM else g
                            for g in child)
            nxt.append(child)
    return nxt[: len(pop)]


def part1():
    print("=== part 1: schema theorem lower bound ===")
    fits = [fitness(c) for c in POPULATION]
    f_avg = sum(fits) / len(fits)
    print(f"  no  chromosome  fitness  in {SCHEMA}")
    for i, (c, f) in enumerate(zip(POPULATION, fits)):
        print(f"  {i:>2}  {c:>10}  {f:>7}  {'yes' if matches(c, SCHEMA) else 'no'}")
    members = [f for c, f in zip(POPULATION, fits) if matches(c, SCHEMA)]
    m_t = len(members)
    f_h = sum(members) / m_t
    o_h, d_h, length = order(SCHEMA), defining_length(SCHEMA), len(SCHEMA)
    survive_x = 1 - PC * d_h / (length - 1)
    survive_m = 1 - o_h * PM
    bound = m_t * f_h / f_avg * survive_x * survive_m
    print(f"  m(H,t) = {m_t}, f(H) = {f_h:.4f}, f_avg = {f_avg:.4f}")
    print(f"  o(H) = {o_h}, delta(H) = {d_h}, l = {length}, pc = {PC}, pm = {PM}")
    print(f"  selection term  m*f(H)/f_avg            = {m_t * f_h / f_avg:.4f}")
    print(f"  crossover term  1 - pc*delta/(l-1)       = {survive_x:.4f}")
    print(f"  mutation term   1 - o*pm                 = {survive_m:.4f}")
    print(f"  lower bound E[m(H,t+1)] >=               {bound:.4f}")

    rng = random.Random(0)
    total = 0
    for _ in range(TRIALS):
        total += sum(1 for c in one_generation(POPULATION, rng) if matches(c, SCHEMA))
    print(f"  simulated mean m(H,t+1) over {TRIALS} runs = {total / TRIALS:.4f}")
    print()


# ---------- 2부: Rudolph 수렴 결과 ----------

BITS = 2
N = 2
F = {"00": 1, "01": 2, "10": 2, "11": 4}   # 최적해는 11 하나
INDIVIDUALS = list(F)
STATES = [(a, b) for a in INDIVIDUALS for b in INDIVIDUALS]
F_STAR = max(F.values())


def mutate_prob(src, dst, pm):
    flips = sum(1 for s, d in zip(src, dst) if s != d)
    return pm ** flips * (1 - pm) ** (BITS - flips)


def transition(pm):
    """P = M*S (교차 확률 0). 정리 3은 pc가 [0,1] 어디든 성립하므로 0을 써도 된다."""
    m_mat = {i: {j: mutate_prob(i[0], j[0], pm) * mutate_prob(i[1], j[1], pm)
                 for j in STATES} for i in STATES}
    s_mat = {}
    for i in STATES:
        total = sum(F[x] for x in i)
        pick = {}
        for x in i:
            pick[x] = pick.get(x, 0) + F[x] / total
        s_mat[i] = {j: pick.get(j[0], 0) * pick.get(j[1], 0) for j in STATES}
    return {i: {j: sum(m_mat[i][k] * s_mat[k][j] for k in STATES) for j in STATES}
            for i in STATES}


def best(state):
    return max(F[x] for x in state)


def run_cga(p_mat, steps):
    dist = {s: 1 / len(STATES) for s in STATES}
    out = {}
    for t in range(1, steps + 1):
        dist = {j: sum(dist[i] * p_mat[i][j] for i in STATES) for j in STATES}
        out[t] = sum(p for s, p in dist.items() if best(s) == F_STAR)
    return out


def run_elitist(p_mat, steps):
    # 정리 6의 구성: 진화에 참여하지 않는 슈퍼 개체가 선택 뒤 지금까지의 최고 해를 기억한다
    dist = {}
    for s in STATES:
        sup = max(s, key=lambda x: F[x])
        dist[(sup, s)] = dist.get((sup, s), 0) + 1 / len(STATES)
    out = {}
    for t in range(1, steps + 1):
        nxt = {}
        for (sup, s), p in dist.items():
            for j, q in p_mat[s].items():
                if q == 0:
                    continue
                cand = max([sup, *j], key=lambda x: F[x])
                nxt[(cand, j)] = nxt.get((cand, j), 0) + p * q
        dist = nxt
        out[t] = sum(p for (sup, _), p in dist.items() if F[sup] == F_STAR)
    return out


def part2():
    print("=== part 2: Rudolph 1994, exact Markov chain (l=2, n=2, pc=0) ===")
    print(f"  f = {F}, states = {len(STATES)}")
    checkpoints = [1, 5, 10, 50, 200, 1000]
    print("  P{best fitness in population = f*} at step t")
    print("  pm    variant     " + "".join(f"{'t=' + str(t):>9}" for t in checkpoints))
    for pm in (0.05, 0.2):
        p_mat = transition(pm)
        positive = all(v > 0 for row in p_mat.values() for v in row.values())
        cga = run_cga(p_mat, checkpoints[-1])
        eli = run_elitist(p_mat, checkpoints[-1])
        print(f"  {pm:<5} canonical   " + "".join(f"{cga[t]:>9.4f}" for t in checkpoints))
        print(f"  {pm:<5} keep-best   " + "".join(f"{eli[t]:>9.4f}" for t in checkpoints))
        print(f"        transition matrix all entries > 0: {positive}")
    print()


if __name__ == "__main__":
    print(f"Python {platform.python_version()}")
    print()
    part1()
    part2()
