"""워킹셋 모델과 스래싱 — 원 논문의 정의와 식을 그대로 계산한다.

Denning(1968a) 의 워킹셋 정의 W(t, tau) 와 크기 성질, Denning(1968b) 의
효율 식 e(m) = 1 / (1 + m*T) 와 프로그램 한 개를 더 밀어 넣었을 때의
붕괴 실험을 표준 라이브러리만으로 재현한다.
"""

import sys

# 지역성이 드러나도록 만든 참조열. 앞쪽은 A·B·C 를, 뒤쪽은 D·E·F 를 맴돈다.
REFERENCE_STRING = "ABCABCABACBDEFDEFDEDFEDA"


def working_set(reference_string, t, tau):
    """시각 t 에서 창 길이 tau 인 워킹셋 W(t, tau) 를 집합으로 돌려준다.

    원 논문은 구간을 (t - tau, t) 로 적는다. 참조를 한 칸에 하나씩 놓는
    이산 모형에서는 직전 tau 개의 참조가 그 구간에 해당한다.
    """
    start = max(0, t - tau)
    return set(reference_string[start:t])


def print_environment():
    print("[환경]")
    print(f"  Python {sys.version.split()[0]}")
    print(f"  참조열 {REFERENCE_STRING} (길이 {len(REFERENCE_STRING)})")
    print()


def print_working_sets():
    print("[1] 창 길이에 따른 워킹셋 — W(t, tau) 와 크기 w(t, tau)")
    print("    t 는 그 시점까지 참조가 끝난 자리다.")
    print()
    print("     t  참조열 앞부분              tau=2        tau=4           tau=8")
    for t in (3, 6, 9, 12, 15, 18, 21, 24):
        cells = []
        for tau in (2, 4, 8):
            ws = working_set(REFERENCE_STRING, t, tau)
            cells.append(f"{{{','.join(sorted(ws))}}}({len(ws)})")
        prefix = REFERENCE_STRING[:t]
        print(f"    {t:2d}  {prefix:<24s}  {cells[0]:<12s} {cells[1]:<15s} {cells[2]}")
    print()


def check_size_properties():
    """P1(크기) 이 참조열 전체에서 성립하는지 확인한다."""
    print("[2] 크기 성질 P1 검사 — 원 논문이 든 세 가지")
    zero_ok = True
    bound_ok = True
    monotone_ok = True
    for t in range(len(REFERENCE_STRING) + 1):
        if len(working_set(REFERENCE_STRING, t, 0)) != 0:
            zero_ok = False
        previous = 0
        for tau in range(0, 13):
            size = len(working_set(REFERENCE_STRING, t, tau))
            if size > tau:
                bound_ok = False
            if size < previous:
                monotone_ok = False
            previous = size
    print(f"    w(t, 0) = 0                : {zero_ok}")
    print(f"    w(t, tau) <= tau           : {bound_ok}")
    print(f"    tau 에 대해 비감소          : {monotone_ok}")
    print()


def efficiency(missing_page_probability, traverse_time):
    """e(m) = 1 / (1 + m*T). 프로세서를 실제로 쓰고 있는 시간의 비율."""
    return 1.0 / (1.0 + missing_page_probability * traverse_time)


def print_efficiency_table():
    print("[3] 효율 e(m) = 1 / (1 + m*T) — T 는 가상시간 단위(vtu)")
    traverse_times = (1, 10, 100, 1000, 10000)
    header = "     m         " + "".join(f"T={t:<10d}" for t in traverse_times)
    print(header)
    for m in (0.0001, 0.001, 0.01, 0.1):
        row = f"    {m:<10.4f}"
        for traverse_time in traverse_times:
            row += f"{efficiency(m, traverse_time):<12.4f}"
        print(row)
    print()


def print_collapse_experiment():
    """Denning(1968b) 의 사고실험: 꽉 찬 메모리에 프로그램 하나를 더 넣는다."""
    print("[4] 프로그램 하나를 더 넣었을 때 — 바쁜 프로세서 수의 변화")
    traverse_time = 10000
    m0 = 0.001
    print(f"    T = {traverse_time} vtu, m0 = {m0}")
    print()
    print("      n   늘어난 결함확률 d   바쁜 프로세서 n개일 때   n+1개일 때   비율")
    for n in (4, 10, 20, 50):
        delta = 1.0 / (n + 1)
        before = n * efficiency(m0, traverse_time)
        after = (n + 1) * efficiency(m0 + delta, traverse_time)
        print(
            f"    {n:3d}   {delta:<17.4f} {before:<24.3f} {after:<12.3f} {after / before:.4f}"
        )
    print()


def print_memory_condition():
    """워킹셋 합이 메모리를 넘는 지점 n0 를 센다."""
    print("[5] 워킹셋 합 조건 — sum w_i <= M 을 지키는 최대 다중도")
    memory_pages = 40
    for working_set_size in (6, 8, 12):
        n0 = memory_pages // working_set_size
        used = n0 * working_set_size
        print(
            f"    M={memory_pages}, 프로그램당 워킹셋 {working_set_size:2d}쪽 "
            f"-> n0={n0}, 쓰는 쪽 {used}, 남는 쪽 {memory_pages - used}"
        )
    print()


def main():
    print_environment()
    print_working_sets()
    check_size_properties()
    print_efficiency_table()
    print_collapse_experiment()
    print_memory_condition()


if __name__ == "__main__":
    main()
