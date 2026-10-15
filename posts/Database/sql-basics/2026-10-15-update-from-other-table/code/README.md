# UPDATE … FROM 예제

다른 표의 값으로 갱신하는 세 가지 방법을 같은 초기 데이터에서 각각 돌려 비교한다.
의존성은 없다. 파이썬 표준 라이브러리의 `sqlite3` 모듈만 쓴다.

## 실행

```bash
python update_from.py
```

## 바꿔 볼 값

- `SCHEMA` 안의 `supplier_price` 행에 `('마바상사', 3, 190000)` 를 더 넣으면
  3번 모니터에 걸리는 공급사가 셋이 된다. ④·⑥의 결과가 어떻게 되는지 본다
- ④의 `WHERE sp.product_id = product.product_id` 뒤에
  `AND sp.unit_price = (SELECT MIN(unit_price) FROM supplier_price s2
  WHERE s2.product_id = product.product_id)` 를 붙이면 여러 행 중 하나를
  명시적으로 고르게 된다. ⑥에서 값이 더는 흔들리지 않는지 확인한다
- `product` 에 행을 늘리고 ⑦의 실행계획이 바뀌는지 본다.
  `supplier_price(product_id)` 에 인덱스를 만들면 `SCAN` 이 무엇으로 바뀌는지도 같이 본다

## 파일

| 파일 | 무엇 |
|---|---|
| `update_from.py` | 예제 본문 |
| `dbshow.py` | 표 정의와 데이터를 출력 앞에 찍는 도우미 (`references/dbshow.py` 사본) |
| `output.txt` | `blog.py run-example` 이 남긴 실행 기록. 손으로 고치지 않는다 |
