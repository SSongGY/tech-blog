# 예제 코드 — LAG와 LEAD

메모리 SQLite에 두 매장(강남점·판교점)의 월 매출을 넣고 LAG·LEAD로 전월 대비 증감을 구한다.
강남점 4월은 매출 값이 NULL이고, 판교점은 3월 행이 아예 없다. 두 경우가 LAG에서 어떻게
다르게 나오는지가 이 예제의 중심이다. 외부 의존성 없이 파이썬 표준 라이브러리만 쓴다.
`dbshow.py`는 표 정의와 데이터를 찍는 도우미다.

## 실행

```bash
python lag_lead_month_over_month.py
```

## 바꿔볼 값

- `MONTHLY_SALES`에 `("판교점", "2026-03", 100)`을 넣으면 6번의 `prev_month`가 어떻게 바뀌는지 본다.
- 4번의 기본값 `0`을 `NULL`로 바꾸면 강남점 1월의 `diff`가 무엇이 되는지 본다.
- 3번의 `PARTITION BY store`를 지우면 판교점 1월의 `prev_amount`에 어느 매장의 값이 들어가는지 본다.
