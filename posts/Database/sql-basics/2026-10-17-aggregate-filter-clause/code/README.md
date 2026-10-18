# 예제 코드 — 집계 함수의 FILTER 절

메모리 SQLite에 문의 티켓 12행을 넣고, 같은 숫자를 `CASE WHEN` 과 `FILTER` 로
각각 뽑아 결과가 일치하는지 확인한다. 이어서 둘이 갈리는 자리를 차례로 찍는다.

## 실행

```bash
python filter_clause.py
```

## 바꿔볼 값

- `TICKETS` 의 `priority` 를 전부 `normal` 로 바꾸면 4번 절(빈 집합)에서
  `COUNT` 만 0을 돌려주고 `SUM`·`AVG`·`MAX` 는 전부 NULL 이 되는 것을 모든 채널에서 볼 수 있다.
- `response_minutes` 에 NULL 을 더 넣으면 6번 절의 `참 + 거짓 + 널` 합이
  `전체` 와 맞는지가 다시 확인된다.
- 7번 절의 `OVER (PARTITION BY channel)` 을 지우면 윈도우 전체에 대한 집계가 된다.
