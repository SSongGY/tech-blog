"""RED과 CoDel의 판단 규칙을 원 논문·RFC 식 그대로 계산한다.

RED  : Floyd & Jacobson, IEEE/ACM ToN 1993 — §4 알고리즘, §6.2 w_q 하한, §7 표시 확률
CoDel: RFC 8289 — §5.5 dequeue 의사코드, §5.6 control_law
TCP 송신원의 반응은 모델에 넣지 않았다. 판단 규칙이 무엇을 언제 버리는지만 본다.
"""

import math
import random

PACKET_BYTES = 1500


# ---------------------------------------------------------------- RED

def red_initial_probability(avg, min_th, max_th, max_p):
    """논문 §7의 p_b. 두 임계치 사이에서 0 → max_p 로 선형 증가한다."""
    if avg < min_th:
        return 0.0
    if avg >= max_th:
        return 1.0  # 이 구간은 확률이 아니라 '도착하는 패킷 전부 표시'다
    return max_p * (avg - min_th) / (max_th - min_th)


def red_final_probability(p_b, count):
    """§7 Method 2. count 는 직전 표시 이후 표시하지 않은 패킷 수다."""
    if count * p_b >= 1:
        return 1.0
    return p_b / (1 - count * p_b)


def arrivals_until_avg(w_q, goal=1 - 1 / math.e):
    """큐가 0에서 1로 바뀐 채 유지될 때 EWMA 평균이 goal 에 닿기까지의 도착 수 (§6.2)."""
    avg, n = 0.0, 0
    while avg < goal:
        avg = (1 - w_q) * avg + w_q * 1
        n += 1
    return n


def intermark_gaps(p_b, method, samples, rng):
    """표시 사이 간격(도착 수)을 모은다. method 1: 매번 p_b, method 2: count 반영."""
    gaps, count = [], 0
    while len(gaps) < samples:
        p = p_b if method == 1 else red_final_probability(p_b, count)
        count += 1
        if rng.random() < p:
            gaps.append(count)
            count = 0
    return gaps


def section_red():
    print("== 1. RED 초기 표시 확률 p_b (min_th 5, max_th 15, max_p 0.02) ==")
    for avg in [4, 5, 7.5, 10, 12.5, 14.9, 15, 20]:
        p_b = red_initial_probability(avg, 5, 15, 0.02)
        print(f"  평균 큐 {avg:>5}  p_b = {p_b:.4f}")

    print("\n== 2. 최종 확률 p_a — 평균 큐 10, p_b 0.01 에서 count 가 늘 때 ==")
    for count in [0, 25, 50, 75, 90, 99, 100]:
        p_a = red_final_probability(0.01, count)
        print(f"  count {count:>3}  p_a = {p_a:.4f}")

    print("\n== 3. 표시 간격 분포 — p_b 0.01, 표시 10,000번 ==")
    for method in (1, 2):
        gaps = intermark_gaps(0.01, method, 10_000, random.Random(7))
        mean = sum(gaps) / len(gaps)
        short = sum(1 for g in gaps if g <= 5)
        print(f"  Method {method}  평균 {mean:6.1f}  최대 {max(gaps):4d}  "
              f"5개 이내 연속 표시 {short:4d}번")
    print("  이론값  Method 1 평균 1/p_b = 100,  Method 2 평균 (1/p_b + 1)/2 = 50.5, 최대 100")

    print("\n== 4. EWMA 가중치 w_q 와 반응 속도 (§6.2: 1000 / 500 / 333) ==")
    for w_q in (0.001, 0.002, 0.003):
        print(f"  w_q {w_q}  평균이 0.63 에 닿기까지 {arrivals_until_avg(w_q)}개 도착")


# ---------------------------------------------------------------- 큐 길이 대 지연

def section_length_vs_delay():
    print("\n== 5. 같은 큐 길이 50패킷(1500B)이 링크 속도별로 뜻하는 지연 ==")
    for mbps in (1, 10, 100, 1000):
        delay_ms = 50 * PACKET_BYTES * 8 / (mbps * 1e6) * 1000
        target_pkts = 0.005 * mbps * 1e6 / (PACKET_BYTES * 8)
        print(f"  {mbps:>5} Mbps  50패킷 = {delay_ms:7.1f} ms   "
              f"CoDel TARGET 5 ms = {target_pkts:7.2f} 패킷")


# ---------------------------------------------------------------- CoDel

TARGET = 5.0      # ms, RFC 8289 §4.3
INTERVAL = 100.0  # ms, RFC 8289 §4.2


def control_law(t, count):
    return t + INTERVAL / math.sqrt(count)


class CoDel:
    """RFC 8289 §5.5 의 dequeue 상태 기계. 바이트 수 검사(MAXPACKET)는 뺐다."""

    def __init__(self):
        self.first_above_time = 0.0
        self.drop_next = 0.0
        self.count = 0
        self.lastcount = 0
        self.dropping = False
        self.drops = []

    def _ok_to_drop(self, now, sojourn):
        if sojourn < TARGET:
            self.first_above_time = 0.0
            return False
        if self.first_above_time == 0.0:
            self.first_above_time = now + INTERVAL
            return False
        return now >= self.first_above_time

    def dequeue(self, now, sojourn):
        ok = self._ok_to_drop(now, sojourn)
        if self.dropping:
            if not ok:
                self.dropping = False
            while self.dropping and now >= self.drop_next:
                self.count += 1
                self.drops.append((now, self.count, "제어 법칙"))
                ok = self._ok_to_drop(now, sojourn)
                if not ok:
                    self.dropping = False
                else:
                    self.drop_next = control_law(self.drop_next, self.count)
        elif ok:
            self.dropping = True
            delta = self.count - self.lastcount
            self.count = 1
            if delta > 1 and now - self.drop_next < 16 * INTERVAL:
                self.count = delta  # 직전 드롭 속도를 이어받는다
            self.drops.append((now, self.count, "진입"))
            self.drop_next = control_law(now, self.count)
            self.lastcount = self.count


def run_codel(name, sojourn_at, until_ms):
    codel = CoDel()
    for now in range(1, until_ms + 1):  # 1 ms 마다 패킷 하나를 꺼낸다고 본다
        codel.dequeue(float(now), sojourn_at(now))
    print(f"\n  [{name}] 드롭 {len(codel.drops)}회")
    for now, count, why in codel.drops:
        print(f"    {now:6.0f} ms  count {count:2d}  ({why})")


def good_queue(now):
    # 0~40 ms 에 쌓였다가 80 ms 에 다 빠지는 버스트. 최대 체류 40 ms
    if now <= 40:
        return float(now)
    return max(0.0, 40.0 - (now - 40))


def standing_queue(now):
    # 20 ms 체류가 400 ms 동안 계속되다 50 ms 빠지고, 다시 300 ms 선다
    if now <= 400:
        return 20.0
    if now <= 450:
        return 2.0
    return 20.0


def section_codel():
    print("\n== 6. CoDel 제어 법칙 — 드롭 진입 후 다음 드롭까지의 간격 ==")
    t = 0.0
    for count in range(1, 11):
        gap = INTERVAL / math.sqrt(count)
        t += gap
        print(f"  count {count:2d}  간격 {gap:6.1f} ms  누적 {t:7.1f} ms")

    print("\n== 7. 체류 시간 흐름에 CoDel 상태 기계를 돌린 결과 ==")
    run_codel("좋은 큐: 80 ms 안에 빠지는 버스트", good_queue, 200)
    run_codel("나쁜 큐: 20 ms 체류가 서 있음, 450 ms 에 재진입", standing_queue, 750)


if __name__ == "__main__":
    section_red()
    section_length_vs_delay()
    section_codel()
