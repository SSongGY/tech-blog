"""유전 알고리즘 검산 — 0/1 배낭 문제.

1부: 개체 6개로 한 세대를 손으로 따라갈 수 있게 찍는다
     (평가 → 룰렛 선택 → 1점 교차 → 비트 변이 → 다음 세대).
2부: 같은 문제를 네 가지 설정으로 50번씩 돌려 최적화 방법의 효과를 비교한다.
"""
import itertools
import random
import statistics

WEIGHTS = [12, 7, 11, 8, 9, 6, 14, 5, 10, 3]
VALUES = [24, 13, 23, 15, 16, 11, 28, 8, 19, 4]
CAPACITY = 40
PENALTY = 5  # 초과 무게 1당 깎는 가치. 제약을 버리지 않고 적합도에 녹이는 방식
GENE_COUNT = len(WEIGHTS)


def weight_of(chromosome):
    return sum(w for w, bit in zip(WEIGHTS, chromosome) if bit)


def value_of(chromosome):
    return sum(v for v, bit in zip(VALUES, chromosome) if bit)


def fitness(chromosome):
    excess = max(0, weight_of(chromosome) - CAPACITY)
    # 룰렛 선택은 음수 적합도를 다룰 수 없으므로 0에서 자른다
    return max(0, value_of(chromosome) - PENALTY * excess)


def to_text(chromosome):
    return "".join(str(bit) for bit in chromosome)


def brute_force_optimum():
    best = max(itertools.product([0, 1], repeat=GENE_COUNT), key=fitness)
    return list(best), fitness(best)


def roulette_select(population, scores, rng):
    total = sum(scores)
    if total == 0:
        return list(rng.choice(population))
    pick = rng.uniform(0, total)
    running = 0.0
    for chromosome, score in zip(population, scores):
        running += score
        if running >= pick:
            return list(chromosome)
    return list(population[-1])


def tournament_select(population, scores, rng, size=2):
    contenders = rng.sample(range(len(population)), size)
    winner = max(contenders, key=lambda i: scores[i])
    return list(population[winner])


def one_point_crossover(parent_a, parent_b, rng, crossover_rate):
    if rng.random() >= crossover_rate:
        return list(parent_a), list(parent_b), None
    point = rng.randint(1, GENE_COUNT - 1)
    child_a = parent_a[:point] + parent_b[point:]
    child_b = parent_b[:point] + parent_a[point:]
    return child_a, child_b, point


def bit_flip_mutation(chromosome, rng, mutation_rate):
    flipped = []
    for i in range(GENE_COUNT):
        if rng.random() < mutation_rate:
            chromosome[i] ^= 1
            flipped.append(i)
    return flipped


def local_search(chromosome):
    """한 비트씩 뒤집어 나아지면 받아들인다. 더 나아질 곳이 없을 때까지."""
    current = list(chromosome)
    evaluations = 0
    improved = True
    while improved:
        improved = False
        base = fitness(current)
        for i in range(GENE_COUNT):
            current[i] ^= 1
            evaluations += 1
            if fitness(current) > base:
                improved = True
                break
            current[i] ^= 1
    return current, evaluations


def print_population(title, population):
    scores = [fitness(c) for c in population]
    total = sum(scores)
    print(title)
    print("  no  chromosome  weight  value  fitness  roulette")
    for i, (chromosome, score) in enumerate(zip(population, scores)):
        share = score / total if total else 0
        print(f"  {i:>2}  {to_text(chromosome)}  {weight_of(chromosome):>6}"
              f"  {value_of(chromosome):>5}  {score:>7}  {share:>8.3f}")
    print(f"  sum of fitness = {total}, best = {max(scores)}")
    return scores


def walk_one_generation():
    rng = random.Random(7)
    population = [[rng.randint(0, 1) for _ in range(GENE_COUNT)] for _ in range(6)]
    scores = print_population("[gen 0] initial population", population)

    print("\n[selection] roulette wheel, 6 picks")
    parents = []
    for _ in range(6):
        chosen = roulette_select(population, scores, rng)
        parents.append(chosen)
        print(f"  picked {to_text(chosen)} (fitness {fitness(chosen)})")

    print("\n[crossover] one-point, pc = 0.9")
    offspring = []
    for a, b in zip(parents[0::2], parents[1::2]):
        child_a, child_b, point = one_point_crossover(a, b, rng, 0.9)
        where = "no crossover" if point is None else f"cut after gene {point}"
        print(f"  {to_text(a)} x {to_text(b)} -> {to_text(child_a)}, {to_text(child_b)} ({where})")
        offspring += [child_a, child_b]

    print("\n[mutation] bit flip, pm = 0.1 per gene")
    for child in offspring:
        before = to_text(child)
        flipped = bit_flip_mutation(child, rng, 0.1)
        print(f"  {before} -> {to_text(child)} flipped {flipped if flipped else '-'}")

    print()
    print_population("[gen 1] next population", offspring)


def run_ga(seed, selection, elitism, memetic,
           population_size=20, generations=40, crossover_rate=0.9, mutation_rate=0.1):
    rng = random.Random(seed)
    population = [[rng.randint(0, 1) for _ in range(GENE_COUNT)]
                  for _ in range(population_size)]
    evaluations = population_size
    best_ever = max(fitness(c) for c in population)
    history = []
    for _ in range(generations):
        scores = [fitness(c) for c in population]
        history.append(max(scores))
        elite = list(population[scores.index(max(scores))])
        offspring = []
        while len(offspring) < population_size:
            a = selection(population, scores, rng)
            b = selection(population, scores, rng)
            child_a, child_b, _ = one_point_crossover(a, b, rng, crossover_rate)
            for child in (child_a, child_b):
                bit_flip_mutation(child, rng, mutation_rate)
                if memetic:
                    child, used = local_search(child)
                    evaluations += used
                offspring.append(child)
        offspring = offspring[:population_size]
        evaluations += population_size
        if elitism:
            # 가장 못한 자식 자리를 앞 세대 최고 개체에게 내준다
            worst = min(range(population_size), key=lambda i: fitness(offspring[i]))
            offspring[worst] = elite
        population = offspring
        best_ever = max(best_ever, max(fitness(c) for c in population))
    final_best = max(fitness(c) for c in population)
    history.append(final_best)
    return final_best, best_ever, evaluations, history


def compare_settings(optimum_fitness, runs=50):
    settings = [
        ("A roulette", roulette_select, False, False),
        ("B roulette+elite", roulette_select, True, False),
        ("C tournament+elite", tournament_select, True, False),
        ("D C+local search", tournament_select, True, True),
    ]
    checkpoints = [0, 5, 10, 20, 40]
    print(f"population 20, generations 40, pc 0.9, pm 0.1, {runs} runs (seed 0..{runs - 1})")
    print("setting              final=opt  mean final  lost best  mean evals")
    curves = {}
    for name, selection, elitism, memetic in settings:
        results = [run_ga(seed, selection, elitism, memetic) for seed in range(runs)]
        hits = sum(1 for final, _, _, _ in results if final == optimum_fitness)
        mean_final = statistics.mean(final for final, _, _, _ in results)
        lost = sum(1 for final, ever, _, _ in results if final < ever)
        mean_evals = statistics.mean(evals for _, _, evals, _ in results)
        print(f"{name:<20} {hits:>5}/{runs}  {mean_final:>10.1f}  {lost:>9}  {mean_evals:>10.0f}")
        curves[name] = [statistics.mean(r[3][g] for r in results) for g in checkpoints]

    print("\nmean best fitness by generation")
    print("setting             " + "".join(f"  gen{g:<4}" for g in checkpoints))
    for name, curve in curves.items():
        print(f"{name:<20}" + "".join(f"  {v:>7.1f}" for v in curve))


def main():
    print("items (weight, value):", list(zip(WEIGHTS, VALUES)), "capacity:", CAPACITY)
    best, best_fitness = brute_force_optimum()
    print(f"brute force over 2^{GENE_COUNT} = {2 ** GENE_COUNT} candidates:"
          f" {to_text(best)} weight {weight_of(best)} value {best_fitness}")

    print("\n=== part 1: one generation by hand ===\n")
    walk_one_generation()

    print("\n=== part 2: optimization settings compared ===\n")
    compare_settings(best_fitness)


if __name__ == "__main__":
    main()
