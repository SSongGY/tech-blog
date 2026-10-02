"""PER — 같은 주가에서 분모를 무엇으로 두느냐에 따라 값이 갈린다.

주가는 고정하고 분모(이익)만 바꾼다. 확정 연간 이익·최근 4분기 합산·예상 이익,
지배주주 몫과 연결 전체, 기말 주식수와 가중평균 주식수, 일회성 이익의 포함 여부,
그리고 이익이 0 근처나 음수로 갈 때 PER 이 어떻게 되는지를 본다.
EPS 산식은 K-IFRS 제1033호 주당이익(문단 10·19·20)을 따른다.
"""
import platform
import sys

EOK = 100_000_000  # 1억원

PRICE = 30_000  # 가나전자 주가(원). 이 글 내내 고정한다
SHARES_BEGIN = 10_000_000
SHARES_ISSUED = 2_000_000  # 7월 1일 유상증자로 발행 (가정)
ISSUE_MONTHS_OUTSTANDING = 6


def eps(net_income_eok: float, shares: float) -> float:
    return net_income_eok * EOK / shares


def per(price: float, eps_value: float) -> float:
    return price / eps_value


def weighted_shares() -> float:
    # 기초 주식은 12개월, 7월 발행분은 6개월만 유통됐으므로 기간 가중치를 준다(문단 20)
    return SHARES_BEGIN + SHARES_ISSUED * ISSUE_MONTHS_OUTSTANDING / 12


def print_definitions() -> None:
    print("[0] 산식")
    print("  PER = 주가 ÷ 주당순이익(EPS)  =  시가총액 ÷ 순이익 (주식수가 같을 때)")
    print("  기본 EPS = 지배기업 보통주 귀속 당기순이익 ÷ 가중평균유통보통주식수  (K-IFRS 1033 문단 10)")
    print()


def print_shares() -> None:
    print("[1] 가나전자 주식수 (기초 1,000만 주, 7/1 유상증자 200만 주)")
    print(f"  기말 주식수         {SHARES_BEGIN + SHARES_ISSUED:>12,.0f}주")
    print(f"  가중평균 주식수     {weighted_shares():>12,.0f}주  = 1,000만 × 12/12 + 200만 × 6/12")
    print()


def print_denominators() -> list[tuple[str, float]]:
    print(f"[2] 주가 {PRICE:,}원 고정, 분모만 바꾼 PER (순이익 단위: 억원)")
    shares = weighted_shares()
    cases = [
        ("후행 — 직전 사업연도 확정 이익", 330),
        ("후행 — 최근 4분기 합산(TTM)", 264),
        ("선행 — 향후 12개월 예상 이익(가정)", 495),
    ]
    print(f"  {'분모':32}{'순이익':>6}{'EPS(원)':>10}{'PER':>9}")
    for label, ni in cases:
        e = eps(ni, shares)
        print(f"  {label:32}{ni:>6}{e:>10,.0f}{per(PRICE, e):>8.2f}배")
    print("  TTM = 직전 사업연도의 남은 분기 + 올해 공시된 분기. 분기 이익이 줄고 있으면 확정 연간보다 PER 이 높게 나온다")
    print()
    return cases


def print_controlling() -> None:
    print("[3] 연결 순이익 전체를 쓰면 (직전 사업연도)")
    shares = weighted_shares()
    total, controlling = 440, 330
    for label, ni in (("연결 당기순이익 전체", total), ("지배기업 소유주 귀속분", controlling)):
        e = eps(ni, shares)
        print(f"  {label:20}{ni:>5}억  EPS {e:>7,.0f}원  PER {per(PRICE, e):>6.2f}배")
    print(f"  비지배지분 몫 {total - controlling}억은 자회사의 다른 주주 몫이라 가나전자 주주의 EPS 에 들어가지 않는다")
    print()


def print_share_basis() -> None:
    print("[4] 같은 이익 330억, 주식수 기준만 다르면")
    for label, shares in (("가중평균 주식수", weighted_shares()), ("기말 주식수", SHARES_BEGIN + SHARES_ISSUED)):
        e = eps(330, shares)
        print(f"  {label:12}{shares:>12,.0f}주  EPS {e:>7,.0f}원  PER {per(PRICE, e):>6.2f}배")
    print()


def print_one_off() -> None:
    print("[5] 일회성 이익이 섞이면 — 다라물산 (주가 20,000원, 주식 500만 주)")
    price, shares = 20_000, 5_000_000
    recurring, one_off = 50, 50  # 일회성: 공장 부지 처분이익(세후, 가정)
    for label, ni in (("보고 순이익(처분이익 포함)", recurring + one_off), ("처분이익을 뺀 순이익", recurring)):
        e = eps(ni, shares)
        print(f"  {label:22}{ni:>5}억  EPS {e:>7,.0f}원  PER {per(price, e):>6.2f}배")
    print()


def print_near_zero() -> None:
    print(f"[6] 주가 {PRICE:,}원 고정, 이익이 0을 지나 적자로 갈 때 (주식 1,000만 주)")
    print(f"  {'순이익(억)':>10}{'EPS(원)':>10}{'PER':>12}{'이익수익률 E/P':>16}")
    for ni in (300, 150, 30, 3, 0, -30):
        e = eps(ni, SHARES_BEGIN)
        per_text = "계산 불가" if e == 0 else f"{per(PRICE, e):,.1f}배"
        print(f"  {ni:>10}{e:>10,.0f}{per_text:>12}{e / PRICE:>16.2%}")
    print("  PER 은 이익이 0 에 다가가면 끝없이 커지고, 0 을 지나면 부호가 뒤집힌다. E/P 는 같은 방향으로 이어진다")
    print()


def main() -> None:
    print(f"Python {platform.python_version()} / {platform.system()}")
    print("회사: 가나전자·다라물산(모두 가상) / 예상 이익은 설명용 가정값")
    print()
    print_definitions()
    print_shares()
    print_denominators()
    print_controlling()
    print_share_basis()
    print_one_off()
    print_near_zero()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
