# 예제 코드 — DISTINCT — 중복 제거가 정렬을 부르는 이유

표준 라이브러리만 쓴다. 메모리 DB에 8행짜리 `employee` 테이블을 만들고
`EXPLAIN QUERY PLAN`으로 `DISTINCT`가 어떤 연산으로 바뀌는지 뽑는다.

## 실행

```bash
python distinct_plan.py
```

## 바꿔 볼 값

- `EMPLOYEE_ROWS` — 중복 조합을 늘리거나 줄여 본다. 행 수가 바뀌어도
  실행계획의 형태는 같다. `USE TEMP B-TREE FOR DISTINCT`가 나오는지가 핵심이다.
- `ix_employee_team` 생성 줄을 지우고 돌리면 3장의 계획이 2장과 같아진다.
- `SELECT DISTINCT team, grade` 를 `SELECT DISTINCT grade, team` 으로 바꾸면
  `ix_employee_team_grade` 인덱스를 타는지 확인할 수 있다. 인덱스 컬럼 순서와
  SELECT 목록 순서가 어떻게 맞물리는지가 드러난다.
