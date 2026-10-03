"""IEEE 802.11 DCF·EDCA의 IFS, 백오프 창, 충돌 확률을 규격 값과 Bianchi 모델로 계산한다.

근거
- RFC 8325 §6.1 (5 GHz: 슬롯 9 us, SIFS 16 us, DIFS = SIFS + 2*슬롯, CWmin 15 / CWmax 1023)
- RFC 8325 §6.2.3·§6.2.4 (AC별 AIFSN, CWmin, CWmax)
- Inan·Keceli·Ayanoglu 2007 §II (AIFS = SIFS + AIFSN * 슬롯, 가상 충돌 규칙)
- Bianchi 2000 §II·§IV (백오프 동결, 식 (7)·(9))
"""

import platform
import random

SLOT_US = 9
SIFS_US = 16

# AC: (AIFSN, CWmin, CWmax) — RFC 8325 Figure 3·4, 5 GHz
EDCA = {
    "AC_VO": (2, 3, 7),
    "AC_VI": (2, 7, 15),
    "AC_BE": (3, 15, 1023),
    "AC_BK": (7, 15, 1023),
}


def print_section(title):
    print()
    print(f"[{title}]")


def interframe_spaces():
    difs = SIFS_US + 2 * SLOT_US
    print(f"  SIFS {SIFS_US} us, 슬롯 {SLOT_US} us → DIFS = SIFS + 2x슬롯 = {difs} us")
    for ac, (aifsn, cw_min, _) in EDCA.items():
        aifs = SIFS_US + aifsn * SLOT_US
        # 백오프를 고르기 전까지 기다리는 최소 시간과, CWmin에서 고를 수 있는 최대 대기
        print(f"  {ac}  AIFSN {aifsn}  AIFS {aifs:>3} us"
              f"  + 백오프 0~{cw_min:>2} 슬롯 → 첫 시도 대기 {aifs}~{aifs + cw_min * SLOT_US} us")


def contention_windows():
    for ac, (_, cw_min, cw_max) in EDCA.items():
        windows = []
        cw = cw_min
        while True:
            windows.append(cw)
            if cw == cw_max:
                break
            cw = min(2 * (cw + 1) - 1, cw_max)
        print(f"  {ac}  재전송마다 CW {' → '.join(str(w) for w in windows)}  (단계 {len(windows) - 1}개)")


def freeze_example():
    # Bianchi Fig.1의 장면: B가 백오프 8을 고른 뒤, 3 슬롯이 지났을 때 A가 송신한다
    counter = 8
    log = []
    for slot in range(1, 4):
        counter -= 1
        log.append(f"슬롯{slot}:{counter}")
    log.append(f"A 송신 감지 → 동결 {counter}")
    log.append(f"A 끝 + DIFS 동안 빔 → 재개 {counter}")
    while counter > 0:
        counter -= 1
        log.append(f"{counter}")
    log.append("0에서 B 송신")
    print("  B 백오프 8:  " + " · ".join(log))
    print("  새로 고르지 않고 남은 5부터 이어서 줄인다 → 오래 기다린 단말이 다음 경쟁에서 앞선다")


def bianchi_tau(p, window, stages):
    # 식 (7): tau = 2(1-2p) / ((1-2p)(W+1) + pW(1-(2p)^m))
    return 2 * (1 - 2 * p) / ((1 - 2 * p) * (window + 1) + p * window * (1 - (2 * p) ** stages))


def solve_bianchi(n, window, stages):
    # 식 (9): p = 1 - (1-tau)^(n-1). 이분법으로 두 식의 교점을 찾는다
    low, high = 0.0, 1.0
    for _ in range(200):
        p = (low + high) / 2
        if p == 0.5:
            p += 1e-12  # 식 (7)은 p=1/2에서 0/0 꼴이라 피한다
        tau = bianchi_tau(p, window, stages)
        if 1 - (1 - tau) ** (n - 1) > p:
            low = p
        else:
            high = p
    return p, tau


def simulate(n, cw_min, cw_max, slots, seed):
    # 포화 상태 슬롯 시뮬레이션: 모두 늘 보낼 패킷이 있고 채널 오류는 없다
    rng = random.Random(seed)
    cws = [cw_min] * n
    counters = [rng.randint(0, cw_min) for _ in range(n)]
    attempts = collisions = 0
    for _ in range(slots):
        ready = [i for i in range(n) if counters[i] == 0]
        if not ready:
            counters = [c - 1 for c in counters]
            continue
        attempts += len(ready)
        if len(ready) > 1:
            collisions += len(ready)
            for i in ready:
                cws[i] = min(2 * (cws[i] + 1) - 1, cw_max)
        else:
            cws[ready[0]] = cw_min
        for i in ready:
            counters[i] = rng.randint(0, cws[i])
    return collisions / attempts


def stages_of(cw_min, cw_max):
    stages = 0
    while (cw_min + 1) * 2 ** stages < cw_max + 1:
        stages += 1
    return stages


def collision_table():
    print("  W = CWmin+1, m = 백오프 단계 수. p = 보낸 프레임이 충돌할 확률")
    print("  단말수 |      AC_BE (W=16, m=6)        |      AC_VO (W=4, m=1)")
    print("         |  p(모델)  p(시뮬)  tau(모델)    |  p(모델)  p(시뮬)  tau(모델)")
    for n in (2, 5, 10, 20, 50):
        cells = []
        for ac in ("AC_BE", "AC_VO"):
            _, cw_min, cw_max = EDCA[ac]
            p, tau = solve_bianchi(n, cw_min + 1, stages_of(cw_min, cw_max))
            p_sim = simulate(n, cw_min, cw_max, slots=200_000, seed=n)
            cells.append(f"  {p:6.3f}   {p_sim:6.3f}   {tau:7.4f}   ")
        print(f"  {n:>5}  |" + "|".join(cells))


def main():
    print(f"Python {platform.python_version()}")
    print_section("IFS — 5 GHz 값 (RFC 8325 §6.1, §6.2.3)")
    interframe_spaces()
    print_section("이진 지수 백오프 — 경쟁 창 (RFC 8325 §6.1.3, §6.2.4)")
    contention_windows()
    print_section("백오프 동결과 재개 (Bianchi 2000 Fig.1)")
    freeze_example()
    print_section("포화 상태 충돌 확률 — Bianchi 식 (7)·(9) vs 슬롯 시뮬레이션")
    collision_table()


if __name__ == "__main__":
    main()
