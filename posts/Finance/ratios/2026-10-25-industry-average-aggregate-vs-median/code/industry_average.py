"""업종 평균을 세 가지 방식으로 구해 보고 셋이 갈리는 지점을 확인한다.

한국은행 기업경영분석은 업종별 재무비율을 '합산재무제표'에서 뽑는다.
개별 회사의 비율을 평균내는 것이 아니라 항목을 먼저 더한 뒤 나누므로,
결과는 금액 가중평균이 된다. 그 가중치가 어느 변수인지는 지표마다 다르다.

회사 이름과 숫자는 전부 가상이다.
"""

from statistics import median


def companies():
    """가상 업종 '정밀부품 제조업'에 속한 다섯 회사. 금액 단위는 억원."""
    return [
        # 이름, 자기자본, 부채총계, 매출액, 영업이익
        ("큰별정밀", 4000, 4000, 10000, 900),
        ("가온부품", 200, 400, 800, 40),
        ("늘품소재", 150, 450, 700, 21),
        ("밝은기계", 120, 480, 600, 12),
        ("한솔정공", 30, 570, 500, 5),
    ]


def quantiles(values):
    """1사분위·중앙값·3사분위. 선형보간 없이 하위/상위 절반의 중앙값을 쓴다."""
    s = sorted(values)
    half = len(s) // 2
    low = s[:half]
    high = s[half + 1:] if len(s) % 2 else s[half:]
    return median(low), median(s), median(high)


def print_dataset(rows):
    print("[1] 업종에 속한 다섯 회사 — 전부 가상 (억원)")
    print(f"{'':10}{'자기자본':>10}{'부채총계':>10}{'매출액':>10}{'영업이익':>10}"
          f"{'부채비율':>10}{'영업이익률':>12}")
    for name, equity, debt, sales, profit in rows:
        print(f"{name:10}{equity:>10}{debt:>10}{sales:>10}{profit:>10}"
              f"{debt / equity * 100:>10.1f}{profit / sales * 100:>12.1f}")


def three_averages(rows):
    debt_ratios = [d / e * 100 for _, e, d, _, _ in rows]
    margins = [p / s * 100 for _, _, _, s, p in rows]

    agg_debt = sum(d for _, _, d, _, _ in rows) / sum(e for _, e, _, _, _ in rows) * 100
    agg_margin = sum(p for _, _, _, _, p in rows) / sum(s for _, _, _, s, _ in rows) * 100

    print("\n[2] 같은 다섯 회사에서 나오는 세 개의 '업종 평균' (%)")
    print(f"{'':16}{'합산방식':>12}{'단순평균':>12}{'중앙값':>12}")
    print(f"{'부채비율':16}{agg_debt:>12.1f}"
          f"{sum(debt_ratios) / len(debt_ratios):>12.1f}{median(debt_ratios):>12.1f}")
    print(f"{'매출액영업이익률':16}{agg_margin:>12.2f}"
          f"{sum(margins) / len(margins):>12.2f}{median(margins):>12.2f}")
    return agg_debt, agg_margin, debt_ratios, margins


def weights(rows):
    """합산방식이 금액 가중평균이라는 것과, 지표마다 가중치 변수가 다르다는 것."""
    total_equity = sum(e for _, e, _, _, _ in rows)
    total_sales = sum(s for _, _, _, s, _ in rows)

    print("\n[3] 합산방식의 정체 — 지표마다 가중치로 쓰이는 금액이 다르다 (%)")
    print(f"{'':10}{'자기자본비중':>14}{'부채비율':>10}{'기여분':>10}"
          f"{'매출액비중':>12}{'영업이익률':>12}{'기여분':>10}")
    for name, equity, debt, sales, profit in rows:
        we, wm = equity / total_equity, sales / total_sales
        print(f"{name:10}{we * 100:>14.1f}{debt / equity * 100:>10.1f}"
              f"{we * debt / equity * 100:>10.1f}"
              f"{wm * 100:>12.1f}{profit / sales * 100:>12.1f}"
              f"{wm * profit / sales * 100:>10.2f}")


def verdict_flips(rows, agg_debt, agg_margin, debt_ratios, margins):
    """비교 대상 한 곳을 세 기준에 각각 견주면 판정이 뒤집힌다."""
    name, equity, debt, sales, profit = rows[1]
    my_debt, my_margin = debt / equity * 100, profit / sales * 100
    simple_debt = sum(debt_ratios) / len(debt_ratios)
    simple_margin = sum(margins) / len(margins)

    print(f"\n[4] {name}(부채비율 {my_debt:.1f}%, 영업이익률 {my_margin:.1f}%)을"
          f" 세 기준에 견주면")
    print(f"{'':16}{'기준값':>10}{'내 회사':>10}{'판정':>14}")
    for label, base, mine, lower_is_better in [
        ("부채비율·합산", agg_debt, my_debt, True),
        ("부채비율·단순평균", simple_debt, my_debt, True),
        ("부채비율·중앙값", median(debt_ratios), my_debt, True),
        ("이익률·합산", agg_margin, my_margin, False),
        ("이익률·단순평균", simple_margin, my_margin, False),
        ("이익률·중앙값", median(margins), my_margin, False),
    ]:
        better = (mine < base) if lower_is_better else (mine > base)
        print(f"{label:16}{base:>10.2f}{mine:>10.2f}"
              f"{'업종 평균보다 양호' if better else '업종 평균보다 미흡':>14}")


def distribution(debt_ratios, agg_debt):
    q1, med, q3 = quantiles(debt_ratios)
    print("\n[5] 분포 안에서 합산 평균의 자리 (%)")
    print(f"{'1사분위':>10}{'중앙값':>10}{'3사분위':>10}{'최댓값':>10}{'합산방식':>10}")
    print(f"{q1:>10.1f}{med:>10.1f}{q3:>10.1f}"
          f"{max(debt_ratios):>10.1f}{agg_debt:>10.1f}")
    below = sum(1 for r in debt_ratios if r < agg_debt)
    print(f"다섯 회사 중 합산 평균보다 낮은 곳: {below}곳")


def sample_change(rows):
    """어느 회사도 숫자가 변하지 않았는데 업종 평균만 움직이는 경우."""
    stayed = rows[:-1]
    dropped = rows[-1][0]

    def summary(group):
        ratios = [d / e * 100 for _, e, d, _, _ in group]
        agg = sum(d for _, _, d, _, _ in group) / sum(e for _, e, _, _, _ in group) * 100
        return agg, sum(ratios) / len(ratios), median(ratios)

    before, after = summary(rows), summary(stayed)
    print(f"\n[6] {dropped}이 결산월을 바꿔 작성대상에서 빠지면 (부채비율, %)")
    print(f"{'':16}{'전년':>10}{'당해':>10}{'변동':>10}")
    for label, b, a in zip(("합산방식", "단순평균", "중앙값"), before, after):
        print(f"{label:16}{b:>10.1f}{a:>10.1f}{a - b:>+10.1f}")
    print("남은 네 회사의 자기자본·부채는 한 숫자도 바뀌지 않았다.")


def mixed_business(rows):
    """겸업 기업은 매출 비중이 가장 큰 부문의 업종으로 통째 분류된다."""
    name, _, _, sales, _ = rows[0]
    manufacturing, distribution_ = 5500, 4500
    total_sales = sum(s for _, _, _, s, _ in rows)

    print(f"\n[7] {name}의 매출 {sales} 중 {distribution_}이 유통부문이라면 (억원, %)")
    print(f"{'':20}{'금액':>10}{'업종 매출 대비':>16}")
    print(f"{'업종 전체 매출':20}{total_sales:>10}{100.0:>16.1f}")
    print(f"{'그중 제조부문':20}{total_sales - distribution_:>10}"
          f"{(total_sales - distribution_) / total_sales * 100:>16.1f}")
    print(f"{'그중 유통부문':20}{distribution_:>10}"
          f"{distribution_ / total_sales * 100:>16.1f}")
    print(f"매출 비중이 큰 쪽이 제조({manufacturing}) 이므로 회사 전체가 제조업으로 분류된다.")


def main():
    rows = companies()
    print("환경: Python 3.13.5 · 표준 라이브러리 statistics")
    print("회사 이름과 금액은 계산 원리를 보이려고 만든 가상 값이다.\n")
    print_dataset(rows)
    agg_debt, agg_margin, debt_ratios, margins = three_averages(rows)
    weights(rows)
    verdict_flips(rows, agg_debt, agg_margin, debt_ratios, margins)
    distribution(debt_ratios, agg_debt)
    sample_change(rows)
    mixed_business(rows)


if __name__ == "__main__":
    main()
