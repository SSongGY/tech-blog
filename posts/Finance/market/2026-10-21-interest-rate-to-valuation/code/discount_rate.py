"""할인율이 1%p 바뀔 때 기업가치가 얼마나 움직이는지 계산한다.

두 회사는 전부 가상이다. 실재하는 기업과 관계가 없다.
현재 기업가치를 같은 금액으로 맞춰 놓고, 현금흐름이 들어오는 시점만 다르게
설계했다. 보이고 싶은 것이 "시점 분포가 민감도를 정한다"는 하나이기 때문이다.
"""

import sys

HORIZON = 200  # 영구현금흐름을 명시적으로 펼쳐 보는 햇수
BASE_R = 0.08  # 기준 할인율


class Firm:
    def __init__(self, name, fcf1, high_growth, high_years, terminal_growth):
        self.name = name
        self.fcf1 = fcf1  # 1년 차 잉여현금흐름(억원)
        self.high_growth = high_growth  # 고성장 구간 성장률
        self.high_years = high_years  # 고성장 구간 햇수
        self.terminal_growth = terminal_growth  # 그 뒤 영구 성장률

    def scaled(self, factor):
        return Firm(
            self.name,
            self.fcf1 * factor,
            self.high_growth,
            self.high_years,
            self.terminal_growth,
        )

    def flows(self, years=HORIZON):
        """연도별 잉여현금흐름. 고성장 구간이 끝나면 영구 성장률로 넘어간다."""
        out = []
        cf = self.fcf1
        for t in range(1, years + 1):
            out.append((t, cf))
            g = self.high_growth if t < self.high_years else self.terminal_growth
            cf *= 1 + g
        return out

    def value(self, r, years=HORIZON):
        return sum(cf / (1 + r) ** t for t, cf in self.flows(years))

    def value_gordon(self, r):
        """고성장 구간은 그대로 할인하고 그 뒤는 영구성장모형으로 닫는다.

        flows() 와 같은 현금흐름을 써야 두 값을 맞대 볼 수 있다.
        """
        total = 0.0
        last = 0.0
        for t, cf in self.flows(self.high_years):
            total += cf / (1 + r) ** t
            last = cf
        nxt = last * (1 + self.terminal_growth)  # high_years+1 년 차
        terminal = nxt / (r - self.terminal_growth)
        return total + terminal / (1 + r) ** self.high_years

    def duration(self, r, years=HORIZON):
        """현재가치로 가중한 평균 회수 시점. 채권 듀레이션과 같은 정의다."""
        v = self.value(r, years)
        return sum(t * cf / (1 + r) ** t for t, cf in self.flows(years)) / v


def rule(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


mature = Firm("다라중공업", fcf1=1_000.0, high_growth=0.010, high_years=10,
              terminal_growth=0.010)
growth_raw = Firm("가나소프트", fcf1=100.0, high_growth=0.250, high_years=10,
                  terminal_growth=0.040)

# 두 회사의 현재 기업가치를 같게 맞춘다. 가치는 fcf1 에 비례하므로 배수 하나면 된다.
target = mature.value(BASE_R)
growth = growth_raw.scaled(target / growth_raw.value(BASE_R))
FIRMS = [mature, growth]

rule("1. 두 가상 회사 — 현재가치는 같고 시점 분포만 다르다")
print(f"{'회사':<12}{'1년차 FCF':>13}{'고성장률':>10}{'고성장 햇수':>12}{'영구성장률':>11}")
for f in FIRMS:
    print(
        f"{f.name:<12}{f.fcf1:>12,.1f}억{f.high_growth * 100:>9.1f}%"
        f"{f.high_years:>11}년{f.terminal_growth * 100:>10.1f}%"
    )
print()
print(f"할인율 {BASE_R * 100:.0f}% 기준 기업가치")
for f in FIRMS:
    print(f"  {f.name}: {f.value(BASE_R):,.1f}억원")
print()
print("영구현금흐름을 200년까지 펼쳐 더한 값이다. 영구성장모형으로 닫은 값과")
print("얼마나 차이 나는지 확인한다 — 잘라낸 꼬리가 무시할 만한지 봐야 한다.")
for f in FIRMS:
    a, b = f.value(BASE_R), f.value_gordon(BASE_R)
    print(f"  {f.name}: 펼침 {a:,.2f}억 / 모형 {b:,.2f}억 / 차이 {(a - b) / b * 100:+.4f}%")

rule("2. 현금흐름이 언제 들어오는가 — 앞 20년의 현재가치 비중")
for f in FIRMS:
    v = f.value(BASE_R)
    print()
    print(f"[{f.name}]  할인율 {BASE_R * 100:.0f}%")
    print(f"{'연차':>6}{'FCF(억)':>12}{'현재가치(억)':>14}{'비중':>9}{'누적비중':>10}")
    acc = 0.0
    for t, cf in f.flows(20):
        pv = cf / (1 + BASE_R) ** t
        acc += pv / v
        print(f"{t:>6}{cf:>11,.1f}{pv:>13,.1f}{pv / v * 100:>8.2f}%{acc * 100:>9.2f}%")
    print(f"{'21년~':>6}{'':>11}{v - v * acc:>13,.1f}{(1 - acc) * 100:>8.2f}%{100.0:>9.2f}%")

rule("3. 주식 듀레이션 — 투자금이 평균적으로 회수되는 시점")
print(f"{'회사':<12}{'듀레이션':>12}{'앞 10년 비중':>14}{'앞 20년 비중':>14}")
for f in FIRMS:
    v = f.value(BASE_R)
    w10 = sum(cf / (1 + BASE_R) ** t for t, cf in f.flows(10)) / v
    w20 = sum(cf / (1 + BASE_R) ** t for t, cf in f.flows(20)) / v
    print(
        f"{f.name:<12}{f.duration(BASE_R):>11.2f}년"
        f"{w10 * 100:>13.2f}%{w20 * 100:>13.2f}%"
    )
print()
print("채권 듀레이션과 정의가 같다. 현금흐름이 뒤로 갈수록 길어진다.")

rule("4. 할인율을 올리면 — 같은 1%p 에 가치가 얼마나 빠지는가")
print(f"{'할인율':>8}", end="")
for f in FIRMS:
    print(f"{f.name + ' 가치':>18}{'변동':>10}", end="")
print()
for r in (0.06, 0.07, 0.08, 0.09, 0.10, 0.11):
    print(f"{r * 100:>7.0f}%", end="")
    for f in FIRMS:
        v = f.value(r)
        base = f.value(BASE_R)
        print(f"{v:>17,.1f}억{(v - base) / base * 100:>9.2f}%", end="")
    print()
print()
print("8%에서 9%로 1%p 올렸을 때:")
for f in FIRMS:
    base = f.value(BASE_R)
    up = f.value(BASE_R + 0.01)
    approx = -f.duration(BASE_R) / (1 + BASE_R) * 0.01
    print(
        f"  {f.name}: {(up - base) / base * 100:+.2f}%"
        f"  (듀레이션 근사 {approx * 100:+.2f}%)"
    )

rule("5. 영구성장모형에서 민감도가 터지는 자리")
print("P = FCF / (r - g). 분모가 작아질수록 같은 1%p 가 더 크게 때린다.")
print(f"{'r':>6}{'g':>6}{'r-g':>7}{'가치(억)':>13}{'r +1%p 가치':>15}{'변동':>10}")
for r, g in ((0.12, 0.01), (0.10, 0.02), (0.08, 0.03), (0.07, 0.05), (0.065, 0.055)):
    v0 = 100.0 / (r - g)
    v1 = 100.0 / (r + 0.01 - g)
    print(
        f"{r * 100:>5.1f}%{g * 100:>5.1f}%{(r - g) * 100:>6.1f}%"
        f"{v0:>12,.1f}{v1:>14,.1f}{(v1 - v0) / v0 * 100:>9.2f}%"
    )
print()
print("1년 차 현금흐름을 100억으로 고정했다. r-g 가 1%p 로 좁혀지면")
print("할인율 1%p 가 가치의 절반을 가져간다.")

rule("6. 할인율은 금리 하나로 되어 있지 않다")
print("할인율 = 무위험이자율 + 리스크프리미엄")
print("기준금리가 1%p 올라도 리스크프리미엄이 같이 움직이면 결과가 달라진다.")
print(f"{'시나리오':<28}{'무위험':>8}{'프리미엄':>10}{'할인율':>8}{'가나소프트':>13}{'다라중공업':>13}")
scenarios = [
    ("출발점", 0.035, 0.045),
    ("금리만 +1%p", 0.045, 0.045),
    ("금리 +1%p, 프리미엄 -0.5%p", 0.045, 0.040),
    ("금리 +1%p, 프리미엄 +1%p", 0.045, 0.055),
]
base_vals = {f.name: f.value(BASE_R) for f in FIRMS}
for label, rf, prem in scenarios:
    r = rf + prem
    cells = ""
    for f in (growth, mature):
        v = f.value(r)
        cells += f"{(v - base_vals[f.name]) / base_vals[f.name] * 100:>12.2f}%"
    print(f"{label:<28}{rf * 100:>7.1f}%{prem * 100:>9.1f}%{r * 100:>7.1f}%{cells}")
print()
print("금리가 오르는데 경기 전망이 좋아져 프리미엄이 내리면 할인율은 덜 오른다.")
print("기준금리 인상이 곧바로 같은 폭의 할인율 상승은 아니다.")

rule("7. 10년 구간별 현재가치 비중 — 도식에 쓴 값")
buckets = [(1, 10), (11, 20), (21, 30), (31, 40), (41, 50)]
print(f"{'구간':>10}", end="")
for f in FIRMS:
    print(f"{f.name:>14}", end="")
print()
for lo, hi in buckets:
    print(f"{f'{lo}~{hi}년':>10}", end="")
    for f in FIRMS:
        v = f.value(BASE_R)
        share = sum(
            cf / (1 + BASE_R) ** t for t, cf in f.flows(hi) if t >= lo
        ) / v
        print(f"{share * 100:>13.2f}%", end="")
    print()
print(f"{'51년~':>10}", end="")
for f in FIRMS:
    v = f.value(BASE_R)
    share = 1 - sum(cf / (1 + BASE_R) ** t for t, cf in f.flows(50)) / v
    print(f"{share * 100:>13.2f}%", end="")
print()
print(f"{'듀레이션':>10}", end="")
for f in FIRMS:
    print(f"{f.duration(BASE_R):>12.2f}년", end="")
print()

print()
print(f"[환경] Python {sys.version.split()[0]}")
