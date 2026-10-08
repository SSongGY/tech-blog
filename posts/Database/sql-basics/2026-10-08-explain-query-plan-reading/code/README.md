# 예제 코드 — EXPLAIN QUERY PLAN 읽는 법

사원 5,000행과 부서 10행을 만들고, 같은 질의를 인덱스가 없을 때와 있을 때로 나눠
`EXPLAIN QUERY PLAN`을 찍는다. 계획의 날것 네 컬럼(`id`·`parent`·`notused`·`detail`)을
먼저 보이고, 그 행을 `parent`로 이어 `sqlite3` CLI와 같은 트리로 그린다. 각 질의는
끝까지 실행해 VDBE 명령 수를 센다. 시간은 환경마다 흔들리지만 명령 수는 매번 같다.
외부 의존성 없이 파이썬 표준 라이브러리만 쓴다. `dbshow.py`는 표 정의와 데이터를 찍는 도우미다.

## 실행

```bash
python explain_query_plan.py
```

## 바꿔볼 값

- `EMPLOYEE_ROWS`를 50,000으로 올려 SCAN과 SEARCH의 명령 수 차이가 행 수에 비례해 벌어지는지 본다.
- 2-A 앞에서 `ANALYZE`를 돌려도 인덱스가 없으면 계획이 그대로인지 본다.
- 5-C의 `bonus`에 `(employee_id)` 인덱스를 만들면 `AUTOMATIC` 줄이 사라지는지 본다.
