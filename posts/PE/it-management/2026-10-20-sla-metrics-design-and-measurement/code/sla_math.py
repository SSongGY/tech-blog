"""SLA 지표를 실제로 계산해 본다. 답안에 쓰는 숫자는 전부 여기서 나온 값이다.

재는 것은 다섯이다.
  1. 가용률 수준별 허용 중단 시간 — 99.9% 가 실제로 몇 분인가
  2. 같은 장애, 다른 분모 — 시간 기준과 요청 기준이 갈리는 폭
  3. 직렬·병렬 구성의 복합 가용률 — 부품이 늘면 목표가 저절로 내려간다
  4. 응답시간은 평균이 아니라 백분위로 — 평균이 멀쩡한데 p99 가 깨지는 경우
  5. 오차 예산 소진 — 한 번의 장애가 월 예산의 몇 %인가

난수는 시드를 고정했으므로 몇 번을 돌려도 같은 값이 나온다.
"""

from __future__ import annotations

import math
import random
import unicodedata

MINUTES_PER_DAY = 24 * 60
PERIODS = {
    "하루": MINUTES_PER_DAY,
    "한 주": 7 * MINUTES_PER_DAY,
    "30일": 30 * MINUTES_PER_DAY,
    "365일": 365 * MINUTES_PER_DAY,
}
LEVELS = [99.0, 99.5, 99.9, 99.95, 99.99, 99.999]


def width(text: str) -> int:
    """한글은 터미널에서 두 칸을 차지한다. 그대로 len 으로 재면 표가 어긋난다."""
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in str(text))


def pad(text: str, size: int, *, right: bool = False) -> str:
    gap = " " * max(0, size - width(text))
    return gap + str(text) if right else str(text) + gap


def fmt_minutes(minutes: float) -> str:
    """분을 사람이 읽는 단위로 바꾼다. 자릿수를 줄이지 않는다."""
    sign = "-" if minutes < 0 else ""
    value = abs(minutes)
    if value >= MINUTES_PER_DAY:
        return f"{sign}{value / MINUTES_PER_DAY:.2f}일"
    if value >= 60:
        return f"{sign}{value / 60:.2f}시간"
    if value >= 1:
        return f"{sign}{value:.2f}분"
    if value >= 1 / 60:
        return f"{sign}{value * 60:.2f}초"
    return f"{sign}{value * 60_000:.2f}ms"


def rule(title: str) -> None:
    print("\n" + "=" * 68)
    print(title)
    print("=" * 68)


def section_allowed_downtime() -> None:
    rule("1. 가용률 수준별 허용 중단 시간")
    header = "  " + pad("가용률", 8, right=True) + " | " + " | ".join(
        pad(name, 10, right=True) for name in PERIODS)
    print(header)
    print("  " + "-" * (width(header) - 2))
    for level in LEVELS:
        cells = [fmt_minutes(span * (100 - level) / 100) for span in PERIODS.values()]
        print(f"  {level:>7}% | " + " | ".join(f"{c:>10}" for c in cells))
    print("\n  읽는 법: 목표 가용률은 기준 기간이 붙어야 뜻이 생긴다.")
    print("  99.9% 라도 '하루 기준'과 '365일 기준'이 허용하는 중단 시간이 다르다.")


def section_denominator() -> None:
    rule("2. 같은 30분 장애, 분모를 무엇으로 두느냐로 갈린다")
    window_minutes = 30 * MINUTES_PER_DAY
    outage_minutes = 30

    # 요청이 시간대별로 고르게 들어오지 않는다. 아래는 하루 요청의 시간대 분포를
    # 가정한 값이고, 합이 1이 되도록 맞췄다. 분포 자체가 협약에서 합의할 대상이다.
    peak_share_per_minute = 0.0025     # 피크 1분이 하루 요청에서 차지하는 비율
    night_share_per_minute = 0.0002    # 새벽 1분
    daily_requests = 2_000_000
    monthly_requests = daily_requests * 30

    time_based = (1 - outage_minutes / window_minutes) * 100
    print(f"  측정 창 30일 = {window_minutes:,}분 · 장애 {outage_minutes}분")
    print(f"  시간 기준 가용률 : {time_based:.5f}%  (장애가 언제 났든 같다)")

    for label, share in (("피크 시간대", peak_share_per_minute),
                         ("새벽 시간대", night_share_per_minute)):
        lost = daily_requests * share * outage_minutes
        request_based = (1 - lost / monthly_requests) * 100
        print(f"  요청 기준 가용률 ({label}) : {request_based:.5f}%  "
              f"— 실패 요청 {lost:,.0f}건")

    print("\n  시간 기준은 한 값인데 요청 기준은 장애가 난 시각에 따라 갈린다.")
    print("  어느 쪽을 쓸지, 분포를 누가 정할지를 협약에 적지 않으면 매달 재협상한다.")


def section_composite() -> None:
    rule("3. 직렬 구성과 병렬 구성의 복합 가용률")
    component = 0.999
    print(f"  구성요소 하나의 가용률 : {component * 100:.3f}%")
    print(f"\n  {pad('직렬 개수', 9, right=True)} | {pad('복합 가용률', 12, right=True)}"
          f" | {pad('30일 허용 중단', 14, right=True)}")
    print("  " + "-" * 41)
    for n in (1, 2, 3, 5, 10):
        combined = component ** n
        downtime = 30 * MINUTES_PER_DAY * (1 - combined)
        print(f"  {n:>8} | {combined * 100:>11.4f}% | {fmt_minutes(downtime):>14}")

    print("\n  같은 부품을 병렬로 이중화하면 (고장이 서로 독립이라고 볼 때)")
    for n in (1, 2, 3):
        combined = 1 - (1 - component) ** n
        downtime = 30 * MINUTES_PER_DAY * (1 - combined)
        print(f"    {n}중화 : {combined * 100:.7f}%  ·  30일 허용 중단 {fmt_minutes(downtime)}")

    # 현실적인 조합 — 앞단 이중화 + 단일 DB + 외부 결제 연동
    tiers = [("웹 2중화", 1 - (1 - 0.999) ** 2),
             ("WAS 2중화", 1 - (1 - 0.999) ** 2),
             ("DB 단일", 0.999),
             ("외부 결제 연동", 0.9995)]
    total = math.prod(a for _, a in tiers)
    print("\n  네 구간을 직렬로 이은 서비스")
    for name, value in tiers:
        print(f"    {pad(name, 16)} {value * 100:.6f}%")
    print(f"    {pad('전체', 16)} {total * 100:.6f}%  "
          f"·  30일 허용 중단 {fmt_minutes(30 * MINUTES_PER_DAY * (1 - total))}")
    print("  가장 약한 구간(DB 단일 99.9%)보다 전체가 낮다. 직렬은 곱이기 때문이다.")


def percentile(values: list[float], q: float) -> float:
    """선형 보간 방식의 백분위. numpy 없이 돌도록 직접 구현한다."""
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return ordered[low]
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def section_percentile() -> None:
    rule("4. 응답시간을 평균으로 재면 안 되는 이유")
    rng = random.Random(20261020)
    # 응답시간은 한쪽으로 긴 꼬리를 갖는다. 로그정규분포로 그 모양을 만들고,
    # 2%에만 재시도·락 대기에 해당하는 지연을 얹었다. 분포는 가정이고,
    # 아래 계산은 그 분포에서 나온 실제 값이다.
    samples = []
    for _ in range(100_000):
        base = rng.lognormvariate(math.log(80), 0.45)
        if rng.random() < 0.02:
            base += rng.lognormvariate(math.log(900), 0.6)
        samples.append(base)

    mean = sum(samples) / len(samples)
    target = 300.0
    print(f"  표본 {len(samples):,}건 · 목표 '응답시간 {target:.0f} ms 이하'")
    print(f"    평균      : {mean:8.1f} ms  -> 목표 {'충족' if mean <= target else '미달'}")
    for q, name in ((0.50, "p50"), (0.90, "p90"), (0.95, "p95"),
                    (0.99, "p99"), (0.999, "p99.9")):
        value = percentile(samples, q)
        print(f"    {name:<9} : {value:8.1f} ms  -> 목표 {'충족' if value <= target else '미달'}")

    over = sum(1 for v in samples if v > target)
    print(f"\n  목표를 넘긴 요청 : {over:,}건 ({over / len(samples) * 100:.2f}%)")
    print("  평균만 보면 통과하는데 100명 중 2명은 목표의 몇 배를 기다린다.")
    print("  백분위를 안 적으면 '평균 기준'이라는 해석이 끼어든다.")


def section_error_budget() -> None:
    rule("5. 오차 예산 소진 — 장애 한 번이 월 예산의 몇 %인가")
    slo = 99.9
    budget = 30 * MINUTES_PER_DAY * (100 - slo) / 100
    print(f"  SLO {slo}% · 30일 기준 오차 예산 : {fmt_minutes(budget)}")
    print(f"\n  {pad('사건', 24)} | {pad('중단', 8, right=True)} | "
          f"{pad('소진', 8, right=True)} | {pad('누적 소진', 10, right=True)}")
    print("  " + "-" * 58)
    used = 0.0
    for name, minutes in (("배포 롤백 (화)", 7),
                          ("DB 페일오버 (목)", 12),
                          ("외부 결제 지연 (토)", 18),
                          ("스위치 재기동 (월)", 9)):
        used += minutes
        print(f"  {pad(name, 24)} | {minutes:>6}분 | "
              f"{minutes / budget * 100:>7.1f}% | {used / budget * 100:>9.1f}%")
    print(f"\n  남은 예산 : {fmt_minutes(budget - used)} "
          f"({(budget - used) / budget * 100:.1f}%)")
    print("  달성 가용률 : "
          f"{(1 - used / (30 * MINUTES_PER_DAY)) * 100:.4f}% (목표 {slo}%)")


def main() -> None:
    print("SLA 지표 계산 — 아래 숫자는 전부 이 스크립트가 계산한 값이다")
    section_allowed_downtime()
    section_denominator()
    section_composite()
    section_percentile()
    section_error_budget()


if __name__ == "__main__":
    main()
