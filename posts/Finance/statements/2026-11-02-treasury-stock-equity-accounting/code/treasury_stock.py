"""자기주식 — 취득·처분·소각이 자본의 어느 줄에 닿는가.

손익계산서를 한 번도 거치지 않는데 EPS 와 ROE 는 움직인다. 그 경로를 숫자로 따라간다.

1. 가나전자의 기초 자본 구성
2. 거래 네 건이 자본의 어느 줄을 얼마나 움직이는가
3. 거래마다 다시 그린 자본 항목 표
4. 손익계산서는 그대로인데 EPS·ROE 만 바뀐다
5. 처분손실 상계 순서 — 자본잉여금이 먼저, 모자라면 자본조정
"""
import platform
import sys

EOK = 100_000_000  # 1억원
PAR = 500          # 액면금액

# 가나전자 2026년 기초 (단위: 원)
OPENING = {
    "자본금": 50 * EOK,                    # 액면 500원 × 10,000,000주
    "주식발행초과금": 200 * EOK,
    "자기주식처분이익": 0,
    "이익준비금": 25 * EOK,
    "이익잉여금": 725 * EOK,
    "자기주식": 0,                          # 음수로 쌓인다 — 자본에서 차감
    "자기주식처분손실": 0,                   # 음수로 쌓인다
}
SHARES_ISSUED = 10_000_000   # 발행주식수
NET_INCOME = 150 * EOK       # 연간 순이익 — 자기주식 거래와 무관하다고 둔다
FEE_RATE = 0.003             # 취득 수수료율 — 자본거래 거래원가

ORDER = ["자본금", "주식발행초과금", "자기주식처분이익", "이익준비금",
         "이익잉여금", "자기주식", "자기주식처분손실"]


def won(amount: float) -> str:
    return f"{amount / EOK:,.3f}"


def print_environment() -> None:
    print(f"Python {platform.python_version()} ({sys.platform})")
    print("가정: 순이익 150억원은 자기주식 거래와 무관하게 고정. 매입에 쓴 현금이 벌던 "
          "이자수익은 무시한다. 취득 수수료 0.3%는 취득원가에 더해 자본에서 차감한다.")
    print("단위: 억원 (주식 수는 주)")
    print()


class Company:
    """자본 항목만 가진 가상 회사. 손익계산서는 건드리지 않는다."""

    def __init__(self) -> None:
        self.equity = dict(OPENING)
        self.issued = SHARES_ISSUED
        self.treasury_shares = 0
        self.log: list[tuple[str, dict]] = []

    @property
    def total(self) -> int:
        return sum(self.equity.values())

    @property
    def outstanding(self) -> int:
        return self.issued - self.treasury_shares

    @property
    def book_per_treasury(self) -> float:
        if self.treasury_shares == 0:
            return 0.0
        return -self.equity["자기주식"] / self.treasury_shares

    def acquire(self, shares: int, price: int) -> dict:
        payment = shares * price
        fee = round(payment * FEE_RATE)
        self.equity["자기주식"] -= payment + fee
        self.treasury_shares += shares
        return {"현금": -(payment + fee), "자기주식": -(payment + fee),
                "  이 중 거래원가": -fee}

    def dispose(self, shares: int, price: int) -> dict:
        proceeds = shares * price
        carrying = round(self.book_per_treasury * shares)
        self.equity["자기주식"] += carrying
        self.treasury_shares -= shares
        diff = proceeds - carrying
        moved = {"현금": proceeds, "자기주식": carrying}
        if diff >= 0:
            # 일반기업회계기준 15.9 — 처분이익은 자본잉여금
            self.equity["자기주식처분이익"] += diff
            moved["자기주식처분이익"] = diff
        else:
            # 같은 문단 — 손실은 처분이익과 먼저 상계하고, 남으면 자본조정
            offset = min(self.equity["자기주식처분이익"], -diff)
            self.equity["자기주식처분이익"] -= offset
            rest = -diff - offset
            self.equity["자기주식처분손실"] -= rest
            moved["자기주식처분이익"] = -offset
            moved["자기주식처분손실"] = -rest
        return moved

    def retire(self, shares: int) -> dict:
        carrying = round(self.book_per_treasury * shares)
        self.equity["자기주식"] += carrying
        # 상법 제343조 제1항 단서의 소각 — 자본금 감소 규정을 따르지 않으므로 자본금은 그대로.
        # 일반기업회계기준 15.12 — 소각하는 주식의 취득원가만큼 이익잉여금을 줄인다.
        self.equity["이익잉여금"] -= carrying
        self.treasury_shares -= shares
        self.issued -= shares
        return {"자기주식": carrying, "이익잉여금": -carrying, "자본금": 0}

    def snapshot(self, label: str) -> None:
        self.log.append((label, dict(self.equity) | {
            "_자본총계": self.total, "_발행": self.issued,
            "_자기주식수": self.treasury_shares, "_유통": self.outstanding}))


def print_opening(firm: Company) -> None:
    print("[1] 가나전자 2026년 기초 자본 — 발행주식 10,000,000주, 액면 500원")
    for name in ORDER:
        if firm.equity[name] == 0 and name in ("자기주식", "자기주식처분손실", "자기주식처분이익"):
            continue
        print(f"  {name:14}{won(firm.equity[name]):>12}")
    print(f"  {'자본총계':14}{won(firm.total):>12}")
    print(f"  주당 장부가치(BPS) {firm.total / firm.outstanding:,.0f}원")
    print()


def print_moves(moves: list[tuple[str, dict]]) -> None:
    print("[2] 거래 네 건이 자본의 어느 줄을 움직이는가 (+ 는 자본을 늘림)")
    for label, moved in moves:
        print(f"  {label}")
        for name, amount in moved.items():
            if amount == 0:
                continue
            if name == "현금":
                mark = "현금 유출입"
            elif name.strip() == "이 중 거래원가":
                mark = "위 자기주식에 포함"
            else:
                mark = "자본"
            print(f"      {name:16}{won(amount):>12}   ({mark})")
        print("      손익계산서                   0.000   (어느 줄도 거치지 않는다)")
    print()


def print_table(firm: Company) -> None:
    print("[3] 거래마다 다시 그린 자본 항목 (단위 억원)")
    header = f"  {'':18}" + "".join(f"{label:>12}" for label, _ in firm.log)
    print(header)
    for name in ORDER:
        row = "".join(f"{won(state[name]):>12}" for _, state in firm.log)
        print(f"  {name:18}{row}")
    print(f"  {'─' * (18 + 12 * len(firm.log))}")
    print(f"  {'자본총계':18}" + "".join(f"{won(s['_자본총계']):>12}" for _, s in firm.log))
    print(f"  {'발행주식수':18}" + "".join(f"{s['_발행']:>12,}" for _, s in firm.log))
    print(f"  {'자기주식 수':18}" + "".join(f"{s['_자기주식수']:>12,}" for _, s in firm.log))
    print(f"  {'유통주식수':18}" + "".join(f"{s['_유통']:>12,}" for _, s in firm.log))
    print()


def print_metrics(firm: Company) -> None:
    print("[4] 순이익 150.000 억원은 네 번 모두 같다 — 움직인 것은 분모뿐이다")
    print(f"  {'':18}{'순이익':>12}{'자본총계':>12}{'유통주식수':>14}{'EPS(원)':>12}{'ROE':>10}{'BPS(원)':>12}")
    for label, state in firm.log:
        eps = NET_INCOME / state["_유통"]
        roe = NET_INCOME / state["_자본총계"]
        bps = state["_자본총계"] / state["_유통"]
        print(f"  {label:18}{won(NET_INCOME):>12}{won(state['_자본총계']):>12}"
              f"{state['_유통']:>14,}{eps:>12,.0f}{roe:>9.2%}{bps:>12,.0f}")
    print("  EPS 는 기말 유통주식수로 나눈 값이다. 실제 공시는 가중평균유통주식수를 쓴다.")
    print()


def print_offset_order() -> None:
    print("[5] 처분손실 상계 순서 — 같은 손실 15.135 억원이 자본잉여금 잔액에 따라 갈린다")
    print(f"  {'앞서 쌓인 자기주식처분이익':28}{'상계된 금액':>14}{'자본조정으로 남는 손실':>22}")
    for prior in (0, 5 * EOK, 11.82 * EOK, 20 * EOK):
        loss = 15.135 * EOK
        offset = min(prior, loss)
        print(f"  {won(prior):>26}  {won(offset):>14}{won(loss - offset):>22}")
    print("  자본조정으로 남은 손실은 이익잉여금 처분으로 상각하거나, 나중에 생기는")
    print("  자기주식처분이익과 먼저 상계한다 (일반기업회계기준 15.9).")
    print()


def main() -> None:
    print_environment()
    firm = Company()
    print_opening(firm)
    firm.snapshot("기초")

    moves = []
    moves.append(("① 취득 1,000,000주 @ 15,000원 (수수료 0.3%)", firm.acquire(1_000_000, 15_000)))
    firm.snapshot("① 취득")
    moves.append(("② 처분 400,000주 @ 18,000원 — 장부가보다 비싸게", firm.dispose(400_000, 18_000)))
    firm.snapshot("② 처분(이익)")
    moves.append(("③ 처분 300,000주 @ 10,000원 — 장부가보다 싸게", firm.dispose(300_000, 10_000)))
    firm.snapshot("③ 처분(손실)")
    moves.append(("④ 남은 300,000주 소각 (상법 제343조 제1항 단서)", firm.retire(300_000)))
    firm.snapshot("④ 소각")

    print(f"  취득 후 자기주식 주당 장부금액 {15_000 * (1 + FEE_RATE):,.0f}원 "
          f"(= 15,000원 + 수수료 0.3%)\n")
    print_moves(moves)
    print_table(firm)
    print_metrics(firm)
    print_offset_order()


if __name__ == "__main__":
    main()
