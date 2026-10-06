"""CAP 정리의 증명 장면과 정족수 겹침 조건을 직접 돌려 확인한다.

1부: 복제본 N=3 에서 쓰기 정족수 W, 읽기 정족수 R 의 모든 조합을 전수 조사해
     "W + R > N 이면 읽기 집합이 항상 마지막 쓰기 집합과 겹친다"가 맞는지 센다.
2부: Gilbert·Lynch 의 증명 장면을 그대로 옮긴다. 서버 p1, p2 사이의 메시지가
     끊긴 상태에서 p1 에 쓰기가 들어오고 p2 에 읽기가 오면 p2 는
     (가) 기다리다 응답하지 않거나 (나) 자기가 가진 옛 값을 답하는 수밖에 없다.
3부: 메시지가 "늦은" 경우와 "잃어버린" 경우를 p2 가 시간 제한 안에서 구별하지
     못한다는 것을 두 실행의 p2 관측 기록을 나란히 놓아 보인다.
"""

from itertools import combinations

REPLICA_COUNT = 3


def quorum_table() -> None:
    print("==== 1부. 정족수 겹침 전수 조사 (N = 3) ====")
    nodes = range(REPLICA_COUNT)
    print("  W | R | W+R>N | 조합 수 | 겹치지 않는 조합")
    for write_size in range(1, REPLICA_COUNT + 1):
        for read_size in range(1, REPLICA_COUNT + 1):
            pairs = [
                (set(w), set(r))
                for w in combinations(nodes, write_size)
                for r in combinations(nodes, read_size)
            ]
            disjoint = sum(1 for w, r in pairs if not (w & r))
            strict = "예" if write_size + read_size > REPLICA_COUNT else "아니오"
            print(f"  {write_size} | {read_size} | {strict:<4} | {len(pairs):>6} | {disjoint}")


class Server:
    def __init__(self, name: str) -> None:
        self.name = name
        self.value = "v0"
        self.version = 0

    def apply(self, value: str, version: int) -> None:
        if version > self.version:
            self.value, self.version = value, version


def partition_scenario() -> None:
    print("\n==== 2부. 분할 중 쓰기와 읽기 ====")
    for policy in ("CP", "AP"):
        p1, p2 = Server("p1"), Server("p2")
        link_up = False          # p1 과 p2 사이 메시지가 전부 사라지는 상태
        outbox = []              # p1 이 p2 에 보내지 못한 복제 메시지

        # 클라이언트 A 가 p1 에 v1 을 쓴다.
        # CP 는 상대 복제본에 전달됐다는 확인을 받아야 ok 를 준다. 분할 중이라 못 받는다
        # AP 는 자기 복제본에 반영하고 바로 ok 를 준 뒤, 전달은 나중으로 미룬다
        if policy == "CP" and not link_up:
            write_answer = "응답 없음 (오류 반환)"
        else:
            p1.apply("v1", 1)
            outbox.append(("v1", 1))
            write_answer = "ok"
        print(f"\n[{policy}] 분할 중 p1 에 v1 쓰기 → {write_answer}"
              f"  (p1={p1.value}, p2={p2.value})")

        # 클라이언트 B 가 p2 에 읽기. CP 는 상대와 맞춰 보지 못하면 답하지 않는다
        if policy == "CP" and not link_up:
            read_answer = "응답 없음 (오류 반환)"
        else:
            read_answer = p2.value
        print(f"[{policy}] 분할 중 p2 읽기 → {read_answer}")

        # 원자적 일관성 위반: 완료(ok)된 쓰기 뒤의 읽기가 그 값을 못 본 경우
        stale = write_answer == "ok" and read_answer not in ("v1", "응답 없음 (오류 반환)")
        print(f"[{policy}] 완료된 쓰기 뒤에 옛 값을 읽었는가 → {stale}")

        # 분할이 풀리면 쌓인 복제 메시지가 전달된다
        link_up = True
        for value, version in outbox:
            p2.apply(value, version)
        print(f"[{policy}] 분할 해소 후 p2 읽기 → {p2.value}")


def observed_by_p2(drop: bool, delay: int, timeout: int) -> list[str]:
    """p2 가 시각 0..timeout 동안 받은 메시지 기록. drop 이면 메시지가 사라진다."""
    log = []
    for tick in range(timeout + 1):
        arrived = (not drop) and tick == delay
        log.append(f"t{tick}:{'v1 도착' if arrived else '-'}")
    return log


def indistinguishable() -> None:
    print("\n==== 3부. 늦은 메시지와 잃어버린 메시지 ====")
    timeout = 3
    late = observed_by_p2(drop=False, delay=5, timeout=timeout)
    lost = observed_by_p2(drop=True, delay=5, timeout=timeout)
    print(f"  시간 제한 t{timeout} 까지 p2 가 본 것")
    print(f"  메시지가 t5 에 도착할 실행 : {' '.join(late)}")
    print(f"  메시지가 사라진 실행       : {' '.join(lost)}")
    print(f"  두 기록이 같은가           : {late == lost}")


if __name__ == "__main__":
    quorum_table()
    partition_scenario()
    indistinguishable()
