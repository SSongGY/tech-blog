"""매출에서 당기순이익까지 단계마다 무엇을 빼는지 두 가상 회사로 계산한다.

가나전자와 다라물산은 매출도 200억, 당기순이익도 10억으로 같다. 그런데
단계별로 풀면 가나전자는 영업에서 번 이익을 이자로 깎였고, 다라물산은 영업에서
손실을 낸 것을 설비를 팔아 얻은 차익으로 메웠다. 비용은 기능별로 분류하고
영업이익은 K-IFRS 제1001호 문단 한138.2 정의(수익 − 매출원가 − 판매비와관리비)를
따른다. 금액 단위는 억원이고, 법인세는 계산을 단순하게 하려고 세전이익의 20%로 두었다.
"""

import platform
import sys

TAX_RATE = 0.20   # 실제 법인세율·세무조정과 무관한 가정값

COMPANIES = {
    "가나전자": {
        "매출액": 200, "매출원가": 140, "판매비와관리비": 40,
        "기타수익": 0, "기타비용": 0, "금융수익": 1, "금융원가": 8.5,
    },
    "다라물산": {
        "매출액": 200, "매출원가": 170, "판매비와관리비": 40,
        "기타수익": 25,   # 유형자산처분이익. 한 번 팔면 끝나는 이익이다
        "기타비용": 0, "금융수익": 0, "금융원가": 2.5,
    },
}


def steps(pl: dict) -> list[tuple[str, str, float]]:
    """(단계 이름, 그 단계에서 뺀 것, 남은 값)을 차례로 만든다."""
    gross = pl["매출액"] - pl["매출원가"]
    operating = gross - pl["판매비와관리비"]
    pretax = (operating + pl["기타수익"] - pl["기타비용"]
              + pl["금융수익"] - pl["금융원가"])
    tax = pretax * TAX_RATE
    net = pretax - tax
    return [
        ("매출액", "", pl["매출액"]),
        ("매출총이익", "− 매출원가", gross),
        ("영업이익", "− 판매비와관리비", operating),
        ("법인세비용차감전순이익", "± 기타손익·금융손익", pretax),
        ("당기순이익", "− 법인세비용", net),
    ]


def main() -> None:
    print(f"Python {sys.version.split()[0]} / {platform.system()}")
    print(f"단위: 억원 / 회사: 가나전자·다라물산(가상) / 법인세 = 세전이익 × {TAX_RATE:.0%}(가정)")

    print("\n[1] 항목 — 두 회사가 무엇을 벌고 썼나")
    names = list(next(iter(COMPANIES.values())))
    print("  항목              " + "".join(f"{c:>10}" for c in COMPANIES))
    for n in names:
        print(f"  {n:<14}" + "".join(f"{pl[n]:>12g}" for pl in COMPANIES.values()))

    results = {c: steps(pl) for c, pl in COMPANIES.items()}
    print("\n[2] 다섯 단계 — 남은 값과 매출액 대비 비율")
    for name, rows in results.items():
        print(f"  {name}")
        revenue = rows[0][2]
        for step, minus, value in rows:
            print(f"    {step:<14}{minus:<16}{value:>8g}  ({value / revenue:>6.1%})")

    print("\n[3] 단계 사이 차이 — 두 회사가 어디서 갈렸나 (가나 − 다라)")
    gana, dara = results["가나전자"], results["다라물산"]
    for (step, _, g), (_, _, d) in zip(gana, dara):
        print(f"  {step:<14}{g:>8g}{d:>8g}   차이 {g - d:>+6g}")

    print("\n[4] 내년에 설비 처분이 없다면 — 다른 항목은 그대로 두고 기타수익만 0으로")
    no_disposal = dict(COMPANIES["다라물산"], 기타수익=0)
    for step, _, value in steps(no_disposal)[2:]:
        print(f"  다라물산 {step:<14}{value:>8g}")


if __name__ == "__main__":
    main()
