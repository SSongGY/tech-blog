# 예제 코드 — 관계 나눗셈 — '전부 가진' 행을 SQL로 찾는 두 가지 방법

표준 라이브러리만 쓴다. 메모리 DB 라 파일을 남기지 않는다.

## 실행

```bash
python relational_division.py
```

## 바꿔 볼 값

- `required_course` 에 `('ai')` 를 넣으면 kim 도 빠지고 아무도 남지 않는다
- `GROUP_BY_SQL` 의 `JOIN required_course` 를 지우면 2절의 잘못된 결과가 다시 나온다
- 4절에서 `GROUP BY` 쪽을 `LEFT JOIN` 으로 바꿔도 필수 목록이 비면 결과가 비는지 확인해 본다
