# 예제 코드 — CREATE TABLE 타입과 기본 제약조건

`constraints_basics.py` 하나로 `NOT NULL`·`UNIQUE`·`CHECK`·`DEFAULT`와 컬럼 타입이
어떤 값을 막고 어떤 값을 통과시키는지 차례로 확인한다. 표준 라이브러리만 쓰고
메모리 DB에서 돈다.

## 실행

```bash
python constraints_basics.py
```

## 바꿔 볼 값

- `price` 의 `CHECK (price > 0)` 을 `CHECK (price IS NOT NULL AND price > 0)` 으로 바꾼다.
  4번의 NULL 가격 행이 막히는지 본다.
- `barcode TEXT UNIQUE` 에 `NOT NULL` 을 더한다. 5번의 두 번째 문장이 어떻게 바뀌는지 본다.
- 8번의 `IN (2, 3)` 을 `IN (3)` 으로 줄인다. 한 행만 바꿔도 같은 에러가 나는지 본다.
