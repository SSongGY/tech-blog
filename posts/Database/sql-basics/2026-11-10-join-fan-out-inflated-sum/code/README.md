# 예제 코드 — 조인 뒤 SUM이 부풀려지는 이유 — 1:N 두 개를 한 번에 조인할 때

파이썬 표준 라이브러리(`sqlite3`)만 쓴다. 설치할 것이 없다.

## 실행

```bash
python join_fan_out.py
```

## 바꿔 볼 값

- `payment` 에 kim 의 결제를 한 건 더 넣으면 kim 의 주문 합계가 3배(75,000)로 바뀐다
- `orders` 의 102번 금액을 10000 이 아닌 값으로 바꾸면 3)의 `SUM(DISTINCT o.amount)` 가 우연히 맞아진다 — 그래서 DISTINCT 는 고친 것처럼 보이기 쉽다
