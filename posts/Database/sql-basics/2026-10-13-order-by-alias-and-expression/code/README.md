# 예제 코드 — ORDER BY의 별칭과 표현식

메모리 SQLite에 사원 5행(`employee`)을 넣고 `SELECT`에서 만든 별칭을 `ORDER BY`·`WHERE`·
`GROUP BY`·`HAVING`이 각각 어떻게 읽는지 확인한다. 자리 번호로 정렬할 때의 규칙, 별칭이
실제 컬럼 이름과 겹칠 때 어느 쪽이 이기는지, `DISTINCT`와 `UNION ALL`이 붙으면 무엇이
막히는지까지 24개 질의를 돌린다. 에러가 나는 질의는 에러 메시지를 그대로 찍는다.
외부 의존성 없이 파이썬 표준 라이브러리만 쓴다. `dbshow.py`는 표 정의와 데이터를 찍는 도우미다.

## 실행

```bash
python order_by_alias.py
```

## 바꿔볼 값

- 11번의 별칭 이름 `bonus_rate`를 `base_salary`로 바꿔 정렬 결과가 달라지는지 본다.
- 15번의 `ORDER BY base_salary`를 `ORDER BY dept DESC`로 바꾸면 `DISTINCT`에서도 통하는지 본다.
- 18번의 `ORDER BY amount * -1`을 `ORDER BY -amount`로 바꿔 에러 메시지가 같은지 본다.
