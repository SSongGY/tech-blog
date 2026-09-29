# 예제 코드 — ALTER TABLE — 컬럼을 바꿀 때의 제약

메모리 DB에 회원 표 `member`, 주문 표 `orders`(외래 키), 인덱스 하나, 뷰 하나를 만들고
SQLite의 `ALTER TABLE`이 받아들이는 변경과 거절하는 변경을 차례로 돌린다. 파이썬 표준 라이브러리만 쓴다.

| 장 | 무엇을 보는가 |
|---|---|
| 1 | `ADD COLUMN`이 기존 행에 기본값을 채우는 것 |
| 2 | `ADD COLUMN`이 거절하는 네 가지 — 기본값 없는 NOT NULL, UNIQUE, CURRENT_TIMESTAMP, 기존 행이 어기는 CHECK |
| 3 | `RENAME COLUMN`이 뷰 정의까지 고치는 것 |
| 4 | 인덱스가 걸린 컬럼의 `DROP COLUMN`이 실패하는 것 |
| 5 | `ALTER COLUMN`이 이 판(3.49.1)에 없는 것 |
| 6 | 공식 문서 순서대로 표를 다시 만들어 NOT NULL을 더하는 절차 |
| 7 | 옛 표 이름을 먼저 바꾸면 외래 키와 뷰가 사라진 표를 가리키게 되는 것 |

## 실행

```bash
python alter_table_basics.py
```

## 바꿔볼 값

- 2장의 `CHECK (point > 0)`을 `CHECK (point >= 0)`으로 바꾸면 기존 행이 조건을 지켜 성공한다.
- 4장 앞에 `DROP INDEX ix_member_phone`을 넣으면 `phone`도 지워진다.
- SQLite 3.53.0 이상에서 돌리면 5장의 `SET NOT NULL`이 성공하는지 본다.
