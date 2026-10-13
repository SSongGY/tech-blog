# 예제 코드 — BETWEEN과 IN

메모리 SQLite에 주문 기록 6행(`order_log`)과 환불 요청 3행(`refund_request`)을 넣고
BETWEEN·IN의 동작을 확인한다. 금액에는 경계값 10000과 50000이 들어 있고, 3월 31일
주문에는 시각이 붙어 있으며, 환불 요청 하나는 `order_id`가 NULL이다. 사용자 정의 함수로
BETWEEN이 왼쪽 식을 몇 번 계산하는지 세고, 인덱스를 만든 뒤 `EXPLAIN QUERY PLAN`까지 찍는다.
외부 의존성 없이 파이썬 표준 라이브러리만 쓴다. `dbshow.py`는 표 정의와 데이터를 찍는 도우미다.

## 실행

```bash
python between_in_orders.py
```

## 바꿔볼 값

- `ORDERS`의 4번 주문 시각을 `"2026-03-31 00:00:00"`으로 바꾸면 5번 질의가 몇 행이 되는지 본다.
- 13번 질의의 하위 질의에서 `RF-002`를 빼고 돌려 `NOT IN`이 몇 행을 돌려주는지 본다.
- 21번 질의의 `abs(amount)`를 `amount`로 되돌려 실행계획이 어떻게 달라지는지 본다.
