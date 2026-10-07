# 예제 코드 — UPSERT, INSERT ... ON CONFLICT

외부 의존성 없다. 파이썬 표준 라이브러리 `sqlite3`로 메모리 DB에 재고 표 `stock`과 회원 표 `member`를
만들고, `ON CONFLICT`의 갈래를 하나씩 돌린다. `dbshow.py`는 표 정의와 데이터를 찍는 보조 모듈이다.

## 실행

```bash
python upsert.py
```

확인 환경: SQLite 3.49.1 (파이썬 내장) / Python 3.13.5 / Windows 11. 실행 기록은 `output.txt`.

## 각 장이 보는 것

| 장 | 확인하는 것 |
|---|---|
| 1 | `ON CONFLICT` 없는 INSERT가 같은 키에서 실패하는 것 |
| 2 | `DO NOTHING`이 있는 키는 건너뛰고 없는 키는 넣는 것 |
| 3 | `DO UPDATE`에서 `excluded.컬럼`과 그냥 `컬럼`이 가리키는 값 |
| 4 | `DO UPDATE ... WHERE`로 오래된 값을 무시하는 것 |
| 5 | `INSERT OR REPLACE`가 지정하지 않은 컬럼을 잃고 rowid가 바뀌는 것 |
| 6 | 한 문장 안에서 같은 키가 두 번 나올 때 |
| 7 | 충돌 대상과 다른 제약에서 충돌할 때, 대상을 여럿 적거나 생략할 때 |
| 8 | `INSERT ... SELECT`에 붙일 때 `WHERE true`가 필요한 것 |

## 바꿔 볼 값

- 3장의 `qty + excluded.qty`를 `excluded.qty`로 바꾸면 더하지 않고 덮어쓴다.
- 4장의 `WHERE` 절을 지우면 오래된 날짜(`2026-09-30`)도 반영된다.
