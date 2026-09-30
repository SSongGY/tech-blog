# 예제 코드 — 문자열 함수 기본 — 자르기, 붙이기, 바꾸기

메모리 SQLite에 회원 5명을 넣고 상품 코드·이메일·메모를 문자열 함수로 자르고, 잇고, 바꾼다.
마지막 절에서는 JPN- 코드 회원 2,000행을 더 넣고 `ANALYZE`한 뒤, `WHERE` 절 컬럼에 함수를
씌웠을 때 인덱스가 쓰이는지 `EXPLAIN QUERY PLAN`으로 본다. 파이썬 표준 라이브러리만 쓴다.

`CONCAT`·`CONCAT_WS`는 SQLite 3.44.0부터 있다. 그보다 낮은 SQLite에서는 2-B·2-C가 에러를 낸다.

## 실행

```bash
python string_functions.py
```

## 바꿔볼 값

- 4-B 앞에 `conn.execute("PRAGMA case_sensitive_like = ON")`을 넣고 `LIKE 'KOR%'`의 실행계획이 바뀌는지 본다.
- `product_code` 컬럼을 `TEXT NOT NULL COLLATE NOCASE`로 바꾸면 4-B와 4-D의 실행계획이 서로 뒤바뀌는지 본다.
- 3-B의 `TRIM(memo, ' ' || CHAR(9))`에서 `CHAR(9)`를 빼고 2번 회원의 탭이 남는지 본다.
