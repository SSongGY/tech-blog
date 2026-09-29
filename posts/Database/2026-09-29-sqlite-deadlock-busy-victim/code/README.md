# 예제 코드 — SQLite 교착과 SQLITE_BUSY

`deadlock_victim.py` 하나로 두 연결이 같은 DB 파일을 두고 부딪히는 다섯 경우를 돌린다.
표준 라이브러리만 쓴다. DB 파일은 임시 폴더에 만들고 끝나면 지운다.

## 실행

```bash
python deadlock_victim.py
```

## 무엇을 보는가

두 연결 모두 `busy_timeout`이 1초다. 각 줄의 **시간** 칸이 판정 기준이다.

| 시간 | 뜻 |
|---|---|
| 약 1초 | busy handler 가 불려서 1초 동안 잠금을 기다리다 포기했다 |
| 약 0초 | busy handler 를 부르지 않고 바로 `SQLITE_BUSY`를 돌려줬다 |

| 번호 | 경우 | 저널 |
|---|---|---|
| 1 | 한쪽이 쓰는 중에 다른 쪽이 `BEGIN IMMEDIATE` | rollback |
| 2-A | 둘 다 읽은 뒤 A가 먼저 쓴다 | rollback |
| 2-B | 둘 다 읽은 뒤 B가 먼저 쓴다 | rollback |
| 3 | 둘 다 `BEGIN IMMEDIATE`, A가 0.3초 뒤 커밋 | rollback |
| 4 | 2-A와 같은 순서 | WAL |

## 바꿔 볼 값

- `BUSY_TIMEOUT_S`를 5로 늘린다. 1번과 2번의 첫 `COMMIT`은 5초로 늘고, 2번의 두 번째
  `UPDATE`는 그대로 0초다. 기다려도 풀리지 않는 경우를 SQLite 가 가려낸다는 뜻이다.
- `LATE_COMMIT_S`를 `BUSY_TIMEOUT_S`보다 크게 한다. 3번의 B가 기다리다 `SQLITE_BUSY`로 바뀐다.
