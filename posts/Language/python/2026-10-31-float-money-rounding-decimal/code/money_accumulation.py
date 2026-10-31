"""금액을 float 으로 더하면 어디서 얼마나 틀어지는지, 고치는 세 방법의 비용은
얼마인지를 같은 입력으로 재 본다.

측정 대상은 세 가지다.
  1. float 누적 합계가 정답에서 얼마나 벗어나는가
  2. Decimal·정수 최소단위로 고쳤을 때 걸리는 시간
  3. 반올림 방식(ROUND_HALF_UP / ROUND_HALF_EVEN)이 합계를 얼마나 가르는가

난수는 시드를 고정했다. 같은 명령을 돌리면 같은 숫자가 나온다.
"""

import math
import random
import sys
import time
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP, getcontext

ITEM_COUNT = 100_000
SEED = 20261031
CENT = Decimal("0.01")


def make_prices() -> list[str]:
    """소수점 둘째 자리까지의 금액을 문자열로 만든다.

    문자열로 두는 이유는 float·Decimal·int 세 방식이 모두 같은 원본에서
    출발해야 비교가 성립하기 때문이다. float 로 먼저 만들면 그 시점에 이미
    오차가 섞인다.
    """
    rng = random.Random(SEED)
    return [f"{rng.randrange(1, 1_000_00) / 100:.2f}" for _ in range(ITEM_COUNT)]


def timed(label: str, func, *args):
    started = time.perf_counter()
    result = func(*args)
    elapsed = time.perf_counter() - started
    return label, result, elapsed


def sum_float(prices: list[str]) -> float:
    total = 0.0
    for price in prices:
        total += float(price)
    return total


def sum_decimal(prices: list[str]) -> Decimal:
    total = Decimal(0)
    for price in prices:
        total += Decimal(price)
    return total


def sum_int_cents(prices: list[str]) -> int:
    total = 0
    for price in prices:
        won, cent = price.split(".")
        total += int(won) * 100 + int(cent)
    return total


def rule(title: str) -> None:
    print("\n" + "=" * 68)
    print(title)
    print("=" * 68)


def scan_mismatch(item_count: int, seed_count: int) -> tuple[int, Decimal]:
    """건수를 바꿔 가며, 원 단위로 끊은 float 합계가 정답과 어긋나는 횟수를 센다.

    리스트를 만들지 않고 그 자리에서 더한다. 1,000만 건을 문자열로 들고 있으면
    메모리가 먼저 바닥나기 때문이다.
    """
    mismatches = 0
    worst = Decimal(0)
    for seed in range(seed_count):
        rng = random.Random(seed)
        exact_cents = 0
        float_total = 0.0
        for _ in range(item_count):
            cents = rng.randrange(1, 1_000_00)
            exact_cents += cents
            float_total += cents / 100
        exact_won = Decimal(exact_cents) / 100
        rounded = Decimal(repr(round(float_total, 2)))
        if rounded != exact_won:
            mismatches += 1
            worst = max(worst, abs(rounded - exact_won))
    return mismatches, worst


def main() -> None:
    print(f"파이썬 {sys.version.split()[0]}")
    print(f"float 유효 십진 자릿수 sys.float_info.dig = {sys.float_info.dig}")
    print(f"기본 Decimal 정밀도 getcontext().prec = {getcontext().prec}")

    rule("0. 흔히 보는 한 줄")
    print(f"   0.1 + 0.2          = {0.1 + 0.2!r}")
    print(f"   0.1 + 0.2 == 0.3   -> {0.1 + 0.2 == 0.3}")
    print(f"   Decimal(0.1)       = {Decimal(0.1)}")
    print(f"   Decimal('0.1')     = {Decimal('0.1')}")

    prices = make_prices()
    print(f"\n   금액 {len(prices):,}건 생성 (시드 {SEED}) · 앞 5건: {prices[:5]}")

    rule(f"1. {ITEM_COUNT:,}건을 더한 결과")
    runs = [
        timed("float", sum_float, prices),
        timed("Decimal", sum_decimal, prices),
        timed("int(전)", sum_int_cents, prices),
    ]
    exact = next(r[1] for r in runs if r[0] == "int(전)")
    print(f"   정답(정수 전 단위)  = {exact:,}전 = {Decimal(exact) / 100:,}원")
    for label, result, elapsed in runs:
        print(f"   {label:<9} {str(result):>22}   {elapsed * 1000:7.1f} ms")

    float_total = next(r[1] for r in runs if r[0] == "float")
    exact_decimal = Decimal(exact) / 100
    gap = Decimal(repr(float_total)) - exact_decimal
    print(f"\n   float 과 정답의 차이 = {gap}원")
    print(f"   repr(float 합계)     = {float_total!r}")
    print(f"   Decimal(float 합계)  = {Decimal(float_total)}")

    rule("2. 차이가 보이는 자리 — 원 단위로 끊어 보면")
    print(f"   round(float 합계, 2) = {round(float_total, 2)}")
    print(f"   정답을 원 단위로      = {exact_decimal}")
    print(f"   두 값이 같은가        -> {Decimal(repr(round(float_total, 2))) == exact_decimal}")

    rule("2b. 그럼 몇 건부터 어긋나는가 — 시드를 바꿔 가며 센다")
    for count, seeds in [(10_000, 20), (100_000, 20), (1_000_000, 20),
                         (10_000_000, 3)]:
        started = time.perf_counter()
        bad, worst = scan_mismatch(count, seeds)
        elapsed = time.perf_counter() - started
        note = f"최대 오차 {worst}원" if bad else "전부 일치"
        print(f"   {count:>10,}건 × {seeds:>2}회  어긋남 {bad:>2}회  "
              f"{note:<22} ({elapsed:5.1f}초)")

    rule("2c. 그래도 깨지는 자리 — 잔액이 커지면 1전이 사라진다")
    balance = 1.0
    while balance + 0.01 != balance:
        balance *= 10
    print(f"   balance + 0.01 == balance 가 처음 성립하는 크기 = {balance:,.0f}원")
    print(f"   그 크기에서 float 끼리의 간격 math.ulp = {math.ulp(balance)}")
    print(f"   float   {balance:,.0f} + 0.01 -> {balance + 0.01:,.2f}")
    print(f"   Decimal {balance:,.0f} + 0.01 -> "
          f"{Decimal(int(balance)) + Decimal('0.01')}")
    print(f"   int(전) {int(balance) * 100:,} + 1 -> {int(balance) * 100 + 1:,}")

    rule("3. 부가세 10% 를 건마다 붙여 반올림할 때")
    half_up = Decimal(0)
    half_even = Decimal(0)
    float_tax = 0.0
    for price in prices:
        amount = Decimal(price)
        tax = amount * Decimal("0.1")
        half_up += tax.quantize(CENT, rounding=ROUND_HALF_UP)
        half_even += tax.quantize(CENT, rounding=ROUND_HALF_EVEN)
        float_tax += round(float(price) * 0.1, 2)
    print(f"   ROUND_HALF_UP   합계 = {half_up:,}")
    print(f"   ROUND_HALF_EVEN 합계 = {half_even:,}")
    print(f"   두 방식의 차이       = {half_up - half_even}")
    print(f"   float+round() 합계   = {float_tax!r}")
    print(f"   float 이 HALF_UP 과 같은가 -> "
          f"{Decimal(repr(float_tax)) == half_up}")

    rule("4. 한 건만 떼어 보면 왜 갈리는지 보인다")
    for sample in ["0.125", "0.135", "2.675"]:
        value = Decimal(sample)
        print(f"   {sample:>6}  HALF_UP={value.quantize(CENT, rounding=ROUND_HALF_UP)}"
              f"  HALF_EVEN={value.quantize(CENT, rounding=ROUND_HALF_EVEN)}"
              f"  round(float)={round(float(sample), 2)}")

    rule("5. 세 방식의 비용 — 같은 10만 건, 3회 반복 중 최저")
    for label, func in [("float", sum_float),
                        ("Decimal", sum_decimal),
                        ("int(전)", sum_int_cents)]:
        best = min(timed(label, func, prices)[2] for _ in range(3))
        print(f"   {label:<9} {best * 1000:7.1f} ms")


if __name__ == "__main__":
    main()
