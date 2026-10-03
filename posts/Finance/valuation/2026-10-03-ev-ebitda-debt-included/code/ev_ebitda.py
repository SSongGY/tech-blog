"""EV/EBITDA — 시가총액에 순차입금을 더해 회사 전체를 사는 값으로 이익을 잰다.

PER 이 똑같이 10배인 두 가상 회사가 차입금 구성만 달라 EV/EBITDA 가 두 배 갈리는
것을 계산한다. 이어서 EBITDA 가 같아도 감가상각·설비투자 규모가 다르면 무엇이
달라지는지, K-IFRS 제1116호 리스(2019-01-01 시행) 이후 리스부채를 EV 에 넣느냐에
따라 배수가 어떻게 어긋나는지 본다. 법인세는 단일 세율 22% 로 단순화한다(가정).
"""
import platform
import sys

TAX_RATE = 0.22
INTEREST_RATE = 0.05
TARGET_PER = 10.0  # 두 회사의 PER 을 일부러 같게 맞춘다


def net_income(operating_income: float, debt: float) -> float:
    return (operating_income - debt * INTEREST_RATE) * (1 - TAX_RATE)


def enterprise_value(market_cap: float, debt: float, cash: float) -> float:
    return market_cap + debt - cash


def print_definitions() -> None:
    print("[0] 산식")
    print("  EV        = 시가총액 + 차입금(이자부 부채) − 현금및현금성자산")
    print("  EBITDA    = 영업이익 + 감가상각비 + 무형자산상각비")
    print("  EV/EBITDA = EV ÷ EBITDA")
    print(f"  가정: 차입 이자율 {INTEREST_RATE:.0%}, 법인세율 {TAX_RATE:.0%} 단일 세율")
    print()


def print_same_per() -> None:
    print(f"[1] PER {TARGET_PER:.0f}배로 같은 두 회사 (단위: 억원)")
    companies = [
        # 이름, 영업이익, 감가상각비, 차입금, 현금
        ("하카기계", 150, 50, 100, 400),
        ("타파중공업", 150, 50, 900, 100),
    ]
    header = f"  {'':12}{'영업이익':>8}{'EBITDA':>8}{'차입금':>7}{'현금':>6}{'이자':>6}{'순이익':>8}{'시가총액':>8}{'EV':>8}{'PER':>8}{'EV/EBITDA':>11}"
    print(header)
    for name, op, da, debt, cash in companies:
        ni = net_income(op, debt)
        cap = ni * TARGET_PER
        ev = enterprise_value(cap, debt, cash)
        ebitda = op + da
        print(f"  {name:12}{op:>8}{ebitda:>8}{debt:>7}{cash:>6}{debt * INTEREST_RATE:>6.0f}"
              f"{ni:>8.1f}{cap:>8.0f}{ev:>8.0f}{cap / ni:>7.1f}배{ev / ebitda:>10.2f}배")
    print("  EBITDA 는 이자를 빼기 전 이익이라 두 회사가 같다. 순이익은 이자 차이만큼 갈린다")
    print()


def print_acquirer_view() -> None:
    print("[2] 지분 100% 를 시가총액에 산다면 실제로 치르는 값 (단위: 억원)")
    caps, evs = [], []
    for name, op, debt, cash in (("하카기계", 150, 100, 400), ("타파중공업", 150, 900, 100)):
        cap = round(net_income(op, debt) * TARGET_PER)
        ev = enterprise_value(cap, debt, cash)
        caps.append(cap)
        evs.append(ev)
        print(f"  {name:10} 지분 대가 {cap:>5,} + 떠안는 차입금 {debt:>4} − 손에 들어오는 현금 {cash:>4} = {ev:>5,}")
    print(f"  시가총액은 하카기계가 {caps[0] - caps[1]}억 크지만, 빚과 현금까지 넘겨받으면 타파중공업이 {evs[1] - evs[0]}억 비싸다")
    print()


def print_capex() -> None:
    print("[3] EBITDA 가 같아도 감가상각·설비투자가 다르면 (EV 1,600억으로 같다, 단위: 억원)")
    ev = 1_600
    print(f"  {'':10}{'EBITDA':>8}{'감가상각':>8}{'영업이익':>8}{'설비투자':>8}{'EBITDA−설비투자':>16}{'EV/EBITDA':>11}{'EV/EBIT':>9}")
    for name, ebitda, da, capex in (("라마소프트", 200, 50, 50), ("바사제철", 200, 150, 160)):
        ebit = ebitda - da
        print(f"  {name:10}{ebitda:>8}{da:>8}{ebit:>8}{capex:>8}{ebitda - capex:>16}{ev / ebitda:>10.2f}배{ev / ebit:>8.2f}배")
    print("  EBITDA 는 감가상각을 더해 놓은 값이라, 설비를 계속 새로 사야 하는 회사의 그 지출이 보이지 않는다")
    print()


def print_lease() -> None:
    print("[4] 리스 회계(K-IFRS 1116, 2019-01-01 시행) 전후 — 하카기계, 연간 건물 임차료 40억 (단위: 억원)")
    debt, cash = 100, 400
    cap = round(net_income(150, debt) * TARGET_PER)  # [1] 의 하카기계 시가총액
    lease_liability = 200       # 리스부채 (가정)
    annual_rent = 40
    ebitda_old = 200
    # 임차료가 영업비용에서 빠지고 감가상각비·이자비용(둘 다 EBITDA 아래)으로 옮겨 가므로
    # 둘을 어떻게 나누든 EBITDA 는 임차료만큼 커진다
    ebitda_new = ebitda_old + annual_rent
    ev_without = enterprise_value(cap, debt, cash)
    ev_with = enterprise_value(cap, debt + lease_liability, cash)
    rows = [
        ("이전 기준: 임차료가 영업비용", ev_without, ebitda_old),
        ("1116 이후 EBITDA, 리스부채는 EV 에서 뺌", ev_without, ebitda_new),
        ("1116 이후 EBITDA, 리스부채도 EV 에 넣음", ev_with, ebitda_new),
    ]
    print(f"  {'조합':40}{'EV':>7}{'EBITDA':>8}{'EV/EBITDA':>11}")
    for label, ev, ebitda in rows:
        print(f"  {label:40}{ev:>7}{ebitda:>8}{ev / ebitda:>10.2f}배")
    print("  둘째 줄은 분모에만 리스 효과가 들어가 배수가 낮게 나온다. 분자와 분모의 기준을 맞춰야 비교가 된다")
    print()


def main() -> None:
    print(f"Python {platform.python_version()} / {platform.system()}")
    print("회사: 하카기계·타파중공업·라마소프트·바사제철(모두 가상) / 이자율·세율·리스 금액은 설명용 가정값")
    print()
    print_definitions()
    print_same_per()
    print_acquirer_view()
    print_capex()
    print_lease()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
