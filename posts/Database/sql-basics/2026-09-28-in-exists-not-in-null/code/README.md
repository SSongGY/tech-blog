# 예제 코드 — IN, EXISTS, NOT IN

메모리 SQLite에 고객 5명과 구매 6건을 넣는다. 구매 한 건은 비회원 결제라 `customer_id`가
NULL이다. "산 적이 있는 고객"과 "한 번도 안 산 고객"을 `IN`·`EXISTS`·`JOIN`으로 각각 풀어
결과를 나란히 찍는다. 외부 의존성 없이 파이썬 표준 라이브러리만 쓴다.

## 실행

```bash
python in_exists_not_in.py
```

## 바꿔볼 값

- `PURCHASES`의 `(105, None, 7000)`을 지우면 3-A의 `NOT IN`이 3-B와 같은 결과를 낸다(4-A가 이것을 확인한다).
- `purchase.customer_id`에 `NOT NULL`을 붙이면 105번 행을 넣을 수 없어 삽입에서 에러가 난다.
  NULL이 들어올 수 없는 컬럼이면 `NOT IN`의 함정도 생기지 않는다.
- 2-C의 `INNER JOIN`에 `DISTINCT`를 붙이면 2-A와 같은 3행이 된다.
