# 예제 코드 — COUNT(*)와 COUNT(컬럼)

메모리 SQLite에 회원 5명과 주문 5건을 넣는다. 휴대폰이 NULL인 회원, 빈 문자열('')인 회원,
지역이 겹치는 회원, 주문이 하나도 없는 회원이 섞여 있다. `COUNT(*)`·`COUNT(컬럼)`·
`COUNT(DISTINCT 컬럼)`을 나란히 찍고, LEFT JOIN 뒤에 무엇을 세느냐에 따라 결과가 달라지는 것을 본다.
외부 의존성 없이 파이썬 표준 라이브러리만 쓴다.

## 실행

```bash
python count_variants.py
```

## 바꿔볼 값

- `MEMBERS`의 4번 회원 휴대폰 `""`을 `None`으로 바꾸면 1-B의 두 값이 같아진다.
- 4번 회원의 지역 `None`을 `"부산"`으로 바꾸면 1-A의 `COUNT(city)`는 늘지만 `COUNT(DISTINCT city)`는 그대로다.
- `ORDERS`에 회원 2의 주문을 하나 넣으면 4-A와 4-B에서 2번 회원의 값이 같아진다.
