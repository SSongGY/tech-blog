# 예제 코드 — SQLite WAL에서 오래 열린 읽기 트랜잭션의 비용

임시 폴더에 파일 DB를 만들고 두 연결(읽는 쪽·쓰는 쪽)을 연다. rollback journal 모드와 WAL 모드에서
같은 순서로 읽기·쓰기를 섞어 어디서 막히는지 보고, WAL 모드에서 읽기 트랜잭션을 연 채 커밋을
1,200번 쌓아 체크포인트 결과와 WAL 파일 크기를 찍는다. 외부 의존성 없이 파이썬 표준 라이브러리만 쓴다.
임시 폴더는 실행이 끝나면 지워진다.

## 실행

```bash
python mvcc_wal_cost.py
```

## 바꿔볼 값

- `WRITE_BATCHES`·`COMMITS_PER_BATCH`를 늘리면 읽기 트랜잭션이 열려 있는 동안 WAL이 커지는 폭이 늘어난다.
- `measure_wal_growth`에서 체크포인트 모드를 `PASSIVE`에서 `RESTART`로 바꾸면, 열린 읽기 트랜잭션
  때문에 `busy`가 1이 되는지 볼 수 있다(`timeout=0`이라 기다리지 않는다).
- `ACCOUNT_COUNT`를 늘리면 표가 여러 페이지로 나뉘어 커밋 한 번에 붙는 프레임 수가 달라진다.
