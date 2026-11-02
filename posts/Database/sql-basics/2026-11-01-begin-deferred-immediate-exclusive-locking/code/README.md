# BEGIN 세 모드의 잠금 시점 비교

연결 두 개를 열어 두고, 한쪽이 `BEGIN DEFERRED` / `BEGIN IMMEDIATE` / `BEGIN EXCLUSIVE`
로 트랜잭션을 연 동안 다른 쪽이 읽거나 쓸 수 있는지 확인한다.
SQLite 파일 DB 하나만 쓰므로 설치할 것이 없다.

## 실행

```bash
python locking_modes.py
```

작업 파일은 `probe_work/ledger.db` 에 만들어지고 실행할 때마다 지워졌다 다시 만들어진다.

## 바꿔볼 값

- `open_connection()` 의 `timeout=0` 을 `timeout=5` 로 바꾸면 `SQLITE_BUSY` 대신
  5초를 기다린다. 기다려도 상대가 커밋하지 않으므로 결국 같은 오류가 나지만,
  오류가 뜨기까지 걸리는 시간이 달라진다. 운영에서 "가끔 느리다"로 보이는 모양이다.
- 시나리오 5 의 `PRAGMA journal_mode = WAL` 줄을 지우고 돌리면 4번과 같은 결과가 된다.
  EXCLUSIVE 의 의미가 저널 모드에 따라 갈리는 자리다.
- 시나리오 2 에서 `BEGIN DEFERRED` 를 `BEGIN IMMEDIATE` 로 바꾸면 A 가 먼저
  쓰기 자리를 잡으므로 막히는 쪽이 B 로 뒤집힌다.
