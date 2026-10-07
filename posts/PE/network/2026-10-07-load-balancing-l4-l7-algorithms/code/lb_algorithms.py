"""로드 밸런서 분배 알고리즘을 같은 요청 흐름에 적용해 분배 결과를 비교한다.

망을 흉내 낸 측정이 아니라 **알고리즘 자체의 계산**이다. 보는 것 4가지.
1. 라운드 로빈과 가중 라운드 로빈 — 요청 수가 가중치 비율로 나뉘는가
2. 최소 연결 — 요청 길이가 제각각일 때 라운드 로빈과 동시 접속 수가 어떻게 다른가
3. 해시 분배 — 서버를 하나 더할 때 mod N, 링 기반 일관된 해시, Maglev 해시가 각각 몇 %의 키를 옮기는가
4. 세션 고정 — 출발지 IP 해시로 고정하면 NAT 뒤의 사용자 때문에 치우침이 얼마나 생기는가

난수는 시드를 고정했고 해시는 hashlib 을 써서 어디서 돌려도 같은 값이 나온다.
"""

import hashlib
import random
import statistics
from bisect import bisect_right

SEED = 20261007


def stable_hash(text: str, salt: str = "") -> int:
    """파이썬 hash() 는 실행마다 바뀌므로 SHA-1 앞 8바이트를 정수로 쓴다."""
    return int.from_bytes(hashlib.sha1((salt + text).encode()).digest()[:8], "big")


def share_table(title: str, counts: dict[str, int]) -> None:
    total = sum(counts.values())
    print(f"   {title}")
    for name in sorted(counts):
        print(f"     {name:<8} {counts[name]:>6}건  {counts[name] / total * 100:5.1f}%")


# ---------------------------------------------------------------- 1. 라운드 로빈
def round_robin(servers: list[str], request_count: int) -> dict[str, int]:
    counts = {s: 0 for s in servers}
    for i in range(request_count):
        counts[servers[i % len(servers)]] += 1
    return counts


def weighted_round_robin(weights: dict[str, int], request_count: int) -> dict[str, int]:
    """가중치만큼 차례를 더 받는 가장 단순한 형태. 가중치 3·2·1 이면 한 바퀴가 6칸이다."""
    cycle = [name for name, w in weights.items() for _ in range(w)]
    counts = {s: 0 for s in weights}
    for i in range(request_count):
        counts[cycle[i % len(cycle)]] += 1
    return counts


# ---------------------------------------------------------------- 2. 최소 연결
def simulate_connections(
    policy: str, servers: list[str], durations: list[int], slowdown: dict[str, int]
) -> tuple[dict[str, int], dict[str, int]]:
    """매 틱에 요청 하나가 들어오고 durations[i] × slowdown[서버] 틱 뒤에 끝난다.

    서버별 (받은 요청 수, 최대 동시 접속 수) 를 돌려준다. 분배기는 서버가 느린지 모른다 —
    최소 연결은 현재 열린 연결 수만 보고 고른다.
    """
    active: dict[str, list[int]] = {s: [] for s in servers}   # 서버별 종료 시각 목록
    peak = {s: 0 for s in servers}
    counts = {s: 0 for s in servers}
    for tick, duration in enumerate(durations):
        for s in servers:
            active[s] = [end for end in active[s] if end > tick]
        if policy == "round_robin":
            chosen = servers[tick % len(servers)]
        else:  # least_conn — 동률이면 이름 순 첫 번째
            chosen = min(servers, key=lambda s: (len(active[s]), s))
        active[chosen].append(tick + duration * slowdown[chosen])
        counts[chosen] += 1
        peak[chosen] = max(peak[chosen], len(active[chosen]))
    return counts, peak


# ---------------------------------------------------------------- 3. 해시 분배
def mod_hash(servers: list[str], keys: list[str]) -> dict[str, str]:
    return {k: servers[stable_hash(k) % len(servers)] for k in keys}


class HashRing:
    """Karger 식 일관된 해시. 서버마다 points 개의 점을 링(0..2^64)에 찍고, 키는 시계 방향 첫 점의 서버로 간다."""

    def __init__(self, servers: list[str], points: int = 160) -> None:
        pairs = sorted((stable_hash(f"{s}#{i}"), s) for s in servers for i in range(points))
        self.positions = [p for p, _ in pairs]
        self.owners = [s for _, s in pairs]

    def lookup(self, key: str) -> str:
        idx = bisect_right(self.positions, stable_hash(key))
        return self.owners[idx % len(self.owners)]


class MaglevTable:
    """Maglev 해시(Eisenbud et al., NSDI 2016) 의사코드 1 그대로. M 은 소수여야 한다."""

    def __init__(self, servers: list[str], table_size: int = 65537) -> None:
        self.size = table_size
        n = len(servers)
        offsets = [stable_hash(s, "offset") % table_size for s in servers]
        skips = [stable_hash(s, "skip") % (table_size - 1) + 1 for s in servers]
        next_index = [0] * n
        entry = [-1] * table_size
        filled = 0
        while True:
            for i in range(n):
                c = (offsets[i] + next_index[i] * skips[i]) % table_size
                while entry[c] >= 0:
                    next_index[i] += 1
                    c = (offsets[i] + next_index[i] * skips[i]) % table_size
                entry[c] = i
                next_index[i] += 1
                filled += 1
                if filled == table_size:
                    self.entry = [servers[e] for e in entry]
                    return

    def lookup(self, key: str) -> str:
        return self.entry[stable_hash(key) % self.size]

    def shares(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for s in self.entry:
            counts[s] = counts.get(s, 0) + 1
        return counts


def moved_fraction(before: dict[str, str], after: dict[str, str]) -> float:
    return sum(1 for k in before if before[k] != after[k]) / len(before)


# ---------------------------------------------------------------- 4. 세션 고정
def sticky_by_source_ip(servers: list[str], sessions: list[str]) -> dict[str, int]:
    ring = HashRing(servers)
    counts = {s: 0 for s in servers}
    for ip in sessions:
        counts[ring.lookup(ip)] += 1
    return counts


def main() -> None:
    rng = random.Random(SEED)

    print("== 1. 라운드 로빈 vs 가중 라운드 로빈 — 요청 600건")
    servers = ["web-a", "web-b", "web-c"]
    share_table("라운드 로빈 (가중치 없음)", round_robin(servers, 600))
    share_table("가중 라운드 로빈 (web-a 3 · web-b 2 · web-c 1)",
                weighted_round_robin({"web-a": 3, "web-b": 2, "web-c": 1}, 600))

    print("\n== 2. 서버 한 대가 느릴 때 — 라운드 로빈 vs 최소 연결, 요청 3,000건")
    # 70% 는 2틱 만에 끝나는 짧은 요청, 30% 는 40틱 걸리는 긴 요청(보고서 생성 같은 것).
    # web-c 는 디스크가 느려 모든 요청이 3배 오래 걸린다. 분배기는 이 사실을 모른다.
    durations = [2 if rng.random() < 0.7 else 40 for _ in range(3000)]
    slowdown = {"web-a": 1, "web-b": 1, "web-c": 3}
    print(f"   짧은 요청(2틱) {durations.count(2)}건 · 긴 요청(40틱) {durations.count(40)}건 · web-c 는 3배 느림")
    for policy in ("round_robin", "least_conn"):
        counts, peak = simulate_connections(policy, servers, durations, slowdown)
        print(f"   {policy:<12} 받은 요청: "
              + ", ".join(f"{s} {counts[s]}" for s in servers)
              + " / 최대 동시 접속: "
              + ", ".join(f"{s} {peak[s]}" for s in servers))

    print("\n== 3. 서버 4대 → 5대로 늘릴 때 자리를 옮기는 키의 비율 — 키 20,000개")
    keys = [f"user-{i}" for i in range(20000)]
    four = ["app-1", "app-2", "app-3", "app-4"]
    five = four + ["app-5"]

    mod_moved = moved_fraction(mod_hash(four, keys), mod_hash(five, keys))
    print(f"   hash mod N          : {mod_moved * 100:5.1f}% 이동  (이론값 1 - 1/5 = 80.0%: "
          f"h mod 4 == h mod 5 인 키만 남는다)")

    ring4, ring5 = HashRing(four), HashRing(five)
    ring_moved = moved_fraction({k: ring4.lookup(k) for k in keys}, {k: ring5.lookup(k) for k in keys})
    print(f"   링 일관된 해시(160점) : {ring_moved * 100:5.1f}% 이동  (이상적으로는 새 서버 몫 1/5 = 20.0% 만 옮긴다)")
    share_table("     링 일관된 해시 — 5대일 때 키 분포", {s: 0 for s in five} | {
        s: sum(1 for k in keys if ring5.lookup(k) == s) for s in five})

    mag4, mag5 = MaglevTable(four), MaglevTable(five)
    mag_moved = moved_fraction({k: mag4.lookup(k) for k in keys}, {k: mag5.lookup(k) for k in keys})
    table_changed = sum(1 for a, b in zip(mag4.entry, mag5.entry) if a != b) / mag4.size
    print(f"   Maglev 해시(M=65537) : {mag_moved * 100:5.1f}% 이동  "
          f"(조회표 칸 {table_changed * 100:.1f}% 가 바뀜)")
    shares = mag5.shares()
    print(f"     Maglev 조회표 — 서버별 칸 수: "
          + ", ".join(f"{s} {shares[s]}" for s in five)
          + f"  (최대-최소 {max(shares.values()) - min(shares.values())}칸)")

    print("\n== 4. 세션 고정 — 출발지 IP 해시의 치우침, 세션 2,000개")
    # 사무실 NAT 하나(10.0.0.1)가 전체 세션의 30% 를 내고, 나머지는 서로 다른 39개 IP 에서 온다
    client_ips = [f"203.0.113.{i}" for i in range(1, 40)]
    sessions = ["10.0.0.1" if rng.random() < 0.3 else rng.choice(client_ips) for _ in range(2000)]
    print(f"   NAT 뒤 세션 {sessions.count('10.0.0.1')}건 / 전체 {len(sessions)}건")
    share_table("라운드 로빈으로 세션을 나누고 쿠키로 고정했을 때", round_robin(four, len(sessions)))
    ip_counts = sticky_by_source_ip(four, sessions)
    share_table("출발지 IP 해시로 고정했을 때", ip_counts)
    busiest = max(ip_counts, key=ip_counts.get)
    print(f"   -> IP 해시에서 가장 바쁜 서버 {busiest} 가 평균의 "
          f"{ip_counts[busiest] / statistics.mean(ip_counts.values()):.2f}배를 받는다")

    # 서버 한 대가 빠지면 그 서버에 묶인 세션 상태는 사라진다
    lost = ip_counts[busiest]
    print(f"   -> {busiest} 가 내려가면 거기 고정돼 있던 세션 {lost}건({lost / len(sessions) * 100:.1f}%)의 "
          f"서버 측 상태가 사라진다. 세션 저장소를 밖에 두면 0건")


if __name__ == "__main__":
    main()
