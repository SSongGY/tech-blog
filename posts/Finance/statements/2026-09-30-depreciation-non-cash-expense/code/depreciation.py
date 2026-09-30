"""같은 설비를 정액법과 정률법으로 감가상각하면 이익과 현금이 어떻게 갈리는지 계산한다.

거너정밀과 더러정밀은 0년차 말에 똑같은 설비를 1,000에 사고, 5년 동안 해마다 똑같이
감가상각 전 영업이익 400을 번다(전부 현금으로 받는다고 둔다). 다른 것은 감가상각방법뿐이다.
거너정밀은 정액법, 더러정밀은 정률법(체감잔액법의 한 방식)을 쓴다. 잔존가치는 100이다.

감가상각은 K-IFRS 제1016호 문단 6·50·62를, 현금흐름표에서 되돌리는 처리는
제1007호 문단 20을 따른다. 법인세는 두지 않는다. 금액 단위는 억원이다.
"""

import platform
import sys

COST = 1000
RESIDUAL = 100
LIFE = 5
EBITDA = 400              # 감가상각 전 영업이익. 해마다 같은 현금으로 들어온다고 둔다
SALE_YEAR, SALE_PRICE = 2, 500   # [5]에서 2년차 말에 설비를 파는 경우

# 정률: 매년 기초 장부금액에 같은 비율을 곱해 LIFE년 뒤 정확히 잔존가치가 남게 하는 비율
DB_RATE = 1 - (RESIDUAL / COST) ** (1 / LIFE)


def straight_line() -> list[float]:
    return [(COST - RESIDUAL) / LIFE] * LIFE


def declining_balance() -> list[float]:
    book, out = COST, []
    for _ in range(LIFE):
        dep = book * DB_RATE
        out.append(dep)
        book -= dep
    return out


def book_values(deps: list[float]) -> list[float]:
    book, out = COST, []
    for d in deps:
        book -= d
        out.append(book)
    return out


def main() -> None:
    print(f"Python {sys.version.split()[0]} / {platform.system()}")
    print(f"단위: 억원 / 회사: 거너정밀·더러정밀(가상) / 설비 원가 {COST:,}, 잔존가치 {RESIDUAL}, "
          f"내용연수 {LIFE}년, 감가상각 전 영업이익 해마다 {EBITDA}(가정, 법인세 없음)")

    methods = {"거너정밀(정액법)": straight_line(), "더러정밀(정률법)": declining_balance()}

    print("\n[1] 감가상각비 계산식")
    print(f"  정액법  (원가 − 잔존가치) ÷ 내용연수 = ({COST:,} − {RESIDUAL}) ÷ {LIFE} = {(COST - RESIDUAL) / LIFE:.1f}")
    print(f"  정률법  기초 장부금액 × 상각률, 상각률 = 1 − (잔존가치 ÷ 원가)^(1/내용연수)"
          f" = 1 − ({RESIDUAL}/{COST:,})^(1/{LIFE}) = {DB_RATE:.4f}")

    for name, deps in methods.items():
        books = book_values(deps)
        print(f"\n[2] {name} — 연도별")
        print("  연도  감가상각비  기말 장부금액  영업이익  영업CF(간접법)")
        for y, (d, b) in enumerate(zip(deps, books), start=1):
            profit = EBITDA - d
            ocf = profit + d          # 간접법: 이익에 현금이 안 나간 감가상각비를 되돌린다
            print(f"  {y:>2}년 {d:>11.1f} {b:>14.1f} {profit:>9.1f} {ocf:>14.1f}")
        print(f"  합계 {sum(deps):>11.1f} {'':>14} {sum(EBITDA - d for d in deps):>9.1f} {EBITDA * LIFE:>14.1f}")

    print("\n[3] 5년 동안 들어오고 나간 현금 — 두 회사가 같은가")
    for name in methods:
        print(f"  {name}  투자CF(0년차 설비 취득) {-COST:,}  영업CF 합계 {EBITDA * LIFE:,}"
              f"  잔존가치 회수 {RESIDUAL}  → 순현금 {EBITDA * LIFE - COST + RESIDUAL:,}")

    print("\n[4] 1년차 이익 차이")
    sl, db = (methods[k][0] for k in methods)
    print(f"  영업이익  정액 {EBITDA - sl:.1f}  정률 {EBITDA - db:.1f}  차이 {db - sl:.1f}"
          f"  (정률 쪽 이익이 정액의 {(EBITDA - db) / (EBITDA - sl):.0%})")

    print(f"\n[5] {SALE_YEAR}년차 말에 설비를 {SALE_PRICE}에 판다면")
    for name, deps in methods.items():
        book = book_values(deps)[SALE_YEAR - 1]
        gain = SALE_PRICE - book
        dep_sum = sum(deps[:SALE_YEAR])
        print(f"  {name}  장부금액 {book:.1f}  처분손익 {gain:+.1f}  "
              f"2년 감가상각비 {dep_sum:.1f} − 처분손익 = 설비가 이익에서 뺀 총액 {dep_sum - gain:.1f}")
    print(f"  두 회사 모두 원가 {COST:,} − 매각대금 {SALE_PRICE} = {COST - SALE_PRICE}")


if __name__ == "__main__":
    main()
