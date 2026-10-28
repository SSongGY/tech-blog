# Redis 분산 락 예제

락이 깨지는 자리를 여섯 단계로 하나씩 재현한다. Redis 서버 없이 돌리려고
`fakeredis` 를 쓴다. `redis-py` 와 같은 명령 API 를 쓰므로 `SET NX PX`·`TTL`·`EVAL`
같은 명령 수준의 동작은 그대로 보이지만, **네트워크 지연·복제·페일오버는
재현되지 않는다.**

## 준비

```bash
python -m pip install -r requirements.txt
```

## 실행

```bash
python lock_pitfalls.py
```

## 바꿔 볼 값

| 값 | 어디 | 무엇이 달라지는가 |
|---|---|---|
| `px=300` → `px=2000` | 실험 [3] | 작업(0.45초)이 TTL 안에 끝나 두 워커가 겹치지 않는다 |
| `time.sleep(0.45)` → `0.1` | 실험 [3]·[5]·[6] | 만료 전에 끝나므로 해제가 정상 동작한다 |
| `fence <= self.last_token` → `False` | 실험 [6] | 펜싱을 끄면 뒤처진 A 의 쓰기가 B 의 결과를 덮는다 |

실제 Redis 서버에 붙이고 싶으면 `new_server()` 를
`redis.Redis(host=..., decode_responses=True)` 로 바꾼다. 나머지 코드는 그대로 돈다.
