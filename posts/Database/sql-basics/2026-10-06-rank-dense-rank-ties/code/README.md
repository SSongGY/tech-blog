# 예제 코드 — RANK와 DENSE_RANK

메모리 SQLite에 학생 10명(1반·2반)의 시험 점수를 넣는다. 88점 2명, 75점 3명이 동점이고
결시자 2명은 점수가 NULL이다. 여기에 ROW_NUMBER·RANK·DENSE_RANK를 나란히 붙여 동점을
어떻게 세는지 비교한다. 외부 의존성 없이 파이썬 표준 라이브러리만 쓴다.
`dbshow.py`는 표 정의와 데이터를 찍는 도우미다.

## 실행

```bash
python rank_dense_rank_ties.py
```

## 바꿔볼 값

- `SCORES`에서 박서준의 88점을 87점으로 바꾸면 1번의 세 컬럼 가운데 어느 줄부터 값이 같아지는지 본다.
- 2번의 `<= 3`을 `<= 2`로 바꾸면 RANK와 DENSE_RANK가 몇 명씩 돌려주는지 다시 센다.
- 6번의 `NULLS LAST`를 지우면 결시자 두 명이 몇 등이 되는지 본다.
