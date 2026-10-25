"""배당할인모형(고든 성장모형)을 가상 회사 둘로 계산한다.

Gordon & Shapiro(1956)의 원식은 연속복리 가정에서 P0 = D0/(k-g) 이고,
교과서가 쓰는 이산 형태는 P0 = D1/(k-g) 다. 같은 입력에서 두 값이
(1+g) 배만큼 갈린다. 성장률이 요구수익률에 가까워질 때 값이 발산하는 구간과,
자기자본이익률이 요구수익률보다 높은지 낮은지에 따라 배당성향의 효과가
뒤집히는 것도 함께 확인한다.

회사 이름과 숫자는 전부 가상이다.
"""

K = 0.11  # 요구수익률. 설명용 가정값이다.


def price_discrete(d0, k, g):
    """교과서 형태. 1기 뒤 배당을 분자에 둔다."""
    return d0 * (1 + g) / (k - g)


def price_continuous(d0, k, g):
    """Gordon & Shapiro(1956) 식 (7). 연속 배당·연속 할인 가정."""
    return d0 / (k - g)


def company(name, book_value, roe, payout):
    """주당 장부가와 자기자본이익률, 배당성향에서 나머지를 끌어낸다."""
    income = book_value * roe
    dividend = income * payout
    retention = 1 - payout
    return {
        "name": name,
        "book": book_value,
        "roe": roe,
        "payout": payout,
        "income": income,
        "dividend": dividend,
        "growth": retention * roe,  # g = br
    }


def print_inputs(firms):
    print("[1] 가상 회사 둘의 주당 수치 — 요구수익률은 둘 다 11.0% 로 둔다 (원, %)")
    print(f"{'':10}{'장부가':>10}{'ROE':>8}{'순이익':>10}{'배당성향':>10}"
          f"{'배당':>10}{'유보율':>8}{'g=br':>8}")
    for f in firms:
        print(f"{f['name']:10}{f['book']:>10,.0f}{f['roe'] * 100:>8.1f}"
              f"{f['income']:>10,.0f}{f['payout'] * 100:>10.1f}"
              f"{f['dividend']:>10,.0f}{(1 - f['payout']) * 100:>8.1f}"
              f"{f['growth'] * 100:>8.1f}")


def two_forms(firm):
    g, d0 = firm["growth"], firm["dividend"]
    disc, cont = price_discrete(d0, K, g), price_continuous(d0, K, g)
    print(f"\n[2] {firm['name']} — 같은 입력에서 나오는 두 개의 값 (원)")
    print(f"{'':28}{'분자':>12}{'분모':>10}{'주당가치':>12}")
    print(f"{'이산 P0 = D1/(k-g)':28}{d0 * (1 + g):>12,.0f}{K - g:>10.4f}{disc:>12,.0f}")
    print(f"{'연속 P0 = D0/(k-g)':28}{d0:>12,.0f}{K - g:>10.4f}{cont:>12,.0f}")
    print(f"두 값의 비는 {disc / cont:.4f} 로 (1+g) 와 같다.")
    return disc, cont


def recover_k(firm, price_cont):
    """원 논문 식 (8): k = D0/P0 + g. 연속 형태의 값에서 요구수익률이 되돌아온다."""
    d0, g = firm["dividend"], firm["growth"]
    print(f"\n[3] {firm['name']} — 식 (8) 로 요구수익률을 되돌리면 (%)")
    print(f"{'':24}{'배당수익률':>12}{'성장률 g':>12}{'합계 k':>10}")
    print(f"{'연속 형태의 값 기준':24}{d0 / price_cont * 100:>12.2f}"
          f"{g * 100:>12.2f}{(d0 / price_cont + g) * 100:>10.2f}")


def book_equals_price(firm):
    """원 논문 식 (10)(11): 장부가와 시장가가 같으면 이익수익률 y 와 k 가 같아진다."""
    b, y0, d0, g = firm["book"], firm["income"], firm["dividend"], firm["growth"]
    print(f"\n[4] {firm['name']} — 값이 장부가와 같을 때 두 수익률 (원, %)")
    print(f"{'':16}{'가격':>12}{'이익수익률 y':>14}{'k = D/P + br':>14}")
    for label, p in [("장부가와 같을 때", b), ("연속 형태의 값", price_continuous(d0, K, g))]:
        print(f"{label:16}{p:>12,.0f}{y0 / p * 100:>14.2f}{(d0 / p + g) * 100:>14.2f}")


def divergence(firm):
    d0 = firm["dividend"]
    print(f"\n[5] {firm['name']} — 성장률이 요구수익률 11.0% 에 다가갈 때 (원, %)")
    print(f"{'g':>8}{'k-g':>10}{'분자 D1':>12}{'주당가치':>14}{'g=8.0% 대비':>14}")
    base = price_discrete(d0, K, 0.08)
    for g in (0.04, 0.06, 0.08, 0.09, 0.10, 0.105, 0.109):
        p = price_discrete(d0, K, g)
        print(f"{g * 100:>8.1f}{(K - g) * 100:>10.1f}{d0 * (1 + g):>12,.0f}"
              f"{p:>14,.0f}{p / base:>13.1f}배")
    print(f"{11.0:>8.1f}{0.0:>10.1f}{'—':>12}{'정의되지 않음':>14}{'':>14}")
    print(f"{12.0:>8.1f}{-1.0:>10.1f}{d0 * 1.12:>12,.0f}"
          f"{price_discrete(d0, K, 0.12):>14,.0f}{'음수 — 뜻이 없다':>14}")


def sensitivity(firm):
    d0, g = firm["dividend"], firm["growth"]
    base = price_discrete(d0, K, g)
    print(f"\n[6] {firm['name']} — 가정을 0.5%p 씩 흔들면 (원, %)")
    print(f"{'':22}{'g':>8}{'k':>8}{'주당가치':>12}{'변화':>10}")
    for label, dg, dk in [("기준", 0, 0), ("g 를 +0.5%p", 0.005, 0),
                          ("g 를 -0.5%p", -0.005, 0), ("k 를 +0.5%p", 0, 0.005),
                          ("k 를 -0.5%p", 0, -0.005)]:
        p = price_discrete(d0, K + dk, g + dg)
        print(f"{label:22}{(g + dg) * 100:>8.1f}{(K + dk) * 100:>8.1f}"
              f"{p:>12,.0f}{(p / base - 1) * 100:>+9.1f}%")


def payout_effect(tag, book_value, roe, label):
    print(f"\n[{tag}] {label} ROE {roe * 100:.1f}% 일 때 배당성향을 바꾸면 (원, %)")
    print(f"{'배당성향':>10}{'배당 D0':>12}{'g=br':>10}{'k-g':>10}{'주당가치':>16}")
    for payout in (1.0, 0.8, 0.6, 0.4, 0.2, 0.0):
        f = company("", book_value, roe, payout)
        g, d0 = f["growth"], f["dividend"]
        if payout == 0:
            value = "배당이 0 — 적용 불가"
        elif g >= K:
            value = "g ≥ k — 발산"
        else:
            value = f"{price_discrete(d0, K, g):,.0f}"
        print(f"{payout * 100:>10.1f}{d0:>12,.0f}{g * 100:>10.1f}"
              f"{(K - g) * 100:>10.1f}{value:>16}")


def two_stage(d0, high_g, years, stable_g):
    print(f"\n[9] 2단계 모형 — {years}년간 {high_g * 100:.1f}% 로 자란 뒤"
          f" {stable_g * 100:.1f}% 로 내려앉으면 (원)")
    print(f"{'연차':>6}{'배당':>12}{'할인계수':>12}{'현재가치':>12}")
    pv_dividends = 0.0
    d = d0
    for t in range(1, years + 1):
        d *= 1 + high_g
        factor = (1 + K) ** t
        pv = d / factor
        pv_dividends += pv
        print(f"{t:>6}{d:>12,.0f}{factor:>12.4f}{pv:>12,.0f}")
    terminal = d * (1 + stable_g) / (K - stable_g)
    pv_terminal = terminal / (1 + K) ** years
    total = pv_dividends + pv_terminal
    print(f"{'배당 현재가치 합':>18}{pv_dividends:>24,.0f}")
    print(f"{'종가치(5년 말)':>18}{terminal:>24,.0f}")
    print(f"{'종가치의 현재가치':>18}{pv_terminal:>24,.0f}")
    print(f"{'주당가치 합계':>18}{total:>24,.0f}")
    print(f"값의 {pv_terminal / total * 100:.1f}% 가 종가치에서 나온다.")


def main():
    print("환경: Python 3.13.5 · 표준 라이브러리만 사용")
    print("회사 이름과 금액은 계산 원리를 보이려고 만든 가상 값이다.")
    print(f"요구수익률 k 는 {K * 100:.1f}% 로 고정한 가정값이다.\n")

    haneul = company("하늘제과", 25000, 0.20, 0.60)
    yeoul = company("여울전기", 25000, 0.09, 0.60)
    print_inputs([haneul, yeoul])

    _, cont = two_forms(haneul)
    recover_k(haneul, cont)
    book_equals_price(haneul)
    divergence(haneul)
    sensitivity(haneul)
    payout_effect(7, 25000, 0.20, "하늘제과처럼")
    payout_effect(8, 25000, 0.09, "여울전기처럼")
    two_stage(1000, 0.20, 5, 0.04)


if __name__ == "__main__":
    main()
