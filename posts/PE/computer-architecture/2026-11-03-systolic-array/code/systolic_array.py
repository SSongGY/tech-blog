"""가중치 고정(weight stationary) 시스톨릭 어레이를 사이클 단위로 돌려 본다.

행렬 곱 C = A x B 를 K x N 짜리 PE 배열에 올리고, 한 사이클씩 진행하며
 - 결과가 직접 계산한 행렬 곱과 같은지
 - 전체 사이클 수가 M + K + N - 2 로 떨어지는지
 - 메모리에서 읽은 원소 수가 삼중 루프 대비 몇 분의 1인지
를 센다. Python 3.13.5 에서 돌렸다. 외부 의존성은 없다.
"""

Matrix = list[list[int]]


def naive_matmul(a: Matrix, b: Matrix) -> tuple[Matrix, int]:
    """삼중 루프. 곱셈 한 번마다 두 원소를 새로 읽는다고 보고 읽기 횟수를 센다."""
    rows, inner, cols = len(a), len(b), len(b[0])
    reads = 0
    out = [[0] * cols for _ in range(rows)]
    for i in range(rows):
        for j in range(cols):
            acc = 0
            for k in range(inner):
                acc += a[i][k] * b[k][j]
                reads += 2
            out[i][j] = acc
    return out, reads


class SystolicArray:
    """PE(r, c) 가 가중치 B[r][c] 를 쥐고 움직이지 않는다.

    활성값은 왼쪽에서 들어와 오른쪽으로, 부분합은 위에서 들어와 아래로 흐른다.
    PE(r, c) 는 매 사이클 psum_out = psum_in + act_in * weight 를 계산한다.
    """

    def __init__(self, weights: Matrix) -> None:
        self.weights = weights
        self.rows = len(weights)
        self.cols = len(weights[0])
        # 셀 사이를 잇는 선. None 은 그 사이클에 아무것도 안 흐른다는 뜻이다.
        self.act_wire = [[None] * (self.cols + 1) for _ in range(self.rows)]
        self.psum_wire = [[None] * self.cols for _ in range(self.rows + 1)]
        self.mac_count = 0
        self.busy_log: list[list[bool]] = []

    def step(self, act_inputs: list[int | None], psum_inputs: list[int | None]):
        """한 사이클. 모든 PE 가 동시에 계산하므로 선의 값을 먼저 전부 떠 둔다."""
        for r in range(self.rows):
            self.act_wire[r][0] = act_inputs[r]
        for c in range(self.cols):
            self.psum_wire[0][c] = psum_inputs[c]

        act_snapshot = [row[:] for row in self.act_wire]
        psum_snapshot = [row[:] for row in self.psum_wire]
        busy = [[False] * self.cols for _ in range(self.rows)]

        for r in range(self.rows):
            for c in range(self.cols):
                act = act_snapshot[r][c]
                psum = psum_snapshot[r][c]
                if act is None or psum is None:
                    # 한쪽만 도착한 셀은 쉰다. 활용률이 떨어지는 지점이다.
                    self.act_wire[r][c + 1] = act
                    self.psum_wire[r + 1][c] = psum
                    continue
                self.act_wire[r][c + 1] = act
                self.psum_wire[r + 1][c] = psum + act * self.weights[r][c]
                self.mac_count += 1
                busy[r][c] = True

        self.busy_log.append([any(row) for row in busy])
        return [self.psum_wire[self.rows][c] for c in range(self.cols)], busy


def run(a: Matrix, b: Matrix, *, trace: bool = False):
    """A 를 비스듬히 밀어 넣고, 열 아래로 떨어지는 부분합을 결과로 모은다."""
    m, k, n = len(a), len(b), len(b[0])
    array = SystolicArray(b)
    out = [[None] * n for _ in range(m)]
    total_cycles = 0
    first_out_cycle = None
    # 넉넉히 돌린 뒤 결과가 다 찼으면 멈춘다.
    for cycle in range(m + k + n + 4):
        acts: list[int | None] = []
        for r in range(k):
            i = cycle - r
            acts.append(a[i][r] if 0 <= i < m else None)
        psums: list[int | None] = []
        for c in range(n):
            i = cycle - c
            psums.append(0 if 0 <= i < m else None)

        exits, busy = array.step(acts, psums)
        total_cycles = cycle + 1

        for c in range(n):
            i = cycle - c - k + 1
            if exits[c] is not None and 0 <= i < m:
                out[i][c] = exits[c]
                if first_out_cycle is None:
                    first_out_cycle = cycle + 1

        if trace:
            marks = "".join(
                "".join("■" if busy[r][c] else "·" for c in range(n)) + " "
                for r in range(k)
            )
            print(f"  사이클 {cycle + 1:>2}  {marks}")

        if all(all(v is not None for v in row) for row in out):
            break

    return out, total_cycles, array.mac_count, first_out_cycle


def section(title: str) -> None:
    print()
    print("=" * 62)
    print(title)
    print("=" * 62)


def main() -> None:
    import platform
    import sys

    print("=" * 62)
    print("환경")
    print("=" * 62)
    print(f"  Python  {sys.version.split()[0]}")
    print(f"  OS      {platform.system()} {platform.release()}")

    a = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]]
    b = [[1, 0, 2], [0, 1, 3], [4, 2, 1]]

    section("1. 입력 — A(4x3) 와 B(3x3)")
    print("  A (왼쪽에서 흘러 들어간다)      B (PE 에 고정된다)")
    for row_a, row_b in zip(a, b + [None]):
        left = " ".join(f"{v:>3}" for v in row_a)
        right = " ".join(f"{v:>3}" for v in row_b) if row_b else ""
        print(f"    {left}                  {right}")

    section("2. 사이클마다 일하는 PE — 대각선 파면이 지나간다")
    print("  (3x3 배열을 행마다 끊어 찍는다. ■ 는 그 사이클에 곱셈한 PE)")
    out, cycles, macs, first_out = run(a, b, trace=True)

    section("3. 결과 검산")
    expected, naive_reads = naive_matmul(a, b)
    print("  시스톨릭 결과 :", out)
    print("  직접 계산     :", expected)
    print("  일치 여부     :", out == expected)

    section("4. 사이클 수")
    m, k, n = len(a), len(b), len(b[0])
    print(f"  M={m}, K={k}, N={n}")
    print(f"  실측 사이클          {cycles}")
    print(f"  M + K + N - 2        {m + k + n - 2}")
    print(f"  유효 MAC 수          {macs}  (= M x K x N = {m * k * n})")
    print(f"  PE 수                {k * n}")
    print(f"  PE 활용률            {macs / (k * n * cycles) * 100:.1f}%")

    section("5. 메모리에서 읽은 원소 수")
    systolic_reads = m * k + k * n
    print(f"  삼중 루프            {naive_reads}회  (곱셈마다 A, B 를 한 번씩)")
    print(f"  시스톨릭             {systolic_reads}회"
          f"  (A {m * k}개 + 가중치 선적재 {k * n}개)")
    print(f"  비율                 {naive_reads / systolic_reads:.1f}배")
    print("  한 번 읽은 A 원소가 배열을 가로지르며 N 번 쓰인다.")

    section("6. 배열이 클수록 활용률이 오른다 — 같은 8x8 배열, 행 수만 바꾼다")
    k_big, n_big = 8, 8
    weights = [[(r + c) % 5 for c in range(n_big)] for r in range(k_big)]
    print("   M행   사이클   유효MAC    PE활용률   읽기 절감")
    for m_big in (1, 8, 64, 512):
        act = [[(i + j) % 7 for j in range(k_big)] for i in range(m_big)]
        got, cyc, mac, _ = run(act, weights)
        assert got == naive_matmul(act, weights)[0]
        util = mac / (k_big * n_big * cyc) * 100
        ratio = (2 * m_big * k_big * n_big) / (m_big * k_big + k_big * n_big)
        print(f"  {m_big:>5} {cyc:>8} {mac:>9} {util:>10.1f}% {ratio:>10.1f}배")

    section("7. 지연 — 첫 결과가 나오기까지 몇 사이클인가")
    print(f"  3x3 배열, 4행 입력: 첫 결과가 나온 사이클 {first_out}")
    print("   배열 K   첫 결과 사이클   전체 사이클")
    for k_try in (2, 4, 8, 16):
        w = [[1] * k_try for _ in range(k_try)]
        act = [[1] * k_try for _ in range(4)]
        _, cyc, _, first = run(act, w)
        print(f"  {k_try:>8} {first:>14} {cyc:>13}")
    print("  첫 결과는 배열 깊이 K 만큼 기다려야 나온다. 배열을 키우면 처리량은")
    print("  오르지만 한 건의 응답 시간은 길어진다.")


if __name__ == "__main__":
    main()
