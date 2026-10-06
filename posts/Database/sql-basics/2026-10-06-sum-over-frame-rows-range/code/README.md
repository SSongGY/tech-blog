# 예제 코드 — SUM OVER의 프레임

메모리 SQLite에 주문 7건을 넣는다. 10-03과 10-05에는 주문이 두 건씩 있고(같은 날짜 = 동점),
10-04에는 주문이 없다. 여기에 누적합·이동평균을 프레임 종류(ROWS·RANGE·GROUPS)만 바꿔 구해
값이 갈리는 자리를 본다. 외부 의존성 없이 파이썬 표준 라이브러리만 쓴다.
`dbshow.py`는 표 정의와 데이터를 찍는 도우미다.

## 실행

```bash
python sum_over_frame.py
```

## 바꿔볼 값

- `ORDERS`에서 4번 주문의 날짜를 `2026-10-04`(day_no 4)로 옮기면 2번의 두 컬럼이 어느 줄부터 같아지는지 본다.
- 5번의 `2 PRECEDING`을 `1 PRECEDING`으로 바꾸면 10-05 행의 `range_3`에서 어느 날짜가 빠지는지 센다.
- 3번의 `ORDER BY order_date, order_id`를 `ORDER BY order_date, amount`로 바꾸면 같은 날 두 행의 누적값이 어떻게 바뀌는지 본다.
