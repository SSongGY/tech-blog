# 예제 코드 — 트랜잭션 기본 — COMMIT, ROLLBACK, SAVEPOINT

임시 폴더에 파일 DB를 만들고 두 연결(세션 A·B)을 열어, 계좌 표 `account`와 기록 표 `transfer_log`로
트랜잭션 문장을 차례로 돌린다. 파이썬 표준 라이브러리만 쓴다.

| 장 | 무엇을 보는가 |
|---|---|
| 1 | BEGIN 없이 쓴 문장은 곧바로 저장되는 것 (자동 커밋) |
| 2 | BEGIN 이후 바꾼 값이 COMMIT 전에는 다른 세션에 안 보이는 것 |
| 3 | ROLLBACK 이 BEGIN 이후의 변경을 전부 되돌리는 것 |
| 4 | 쓰는 트랜잭션이 열려 있으면 다른 세션의 쓰기가 `database is locked`로 실패하는 것 |
| 5 | SAVEPOINT·ROLLBACK TO·RELEASE, 그리고 ROLLBACK TO 뒤에도 저장점이 남는 것 |
| 6 | BEGIN 없이 SAVEPOINT 로 시작한 트랜잭션은 RELEASE 가 COMMIT 이 되는 것 |
| 7 | 트랜잭션 도중 한 문장이 실패해도 트랜잭션은 열린 채 남는 것 |
| 8 | COMMIT 없이 연결을 닫으면 변경이 사라지는 것 |

## 실행

```bash
python transaction_basics.py
```

## 바꿔볼 값

- `open_session`의 `timeout=0`을 `timeout=2`로 바꾸면 4장의 B가 2초 기다린 뒤 실패한다.
- 7장에서 `ROLLBACK` 대신 `COMMIT`을 넣으면 실패한 문장 앞의 +500 만 저장된다.
- `a.executescript(SCHEMA)` 다음에 `a.execute("PRAGMA journal_mode=WAL")`을 넣고 4장을 다시 본다.
