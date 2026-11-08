"""신뢰도·가용성 계산과 몬테카를로 검산.

1) 지수 분포 R(t) = exp(-λt) — t = MTTF 에서 몇 % 가 살아남는가
2) NIST 8.1.8 의 구성 모델 4가지(직렬·병렬·r-out-of-n·대기)를 식으로 계산하고 시뮬레이션으로 맞춘다
3) 구성별 MTTF — 신뢰도 곡선을 적분해 구한다
4) 가용도 A = MTBF / (MTBF + MTTR) — 고장·수리를 번갈아 시뮬레이션해 맞춘다
5) 3계층 서비스(웹·WAS·DB)의 가용도와 연간 정지 시간
"""
import math
import random
from math import comb

SEED = 20261108
HOURS_PER_YEAR = 8760


def r_exp(failure_rate, t):
    return math.exp(-failure_rate * t)


def r_series(reliabilities):
    return math.prod(reliabilities)


def r_parallel(reliabilities):
    return 1 - math.prod(1 - r for r in reliabilities)


def r_k_of_n(r, k, n):
    """NIST 8.1.8.4 — 같은 부품 n 개 중 k 개 이상이 살아 있으면 동작."""
    return sum(comb(n, i) * r**i * (1 - r) ** (n - i) for i in range(k, n + 1))


def r_standby(failure_rate, t, spares=1):
    """NIST 8.1.8.5 — 완전 전환 대기, 지수 분포면 감마(얼랑) 분포의 생존 함수."""
    lt = failure_rate * t
    return math.exp(-lt) * sum(lt**i / math.factorial(i) for i in range(spares + 1))


def integrate(func, upper, steps=200_000):
    """사다리꼴 적분 — MTTF = ∫ R(t) dt."""
    h = upper / steps
    total = 0.5 * (func(0) + func(upper))
    for i in range(1, steps):
        total += func(i * h)
    return total * h


def section_exponential():
    print("== 1) 지수 분포: MTTF = 10,000 시간인 부품 ==")
    mttf = 10_000
    lam = 1 / mttf
    for t in (1_000, HOURS_PER_YEAR, mttf, 2 * mttf):
        print(f"  t = {t:>6,} h   R(t) = exp(-t/MTTF) = {r_exp(lam, t):.4f}")
    print(f"  중앙값(절반이 고장 나는 시각) = ln2 * MTTF = {math.log(2) * mttf:,.0f} h")
    print()


def simulate_lifetimes(rng, lam, n_parts, trials):
    return [[rng.expovariate(lam) for _ in range(n_parts)] for _ in range(trials)]


def section_structures(rng):
    print("== 2) 구성 모델 4가지: λ = 1/10,000 /h, 임무 시간 t = 8,760 h ==")
    lam, t, trials = 1 / 10_000, HOURS_PER_YEAR, 200_000
    r = r_exp(lam, t)
    samples = simulate_lifetimes(rng, lam, 3, trials)

    def frac(pred):
        return sum(1 for s in samples if pred(s)) / trials

    rows = [
        ("단일 부품", r, frac(lambda s: s[0] > t)),
        ("직렬 3개", r_series([r] * 3), frac(lambda s: min(s) > t)),
        ("병렬 2개", r_parallel([r] * 2), frac(lambda s: max(s[:2]) > t)),
        ("병렬 3개", r_parallel([r] * 3), frac(lambda s: max(s) > t)),
        ("2-out-of-3", r_k_of_n(r, 2, 3), frac(lambda s: sorted(s)[1] > t)),
        ("대기 1+1", r_standby(lam, t), frac(lambda s: s[0] + s[1] > t)),
    ]
    print(f"  {'구성':<12}| 식으로 계산 | 시뮬레이션({trials:,}회)")
    for name, formula, simulated in rows:
        print(f"  {name:<12}| {formula:11.4f} | {simulated:.4f}")
    print()
    print("  단일 부품과 2-out-of-3 — 임무 시간에 따라 앞뒤가 바뀐다")
    crossover = math.log(2) / lam
    for mission in (1_000, 3_000, crossover, HOURS_PER_YEAR, 15_000):
        single = r_exp(lam, mission)
        tmr = r_k_of_n(single, 2, 3)
        mark = "2oo3 가 높다" if tmr > single + 1e-12 else ("같다" if abs(tmr - single) < 1e-12 else "단일이 높다")
        print(f"    t = {mission:>8,.0f} h  단일 {single:.4f}  2oo3 {tmr:.4f}  {mark}")
    print()
    print("  NIST 8.1.8.5 대기 모델 예: MTTF 30개월, 임무 24개월")
    print(f"    단일 {r_exp(1 / 30, 24):.2f} · 대기 1+1 {r_standby(1 / 30, 24):.2f}")
    print()


def section_mttf():
    print("== 3) 구성별 MTTF — R(t) 를 0 부터 적분 (λ = 1/10,000 /h) ==")
    lam = 1 / 10_000
    upper = 300_000
    cases = [
        ("단일 부품", lambda x: r_exp(lam, x), "1/λ"),
        ("직렬 3개", lambda x: r_exp(lam, x) ** 3, "1/(3λ)"),
        ("병렬 2개", lambda x: r_parallel([r_exp(lam, x)] * 2), "1/λ + 1/(2λ)"),
        ("2-out-of-3", lambda x: r_k_of_n(r_exp(lam, x), 2, 3), "1/(3λ) + 1/(2λ)"),
        ("대기 1+1", lambda x: r_standby(lam, x), "2/λ"),
    ]
    closed = [1 / lam, 1 / (3 * lam), 1 / lam + 1 / (2 * lam), 1 / (3 * lam) + 1 / (2 * lam), 2 / lam]
    print(f"  {'구성':<12}| 적분값      | 닫힌 식            | 닫힌 식 값")
    for (name, func, expr), value in zip(cases, closed):
        print(f"  {name:<12}| {integrate(func, upper):10,.0f} | {expr:<18} | {value:10,.0f}")
    print()


def simulate_availability(rng, mtbf, mttr, horizon):
    """고장까지 지수(MTBF), 수리까지 지수(MTTR)를 번갈아 뽑아 가동 시간 비율을 잰다."""
    clock = up_time = 0.0
    failures = 0
    while clock < horizon:
        up = rng.expovariate(1 / mtbf)
        up_time += min(up, horizon - clock)
        clock += up
        if clock >= horizon:
            break
        failures += 1
        clock += rng.expovariate(1 / mttr)
    return up_time / horizon, failures


def section_availability(rng):
    print("== 4) 가용도 A = MTBF / (MTBF + MTTR) ==")
    horizon = 1_000 * HOURS_PER_YEAR
    print(f"  {'MTBF(h)':>8} | {'MTTR(h)':>7} | 식     A | 시뮬레이션 A | 고장 횟수")
    for mtbf, mttr in ((1_000, 1), (1_000, 10), (10_000, 10), (2_000, 2)):
        formula = mtbf / (mtbf + mttr)
        simulated, failures = simulate_availability(rng, mtbf, mttr, horizon)
        print(f"  {mtbf:>8,} | {mttr:>7} | {formula:.6f} | {simulated:.6f}     | {failures:,}")
    print("  -- MTBF : MTTR 비율이 같으면 A 가 같다 (고장 횟수는 10배까지 다르다)")
    print()
    print("  가용도와 연간 정지 시간 (8,760 h 기준)")
    for a in (0.99, 0.999, 0.9999, 0.99999):
        minutes = (1 - a) * HOURS_PER_YEAR * 60
        print(f"    {a * 100:.3f}% -> {minutes:9.2f} 분/년")
    print()


def section_service():
    print("== 5) 3계층 서비스: 웹 · WAS · DB 를 직렬로 잇는다 ==")
    a_web = 0.999
    a_was = 0.999
    a_db = 0.9995

    def show(label, value):
        minutes = (1 - value) * HOURS_PER_YEAR * 60
        print(f"  {label:<34} A = {value:.6f}  정지 {minutes:8.1f} 분/년")

    show("각 1대 (직렬)", r_series([a_web, a_was, a_db]))
    web2 = r_parallel([a_web] * 2)
    was2 = r_parallel([a_was] * 2)
    show("웹·WAS 2대씩, DB 1대", r_series([web2, was2, a_db]))
    db2 = r_parallel([a_db] * 2)
    show("웹·WAS·DB 모두 2대씩", r_series([web2, was2, db2]))
    show("  참고: 이중화한 웹 계층 하나", web2)
    print()


def main():
    rng = random.Random(SEED)
    print(f"random seed = {SEED}")
    print()
    section_exponential()
    section_structures(rng)
    section_mttf()
    section_availability(rng)
    section_service()


if __name__ == "__main__":
    main()
