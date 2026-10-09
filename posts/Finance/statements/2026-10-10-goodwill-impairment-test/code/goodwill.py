"""영업권 — 인수 대가가 순자산보다 클 때 남는 숫자와 손상검사.

같은 피취득회사(하나소재)를 서로 다른 값에 사들인 가상 회사 셋을 놓는다.
영업권은 K-IFRS 제1103호 문단 32의 차액으로 계산하고, 대가가 순자산보다 작으면
염가매수차익(문단 34)이 된다. 1년 뒤 하나소재 사업(현금창출단위)의 회수가능액이
떨어졌을 때 제1036호 문단 104 순서로 손상차손을 배분하고, 그 다음 해 회수가능액이
회복돼도 영업권은 되돌리지 않는다(문단 124).

[1] 하나소재의 장부금액과 취득일 공정가치(문단 18)
[2] 인수 대가별 영업권과 염가매수차익
[3] 80%만 인수할 때 비지배지분 측정 방법(문단 19)에 따라 달라지는 영업권
[4] 1년 뒤 손상검사 — 같은 사업, 같은 회수가능액, 다른 손상차손
[5] 영업권을 넘는 손상은 다른 자산에 장부금액 비례로 배분(문단 104)
[6] 회수가능액이 회복된 다음 해 — 영업권은 환입하지 않는다(문단 124)

단순화: 하나소재는 인수 부채가 없고, 인수 후 1년간 자산 장부금액은 변하지 않는다고 둔다.
감가상각·법인세·이연법인세는 없다. 문단 105의 개별 자산 하한도 이 숫자에서는 걸리지 않는다.
금액 단위는 억원.
"""
import platform
import sys

# 하나소재의 식별 가능한 자산. 장부금액과 취득일 공정가치가 다르다
TARGET_ASSETS = {
    "토지": {"book": 100, "fair": 200},
    "건물·설비": {"book": 550, "fair": 600},
}

ACQUIRERS = {
    "가나전자": {"price": 1_000, "net_income": 300},
    "다라화학": {"price": 1_300, "net_income": 300},
    "마바산업": {"price": 700, "net_income": 300},
}

RECOVERABLE_YEAR1 = 950   # 1년 뒤 하나소재 사업의 회수가능액 — 누가 샀든 사업은 같다


def fair_net_assets() -> int:
    return sum(a["fair"] for a in TARGET_ASSETS.values())


def goodwill_or_gain(price: int, nci: int = 0, net_assets_share: int | None = None) -> tuple[int, int]:
    """문단 32: (이전대가 + 비지배지분) − 식별 가능한 순자산. 음수면 염가매수차익(문단 34)."""
    net = fair_net_assets() if net_assets_share is None else net_assets_share
    diff = price + nci - net
    return (diff, 0) if diff >= 0 else (0, -diff)


def print_target() -> None:
    print("[1] 하나소재 — 장부금액과 취득일 공정가치 (K-IFRS 제1103호 문단 18)")
    print(f"  {'자산':<10}{'장부금액':>10}{'공정가치':>10}")
    for name, a in TARGET_ASSETS.items():
        print(f"  {name:<10}{a['book']:>12,}{a['fair']:>12,}")
    book = sum(a["book"] for a in TARGET_ASSETS.values())
    print(f"  {'순자산':<10}{book:>12,}{fair_net_assets():>12,}   (인수 부채 없음)")
    print()


def print_goodwill() -> None:
    print("[2] 100% 인수 — 대가별 영업권 (문단 32·34)")
    print(f"  {'인수 회사':<10}{'이전대가':>10}{'공정가치 순자산':>14}{'영업권':>10}{'염가매수차익':>12}")
    for name, a in ACQUIRERS.items():
        gw, gain = goodwill_or_gain(a["price"])
        print(f"  {name:<10}{a['price']:>12,}{fair_net_assets():>16,}{gw:>12,}{gain:>14,}")
    print("  장부 순자산 650 이 아니라 공정가치 800 에서 뺀다 — 차이 150 은 토지·설비 평가 증가분")
    print()


def print_nci() -> None:
    print("[3] 80% 인수, 대가 800 — 비지배지분 측정 방법에 따른 영업권 (문단 19)")
    price, share = 800, 0.8
    proportionate = round(fair_net_assets() * (1 - share))     # 순자산의 비례적 몫
    fair_value_nci = 220                                        # 나머지 20% 지분의 공정가치(가정)
    for label, nci in (("순자산 비례 몫", proportionate), ("공정가치", fair_value_nci)):
        gw, _ = goodwill_or_gain(price, nci)
        print(f"  비지배지분 = {label:<10} {nci:>4}  →  영업권 = {price} + {nci} − {fair_net_assets()} = {gw}")
    print("  비례 몫 방식은 지배기업 몫의 영업권만, 공정가치 방식은 비지배지분 몫까지 올린다")
    print()


def impairment(goodwill: int, other_assets: dict[str, int], recoverable: int) -> dict:
    """문단 104: 손상차손은 영업권부터 줄이고, 남으면 다른 자산에 장부금액 비례로 배분한다."""
    carrying = goodwill + sum(other_assets.values())
    loss = max(0, carrying - recoverable)
    to_goodwill = min(loss, goodwill)
    rest = loss - to_goodwill
    base = sum(other_assets.values())
    to_others = {k: rest * v / base for k, v in other_assets.items()}
    return {"carrying": carrying, "loss": loss, "to_goodwill": to_goodwill,
            "goodwill_after": goodwill - to_goodwill, "to_others": to_others}


def print_impairment_year1() -> None:
    print(f"[4] 1년 뒤 손상검사 — 하나소재 사업의 회수가능액 {RECOVERABLE_YEAR1} (제1036호 문단 90·104)")
    others = {k: a["fair"] for k, a in TARGET_ASSETS.items()}
    print(f"  {'인수 회사':<10}{'영업권':>8}{'장부금액':>10}{'회수가능액':>10}{'손상차손':>10}"
          f"{'손상 후 영업권':>14}{'당기순이익':>14}")
    for name, a in ACQUIRERS.items():
        gw, gain = goodwill_or_gain(a["price"])
        r = impairment(gw, others, RECOVERABLE_YEAR1)
        before = a["net_income"]
        after = before - r["loss"]
        print(f"  {name:<10}{gw:>10,}{r['carrying']:>12,}{RECOVERABLE_YEAR1:>12,}{r['loss']:>12,}"
              f"{r['goodwill_after']:>14,}   {before:>4} → {after:>4}")
    print("  손상 전 당기순이익은 셋 다 300 으로 둔다 (마바산업의 인수 연도 염가매수차익 100 은 전년도 손익)")
    print()


def print_beyond_goodwill() -> None:
    print("[5] 다라화학, 회수가능액이 700 까지 떨어지면 (문단 104 배분 순서)")
    gw, _ = goodwill_or_gain(ACQUIRERS["다라화학"]["price"])
    others = {k: a["fair"] for k, a in TARGET_ASSETS.items()}
    r = impairment(gw, others, 700)
    print(f"  장부금액 {r['carrying']:,} − 회수가능액 700 = 손상차손 {r['loss']:,}")
    print(f"  ① 영업권         {gw:>5,} → {r['goodwill_after']:>5,}   ({r['to_goodwill']:,} 감액)")
    for k, v in r["to_others"].items():
        print(f"  ② {k:<10}{others[k]:>8,} → {others[k] - v:>8.1f}   ({v:.1f} 감액, 장부금액 비례)")
    print()


def print_no_reversal() -> None:
    print("[6] 그 다음 해 회수가능액이 1,300 으로 회복되면 (문단 124)")
    gw, _ = goodwill_or_gain(ACQUIRERS["다라화학"]["price"])
    others = {k: a["fair"] for k, a in TARGET_ASSETS.items()}
    r = impairment(gw, others, RECOVERABLE_YEAR1)
    print(f"  다라화학 영업권: 인수 시 {gw} → 1년 뒤 손상 후 {r['goodwill_after']} → 회복 후에도 {r['goodwill_after']}")
    print("  영업권에 인식한 손상차손은 후속 기간에 환입하지 않는다")
    print()


def main() -> None:
    print(f"Python {platform.python_version()} · {sys.platform}")
    print()
    print_target()
    print_goodwill()
    print_nci()
    print_impairment_year1()
    print_beyond_goodwill()
    print_no_reversal()


if __name__ == "__main__":
    main()
