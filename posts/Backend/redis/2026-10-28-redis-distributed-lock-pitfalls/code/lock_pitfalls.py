"""Redis 분산 락이 깨지는 네 자리를 하나씩 재현한다.

실행 환경에 Redis 서버가 없어 fakeredis 로 돌린다. redis-py 와 같은 명령 API 를
쓰므로 명령 수준의 동작(NX·PX·TTL·EVAL)은 그대로 보이지만, 네트워크 지연이나
복제·페일오버는 재현되지 않는다. 그 부분은 본문에서 따로 다룬다.
"""

from __future__ import annotations

import time
import uuid

import fakeredis
import redis as redis_py

LOCK_KEY = "lock:invoice:4821"

# 공식 문서가 제시하는 해제 스크립트. 값이 내 것일 때만 지운다.
RELEASE_LUA = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""


def new_server() -> fakeredis.FakeStrictRedis:
    server = fakeredis.FakeServer()
    return fakeredis.FakeStrictRedis(server=server, decode_responses=True)


def header(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def show(text: str) -> None:
    print(f"  {text}")


def versions() -> None:
    print("=" * 72)
    print("환경")
    print("=" * 72)
    show(f"fakeredis {fakeredis.__version__}  (Redis 서버 동작을 흉내 내는 구현)")
    show(f"redis-py  {redis_py.__version__}")


# ----------------------------------------------------------------------
versions()

header("[1] SETNX 와 EXPIRE 를 따로 치면 — 사이에서 죽었을 때")
r = new_server()
got = r.setnx(LOCK_KEY, "worker-a")
show(f"SETNX {LOCK_KEY} worker-a  -> {got}")
show("여기서 프로세스가 죽었다고 치고 EXPIRE 를 치지 않는다")
show(f"TTL {LOCK_KEY}  -> {r.ttl(LOCK_KEY)}   (-1 은 만료 시각이 없다는 뜻)")
show(f"다른 워커의 SETNX -> {r.setnx(LOCK_KEY, 'worker-b')}  (영원히 못 잡는다)")

header("[2] SET ... NX PX — 획득을 한 문장으로")
r = new_server()
token_a = str(uuid.uuid4())
show(f"A: SET {LOCK_KEY} <token-a> NX PX 2000 -> {r.set(LOCK_KEY, token_a, nx=True, px=2000)}")
show(f"B: SET {LOCK_KEY} <token-b> NX PX 2000 -> {r.set(LOCK_KEY, str(uuid.uuid4()), nx=True, px=2000)}")
show(f"TTL -> {r.ttl(LOCK_KEY)}초  (획득과 만료가 같은 명령에서 정해진다)")

header("[3] 작업이 TTL 보다 길어지면 — 두 워커가 같이 들어간다")
r = new_server()
token_a = str(uuid.uuid4())
r.set(LOCK_KEY, token_a, nx=True, px=300)
show("A: 락 획득 (TTL 300ms). 이제 A 가 0.45초 걸리는 작업을 한다")
time.sleep(0.45)
show(f"0.45초 뒤 TTL -> {r.ttl(LOCK_KEY)}  (-2 는 키가 없다는 뜻)")
token_b = str(uuid.uuid4())
show(f"B: SET ... NX PX 2000 -> {r.set(LOCK_KEY, token_b, nx=True, px=2000)}")
show("A 는 아직 자기가 락을 쥐고 있다고 믿는다 — 이 순간 둘 다 임계구역 안이다")

header("[4] DEL 로 해제하면 — 남의 락을 지운다")
show(f"A 가 작업을 끝내고 DEL {LOCK_KEY} -> {r.delete(LOCK_KEY)}")
show(f"B 의 락이 남아 있는가 -> {r.exists(LOCK_KEY) == 1}")
show("B 는 아직 작업 중인데 락이 사라졌다. 이제 C 가 들어올 수 있다")

header("[5] 값이 내 것일 때만 지우면")
r = new_server()
release = r.register_script(RELEASE_LUA)
token_a = str(uuid.uuid4())
r.set(LOCK_KEY, token_a, nx=True, px=300)
time.sleep(0.45)
token_b = str(uuid.uuid4())
r.set(LOCK_KEY, token_b, nx=True, px=2000)
show(f"A 가 자기 토큰으로 해제 시도 -> 지운 키 수 {release(keys=[LOCK_KEY], args=[token_a])}")
show(f"B 의 락이 남아 있는가 -> {r.exists(LOCK_KEY) == 1}")
show(f"B 가 자기 토큰으로 해제 -> 지운 키 수 {release(keys=[LOCK_KEY], args=[token_b])}")

header("[6] 그래도 남는 것 — 펜싱 토큰")
r = new_server()


class Resource:
    """락이 보호하려던 공유 자원. 받은 토큰이 뒤처지면 쓰기를 거절한다."""

    def __init__(self) -> None:
        self.content: str | None = None
        self.last_token = 0

    def write(self, text: str, fence: int) -> str:
        if fence <= self.last_token:
            return f"거절 (토큰 {fence} ≤ 이미 처리한 {self.last_token})"
        self.last_token = fence
        self.content = text
        return f"기록 (토큰 {fence})"


resource = Resource()
token_a = str(uuid.uuid4())
r.set(LOCK_KEY, token_a, nx=True, px=300)
fence_a = r.incr("fence:invoice:4821")
show(f"A: 락 획득, 펜싱 토큰 {fence_a}. 작업 중 0.45초 멈춘다")
time.sleep(0.45)

token_b = str(uuid.uuid4())
r.set(LOCK_KEY, token_b, nx=True, px=2000)
fence_b = r.incr("fence:invoice:4821")
show(f"B: 락 획득, 펜싱 토큰 {fence_b}")
show(f"B 가 먼저 쓴다 -> {resource.write('B 가 계산한 값', fence_b)}")
show(f"A 가 깨어나 쓴다 -> {resource.write('A 가 계산한 값', fence_a)}")
show(f"자원에 남은 내용 -> {resource.content}")
print()
show("락만으로는 A 의 쓰기를 막지 못한다. 자원 쪽에서 토큰을 보고 거절해야 막힌다.")
