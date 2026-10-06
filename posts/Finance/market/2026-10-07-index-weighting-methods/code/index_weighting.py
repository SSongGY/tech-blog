"""주가지수는 어떻게 계산되는가 — 주가 가중과 시가총액 가중.

같은 세 종목으로 두 방식의 지수를 만들고, 같은 하루 등락에 두 지수가
반대 방향으로 움직이는 것을 본다. 이어서 액면분할이 일어났을 때 주가 가중
지수만 제수(divisor)를 고쳐야 하는 이유와, 유동비율을 곱하면 시가총액 가중
지수의 비중이 어떻게 바뀌는지를 계산한다.
"""
import platform
import sys

EOK = 100_000_000  # 1억원
BASE_LEVEL = 100.0

# 이름, 주가(원), 상장주식수, 유동비율 — 모두 가상 회사
STOCKS = [
    ("가나정밀", 500_000, 2_000_000, 0.60),
    ("다라통신", 50_000, 100_000_000, 0.90),
    ("마바유통", 10_000, 200_000_000, 0.30),
]


def print_definitions() -> None:
    print("[0] 산식")
    print("  주가 가중     지수 = Σ 주가 ÷ 제수")
    print("  시가총액 가중 지수 = Σ (주가 × 주식수) ÷ 기준시점 시가총액 × 100")
    print("  제수는 기준일에 지수가 100 이 되도록 정하고, 종목 교체·분할 때 지수가 튀지 않게 고친다")
    print()


def print_base_weights() -> tuple[float, float]:
    print("[1] 기준일 — 같은 세 종목, 두 가지 비중 (시가총액은 억원)")
    price_sum = sum(price for _, price, _, _ in STOCKS)
    cap_sum = sum(price * shares for _, price, shares, _ in STOCKS)
    print(f"  {'':10}{'주가':>9}{'상장주식수':>14}{'시가총액':>10}{'주가 비중':>10}{'시총 비중':>10}")
    for name, price, shares, _ in STOCKS:
        cap = price * shares
        print(f"  {name:10}{price:>9,}{shares:>14,}{cap / EOK:>10,.0f}"
              f"{price / price_sum:>10.1%}{cap / cap_sum:>10.1%}")
    divisor = price_sum / BASE_LEVEL
    print(f"  주가 합 {price_sum:,}원 → 제수 {divisor:,.0f} (지수 100 에 맞춘 값)")
    print(f"  시가총액 합 {cap_sum / EOK:,.0f}억원 → 기준 시가총액")
    print()
    return divisor, cap_sum


def print_one_day(divisor: float, base_cap: int) -> None:
    print("[2] 다음 날 — 가나정밀 +10%, 다라통신 -5%, 마바유통 보합")
    moves = {"가나정밀": 0.10, "다라통신": -0.05, "마바유통": 0.0}
    price_sum = 0.0
    cap_sum = 0.0
    print(f"  {'':10}{'등락':>7}{'새 주가':>10}{'주가 가중 기여':>14}{'시총 가중 기여':>14}")
    old_price_sum = sum(price for _, price, _, _ in STOCKS)
    for name, price, shares, _ in STOCKS:
        new_price = price * (1 + moves[name])
        price_sum += new_price
        cap_sum += new_price * shares
        # 기여도 = 그 종목의 비중 × 그 종목의 등락률
        price_contrib = price / old_price_sum * moves[name]
        cap_contrib = price * shares / base_cap * moves[name]
        print(f"  {name:10}{moves[name]:>+7.0%}{new_price:>10,.0f}{price_contrib:>+14.2%}{cap_contrib:>+14.2%}")
    price_index = price_sum / divisor
    cap_index = cap_sum / base_cap * BASE_LEVEL
    print(f"  주가 가중 지수     {BASE_LEVEL:.2f} → {price_index:.2f} ({price_index / BASE_LEVEL - 1:+.2%})")
    print(f"  시가총액 가중 지수 {BASE_LEVEL:.2f} → {cap_index:.2f} ({cap_index / BASE_LEVEL - 1:+.2%})")
    print("  같은 종목, 같은 등락인데 두 지수가 반대 방향으로 움직였다")
    print()


def print_split(divisor: float) -> None:
    print("[3] 가나정밀 1주 → 10주 액면분할 (분할 직전 주가 그대로 두고 계산)")
    before = {name: price for name, price, _, _ in STOCKS}
    after = dict(before)
    after["가나정밀"] = before["가나정밀"] / 10
    sum_before = sum(before.values())
    sum_after = sum(after.values())
    print(f"  주가 합 {sum_before:,.0f} → {sum_after:,.0f}")
    print(f"  제수를 그대로 두면 지수 {sum_before / divisor:.2f} → {sum_after / divisor:.2f}  (회사 값은 그대로인데 지수가 떨어진다)")
    new_divisor = divisor * sum_after / sum_before
    print(f"  새 제수 = {divisor:,.0f} × {sum_after:,.0f} ÷ {sum_before:,.0f} = {new_divisor:,.2f} → 지수 {sum_after / new_divisor:.2f}")
    after_weight = after["가나정밀"] / sum_after
    print(f"  분할 뒤 가나정밀의 주가 비중 {before['가나정밀'] / sum_before:.1%} → {after_weight:.1%}")
    print(f"  분할 뒤 가나정밀이 10% 오르면 주가 가중 지수는 {after_weight * 0.10:+.2%} 움직인다 (분할 전에는 {before['가나정밀'] / sum_before * 0.10:+.2%})")
    print("  시가총액 가중: 주식 수 ×10, 주가 ÷10 이라 시가총액이 그대로다 → 고칠 것이 없다")
    print()


def print_float_adjusted() -> None:
    print("[4] 유동비율을 곱하면 — 시가총액 가중 지수의 비중 (시가총액은 억원)")
    cap_sum = sum(price * shares for _, price, shares, _ in STOCKS)
    float_sum = sum(price * shares * ratio for _, price, shares, ratio in STOCKS)
    print(f"  {'':10}{'유동비율':>9}{'유동시가총액':>13}{'상장 기준':>10}{'유동 기준':>10}")
    for name, price, shares, ratio in STOCKS:
        cap = price * shares
        print(f"  {name:10}{ratio:>9.0%}{cap * ratio / EOK:>13,.0f}"
              f"{cap / cap_sum:>10.1%}{cap * ratio / float_sum:>10.1%}")
    print("  대주주가 70% 를 가진 마바유통은 시장에서 사고팔 수 있는 몫만큼만 비중을 받는다")
    print()


def main() -> None:
    print(f"Python {platform.python_version()} / {platform.system()}")
    print("종목: 가나정밀·다라통신·마바유통(모두 가상) / 숫자는 설명용 가정값")
    print()
    print_definitions()
    divisor, base_cap = print_base_weights()
    print_one_day(divisor, base_cap)
    print_split(divisor)
    print_float_adjusted()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
