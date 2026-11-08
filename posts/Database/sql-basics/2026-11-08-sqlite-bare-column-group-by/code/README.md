# 예제 코드 — GROUP BY에 없는 컬럼을 SELECT에 쓰면

파이썬 표준 라이브러리(`sqlite3`)만 쓴다. 설치할 것이 없다.

## 실행

```bash
python bare_column.py
```

## 바꿔볼 값

- 동점 행(`baek`)을 넣는 순서를 바꿔 보고 맨 컬럼 값이 따라 바뀌는지 본다
- `max(salary)` 를 `sum(salary)` 로 바꾸고 이름이 어느 행에서 오는지 본다
- 6절의 `RANK()` 를 `ROW_NUMBER()` 로 바꿔 동점 중 한 명만 남는 것을 본다
