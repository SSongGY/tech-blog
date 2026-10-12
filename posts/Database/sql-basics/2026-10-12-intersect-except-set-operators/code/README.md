# 예제 코드 — INTERSECT와 EXCEPT

메모리 SQLite에 사내 교육 신청자 명단(`signup`)과 출석 명단(`attendance`)을 넣고,
INTERSECT·EXCEPT로 겹치는 사람과 한쪽에만 있는 사람을 구한다. 신청 명단에는 같은 사람이
두 번 들어가 있고, 두 명단 모두에 이메일이 NULL인 사람이 있다. 사번을 TEXT로 들고 있는
출석부(`attendance_sheet`)도 하나 더 둔다. 외부 의존성 없이 파이썬 표준 라이브러리만 쓴다.
`dbshow.py`는 표 정의와 데이터를 찍는 도우미다.

## 실행

```bash
python intersect_except_rosters.py
```

## 바꿔볼 값

- `ATTENDANCE`에서 박서준의 이메일을 `"seojun@example.com"`으로 바꾸면 6번과 8번이 어떻게 바뀌는지 본다.
- 15번 질의에서 `EXCEPT`와 `INTERSECT`의 자리를 바꿔 결과가 달라지는지 본다.
- `attendance_sheet`의 `employee_id` 타입을 `INTEGER`로 바꾸면 12번이 몇 행이 되는지 본다.
