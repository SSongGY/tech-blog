"""합의 알고리즘 비교에 쓰는 두 가지 계산을 검산한다.

1. PoW 의 확률적 최종성 — 비트코인 백서 11절의 공식으로, 공격자가 z 블록 뒤에서
   정직한 체인을 따라잡을 확률 P 를 계산해 백서에 실린 표와 대조한다.
2. PBFT 의 정족수 — n = 3f + 1 에서 prepared(2f) · committed-local(2f+1) ·
   클라이언트 응답(f+1) 크기, 그리고 n - 2f > f 가 성립하는지.
"""

import math
import sys

# 백서 11절에 실린 값 (q=0.1, z=0..10)
PAPER_Q10 = [1.0000000, 0.2045873, 0.0509779, 0.0131722, 0.0034552, 0.0009137,
             0.0002428, 0.0000647, 0.0000173, 0.0000046, 0.0000012]
# 백서 11절 "P < 0.001" 표
PAPER_Z_FOR_01PCT = {0.10: 5, 0.15: 8, 0.20: 11, 0.25: 15, 0.30: 24,
                     0.35: 41, 0.40: 89, 0.45: 340}


def attacker_success(q, z):
    """백서 11절: 공격자 진행을 포아송 분포로 두고, 남은 격차를 따라잡을 확률을 더한다."""
    p = 1.0 - q
    lam = z * (q / p)
    total = 1.0
    poisson = math.exp(-lam)
    for k in range(z + 1):
        # lam**k / k! 를 따로 계산하면 z 가 수백일 때 넘친다. 한 항씩 곱해 나간다
        if k > 0:
            poisson *= lam / k
        total -= poisson * (1 - (q / p) ** (z - k))
    return total


def min_blocks_below(q, threshold):
    z = 0
    while attacker_success(q, z) >= threshold:
        z += 1
    return z


def main():
    print(f"Python {sys.version.split()[0]}")
    print()
    print("== 1. PoW — 공격자가 z 블록 뒤에서 따라잡을 확률 (q = 공격자 해시 비율 0.1)")
    print("   z  | 계산값     | 백서 값    | 일치")
    for z, paper in enumerate(PAPER_Q10):
        mine = attacker_success(0.1, z)
        same = "예" if f"{mine:.7f}" == f"{paper:.7f}" else "아니오"
        print(f"   {z:<2} | {mine:.7f}  | {paper:.7f}  | {same}")
    print()

    print("== 2. PoW — P < 0.1% 가 되는 최소 z (확인 블록 수)")
    print("   q    | 계산 z | 백서 z | 일치")
    for q, paper_z in PAPER_Z_FOR_01PCT.items():
        z = min_blocks_below(q, 0.001)
        same = "예" if z == paper_z else "아니오"
        print(f"   {q:.2f} | {z:<6} | {paper_z:<6} | {same}")
    print()

    print("== 3. PoW — z=6 일 때 q 별 P")
    for q in (0.10, 0.20, 0.30, 0.40, 0.45):
        print(f"   q={q:.2f}  P={attacker_success(q, 6):.7f}")
    print()

    print("== 4. PBFT — n = 3f + 1 과 정족수")
    print("   f | n  | prepared 2f | committed-local 2f+1 | 클라이언트 f+1 | n-2f > f")
    for f in range(1, 5):
        n = 3 * f + 1
        print(f"   {f} | {n:<2} | {2 * f:<11} | {2 * f + 1:<20} | {f + 1:<14} | {n - 2 * f > f}")
    print("   n = 3f (복제본 하나 모자랄 때)")
    for f in range(1, 5):
        n = 3 * f
        print(f"   {f} | {n:<2} | n-2f = {n - 2 * f}, f = {f} → n-2f > f 는 {n - 2 * f > f}")
    print()

    print("== 5. PBFT — 요청 하나에 오가는 복제본 간 메시지 수 (정상 경로 3단계)")
    print("   주 복제본이 백업에게 pre-prepare, 백업마다 나머지 전부에게 prepare,")
    print("   복제본마다 나머지 전부에게 commit 을 멀티캐스트한다고 보고 센다")
    print("   n   | pre-prepare | prepare | commit | 합계")
    for n in (4, 7, 10, 13, 31, 100):
        pre = n - 1
        prepare = (n - 1) * (n - 1)
        commit = n * (n - 1)
        print(f"   {n:<3} | {pre:<11} | {prepare:<7} | {commit:<6} | {pre + prepare + commit:,}")


if __name__ == "__main__":
    main()
