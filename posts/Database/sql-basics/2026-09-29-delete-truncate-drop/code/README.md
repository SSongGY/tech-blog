# 예제 코드 — DELETE, TRUNCATE, DROP — 무엇이 어디까지 지우는가

메모리 DB에 상품 표 `product` 4행을 만들고 `DELETE`와 `DROP TABLE`을 트랜잭션 안에서 돌려
되돌릴 수 있는지 본다. 이어 임시 폴더에 파일 DB를 만들어 2만 행을 넣고 지운 뒤
파일 크기·전체 페이지·빈 페이지가 어떻게 바뀌는지 잰다. 파이썬 표준 라이브러리만 쓴다.

| 장 | 무엇을 보는가 |
|---|---|
| 1 | `DELETE ... WHERE`가 고른 행만 지우고 `ROLLBACK`으로 돌아오는 것 |
| 2 | `WHERE` 없는 `DELETE`가 행을 전부 지우되 표는 남기는 것 |
| 3 | `DROP TABLE`이 표 정의까지 지우고, SQLite에서는 이것도 `ROLLBACK`되는 것 |
| 4 | SQLite에 `TRUNCATE` 문이 없다는 것 |
| 5 | 지운 뒤 파일 크기는 그대로이고 빈 페이지만 늘며, `VACUUM`이 파일을 줄이는 것 |
| 6 | `auto_vacuum = FULL`이면 `DELETE` 직후 파일이 줄어드는 것 |

## 실행

```bash
python delete_truncate_drop.py
```

## 바꿔볼 값

- `BULK_ROWS`를 늘리거나 줄여 5장의 페이지 수가 비례해 움직이는지 본다.
- 5장의 `DELETE FROM access_log`에 `WHERE log_id % 2 = 0`을 붙이면 반만 지워진다.
  이때 빈 페이지가 얼마나 생기는지 본다. 행이 흩어져 지워지면 페이지가 통째로 비지 않을 수 있다.
