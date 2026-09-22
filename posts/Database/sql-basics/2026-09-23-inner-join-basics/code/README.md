# 예제 코드 — INNER JOIN — 두 테이블을 잇는 기본

메모리 SQLite에 고객 4명·주문 6건·배송 3건을 넣고, 조인 조건의 유무와 중복 키가
결과 행 수를 어떻게 바꾸는지 확인한다. 외부 의존성 없이 파이썬 표준 라이브러리만 쓴다.

## 실행

```bash
python inner_join_basics.py
```

## 바꿔볼 값

- `SALE_ORDERS`의 105번(`customer_id = 9`) — `customer`에 없는 값이다. 지우면
  4-B가 0건에서 1건으로 바뀐다.
- `SALE_ORDERS`의 106번(`customer_id = None`) — NULL 키다. 4-C·4-D가 왜 0건인지 보는 자리다.
- `SHIPMENTS`에 고객 1번 배송을 한 건 더 넣으면 5-B의 합계가 400 → 1200 → 1600으로 늘어난다.
  조인이 합계를 몇 배로 만드는지 직접 보는 자리다.
- 6-B의 `CREATE INDEX` 줄을 주석 처리하면 실행계획이 6-A와 같아진다.
