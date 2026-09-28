# 예제 코드 — COALESCE와 NULLIF

메모리 SQLite에 주문 5건을 넣는다. 할인액이 NULL인 주문, 휴대폰이 빈 문자열('')인 주문,
수량이 0인 주문이 섞여 있다. 연산·비교·집계에서 NULL이 결과를 어떻게 바꾸는지 찍고,
`COALESCE`와 `NULLIF`로 고친 결과를 나란히 찍는다. 외부 의존성 없이 파이썬 표준 라이브러리만 쓴다.

## 실행

```bash
python coalesce_nullif.py
```

## 바꿔볼 값

- `ORDERS`의 2번 주문 휴대폰 `""`을 `None`으로 바꾸면 4-A와 5-B 결과가 같아진다.
- 3번 주문의 할인액 `0`을 `None`으로 바꾸면 3-A의 `COUNT(discount)`가 하나 줄고 3-B의 평균이 바뀐다.
- 5-C의 `list_price / quantity`를 `list_price * 1.0 / quantity`로 바꿔 실수 나눗셈에서도
  0으로 나눈 결과가 같은지 본다.
