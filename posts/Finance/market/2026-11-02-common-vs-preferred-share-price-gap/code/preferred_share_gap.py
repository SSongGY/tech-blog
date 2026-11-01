"""보통주와 우선주의 가격 차이를 배당·의결권·발행한도로 나눠 계산한다.

가상 회사 `마바화학`의 자본 구성과 배당금으로 보통주·구형우선주·신형우선주의
배당수익률을 각각 구하고, 보통주 대비 할인율이 달라질 때 그 수익률이 어떻게
움직이는지를 본다. 의결권 쪽은 상법 제371조 제1항의 분모 산정과 제344조의3
제2항의 발행한도를 그대로 계산에 넣는다. 금액 단위는 원이다.
"""

from dataclasses import dataclass

PAR_VALUE = 5_000  # 액면가

COMMON_SHARES = 8_000_000
PREFERRED_SHARES = 2_000_000
TOTAL_SHARES = COMMON_SHARES + PREFERRED_SHARES

COMMON_PRICE = 20_000
PREFERRED_PRICE = 12_000

# 지배주주는 보통주만 들고 있다고 둔다.
CONTROLLING_COMMON = 3_200_000

# 상법 제344조의3 제2항 — 의결권 없는 종류주식 총수는 발행주식총수의 1/4 이내.
COMMERCIAL_ACT_CAP = 0.25
# 자본시장법 제165조의15 — 상장법인이 같은 조 제1항 각 호(해외 발행 등)에 해당해
# 발행하는 의결권 없는 주식은 1/4 한도 계산에서 빠지고, 이를 합한 총수의 한도가
# 제2항의 1/2 이다. 아무 주식이나 1/2 까지 찍을 수 있다는 뜻이 아니다.
CAPITAL_MARKETS_ACT_CAP = 0.50


@dataclass
class PreferredClass:
    """우선주 한 종류의 배당 조건.

    구형우선주는 보통주 배당금에 액면 기준 가산율만큼을 더해 받는다.
    신형우선주는 액면 기준 최저배당률을 보장받되, 이 예제에서는 비참가적이어서
    보통주 배당금을 넘어서는 추가 배당에는 참여하지 않는다.
    """

    name: str
    extra_rate_on_par: float = 0.0
    minimum_rate_on_par: float = 0.0

    def dividend_per_share(self, common_dps: float) -> float:
        if self.extra_rate_on_par:
            return common_dps + PAR_VALUE * self.extra_rate_on_par
        return max(common_dps, PAR_VALUE * self.minimum_rate_on_par)


OLD_TYPE = PreferredClass("구형우선주 (액면 +1%p)", extra_rate_on_par=0.01)
NEW_TYPE = PreferredClass("신형우선주 (최저배당률 2%)", minimum_rate_on_par=0.02)


def discount_rate(common_price: float, preferred_price: float) -> float:
    """보통주 대비 우선주 할인율. 우선주가 더 비싸면 음수가 된다."""
    return (common_price - preferred_price) / common_price * 100


def dividend_yield(dps: float, price: float) -> float:
    return dps / price * 100


def print_capital_structure() -> None:
    rows = [
        ("보통주", COMMON_SHARES, COMMON_PRICE),
        ("우선주", PREFERRED_SHARES, PREFERRED_PRICE),
    ]
    print(f"  {'구분':<8}{'주식수':>12}{'주가':>10}{'시가총액':>18}{'지분율(%)':>12}")
    for label, shares, price in rows:
        print(
            f"  {label:<8}{shares:>12,}{price:>10,}"
            f"{shares * price:>18,}{shares / TOTAL_SHARES * 100:>12.2f}"
        )
    total_cap = COMMON_SHARES * COMMON_PRICE + PREFERRED_SHARES * PREFERRED_PRICE
    print(f"  {'합계':<8}{TOTAL_SHARES:>12,}{'':>10}{total_cap:>18,}{100.00:>12.2f}")
    print(
        f"  보통주 대비 우선주 할인율: "
        f"{discount_rate(COMMON_PRICE, PREFERRED_PRICE):.2f}%"
    )


def print_dividend_cases(common_dps_cases: list[tuple[str, float]]) -> None:
    for label, common_dps in common_dps_cases:
        print(f"  {label} — 보통주 주당배당금 {common_dps:,.0f}원")
        print(
            f"    {'구분':<24}{'주당배당금':>12}{'주가':>10}"
            f"{'배당수익률(%)':>16}{'배당총액':>18}"
        )
        entries = [
            ("보통주", common_dps, COMMON_PRICE, COMMON_SHARES),
            (
                OLD_TYPE.name,
                OLD_TYPE.dividend_per_share(common_dps),
                PREFERRED_PRICE,
                PREFERRED_SHARES,
            ),
            (
                NEW_TYPE.name,
                NEW_TYPE.dividend_per_share(common_dps),
                PREFERRED_PRICE,
                PREFERRED_SHARES,
            ),
        ]
        for name, dps, price, shares in entries:
            print(
                f"    {name:<24}{dps:>12,.0f}{price:>10,}"
                f"{dividend_yield(dps, price):>16.2f}{dps * shares:>18,.0f}"
            )
        print()


def print_discount_sweep(common_dps: float) -> None:
    print(
        f"  보통주 주가 {COMMON_PRICE:,}원 · 보통주 주당배당금 {common_dps:,.0f}원 · "
        f"구형우선주 주당배당금 {OLD_TYPE.dividend_per_share(common_dps):,.0f}원 고정"
    )
    print(
        f"    {'할인율(%)':>10}{'우선주 주가':>14}"
        f"{'보통주 배당수익률(%)':>22}{'우선주 배당수익률(%)':>22}{'차이(%p)':>12}"
    )
    preferred_dps = OLD_TYPE.dividend_per_share(common_dps)
    common_yield = dividend_yield(common_dps, COMMON_PRICE)
    for pct in (0, 10, 20, 30, 40, 50, 60):
        price = COMMON_PRICE * (1 - pct / 100)
        preferred_yield = dividend_yield(preferred_dps, price)
        print(
            f"    {pct:>10}{price:>14,.0f}{common_yield:>22.2f}"
            f"{preferred_yield:>22.2f}{preferred_yield - common_yield:>12.2f}"
        )


def print_voting_math() -> None:
    """상법 제371조 제1항 — 의결권 없는 주식은 발행주식총수에서 제외한다."""
    by_total = CONTROLLING_COMMON / TOTAL_SHARES * 100
    by_voting = CONTROLLING_COMMON / COMMON_SHARES * 100
    print(f"  지배주주 보유 보통주       {CONTROLLING_COMMON:>12,}주")
    print(
        f"  발행주식총수 기준 지분율   {by_total:>12.2f}%   "
        f"(분모 {TOTAL_SHARES:,}주)"
    )
    print(
        f"  의결권 기준 지분율         {by_voting:>12.2f}%   "
        f"(분모 {COMMON_SHARES:,}주 — 우선주 제외)"
    )
    print(f"  차이                       {by_voting - by_total:>12.2f}%p")


def print_issuance_cap() -> None:
    current_ratio = PREFERRED_SHARES / TOTAL_SHARES * 100
    print(f"  현재 의결권 없는 주식 비중   {current_ratio:>10.2f}%")
    for label, cap in [
        ("상법 제344조의3 제2항 (1/4)", COMMERCIAL_ACT_CAP),
        ("자본시장법 제165조의15 제2항 (1/2)", CAPITAL_MARKETS_ACT_CAP),
    ]:
        # 보통주 수를 고정한 채 우선주 x 주를 더 발행하면
        # (PREFERRED + x) / (TOTAL + x) = cap 을 만족하는 x 를 구한다.
        room = (cap * COMMON_SHARES - (1 - cap) * PREFERRED_SHARES) / (1 - cap)
        print(
            f"  {label:<36}한도 {cap * 100:>5.1f}%  "
            f"추가 발행 여력 {room:>12,.0f}주"
        )


def main() -> None:
    print("[1] 마바화학의 자본 구성")
    print_capital_structure()

    print()
    print("[2] 배당이 많은 해와 적은 해 — 구형과 신형이 뒤바뀐다")
    print_dividend_cases([("호황", 800.0), ("부진", 30.0)])

    print("[3] 할인율이 커질수록 우선주 배당수익률은 어떻게 움직이는가")
    print_discount_sweep(800.0)

    print()
    print("[4] 의결권 분모에서 우선주를 빼면")
    print_voting_math()

    print()
    print("[5] 의결권 없는 주식의 발행한도")
    print_issuance_cap()


if __name__ == "__main__":
    main()
