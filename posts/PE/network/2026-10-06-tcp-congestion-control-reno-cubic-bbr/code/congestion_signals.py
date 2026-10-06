"""Reno · CUBIC · BBR 의 창 크기 식을 RFC 와 드래프트에 적힌 그대로 계산한다.

측정이 아니라 식의 계산이다. 실제 망에는 지연 ACK, 재정렬, 다른 흐름이 있어
값이 그대로 나오지 않는다. 여기서 보려는 것은 "무엇이 창을 줄이고 늘리는가"
라는 신호의 차이가 숫자로 어떻게 드러나는가다.

단위는 세그먼트. Reno 는 RFC 5681, CUBIC 은 RFC 9438, BBR 은 draft-ietf-ccwg-bbr-06.
"""

# RFC 9438 — C 는 5.1 절 권고값, beta 는 4.6 절 권고값
CUBIC_C = 0.4
CUBIC_BETA = 0.7
# RFC 9438 4.3 절 — Reno 와 평균 창이 같아지게 하는 증가폭
CUBIC_ALPHA = 3 * (1 - CUBIC_BETA) / (1 + CUBIC_BETA)

SEGMENT_BYTES = 1460


def reno_recovery_seconds(w_max: float, rtt: float) -> float:
    """손실 뒤 W_max/2 에서 RTT 마다 1 세그먼트씩 늘어 W_max 로 돌아오는 시간."""
    rounds = w_max - w_max / 2
    return rounds * rtt


def cubic_k(w_max: float) -> float:
    """RFC 9438 Figure 2. 창이 beta*W_max 에서 시작할 때 W_max 에 닿는 시간(초)."""
    cwnd_epoch = CUBIC_BETA * w_max
    return ((w_max - cwnd_epoch) / CUBIC_C) ** (1 / 3)


def cubic_recovery(w_max: float, rtt: float) -> tuple[float, str]:
    """RTT 단위로 W_cubic 과 W_est 를 함께 굴려 W_max 에 닿는 시간과 그때 이긴 쪽을 돌려준다.

    W_est 는 RTT 마다 alpha 만큼 는다 (4.3 절 식을 한 RTT 로 묶은 것).
    cwnd 는 둘 중 큰 값이다 — W_est 가 크면 Reno 친화 구간.
    """
    k = cubic_k(w_max)
    w_est = CUBIC_BETA * w_max
    t = 0.0
    while True:
        t += rtt
        w_est += CUBIC_ALPHA
        w_cubic = CUBIC_C * (t - k) ** 3 + w_max
        if max(w_cubic, w_est) >= w_max:
            return t, ("W_est (Reno 친화)" if w_est >= w_cubic else "W_cubic")


def bdp_segments(bandwidth_mbps: float, rtt_ms: float) -> float:
    """BBR.bdp = BBR.bw * BBR.min_rtt (드래프트 2.9.2 절)."""
    bytes_per_sec = bandwidth_mbps * 1_000_000 / 8
    return bytes_per_sec * rtt_ms / 1000 / SEGMENT_BYTES


def queue_rtt_ms(rtprop_ms: float, inflight: float, bdp: float) -> float:
    """병목 큐 하나만 있는 경로. BDP 를 넘는 분량은 큐에 쌓여 그만큼 RTT 가 는다."""
    queued = max(0.0, inflight - bdp)
    return rtprop_ms * (1 + queued / bdp)


def main() -> None:
    print("== 상수 ==")
    print(f"  CUBIC C = {CUBIC_C}, beta = {CUBIC_BETA}, alpha = 3(1-b)/(1+b) = {CUBIC_ALPHA:.4f}")
    print("  Reno: 혼잡 회피에서 RTT 마다 +1, 손실 시 절반 (RFC 5681)")

    print("\n== 1. 손실 뒤 W_max 로 돌아오는 시간 — Reno ==")
    print("  W_max | RTT    | 걸린 RTT 수 | 시간(초)")
    for w_max in (100, 1000):
        for rtt in (0.01, 0.1):
            sec = reno_recovery_seconds(w_max, rtt)
            print(f"  {w_max:5d} | {rtt*1000:4.0f}ms | {w_max/2:11.0f} | {sec:8.2f}")

    print("\n== 2. CUBIC 의 K — RTT 가 식에 없다 ==")
    print("  W_max | K(초)")
    for w_max in (100, 1000):
        print(f"  {w_max:5d} | {cubic_k(w_max):6.3f}")

    print("\n== 3. CUBIC 이 실제로 W_max 에 닿는 시간 — max(W_cubic, W_est) ==")
    print("  W_max | RTT    | 시간(초) | 먼저 닿은 쪽")
    for w_max in (100, 1000):
        for rtt in (0.01, 0.1, 0.3):
            t, winner = cubic_recovery(w_max, rtt)
            print(f"  {w_max:5d} | {rtt*1000:4.0f}ms | {t:8.2f} | {winner}")

    print("\n== 4. BBR 의 모델 — BDP = 대역폭 x 최소 RTT ==")
    print("  대역폭   | min_rtt | BDP(세그먼트) | cwnd 상한 2 x BDP")
    for bw, rtt_ms in ((100, 40), (1000, 40), (100, 200)):
        bdp = bdp_segments(bw, rtt_ms)
        print(f"  {bw:5d}Mbps | {rtt_ms:5d}ms | {bdp:13.1f} | {2*bdp:10.1f}")

    print("\n== 5. 기내 데이터(inflight)가 BDP 를 넘으면 RTT 가 는다 ==")
    print("  병목 100Mbps, RTprop 40ms, 버퍼 = 1 BDP 인 경로")
    bdp = bdp_segments(100, 40)
    buffer = bdp
    print(f"  BDP = {bdp:.1f} 세그먼트, 버퍼 = {buffer:.1f} 세그먼트")
    print("  inflight 배수 | 큐(세그먼트) | RTT(ms) | 비고")
    cases = (
        (0.9, "BBR ProbeBW_DOWN pacing_gain"),
        (1.0, "BBR CRUISE 목표 (큐 없음)"),
        (1.25, "BBR ProbeBW_UP pacing_gain"),
        (2.0, "손실 기반이 버퍼를 다 채운 순간"),
    )
    for ratio, note in cases:
        inflight = bdp * ratio
        queued = max(0.0, inflight - bdp)
        print(f"  {ratio:13.2f} | {queued:12.1f} | {queue_rtt_ms(40, inflight, bdp):7.1f} | {note}")

    print("\n== 6. 손실 기반이 버퍼를 채우고 비우는 한 주기 (Reno, 같은 경로) ==")
    # 버퍼가 넘칠 때(inflight = 2 BDP) 손실, 절반으로 줄어 1 BDP 에서 다시 시작
    cwnd = 2 * bdp / 2
    rounds = 0
    rtt_sum = 0.0
    while cwnd <= bdp + buffer:
        rtt_sum += queue_rtt_ms(40, cwnd, bdp)
        cwnd += 1
        rounds += 1
    print(f"  한 주기 = {rounds} RTT, 평균 RTT = {rtt_sum/rounds:.1f}ms (RTprop 40ms)")
    print(f"  주기 시간 = {rtt_sum/1000:.2f}초 — 이 동안 큐는 0 에서 버퍼 끝까지 쌓인다")


if __name__ == "__main__":
    main()
