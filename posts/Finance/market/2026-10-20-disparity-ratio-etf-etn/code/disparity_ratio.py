"""괴리율 — 기준가가 어떻게 만들어지고, 어느 문턱에서 무슨 조치가 붙는가.

가상 상장지수증권 '가나변동성 ETN'의 숫자로 계산한다. 실재하는 종목이 아니다.
문턱과 조치는 금융위원회 2026-08-12 보도자료에 적힌 2026-08-19 시행 기준이다.
"""

# 국내 자산만으로 구성된 기초지수 기준. 해외 자산이 섞이면 괄호 안 값이 쓰인다.
DISCLOSURE = {"국내형": 1.0, "해외형": 2.0}   # 괴리율 초과 공시 기준(초과 시)
LP_DUTY = {"국내형": 2.0, "해외형": 5.0}      # 유동성공급자 괴리율 관리의무 범위


def indicative_value(prev_iv, index_change_pct, annual_cost_pct, days=1):
    """전일 지표가치에 당일 기초지수 변화율을 반영하고 제비용을 일할로 뺀다."""
    moved = prev_iv * (1 + index_change_pct / 100)
    return moved * (1 - annual_cost_pct / 100 * days / 365)


def disparity(market_price, base_value):
    """괴리율(%) = (시장가격 − 기준가) ÷ 기준가 × 100."""
    return (market_price - base_value) / base_value * 100


def actions(ratio, kind):
    """하루치 괴리율 하나에 붙는 조치를 모은다. 2026-08-19 개정 기준 절댓값으로 본다."""
    r = abs(ratio)
    duty = LP_DUTY[kind]
    out = []
    if r > DISCLOSURE[kind]:
        out.append("공시")
    if r > duty:
        out.append("의무범위 밖")
    if r > duty * 2:
        out.append("예고 요건")
    if r >= duty * 3:
        out.append("정지 요건")
    return out or ["해당 없음"]


def designation(path, duty):
    """괴리율 경로를 날짜순으로 훑어 지정예고·지정 시점을 찾는다.

    예고 요건은 의무범위의 2배 초과, 지정 요건은 예고일부터 10거래일 이내 재초과다.
    """
    notice_day = None
    for day, ratio in enumerate(path, start=1):
        if abs(ratio) <= duty * 2:
            continue
        if notice_day is None:
            notice_day = day
        elif day - notice_day <= 10:
            return notice_day, day
    return notice_day, None


def main():
    print("[0] 산식")
    print("  괴리율(%) = (시장가격 − 기준가) ÷ 기준가 × 100")
    print("  기준가는 ETF 는 실시간 순자산가치(iNAV), ETN 은 실시간 지표가치(IIV) 다.")
    print()

    print("[1] 전일 지표가치에서 당일 실시간 지표가치로 — 가나변동성 ETN")
    prev_iv, index_change, annual_cost = 10250.00, 1.80, 0.95
    iv = indicative_value(prev_iv, index_change, annual_cost)
    moved = prev_iv * (1 + index_change / 100)
    print(f"  전일 지표가치(IV)         {prev_iv:>10,.2f} 원")
    print(f"  당일 기초지수 변화율       {index_change:>10.2f} %")
    print(f"  지수만 반영한 값           {moved:>10,.2f} 원")
    print(f"  연 제비용 {annual_cost}% 의 1일치    {-moved * annual_cost / 100 / 365:>10,.2f} 원")
    print(f"  실시간 지표가치(IIV)      {iv:>10,.2f} 원")
    for price in (10620, 10450, 10180):
        print(f"  시장가격 {price:>7,}원 → 괴리율 {disparity(price, iv):+7.2f} %")
    print()

    print("[2] 같은 괴리율에 붙는 조치 — 기초지수가 국내 자산인가 아닌가로 갈린다")
    print(f"  {'괴리율':>7}   {'국내형(공시 1% · 의무 2%)':<34}{'해외형(공시 2% · 의무 5%)'}")
    for ratio in (0.8, -1.5, 2.6, -4.3, 5.5, -6.4):
        dom = ", ".join(actions(ratio, "국내형"))
        ovs = ", ".join(actions(ratio, "해외형"))
        print(f"  {ratio:>+6.1f}%   {dom:<34}{ovs}")
    print()

    print("[3] 13 거래일 괴리율 경로 — 음수를 절댓값으로 세느냐로 판정이 갈린다")
    path = [1.2, 2.6, -4.3, -2.1, 0.8, -4.6, 1.1, 4.2, 0.5, -1.0, 1.8, 1.5, 6.4]
    duty = LP_DUTY["국내형"]
    print(f"  {'일차':>4}  {'괴리율':>8}  {'절댓값':>8}  관리의무 2% · 예고선 4% · 정지선 6%")
    for day, ratio in enumerate(path, start=1):
        marks = []
        if abs(ratio) > DISCLOSURE["국내형"]:
            marks.append("공시")
        if abs(ratio) > duty:
            marks.append("의무범위 밖")
        if abs(ratio) > duty * 2:
            marks.append("2배 초과")
        if abs(ratio) >= duty * 3:
            marks.append("3배 이상")
        print(f"  {day:>4}  {ratio:>+7.1f}%  {abs(ratio):>7.1f}%  {', '.join(marks) or '-'}")

    signed = [r for r in path]
    positive_only = [r if r > 0 else 0.0 for r in path]
    for label, series in (("절댓값으로 셀 때", signed), ("양수만 셀 때", positive_only)):
        notice, fixed = designation(series, duty)
        notice_txt = f"{notice}일차" if notice else "없음"
        fixed_txt = f"{fixed}일차" if fixed else "없음"
        print(f"  {label:<12} 지정예고 {notice_txt:<6} 지정 {fixed_txt}")

    print(f"  의무범위 밖인 날   {sum(1 for r in path if abs(r) > duty)} 일 / {len(path)} 일")
    print(f"  공시 대상인 날     {sum(1 for r in path if abs(r) > DISCLOSURE['국내형'])} 일 / {len(path)} 일")
    print("  지정 뒤 단일가매매 3거래일(11~13일차): 2% 이하가 3거래일 연속이어야 해제인데")
    print("  13일차가 6.4% 라 해제 요건을 못 채우고, 3배(6%) 이상이라 1거래일 거래정지가 붙는다.")


if __name__ == "__main__":
    main()
