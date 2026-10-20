"""채권 가격·만기수익률·듀레이션을 현재가치 정의만으로 계산한다.

발행체와 종목은 전부 가상이다. 실재하는 채권이 아니다.
국고채와 같은 조건(이표 6개월 후급, 액면 10,000원)을 본떴다.
"""

import sys

FACE = 10_000.0  # 액면가(원)
FREQ = 2  # 연 이표 지급 횟수 — 국고채는 매6월후급


def cashflows(coupon_rate, years):
    """(시점(년), 금액) 목록. 마지막 회차에 원금이 함께 실린다."""
    n = int(round(years * FREQ))
    coupon = FACE * coupon_rate / FREQ
    flows = []
    for k in range(1, n + 1):
        amount = coupon + (FACE if k == n else 0.0)
        flows.append((k / FREQ, amount))
    return flows


def price(flows, ytm):
    """만기수익률로 할인한 현재가치의 합. 연 2회 복리로 센다."""
    return sum(cf / (1 + ytm / FREQ) ** (t * FREQ) for t, cf in flows)


def ytm_from_price(flows, target, lo=-0.5, hi=1.0, tol=1e-12):
    """가격을 주고 할인율을 거꾸로 찾는다.

    가격은 수익률에 대해 단조감소하므로 이분법이 항상 수렴한다.
    닫힌 해가 없어서 실무에서도 이렇게 수치로 푼다.
    """
    for _ in range(300):
        mid = (lo + hi) / 2
        if price(flows, mid) > target:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return (lo + hi) / 2


def macaulay_duration(flows, ytm):
    """현금흐름의 가중평균 회수기간. 가중치는 현재가치 비중이다."""
    p = price(flows, ytm)
    weighted = sum(
        t * cf / (1 + ytm / FREQ) ** (t * FREQ) for t, cf in flows
    )
    return weighted / p


def modified_duration(flows, ytm):
    """맥컬레이 듀레이션을 (1 + ytm/FREQ) 로 나눈 값. 가격 변화율의 기울기다."""
    return macaulay_duration(flows, ytm) / (1 + ytm / FREQ)


def convexity(flows, ytm):
    """가격-수익률 곡선의 2차 계수. 듀레이션 근사가 남긴 오차를 메운다."""
    p = price(flows, ytm)
    acc = 0.0
    for t, cf in flows:
        m = t * FREQ
        acc += m * (m + 1) * cf / (1 + ytm / FREQ) ** (m + 2)
    return acc / p / FREQ**2


def rule(title):
    print()
    print("=" * 66)
    print(title)
    print("=" * 66)


BONDS = [
    # (종목명, 표면금리, 잔존만기(년))
    ("가나전자 3년물", 0.0325, 3),
    ("다라물산 3년물", 0.0100, 3),
    ("마바중공업 10년물", 0.0325, 10),
    ("사아리스 30년물", 0.0325, 30),
]

rule("1. 발행 조건 — 전부 가상 종목이다")
print(f"{'종목':<16}{'표면금리':>10}{'잔존만기':>10}{'이표주기':>10}{'액면':>12}")
for name, c, y in BONDS:
    print(f"{name:<16}{c * 100:>9.2f}%{y:>9}년{'6개월':>10}{FACE:>11,.0f}원")

rule("2. 가격은 할인율을 넣으면 그냥 나온다 — 역관계의 정체")
print("가나전자 3년물(표면금리 3.25%)의 수익률별 가격")
print(f"{'만기수익률':>10}{'가격(원)':>14}{'액면 대비':>12}")
for ytm in (0.0125, 0.0225, 0.0325, 0.0425, 0.0525):
    flows = cashflows(0.0325, 3)
    p = price(flows, ytm)
    tag = "할증" if p > FACE else ("액면" if abs(p - FACE) < 0.005 else "할인")
    print(f"{ytm * 100:>9.2f}%{p:>13,.2f}{p / FACE * 100:>10.2f}% {tag}")
print()
print("할인율이 분모에 있으니 올리면 모든 항이 작아진다. 가격과 수익률이")
print("반대로 움직이는 이유는 이 한 줄이 전부다.")

rule("3. 가격을 주고 수익률을 거꾸로 찾는다")
flows = cashflows(0.0325, 3)
for quoted in (9_600.0, 10_000.0, 10_400.0):
    y = ytm_from_price(flows, quoted)
    back = price(flows, y)
    print(
        f"가격 {quoted:>9,.2f}원 → 만기수익률 {y * 100:>6.3f}%"
        f"  (검산: 그 수익률로 다시 할인하면 {back:,.2f}원)"
    )
print()
print("표면금리 3.25% 채권이 액면보다 싸게 거래되면 수익률은 3.25%보다 높고,")
print("비싸게 거래되면 낮다. 액면가면 둘이 같다.")

rule("4. 듀레이션 — 현금흐름 회수의 무게중심")
print("가나전자 3년물, 만기수익률 3.25% 일 때 시점별 현재가치 비중")
flows = cashflows(0.0325, 3)
p = price(flows, 0.0325)
print(f"{'시점(년)':>9}{'현금흐름(원)':>14}{'현재가치(원)':>14}{'비중':>9}{'시점×비중':>11}")
acc = 0.0
for t, cf in flows:
    pv = cf / (1 + 0.0325 / FREQ) ** (t * FREQ)
    w = pv / p
    acc += t * w
    print(f"{t:>9.1f}{cf:>13,.2f}{pv:>14,.2f}{w * 100:>8.2f}%{t * w:>11.4f}")
print(f"{'합계':>9}{'':>13}{p:>14,.2f}{100.0:>8.2f}%{acc:>11.4f}")
print()
print(f"맥컬레이 듀레이션 = {acc:.4f}년  (잔존만기 3년보다 짧다)")
print(f"수정 듀레이션     = {modified_duration(flows, 0.0325):.4f}년")

rule("5. 무엇이 듀레이션을 늘리고 줄이는가")
print(f"{'종목':<16}{'표면금리':>9}{'잔존만기':>9}{'맥컬레이':>11}{'수정':>10}{'볼록성':>10}")
for name, c, y in BONDS:
    f = cashflows(c, y)
    md = macaulay_duration(f, 0.0325)
    print(
        f"{name:<16}{c * 100:>8.2f}%{y:>8}년{md:>10.4f}년"
        f"{modified_duration(f, 0.0325):>9.4f}{convexity(f, 0.0325):>10.2f}"
    )
print()
print("만기가 길수록 길어지고, 표면금리가 낮을수록 길어진다.")
print("표면금리가 낮으면 중간에 돌려받는 돈이 적어 무게가 뒤로 쏠린다.")

rule("6. 듀레이션으로 가격 변동을 재 본다 (수익률 +1%p)")
print(f"{'종목':<16}{'기준가격':>11}{'실제가격':>11}{'실제변동':>10}{'듀레이션근사':>13}{'오차':>9}")
for name, c, y in BONDS:
    f = cashflows(c, y)
    p0 = price(f, 0.0325)
    p1 = price(f, 0.0425)
    actual = (p1 - p0) / p0
    approx = -modified_duration(f, 0.0325) * 0.01
    print(
        f"{name:<16}{p0:>10,.2f}{p1:>11,.2f}{actual * 100:>9.3f}%"
        f"{approx * 100:>12.3f}%{(actual - approx) * 100:>8.3f}%p"
    )
print()
print("근사는 전부 실제보다 더 많이 떨어진다고 말한다. 가격-수익률 곡선이")
print("아래로 볼록해서, 직선으로 자르면 늘 아래를 지나기 때문이다.")

rule("7. 볼록성까지 넣으면 오차가 얼마나 줄어드는가")
print("사아리스 30년물, 수익률 변동 폭을 넓혀 가며")
f = cashflows(0.0325, 30)
p0 = price(f, 0.0325)
md = modified_duration(f, 0.0325)
cx = convexity(f, 0.0325)
print(f"{'변동폭':>8}{'실제변동':>11}{'듀레이션만':>12}{'+볼록성':>11}{'남은오차':>11}")
for bp in (-0.03, -0.01, -0.005, 0.005, 0.01, 0.03):
    actual = (price(f, 0.0325 + bp) - p0) / p0
    d_only = -md * bp
    d_cx = -md * bp + 0.5 * cx * bp**2
    print(
        f"{bp * 100:>+7.1f}%p{actual * 100:>10.3f}%{d_only * 100:>11.3f}%"
        f"{d_cx * 100:>10.3f}%{(actual - d_cx) * 100:>10.3f}%p"
    )
print()
print("1%p 안쪽이면 듀레이션만으로도 충분하지만, 3%p 를 움직이면")
print("듀레이션만 쓴 값은 한참 빗나간다.")

rule("8. 같은 1%p 라도 수익률 수준에 따라 타격이 다르다")
print("마바중공업 10년물의 수익률 수준별 수정 듀레이션")
f = cashflows(0.0325, 10)
print(f"{'기준 수익률':>11}{'수정 듀레이션':>14}{'+1%p 실제변동':>15}")
for base in (0.0100, 0.0325, 0.0600, 0.0900):
    md = modified_duration(f, base)
    p0 = price(f, base)
    actual = (price(f, base + 0.01) - p0) / p0
    print(f"{base * 100:>10.2f}%{md:>13.4f}년{actual * 100:>14.3f}%")
print()
print("수익률이 낮을수록 듀레이션이 길다. 저금리에서 금리가 오를 때")
print("장기채가 유난히 크게 흔들리는 이유가 여기에 있다.")

rule("9. 가격-수익률 곡선과 접선 — 도식에 쓴 좌표")
print("사아리스 30년물. 접선은 3.25% 에서의 수정 듀레이션으로 그은 직선이다.")
f = cashflows(0.0325, 30)
p0 = price(f, 0.0325)
slope = -modified_duration(f, 0.0325) * p0  # 수익률 1단위당 가격 변화
print(f"{'만기수익률':>10}{'실제가격(원)':>15}{'접선 위 가격(원)':>18}")
for i in range(13):
    y = 0.0025 + 0.005 * i
    tangent = p0 + slope * (y - 0.0325)
    print(f"{y * 100:>9.2f}%{price(f, y):>14,.2f}{tangent:>17,.2f}")
print()
print("곡선은 접선 위에 있거나 겹친다. 어디서 재도 그렇다.")

print()
print(f"[환경] Python {sys.version.split()[0]}")
