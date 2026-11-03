"""루프라인 모델의 상한을 논문 수치로 직접 계산해 검산한다.

Williams · Waterman · Patterson, "Roofline: An Insightful Visual Performance Model
for Floating-Point Programs and Multicore Architectures", UCB/EECS-2008-134 의
§3(AMD Opteron X2 수치), §4(천장 수치), §6.2 표 2(커널 연산강도)를 그대로 쓴다.
Python 3.13.5 에서 돌렸다. 외부 의존성은 없다.
"""

PEAK_GFLOPS = 17.6          # §3 Opteron X2 배정밀도 최대 성능
PEAK_GBPS = 15.0            # §3 측정한 메모리 대역폭

# §4 그림 2 의 천장. 아래 천장을 깨지 않고는 위 천장에 못 간다.
COMPUTE_CEILINGS = [
    ("ILP·SIMD 없음", 2.2),
    ("곱·합 불균형", 8.8),
    ("최대 성능", PEAK_GFLOPS),
]
MEMORY_CEILINGS = [
    ("단위 보폭만", 2.7),
    ("메모리 친화 없음", 4.8),
    ("SW 프리페치 없음", 11.0),
    ("최대 대역폭", PEAK_GBPS),
]

# §6.2 표 2 — 최적화 전·후 연산강도 (Flops / DRAM byte)
KERNELS = [
    ("SpMV", 0.17, 0.25),
    ("Stencil", 0.33, 0.50),
    ("LBMHD", 0.70, 1.07),
    ("3-D FFT", 1.09, 1.64),
]


def attainable(intensity: float, peak_gflops: float, peak_gbps: float) -> float:
    """§3 의 식: min(최대 연산 성능, 최대 대역폭 × 연산강도)."""
    return min(peak_gflops, peak_gbps * intensity)


def bound_kind(intensity: float, ridge: float) -> str:
    return "연산 바운드" if intensity >= ridge else "메모리 바운드"


def main() -> None:
    ridge = PEAK_GFLOPS / PEAK_GBPS
    print("== 1. 능선점 — 두 지붕이 만나는 연산강도")
    print(f"  최대 연산 성능 {PEAK_GFLOPS} GFlop/s ÷ 최대 대역폭 {PEAK_GBPS} GB/s"
          f" = {ridge:.2f} Flops/byte")
    print(f"  검산: {PEAK_GBPS} × {ridge:.4f} = {PEAK_GBPS * ridge:.2f} GFlop/s"
          f" (= 최대 연산 성능)")

    print()
    print("== 2. 커널별 상한 — 최적화 전·후 연산강도로 각각")
    print("  커널      연산강도   상한(GFlop/s)   판정")
    for name, before, after in KERNELS:
        for label, intensity in (("전", before), ("후", after)):
            bound = attainable(intensity, PEAK_GFLOPS, PEAK_GBPS)
            print(f"  {name:<8} {label} {intensity:5.2f}     {bound:6.2f}"
                  f"        {bound_kind(intensity, ridge)}")

    print()
    print("== 3. 연산강도 1 과 2 — 논문 §3 이 든 두 경우")
    for intensity in (1.0, 2.0):
        memory_side = PEAK_GBPS * intensity
        print(f"  연산강도 {intensity:.0f}: 대역폭 쪽 {memory_side:.1f} GFlop/s,"
              f" 연산 쪽 {PEAK_GFLOPS} GFlop/s → 상한 {min(memory_side, PEAK_GFLOPS):.1f}"
              f" ({bound_kind(intensity, ridge)})")

    print()
    print("== 4. 천장을 넣으면 — Stencil(0.33) 이 어느 구역에 있는가")
    intensity = 0.33
    print("  메모리 천장               대역폭×강도   연산 천장          GFlop/s")
    for (mem_label, gbps), (cmp_label, gflops) in zip(
        MEMORY_CEILINGS, COMPUTE_CEILINGS + [COMPUTE_CEILINGS[-1]]
    ):
        print(f"  {mem_label:<14} {gbps:5.1f} GB/s   {gbps * intensity:6.2f}"
              f"       {cmp_label:<12} {gflops:5.1f}")
    # 연산강도 0.33 의 수직선이 아래부터 어떤 천장을 차례로 만나는지
    crossings = sorted(
        [(gbps * intensity, "메모리", label) for label, gbps in MEMORY_CEILINGS]
        + [(gflops, "연산", label) for label, gflops in COMPUTE_CEILINGS
           if gflops < attainable(intensity, PEAK_GFLOPS, PEAK_GBPS)]
    )
    print("  수직선이 아래부터 만나는 천장:")
    for gflops, kind, label in crossings:
        print(f"    {gflops:5.2f} GFlop/s  {kind:<4} {label}")
    print("  → 두 종류 천장이 섞여 있으므로 둘 다 손봐야 하고, 가장 낮은 두 개가 메모리라"
          " 메모리부터 간다")

    print()
    print("== 5. 연산강도를 올리면 상한이 얼마나 오르는가 (SpMV 0.17 → 0.25)")
    before = attainable(0.17, PEAK_GFLOPS, PEAK_GBPS)
    after = attainable(0.25, PEAK_GFLOPS, PEAK_GBPS)
    print(f"  {before:.2f} → {after:.2f} GFlop/s, {after / before:.2f}배"
          f" (= 0.25 / 0.17 = {0.25 / 0.17:.2f}, 메모리 바운드 구역에선 강도에 비례)")

    print()
    print("== 6. 같은 커널, 다른 장비 — 논문이 적은 능선점으로 판정")
    for machine, ridge_point in (
        ("Intel Xeon", 6.7), ("AMD Opteron X4", 4.4),
        ("Sun UltraSPARC T2+", 0.33), ("IBM Cell", 0.65),
    ):
        verdicts = [
            f"{name} {bound_kind(after, ridge_point)[:3]}"
            for name, _before, after in KERNELS
        ]
        print(f"  {machine:<20} 능선점 {ridge_point:4.2f}  " + " · ".join(verdicts))


if __name__ == "__main__":
    main()
