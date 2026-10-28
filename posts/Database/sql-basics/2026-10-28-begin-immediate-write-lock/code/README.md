# BEGIN IMMEDIATE 예제

두 연결을 같은 SQLite 파일에 붙여 놓고, 트랜잭션을 여는 방식(`BEGIN` / `BEGIN IMMEDIATE`)만
바꿔 가며 어느 문장에서 `SQLITE_BUSY` 가 나오는지 본다. 데이터베이스 파일은 임시 폴더에
만들고 실험마다 다시 만든다.

## 실행

```bash
python locking_demo.py
```

추가 의존성은 없다. `dbshow.py` 는 표 정의와 행을 출력 앞에 찍어 주는 도우미다.

## 바꿔 볼 값

| 값 | 어디 | 무엇이 달라지는가 |
|---|---|---|
| `build_database("delete")` → `"wal"` | 실험 [1] | 롤백 저널에서는 A 의 `COMMIT` 까지 `SQLITE_BUSY` 가 되지만, WAL 에서는 A 가 먼저 커밋되고 B 가 `SQLITE_BUSY_SNAPSHOT` 을 받는다 |
| `connect(3000)` → `connect(0)` | 실험 [4] | `BEGIN IMMEDIATE` 충돌이 기다리지 않고 즉시 실패한다 |
| `BEGIN IMMEDIATE` → `BEGIN EXCLUSIVE` | 실험 [3] | WAL 모드에서는 결과가 같다. `delete` 모드로 바꾸면 다른 연결의 읽기까지 막힌다 |

`probe_lock.py` · `probe_timeout.py` 는 본문에 싣지 않은 확인용 스크립트다.
