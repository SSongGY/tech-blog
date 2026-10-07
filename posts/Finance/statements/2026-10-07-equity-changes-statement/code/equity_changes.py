"""자본변동표 — 자본은 무엇으로 늘고 무엇으로 줄었는가.

기초 자본이 1,000으로 똑같은 가상 회사 둘이 한 해를 보낸다. 가나전자는 순이익을 내고
배당을 주고, 다라물산은 순손실을 내고 유상증자를 받는다. 기말 자본총계는 둘 다
1,100으로 같지만 구성요소가 다르다. 자본변동표는 그 차이를 구성요소별 기초→기말
조정내역으로 보여 준다(K-IFRS 제1001호 문단 106).

이어서 가나전자가 자기주식을 샀다가 되파는 경우를 붙인다. 자기주식 거래의 손익은
당기손익으로 잡지 않고 자본에서 직접 움직인다(K-IFRS 제1032호 문단 33).

단순화: 기타포괄손익은 없고, 미실현이익(상법 제462조 제1항 제4호)도 없다. 금액 단위는 억원.
"""
import platform
import sys

# 자본 구성요소. 자기주식은 자본의 차감 항목이라 음수로 든다.
COLUMNS = ["자본금", "주식발행초과금", "이익준비금", "미처분이익잉여금", "자기주식"]

OPENING = {"자본금": 300, "주식발행초과금": 200, "이익준비금": 100, "미처분이익잉여금": 400, "자기주식": 0}

# 한 해 동안 일어난 거래. 각 거래는 구성요소 몇 개를 얼마씩 움직인다.
# 이익준비금 적립은 이익잉여금 안에서 자리만 옮기므로 합계가 변하지 않는다(상법 제458조).
EVENTS = {
    "가나전자": [
        ("당기순이익", {"미처분이익잉여금": +150}),
        ("배당 지급", {"미처분이익잉여금": -50}),
        ("이익준비금 적립(배당의 1/10)", {"이익준비금": +5, "미처분이익잉여금": -5}),
    ],
    "다라물산": [
        ("당기순손실", {"미처분이익잉여금": -100}),
        ("유상증자(액면 50, 발행가 200)", {"자본금": +50, "주식발행초과금": +150}),
    ],
}

TREASURY_EVENTS = [
    ("자기주식 취득(30)", {"자기주식": -30}),
    ("자기주식 처분(40에 매각)", {"자기주식": +30, "주식발행초과금": +10}),
]


def total(row: dict) -> int:
    return sum(row[c] for c in COLUMNS)


def apply(row: dict, delta: dict) -> dict:
    out = dict(row)
    for col, amount in delta.items():
        out[col] += amount
    return out


def print_statement(name: str, opening: dict, events: list) -> dict:
    """자본변동표 모양으로 찍는다. 행은 거래, 열은 구성요소, 맨 오른쪽이 합계."""
    width = 11
    head = "".join(f"{c:>{width}}" for c in COLUMNS)
    print(f"  {name}")
    print(f"  {'':<28}{head}{'합계':>{width}}")
    row = opening
    cells = "".join(f"{row[c]:>{width},}" for c in COLUMNS)
    print(f"  {'기초':<28}{cells}{total(row):>{width},}")
    for label, delta in events:
        before = total(row)
        row = apply(row, delta)
        cells = "".join(f"{delta.get(c, 0):>+{width},}" if c in delta else f"{'':>{width}}" for c in COLUMNS)
        print(f"  {label:<28}{cells}{total(row) - before:>+{width},}")
    cells = "".join(f"{row[c]:>{width},}" for c in COLUMNS)
    print(f"  {'기말':<28}{cells}{total(row):>{width},}")
    print()
    return row


def dividend_limit(row: dict) -> tuple[int, dict]:
    """상법 제462조 제1항 — 순자산에서 자본금, 적립된 준비금을 뺀 값이 배당 한도다.

    3호(그 결산기에 적립할 이익준비금)는 배당액이 정해져야 계산되고
    4호(미실현이익)는 예제에 없으므로 둘 다 0으로 둔다.
    """
    net_assets = total(row)
    parts = {
        "순자산액": net_assets,
        "1호 자본금": row["자본금"],
        "2호 자본준비금+이익준비금": row["주식발행초과금"] + row["이익준비금"],
        "3호 적립할 이익준비금": 0,
        "4호 미실현이익": 0,
    }
    limit = net_assets - sum(v for k, v in parts.items() if k != "순자산액")
    return limit, parts


def print_composition(closings: dict) -> None:
    print("[2] 기말 자본 1,100 의 구성 — 주주가 넣은 돈과 회사가 번 돈")
    print(f"  {'회사':<8}{'납입자본':>10}{'이익잉여금':>10}{'자기주식':>10}{'합계':>8}   {'납입자본 비중':>8}")
    for name, row in closings.items():
        paid_in = row["자본금"] + row["주식발행초과금"]
        retained = row["이익준비금"] + row["미처분이익잉여금"]
        print(f"  {name:<8}{paid_in:>10,}{retained:>12,}{row['자기주식']:>10,}{total(row):>10,}   {paid_in / total(row):>8.1%}")
    print()
    print("[3] 배당 한도 (상법 제462조 제1항)")
    for name, row in closings.items():
        limit, parts = dividend_limit(row)
        expr = " − ".join(f"{v:,}" for v in parts.values())
        print(f"  {name:<8} {expr} = {limit:,}")
    print()


def main() -> None:
    print(f"Python {platform.python_version()} · {sys.platform}")
    print()
    print("[1] 한 해의 자본변동표 — 거래가 구성요소 중 어디를 움직이는가 (억원)")
    closings = {name: print_statement(name, OPENING, events) for name, events in EVENTS.items()}
    assert total(closings["가나전자"]) == total(closings["다라물산"]) == 1100
    print_composition(closings)

    print("[4] 가나전자가 자기주식을 샀다가 되팔면 (K-IFRS 제1032호 문단 33)")
    after = print_statement("가나전자 — 이듬해", closings["가나전자"], TREASURY_EVENTS)
    gain_in_pl = 0   # 40 − 30 = 10 의 차익은 당기손익이 아니라 자본(주식발행초과금)으로 간다
    print(f"  취득 30 → 자본총계 {total(closings['가나전자']) - 30:,}  (자본에서 차감)")
    print(f"  처분 40 → 자본총계 {total(after):,}  차익 10 은 자본으로 직접, 당기손익 반영 {gain_in_pl}")
    print()


if __name__ == "__main__":
    main()
