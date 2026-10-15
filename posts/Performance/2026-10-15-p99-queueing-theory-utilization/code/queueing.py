"""이용률이 오를 때 응답시간과 p99 가 어떻게 벌어지는지 — 단일 서버 대기행렬 시뮬레이션.

Lindley 점화식 W(n+1) = max(0, W(n) + S(n) - A(n+1)) 하나로 FCFS 단일 서버를
그대로 돌린다. 도착 간격 A 는 지수분포(= 푸아송 도착)이고, 서비스 시간 S 의
분포는 바꿔 가며 쓴다.

난수는 시드를 고정했다. 같은 시드면 같은 숫자가 나온다.
"""

from __future__ import annotations

import math
import platform
import random
import statistics

MEAN_SERVICE_MS = 10.0     # 서비스 시간 평균 — 모든 실험에서 같다
REQUESTS = 400_000
WARMUP = 40_000            # 빈 큐에서 출발한 초기 구간은 버린다
SEED = 20261015
RULE = "=" * 72


def exponential(rng: random.Random) -> float:
    """C^2 = 1. M/M/1 의 M."""
    return rng.expovariate(1.0 / MEAN_SERVICE_MS)


def deterministic(_rng: random.Random) -> float:
    """C^2 = 0. 모든 요청이 정확히 같은 시간이 걸린다 (M/D/1 의 D)."""
    return MEAN_SERVICE_MS


def hyperexponential(rng: random.Random) -> float:
    """95%는 5ms, 5%는 105ms. 평균은 같은데 흔들림이 크다."""
    if rng.random() < 0.95:
        return rng.expovariate(1.0 / 5.0)
    return rng.expovariate(1.0 / 105.0)


def percentile(sorted_values: list[float], q: float) -> float:
    """정렬된 표본에서 q 분위수 (nearest-rank)."""
    rank = max(1, math.ceil(q * len(sorted_values)))
    return sorted_values[rank - 1]


def simulate(rho: float, sampler, *, seed: int = SEED) -> dict:
    rng = random.Random(seed)
    arrival_rate = rho / MEAN_SERVICE_MS      # 초당이 아니라 ms 당 — 단위는 ms 로 통일
    waits: list[float] = []
    responses: list[float] = []
    services: list[float] = []

    wait = 0.0
    service = sampler(rng)
    for _ in range(REQUESTS):
        waits.append(wait)
        responses.append(wait + service)
        services.append(service)
        gap = rng.expovariate(arrival_rate)
        wait = max(0.0, wait + service - gap)
        service = sampler(rng)

    waits, responses, services = waits[WARMUP:], responses[WARMUP:], services[WARMUP:]
    ordered = sorted(responses)
    mean_s = statistics.fmean(services)
    return {
        "rho": rho,
        "mean_wait": statistics.fmean(waits),
        "mean_response": statistics.fmean(responses),
        "p50": percentile(ordered, 0.50),
        "p90": percentile(ordered, 0.90),
        "p99": percentile(ordered, 0.99),
        "p999": percentile(ordered, 0.999),
        "cv2_service": statistics.pvariance(services) / (mean_s ** 2),
    }


def part1_utilization() -> list[dict]:
    print(RULE)
    print("1. 서비스 시간은 그대로 두고 이용률만 올린다 (M/M/1, 평균 서비스 10ms)")
    print(RULE)
    print(f"요청 {REQUESTS:,}건 중 앞 {WARMUP:,}건은 버렸다. 단위는 모두 ms.\n")
    print("  이용률 | 평균응답 | 이론평균 |    p50 |    p90 |    p99 |  p99.9 | 이론 p99 | p99/평균")
    print("  " + "-" * 87)

    rows = []
    for rho in (0.50, 0.70, 0.80, 0.90, 0.95):
        row = simulate(rho, exponential)
        # M/M/1 의 체류시간은 평균 E[S]/(1-rho) 인 지수분포다
        theory_mean = MEAN_SERVICE_MS / (1 - rho)
        theory_p99 = -math.log(1 - 0.99) * theory_mean
        row["theory_mean"] = theory_mean
        row["theory_p99"] = theory_p99
        rows.append(row)
        print(f"  {rho:6.0%} | {row['mean_response']:8.1f} | {theory_mean:8.1f} | "
              f"{row['p50']:6.1f} | {row['p90']:6.1f} | {row['p99']:6.1f} | "
              f"{row['p999']:6.1f} | {theory_p99:8.1f} | "
              f"{row['p99'] / row['mean_response']:7.2f}배")
    print()
    print("  M/M/1 의 체류시간은 지수분포이므로 p99 / 평균 = -ln(0.01) = "
          f"{-math.log(0.01):.2f} 가 이론값이다.")
    print("  이 비는 이용률과 무관하다 — 이용률이 바꾸는 것은 절대값이다.\n")
    return rows


def part2_seventy_vs_ninety(rows: list[dict]) -> None:
    print(RULE)
    print("2. 70% 와 90% 의 차이")
    print(RULE)
    low = next(r for r in rows if r["rho"] == 0.70)
    high = next(r for r in rows if r["rho"] == 0.90)

    print("  항목       |    70% |    90% | 배수")
    print("  " + "-" * 44)
    for label, key in (
        ("평균 응답", "mean_response"),
        ("p50", "p50"),
        ("p99", "p99"),
        ("p99.9", "p999"),
        ("평균 대기", "mean_wait"),
    ):
        print(f"  {label:10s} | {low[key]:6.1f} | {high[key]:6.1f} | "
              f"{high[key] / low[key]:4.1f}배")
    print()
    print(f"  서버를 늘리지 않고 트래픽만 {0.9 / 0.7 - 1:.0%} 늘린 것인데")
    print(f"  p99 는 {high['p99'] / low['p99']:.1f}배가 됐다.\n")


def part3_variability() -> None:
    print(RULE)
    print("3. 이용률을 70% 로 고정하고 서비스 시간의 흔들림만 바꾼다")
    print(RULE)
    rho = 0.70
    print(f"  평균 서비스 시간은 세 경우 모두 {MEAN_SERVICE_MS:.0f}ms 다.\n")
    print("  서비스 시간 분포    |   C^2 | 평균대기 | 이론대기 | 평균응답 |    p99 | p99/평균")
    print("  " + "-" * 79)

    cases = [
        ("고정 (M/D/1)", deterministic),
        ("지수 (M/M/1)", exponential),
        ("95%는 5ms·5%는 105ms", hyperexponential),
    ]
    for label, sampler in cases:
        row = simulate(rho, sampler)
        cv2 = row["cv2_service"]
        # 폴라체크–힌친: Wq = rho * E[S] * (1 + C^2) / (2 (1 - rho))
        theory_wait = rho * MEAN_SERVICE_MS * (1 + cv2) / (2 * (1 - rho))
        print(f"  {label:19s} | {cv2:5.2f} | {row['mean_wait']:8.1f} | "
              f"{theory_wait:8.1f} | {row['mean_response']:8.1f} | {row['p99']:6.1f} | "
              f"{row['p99'] / row['mean_response']:7.2f}배")
    print()
    print("  이용률은 셋 다 70% 로 같다. 바뀐 것은 서비스 시간의 흔들림뿐이다.\n")


def main() -> None:
    print(RULE)
    print("환경")
    print(RULE)
    print(f"  Python  {platform.python_version()}")
    print(f"  OS      {platform.system()} {platform.release()}")
    print(f"  시드    {SEED} (고정)")
    print()
    rows = part1_utilization()
    part2_seventy_vs_ninety(rows)
    part3_variability()


if __name__ == "__main__":
    main()
