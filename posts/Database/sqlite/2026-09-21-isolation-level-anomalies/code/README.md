# 트랜잭션 격리 — 이상 현상 재현

```bash
python isolation_anomalies.py
```

표준 라이브러리만 쓴다. 임시 폴더에 DB를 만들고 끝나면 지운다.
두 연결을 한 스레드에서 번갈아 조작하므로 실행할 때마다 같은 결과가 나온다.

## 바꿔볼 값

| 값 | 기본 | 바꾸면 |
|---|---|---|
| `BUSY_TIMEOUT_SEC` | `0.5` | 늘려도 3번 실험의 교착은 풀리지 않는다. 기다리는 시간만 길어진다 |
| `demo_repeatable`의 `journal_mode` | `delete`, `wal` | `truncate`, `persist`도 롤백 저널 계열이라 `delete`와 같게 동작한다 |
| `reader.execute("PRAGMA read_uncommitted = 1")` | 켬 | 끄면 공유 캐시여도 더티 리드가 사라진다 |
| `connect()`의 `isolation_level` | `None` | 기본값(`""`)으로 두면 드라이버가 DML 앞에 BEGIN을 넣어 경계가 달라진다 |
