"""심슨의 역설을 두 자료로 확인한다.

1. Simpson(1951) Table 2·3·4 — 부분표에서 보이던 연관이 합친 표에서 사라진다.
2. Bickel·Hammel·O'Connell(1975) 버클리 대학원 지원 자료 — 전체와 학과별 방향이 갈린다.
3. Simpson(1951) §11의 합산 가능 조건이 왜 깨졌는지 수치로 확인한다.

둘 다 발표된 표의 숫자를 그대로 넣고, 계산만 여기서 한다.
"""

import sys
import unicodedata


def width(text):
    """한글·한자는 터미널에서 두 칸을 차지하므로 표시 폭으로 센다."""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def ljust(text, n):
    return text + " " * max(0, n - width(text))


def rjust(text, n):
    return " " * max(0, n - width(text)) + text


def rule(title):
    print()
    print("=" * 76)
    print(title)
    print("=" * 76)


def odds_ratio(a, b, c, d):
    """2x2 표 [[a, b], [c, d]] 의 교차비 (a·d)/(b·c)."""
    return (a * d) / (b * c)


# ---------------------------------------------------------------------------
# 1. Simpson(1951) 의 카드 예와 처치 예
# ---------------------------------------------------------------------------

# Table 2: (더러움/깨끗함) x (빨강/검정) x (그림패/숫자패), 52장 중 장수
CARDS = {
    "더러운 카드": {"빨강": (4, 8), "검정": (3, 5)},   # (그림패, 숫자패)
    "깨끗한 카드": {"빨강": (2, 12), "검정": (3, 15)},
}

# Table 4: Table 2 와 숫자가 같고 이름만 바뀐 표
#   (남/여) x (미처치/처치) x (생존/사망)
TREATMENT = {
    "남성": {"미처치": (4, 3), "처치": (8, 5)},        # (생존, 사망)
    "여성": {"미처치": (2, 3), "처치": (12, 15)},
}


def simpson_cards():
    rule("1-A. Simpson(1951) Table 2 — 카드 한 벌 (단위: 52장 중 장수)")
    print(ljust("층", 14) + ljust("색", 8) + rjust("그림패", 8)
          + rjust("숫자패", 8) + rjust("그림패 비율", 14))
    print("-" * 76)
    totals = {"빨강": [0, 0], "검정": [0, 0]}
    for layer, rows in CARDS.items():
        for colour, (court, plain) in rows.items():
            share = court / (court + plain)
            print(ljust(layer, 14) + ljust(colour, 8) + rjust(str(court), 8)
                  + rjust(str(plain), 8) + rjust(f"{share:.1%}", 14))
            totals[colour][0] += court
            totals[colour][1] += plain
        a, b = rows["빨강"]
        c, d = rows["검정"]
        print(" " * 14 + f"→ 교차비(빨강 그림패 / 검정 그림패) = {odds_ratio(a, b, c, d):.4f}")
        print("-" * 76)

    rule("1-B. Simpson(1951) Table 3 — 두 층을 합친 표")
    print(ljust("색", 8) + rjust("그림패", 8) + rjust("숫자패", 8) + rjust("그림패 비율", 14))
    print("-" * 76)
    for colour, (court, plain) in totals.items():
        print(ljust(colour, 8) + rjust(str(court), 8) + rjust(str(plain), 8)
              + rjust(f"{court / (court + plain):.1%}", 14))
    a, b = totals["빨강"]
    c, d = totals["검정"]
    print(f"\n합친 표의 교차비 = {odds_ratio(a, b, c, d):.4f}")
    print("두 부분표의 교차비가 서로 같으므로 Bartlett 기준의 2차 상호작용은 없다.")
    print("그런데 그 공통값 0.8333 이 합치면 1.0000 이 된다 — 연관이 사라졌다.")


def simpson_treatment():
    rule("1-C. Simpson(1951) Table 4 — 이름만 바꾼 같은 숫자")
    print(ljust("층", 8) + ljust("구분", 10) + rjust("생존", 7)
          + rjust("사망", 7) + rjust("생존율", 11))
    print("-" * 76)
    merged = {"미처치": [0, 0], "처치": [0, 0]}
    for layer, rows in TREATMENT.items():
        for arm, (alive, dead) in rows.items():
            print(ljust(layer, 8) + ljust(arm, 10) + rjust(str(alive), 7)
                  + rjust(str(dead), 7) + rjust(f"{alive / (alive + dead):.1%}", 11))
            merged[arm][0] += alive
            merged[arm][1] += dead
        ta, td = rows["처치"]
        ua, ud = rows["미처치"]
        print(" " * 18 + f"→ 처치의 생존 교차비 = {odds_ratio(ta, td, ua, ud):.4f}")
        print("-" * 76)

    for arm, (alive, dead) in merged.items():
        print(ljust("전체", 8) + ljust(arm, 10) + rjust(str(alive), 7)
              + rjust(str(dead), 7) + rjust(f"{alive / (alive + dead):.1%}", 11))
    ta, td = merged["처치"]
    ua, ud = merged["미처치"]
    print(" " * 18 + f"→ 처치의 생존 교차비 = {odds_ratio(ta, td, ua, ud):.4f}")
    print("\n남성에서도 여성에서도 처치가 생존에 유리한데(두 층 모두 교차비 1.2),")
    print("합치면 처치군과 미처치군의 생존율이 똑같이 50.0% 다.")
    print("숫자가 1-A 와 완전히 같은데, 이번에는 합친 표 쪽을 믿으면 안 된다.")


# ---------------------------------------------------------------------------
# 2. 버클리 대학원 지원 자료 (1973년 상위 6개 학과)
# ---------------------------------------------------------------------------

# 학과: (남성 지원, 남성 합격, 여성 지원, 여성 합격)
BERKELEY = {
    "A": (825, 512, 108, 89),
    "B": (560, 353, 25, 17),
    "C": (325, 120, 593, 202),
    "D": (417, 138, 375, 131),
    "E": (191, 53, 393, 94),
    "F": (373, 22, 341, 24),
}


def berkeley_tables():
    rule("2-A. 버클리 1973년 상위 6개 학과 — 학과별 합격률")
    print(ljust("학과", 6) + rjust("남 지원", 9) + rjust("남 합격", 9)
          + rjust("남 합격률", 12) + rjust("여 지원", 9) + rjust("여 합격", 9)
          + rjust("여 합격률", 12) + rjust("차이(여-남)", 14))
    print("-" * 76)
    m_app = m_adm = w_app = w_adm = 0
    higher_for_women = 0
    for dept, (ma, mad, wa, wad) in BERKELEY.items():
        mr, wr = mad / ma, wad / wa
        gap = wr - mr
        if gap > 0:
            higher_for_women += 1
        print(ljust(dept, 6) + rjust(str(ma), 9) + rjust(str(mad), 9)
              + rjust(f"{mr:.1%}", 12) + rjust(str(wa), 9) + rjust(str(wad), 9)
              + rjust(f"{wr:.1%}", 12) + rjust(f"{gap * 100:+.1f}p", 14))
        m_app += ma
        m_adm += mad
        w_app += wa
        w_adm += wad
    mr_all, wr_all = m_adm / m_app, w_adm / w_app
    print("-" * 76)
    print(ljust("전체", 6) + rjust(str(m_app), 9) + rjust(str(m_adm), 9)
          + rjust(f"{mr_all:.1%}", 12) + rjust(str(w_app), 9) + rjust(str(w_adm), 9)
          + rjust(f"{wr_all:.1%}", 12) + rjust(f"{(wr_all - mr_all) * 100:+.1f}p", 14))
    print(f"\n여성 합격률이 더 높은 학과: 6개 중 {higher_for_women}개")
    print(f"그런데 전체로는 남성이 {(mr_all - wr_all) * 100:.1f} 포인트 높다.")
    return m_app, m_adm, w_app, w_adm


def berkeley_standardize(m_app, m_adm, w_app, w_adm):
    rule("2-B. 학과 구성비를 맞추면(직접 표준화) 격차가 어떻게 되나")
    print(ljust("학과", 6) + rjust("남 지원 비중", 14) + rjust("여 지원 비중", 14)
          + rjust("남 합격률", 12) + rjust("여 합격률", 12))
    print("-" * 76)
    expected_men = 0.0
    expected_women = 0.0
    for dept, (ma, mad, wa, wad) in BERKELEY.items():
        mr, wr = mad / ma, wad / wa
        expected_men += wa * mr      # 여성 구성비 × 남성 합격률
        expected_women += ma * wr    # 남성 구성비 × 여성 합격률
        print(ljust(dept, 6) + rjust(f"{ma / m_app:.1%}", 14)
              + rjust(f"{wa / w_app:.1%}", 14) + rjust(f"{mr:.1%}", 12)
              + rjust(f"{wr:.1%}", 12))
    print("-" * 76)

    mr_all, wr_all = m_adm / m_app, w_adm / w_app
    std_m, std_w = expected_men / w_app, expected_women / m_app
    print(ljust("관측된 그대로", 28) + f"남 {mr_all:.1%} vs 여 {wr_all:.1%}"
          + f"   → 여성이 {(wr_all - mr_all) * 100:+.1f} 포인트")
    print(ljust("여성의 학과 구성비로 맞추면", 28) + f"남 {std_m:.1%} vs 여 {wr_all:.1%}"
          + f"   → 여성이 {(wr_all - std_m) * 100:+.1f} 포인트")
    print(ljust("남성의 학과 구성비로 맞추면", 28) + f"남 {mr_all:.1%} vs 여 {std_w:.1%}"
          + f"   → 여성이 {(std_w - mr_all) * 100:+.1f} 포인트")
    print("\n구성비를 어느 쪽으로 맞추든 부호가 뒤집힌다.")
    print("격차를 만든 것은 학과별 합격 판정이 아니라 어느 학과에 지원했는가다.")


# ---------------------------------------------------------------------------
# 3. Simpson(1951) §11 의 합산 가능 조건
# ---------------------------------------------------------------------------

def collapsibility_check():
    rule("3. 합산 가능 조건 — 숨기는 변수가 둘 중 하나와 독립이어야 한다")
    print("Simpson(1951) §11: 2차 상호작용이 없을 때, 합친 표의 연관도가 부분표와")
    print("같으려면 숨기는 분류 C 가 A 와 독립이거나 B 와 독립이어야 한다.")
    print("카드 예에서 C='더러움', A='색', B='패 종류' 로 두고 확인한다.\n")

    total = 52
    dirty = sum(sum(v) for v in CARDS["더러운 카드"].values())
    red = sum(CARDS[layer]["빨강"][i] for layer in CARDS for i in (0, 1))
    court = sum(CARDS[layer][c][0] for layer in CARDS for c in ("빨강", "검정"))
    dirty_red = sum(CARDS["더러운 카드"]["빨강"])
    dirty_court = sum(CARDS["더러운 카드"][c][0] for c in ("빨강", "검정"))

    for name, joint, marginal in (
        ("더러움 × 빨강", dirty_red, red),
        ("더러움 × 그림패", dirty_court, court),
    ):
        expected = dirty * marginal / total
        verdict = "독립" if abs(joint - expected) < 1e-9 else "독립 아님"
        print(ljust(name, 18) + rjust(f"실제 {joint:.1f}/52", 16)
              + rjust(f"독립이라면 {expected:.1f}/52", 22) + f"   → {verdict}")

    print("\n둘 다 독립이 아니므로 조건이 깨진다 — 합치면 연관도가 보존되지 않는다.")
    print("1-A 의 0.8333 이 1-B 에서 1.0000 으로 바뀐 것이 바로 그 결과다.")


def main():
    print(f"Python {sys.version.split()[0]}")
    simpson_cards()
    simpson_treatment()
    m_app, m_adm, w_app, w_adm = berkeley_tables()
    berkeley_standardize(m_app, m_adm, w_app, w_adm)
    collapsibility_check()


if __name__ == "__main__":
    main()
