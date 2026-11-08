# 예제 코드 — 중앙값 구하기 — 함수가 없을 때 ROW_NUMBER와 COUNT로 홀짝 행을 함께 처리하는 법

파이썬 표준 라이브러리(`sqlite3`, `statistics`)만 쓴다. 설치할 것이 없다.

## 실행

```bash
python median_sql.py
```

## 바꿔볼 값

- `employee` 에 행을 하나 넣고 빼며 홀수·짝수일 때 `lo`, `hi` 가 어떻게 바뀌는지 본다
- `ROW_NUMBER()` 를 `DENSE_RANK()` 로 바꿔 동점이 있는 부서의 중앙값이 어떻게 틀어지는지 본다
- `WHERE salary IS NOT NULL` 을 지우고 `ops` 부서의 결과를 본다
