"""같은 평가 예산에서 언덕 오르기·SA·타부 탐색·GA를 비교한다.

문제는 물건 20개 0/1 배낭이다. 최적해는 동적 계획법으로 정확히 구해 기준으로 쓴다.
네 기법 모두 적합도 평가를 BUDGET번만 쓰게 맞췄다. 세대 수나 반복 수로 맞추면
한 번에 이웃 20개를 보는 타부 탐색과 1개만 보는 SA가 같은 비용처럼 보이기 때문이다.
"""
import math
import platform
import random

N_ITEMS = 20
BUDGET = 2000
SEEDS = range(30)

gen = random.Random(42)
WEIGHTS = [gen.randint(5, 30) for _ in range(N_ITEMS)]
VALUES = [gen.randint(10, 60) for _ in range(N_ITEMS)]
CAPACITY = sum(WEIGHTS) // 2


def optimum():
    best = [0] * (CAPACITY + 1)
    for w, v in zip(WEIGHTS, VALUES):
        for c in range(CAPACITY, w - 1, -1):
            best[c] = max(best[c], best[c - w] + v)
    return best[CAPACITY]


class Counter:
    """평가 횟수를 세고 지금까지의 최고값을 기억한다. 예산을 넘기면 멈추게 한다."""

    def __init__(self):
        self.used = 0
        self.best = -math.inf

    def __call__(self, x):
        self.used += 1
        w = sum(wi for wi, xi in zip(WEIGHTS, x) if xi)
        v = sum(vi for vi, xi in zip(VALUES, x) if xi)
        # 용량을 넘으면 넘은 만큼 음수로 둔다. 실행 가능한 해는 항상 0 이상이라 이것보다 낫다
        f = v if w <= CAPACITY else -(w - CAPACITY)
        self.best = max(self.best, f)
        return f

    @property
    def left(self):
        return self.used < BUDGET


def flip(x, i):
    y = list(x)
    y[i] ^= 1
    return y


def hill_climb(rng, ev):
    x = [0] * N_ITEMS
    fx = ev(x)
    while ev.left:
        improved = False
        for i in rng.sample(range(N_ITEMS), N_ITEMS):
            if not ev.left:
                break
            y = flip(x, i)
            fy = ev(y)
            if fy > fx:
                x, fx, improved = y, fy, True
                break
        if not improved and ev.left:  # 지역 최적해: 탈출 수단이 없으므로 무작위 재시작
            x = [rng.randint(0, 1) for _ in range(N_ITEMS)]
            fx = ev(x)


def annealing(rng, ev, t0=50.0, t_end=0.5):
    x = [0] * N_ITEMS
    fx = ev(x)
    alpha = (t_end / t0) ** (1 / BUDGET)
    t = t0
    while ev.left:
        y = flip(x, rng.randrange(N_ITEMS))
        fy = ev(y)
        delta = fx - fy  # 최대화 문제이므로 나빠진 양
        if delta <= 0 or rng.random() < math.exp(-delta / t):
            x, fx = y, fy
        t *= alpha


def tabu(rng, ev, tenure=7):
    x = [0] * N_ITEMS
    ev(x)
    tabu_until = [0] * N_ITEMS
    it = 0
    while ev.left:
        it += 1
        cand = []
        for i in range(N_ITEMS):
            if not ev.left:
                break
            fy = ev(flip(x, i))
            # 열망 기준: 금지된 이동이라도 지금까지의 최고를 넘으면 허용한다
            if tabu_until[i] < it or fy >= ev.best:
                cand.append((fy, rng.random(), i))
        if not cand:
            continue
        _, _, i = max(cand)  # 나빠지더라도 허용된 이웃 중 가장 좋은 것으로 간다
        x = flip(x, i)
        tabu_until[i] = it + tenure


def genetic(rng, ev, pop_size=20, pm=1 / N_ITEMS, pc=0.9):
    pop = [[rng.randint(0, 1) for _ in range(N_ITEMS)] for _ in range(pop_size)]
    fit = [ev(p) for p in pop]
    while ev.left:
        elite_fit = max(fit)
        elite = pop[fit.index(elite_fit)]
        nxt = [elite]
        while len(nxt) < pop_size:
            a = max(rng.sample(range(pop_size), 2), key=lambda k: fit[k])
            b = max(rng.sample(range(pop_size), 2), key=lambda k: fit[k])
            c = list(pop[a])
            if rng.random() < pc:
                cut = rng.randint(1, N_ITEMS - 1)
                c = pop[a][:cut] + pop[b][cut:]
            c = [g ^ 1 if rng.random() < pm else g for g in c]
            nxt.append(c)
        pop = nxt
        # 엘리트는 이미 평가했으므로 다시 세지 않는다
        # 예산이 세대 중간에 끝나면 남은 자식은 평가하지 않는다
        fit = [elite_fit if k == 0 else (ev(p) if ev.left else -math.inf)
               for k, p in enumerate(pop)]


def acceptance_table():
    print("=== Metropolis acceptance probability exp(-delta/T) ===")
    temps = [50, 10, 2, 0.5]
    print("  delta " + "".join(f"{'T=' + str(t):>10}" for t in temps))
    for delta in (1, 5, 20):
        print(f"  {delta:>5} " + "".join(f"{math.exp(-delta / t):>10.5f}" for t in temps))
    print()


def main():
    print(f"Python {platform.python_version()}")
    print(f"items = {N_ITEMS}, capacity = {CAPACITY}")
    print(f"weights = {WEIGHTS}")
    print(f"values  = {VALUES}")
    opt = optimum()
    print(f"optimum by dynamic programming = {opt}")
    print()
    acceptance_table()
    print(f"=== same budget: {BUDGET} evaluations, {len(SEEDS)} seeds ===")
    print("  method              hit opt   mean best   worst   mean gap")
    for name, algo in [("hill climb+restart", hill_climb), ("simulated annealing", annealing),
                       ("tabu search", tabu), ("genetic algorithm", genetic)]:
        bests = []
        for s in SEEDS:
            ev = Counter()
            algo(random.Random(s), ev)
            assert ev.used <= BUDGET
            bests.append(ev.best)
        hit = sum(1 for b in bests if b == opt)
        mean = sum(bests) / len(bests)
        gap = (opt - mean) / opt * 100
        print(f"  {name:<19} {hit:>4}/{len(SEEDS)}  {mean:>10.2f}  {min(bests):>6}  {gap:>8.2f}%")


if __name__ == "__main__":
    main()
