"""수익의 구분 공시 — 기업회계기준서 제1115호 문단 113~115, B87~B89.

가상 회사 가나소프트와 다라시스템은 보고부문별 매출이 똑같다.
부문 숫자만 보면 구별되지 않는 두 회사가, 범주별로 구분한 수익에서는
현금흐름의 시기와 불확실성이 다르게 드러나는 것을 계산한다. 금액 단위 억원.
"""

# 한 줄이 (보고부문, 재화·용역 유형, 지역, 이행 시기, 계약 유형, 금액) 이다.
# 이행 시기는 B89⑹, 계약 유형은 B89⑷ 의 범주 예시를 따른다.
GANA = [
    ("소프트웨어", "영구 라이선스", "국내", "한 시점", "고정가격", 60),
    ("소프트웨어", "구독(SaaS)", "국내", "기간", "고정가격", 300),
    ("소프트웨어", "구독(SaaS)", "해외", "기간", "고정가격", 240),
    ("서비스", "유지보수", "국내", "기간", "고정가격", 250),
    ("서비스", "구축 용역", "국내", "기간", "투입시간 정산", 150),
]
DARA = [
    ("소프트웨어", "영구 라이선스", "국내", "한 시점", "고정가격", 420),
    ("소프트웨어", "영구 라이선스", "해외", "한 시점", "고정가격", 120),
    ("소프트웨어", "구독(SaaS)", "국내", "기간", "고정가격", 60),
    ("서비스", "유지보수", "국내", "기간", "고정가격", 100),
    ("서비스", "구축 용역", "국내", "기간", "투입시간 정산", 300),
]
COMPANIES = {"가나소프트": GANA, "다라시스템": DARA}

# 문단 113⑴: 고객과의 계약 수익은 다른 수익원천과 별도로 공시한다.
# 손익계산서 매출 한 줄에 리스 수익(제1116호)이 섞여 있다고 가정한다.
LEASE_INCOME = {"가나소프트": 40, "다라시스템": 40}

FIELDS = {"부문": 0, "유형": 1, "지역": 2, "이행 시기": 3, "계약 유형": 4}


def group_sum(rows, field):
    idx = FIELDS[field]
    out = {}
    for row in rows:
        out[row[idx]] = out.get(row[idx], 0) + row[5]
    return out


def total(rows):
    return sum(row[5] for row in rows)


def print_share(title, by_company):
    print(title)
    keys = []
    for groups in by_company.values():
        for k in groups:
            if k not in keys:
                keys.append(k)
    head = "  범주".ljust(16) + "".join(f"{name:>16}" for name in by_company)
    print(head)
    for k in keys:
        cells = []
        for name, groups in by_company.items():
            amt = groups.get(k, 0)
            share = amt / total(COMPANIES[name]) * 100
            cells.append(f"{amt:>7} ({share:5.1f}%)")
        print(f"  {k:<14}" + "".join(f"{c:>16}" for c in cells))
    print()


def main():
    print("[1] 입력 자료 — 고객과의 계약 수익 (억원)")
    for name, rows in COMPANIES.items():
        print(f"  {name}")
        print("    부문        유형           지역  이행 시기  계약 유형        금액")
        for r in rows:
            print(f"    {r[0]:<10}{r[1]:<14}{r[2]:<5}{r[3]:<8}{r[4]:<12}{r[5]:>6}")
    print()

    print("[2] 손익계산서 매출과 문단 113⑴ 구분")
    for name, rows in COMPANIES.items():
        contract = total(rows)
        lease = LEASE_INCOME[name]
        print(f"  {name}  매출 {contract + lease:>5} = 고객과의 계약 수익 {contract:>5} + 리스 수익 {lease:>3}")
    print()

    print_share("[3] 보고부문별 수익 (제1108호 부문 공시만 보면)",
                {n: group_sum(r, "부문") for n, r in COMPANIES.items()})
    print_share("[4] 이행 시기별 구분 — B89⑹",
                {n: group_sum(r, "이행 시기") for n, r in COMPANIES.items()})
    print_share("[5] 계약 유형별 구분 — B89⑷",
                {n: group_sum(r, "계약 유형") for n, r in COMPANIES.items()})
    print_share("[6] 지역별 구분 — B89⑵",
                {n: group_sum(r, "지역") for n, r in COMPANIES.items()})

    # 문단 115: 구분 공시와 부문 수익의 관계를 이해할 수 있게 한다.
    # 부문 × 이행 시기 표의 행 합이 부문 수익, 열 합이 구분 공시 금액과 같아야 한다.
    print("[7] 부문 × 이행 시기 대사표 — 문단 115")
    for name, rows in COMPANIES.items():
        print(f"  {name}")
        print("    부문          한 시점    기간    부문 합계")
        col = {"한 시점": 0, "기간": 0}
        for seg, seg_total in group_sum(rows, "부문").items():
            seg_rows = [r for r in rows if r[0] == seg]
            timing = group_sum(seg_rows, "이행 시기")
            pt, ot = timing.get("한 시점", 0), timing.get("기간", 0)
            col["한 시점"] += pt
            col["기간"] += ot
            assert pt + ot == seg_total
            print(f"    {seg:<10}{pt:>9}{ot:>8}{seg_total:>11}")
        grand = col["한 시점"] + col["기간"]
        assert grand == total(rows)
        print(f"    {'합계':<10}{col['한 시점']:>9}{col['기간']:>8}{grand:>11}")
    print()

    # 기간에 걸쳐 이행하는 고정가격 수익은 계약이 이어지는 한 다음 해에도 반복되는 몫이다.
    # 이 비중이 현금흐름의 '시기·불확실성'을 가르는 지표로 쓰인다(문단 114).
    print("[8] 범주를 겹쳐 본 비중 — 기간 이행이면서 고정가격인 수익")
    for name, rows in COMPANIES.items():
        recurring = sum(r[5] for r in rows if r[3] == "기간" and r[4] == "고정가격")
        print(f"  {name}  {recurring:>5} / {total(rows):>5} = {recurring / total(rows) * 100:5.1f}%")


if __name__ == "__main__":
    main()
