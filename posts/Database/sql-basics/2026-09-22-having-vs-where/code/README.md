# 예제 코드 — HAVING과 WHERE — 어느 단계에서 걸러지는가

메모리 SQLite에 판매 8건을 넣고, 같은 데이터에 WHERE와 HAVING을 각각 걸어
어느 단계에서 무엇이 걸러지는지 확인한다. 외부 의존성 없이 파이썬 표준 라이브러리만 쓴다.

## 실행

```bash
python having_vs_where.py
```

## 바꿔볼 값

- `ROWS`의 7번 행(`대구`, `amount`가 `None`) — 이 행을 지우면 9번 질의에서
  `COUNT(*)`와 `COUNT(amount)`가 같아진다. NULL이 집계에서 빠지는 것을 보는 자리다.
- 3번 질의의 `HAVING COUNT(*) >= 2` — 1로 낮추면 모든 그룹이 살아남는다.
- 6번 질의의 `SUM(amount) > 100000` — `GROUP BY` 없는 `HAVING`이 거짓일 때
  0건이 나오는지 `NULL` 한 줄이 나오는지 보는 자리다.
- 11-A / 11-B의 `EXPLAIN QUERY PLAN` — `CREATE INDEX` 줄을 주석 처리하면
  두 질의의 계획이 다시 같아진다.
