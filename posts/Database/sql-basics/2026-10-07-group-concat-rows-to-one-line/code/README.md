# 예제 코드 — GROUP_CONCAT

메모리 SQLite에 직원 5명과 보유 기술 11행을 넣고, 직원별 기술 목록을 한 칸에 모으는
`group_concat()`을 돌려 본다. 구분자 지정, 함수 안의 `ORDER BY`, `string_agg` 별칭, `NULL`
처리, `DISTINCT`와 구분자를 같이 쓸 때의 에러, `ORDER BY`가 없을 때 인덱스에 따라 순서가
바뀌는 것, 길이 상한을 낮췄을 때의 에러, 값 안에 구분자가 있을 때 되돌릴 수 없는 문제를 확인한다.
외부 의존성 없이 파이썬 표준 라이브러리만 쓴다. `dbshow.py`는 표 정의와 데이터를 찍는 도우미다.

## 실행

```bash
python group_concat_basics.py
```

## 바꿔볼 값

- 5번 질의의 `ORDER BY s.level DESC, s.skill`에서 `, s.skill`을 지우고 같은 레벨끼리의 순서가 매번 같은지 본다.
- 11번의 상한 `60`을 `200`으로 올리면 11-B가 몇 바이트에서 통과하는지 본다.
- 9-B의 인덱스를 `(employee_id, skill)`(오름차순)으로 바꾸면 9-A와 결과가 같아지는지 본다.
