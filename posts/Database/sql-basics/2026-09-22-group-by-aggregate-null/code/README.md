# 예제 코드 — GROUP BY와 집계 함수 — 묶는 기준 정하기

표준 라이브러리만 쓴다. 메모리 DB에 9행짜리 `employee` 테이블을 만든다.
`bonus`에 `NULL`이 네 개 섞여 있고 `team`에도 하나 있다. 이 `NULL`들이
`COUNT(*)` · `COUNT(bonus)` · `SUM` · `AVG` 에서 각각 어떻게 세어지는지와,
`GROUP BY`가 실행계획에서 무엇으로 바뀌는지를 뽑는다.

## 실행

```bash
python group_by_null.py
```

## 바꿔 볼 값

- `EMPLOYEE_ROWS` — 지원팀 세 행의 `None`을 숫자로 바꾸면 3장의 `SUM`·`AVG`가
  `NULL`에서 숫자로 바뀐다. 반대로 개발팀의 `200`을 `None`으로 바꾸면
  2장의 `AVG`와 손계산 값의 차이가 더 벌어진다.
- 9번 행의 `team` 을 `None` 에서 문자열로 바꾸면 4장의 `NULL` 그룹이 사라진다.
- 7장의 `CREATE INDEX ix_employee_team` 줄을 지우고 돌리면 7-2·7-3의 계획이
  7-1과 같아진다. `USE TEMP B-TREE FOR GROUP BY`가 나오는지가 핵심이다.
- 7-3의 `COUNT(bonus)` 를 `COUNT(*)` 로 바꾸면 `COVERING INDEX` 로 돌아간다.
