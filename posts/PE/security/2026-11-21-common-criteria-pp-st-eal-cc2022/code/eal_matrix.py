"""CC:2022 Part 5 의 EAL 요약표(Table 1)를 옮겨 등급 사이의 차이를 계산한다.

1) Table 1(요약 행렬)과 Table 2~8(등급별 컴포넌트 목록)이 서로 맞는지 대조한다
2) 각 EAL 이 '한 패밀리에 컴포넌트 하나'이고 등급이 오를 때 내려가는 패밀리가 없는지 본다
3) EAL n → n+1 에서 새로 들어온 패밀리와 한 단계 올라간 컴포넌트를 뽑는다
4) ST 평가 패키지(STA-DR·STA-STD, Table 18·19)를 EAL1·EAL2 의 ASE 부분과 비교한다
"""

# Part 5 Table 1 — Evaluation assurance level summary. 0 은 그 EAL 에 없다는 뜻.
EAL_SUMMARY = {
    "ADV_ARC": (0, 1, 1, 1, 1, 1, 1),
    "ADV_FSP": (1, 2, 3, 4, 5, 5, 6),
    "ADV_IMP": (0, 0, 0, 1, 1, 2, 2),
    "ADV_INT": (0, 0, 0, 0, 2, 3, 3),
    "ADV_SPM": (0, 0, 0, 0, 0, 1, 1),
    "ADV_TDS": (0, 1, 2, 3, 4, 5, 6),
    "AGD_OPE": (1, 1, 1, 1, 1, 1, 1),
    "AGD_PRE": (1, 1, 1, 1, 1, 1, 1),
    "ALC_CMC": (1, 2, 3, 4, 4, 5, 5),
    "ALC_CMS": (1, 2, 3, 4, 5, 5, 5),
    "ALC_DEL": (0, 1, 1, 1, 1, 1, 1),
    "ALC_DVS": (0, 0, 1, 1, 1, 2, 2),
    "ALC_LCD": (0, 0, 1, 1, 1, 1, 2),
    "ALC_TAT": (0, 0, 0, 1, 2, 3, 3),
    "ASE_CCL": (1, 1, 1, 1, 1, 1, 1),
    "ASE_ECD": (1, 1, 1, 1, 1, 1, 1),
    "ASE_INT": (1, 1, 1, 1, 1, 1, 1),
    "ASE_OBJ": (1, 2, 2, 2, 2, 2, 2),
    "ASE_REQ": (1, 2, 2, 2, 2, 2, 2),
    "ASE_SPD": (0, 1, 1, 1, 1, 1, 1),
    "ASE_TSS": (1, 1, 1, 1, 1, 1, 1),
    "ATE_COV": (0, 1, 2, 2, 2, 3, 3),
    "ATE_DPT": (0, 0, 1, 1, 3, 3, 4),
    "ATE_FUN": (0, 1, 1, 1, 1, 2, 2),
    "ATE_IND": (1, 2, 2, 2, 2, 2, 3),
    "AVA_VAN": (1, 2, 2, 3, 4, 5, 5),
}

ASE_STANDARD = "ASE_CCL.1 ASE_ECD.1 ASE_INT.1 ASE_OBJ.2 ASE_REQ.2 ASE_SPD.1 ASE_TSS.1"

# Part 5 Table 2~8 — 등급별 표를 옮긴 것. Table 1 과 따로 옮겨 서로 검산한다.
EAL_TABLES = {
    1: "ADV_FSP.1 AGD_OPE.1 AGD_PRE.1 ALC_CMC.1 ALC_CMS.1 ASE_CCL.1 ASE_ECD.1 "
       "ASE_INT.1 ASE_OBJ.1 ASE_REQ.1 ASE_TSS.1 ATE_IND.1 AVA_VAN.1",
    2: "ADV_ARC.1 ADV_FSP.2 ADV_TDS.1 AGD_OPE.1 AGD_PRE.1 ALC_CMC.2 ALC_CMS.2 "
       "ALC_DEL.1 " + ASE_STANDARD + " ATE_COV.1 ATE_FUN.1 ATE_IND.2 AVA_VAN.2",
    3: "ADV_ARC.1 ADV_FSP.3 ADV_TDS.2 AGD_OPE.1 AGD_PRE.1 ALC_CMC.3 ALC_CMS.3 "
       "ALC_DEL.1 ALC_DVS.1 ALC_LCD.1 " + ASE_STANDARD
       + " ATE_COV.2 ATE_DPT.1 ATE_FUN.1 ATE_IND.2 AVA_VAN.2",
    4: "ADV_ARC.1 ADV_FSP.4 ADV_IMP.1 ADV_TDS.3 AGD_OPE.1 AGD_PRE.1 ALC_CMC.4 "
       "ALC_CMS.4 ALC_DEL.1 ALC_DVS.1 ALC_LCD.1 ALC_TAT.1 " + ASE_STANDARD
       + " ATE_COV.2 ATE_DPT.1 ATE_FUN.1 ATE_IND.2 AVA_VAN.3",
    5: "ADV_ARC.1 ADV_FSP.5 ADV_IMP.1 ADV_INT.2 ADV_TDS.4 AGD_OPE.1 AGD_PRE.1 "
       "ALC_CMC.4 ALC_CMS.5 ALC_DEL.1 ALC_DVS.1 ALC_LCD.1 ALC_TAT.2 " + ASE_STANDARD
       + " ATE_COV.2 ATE_DPT.3 ATE_FUN.1 ATE_IND.2 AVA_VAN.4",
    6: "ADV_ARC.1 ADV_FSP.5 ADV_IMP.2 ADV_INT.3 ADV_SPM.1 ADV_TDS.5 AGD_OPE.1 "
       "AGD_PRE.1 ALC_CMC.5 ALC_CMS.5 ALC_DEL.1 ALC_DVS.2 ALC_LCD.1 ALC_TAT.3 "
       + ASE_STANDARD + " ATE_COV.3 ATE_DPT.3 ATE_FUN.2 ATE_IND.2 AVA_VAN.5",
    7: "ADV_ARC.1 ADV_FSP.6 ADV_IMP.2 ADV_INT.3 ADV_SPM.1 ADV_TDS.6 AGD_OPE.1 "
       "AGD_PRE.1 ALC_CMC.5 ALC_CMS.5 ALC_DEL.1 ALC_DVS.2 ALC_LCD.2 ALC_TAT.3 "
       + ASE_STANDARD + " ATE_COV.3 ATE_DPT.4 ATE_FUN.2 ATE_IND.3 AVA_VAN.5",
}

# Part 5 Table 18·19 — ST 평가용 보증 패키지
STA_DR = "ASE_INT.1 ASE_CCL.1 ASE_SPD.1 ASE_OBJ.1 ASE_ECD.1 ASE_REQ.1 ASE_TSS.1"
STA_STD = "ASE_INT.1 ASE_CCL.1 ASE_SPD.1 ASE_OBJ.2 ASE_ECD.1 ASE_REQ.2 ASE_TSS.1"


def components_from_summary(level):
    return {
        f"{family}.{levels[level - 1]}"
        for family, levels in EAL_SUMMARY.items()
        if levels[level - 1]
    }


def parse(text):
    return set(text.split())


def family_levels(components):
    levels = {}
    for component in components:
        family, level = component.split(".")
        if family in levels:
            raise ValueError(f"한 패밀리에 컴포넌트가 둘: {family}")
        levels[family] = int(level)
    return levels


def main():
    print("[1] Table 1(요약)과 Table 2~8(등급별)의 대조")
    for level in range(1, 8):
        from_summary = components_from_summary(level)
        from_table = parse(EAL_TABLES[level])
        status = "일치" if from_summary == from_table else (
            f"불일치 요약에만 {sorted(from_summary - from_table)} "
            f"표에만 {sorted(from_table - from_summary)}"
        )
        print(f"  EAL{level}: 컴포넌트 {len(from_table):2d}개 · {status}")

    print("\n[2] 한 패밀리에 하나 · 등급이 오를 때 내려가는 패밀리")
    families = len(EAL_SUMMARY)
    classes = sorted({family[:3] for family in EAL_SUMMARY})
    print(f"  Table 1 의 패밀리 {families}개 · 클래스 {len(classes)}개 {classes}")
    previous = {}
    for level in range(1, 8):
        current = family_levels(parse(EAL_TABLES[level]))
        dropped = [f for f, v in previous.items() if current.get(f, 0) < v]
        print(f"  EAL{level}: 패밀리 {len(current):2d}개 · 앞 등급보다 내려간 패밀리 {dropped or '없음'}")
        previous = current

    print("\n[3] 한 등급 오를 때 바뀌는 것")
    for level in range(2, 8):
        lower = family_levels(parse(EAL_TABLES[level - 1]))
        upper = family_levels(parse(EAL_TABLES[level]))
        added = sorted(f"{f}.{v}" for f, v in upper.items() if f not in lower)
        raised = sorted(
            f"{f}.{lower[f]}→{v}" for f, v in upper.items() if f in lower and v > lower[f]
        )
        print(f"  EAL{level - 1}→EAL{level}: 새 패밀리 {len(added)} {added}")
        print(f"  {'':12} 올라간 컴포넌트 {len(raised)} {raised}")

    print("\n[4] 클래스별 컴포넌트 수")
    print("  클래스 " + " ".join(f"EAL{level}" for level in range(1, 8)))
    for cls in classes:
        counts = [
            sum(1 for c in parse(EAL_TABLES[level]) if c.startswith(cls))
            for level in range(1, 8)
        ]
        print(f"  {cls}    " + " ".join(f"{n:4d}" for n in counts))

    print("\n[5] ST 평가 패키지와 EAL 의 ASE 부분")
    eal1_ase = {c for c in parse(EAL_TABLES[1]) if c.startswith("ASE")}
    eal2_ase = {c for c in parse(EAL_TABLES[2]) if c.startswith("ASE")}
    print(f"  STA-STD == EAL2 의 ASE        : {parse(STA_STD) == eal2_ase}")
    print(f"  STA-DR  - EAL1 의 ASE         : {sorted(parse(STA_DR) - eal1_ase)}")
    print(f"  EAL1 의 ASE - STA-DR          : {sorted(eal1_ase - parse(STA_DR))}")
    print(f"  STA-STD - STA-DR (올라간 것)   : {sorted(parse(STA_STD) - parse(STA_DR))}")


if __name__ == "__main__":
    main()
