"""가상 회사 사아산업의 부문 자료로 보고부문을 가려 본다.

K-IFRS 제1108호가 정한 양적기준(문단 13)과 외부수익 75% 기준(문단 15)을 그대로 적용해
여덟 개 영업부문 가운데 어느 것이 별도 보고 대상인지 판정하고, 전사 합계 하나만 볼 때와
부문별로 나눠 볼 때 무엇이 달라지는지 비교한다. 금액 단위는 억원이고 파이썬 표준
라이브러리만 쓴다.
"""

import sys

# (부문명, 외부고객 수익, 내부거래 수익, 부문당기손익, 부문자산)
SEGMENTS = [
    ("가전", 2000, 0, 250, 1800),
    ("반도체장비", 1500, 0, 210, 1500),
    ("소재", 700, 400, -160, 1200),
    ("물류", 200, 600, 50, 450),
    ("헬스케어", 520, 0, -120, 640),
    ("디스플레이", 700, 0, 45, 620),
    ("소프트웨어", 600, 0, 40, 380),
    ("신사업", 350, 0, -50, 330),
]

UNALLOCATED_HQ_COST = -80   # 어느 부문에도 배분하지 않은 본사 공통비


def revenue(seg):
    return seg[1] + seg[2]


def thresholds():
    """문단 13 의 세 가지 기준선을 구한다."""
    total_revenue = sum(revenue(s) for s in SEGMENTS)
    profits = sum(s[3] for s in SEGMENTS if s[3] > 0)
    losses = abs(sum(s[3] for s in SEGMENTS if s[3] < 0))
    # 손익 기준의 분모는 이익 합계와 손실 합계의 절대치 가운데 큰 금액이다
    profit_base = max(profits, losses)
    total_assets = sum(s[4] for s in SEGMENTS)
    return {
        "수익": (total_revenue, total_revenue * 0.10),
        "손익": (profit_base, profit_base * 0.10),
        "자산": (total_assets, total_assets * 0.10),
        "이익합계": profits,
        "손실합계": losses,
    }


def quantitative_test(th):
    """세 기준 가운데 하나라도 넘으면 별도 보고 대상이다."""
    rows = []
    for seg in SEGMENTS:
        name = seg[0]
        hit_rev = revenue(seg) >= th["수익"][1]
        hit_pl = abs(seg[3]) >= th["손익"][1]
        hit_asset = seg[4] >= th["자산"][1]
        rows.append((name, hit_rev, hit_pl, hit_asset, hit_rev or hit_pl or hit_asset))
    return rows


def seventy_five_percent(reportable):
    """문단 15 — 보고부문의 외부수익 합계가 기업전체 수익의 75% 에 이르는지 본다."""
    entity_external = sum(s[1] for s in SEGMENTS)
    covered = sum(s[1] for s in SEGMENTS if s[0] in reportable)
    return entity_external, covered, covered / entity_external


def main():
    print(f"[0] 환경 — Python {sys.version.split()[0]}")
    print("    가상 회사 사아산업. 금액 단위는 억원이다.")

    print("\n[1] 최고영업의사결정자에게 보고되는 부문 자료")
    print(f"    {'부문':<12}{'외부수익':>10}{'내부거래':>10}{'부문수익':>10}{'부문손익':>10}{'부문자산':>10}")
    for seg in SEGMENTS:
        print(f"    {seg[0]:<12}{seg[1]:>10,}{seg[2]:>10,}{revenue(seg):>10,}{seg[3]:>10,}{seg[4]:>10,}")

    entity_external = sum(s[1] for s in SEGMENTS)
    segment_pl = sum(s[3] for s in SEGMENTS)
    entity_pl = segment_pl + UNALLOCATED_HQ_COST
    entity_margin = entity_pl / entity_external * 100
    print("\n[2] 전사 숫자 하나로 볼 때")
    print(f"    기업전체 수익                         {entity_external:>10,}")
    print(f"    부문손익 합계                         {segment_pl:>10,}")
    print(f"    배분하지 않은 본사 공통비              {UNALLOCATED_HQ_COST:>10,}")
    print(f"    법인세비용차감전순이익                 {entity_pl:>10,}")
    print(f"    기업전체 이익률                       {entity_margin:>9.1f}%")
    print("    이 한 줄만 보면 부문별로 무엇이 벌고 무엇이 까먹는지 알 수 없다.")

    th = thresholds()
    print("\n[3] 양적기준의 기준선 (문단 13)")
    print(f"    부문수익 합계 {th['수익'][0]:,} 의 10%          {th['수익'][1]:>10,.1f}")
    print(f"    이익 합계 {th['이익합계']:,} 와 손실 합계 {th['손실합계']:,} 중 큰 금액의 10%"
          f"   {th['손익'][1]:>6,.1f}")
    print(f"    부문자산 합계 {th['자산'][0]:,} 의 10%          {th['자산'][1]:>10,.1f}")

    rows = quantitative_test(th)
    print("\n[4] 부문별 판정 — 하나라도 넘으면 별도 보고")
    print(f"    {'부문':<12}{'수익':>8}{'손익':>8}{'자산':>8}   판정")
    for name, hit_rev, hit_pl, hit_asset, passed in rows:
        mark = lambda b: "넘음" if b else "  -"
        print(f"    {name:<12}{mark(hit_rev):>8}{mark(hit_pl):>8}{mark(hit_asset):>8}"
              f"   {'보고부문' if passed else '미달'}")

    reportable = [r[0] for r in rows if r[4]]
    print(f"    1차 보고부문 {len(reportable)}개: {', '.join(reportable)}")
    print("    헬스케어는 수익도 자산도 기준에 못 미치지만 손실 크기 때문에 걸렸다.")

    total, covered, ratio = seventy_five_percent(reportable)
    print("\n[5] 외부수익 75% 검증 (문단 15)")
    print(f"    기업전체 외부수익                     {total:>10,}")
    print(f"    1차 보고부문의 외부수익               {covered:>10,}")
    print(f"    비율                                 {ratio * 100:>9.1f}%   "
          f"{'충족' if ratio >= 0.75 else '미달 — 부문을 더 식별한다'}")

    added = []
    if ratio < 0.75:
        # 기준에 못 미친 부문 가운데 외부수익이 큰 것부터 넣어 75% 를 채운다
        rest = sorted((s for s in SEGMENTS if s[0] not in reportable),
                      key=lambda s: s[1], reverse=True)
        for seg in rest:
            reportable.append(seg[0])
            added.append(seg[0])
            total, covered, ratio = seventy_five_percent(reportable)
            print(f"    + {seg[0]} 추가 → {covered:,} / {total:,} = {ratio * 100:.1f}%")
            if ratio >= 0.75:
                break

    others = [s for s in SEGMENTS if s[0] not in reportable]
    print(f"\n[6] 최종 보고부문 {len(reportable)}개 — {', '.join(reportable)}")
    print(f"    추가로 식별한 부문: {', '.join(added) if added else '없음'}")
    print(f"    '그 밖의 모든 부문' (문단 16): {', '.join(s[0] for s in others)}")
    print(f"      외부수익 {sum(s[1] for s in others):,} · 부문손익 {sum(s[3] for s in others):,}"
          f" · 부문자산 {sum(s[4] for s in others):,}")

    rep_segs = [s for s in SEGMENTS if s[0] in reportable]
    rep_revenue = sum(revenue(s) for s in rep_segs)
    other_revenue = sum(revenue(s) for s in others)
    internal = sum(s[2] for s in SEGMENTS)
    rep_pl = sum(s[3] for s in rep_segs)
    other_pl = sum(s[3] for s in others)
    print("\n[7] 조정 — 부문 합계에서 기업전체 금액으로 (문단 28)")
    print(f"    보고부문 수익 합계                    {rep_revenue:>10,}")
    print(f"    그 밖의 모든 부문                     {other_revenue:>10,}")
    print(f"    내부거래 제거                         {-internal:>10,}")
    print(f"    기업전체 수익                         {rep_revenue + other_revenue - internal:>10,}")
    print(f"    보고부문 손익 합계                    {rep_pl:>10,}")
    print(f"    그 밖의 모든 부문                     {other_pl:>10,}")
    print(f"    배분하지 않은 본사 공통비              {UNALLOCATED_HQ_COST:>10,}")
    print(f"    법인세비용차감전순이익                 {rep_pl + other_pl + UNALLOCATED_HQ_COST:>10,}")

    print("\n[8] 부문별 영업이익률 — 합계 하나로는 안 보이던 것")
    print(f"    {'부문':<12}{'부문수익':>10}{'부문손익':>10}{'이익률':>9}")
    for seg in SEGMENTS:
        print(f"    {seg[0]:<12}{revenue(seg):>10,}{seg[3]:>10,}"
              f"{seg[3] / revenue(seg) * 100:>8.1f}%")
    print(f"    기업전체 이익률 {entity_margin:.1f}% 한 줄 안에"
          f" 두 자릿수 이익률 둘과 두 자릿수 적자 셋이 함께 들어 있다.")


if __name__ == "__main__":
    main()
