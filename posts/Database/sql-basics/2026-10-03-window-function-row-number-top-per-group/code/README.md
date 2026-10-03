# 예제 코드 — ROW_NUMBER로 그룹별 1등 뽑기

메모리 SQLite에 직원 9명(부서 3개, 영업부에 최고 연봉 동점자 2명)을 넣고,
부서별 최고 연봉자를 GROUP BY와 ROW_NUMBER 두 방식으로 뽑아 결과를 나란히 찍는다.
외부 의존성 없이 파이썬 표준 라이브러리만 쓴다. `dbshow.py`는 표 정의와 데이터를 찍는 도우미다.

## 실행

```bash
python row_number_top_per_group.py
```

## 바꿔볼 값

- `EMPLOYEES`에서 영업부 동점자의 연봉을 다르게 바꾸면 3번(되붙이기)과 7번(ROW_NUMBER)의 행 수가 같아진다.
- 8번의 `rn <= 2`를 `rn <= 3`으로 바꿔 부서별 상위 N명을 본다.
- 10번의 `ORDER BY salary DESC, employee_id`에서 `employee_id`를 `name`으로 바꾸면 동점자 중 누가 남는지가 이름 순으로 정해진다.
