# 예제 코드 — 코호트 표 — 첫 구매 월을 기준으로 재구매 고객을 세는 SQL

파이썬 표준 라이브러리(`sqlite3`)만 쓴다. 설치할 것이 없다.

## 실행

```bash
python cohort.py
```

## 바꿔 볼 값

- `customer_order` 에 같은 달 주문을 더 넣으면 [3] 의 `order_rows` 와 `customers` 차이가 커진다
- [2] 의 `/ 30` 을 `/ 30.4` 로 바꿔도 월말·월초 주문(1월 31일 → 2월 1일)은 여전히 0 개월로 나온다
- `pivot_columns` 의 `range(4)` 를 늘리면 m4, m5 칸이 생긴다
