# 예제 코드 — Tibero 7 트랜잭션 격리 수준

**아직 실행하지 않았다.** 글을 쓴 시점(2026-09-30)에 검증용 Tibero 인스턴스에 접속할 수 없었다(`TBR-2131`).
인스턴스가 살아나면 아래로 돌려 `output.txt`를 채우고 글을 `executed`로 올린다.

`transaction_isolation.sql`은 한 세션 안에서 확인할 수 있는 것만 담았다.

1. `SET TRANSACTION`을 트랜잭션 첫 문장으로 쓸 때와 `UPDATE`·`SELECT` 뒤에 쓸 때 (`TBR-7191` 여부)
2. `READ ONLY` 트랜잭션에서 `UPDATE` (에러 21030 여부)
3. 매뉴얼 목록에 없는 `REPEATABLE READ`·`READ UNCOMMITTED`를 넘길 때의 반응
4. `SET TRANSACTION NAME`
5. `ALTER SESSION SET ISOLATION_LEVEL`

빈 스키마에 `iso_account` 표 하나만 만들고, 끝에서 지운 뒤 `user_objects`가 0개인지 찍는다.

## 실행

```bash
tbsql -s <사용자>/<암호> @transaction_isolation.sql
```

tbsql 스크립트 모드에서는 문장 뒤 같은 줄에 `--` 주석을 달지 않는다. 설명은 `PROMPT` 줄로 둔다.

## 두 세션이 필요한 확인 — 스크립트에 넣지 않은 것

`SERIALIZABLE`에서 에러 21012가 나는 순간은 세션 두 개를 번갈아 돌려야 보인다. 터미널 두 개를 열고 아래 순서로 친다.

| 순서 | 세션 A | 세션 B |
|---|---|---|
| 1 | `SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;` | |
| 2 | `SELECT balance FROM iso_account WHERE account_id = 1;` | |
| 3 | | `UPDATE iso_account SET balance = 900 WHERE account_id = 1; COMMIT;` |
| 4 | `SELECT balance FROM iso_account WHERE account_id = 1;` (1000이 그대로인가) | |
| 5 | `UPDATE iso_account SET balance = balance - 100 WHERE account_id = 1;` (21012가 나는가) | |

같은 순서를 `READ COMMITTED`로 바꿔 4번에서 900이 보이는지, 5번이 성공하는지도 본다.
