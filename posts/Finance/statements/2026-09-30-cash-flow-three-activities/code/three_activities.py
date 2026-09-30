"""현금흐름표 세 갈래(영업·투자·재무)의 부호 조합으로 회사의 단계를 읽는다.

세 가상 회사의 현금흐름표를 항목부터 쌓아 올린다. 자차전자는 공장을 늘리는 중이고,
카타산업은 번 돈으로 설비를 유지하고 빚을 갚고 배당을 준다. 파하물산은 영업에서
현금이 새고 자산을 팔아 빚을 갚는다. 활동 구분은 K-IFRS 제1007호 문단 6·14·16·17을,
부호 조합과 단계의 대응은 Dickinson(2011)의 분류를 따른다. 금액 단위는 억원이다.

마지막으로 카타산업이 다음 해 창고 하나를 팔았을 때 한 줄 때문에 분류가 바뀌는 것을 본다.
"""

import itertools
import platform
import sys

# Dickinson(2011) 표 1: (영업, 투자, 재무) 부호 → 단계. 8가지 조합이 다섯 단계로 묶인다
STAGE = {
    ("-", "-", "+"): "도입기",
    ("+", "-", "+"): "성장기",
    ("+", "-", "-"): "성숙기",
    ("-", "-", "-"): "정체기",
    ("+", "+", "+"): "정체기",
    ("+", "+", "-"): "정체기",
    ("-", "+", "+"): "쇠퇴기",
    ("-", "+", "-"): "쇠퇴기",
}

# 항목마다 (활동, 금액). 유입은 +, 유출은 −. 0이 나오지 않게 숫자를 잡았다
COMPANIES = {
    "자차전자": [
        ("영업", "당기순이익", 60), ("영업", "감가상각비", 40), ("영업", "운전자본 증가", -30),
        ("투자", "설비 취득", -250),
        ("재무", "장기차입", 150), ("재무", "유상증자", 60),
    ],
    "카타산업": [
        ("영업", "당기순이익", 120), ("영업", "감가상각비", 90), ("영업", "운전자본 증가", -5),
        ("투자", "설비 취득", -100),
        ("재무", "차입금 상환", -40), ("재무", "배당금 지급", -60),
    ],
    "파하물산": [
        ("영업", "당기순손실", -90), ("영업", "감가상각비", 50), ("영업", "운전자본 감소", 10),
        ("투자", "설비 취득", -10), ("투자", "설비 처분", 70),
        ("재무", "차입금 상환", -40),
    ],
}

# 카타산업의 다음 해: 영업·재무는 그대로 두고 쓰지 않는 창고를 150에 판다
NEXT_YEAR = ("카타산업 이듬해", COMPANIES["카타산업"] + [("투자", "창고 처분", 150)])

ACTIVITIES = ("영업", "투자", "재무")


def totals(items: list) -> dict:
    return {a: sum(v for act, _, v in items if act == a) for a in ACTIVITIES}


def signs(t: dict) -> tuple:
    return tuple("+" if t[a] > 0 else "-" for a in ACTIVITIES)


def print_statement(name: str, items: list) -> dict:
    t = totals(items)
    print(f"\n  {name}")
    for act in ACTIVITIES:
        for a, label, v in items:
            if a == act:
                print(f"    {act}  {label:<10} {v:>6}")
        print(f"    {'':4}{act + '활동 합계':<10} {t[act]:>6}")
    print(f"    {'':4}{'현금 증감':<11} {sum(t.values()):>6}")
    return t


def main() -> None:
    print(f"Python {sys.version.split()[0]} / {platform.system()}")
    print("단위: 억원 / 회사: 자차전자·카타산업·파하물산(가상)")

    print("\n[1] Dickinson(2011) 분류 — 세 부호의 8가지 조합")
    print("  영업 투자 재무  단계")
    for combo in itertools.product("+-", repeat=3):
        print(f"   {combo[0]}    {combo[1]}    {combo[2]}   {STAGE[combo]}")

    print("\n[2] 항목에서 세 갈래 합계까지")
    results = {name: print_statement(name, items) for name, items in COMPANIES.items()}

    print("\n[3] 부호 조합과 단계")
    print("  회사        영업   투자   재무  부호     단계     영업CF ÷ 설비 취득")
    for name, t in results.items():
        capex = -sum(v for a, label, v in COMPANIES[name] if label == "설비 취득")
        # 영업에서 현금이 새는 회사는 이 비율이 뜻을 잃는다
        cover = f"{t['영업'] / capex:>6.2f}" if t["영업"] > 0 else "  해당 없음"
        print(f"  {name}  {t['영업']:>5} {t['투자']:>6} {t['재무']:>6}  {''.join(signs(t))}  "
              f"{STAGE[signs(t)]:<6}  {cover}")

    name, items = NEXT_YEAR
    print("\n[4] 한 줄이 분류를 바꾸는 경우")
    t = print_statement(name, items)
    print(f"\n  부호 {''.join(signs(t))} → {STAGE[signs(t)]}"
          f"  (영업활동 {t['영업']}, 재무활동 {t['재무']} — 둘 다 전년과 같다)")


if __name__ == "__main__":
    main()
