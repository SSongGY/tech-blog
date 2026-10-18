"""TCO·ROI·할인 순편익을 같은 자료로 계산해 순위가 어디서 갈리는지 본다.

세 가지를 차례로 계산한다.
1. 숨은 비용을 TCO 에 넣고 빼면 두 대안의 순위가 뒤집히는가
2. 할인율을 올리면 그 격차가 어떻게 움직이는가
3. 단순 ROI 가 같은 두 대안을 할인 순편익이 갈라놓는가

금액 단위는 백만 원, 기간은 5년이다. 숫자는 설명을 위해 지어낸 가상 사업의 값이고
실제 시세가 아니다. 할인계수는 OMB Circular A-94 부록 B 의 정의
1/(1+r)^t 를 그대로 쓴다.
"""

import sys

YEARS = 5

# --- 대안 두 가지 -------------------------------------------------------
# initial  : 0년차에 한 번 나가는 비용
# annual   : 1~5년 매년 나가는 비용
# onetime  : (연차, 금액) — 특정 해에만 나가는 비용
ALTERNATIVES = {
    "A. 자체 구축": {
        "visible": {"initial": 1000, "annual": 260, "onetime": []},
        "hidden": {
            "initial": 0,
            "annual": 50,                      # 계획에 없던 중단으로 잃는 업무 시간
            "onetime": [(1, 80), (5, 70)],     # 1년차 전환 교육, 5년차 폐기·데이터 이관
        },
    },
    "B. 구독 이용": {
        "visible": {"initial": 250, "annual": 430, "onetime": []},
        "hidden": {
            "initial": 0,
            "annual": 15,
            "onetime": [(1, 40), (5, 30)],     # 1년차 전환 교육, 5년차 계약 종료 반출
        },
    },
}


def discount_factor(rate, year):
    """OMB Circular A-94 부록 B: 할인계수 = 1/(1+r)^t"""
    return 1.0 / (1.0 + rate) ** year


def cost_stream(part):
    """연차별 비용 흐름을 만든다. 0년차는 초기 비용."""
    stream = [part["initial"]] + [part["annual"]] * YEARS
    for year, amount in part["onetime"]:
        stream[year] += amount
    return stream


def present_value(stream, rate):
    """0년차는 할인하지 않고, 1년차 이후를 연말 기준으로 할인한다."""
    return sum(amount * discount_factor(rate, year) for year, amount in enumerate(stream))


def total_cost(spec, *, with_hidden, rate=0.0):
    stream = cost_stream(spec["visible"])
    if with_hidden:
        hidden = cost_stream(spec["hidden"])
        stream = [v + h for v, h in zip(stream, hidden)]
    return present_value(stream, rate)


def line(title):
    print("\n" + "=" * 64)
    print(title)
    print("=" * 64)


def table(headers, rows):
    widths = [max(len(h), *(len(str(r[i])) for r in rows)) for i, h in enumerate(headers)]
    print("  " + " | ".join(h.ljust(w) for h, w in zip(headers, widths)))
    print("  " + "-+-".join("-" * w for w in widths))
    for row in rows:
        print("  " + " | ".join(str(c).rjust(w) if i else str(c).ljust(w)
                                for i, (c, w) in enumerate(zip(row, widths))))


def part1():
    line("1. 숨은 비용을 넣고 빼면 순위가 뒤집힌다 (할인 없음, 단위 백만 원)")
    rows = []
    for name, spec in ALTERNATIVES.items():
        visible = total_cost(spec, with_hidden=False)
        full = total_cost(spec, with_hidden=True)
        rows.append([name, f"{visible:,.0f}", f"{full - visible:,.0f}", f"{full:,.0f}"])
    table(["대안", "가시 비용", "숨은 비용", "TCO"], rows)

    names = list(ALTERNATIVES)
    visible = {n: total_cost(ALTERNATIVES[n], with_hidden=False) for n in names}
    full = {n: total_cost(ALTERNATIVES[n], with_hidden=True) for n in names}
    cheap_visible = min(visible, key=visible.get)
    cheap_full = min(full, key=full.get)
    print(f"\n  가시 비용만 보면 싼 쪽 : {cheap_visible} ({visible[cheap_visible]:,.0f})")
    print(f"  숨은 비용까지 넣으면  : {cheap_full} ({full[cheap_full]:,.0f})")
    print(f"  순위가 뒤집히는가     : {cheap_visible != cheap_full}")


def part2():
    line("2. 할인율을 올리면 초기 투자형이 더 불리해진다 (TCO 현재가치)")
    rows = []
    for rate in (0.0, 0.031, 0.05, 0.07):
        values = {n: total_cost(s, with_hidden=True, rate=rate) for n, s in ALTERNATIVES.items()}
        a, b = values["A. 자체 구축"], values["B. 구독 이용"]
        rows.append([f"{rate * 100:.1f}%", f"{a:,.0f}", f"{b:,.0f}", f"{a - b:+,.0f}"])
    table(["할인율", "A 현재가치", "B 현재가치", "A - B"], rows)
    print("\n  A - B 가 양수면 A 가 더 비싸다는 뜻이다.")


# --- 단순 ROI 가 같은 두 대안 -------------------------------------------
# 둘 다 0년차에 1,000 을 쓰고 5년 동안 1,500 을 거둔다. 거두는 시점만 다르다.
ROI_CASES = {
    "C. 편익이 앞에 몰린다": {"cost": 1000, "benefits": [0, 750, 750, 0, 0, 0]},
    "D. 편익이 뒤에 몰린다": {"cost": 1000, "benefits": [0, 0, 0, 0, 750, 750]},
}


def part3():
    line("3. 단순 ROI 가 같아도 할인 순편익은 갈린다 (할인율 3.1%)")
    rate = 0.031
    rows = []
    for name, case in ROI_CASES.items():
        total_benefit = sum(case["benefits"])
        roi = (total_benefit - case["cost"]) / case["cost"]
        pv_benefit = present_value(case["benefits"], rate)
        net = pv_benefit - case["cost"]
        bcr = pv_benefit / case["cost"]
        payback = next(
            (y for y in range(len(case["benefits"]))
             if sum(case["benefits"][: y + 1]) >= case["cost"]),
            None,
        )
        rows.append([
            name,
            f"{case['cost']:,}",
            f"{total_benefit:,}",
            f"{roi * 100:.1f}%",
            f"{pv_benefit:,.1f}",
            f"{net:+,.1f}",
            f"{bcr:.3f}",
            f"{payback}년",
        ])
    table(["대안", "비용", "총편익", "단순 ROI", "편익 현재가치",
           "할인 순편익", "편익비용비", "회수기간"], rows)
    print("\n  단순 ROI 는 두 대안을 구분하지 못하고, 할인 순편익은 구분한다.")


def main():
    print("=" * 64)
    print("IT 투자 평가 — TCO 와 ROI 계산 (가상 사업, 단위 백만 원, 5년)")
    print("=" * 64)
    print("  할인계수 = 1/(1+r)^t  (OMB Circular A-94 부록 B)")
    print("  0년차 비용은 할인하지 않고 1년차부터 연말 기준으로 할인한다.")
    part1()
    part2()
    part3()
    return 0


if __name__ == "__main__":
    sys.exit(main())
