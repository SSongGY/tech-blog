# 예제 코드 — CREATE TABLE AS SELECT로 복사한 표가 잃는 것

파이썬 표준 라이브러리(`sqlite3`)만 쓴다. 설치할 것이 없다.

## 실행

```bash
python ctas_copy.py
```

## 바꿔볼 값

- 1절의 `SELECT * FROM product` 를 `SELECT * FROM product WHERE 0` 으로 바꿔 구조만 복사해도 제약이 따라오지 않는지 본다
- 5절에 `CAST(price AS TEXT)`, `CAST(price AS BLOB)` 컬럼을 더해 각각 어떤 타입 이름을 받는지 본다
- 8절의 `lemon` 가격을 양수로 바꾸고 세 행이 모두 들어가는지 본다
