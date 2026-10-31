"""정성 분석과 정량 분석이 같은 위험 목록을 어떻게 다르게 줄 세우는지 계산한다.

아래 숫자는 설명을 위해 만든 **가상의 입력값**이다. 어떤 조직의 실측치도 아니다.
보이려는 것은 숫자 자체가 아니라, 같은 위험 다섯 건을 두 방식으로 평가했을 때
순위가 어긋난다는 사실과 그 어긋남이 어디서 오는지다.

정성: 발생 가능성 1~5 등급 × 영향 1~5 등급 = 1~25 점
정량: 연간 기대 손실 = 연간 발생 횟수 × 1회 손실액
"""

from dataclasses import dataclass

LEVEL_NAMES = {1: "매우 낮음", 2: "낮음", 3: "보통", 4: "높음", 5: "매우 높음"}


@dataclass(frozen=True)
class Risk:
    name: str
    likelihood_level: int      # 정성 — 발생 가능성 등급 1~5
    impact_level: int          # 정성 — 영향 등급 1~5
    annual_rate: float         # 정량 — 연간 발생 횟수 (0.5 = 2년에 한 번)
    loss_per_event: int        # 정량 — 1회 손실액 (만원)

    @property
    def qualitative_score(self) -> int:
        return self.likelihood_level * self.impact_level

    @property
    def annual_expected_loss(self) -> float:
        return self.annual_rate * self.loss_per_event


RISKS = [
    Risk("핵심 DB 디스크 장애", 2, 5, 0.20, 30_000),
    Risk("배포 스크립트 오작동", 4, 3, 6.00, 400),
    Risk("외부 결제 API 지연", 5, 2, 24.00, 150),
    Risk("개인정보 유출", 1, 5, 0.05, 200_000),
    Risk("사내 위키 서버 다운", 3, 1, 3.00, 60),
]

# 통제안 — 역시 가상의 입력값이다. 연간 비용과, 그 통제가 낮추는 발생 횟수.
CONTROLS = [
    ("배포 전 스테이징 강제", "배포 스크립트 오작동", 6.00, 1.00, 1_200),
    ("DB 이중화", "핵심 DB 디스크 장애", 0.20, 0.02, 4_000),
    ("위키 서버 이중화", "사내 위키 서버 다운", 3.00, 0.30, 900),
]


def rule(title: str) -> None:
    print("\n" + "=" * 68)
    print(title)
    print("=" * 68)


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [max(len(h), *(len(r[i]) for r in rows)) for i, h in enumerate(headers)]
    print("  " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)))
    print("  " + "-+-".join("-" * w for w in widths))
    for row in rows:
        print("  " + " | ".join(row[i].ljust(widths[i]) for i in range(len(headers))))


def show_qualitative() -> list[Risk]:
    rule("1. 정성 분석 — 등급을 곱해 점수를 낸다")
    ranked = sorted(RISKS, key=lambda r: r.qualitative_score, reverse=True)
    rows = [
        [
            str(i + 1),
            r.name,
            f"{r.likelihood_level}({LEVEL_NAMES[r.likelihood_level]})",
            f"{r.impact_level}({LEVEL_NAMES[r.impact_level]})",
            str(r.qualitative_score),
        ]
        for i, r in enumerate(ranked)
    ]
    print_table(["순위", "위험", "가능성", "영향", "점수"], rows)
    return ranked


def show_quantitative() -> list[Risk]:
    rule("2. 정량 분석 — 연간 기대 손실로 환산한다")
    ranked = sorted(RISKS, key=lambda r: r.annual_expected_loss, reverse=True)
    rows = [
        [
            str(i + 1),
            r.name,
            f"{r.annual_rate:g}회/년",
            f"{r.loss_per_event:,}만원",
            f"{r.annual_expected_loss:,.0f}만원",
        ]
        for i, r in enumerate(ranked)
    ]
    print_table(["순위", "위험", "연간 횟수", "1회 손실", "연간 기대 손실"], rows)
    return ranked


def compare(by_score: list[Risk], by_loss: list[Risk]) -> None:
    rule("3. 두 순위가 어긋나는 자리")
    rows = []
    for r in RISKS:
        q = by_score.index(r) + 1
        n = by_loss.index(r) + 1
        rows.append([r.name, str(q), str(n), f"{n - q:+d}"])
    print_table(["위험", "정성 순위", "정량 순위", "차이"], rows)

    ties: dict[int, list[str]] = {}
    for r in RISKS:
        ties.setdefault(r.qualitative_score, []).append(r.name)
    same = {score: names for score, names in ties.items() if len(names) > 1}
    print(f"\n  정성 점수가 같아 순위를 가를 수 없는 묶음: {same if same else '없음'}")
    print(f"  정성 점수가 가질 수 있는 값의 가짓수: "
          f"{len({l * i for l in range(1, 6) for i in range(1, 6)})}가지 (1~25 중)")


def show_controls() -> None:
    rule("4. 통제의 비용 대비 효과 — 정량이라야 나오는 숫자")
    index = {r.name: r for r in RISKS}
    rows = []
    for label, target, before_rate, after_rate, annual_cost in CONTROLS:
        risk = index[target]
        before = before_rate * risk.loss_per_event
        after = after_rate * risk.loss_per_event
        benefit = before - after
        rows.append([
            label,
            f"{before:,.0f}만원",
            f"{after:,.0f}만원",
            f"{benefit:,.0f}만원",
            f"{annual_cost:,}만원",
            f"{benefit - annual_cost:+,.0f}만원",
        ])
    print_table(
        ["통제안", "통제 전", "통제 후", "줄어든 손실", "연간 비용", "순효과"],
        rows,
    )
    print("\n  순효과가 음수면 통제가 막는 손실보다 통제 비용이 크다는 뜻이다.")


def main() -> None:
    by_score = show_qualitative()
    by_loss = show_quantitative()
    compare(by_score, by_loss)
    show_controls()


if __name__ == "__main__":
    main()
